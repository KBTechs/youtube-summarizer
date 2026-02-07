"""
要約APIエンドポイント
POST /api/summarize - YouTube動画の字幕を取得し要約を返す
"""

import logging
from fastapi import APIRouter, HTTPException

from app.models.schemas import SummarizeRequest, SummarizeResponse, ErrorResponse
from app.services.youtube import fetch_transcript, YouTubeTranscriptError
from app.services.summarizer import SummarizerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["summarize"])


@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "無効なリクエスト"},
        404: {"model": ErrorResponse, "description": "字幕が見つからない"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
    summary="YouTube動画を要約する",
    description="YouTube動画のURLを受け取り、字幕を取得してClaude APIで要約を生成する",
)
async def summarize_video(request: SummarizeRequest) -> SummarizeResponse:
    """
    YouTube動画の要約エンドポイント

    処理フロー:
    1. URLから動画IDを抽出
    2. 字幕テキストを取得
    3. Claude APIで要約を生成
    4. 結果を返却
    """
    # ステップ1-2: 字幕を取得
    try:
        transcript = await fetch_transcript(
            url=request.url,
            language=request.language,
        )
    except YouTubeTranscriptError as e:
        logger.warning(f"字幕取得エラー: {e.message}")
        status_code = 404 if e.error_code == "NO_TRANSCRIPT" else 400
        raise HTTPException(
            status_code=status_code,
            detail={"detail": e.message, "error_code": e.error_code},
        )

    # ステップ3: Claude APIで要約を生成
    try:
        service = SummarizerService()
        result = await service.summarize_transcript(transcript.full_text)
    except Exception as e:
        logger.error(f"要約生成エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "detail": "要約の生成に失敗しました",
                "error_code": "SUMMARIZE_FAILED",
            },
        )

    # ステップ4: レスポンスを返却
    return SummarizeResponse(
        video_id=transcript.video_id,
        title=result.title,
        summary=result.summary,
        key_points=result.key_points,
        topics=result.topics,
        language=transcript.language,
        transcript_length=len(transcript.full_text),
    )
