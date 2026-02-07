# YouTube Summarizer

YouTube 動画の字幕を取得し、Groq（LLM）で要約を生成するアプリです。

- **バックエンド**: FastAPI（Python）
- **フロントエンド**: Flutter（Web / macOS 対応）

---

## 主な機能

- YouTube URL を入力して要約を取得
- キーポイントに**動画内の時刻**を表示し、タップでその位置から再生
- 要約結果の**履歴**を保持（セッション内）
- サムネイルタップで動画を開く

---

## 技術スタック

| 層 | 技術 |
|----|------|
| API | FastAPI, Pydantic |
| 要約 | Groq API（llama-3.3-70b-versatile） |
| 字幕取得 | youtube-transcript-api |
| フロント | Flutter, Riverpod |
| テスト | pytest（バックエンド） |

---

## セットアップと起動

### 前提

- Python 3.11+
- Flutter SDK
- [Groq](https://console.groq.com/keys) の API キー（無料枠あり）

### 1. バックエンド

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env の GROQ_API_KEY を設定
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. フロントエンド

```bash
cd frontend
flutter pub get
flutter run -d chrome   # または flutter run -d macos
```

### テスト（バックエンド）

```bash
cd backend && source .venv/bin/activate && pytest tests/ -v
```

---

## プロジェクト構成

```
youtube-summarizer/
├── backend/          # FastAPI アプリ
│   ├── app/
│   │   ├── main.py
│   │   ├── models/   # スキーマ
│   │   ├── routers/ # エンドポイント
│   │   └── services/ # 字幕取得・要約
│   └── tests/
├── frontend/         # Flutter アプリ
│   └── lib/
│       ├── screens/
│       ├── providers/
│       ├── services/
│       └── widgets/
└── docs/             # 手順メモ
```

---

## ライセンス

MIT（またはお好みで）

---

## ポートフォリオ用メモ（採用担当者向け）

- **役割**: 設計・実装（要約パイプライン、履歴・時刻付きキーポイント、エラー処理など）
- **見どころ**: バックエンドとフロントの責務分離、要約のチャンク分割、API のテスト
- **デモ**: Groq の API キーが必要です（[console.groq.com](https://console.groq.com/keys) で無料発行）。動かす場合は上記セットアップを参照してください
