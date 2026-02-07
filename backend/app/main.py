"""
FastAPI アプリケーションのエントリポイント
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# backend/.env を確実に読み込む(どこから起動しても動くように)
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_backend_dir, ".env"))

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

# CORS設定(本番では CORS_ORIGINS にフロントのURLを指定。前後スペース・改行は自動で除去)
_cors_origins = (os.getenv("CORS_ORIGINS") or "*").strip()
allow_origins = [o.strip() for o in _cors_origins.split(",") if o.strip()] or ["*"]
logger.info("CORS allow_origins: %s", allow_origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
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
