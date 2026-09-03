#!/usr/bin/env python3
"""
forex_factory.py — TNVGold Telegram Bot (XAUUSD)
Re-export từ 2 module mới: forex_data (data) + forex_format (format).

Giữ nguyên API cũ để mọi module khác import
`from forex_factory import ...` vẫn hoạt động.
"""

from forex_data import *  # noqa: F401,F403  (get_calendar, filter_usd_events, events_in_window, ...)
from forex_format import *  # noqa: F401,F403  (format_news, format_news_alert, format_alert)
