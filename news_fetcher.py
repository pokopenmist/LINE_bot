import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import time
import logging

logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))

# RSS feed sources for pachinko industry news
RSS_SOURCES = [
    {
        "name": "Googleニュース - パチンコ",
        "url": "https://news.google.com/rss/search?q=パチンコ+業界&hl=ja&gl=JP&ceid=JP:ja",
    },
    {
        "name": "Googleニュース - パチスロ",
        "url": "https://news.google.com/rss/search?q=パチスロ+業界&hl=ja&gl=JP&ceid=JP:ja",
    },
    {
        "name": "Googleニュース - 遊技機",
        "url": "https://news.google.com/rss/search?q=遊技機+新台&hl=ja&gl=JP&ceid=JP:ja",
    },
    {
        "name": "情報島",
        "url": "https://johojima.com/feed",
    },
    {
        "name": "グリーンべると",
        "url": "https://green-verde.com/feed",
    },
]


def parse_entry_date(entry) -> datetime | None:
    """Parse the publication date from a feed entry."""
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def fetch_news(hours: int = 24, max_items: int = 10) -> list[dict]:
    """
    Fetch pachinko industry news published within the last `hours` hours.
    Returns a list of dicts: {title, url, source, published_at}
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    seen_urls: set[str] = set()
    articles: list[dict] = []

    for source in RSS_SOURCES:
        try:
            logger.info(f"Fetching from {source['name']} ...")
            feed = feedparser.parse(source["url"])
            if feed.bozo and not feed.entries:
                logger.warning(f"  Feed parse warning for {source['name']}: {feed.bozo_exception}")
                continue

            for entry in feed.entries:
                pub_dt = parse_entry_date(entry)

                # If date is missing, include entry (can't filter)
                if pub_dt is not None and pub_dt < cutoff:
                    continue

                url = getattr(entry, "link", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                title = getattr(entry, "title", "(タイトルなし)")
                pub_str = (
                    pub_dt.astimezone(JST).strftime("%Y/%m/%d %H:%M")
                    if pub_dt
                    else "日時不明"
                )

                articles.append(
                    {
                        "title": title,
                        "url": url,
                        "source": source["name"],
                        "published_at": pub_str,
                        "published_dt": pub_dt,
                    }
                )

        except Exception as e:
            logger.error(f"Error fetching {source['name']}: {e}")

    # Sort by date (newest first), put None-date entries at the end
    articles.sort(
        key=lambda a: a["published_dt"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    return articles[:max_items]
