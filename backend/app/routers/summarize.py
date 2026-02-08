"""
要約APIエンドポイント
POST /api/summarize - YouTube動画の字幕を取得し要約を返す
"""

import logging
from fastapi import APIRouter, Depends, HTTPException

from app.models.schemas import SummarizeRequest, SummarizeResponse, ErrorResponse, KeyPointItem
from app.services.youtube import fetch_transcript, fetch_video_title
from app.services.summarizer import SummarizerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["summarize"])


def get_summarizer_service() -> SummarizerService:
    """SummarizerService のファクトリ。FastAPI の Depends で注入する。"""
    return SummarizerService()


@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    responses={
        400: {"model": ErrorResponse, "description": "無効なリクエスト"},
        404: {"model": ErrorResponse, "description": "字幕が見つからない"},
        500: {"model": ErrorResponse, "description": "サーバーエラー"},
    },
    summary="YouTube動画を要約する",
    description="YouTube動画のURLを受け取り、字幕を取得してGroq APIで要約を生成する",
)
async def summarize_video(
    request: SummarizeRequest,
    service: SummarizerService = Depends(get_summarizer_service),
) -> SummarizeResponse:
    """
    YouTube動画の要約エンドポイント

    処理フロー:
    1. 字幕テキストを取得（YouTubeTranscriptError は main の例外ハンドラで HTTP に変換）
    2. 動画タイトルを取得
    3. Groq APIで要約を生成（service は Depends で注入）
    4. 結果を返却
    """
    transcript = await fetch_transcript(
        url=request.url,
        language=request.language,
    )

    # 動画タイトルを取得(要約の手がかりにし、レスポンスでも返す)
    video_title = await fetch_video_title(transcript.video_id)

    # 要約生成（service は DI で渡される）
    timestamped_text = "\n".join(
        f"[{int(seg.start)}] {seg.text}" for seg in transcript.segments
    )
    try:
        result = await service.summarize_transcript(timestamped_text, video_title=video_title or None)
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
    key_point_items = [
        KeyPointItem(text=kp.text, start_seconds=kp.start_seconds)
        for kp in result.key_points
    ]
    return SummarizeResponse(
        video_id=transcript.video_id,
        title=result.title,
        video_title=video_title,
        summary=result.summary,
        key_points=key_point_items,
        topics=result.topics,
        language=transcript.language,
        transcript_length=len(transcript.full_text),
    )
