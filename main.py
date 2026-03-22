#!/usr/bin/env python3
"""
パチンコ業界ニュース LINE配信ボット
直近24時間以内のパチンコ/パチスロ関連ニュースを取得し、LINEへ配信します。
"""

import os
import logging
import argparse
from dotenv import load_dotenv

from news_fetcher import fetch_news
from line_sender import (
    send_via_notify,
    send_via_messaging_api,
    build_news_message_notify,
    build_news_messages_api,
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run(hours: int = None, max_items: int = None, dry_run: bool = False):
    """Fetch news and deliver to LINE."""
    hours = hours or int(os.getenv("NEWS_HOURS", "24"))
    max_items = max_items or int(os.getenv("MAX_NEWS_ITEMS", "10"))
    delivery_method = os.getenv("LINE_DELIVERY_METHOD", "notify").lower()

    logger.info(f"パチンコ業界ニュースを取得中... (過去{hours}時間, 最大{max_items}件)")
    articles = fetch_news(hours=hours, max_items=max_items)
    logger.info(f"{len(articles)} 件のニュースを取得しました。")

    if dry_run:
        print("\n--- DRY RUN: 配信内容プレビュー ---")
        msg = build_news_message_notify(articles, hours)
        print(msg)
        return True

    if delivery_method == "notify":
        token = os.getenv("LINE_NOTIFY_TOKEN")
        if not token:
            logger.error("LINE_NOTIFY_TOKEN が設定されていません。.env を確認してください。")
            return False
        message = build_news_message_notify(articles, hours)
        return send_via_notify(token, message)

    elif delivery_method == "messaging_api":
        token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        target_id = os.getenv("LINE_TARGET_ID")
        if not token or not target_id:
            logger.error(
                "LINE_CHANNEL_ACCESS_TOKEN または LINE_TARGET_ID が設定されていません。"
            )
            return False
        messages = build_news_messages_api(articles, hours)
        return send_via_messaging_api(token, target_id, messages)

    else:
        logger.error(f"不明な配信方式: {delivery_method}. 'notify' または 'messaging_api' を指定してください。")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="パチンコ業界ニュースをLINEへ配信するボット"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=None,
        help="取得対象の時間範囲（デフォルト: 24時間）",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=None,
        help="最大配信件数（デフォルト: 10件）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="LINEに送信せず、配信内容をコンソールに表示する",
    )
    parser.add_argument(
        "--schedule",
        type=str,
        default=None,
        help="定期実行の間隔（例: '08:00' で毎朝8時に実行）",
    )
    args = parser.parse_args()

    if args.schedule:
        import schedule
        import time

        logger.info(f"スケジュール設定: 毎日 {args.schedule} に配信")
        schedule.every().day.at(args.schedule).do(
            run, hours=args.hours, max_items=args.max_items, dry_run=args.dry_run
        )
        # Run immediately on start
        run(hours=args.hours, max_items=args.max_items, dry_run=args.dry_run)
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        success = run(hours=args.hours, max_items=args.max_items, dry_run=args.dry_run)
        exit(0 if success else 1)


if __name__ == "__main__":
    main()
