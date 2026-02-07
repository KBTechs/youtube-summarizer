"""
FastAPI アプリケーションのエントリポイント
"""

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# .env を読み込み（ANTHROPIC_API_KEY 等を os.environ に載せる）
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import summarize

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    logger.info("YouTube Summarizer API を起動しました")
    yield
    logger.info("YouTube Summarizer API を停止しました")


app = FastAPI(
    title="YouTube Summarizer API",
    description="YouTube動画の字幕を取得し、Claude APIで要約を生成するAPI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS設定（Flutter Webからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なオリジンに制限すること
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターを登録
app.include_router(summarize.router)


@app.get("/health", tags=["health"])
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "ok"}
