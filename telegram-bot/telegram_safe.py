"""
telegram_safe.py — Helper gửi tin nhắn Telegram an toàn với Markdown.

Mọi module (bot, scheduler, forex_factory, main...) nên dùng
các hàm này thay vì gọi trực tiếp app.bot.send_message / reply_text.

Các hàm này:
- Tự động escape ký tự Markdown lẻ (tránh lỗi "Can't parse entities")
- Bảo vệ cặp italic `_..._` (giữ nguyên để in nghiêng)
- Bảo vệ username @TNVGold_bot (coi là text, không phải Markdown)
- Fallback về plain text nếu Markdown fail
"""
import logging
import re

log = logging.getLogger("telegram_safe")

# Username bot có `_` — bảo vệ để _escape_md không đếm nhầm là Markdown
_TNV_BRAND = "@TNVGold_bot"
_TNV_PLACEHOLDER = "@TNVGOLDBOTPLACEHOLDER"
# Khi khôi phục, dùng LINK Markdown — hiển thị @TNVGold_bot, click được,
# KHÔNG có ký tự _ trong cú pháp Markdown → không bao giờ lỗi parse/escape thô.
_TNV_BRAND_LINK = "[@TNVGold_bot](https://t.me/TNVGold_bot)"


def escape_md(text: str) -> str:
    """Escape ký tự Markdown lẻ, GIỮ NGUYÊN cặp italic `_..._`.

    - Bảo vệ `@TNVGold_bot` (thay placeholder trước khi đếm)
    - `*` lẻ → escape
    - `_` lẻ sau khi loại username → escape (trừ cặp italic)
    """
    if not text:
        return text

    # 1. Bảo vệ username
    text = text.replace(_TNV_BRAND, _TNV_PLACEHOLDER)

    # 2. Đếm `_` còn lại
    count = text.count("_")

    if count == 0:
        # Không có `_` nào → chỉ escape * lẻ
        text = text.replace(_TNV_PLACEHOLDER, _TNV_BRAND_LINK)
        if text.count("*") % 2 != 0:
            text = text.replace("*", "\\*")
        return text

    if count % 2 == 0:
        # Đủ cặp → giữ nguyên, chỉ escape * lẻ
        text = text.replace(_TNV_PLACEHOLDER, _TNV_BRAND_LINK)
        if text.count("*") % 2 != 0:
            text = text.replace("*", "\\*")
        return text

    # Lẻ → tìm cặp italic `_..._` ở cuối, escape các `_` thừa
    italic_pairs = re.findall(r"_\b[^\n_]*\b_", text)
    protected = []
    for i, p in enumerate(italic_pairs):
        placeholder = f"@ITALICPLACEHOLDER{i}@"
        text = text.replace(p, placeholder, 1)
        protected.append((placeholder, p))

    # Escape tất cả `_` còn lại (lẻ, thừa)
    text = text.replace("_", "\\_")

    # Khôi phục italic + username
    for placeholder, original in protected:
        text = text.replace(placeholder, original)
    text = text.replace(_TNV_PLACEHOLDER, _TNV_BRAND_LINK)

    # Escape * lẻ
    if text.count("*") % 2 != 0:
        text = text.replace("*", "\\*")

    return text


async def send(bot, chat_id: int, text: str, parse_mode="Markdown", **kwargs):
    """Gửi message an toàn với Markdown."""
    safe = escape_md(text)
    try:
        return await bot.send_message(
            chat_id=chat_id, text=safe, parse_mode=parse_mode, **kwargs
        )
    except Exception as e:
        log.warning("Send Markdown lỗi: %s — thử plain", e)
        try:
            return await bot.send_message(chat_id=chat_id, text=text, **kwargs)
        except Exception as e2:
            log.error("Send lỗi hoàn toàn: %s", e2)
            return None


async def edit(query, text: str, parse_mode="Markdown", **kwargs):
    """Edit message an toàn (dùng cho inline keyboard callback)."""
    safe = escape_md(text)
    try:
        return await query.edit_message_text(safe, parse_mode=parse_mode, **kwargs)
    except Exception as e:
        log.warning("Edit Markdown lỗi: %s — thử plain", e)
        try:
            return await query.edit_message_text(text, **kwargs)
        except Exception as e2:
            log.error("Edit lỗi hoàn toàn: %s", e2)
            return None
