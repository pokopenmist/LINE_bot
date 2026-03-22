# パチンコ業界ニュース LINE配信ボット

直近24時間以内のパチンコ・パチスロ業界ニュースをRSSフィードから自動収集し、LINEへ配信するPythonボットです。

---

## 概要

- Google ニュースや業界専門サイトのRSSフィードから最新ニュースを取得
- LINE Notify または LINE Messaging API (Push Message) でLINEへ配信
- コマンドライン引数による柔軟な実行オプション
- `--schedule` オプションで指定時刻に毎日自動配信
- Cronジョブによる定期実行にも対応

### 対応ニュースソース

| ソース名 | 説明 |
|---|---|
| Googleニュース - パチンコ | Google ニュース「パチンコ 業界」検索 |
| Googleニュース - パチスロ | Google ニュース「パチスロ 業界」検索 |
| Googleニュース - 遊技機 | Google ニュース「遊技機 新台」検索 |
| 情報島 | パチンコ・パチスロ情報サイト |
| グリーンべると | パチンコ業界専門メディア |

---

## セットアップ方法

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd LINE_bot
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

`.env.example` をコピーして `.env` を作成し、必要な値を設定します。

```bash
cp .env.example .env
```

`.env` を編集してトークン類を設定してください。

```env
# LINE Notify を使う場合
LINE_NOTIFY_TOKEN=your_line_notify_token_here
LINE_DELIVERY_METHOD=notify

# LINE Messaging API を使う場合
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token_here
LINE_TARGET_ID=your_user_or_group_id_here
LINE_DELIVERY_METHOD=messaging_api

# ニュース取得設定
NEWS_HOURS=24
MAX_NEWS_ITEMS=10
```

---

## LINE Notifyトークン取得方法

LINE Notify は個人で簡単に使えるLINE通知サービスです。

1. [LINE Notify 公式サイト](https://notify-bot.line.me/ja/) にアクセスし、LINEアカウントでログイン
2. 右上のユーザー名をクリック → **「マイページ」** へ移動
3. **「トークンを発行する」** をクリック
4. トークン名（例: `パチンコニュース`）を入力
5. 通知先のトークルームを選択（自分のみ通知の場合は「1:1でLINE Notifyから通知を受け取る」）
6. **「発行する」** をクリックし、表示されたトークンをコピー
7. `.env` の `LINE_NOTIFY_TOKEN` に貼り付ける

> 注意: トークンは発行時の一度しか表示されません。必ずコピーして保管してください。

---

## LINE Messaging API設定方法

より高度な配信機能が必要な場合は、LINE Messaging API を使用します。

### チャネルの作成

1. [LINE Developers コンソール](https://developers.line.biz/console/) にアクセスし、LINEアカウントでログイン
2. **「プロバイダーを作成」** からプロバイダーを作成（または既存のプロバイダーを選択）
3. **「チャネルを作成」** → **「Messaging API」** を選択
4. 必要事項（チャネル名、説明など）を入力して作成

### チャネルアクセストークンの取得

1. 作成したチャネルの **「Messaging API設定」** タブを開く
2. **「チャネルアクセストークン（長期）」** の **「発行」** をクリック
3. 表示されたトークンを `.env` の `LINE_CHANNEL_ACCESS_TOKEN` に設定

### ターゲットIDの取得

送信先のユーザーID・グループID・ルームIDを取得します。

**自分のユーザーIDを取得する場合:**
1. Messaging API チャネルと友だちになる（QRコードはチャネル設定ページにあります）
2. チャネルに何かメッセージを送ると、Webhook で `source.userId` が取得できます
3. または LINE Developers コンソールの **「Messaging API設定」** → **「あなたのユーザーID」** を確認

取得したIDを `.env` の `LINE_TARGET_ID` に設定します。

---

## 使い方

### 基本実行（LINEへ配信）

```bash
python main.py
```

### ドライラン（配信内容をコンソールで確認）

実際にLINEへ送信せず、取得したニュースをターミナルで確認できます。

```bash
python main.py --dry-run
```

### 取得時間範囲を指定

過去12時間以内のニュースを取得する場合:

```bash
python main.py --hours 12
```

### 最大配信件数を指定

最大20件まで配信する場合:

```bash
python main.py --max-items 20
```

### 毎日指定時刻に自動配信

毎朝8時に自動配信する場合（プロセスが起動し続けます）:

```bash
python main.py --schedule 08:00
```

### オプションの組み合わせ

```bash
# 過去12時間、最大5件をドライランで確認
python main.py --hours 12 --max-items 5 --dry-run

# 毎朝7時30分に過去24時間のニュース最大15件を配信
python main.py --schedule 07:30 --max-items 15
```

---

## Cronでの定期実行例

`--schedule` オプションを使わず、OS のCronで定期実行することもできます。

### crontab の設定

```bash
crontab -e
```

以下の例を参考に設定してください。

```cron
# 毎朝8時にパチンコ業界ニュースをLINEへ配信
0 8 * * * /usr/bin/python3 /home/user/LINE_bot/main.py >> /home/user/LINE_bot/cron.log 2>&1

# 毎朝8時と夕方18時の1日2回配信（取得範囲を12時間に）
0 8,18 * * * /usr/bin/python3 /home/user/LINE_bot/main.py --hours 12 >> /home/user/LINE_bot/cron.log 2>&1
```

### 仮想環境を使っている場合

```cron
0 8 * * * /home/user/LINE_bot/venv/bin/python /home/user/LINE_bot/main.py >> /home/user/LINE_bot/cron.log 2>&1
```

### ログのローテーション

長期運用時はログが肥大化しないよう、`logrotate` の設定を推奨します。

```
/home/user/LINE_bot/cron.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

---

## ファイル構成

```
LINE_bot/
├── main.py           # エントリーポイント
├── news_fetcher.py   # RSSフィード取得・パース
├── line_sender.py    # LINE送信処理
├── requirements.txt  # 依存パッケージ
├── .env.example      # 環境変数テンプレート
├── .env              # 環境変数（gitignore対象）
└── README.md         # このファイル
```

---

## トラブルシューティング

### ニュースが0件になる

- ネットワーク接続を確認してください
- RSSフィードのURLが有効か確認してください（`--dry-run` で確認可能）
- `NEWS_HOURS` の値を大きくしてみてください（例: `48`）

### LINE Notify でエラーになる

- トークンが正しく設定されているか確認してください
- LINE Notify のトークンが有効か [マイページ](https://notify-bot.line.me/my/) で確認してください

### LINE Messaging API でエラーになる

- `LINE_CHANNEL_ACCESS_TOKEN` と `LINE_TARGET_ID` の両方が設定されているか確認してください
- チャネルアクセストークンが有効期限内か確認してください
- 送信先ユーザーがチャネルと友だちになっているか確認してください
