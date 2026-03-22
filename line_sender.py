import requests
import logging

logger = logging.getLogger(__name__)

LINE_PUSH_API = "https://api.line.me/v2/bot/message/push"
LINE_BROADCAST_API = "https://api.line.me/v2/bot/message/broadcast"


def send_push_message(token: str, target_id: str, messages: list[dict]) -> bool:
    """Send messages to a specific user/group via LINE Messaging API (Push Message)."""
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
            logger.info("LINE Messaging API (Push): 送信成功")
            return True
        else:
            logger.error(f"LINE Messaging API エラー: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        logger.error(f"LINE Messaging API 例外: {e}")
        return False


def send_broadcast_message(token: str, messages: list[dict]) -> bool:
    """Broadcast messages to all friends via LINE Messaging API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {"messages": messages}
    try:
        resp = requests.post(LINE_BROADCAST_API, headers=headers, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info("LINE Messaging API (Broadcast): 送信成功")
            return True
        else:
            logger.error(f"LINE Messaging API (Broadcast) エラー: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        logger.error(f"LINE Messaging API (Broadcast) 例外: {e}")
        return False


def build_news_messages(articles: list[dict], hours: int) -> list[dict]:
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

    # Build news text chunks
    # LINE Messaging API: max 5 messages per push, max 5000 chars each
    chunk_lines = []
    chunk_messages = []

    for i, a in enumerate(articles, 1):
        entry = (
            f"■ {i}. {a['title']}\n"
            f"📅 {a['published_at']}\n"
            f"出典: {a['source']}\n"
            f"🔗 {a['url']}"
        )
        candidate = "\n\n".join(chunk_lines + [entry])
        if len(candidate) > 4800:
            if chunk_lines:
                chunk_messages.append({"type": "text", "text": "\n\n".join(chunk_lines)})
            chunk_lines = [entry]
        else:
            chunk_lines.append(entry)

    if chunk_lines:
        chunk_messages.append({"type": "text", "text": "\n\n".join(chunk_lines)})

    # Header + up to 4 content messages = max 5
    messages.extend(chunk_messages[:4])
    return messages
