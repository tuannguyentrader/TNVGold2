//+------------------------------------------------------------------+
//| TNV_WebBridge_EA.mq5                                             |
//| v2.01 - GlobalVariable version (đọc TNV_SIGNAL_BIAS + SCORE)    |
//| + ADX/VWAP/EMA/ATR/RSI thật + multiTf.*.volatility               |
//| QUAN TRỌNG: trường InpSecretToken là PLACEHOLDER, KHÔNG commit    |
//| token thật. Người dùng tự nhập, phải giống TNV_SECRET_KEY trên   |
//| server (Vercel).                                                 |
//+------------------------------------------------------------------+
#property copyright "TNV"
#property version   "2.01"
#property description "TNV WebBridge GlobalVariable"

input group "=== WebBridge Configuration ===";
input bool   InpWebEnabled   = true;
input string InpWebUrl       = "https://tnvgold.vercel.app/api/pulse";
// KHÔNG đưa token thật vào repo - người dùng tự nhập, phải giống TNV_SECRET_KEY trên server
input string InpSecretToken  = "REPLACE_WITH_YOUR_SECRET_TOKEN";

input group "=== Indicator Calc ===";
input int    InpATRPeriod = 20;
input int    InpRSIPeriod = 14;
input int    InpADXPeriod = 14;

datetime g_last_candle = 0;
int      g_rsi_handle  = INVALID_HANDLE;
int      g_atr_handle  = INVALID_HANDLE;
int      g_adx_handle  = INVALID_HANDLE;
datetime g_lastSignalTime = 0;   // thời điểm ghi TNV_SIGNAL_BIAS LONG/SHORT cuối (tính signalAge)
int      g_lastGvBias     = -1;  // giá trị TNV_SIGNAL_BIAS gần nhất quan sát được

int OnInit()
{
   g_rsi_handle = iRSI(_Symbol, PERIOD_M5, InpRSIPeriod, PRICE_CLOSE);
   g_atr_handle = iATR(_Symbol, PERIOD_M5, InpATRPeriod);
   g_adx_handle = iADX(_Symbol, PERIOD_M5, InpADXPeriod);
   Print("[TNV EA] Khởi động v2.01!");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   if(g_rsi_handle != INVALID_HANDLE) IndicatorRelease(g_rsi_handle);
   if(g_atr_handle != INVALID_HANDLE) IndicatorRelease(g_atr_handle);
   if(g_adx_handle != INVALID_HANDLE) IndicatorRelease(g_adx_handle);
}

void OnTick()
{
   datetime candle_time = iTime(_Symbol, PERIOD_M5, 0);
   if(candle_time == g_last_candle) return;
   g_last_candle = candle_time;
   if(!InpWebEnabled) return;
   SendPulseToWeb();
}

//--- Wilder ATR
double GetATR()
{
   double b[];
   ArraySetAsSeries(b, true);
   if(g_atr_handle != INVALID_HANDLE && CopyBuffer(g_atr_handle, 0, 0, 1, b) >= 1 && b[0] != EMPTY_VALUE) return b[0];
   // fallback
   double h[], l[], c[];
   ArraySetAsSeries(h, true); ArraySetAsSeries(l, true); ArraySetAsSeries(c, true);
   int bn = InpATRPeriod * 3 + 2;
   if(CopyHigh(_Symbol, PERIOD_M5, 1, bn, h) < bn || CopyLow(_Symbol, PERIOD_M5, 1, bn, l) < bn || CopyClose(_Symbol, PERIOD_M5, 1, bn, c) < bn) return 0;
   double tr[]; ArrayResize(tr, bn);
   for(int i = bn - 2; i >= 0; i--) {
      double hl = h[i] - l[i], hc = MathAbs(h[i] - c[i+1]), lc = MathAbs(l[i] - c[i+1]);
      tr[i] = MathMax(hl, MathMax(hc, lc));
   }
   int s = bn - 2; double seed = 0;
   for(int i = 0; i < InpATRPeriod; i++) seed += tr[s - i];
   seed /= InpATRPeriod;
   double nv = seed;
   for(int i = s - InpATRPeriod; i >= 0; i--) nv = (nv * (InpATRPeriod - 1) + tr[i]) / InpATRPeriod;
   return nv;
}

//--- RSI Wilder
double GetRSI()
{
   double b[];
   ArraySetAsSeries(b, true);
   if(g_rsi_handle != INVALID_HANDLE && CopyBuffer(g_rsi_handle, 0, 0, 1, b) >= 1 && b[0] != EMPTY_VALUE) return b[0];
   double c[];
   ArraySetAsSeries(c, true);
   if(CopyClose(_Symbol, PERIOD_M5, 0, InpRSIPeriod + 2, c) < InpRSIPeriod + 2) return 50.0;
   double gains = 0, losses = 0;
   for(int i = 0; i < InpRSIPeriod; i++) { double d = c[i] - c[i+1]; if(d > 0) gains += d; else losses -= d; }
   if(losses == 0) return 100;
   return 100 - (100 / (1 + (gains / losses)));
}

//--- ADX (iADX buffer 0 = ADX)
double GetADX()
{
   double b[];
   ArraySetAsSeries(b, true);
   if(g_adx_handle != INVALID_HANDLE && CopyBuffer(g_adx_handle, 0, 0, 1, b) >= 1 && b[0] != EMPTY_VALUE) return b[0];
   return 0;
}

//--- EMA xuôi chiều
void ComputeEMA(const double &series[], int count, double &ema9, double &ema21)
{
   double m9 = 2.0/10, m21 = 2.0/22;
   ema9 = series[count-1]; ema21 = series[count-1];
   for(int i = count - 2; i >= 0; i--) {
      ema9 = (series[i] - ema9) * m9 + ema9;
      ema21 = (series[i] - ema21) * m21 + ema21;
   }
}

//--- VWAP (tích luỹ typical*vol/vol phiên/ngày)
double ComputeVWAP()
{
   MqlRates r[];
   ArraySetAsSeries(r, true);
   int n = CopyRates(_Symbol, PERIOD_M5, 0, 288, r);
   if(n <= 1) return 0;
   int day = (int)(r[0].time / 86400);
   double tpv = 0, vol = 0;
   for(int i = 0; i < n; i++) {
      if((int)(r[i].time / 86400) != day) break;
      double tp = (r[i].high + r[i].low + r[i].close) / 3.0;
      double v = (double)r[i].tick_volume;
      if(v > 0) { tpv += tp * v; vol += v; }
   }
   if(vol <= 0) return 0;
   return tpv / vol;
}

//--- High/Low/Exit/ATR cho 1 khung
void GetTF(ENUM_TIMEFRAMES tf, double &h, double &l, double &e, double &vol)
{
   MqlRates r[];
   ArraySetAsSeries(r, true);
   h = 0; l = 0; e = 0; vol = 0;
   if(CopyRates(_Symbol, tf, 0, 25, r) < 25) return;
   h = r[1].high; l = r[1].low; e = r[1].low;
   for(int i = 1; i <= 20; i++) { if(r[i].high > h) h = r[i].high; if(r[i].low < l) l = r[i].low; }
   for(int i = 1; i <= 10; i++) { if(r[i].low < e) e = r[i].low; }
   // ATR của khung này (fallback TR trung bình)
   double ts = 0;
   for(int i = 1; i <= 20; i++) {
      double hl = r[i].high - r[i].low;
      double hc = MathAbs(r[i].high - r[i+1].close);
      double lc = MathAbs(r[i].low - r[i+1].close);
      ts += MathMax(hl, MathMax(hc, lc));
   }
   vol = ts / 20.0;
}

string TFBias(double p, double h, double l) { if(p >= h) return "LONG"; if(p <= l) return "SHORT"; return "NEUTRAL"; }

void SendPulseToWeb()
{
   string bias = "NEUTRAL";
   int score = 0;

   // Đọc TNV_SIGNAL_BIAS từ indicator (1=LONG, 2=SHORT, 0=NEUTRAL)
   if(GlobalVariableCheck("TNV_SIGNAL_BIAS")) {
      int sig = (int)GlobalVariableGet("TNV_SIGNAL_BIAS");
      if(sig == 1)      bias = "LONG";
      else if(sig == 2) bias = "SHORT";
      else              bias = "NEUTRAL";
   }

   // Đọc score THẬT từ indicator (0-10). Nếu chưa có, fallback theo bias.
   if(GlobalVariableCheck("TNV_SIGNAL_SCORE")) {
      score = (int)GlobalVariableGet("TNV_SIGNAL_SCORE");
   } else {
      score = (bias == "NEUTRAL") ? 0 : 8;
   }

   // Đọc TNV_SIGNAL_EXIT từ indicator (1=Exit, 0=Breakout/không Exit)
   bool exitSignal = false;
   if(GlobalVariableCheck("TNV_SIGNAL_EXIT")) {
      int ex = (int)GlobalVariableGet("TNV_SIGNAL_EXIT");
      exitSignal = (ex == 1);
   }
   string exit_sig = exitSignal ? "true" : "false";

   // signalAge = số phút kể từ lần ghi TNV_SIGNAL_BIAS LONG/SHORT gần nhất.
   // Chỉ cập nhật mốc khi giá trị GV chuyển sang LONG/SHORT (tín hiệu mới).
   int sigNow = -1;
   if(GlobalVariableCheck("TNV_SIGNAL_BIAS")) sigNow = (int)GlobalVariableGet("TNV_SIGNAL_BIAS");
   if((sigNow == 1 || sigNow == 2) && sigNow != g_lastGvBias)
      g_lastSignalTime = TimeCurrent();
   g_lastGvBias = sigNow;
   int signalAge = 0;
   if(g_lastSignalTime > 0)
      signalAge = (int)((TimeCurrent() - g_lastSignalTime) / 60.0);

   double price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double atr = GetATR();
   double rsi = GetRSI();
   double adx = GetADX();
   double ema9 = 0, ema21 = 0;
   double close_arr[];
   ArraySetAsSeries(close_arr, true);
   if(CopyClose(_Symbol, PERIOD_M5, 0, 30, close_arr) >= 30)
      ComputeEMA(close_arr, 30, ema9, ema21);
   double emaGap = (ema9 > 0 && ema21 > 0) ? (ema9 - ema21) : 0;
   double vwap = ComputeVWAP();
   double vwap_delta = (vwap > 0) ? (price - vwap) : 0;
   double spread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) * _Point;
   if(spread <= 0) spread = 0.12;

   double h20, l20, e10, v5;
   GetTF(PERIOD_M5, h20, l20, e10, v5);
   if(h20 <= 0) h20 = price + 2;
   if(l20 <= 0) l20 = price - 2;
   double gain = price - h20;

   double m15h, m15l, m15e, m15v, m30h, m30l, m30e, m30v, h1h, h1l, h1e, h1v;
   GetTF(PERIOD_M15, m15h, m15l, m15e, m15v);
   GetTF(PERIOD_M30, m30h, m30l, m30e, m30v);
   GetTF(PERIOD_H1, h1h, h1l, h1e, h1v);
   string m15b = TFBias(price, m15h, m15l);
   string m30b = TFBias(price, m30h, m30l);
   string h1b  = TFBias(price, h1h, h1l);
   int m15s = (m15b != "NEUTRAL") ? 8 : 0;
   int m30s = (m30b != "NEUTRAL") ? 7 : 0;
   int h1s  = (h1b != "NEUTRAL") ? 9 : 0;

   string json = StringFormat(
      "{\"symbol\":\"%s\",\"time\":\"%s\",\"price\":%.2f,\"bias\":\"%s\",\"score\":%d,\"exitSignal\":%s,\"signalAge\":%d,"
      "\"volatility\":%.2f,\"entry\":{\"high\":%.2f,\"low\":%.2f,\"gain\":%.2f},\"exit\":%.2f,\"htf\":\"Not Against\","
      "\"multiTf\":{"
         "\"m15\":{\"bias\":\"%s\",\"score\":%d,\"high\":%.2f,\"low\":%.2f,\"exit\":%.2f,\"htf\":\"%s\",\"volatility\":%.2f},"
         "\"m30\":{\"bias\":\"%s\",\"score\":%d,\"high\":%.2f,\"low\":%.2f,\"exit\":%.2f,\"htf\":\"%s\",\"volatility\":%.2f},"
         "\"h1\":{\"bias\":\"%s\",\"score\":%d,\"high\":%.2f,\"low\":%.2f,\"exit\":%.2f,\"htf\":\"%s\",\"volatility\":%.2f}"
      "},"
      "\"indicators\":{\"rsi\":%.1f,\"atr\":%.2f,\"emaGap\":%.2f,\"adx\":%.1f,\"vwap\":%.2f,\"spread\":%.2f}}",
      _Symbol, TimeToString(TimeCurrent(), TIME_SECONDS), price, bias, score, exit_sig, signalAge,
      atr, h20, l20, gain, e10,
      m15b, m15s, m15h, m15l, m15e, (m15b=="NEUTRAL"?"Neutral":(m15b=="LONG"?"Bullish":"Bearish")), m15v,
      m30b, m30s, m30h, m30l, m30e, (m30b=="NEUTRAL"?"Neutral":(m30b=="LONG"?"Bullish":"Bearish")), m30v,
      h1b, h1s, h1h, h1l, h1e, (h1b=="NEUTRAL"?"Neutral":(h1b=="LONG"?"Bullish":"Bearish")), h1v,
      rsi, atr, emaGap, adx, vwap_delta, spread
   );

   char post[], result[];
   string headers = "Content-Type: application/json\r\nUser-Agent: TNVWebEA/2.01\r\nAuthorization: Bearer " + InpSecretToken + "\r\n";
   int len = StringLen(json);
   StringToCharArray(json, post, 0, len, CP_UTF8);
   string result_headers;
   ResetLastError();
   int res = WebRequest("POST", InpWebUrl, headers, 5000, post, result, result_headers);
   if(res == 200 || res == 201)
      PrintFormat("[TNV EA] Sent %s %.2f | RSI:%.1f ATR:%.2f -> web (HTTP %d)", bias, price, rsi, atr, res);
   else {
      string resp = CharArrayToString(result, 0, WHOLE_ARRAY, CP_UTF8);
      PrintFormat("[TNV EA] HTTP %d - %s", res, resp);
   }
}
//+------------------------------------------------------------------+
