"""
アプリケーション設定（Pydantic Settings）

環境変数を型付きで一元管理。.env や os.environ から自動で読む。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """環境変数から読む設定。未設定時は default が使われる。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # CORS 許可オリジン（カンマ区切り）。未設定時は "*"
    cors_origins: str = "*"

    @property
    def allow_origins_list(self) -> list[str]:
        """CORS に渡すオリジンリスト。前後空白は除去。空なら ["*"]。"""
        parts = [s.strip() for s in self.cors_origins.split(",") if s.strip()]
        return parts if parts else ["*"]
