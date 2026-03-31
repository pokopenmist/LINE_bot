#!/usr/bin/env python3
"""
AI最新情報 LINE配信ボット
直近168時間以内のAI関連ニュースを取得し、LINEへ配信します。

配信方式: LINE Messaging API (Push / Broadcast)
※ LINE Notify は 2025年3月31日にサービス終了しました。
"""

import os
import logging
import argparse
from dotenv import load_dotenv

from news_fetcher import fetch_news
from line_sender import send_push_message, send_broadcast_message, build_news_messages

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

    logger.info(f"AI最新情報を取得中... (過去{hours}時間, 最大{max_items}件)")
    articles = fetch_news(hours=hours, max_items=max_items)
    logger.info(f"{len(articles)} 件のニュースを取得しました。")

    messages = build_news_messages(articles, hours)

    if dry_run:
        print("\n--- DRY RUN: 配信内容プレビュー ---")
        for msg in messages:
            print(msg.get("text", ""))
            print("---")
        return True

    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    if not token:
        logger.error("LINE_CHANNEL_ACCESS_TOKEN が設定されていません。.env を確認してください。")
        return False

    target_id = os.getenv("LINE_TARGET_ID", "").strip()

    if target_id:
        # Push: 特定のユーザー/グループへ送信
        return send_push_message(token, target_id, messages)
    else:
        # Broadcast: 全フォロワーへ送信
        logger.info("LINE_TARGET_ID 未設定のため Broadcast で全フォロワーへ送信します。")
        return send_broadcast_message(token, messages)


def main():
    parser = argparse.ArgumentParser(
        description="AI最新情報をLINEへ配信するボット"
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
        help="毎日実行する時刻（例: '08:00' で毎朝8時に配信）",
    )
    args = parser.parse_args()

    if args.schedule:
        import schedule
        import time

        logger.info(f"スケジュール設定: 毎日 {args.schedule} に配信")
        schedule.every().day.at(args.schedule).do(
            run, hours=args.hours, max_items=args.max_items, dry_run=args.dry_run
        )
        # 起動時に即時実行
        run(hours=args.hours, max_items=args.max_items, dry_run=args.dry_run)
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        success = run(hours=args.hours, max_items=args.max_items, dry_run=args.dry_run)
        exit(0 if success else 1)


if __name__ == "__main__":
    main()
