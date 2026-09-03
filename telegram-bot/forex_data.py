#!/usr/bin/env python3
"""
forex_data.py — TNVGold Telegram Bot (XAUUSD)
Module lấy dữ liệu lịch kinh tế từ Forex Factory, cache, parse, filter.

Module độc lập, không phụ thuộc file khác trong project.
Chỉ dùng: requests, beautifulsoup4, json, datetime, zoneinfo, typing.
"""

import json
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

log = logging.getLogger("forex_factory")

# ─── Thư mục chứa module này ───────────────────────────────────────────────
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(MODULE_DIR, "news_cache.json")
DEBUG_LOG_FILE = os.path.join(MODULE_DIR, "ff_debug_log.txt")
# Tăng CACHE_VERSION mỗi khi thay đổi cấu trúc cache để cache cũ tự động bị vô hiệu
CACHE_VERSION = 2


def _debug_log(msg: str) -> None:
    """Ghi dòng log vào ff_debug_log.txt (cạnh module) — để chẩn đoán trên VPS.

    Mỗi lần chạy /news, mở file ở chế độ 'a' (append) để không mất log cũ.
    Nếu không ghi được thì bỏ qua (không crash bot).
    """
    try:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass

# ─── Timezone ───────────────────────────────────────────────────────────────
try:
    from zoneinfo import ZoneInfo
    ET_TZ = ZoneInfo("America/New_York")
    UTC_TZ = timezone.utc
    VN_TZ = timezone(timedelta(hours=7))
except ImportError:
    # Python < 3.9 fallback (dùng timedelta offset cố định)
    UTC_TZ = timezone.utc
    ET_TZ = timezone(timedelta(hours=-4))  # EDT mặc định
    VN_TZ = timezone(timedelta(hours=7))
    ZoneInfo = None  # type: ignore


# ═══════════════════════════════════════════════════════════════════════════════
# 1.  get_calendar(refresh=False)  — entry point chính
# ═══════════════════════════════════════════════════════════════════════════════
def get_calendar(refresh: bool = False) -> list[dict[str, Any]]:
    """Lấy lịch kinh tế hôm nay (theo giờ UTC).

    Args:
        refresh: True → bỏ qua cache, fetch mới.

    Returns:
        List event dict, mỗi dict có keys:
            time_utc:   datetime (UTC)
            currency:   str
            impact:     "High" | "Medium" | "Low"
            title:      str
            forecast:   str | None
            previous:   str | None
            actual:     str | None
        [] nếu lỗi.
    """
    try:
        _debug_log(f"get_calendar: bắt đầu (refresh={refresh})")
        if not refresh:
            cached = _read_cache()
            if cached:
                _debug_log(f"get_calendar: dùng CACHE ({len(cached)} events)")
                return cached
            _debug_log("get_calendar: không có cache hợp lệ")

        # Thử dùng nguồn XML trực tiếp (chính thức, ổn định)
        events = _fetch_via_xml()
        if events:
            log.info("get_calendar: XML feed thành công (%d events)", len(events))
            _debug_log(f"get_calendar: XML feed thành công ({len(events)} events)")
            _write_cache(events)
            return events
        log.info("get_calendar: XML feed không trả events")
        _debug_log("get_calendar: XML feed KHÔNG trả events")

        # Thử dùng thư viện forexfactory_scraper trước
        events = _fetch_via_library()
        if events:
            log.info("get_calendar: library thành công (%d events)", len(events))
            _debug_log(f"get_calendar: library thành công ({len(events)} events)")
            _write_cache(events)
            return events
        log.info("get_calendar: library không trả events")
        _debug_log("get_calendar: library KHÔNG trả events")

        # Fallback: parse HTML
        events = _fetch_via_html()
        if events:
            log.info("get_calendar: HTML thành công (%d events)", len(events))
            _debug_log(f"get_calendar: HTML thành công ({len(events)} events)")
            _write_cache(events)
            return events
        log.warning("get_calendar: CẢ 3 nguồn đều thất bại")
        _debug_log("get_calendar: CẢ 3 nguồn đều thất bại")

        return []
    except Exception as e:
        _debug_log(f"get_calendar: LỖI {type(e).__name__}: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# 2.  CACHE
# ═══════════════════════════════════════════════════════════════════════════════
def _today_utc_str() -> str:
    """Trả về 'YYYY-MM-DD' cho ngày hôm nay UTC."""
    return datetime.now(UTC_TZ).strftime("%Y-%m-%d")


def _read_cache() -> Optional[list[dict[str, Any]]]:
    """Đọc cache nếu còn trong ngày hôm nay (UTC).

    Trả None nếu cache không tồn tại, hết ngày, RỖNG hoặc lỗi —
    để get_calendar() thử fetch mới. Cache rỗng ("events": []) không
    được xem là kết quả cuối: nó có thể được ghi khi Forex Factory
    chưa công bố event của ngày (hoặc khi fetch lỗi một phần), nên
    ta luôn thử fetch lại thay vì trả "không có tin" ngay.
    """
    try:
        if not os.path.isfile(CACHE_FILE):
            return None
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return None
        if data.get("date") != _today_utc_str():
            return None
        if data.get("version") != CACHE_VERSION:
            # Cache cũ từ phiên bản code trước → bỏ qua, fetch mới
            return None
        raw = data.get("events", [])
        if not raw:
            # Cache rỗng → coi như không có cache, cho fetch mới
            return None
        # Khôi phục time_utc từ str → datetime
        events = []
        for ev in raw:
            if isinstance(ev, dict):
                t_str = ev.pop("_time_utc", None)
                if t_str:
                    try:
                        ev["time_utc"] = datetime.fromisoformat(t_str)
                    except (ValueError, TypeError):
                        ev["time_utc"] = None
                events.append(ev)
        return events
    except Exception:
        return None


def _write_cache(events: list[dict[str, Any]]) -> None:
    """Ghi cache với ngày hôm nay."""
    try:
        raw = []
        for ev in events:
            d = dict(ev)
            t = d.pop("time_utc", None)
            if isinstance(t, datetime):
                d["_time_utc"] = t.isoformat()
            else:
                d["_time_utc"] = None
            raw.append(d)
        data = {"date": _today_utc_str(), "version": CACHE_VERSION, "events": raw}
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# 3a.  FETCH VIA XML FEED  (ff_calendar_thisweek.xml — nguồn chính thức)
# ═══════════════════════════════════════════════════════════════════════════════
_COUNTRY_CURRENCY = {
    "united states": "USD",
    "usa": "USD",
    "us": "USD",
    "eurozone": "EUR",
    "germany": "EUR",
    "france": "EUR",
    "italy": "EUR",
    "spain": "EUR",
    "netherlands": "EUR",
    "japan": "JPY",
    "united kingdom": "GBP",
    "uk": "GBP",
    "britain": "GBP",
    "canada": "CAD",
    "australia": "AUD",
    "new zealand": "NZD",
    "switzerland": "CHF",
    "china": "CNY",
    "india": "INR",
}


def _country_to_currency(country: str) -> str:
    """Map tên nước trong XML feed → mã tiền tệ (VD 'United States' → 'USD')."""
    key = (country or "").strip().lower()
    return _COUNTRY_CURRENCY.get(key, country.strip().upper())


def _fetch_via_xml() -> Optional[list[dict[str, Any]]]:
    """Lấy lịch từ XML feed chính thức của Forex Factory.

    URL: https://nfs.faireconomy.media/ff_calendar_thisweek.xml
    Feed có events từ đầu tuần → cuối tuần. Lọc lại theo ngày ET hôm nay.

    Cấu trúc mỗi <event> (dùng CDATA):
      <title>Non-Farm Employment Change</title>
      <country>USD</country>          ← mã tiền tệ, không phải tên nước
      <date>09-01-2026</date>         ← MM-DD-YYYY
      <time>3:15pm</time>             ← 12h
      <impact>High</impact>
      <forecast>180K</forecast> | <previous>142K</previous>
    """
    try:
        import requests
        import xml.etree.ElementTree as ET
    except ImportError:
        return None

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        r = requests.get(
            "https://nfs.faireconomy.media/ff_calendar_thisweek.xml",
            headers=headers,
            timeout=15,
        )
        _debug_log(f"XML feed: HTTP {r.status_code}, len={len(r.text)}")
        # 4xx/5xx = bị chặn → không parse
        if r.status_code >= 400:
            log.warning("XML feed HTTP %d (có thể bị chặn)", r.status_code)
            _debug_log(f"XML feed: HTTP {r.status_code} (bị chặn?)")
            return None

        # Kiểm tra nội dung có phải XML thật không
        raw = r.text.strip()
        if not raw.startswith("<?xml"):
            log.warning("XML feed trả về không phải XML (đầu: %s…)", raw[:60])
            _debug_log(f"XML feed: KHÔNG phải XML (đầu: {raw[:80]!r})")
            return None

        root = ET.fromstring(raw)
        # FEED XML TRẢ GIỜ THEO UTC (đã xác minh: NFP 12:15pm = 12:30 UTC).
        # Ngày lọc theo UTC để khớp giờ UTC của event.
        today_utc = datetime.now(UTC_TZ)
        today_date = today_utc.strftime("%m-%d-%Y")  # MM-DD-YYYY
        _debug_log(f"XML feed: ngày UTC hôm nay = {today_date}")

        results: list[dict[str, Any]] = []
        for ev in root.findall("event"):
            date_str = (ev.findtext("date") or "").strip()
            time_str = (ev.findtext("time") or "").strip()
            currency = (ev.findtext("country") or "").strip().upper()
            impact = (ev.findtext("impact") or "Low").strip()
            title = (ev.findtext("title") or "").strip()

            if date_str != today_date:
                continue

            # Parse giờ 12h (VD "2:00pm") theo UTC → datetime UTC
            time_utc = _parse_ff_time_utc(date_str, time_str)
            if time_utc is None:
                log.warning("XML feed: không parse được time %s %s", date_str, time_str)
                continue

            forecast = _clean_value(ev.findtext("forecast"))
            previous = _clean_value(ev.findtext("previous"))

            results.append({
                "time_utc": time_utc,
                "currency": currency,
                "impact": impact,
                "title": title,
                "forecast": forecast,
                "previous": previous,
                "actual": None,
            })

        if results:
            log.info("XML feed: %d events hôm nay (%s)", len(results), today_date)
            _debug_log(f"XML feed: {len(results)} events hôm nay {today_date}")
        else:
            log.info("XML feed: 0 events cho ngày %s (feed có %d events tổng)",
                     today_date, len(root.findall("event")))
            _debug_log(f"XML feed: 0 events hôm nay (feed tổng {len(root.findall('event'))} events)")
        return results if results else None
    except Exception as e:
        log.warning("XML feed lỗi: %s", e)
        _debug_log(f"XML feed: LỖI {type(e).__name__}: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# 3b.  FETCH VIA LIBRARY  (forexfactory_scraper)
# ═══════════════════════════════════════════════════════════════════════════════
def _fetch_via_library() -> Optional[list[dict[str, Any]]]:
    """Dùng thư viện forexfactory_scraper nếu có.

    API: fetch_and_parse_xml(currency_filter, impact_filter, user_timezone)
    Trả list event dict với keys: title, currency, date, time, impact,
    forecast, previous, url.

    Thời gian trong feed là 12h (vd "5:00pm") ở múi giờ America/New_York.
    Hàm này chuyển về UTC 24h và parse datetime.
    """
    try:
        import forexfactory_scraper  # type: ignore

        # Lấy tất cả events (không filter) để parse hôm nay.
        # Feed đôi khi trả 429 (rate limit) → thử lại tối đa 2 lần.
        raw = []
        for attempt in range(2):
            raw = forexfactory_scraper.fetch_and_parse_xml()
            if raw:
                break
            time.sleep(2)
        if not raw:
            return None

        # Feed dùng ngày theo giờ ET (New York) — so sánh với ngày ET hiện tại
        # (không dùng UTC: lúc 00-07h UTC ngày mới, ET vẫn là ngày cũ → mất hết event)
        today_et = datetime.now(ET_TZ)
        today_date = today_et.strftime("%m-%d-%Y")

        results: list[dict[str, Any]] = []
        for ev in raw:
            date_str = ev.get("date", "")
            time_str = ev.get("time", "")  # 12h format, America/New_York
            impact = ev.get("impact", "Low")
            currency = ev.get("currency", "")

            # Chỉ lấy event hôm nay
            if date_str != today_date:
                continue

            # Parse time_utc: chuyển 12h ET → datetime UTC
            time_utc = _parse_ff_time(date_str, time_str)
            if time_utc is None:
                continue

            forecast = _clean_value(ev.get("forecast"))
            previous = _clean_value(ev.get("previous"))

            results.append({
                "time_utc": time_utc,
                "currency": currency,
                "impact": impact,
                "title": ev.get("title", ""),
                "forecast": forecast,
                "previous": previous,
                "actual": None,  # XML feed không có actual
            })

        # Không có event hôm nay → trả None để thử fallback HTML
        return results if results else None
    except ImportError:
        return None
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# 3b.  FETCH VIA HTML  (fallback — BeautifulSoup)
# ═══════════════════════════════════════════════════════════════════════════════
def _fetch_via_html() -> Optional[list[dict[str, Any]]]:
    """Fallback: tự parse trang Forex Factory HTML bằng BeautifulSoup.

    URL: https://www.forexfactory.com/calendar?day=today
    Parse các hàng tr.calendar__row, đọc các td tương ứng.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return None

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        r = requests.get(
            "https://www.forexfactory.com/calendar?day=today",
            headers=headers,
            timeout=15,
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.select("tr.calendar__row")
        if not rows:
            return None

        # Feed dùng ngày theo giờ ET — so sánh với ngày ET hiện tại
        today_et = datetime.now(ET_TZ)
        today_date_iso = today_et.strftime("%Y-%m-%d")  # dạng data-date của FF
        today_date_ff = today_et.strftime("%m.%d.%Y")  # dạng hiển thị cũ

        # Ngày hiện đang xét: chỉ dòng ĐẦU TIÊN của mỗi ngày có ô ngày đầy đủ,
        # các dòng sau cùng ngày có ô ngày trống → phải nhớ ngày qua các row.
        current_day = None  # 'YYYY-MM-DD'

        def _norm_date(s: str) -> str:
            # Chuẩn hoá 'YYYY-MM-DD' hoặc 'MM.DD.YYYY' → 'YYYY-MM-DD'
            s = (s or "").strip()
            if not s:
                return ""
            s = s.replace(".", "-")
            parts = s.split("-")
            if len(parts) == 3 and len(parts[0]) == 4:
                return f"{parts[0]}-{parts[1]}-{parts[2]}"
            if len(parts) == 3:
                return f"{parts[2]}-{parts[0]}-{parts[1]}"
            return s

        results: list[dict[str, Any]] = []
        for row in rows:
            # Cập nhật ngày hiện tại từ ô ngày (data-date hoặc text)
            date_td = row.select_one("td.calendar__day")
            if date_td:
                data_date = date_td.get("data-date") or ""
                txt = date_td.get_text(strip=True)
                if data_date:
                    current_day = _norm_date(data_date)
                elif txt:
                    # Text như 'Fri Aug 30' → thử parse
                    try:
                        dt = datetime.strptime(txt, "%a %b %d")
                        current_day = dt.replace(year=today_et.year).strftime("%Y-%m-%d")
                    except ValueError:
                        pass

            if current_day is None:
                continue
            if current_day not in (today_date_iso, _norm_date(today_date_ff)):
                continue

            time_td = row.select_one("td.calendar__time")
            currency_td = row.select_one("td.calendar__currency")
            impact_td = row.select_one("td.calendar__impact")
            event_td = row.select_one("td.calendar__event")
            forecast_td = row.select_one("td.calendar__forecast")
            previous_td = row.select_one("td.calendar__previous")

            time_str = time_td.get_text(strip=True) if time_td else ""
            currency = currency_td.get_text(strip=True) if currency_td else ""
            title = event_td.get_text(strip=True) if event_td else ""

            # Xác định impact — class của FF: 'impact--high'/'impact--medium' có thể
            # nằm trên td hoặc span bên trong. Kiểm tra cả hai.
            impact = "Low"
            if impact_td:
                imp_cls = " ".join(impact_td.get("class", [])).lower()
                if "high" in imp_cls:
                    impact = "High"
                elif "medium" in imp_cls:
                    impact = "Medium"
                if impact == "Low":
                    imp_span = impact_td.select_one("span")
                    if imp_span:
                        imp_cls = " ".join(imp_span.get("class", [])).lower()
                        if "high" in imp_cls:
                            impact = "High"
                        elif "medium" in imp_cls:
                            impact = "Medium"

            forecast = _clean_value(
                forecast_td.get_text(strip=True) if forecast_td else None
            )
            previous = _clean_value(
                previous_td.get_text(strip=True) if previous_td else None
            )

            # Parse time: FF dùng 12h format, múi ET
            # current_day là 'YYYY-MM-DD' → đổi sang 'MM-DD-YYYY' cho _parse_ff_time
            iso_parts = current_day.split("-")
            date_for_parse = f"{iso_parts[1]}-{iso_parts[2]}-{iso_parts[0]}"
            time_utc = _parse_ff_time(date_for_parse, time_str)
            if time_utc is None:
                continue

            results.append({
                "time_utc": time_utc,
                "currency": currency,
                "impact": impact,
                "title": title,
                "forecast": forecast,
                "previous": previous,
                "actual": None,
            })

        return results
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
#  HỖ TRỢ: parse thời gian từ feed Forex Factory
# ═══════════════════════════════════════════════════════════════════════════════
def _parse_ff_time_utc(date_str: str, time_str: str) -> Optional[datetime]:
    """Chuyển date_str (MM-DD-YYYY) + time_str (12h, "2:00pm") → datetime UTC.

    XML feed của Forex Factory trả giờ THEO UTC (đã xác minh bằng NFP:
    feed ghi "12:15pm" = 12:30 UTC = 8:30 ET). Không cần đổi múi giờ.
    """
    if not date_str or not time_str:
        return None
    try:
        time_24 = _to_24h(time_str.strip())
        if not time_24:
            return None
        naive = datetime.strptime(f"{date_str} {time_24}", "%m-%d-%Y %H:%M")
        return naive.replace(tzinfo=UTC_TZ)
    except (ValueError, TypeError):
        return None


def _parse_ff_time(date_str: str, time_str: str) -> Optional[datetime]:
    """Chuyển date_str (MM-DD-YYYY) + time_str (12h, "5:00pm") từ ET → UTC.

    Trả về datetime với tzinfo=UTC, hoặc None nếu không parse được.
    """
    if not date_str or not time_str:
        return None

    try:
        # Chuyển 12h → 24h
        time_24 = _to_24h(time_str.strip())
        if not time_24:
            return None

        # Ghép date + time ở ET
        naive_et = datetime.strptime(f"{date_str} {time_24}", "%m-%d-%Y %H:%M")
        aware_et = naive_et.replace(tzinfo=ET_TZ)
        aware_utc = aware_et.astimezone(UTC_TZ)
        return aware_utc
    except (ValueError, TypeError):
        return None


def _to_24h(t12: str) -> Optional[str]:
    """Chuyển '5:00pm' → '17:00', '12:30am' → '00:30'."""
    t12 = t12.strip().lower()
    try:
        # Regex: "5:00pm" or "5pm" (không có phút)
        m = re.match(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", t12)
        if not m:
            return None
        hour = int(m.group(1))
        minute = m.group(2) or "00"
        ampm = m.group(3)
        if ampm == "pm" and hour < 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute}"
    except (ValueError, TypeError):
        return None


def _clean_value(val: Any) -> Optional[str]:
    """Làm sạch giá trị: None, rỗng, 'Nonfarm' → sạch string hoặc None."""
    if val is None:
        return None
    s = str(val).strip()
    if not s or s in ("", "N/A", "n/a", "Nonfarm"):
        return None
    return s


def _dt_key(dt: Any) -> float:
    """Sort key an toàn cho datetime: epoch seconds, None → -inf."""
    if isinstance(dt, datetime):
        try:
            return dt.timestamp()
        except (ValueError, OSError, OverflowError):
            return float("-inf")
    return float("-inf")


# ═══════════════════════════════════════════════════════════════════════════════
# 4.  filter_usd_events(events)
# ═══════════════════════════════════════════════════════════════════════════════
def filter_usd_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Lọc events có currency == 'USD' (không phân biệt hoa thường),
    impact High hoặc Medium.

    Trả list đã sắp theo time_utc.
    """
    filtered = [
        ev
        for ev in events
        if ev.get("currency", "").upper() == "USD"
        and ev.get("impact", "") in ("High", "Medium")
    ]
    filtered.sort(key=lambda e: _dt_key(e.get("time_utc")))
    return filtered


# ═══════════════════════════════════════════════════════════════════════════════
# 5.  events_in_window(events, minutes=30)
# ═══════════════════════════════════════════════════════════════════════════════
def events_in_window(
    events: list[dict[str, Any]], minutes: int = 30
) -> list[dict[str, Any]]:
    """Lọc events diễn ra trong khoảng [now - minutes, now + minutes] (UTC).

    Trả list đã sắp theo time_utc.
    """
    now = datetime.now(UTC_TZ)
    start = now - timedelta(minutes=minutes)
    end = now + timedelta(minutes=minutes)

    filtered = [
        ev
        for ev in events
        if isinstance(ev.get("time_utc"), datetime)
        and start <= ev["time_utc"] <= end
    ]
    filtered.sort(key=lambda e: _dt_key(e.get("time_utc")))
    return filtered


# ═══════════════════════════════════════════════════════════════════════════════
#  TEST / DEMO
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("  TNVGold — forex_data.py  (TEST MODE)")
    print("=" * 60)

    # Thử lấy lịch thật
    print("\n>>> get_calendar() ...")
    real_events = get_calendar(refresh=False)
    print(f"    → {len(real_events)} events (today UTC)")

    if real_events:
        usd_events = filter_usd_events(real_events)
        print(f"    → USD High/Medium: {len(usd_events)} events")

        # Test events_in_window
        print("\n" + "─" * 60)
        print("events_in_window(usd_events, minutes=120):")
        print("─" * 60)
        window = events_in_window(usd_events, minutes=120)
        print(f"    → {len(window)} events in window")
        for ev in window:
            t = ev.get("time_utc")
            print(
                f"    • {t.strftime('%H:%M') if isinstance(t, datetime) else '??'}"
                f" {ev['title']}"
            )
    else:
        print("    → (không fetch được, dùng dữ liệu giả lập)")
        now = datetime.now(UTC_TZ)
        mock_events = [
            {
                "time_utc": now + timedelta(hours=2),
                "currency": "USD",
                "impact": "High",
                "title": "Non-Farm Employment Change",
                "forecast": "180K",
                "previous": "142K",
                "actual": None,
            },
            {
                "time_utc": now + timedelta(hours=3, minutes=30),
                "currency": "USD",
                "impact": "High",
                "title": "Chairman Powell Speaks",
                "forecast": None,
                "previous": None,
                "actual": None,
            },
            {
                "time_utc": now + timedelta(hours=1),
                "currency": "USD",
                "impact": "Medium",
                "title": "CB Consumer Confidence",
                "forecast": "104.5",
                "previous": "102.3",
                "actual": None,
            },
        ]
        usd_filtered = filter_usd_events(mock_events)
        print(f"    → USD High/Medium sau filter: {len(usd_filtered)} events")