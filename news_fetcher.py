import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))

# RSS feed sources for AI latest news
RSS_SOURCES = [
    {
        "name": "Googleニュース - AI最新情報",
        "url": "https://news.google.com/rss/search?q={}&hl=ja&gl=JP&ceid=JP:ja".format(
            quote("AI 人工知能 最新")
        ),
    },
    {
        "name": "Googleニュース - 生成AI",
        "url": "https://news.google.com/rss/search?q={}&hl=ja&gl=JP&ceid=JP:ja".format(
            quote("生成AI LLM")
        ),
    },
    {
        "name": "Googleニュース - ChatGPT Claude Gemini",
        "url": "https://news.google.com/rss/search?q={}&hl=ja&gl=JP&ceid=JP:ja".format(
            quote("ChatGPT OR Claude OR Gemini")
        ),
    },
    {
        "name": "TechCrunch Japan",
        "url": "https://jp.techcrunch.com/feed/",
    },
    {
        "name": "MIT Technology Review Japan",
        "url": "https://www.technologyreview.jp/feed/",
    },
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AINewsBot/1.0)"
}


def parse_rfc2822_date(date_str: str) -> datetime | None:
    """Parse RFC 2822 date string (used in RSS <pubDate>)."""
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str.strip())
    except Exception:
        return None


def parse_rss_feed(xml_text: str, source_name: str) -> list[dict]:
    """Parse RSS/Atom XML and return list of article dicts."""
    articles = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.warning(f"XML parse error for {source_name}: {e}")
        return articles

    # RSS 2.0
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    items = root.findall(".//item")

    # Atom feed fallback
    if not items:
        items = root.findall(".//atom:entry", ns)

    for item in items:
        # Title
        title_el = item.find("title")
        title = (title_el.text or "").strip() if title_el is not None else "(タイトルなし)"

        # Link
        link_el = item.find("link")
        if link_el is not None:
            url = (link_el.text or "").strip()
        else:
            # Atom <link href="...">
            link_el = item.find("atom:link", ns)
            url = link_el.get("href", "") if link_el is not None else ""

        # Publication date
        pub_dt = None
        for tag in ("pubDate", "published", "updated", "dc:date"):
            el = item.find(tag)
            if el is not None and el.text:
                pub_dt = parse_rfc2822_date(el.text)
                if pub_dt:
                    break

        pub_str = (
            pub_dt.astimezone(JST).strftime("%Y/%m/%d %H:%M")
            if pub_dt
            else "日時不明"
        )

        articles.append(
            {
                "title": title,
                "url": url,
                "source": source_name,
                "published_at": pub_str,
                "published_dt": pub_dt,
            }
        )

    return articles


def fetch_news(hours: int = 24, max_items: int = 10) -> list[dict]:
    """
    Fetch AI latest news published within the last `hours` hours.
    Returns a list of dicts: {title, url, source, published_at, published_dt}
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    seen_urls: set[str] = set()
    all_articles: list[dict] = []

    for source in RSS_SOURCES:
        try:
            logger.info(f"取得中: {source['name']} ...")
            resp = requests.get(source["url"], headers=HEADERS, timeout=15)
            resp.raise_for_status()
            # Force UTF-8 for Google News
            resp.encoding = resp.apparent_encoding or "utf-8"

            entries = parse_rss_feed(resp.text, source["name"])
            count = 0
            for entry in entries:
                pub_dt = entry["published_dt"]

                # Filter by recency
                if pub_dt is not None and pub_dt < cutoff:
                    continue

                url = entry["url"]
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)

                all_articles.append(entry)
                count += 1

            logger.info(f"  -> {count} 件取得")

        except requests.RequestException as e:
            logger.error(f"通信エラー ({source['name']}): {e}")
        except Exception as e:
            logger.error(f"エラー ({source['name']}): {e}")

    # Sort newest first; entries without date go to end
    all_articles.sort(
        key=lambda a: a["published_dt"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    return all_articles[:max_items]
