"""
Pydantic スキーマ定義
リクエスト・レスポンスのバリデーションを担当
"""

from pydantic import BaseModel, Field, field_validator
import re


class SummarizeRequest(BaseModel):
    """要約リクエストのスキーマ"""

    url: str = Field(
        ...,
        description="YouTube動画のURL",
        examples=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
    )
    language: str = Field(
        default="ja",
        description="字幕の言語コード（例: ja, en）",
    )

    @field_validator("url")
    @classmethod
    def validate_youtube_url(cls, v: str) -> str:
        """YouTube URLのバリデーション"""
        youtube_patterns = [
            r"^https?://(www\.)?youtube\.com/watch\?v=[\w-]{11}",
            r"^https?://youtu\.be/[\w-]{11}",
            r"^https?://(www\.)?youtube\.com/shorts/[\w-]{11}",
        ]
        if not any(re.match(pattern, v) for pattern in youtube_patterns):
            raise ValueError("有効なYouTube URLを入力してください")
        return v


class TranscriptSegment(BaseModel):
    """字幕セグメントのスキーマ"""

    text: str = Field(..., description="字幕テキスト")
    start: float = Field(..., description="開始時間（秒）")
    duration: float = Field(..., description="継続時間（秒）")


class TranscriptResult(BaseModel):
    """字幕取得結果のスキーマ"""

    video_id: str = Field(..., description="YouTube動画ID")
    title: str = Field(default="", description="動画タイトル")
    language: str = Field(..., description="字幕の言語コード")
    segments: list[TranscriptSegment] = Field(..., description="字幕セグメントのリスト")
    full_text: str = Field(..., description="結合済み字幕テキスト")


class KeyPointItem(BaseModel):
    """キーポイント1件（任意で開始秒数付き）"""

    text: str = Field(..., description="ポイントの内容")
    start_seconds: int | None = Field(default=None, description="動画内の開始秒数（あれば）")


class SummarizeResponse(BaseModel):
    """要約レスポンスのスキーマ"""

    video_id: str = Field(..., description="YouTube動画ID")
    title: str = Field(default="", description="動画タイトル")
    summary: str = Field(..., description="要約テキスト")
    key_points: list[KeyPointItem] = Field(default_factory=list, description="重要ポイントのリスト（開始秒数付き）")
    topics: list[str] = Field(default_factory=list, description="トピックキーワードのリスト")
    language: str = Field(..., description="字幕の言語コード")
    transcript_length: int = Field(..., description="元の字幕の文字数")


class ErrorResponse(BaseModel):
    """エラーレスポンスのスキーマ"""

    detail: str = Field(..., description="エラーの詳細メッセージ")
    error_code: str = Field(..., description="エラーコード")
