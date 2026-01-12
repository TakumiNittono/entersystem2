"""
データモデル（Pydantic）
リクエストとレスポンスのデータ構造を定義
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class OnboardingRequest(BaseModel):
    """入社処理リクエストモデル"""
    
    company: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="顧客名",
        examples=["株式会社サンプル"]
    )
    
    task_type: Literal["onboarding"] = Field(
        ...,
        description="タスク種別",
        examples=["onboarding"]
    )
    
    employee_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="従業員名",
        examples=["山田 太郎"]
    )
    
    employment_type: Literal["正社員", "派遣"] = Field(
        ...,
        description="雇用形態",
        examples=["正社員"]
    )
    
    department: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="部署",
        examples=["営業部"]
    )
    
    @field_validator("company", "employee_name", "department")
    @classmethod
    def validate_no_special_chars(cls, v: str) -> str:
        """特殊文字のサニタイズ（基本的なXSS対策）"""
        # HTMLタグをエスケープ
        import html
        return html.escape(v)
    
    @field_validator("employee_name")
    @classmethod
    def validate_employee_name(cls, v: str) -> str:
        """従業員名のバリデーション"""
        v = v.strip()
        if not v:
            raise ValueError("従業員名は必須です")
        return v


class JudgmentResult(BaseModel):
    """判断結果モデル"""
    
    employment_type: Literal["正社員", "派遣"]
    user_type: str  # "標準ユーザー" または "制限ユーザー"
    license_type: str  # "Microsoft 365 E3" または "Microsoft 365 Basic"
    has_expiration: bool  # 有効期限の有無
    expiration_date: Optional[str] = None  # 有効期限（YYYY-MM-DD形式）


class OnboardingResponse(BaseModel):
    """入社処理レスポンスモデル"""
    
    status: Literal["success", "error"] = Field(
        ...,
        description="処理ステータス"
    )
    
    judgment: Optional[str] = Field(
        None,
        description="AI判断結果（文章）"
    )
    
    powershell_command: Optional[str] = Field(
        None,
        description="生成されたPowerShellコマンド"
    )
    
    message: Optional[str] = Field(
        None,
        description="エラーメッセージ（エラー時）"
    )
    
    details: Optional[dict] = Field(
        None,
        description="エラー詳細（エラー時）"
    )


class ErrorResponse(BaseModel):
    """エラーレスポンスモデル"""
    
    status: Literal["error"] = Field(
        ...,
        description="処理ステータス"
    )
    
    message: str = Field(
        ...,
        description="エラーメッセージ"
    )
    
    details: Optional[dict] = Field(
        None,
        description="エラー詳細"
    )

