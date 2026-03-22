import os
import requests
import logging

logger = logging.getLogger(__name__)

LINE_NOTIFY_API = "https://notify-api.line.me/api/notify"
LINE_PUSH_API = "https://api.line.me/v2/bot/message/push"


def send_via_notify(token: str, message: str) -> bool:
    """Send a message using LINE Notify."""
    headers = {"Authorization": f"Bearer {token}"}
    data = {"message": message}
    try:
        resp = requests.post(LINE_NOTIFY_API, headers=headers, data=data, timeout=10)
        if resp.status_code == 200:
            logger.info("LINE Notify: sent successfully.")
            return True
        else:
            logger.error(f"LINE Notify error: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        logger.error(f"LINE Notify exception: {e}")
        return False


def send_via_messaging_api(token: str, target_id: str, messages: list[dict]) -> bool:
    """Send messages using LINE Messaging API (Push Message)."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "to": target_id,
        "messages": messages,
    }
    try:
        resp = requests.post(LINE_PUSH_API, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info("LINE Messaging API: sent successfully.")
            return True
        else:
            logger.error(f"LINE Messaging API error: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        logger.error(f"LINE Messaging API exception: {e}")
        return False


def build_news_message_notify(articles: list[dict], hours: int) -> str:
    """Build a LINE Notify message string from articles."""
    if not articles:
        return f"\n【パチンコ業界ニュース】\n過去{hours}時間以内の新着ニュースはありません。"

    lines = [f"\n【パチンコ業界ニュース】直近{hours}時間の新着({len(articles)}件)\n"]
    for i, a in enumerate(articles, 1):
        lines.append(f"■ {i}. {a['title']}")
        lines.append(f"   📅 {a['published_at']}  ({a['source']})")
        lines.append(f"   🔗 {a['url']}")
        lines.append("")
    return "\n".join(lines)


def build_news_messages_api(articles: list[dict], hours: int) -> list[dict]:
    """Build LINE Messaging API message objects from articles."""
    if not articles:
        return [
            {
                "type": "text",
                "text": f"【パチンコ業界ニュース】\n過去{hours}時間以内の新着ニュースはありません。",
            }
        ]

    # Header message
    messages = [
        {
            "type": "text",
            "text": f"【パチンコ業界ニュース】\n直近{hours}時間の新着 {len(articles)}件",
        }
    ]

    # Build news text (LINE API allows up to 5 messages per call, max 5000 chars each)
    chunk_lines = []
    chunk_messages = []

    for i, a in enumerate(articles, 1):
        entry = f"■ {i}. {a['title']}\n📅 {a['published_at']}\n出典: {a['source']}\n🔗 {a['url']}"
        # Check if adding this entry exceeds 4800 chars
        current_text = "\n\n".join(chunk_lines + [entry])
        if len(current_text) > 4800:
            if chunk_lines:
                chunk_messages.append({"type": "text", "text": "\n\n".join(chunk_lines)})
            chunk_lines = [entry]
        else:
            chunk_lines.append(entry)

    if chunk_lines:
        chunk_messages.append({"type": "text", "text": "\n\n".join(chunk_lines)})

    # LINE API allows max 5 messages per push
    messages.extend(chunk_messages[:4])  # header + up to 4 content messages
    return messages
