//+------------------------------------------------------------------+
//| TNV_Indicator.mq5                                                |
//| Final version - DRAW_ARROW + Alert with N                        |
//| v3.26 - 10s TNV                               |
//|         + Breakout Quality Filter + Score system                 |
//|         + Buffer, Body Ratio, Range, HTF filter                  |
//|         + Score in alerts for both Entry and Exit                |
//+------------------------------------------------------------------+
#property copyright "TNV Indicator"
#property version   "3.26"
#property indicator_chart_window
#property indicator_buffers 14
#property indicator_plots   12
//--- Level plots
#property indicator_label1  "S1 Entry High"
#property indicator_type1   DRAW_LINE
#property indicator_color1  clrDodgerBlue
#property indicator_style1  STYLE_SOLID
#property indicator_width1  1
#property indicator_label2  "S1 Entry Low"
#property indicator_type2   DRAW_LINE
#property indicator_color2  clrDodgerBlue
#property indicator_style2  STYLE_SOLID
#property indicator_width2  1
#property indicator_label3  "S1 Exit High"
#property indicator_type3   DRAW_LINE
#property indicator_color3  clrAqua
#property indicator_style3  STYLE_DOT
#property indicator_width3  1
#property indicator_label4  "S1 Exit Low"
#property indicator_type4   DRAW_LINE
#property indicator_color4  clrAqua
#property indicator_style4  STYLE_DOT
#property indicator_width4  1
#property indicator_label5  "S2 Entry High"
#property indicator_type5   DRAW_LINE
#property indicator_color5  clrOrangeRed
#property indicator_style5  STYLE_SOLID
#property indicator_width5  2
#property indicator_label6  "S2 Entry Low"
#property indicator_type6   DRAW_LINE
#property indicator_color6  clrOrangeRed
#property indicator_style6  STYLE_SOLID
#property indicator_width6  2
//--- Arrow plots
#property indicator_label7  "S1 Long"
#property indicator_type7   DRAW_ARROW
#property indicator_color7  clrDodgerBlue
#property indicator_width7  2
#property indicator_label8  "S1 Short"
#property indicator_type8   DRAW_ARROW
#property indicator_color8  clrOrangeRed
#property indicator_width8  2
#property indicator_label9  "S1 Exit"
#property indicator_type9   DRAW_ARROW
#property indicator_color9  clrAqua
#property indicator_width9  2
#property indicator_label10 "S2 Long"
#property indicator_type10  DRAW_ARROW
#property indicator_color10 clrOrangeRed
#property indicator_width10 2
#property indicator_label11 "S2 Short"
#property indicator_type11  DRAW_ARROW
#property indicator_color11 clrOrangeRed
#property indicator_width11 2
#property indicator_label12 "S2 Exit"
#property indicator_type12  DRAW_ARROW
#property indicator_color12 clrAqua
#property indicator_width12 2
//+------------------------------------------------------------------+
enum ENUM_TNV_SYSTEM
{
   SYSTEM_1, // Only System 1
   SYSTEM_2, // Only System 2
   BOTH      // Both systems
};
//+------------------------------------------------------------------+
input group "=== System Selection ==="
input ENUM_TNV_SYSTEM InpSystem = SYSTEM_1; // TNV system to use
input group "=== System 1 ==="
input int    InpS1Entry     = 20;    // System 1 Entry period
input int    InpS1Exit      = 10;    // System 1 Exit period
input bool   InpS1SkipRule  = false; // Enable Skip Rule (simple on/off)
input group "=== System 2 ==="
input int    InpS2Entry     = 55;    // System 2 Entry period
input int    InpS2Exit      = 20;    // System 2 Exit period
input group "=== N Calculation ==="
input int    InpATRPeriod   = 20;    // N period (Wilder)
input group "=== Analysis ==="
input int    InpBarsToAnalyze = 5;   // Number of bars to analyze / keep arrows
input group "=== Instance ===";
input string InpInstanceName = "1"; // Đặt khác nhau cho mỗi chart: "1", "2"
input group "=== Alerts ==="
input bool   InpAlertPopup  = false;  // Popup Alert
input bool   InpAlertPush   = false;  // Push Notification
input bool   InpAlertSound  = false;  // Sound Alert
input bool   InpShowArrows  = true;  // Show signal arrows
input group "=== Alert Types ==="
input bool   InpAlertS1Entry = true; // Alert System 1 Entry (Long/Short)
input bool   InpAlertS1Exit  = true; // Alert System 1 Exit
input bool   InpAlertS2Entry = false; // Alert System 2 Entry (Long/Short)
input bool   InpAlertS2Exit  = false; // Alert System 2 Exit
input group "=== Line Visibility ==="
input bool   InpShowS1EntryLines = true; // Show System 1 Entry High/Low lines
input bool   InpShowS1ExitLines  = true; // Show System 1 Exit High/Low lines
input bool   InpShowS2EntryLines = true; // Show System 2 Entry High/Low lines
input group "=== Alert Filter ==="
input bool   InpAlertOnlyFirstBreak = true; // Only alert on the first breakout/exit bar
input group "=== Breakout Quality Filter ==="
input bool   InpUseQualityFilter   = true;  // Enable Quality Filter & Score
input double InpBufferMult         = 0.15;  // Buffer multiplier (x N)
input double InpMinBodyRatio       = 0.50;  // Min body ratio (0.50 = 50%)
input bool   InpRequireCloseThird  = true;  // Require close in top/bottom 1/3
input double InpRangeMult          = 0.70;  // Min range multiplier (x N)
input int    InpBonusRange         = 2;     // Points for good range
input int    InpBonusHTF           = 2;     // Points for HTF not against
input int    InpBonusN             = 1;     // Points for good N level
input int    InpMinScore           = 5;     // Minimum score to send alert (5-10)
//+------------------------------------------------------------------+
double BufS1EntryHigh[], BufS1EntryLow[];
double BufS1ExitHigh[],  BufS1ExitLow[];
double BufS2EntryHigh[], BufS2EntryLow[];
double BufS1LongArrow[], BufS1ShortArrow[], BufS1ExitArrow[];
double BufS2LongArrow[], BufS2ShortArrow[], BufS2ExitArrow[];
double BufN[], BufDummy[];
datetime lastProcessedBar = 0;
string   gvPrefix = "";
bool     firstRun = true;
bool     gvBreakoutFired = false;   // ưu tiên Breakout nếu cùng bar có cả Breakout & Exit
//+------------------------------------------------------------------+
string MakeGVName(string key) { return gvPrefix + key; }
bool WasAlerted(string key, datetime barTime)
{
   string name = MakeGVName(key);
   if(!GlobalVariableCheck(name)) return false;
   return ((datetime)GlobalVariableGet(name) == barTime);
}
void SetAlerted(string key, datetime barTime)
{
   GlobalVariableSet(MakeGVName(key), (double)barTime);
}
//+------------------------------------------------------------------+
string PeriodToShort(ENUM_TIMEFRAMES period)
{
   switch(period)
   {
      case PERIOD_M1:  return "M1";
      case PERIOD_M2:  return "M2";
      case PERIOD_M3:  return "M3";
      case PERIOD_M4:  return "M4";
      case PERIOD_M5:  return "M5";
      case PERIOD_M6:  return "M6";
      case PERIOD_M10: return "M10";
      case PERIOD_M12: return "M12";
      case PERIOD_M15: return "M15";
      case PERIOD_M20: return "M20";
      case PERIOD_M30: return "M30";
      case PERIOD_H1:  return "H1";
      case PERIOD_H2:  return "H2";
      case PERIOD_H3:  return "H3";
      case PERIOD_H4:  return "H4";
      case PERIOD_H6:  return "H6";
      case PERIOD_H8:  return "H8";
      case PERIOD_H12: return "H12";
      case PERIOD_D1:  return "D1";
      case PERIOD_W1:  return "W1";
      case PERIOD_MN1: return "MN1";
      default:         return IntegerToString((int)period);
   }
}
//+------------------------------------------------------------------+
ENUM_TIMEFRAMES GetHigherTimeframe(ENUM_TIMEFRAMES current)
{
   switch(current)
   {
      case PERIOD_M1:
      case PERIOD_M2:
      case PERIOD_M3:
      case PERIOD_M4:
      case PERIOD_M5:  return PERIOD_M15;
      case PERIOD_M6:
      case PERIOD_M10:
      case PERIOD_M12:
      case PERIOD_M15: return PERIOD_H1;
      case PERIOD_M20:
      case PERIOD_M30: return PERIOD_H1;
      case PERIOD_H1:  return PERIOD_H4;
      case PERIOD_H2:
      case PERIOD_H3:
      case PERIOD_H4:  return PERIOD_D1;
      case PERIOD_H6:
      case PERIOD_H8:
      case PERIOD_H12: return PERIOD_D1;
      case PERIOD_D1:  return PERIOD_W1;
      default:         return PERIOD_H1;
   }
}
//+------------------------------------------------------------------+
int OnInit()
{
   gvPrefix = "TNVInd_" + _Symbol + "_" + IntegerToString(_Period) + "_" + InpInstanceName + "_";
   firstRun = true;
   lastProcessedBar = 0;
   SetIndexBuffer(0,  BufS1EntryHigh,  INDICATOR_DATA);
   SetIndexBuffer(1,  BufS1EntryLow,   INDICATOR_DATA);
   SetIndexBuffer(2,  BufS1ExitHigh,   INDICATOR_DATA);
   SetIndexBuffer(3,  BufS1ExitLow,    INDICATOR_DATA);
   SetIndexBuffer(4,  BufS2EntryHigh,  INDICATOR_DATA);
   SetIndexBuffer(5,  BufS2EntryLow,   INDICATOR_DATA);
   SetIndexBuffer(6,  BufS1LongArrow,  INDICATOR_DATA);
   SetIndexBuffer(7,  BufS1ShortArrow, INDICATOR_DATA);
   SetIndexBuffer(8,  BufS1ExitArrow,  INDICATOR_DATA);
   SetIndexBuffer(9,  BufS2LongArrow,  INDICATOR_DATA);
   SetIndexBuffer(10, BufS2ShortArrow, INDICATOR_DATA);
   SetIndexBuffer(11, BufS2ExitArrow,  INDICATOR_DATA);
   SetIndexBuffer(12, BufN,            INDICATOR_CALCULATIONS);
   SetIndexBuffer(13, BufDummy,        INDICATOR_CALCULATIONS);
   PlotIndexSetInteger(6,  PLOT_ARROW, 233); // S1 Long
   PlotIndexSetInteger(7,  PLOT_ARROW, 234); // S1 Short
   PlotIndexSetInteger(8,  PLOT_ARROW, 251); // S1 Exit
   PlotIndexSetInteger(9,  PLOT_ARROW, 233); // S2 Long
   PlotIndexSetInteger(10, PLOT_ARROW, 234); // S2 Short
   PlotIndexSetInteger(11, PLOT_ARROW, 251); // S2 Exit
   ArraySetAsSeries(BufS1EntryHigh,  true);
   ArraySetAsSeries(BufS1EntryLow,   true);
   ArraySetAsSeries(BufS1ExitHigh,   true);
   ArraySetAsSeries(BufS1ExitLow,    true);
   ArraySetAsSeries(BufS2EntryHigh,  true);
   ArraySetAsSeries(BufS2EntryLow,   true);
   ArraySetAsSeries(BufS1LongArrow,  true);
   ArraySetAsSeries(BufS1ShortArrow, true);
   ArraySetAsSeries(BufS1ExitArrow,  true);
   ArraySetAsSeries(BufS2LongArrow,  true);
   ArraySetAsSeries(BufS2ShortArrow, true);
   ArraySetAsSeries(BufS2ExitArrow,  true);
   ArraySetAsSeries(BufN,            true);
   ArraySetAsSeries(BufDummy,        true);
   IndicatorSetString(INDICATOR_SHORTNAME, "TNV Indicator v3.26");
   IndicatorSetInteger(INDICATOR_DIGITS, _Digits);
   return INIT_SUCCEEDED;
}
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
}
//+------------------------------------------------------------------+
double GetHighest(int from_bar, int period)
{
   double high[];
   ArraySetAsSeries(high, true);
   if(CopyHigh(_Symbol, PERIOD_CURRENT, from_bar, period, high) < period)
      return 0.0;
   double result = high[0];
   for(int i = 1; i < period; i++)
      if(high[i] > result) result = high[i];
   return result;
}
double GetLowest(int from_bar, int period)
{
   double low[];
   ArraySetAsSeries(low, true);
   if(CopyLow(_Symbol, PERIOD_CURRENT, from_bar, period, low) < period)
      return DBL_MAX;
   double result = low[0];
   for(int i = 1; i < period; i++)
      if(low[i] < result) result = low[i];
   return result;
}
//+------------------------------------------------------------------+
double ComputeN()
{
   int bars_needed = InpATRPeriod * 3 + 2;
   double high[], low[], close[];
   ArraySetAsSeries(high,  true);
   ArraySetAsSeries(low,   true);
   ArraySetAsSeries(close, true);
   if(CopyHigh (_Symbol, PERIOD_CURRENT, 1, bars_needed, high)  < bars_needed) return 0;
   if(CopyLow  (_Symbol, PERIOD_CURRENT, 1, bars_needed, low)   < bars_needed) return 0;
   if(CopyClose(_Symbol, PERIOD_CURRENT, 1, bars_needed, close) < bars_needed) return 0;
   double tr[];
   ArrayResize(tr, bars_needed);
   for(int i = bars_needed - 2; i >= 0; i--)
   {
      double hl  = high[i] - low[i];
      double hpc = MathAbs(high[i] - close[i + 1]);
      double lpc = MathAbs(low[i]  - close[i + 1]);
      tr[i] = MathMax(hl, MathMax(hpc, lpc));
   }
   int start = bars_needed - 2;
   double seed = 0;
   for(int i = 0; i < InpATRPeriod; i++)
      seed += tr[start - i];
   seed /= InpATRPeriod;
   double n = seed;
   for(int i = start - InpATRPeriod; i >= 0; i--)
      n = (n * (InpATRPeriod - 1) + tr[i]) / InpATRPeriod;
   return n;
}
//+------------------------------------------------------------------+
//| Check if Higher Timeframe is NOT clearly against the direction   |
//+------------------------------------------------------------------+
bool IsHTFNotAgainst(bool isLong)
{
   ENUM_TIMEFRAMES htf = GetHigherTimeframe(_Period);
   double htf_close[], htf_open[], htf_high[], htf_low[];
   ArraySetAsSeries(htf_close, true);
   ArraySetAsSeries(htf_open,  true);
   ArraySetAsSeries(htf_high,  true);
   ArraySetAsSeries(htf_low,   true);

   if(CopyClose(_Symbol, htf, 1, 5, htf_close) < 5) return true;
   if(CopyOpen (_Symbol, htf, 1, 5, htf_open)  < 5) return true;
   if(CopyHigh (_Symbol, htf, 1, 5, htf_high)  < 5) return true;
   if(CopyLow  (_Symbol, htf, 1, 5, htf_low)   < 5) return true;

   int lowerHighs = 0;
   int lowerLows  = 0;
   int higherHighs = 0;
   int higherLows  = 0;

   for(int i = 1; i < 4; i++)
   {
      if(htf_high[i] < htf_high[i+1]) lowerHighs++;
      if(htf_low[i]  < htf_low[i+1])  lowerLows++;
      if(htf_high[i] > htf_high[i+1]) higherHighs++;
      if(htf_low[i]  > htf_low[i+1])  higherLows++;
   }

   if(isLong)
   {
      if(lowerHighs >= 2 && lowerLows >= 2)
         return false;
      return true;
   }
   else
   {
      if(higherHighs >= 2 && higherLows >= 2)
         return false;
      return true;
   }
}
//+------------------------------------------------------------------+
//| Calculate quality score for a signal candle                      |
//| Returns score 0-10. Score < 5 means mandatory conditions failed  |
//+------------------------------------------------------------------+
int CalculateScore(bool isLong, double bar_open, double bar_high, double bar_low, double bar_close, double n_value)
{
   if(!InpUseQualityFilter)
      return 10;

   if(n_value <= 0)
      return 0;

   double range = bar_high - bar_low;
   if(range <= 0)
      return 0;

   double body = MathAbs(bar_close - bar_open);
   double bodyRatio = body / range;

   if(bodyRatio < InpMinBodyRatio)
      return 0;

   if(InpRequireCloseThird)
   {
      double third = range / 3.0;
      if(isLong)
      {
         if(bar_close < (bar_high - third))
            return 0;
      }
      else
      {
         if(bar_close > (bar_low + third))
            return 0;
      }
   }

   int score = 5;

   if(range >= InpRangeMult * n_value)
      score += InpBonusRange;

   if(IsHTFNotAgainst(isLong))
      score += InpBonusHTF;

   if(bodyRatio >= InpMinBodyRatio && range >= (InpRangeMult * 0.8 * n_value))
      score += InpBonusN;

   if(score > 10) score = 10;
   return score;
}
//+------------------------------------------------------------------+
void FireAlert(string msg, string key, datetime barTime, int score)
{
   if(score < InpMinScore)
      return;

   if(WasAlerted(key, barTime))
      return;

   SetAlerted(key, barTime);

   string tf   = PeriodToShort(_Period);
   string full = "TNV | " + _Symbol + " " + tf + " | " + msg +
                 " | Score: " + IntegerToString(score) + "/10";

   if(InpAlertPopup) Alert(full);
   if(InpAlertPush)  SendNotification(full);
   if(InpAlertSound) PlaySound("alert.wav");
   Print(full);

   // Ghi dữ liệu cho EA WebBridge qua GlobalVariable (nhất quán bias/score)
   bool isBreakout = (StringFind(msg, "Breakout") >= 0);

   if(isBreakout)
   {
      // Breakout -> bias LONG/SHORT + score THẬT từ indicator + exitSignal=false
      gvBreakoutFired = true;
      GlobalVariableSet("TNV_SIGNAL_SCORE", score);
      GlobalVariableSet("TNV_SIGNAL_EXIT", 0);   // Breakout -> KHÔNG phải Exit
      if(StringFind(msg, "LONG") >= 0)       GlobalVariableSet("TNV_SIGNAL_BIAS", 1);
      else if(StringFind(msg, "SHORT") >= 0) GlobalVariableSet("TNV_SIGNAL_BIAS", 2);
   }
   else
   {
      // Exit -> exitSignal=true. Trong cùng 1 bar, Exit được đánh giá SAU Breakout
      // (thứ tự: Entry Breakout rồi mới Exit) nên cờ Exit thắng (Exit xảy ra sau).
      // Guard gvBreakoutFired chỉ giữ nguyên bias/score để ưu tiên Breakout,
      // KHÔNG áp dụng cho cờ Exit.
      GlobalVariableSet("TNV_SIGNAL_EXIT", 1);
      if(!gvBreakoutFired)
      {
         GlobalVariableSet("TNV_SIGNAL_BIAS", 0);   // NEUTRAL
         GlobalVariableSet("TNV_SIGNAL_SCORE", 0);  // NEUTRAL -> score 0 (hết mâu thuẫn NEUTRAL + score cao)
      }
   }

}
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
   ArraySetAsSeries(time,  true);
   ArraySetAsSeries(open,  true);
   ArraySetAsSeries(high,  true);
   ArraySetAsSeries(low,   true);
   ArraySetAsSeries(close, true);

   if(rates_total < InpS2Entry + InpATRPeriod + 60)
      return 0;

   bool useSystem1 = (InpSystem == SYSTEM_1 || InpSystem == BOTH);
   bool useSystem2 = (InpSystem == SYSTEM_2 || InpSystem == BOTH);

   int clearLimit = (prev_calculated > 0) ? rates_total - prev_calculated + 2 : rates_total;
   if(clearLimit > rates_total) clearLimit = rates_total;
   for(int i = 0; i < clearLimit; i++)
   {
      BufS1LongArrow[i]  = EMPTY_VALUE;
      BufS1ShortArrow[i] = EMPTY_VALUE;
      BufS1ExitArrow[i]  = EMPTY_VALUE;
      BufS2LongArrow[i]  = EMPTY_VALUE;
      BufS2ShortArrow[i] = EMPTY_VALUE;
      BufS2ExitArrow[i]  = EMPTY_VALUE;
   }

   int limit = (prev_calculated > 0) ? rates_total - prev_calculated + 1 : rates_total - 1;
   if(limit < 2) limit = 2;
   for(int i = limit - 1; i >= 0; i--)
   {
      if(useSystem1)
      {
         if(InpShowS1EntryLines)
         {
            BufS1EntryHigh[i] = GetHighest(i + 1, InpS1Entry);
            BufS1EntryLow[i]  = GetLowest (i + 1, InpS1Entry);
         }
         else
         {
            BufS1EntryHigh[i] = EMPTY_VALUE;
            BufS1EntryLow[i]  = EMPTY_VALUE;
         }
         if(InpShowS1ExitLines)
         {
            BufS1ExitHigh[i] = GetHighest(i + 1, InpS1Exit);
            BufS1ExitLow[i]  = GetLowest (i + 1, InpS1Exit);
         }
         else
         {
            BufS1ExitHigh[i] = EMPTY_VALUE;
            BufS1ExitLow[i]  = EMPTY_VALUE;
         }
      }
      else
      {
         BufS1EntryHigh[i] = EMPTY_VALUE;
         BufS1EntryLow[i]  = EMPTY_VALUE;
         BufS1ExitHigh[i]  = EMPTY_VALUE;
         BufS1ExitLow[i]   = EMPTY_VALUE;
      }
      if(useSystem2 && InpShowS2EntryLines)
      {
         BufS2EntryHigh[i] = GetHighest(i + 1, InpS2Entry);
         BufS2EntryLow[i]  = GetLowest (i + 1, InpS2Entry);
      }
      else
      {
         BufS2EntryHigh[i] = EMPTY_VALUE;
         BufS2EntryLow[i]  = EMPTY_VALUE;
      }
   }

   if(prev_calculated == 0 || firstRun)
   {
      lastProcessedBar = time[0];
      firstRun = false;
      return rates_total;
   }

   bool isNewBar = (time[0] != lastProcessedBar);
   if(isNewBar)
      lastProcessedBar = time[0];

   double n_value = 0;
   if(isNewBar)
      n_value = ComputeN();

   int barsToScan = MathMin(InpBarsToAnalyze, rates_total - 5);
   if(barsToScan < 2) barsToScan = 2;

   for(int i = 1; i <= barsToScan; i++)
   {
      gvBreakoutFired = false;   // reset mỗi bar: nếu bar này có Breakout thì Exit không được đè
      double   bar_open  = open[i];
      double   bar_high  = high[i];
      double   bar_low   = low[i];
      double   bar_close = close[i];
      datetime bar_time  = time[i];

      if(bar_close <= 0) continue;

      bool doAlert = (isNewBar && i == 1);

      //-------------------- SYSTEM 1 --------------------
      if(useSystem1)
      {
         double high20 = GetHighest(i + 1, InpS1Entry);
         double low20  = GetLowest (i + 1, InpS1Entry);
         double high10 = GetHighest(i + 1, InpS1Exit);
         double low10  = GetLowest (i + 1, InpS1Exit);

         double prev_high20 = GetHighest(i + 2, InpS1Entry);
         double prev_low20  = GetLowest (i + 2, InpS1Entry);
         double prev_high10 = GetHighest(i + 2, InpS1Exit);
         double prev_low10  = GetLowest (i + 2, InpS1Exit);

         // Long Entry
         if(bar_high > high20)
         {
            if(!InpS1SkipRule)
            {
               double buffer = InpBufferMult * n_value;
               bool bufferOK = (n_value <= 0) || (bar_close > high20 + buffer);

               if(InpShowArrows && bufferOK)
                  BufS1LongArrow[i] = bar_low;

               bool isFirstBreak = true;
               if(InpAlertOnlyFirstBreak)
                  isFirstBreak = !(high[i + 1] > prev_high20);

               if(doAlert && InpAlertS1Entry && isFirstBreak && bufferOK)
               {
                  int score = CalculateScore(true, bar_open, bar_high, bar_low, bar_close, n_value);
                  FireAlert("SYSTEM 1 LONG Breakout | Close=" + DoubleToString(bar_close, _Digits) +
                            " | N=" + DoubleToString(n_value, _Digits),
                            "S1_LONG", bar_time, score);
               }
            }
         }

         // Short Entry
         if(bar_low < low20)
         {
            if(!InpS1SkipRule)
            {
               double buffer = InpBufferMult * n_value;
               bool bufferOK = (n_value <= 0) || (bar_close < low20 - buffer);

               if(InpShowArrows && bufferOK)
                  BufS1ShortArrow[i] = bar_high;

               bool isFirstBreak = true;
               if(InpAlertOnlyFirstBreak)
                  isFirstBreak = !(low[i + 1] < prev_low20);

               if(doAlert && InpAlertS1Entry && isFirstBreak && bufferOK)
               {
                  int score = CalculateScore(false, bar_open, bar_high, bar_low, bar_close, n_value);
                  FireAlert("SYSTEM 1 SHORT Breakout | Close=" + DoubleToString(bar_close, _Digits) +
                            " | N=" + DoubleToString(n_value, _Digits),
                            "S1_SHORT", bar_time, score);
               }
            }
         }

         // Exit Long
         if(bar_close < low10)
         {
            if(InpShowArrows)
               BufS1ExitArrow[i] = bar_high;

            bool isFirstBreak = true;
            if(InpAlertOnlyFirstBreak)
               isFirstBreak = !(close[i + 1] < prev_low10);

            if(doAlert && InpAlertS1Exit && isFirstBreak)
            {
               int score = CalculateScore(false, bar_open, bar_high, bar_low, bar_close, n_value);
               FireAlert("SYSTEM 1 EXIT LONG | Close=" + DoubleToString(bar_close, _Digits) +
                         " | N=" + DoubleToString(n_value, _Digits),
                         "S1_EXIT_L", bar_time, score);
            }
         }

         // Exit Short
         if(bar_close > high10)
         {
            if(InpShowArrows)
               BufS1ExitArrow[i] = bar_low;

            bool isFirstBreak = true;
            if(InpAlertOnlyFirstBreak)
               isFirstBreak = !(close[i + 1] > prev_high10);

            if(doAlert && InpAlertS1Exit && isFirstBreak)
            {
               int score = CalculateScore(true, bar_open, bar_high, bar_low, bar_close, n_value);
               FireAlert("SYSTEM 1 EXIT SHORT | Close=" + DoubleToString(bar_close, _Digits) +
                         " | N=" + DoubleToString(n_value, _Digits),
                         "S1_EXIT_S", bar_time, score);
            }
         }
      }

      //-------------------- SYSTEM 2 --------------------
      if(useSystem2)
      {
         double high55   = GetHighest(i + 1, InpS2Entry);
         double low55    = GetLowest (i + 1, InpS2Entry);
         double high20s2 = GetHighest(i + 1, InpS2Exit);
         double low20s2  = GetLowest (i + 1, InpS2Exit);

         double prev_high55   = GetHighest(i + 2, InpS2Entry);
         double prev_low55    = GetLowest (i + 2, InpS2Entry);
         double prev_high20s2 = GetHighest(i + 2, InpS2Exit);
         double prev_low20s2  = GetLowest (i + 2, InpS2Exit);

         // Long Entry
         if(bar_high > high55)
         {
            double buffer = InpBufferMult * n_value;
            bool bufferOK = (n_value <= 0) || (bar_close > high55 + buffer);

            if(InpShowArrows && bufferOK)
               BufS2LongArrow[i] = bar_low;

            bool isFirstBreak = true;
            if(InpAlertOnlyFirstBreak)
               isFirstBreak = !(high[i + 1] > prev_high55);

            if(doAlert && InpAlertS2Entry && isFirstBreak && bufferOK)
            {
               int score = CalculateScore(true, bar_open, bar_high, bar_low, bar_close, n_value);
               FireAlert("SYSTEM 2 LONG Breakout | Close=" + DoubleToString(bar_close, _Digits) +
                         " | N=" + DoubleToString(n_value, _Digits),
                         "S2_LONG", bar_time, score);
            }
         }

         // Short Entry
         if(bar_low < low55)
         {
            double buffer = InpBufferMult * n_value;
            bool bufferOK = (n_value <= 0) || (bar_close < low55 - buffer);

            if(InpShowArrows && bufferOK)
               BufS2ShortArrow[i] = bar_high;

            bool isFirstBreak = true;
            if(InpAlertOnlyFirstBreak)
               isFirstBreak = !(low[i + 1] < prev_low55);

            if(doAlert && InpAlertS2Entry && isFirstBreak && bufferOK)
            {
               int score = CalculateScore(false, bar_open, bar_high, bar_low, bar_close, n_value);
               FireAlert("SYSTEM 2 SHORT Breakout | Close=" + DoubleToString(bar_close, _Digits) +
                         " | N=" + DoubleToString(n_value, _Digits),
                         "S2_SHORT", bar_time, score);
            }
         }

         // Exit Long
         if(bar_close < low20s2)
         {
            if(InpShowArrows)
               BufS2ExitArrow[i] = bar_high;

            bool isFirstBreak = true;
            if(InpAlertOnlyFirstBreak)
               isFirstBreak = !(close[i + 1] < prev_low20s2);

            if(doAlert && InpAlertS2Exit && isFirstBreak)
            {
               int score = CalculateScore(false, bar_open, bar_high, bar_low, bar_close, n_value);
               FireAlert("SYSTEM 2 EXIT LONG | Close=" + DoubleToString(bar_close, _Digits) +
                         " | N=" + DoubleToString(n_value, _Digits),
                         "S2_EXIT_L", bar_time, score);
            }
         }

         // Exit Short
         if(bar_close > high20s2)
         {
            if(InpShowArrows)
               BufS2ExitArrow[i] = bar_low;

            bool isFirstBreak = true;
            if(InpAlertOnlyFirstBreak)
               isFirstBreak = !(close[i + 1] > prev_high20s2);

            if(doAlert && InpAlertS2Exit && isFirstBreak)
            {
               int score = CalculateScore(true, bar_open, bar_high, bar_low, bar_close, n_value);
               FireAlert("SYSTEM 2 EXIT SHORT | Close=" + DoubleToString(bar_close, _Digits) +
                         " | N=" + DoubleToString(n_value, _Digits),
                         "S2_EXIT_S", bar_time, score);
            }
         }
      }
   }
   return rates_total;
}
//+------------------------------------------------------------------+