#!/usr/bin/env python3
"""
forex_format.py — TNVGold Telegram Bot (XAUUSD)
Module format hiển thị lịch kinh tế từ Forex Factory.

Phụ thuộc: forex_data (get_calendar, filter_usd_events, events_in_window, VN_TZ, ET_TZ)
"""

from datetime import datetime
from typing import Any

from forex_data import (
    get_calendar,
    filter_usd_events,
    events_in_window,
    VN_TZ,
    ET_TZ,
)


# ═══════════════════════════════════════════════════════════════════════════════
# 6.  format_news(events, lang="vi")
# ═══════════════════════════════════════════════════════════════════════════════
def format_news(events: list[dict[str, Any]], lang: str = "vi") -> str:
    """Format lịch kinh tế XAUUSD hôm nay dạng Markdown Telegram.

    Args:
        events: list event USD High/Medium, đã sắp theo giờ.
        lang:   "vi" (mặc định) hoặc "en".

    Returns:
        Chuỗi Markdown.
    """
    if not events:
        if lang == "en":
            return "📭 No USD High/Medium events today."
        return "📭 Không có sự kiện USD High/Medium hôm nay."

    high = [e for e in events if e.get("impact") == "High"]
    medium = [e for e in events if e.get("impact") == "Medium"]

    # Template strings — bilingual
    if lang == "en":
        header_title = "ECONOMIC CALENDAR XAUUSD (TODAY)"
        header_source = "_Source: Forex Factory_"
        high_header = "🔴 *HIGH IMPACT*"
        medium_header = "🟡 *MEDIUM IMPACT*"
        forecast_label = "Forecast:"
        previous_label = "Previous:"
        line_sep = "━" * 12
    else:
        header_title = "LỊCH KINH TẾ XAUUSD (HÔM NAY)"
        header_source = "_Nguồn: Forex Factory_"
        high_header = "🔴 *HIGH IMPACT*"
        medium_header = "🟡 *MEDIUM IMPACT*"
        forecast_label = "Dự báo:"
        previous_label = "Trước đó:"
        line_sep = "━" * 12

    lines: list[str] = [
        f"⏰ *{header_title}*",
        header_source,
        "",
    ]

    def _is_speech(title: str) -> bool:
        """Kiểm tra event có phải phát biểu / speech không."""
        t = title.lower()
        keywords = [
            "speech", "phát biểu", "bostic", "williams", "powell",
            "fed", "fomc", "testimony", "bullard", "kaplan", "harker",
            "mester", "rosengren", "evans", "brainard", "quarles",
            "clarida", "waller", "barr", "jefferson", "cook", "kugler",
            "goolsbee", "collins", "schmid", "musalem", "logan",
            "barkin", "daly", "hammack", "beige book",
        ]
        return any(kw in t for kw in keywords)

    def _format_event(ev: dict[str, Any], indent: int = 0) -> list[str]:
        t = ev.get("time_utc")
        # Chuyển từ UTC → giờ VN
        if isinstance(t, datetime):
            t_vn = t.astimezone(VN_TZ)
            time_str = t_vn.strftime("%H:%M")
        else:
            time_str = "??:??"
        title = ev.get("title", "")
        currency = ev.get("currency", "")
        flag = "🇺🇸" if currency.upper() == "USD" else ""

        out: list[str] = []
        prefix = " " * indent

        # Dòng event
        out.append(f"{prefix}• `{time_str}` {flag} *{title}*")

        forecast = ev.get("forecast")
        previous = ev.get("previous")
        parts: list[str] = []
        if forecast:
            parts.append(f"{forecast_label} `{forecast}`")
        if previous:
            parts.append(f"{previous_label} `{previous}`")
        if parts:
            out.append(f"{prefix}  - {' | '.join(parts)}")

        return out

    # High impact
    if high:
        lines.append(line_sep)
        lines.append(high_header)
        for ev in high:
            lines.extend(_format_event(ev))
        lines.append("")

    # Medium impact
    if medium:
        lines.append(line_sep)
        lines.append(medium_header)
        for ev in medium:
            lines.extend(_format_event(ev))
        lines.append("")

    return "\n".join(lines).strip()


# ═══════════════════════════════════════════════════════════════════════════════
# 6b.  format_news_alert(events, lang) — gộp nhiều sự kiện sắp tới thành 1 tin
# ═══════════════════════════════════════════════════════════════════════════════
def format_news_alert(events: list[dict[str, Any]], lang: str = "vi",
                      minutes_left: int | None = None) -> str:
    """Gộp các sự kiện USD High/Medium sắp tới thành 1 tin cảnh báo duy nhất.

    Dạng giống /news (HIGH IMPACT / MEDIUM IMPACT, giờ VN) nhưng thêm khối
    💡 Khuyến nghị từ AI ở cuối. Dùng cho cảnh báo chủ động (check_news_alerts)
    để thay thế việc gửi 1 tin cho mỗi sự kiện.

    Args:
        events: list event USD High/Medium sắp diễn ra (đã sắp theo giờ).
        lang:   "vi" hoặc "en".
        minutes_left: số phút còn lại đến sự kiện đầu tiên (None = bỏ qua).

    Returns:
        Chuỗi Markdown 1 tin duy nhất.
    """
    if not events:
        if lang == "en":
            return "📭 No upcoming USD High/Medium events."
        return "📭 Không có sự kiện USD High/Medium sắp tới."

    high = [e for e in events if e.get("impact") == "High"]
    medium = [e for e in events if e.get("impact") == "Medium"]

    brand = "(by @TNVGold_bot)"
    if lang == "en":
        header_title = f"UPCOMING ECONOMIC CALENDAR (XAUUSD) {brand}"
        header_source = "_Source: Forex Factory_"
        if minutes_left is not None:
            header_source = f"_Source: Forex Factory_ | _~{minutes_left} min left_"
        high_header = "🔴 *HIGH IMPACT*"
        medium_header = "🟡 *MEDIUM IMPACT*"
        forecast_label = "Forecast:"
        previous_label = "Previous:"
        advice_header = "Recommendation from AI:"
        advice_pause = "Advise pausing current M5/M15 Scalp setups."
        advice_wait = (
            "Wait 10-15 min after news for the market to "
            "absorb, then look for new entries."
        )
        line_sep = "━" * 12
    else:
        header_title = f"CẢNH BÁO LỊCH KINH TẾ SẮP TỚI (XAUUSD) {brand}"
        header_source = "_Nguồn: Forex Factory_"
        if minutes_left is not None:
            header_source = f"_Nguồn: Forex Factory_ | _Còn ~{minutes_left} phút nữa_"
        high_header = "🔴 *HIGH IMPACT*"
        medium_header = "🟡 *MEDIUM IMPACT*"
        forecast_label = "Dự báo:"
        previous_label = "Trước đó:"
        advice_header = "Khuyến nghị từ AI:"
        advice_pause = "Khuyến cáo tạm ngưng các setup Scalp M5/M15 hiện tại."
        advice_wait = (
            "Chờ thị trường hấp thụ xong tin tức (sau 10-15 phút) "
            "mới tìm điểm vào lệnh mới."
        )
        line_sep = "━" * 12

    lines: list[str] = [
        f"⏰ *{header_title}*",
        header_source,
        "",
    ]

    def _fmt(ev: dict[str, Any], indent: int = 0) -> list[str]:
        t = ev.get("time_utc")
        if isinstance(t, datetime):
            time_str = t.astimezone(VN_TZ).strftime("%H:%M")
        else:
            time_str = "??:??"
        title = ev.get("title", "")
        currency = ev.get("currency", "")
        flag = "🇺🇸" if currency.upper() == "USD" else ""
        prefix = " " * indent

        out = [f"{prefix}• `{time_str}` {flag} *{title}*"]
        parts = []
        if ev.get("forecast"):
            parts.append(f"{forecast_label} `{ev['forecast']}`")
        if ev.get("previous"):
            parts.append(f"{previous_label} `{ev['previous']}`")
        if parts:
            out.append(f"{prefix}  - {' | '.join(parts)}")
        return out

    if high:
        lines.append(line_sep)
        lines.append(high_header)
        for ev in high:
            lines.extend(_fmt(ev))
        lines.append("")

    if medium:
        lines.append(line_sep)
        lines.append(medium_header)
        for ev in medium:
            lines.extend(_fmt(ev))
        lines.append("")

    # Khối khuyến nghị AI (đã yêu cầu: vi | en)
    lines.append(f"💡 *{advice_header}*")
    lines.append(f"• {advice_pause}")
    lines.append(f"• {advice_wait}")

    return "\n".join(lines).strip()


# ═══════════════════════════════════════════════════════════════════════════════
# 7.  format_alert(event, now, lang="vi")
# ═══════════════════════════════════════════════════════════════════════════════
def format_alert(event: dict[str, Any], now: datetime, lang: str = "vi") -> str:
    """Format cảnh báo chủ động cho một event sắp diễn ra.

    Args:
        event: dict event (time_utc, title, currency, impact, …).
        now:   datetime hiện tại UTC.
        lang:  "vi" hoặc "en".

    Returns:
        Chuỗi Markdown cảnh báo.
    """
    t = event.get("time_utc")
    # Chuyển từ UTC → giờ VN
    if isinstance(t, datetime):
        time_str = t.astimezone(VN_TZ).strftime("%H:%M")
    else:
        time_str = "??:??"
    title = event.get("title", "")
    impact = event.get("impact", "Low")
    currency = event.get("currency", "")

    # Tính số phút còn lại
    if isinstance(t, datetime) and isinstance(now, datetime):
        delta = (t - now).total_seconds() / 60.0
        mins_left = max(0, round(delta))
    else:
        mins_left = 0

    # Impact icon & label
    if impact == "High":
        if lang == "en":
            impact_label = "🔴 VERY STRONG (High Impact)"
        else:
            impact_label = "🔴 RẤT MẠNH (High Impact)"
    elif impact == "Medium":
        if lang == "en":
            impact_label = "🟡 MODERATE (Medium Impact)"
        else:
            impact_label = "🟡 TRUNG BÌNH (Medium Impact)"
    else:
        impact_label = "🟢 LOW (Low Impact)"

    # Ngôn ngữ
    if lang == "en":
        title_label = "ECONOMIC CALENDAR ALERT (XAUUSD) (by @TNVGold_bot)"
        time_label = "Time:"
        event_label = "Event:"
        impact_field = "Impact:"
        minutes_suffix = "minutes left"
        advice_header = "Recommendation from AI:"
        advice_pause = "Advise pausing current M5/M15 Scalp setups."
        advice_wait = (
            "Wait 10-15 min after news for the market to "
            "absorb, then look for new entries."
        )
    else:
        title_label = "CẢNH BÁO LỊCH KINH TẾ (XAUUSD) (by @TNVGold_bot)"
        time_label = "Thời gian:"
        event_label = "Sự kiện:"
        impact_field = "Mức độ tác động:"
        minutes_suffix = "phút nữa"
        advice_header = "Khuyến nghị từ AI:"
        advice_pause = "Khuyến cáo tạm ngưng các setup Scalp M5/M15 hiện tại."
        advice_wait = (
            "Chờ thị trường hấp thụ xong tin tức (sau 10-15 phút) "
            "mới tìm điểm vào lệnh mới."
        )

    flag = "🇺🇸" if currency.upper() == "USD" else ""

    if lang == "en":
        time_left_str = f"({mins_left} {minutes_suffix})"
    else:
        time_left_str = f"(Còn {mins_left} {minutes_suffix})"

    return (
        f"🚨 *{title_label}* 🚨\n\n"
        f"⏰ *{time_label}* `{time_str} VN` {time_left_str}\n"
        f"{flag} *{event_label}* {title}\n"
        f"📊 *{impact_field}* {impact_label}\n\n"
        f"💡 *{advice_header}*\n"
        f"• {advice_pause}\n"
        f"• {advice_wait}"
    )