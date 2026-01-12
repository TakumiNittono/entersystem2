"""
設定管理モジュール
環境変数から設定を読み込み、アプリケーション全体で使用する
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # OpenAI API設定
    openai_api_key: str = Field(..., description="OpenAI APIキー")
    openai_model: str = Field(default="gpt-4", description="使用するOpenAIモデル")
    
    # アプリケーション設定
    app_name: str = Field(default="BPO業務自動化AIデモシステム")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    
    # サーバー設定
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    
    # ログ設定
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# グローバル設定インスタンス
settings = Settings()

