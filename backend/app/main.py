"""
FastAPI アプリケーションのエントリポイント
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

# backend/.env を先に読む（app 内で getenv が import 時に使われるため）
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from app.config import Settings  # noqa: E402
from app.routers import summarize  # noqa: E402
from app.services.youtube import YouTubeTranscriptError  # noqa: E402

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# 設定は起動時に1回だけ読む
settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    logger.info("YouTube Summarizer API を起動しました")
    yield
    logger.info("YouTube Summarizer API を停止しました")


app = FastAPI(
    title="YouTube Summarizer API",
    description="YouTube動画の字幕を取得し、Groq APIで要約を生成するAPI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS設定（config から取得。本番では CORS_ORIGINS にフロントのURLを指定）
logger.info("CORS allow_origins: %s", settings.allow_origins_list)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ドメイン例外を HTTP レスポンスに変換（ルーターを薄く保つ）
@app.exception_handler(YouTubeTranscriptError)
async def youtube_transcript_error_handler(_, exc: YouTubeTranscriptError):
    status_code = 404 if exc.error_code == "NO_TRANSCRIPT" else 400
    return JSONResponse(
        status_code=status_code,
        content={"detail": {"detail": exc.message, "error_code": exc.error_code}},
    )

# ルーターを登録
app.include_router(summarize.router)


@app.get("/health", tags=["health"])
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "ok"}
