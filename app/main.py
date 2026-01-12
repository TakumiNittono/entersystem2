"""
FastAPIアプリケーション
BPO向け業務自動化AIデモシステムのメインアプリケーション
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.models import OnboardingRequest, OnboardingResponse, ErrorResponse
from app.services.judgment_service import JudgmentService
from app.services.command_generator import CommandGenerator

# ロガーの設定
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時の処理
    logger.info(f"{settings.app_name} v{settings.app_version} を起動しました")
    logger.info(f"ログレベル: {settings.log_level}")
    logger.info(f"OpenAIモデル: {settings.openai_model}")
    yield
    # 終了時の処理
    logger.info(f"{settings.app_name} を終了しました")


# FastAPIアプリケーションの初期化
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="BPO向け業務自動化AIデモシステム - 入社処理のPowerShellコマンド生成",
    lifespan=lifespan
)

# テンプレートと静的ファイルの設定
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP例外のハンドラー"""
    logger.error(f"HTTPエラー {exc.status_code}: {exc.detail}")
    return {
        "status": "error",
        "message": exc.detail,
        "status_code": exc.status_code
    }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """バリデーション例外のハンドラー"""
    logger.error(f"バリデーションエラー: {exc.errors()}")
    return {
        "status": "error",
        "message": "入力値の検証に失敗しました",
        "details": exc.errors()
    }


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """一般的な例外のハンドラー"""
    logger.exception(f"予期しないエラーが発生しました: {str(exc)}")
    return {
        "status": "error",
        "message": "サーバー内部エラーが発生しました"
    }


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """ルートエンドポイント（入力フォーム）"""
    logger.info("ルートエンドポイントにアクセス")
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "version": settings.app_version
    }


@app.post("/api/onboarding", response_model=OnboardingResponse)
async def create_onboarding(request: OnboardingRequest):
    """
    入社処理のPowerShellコマンドを生成するエンドポイント
    
    Args:
        request: 入社処理リクエスト
        
    Returns:
        OnboardingResponse: 判断結果とPowerShellコマンド
    """
    try:
        # リクエストデータをログ出力
        request_dict = request.model_dump()
        logger.info(f"入力受信: {request_dict}")
        
        # 判断ロジックの実行
        judgment = JudgmentService.judge(request_dict)
        logger.info(
            f"判断結果: {judgment.employment_type} -> "
            f"{judgment.user_type} + {judgment.license_type}"
        )
        
        # assign_licenseの値を取得（デフォルトFalse）
        assign_license = request_dict.get("assign_license", False)
        
        # 判断結果の説明文を生成（assign_licenseを含める）
        judgment_text = JudgmentService.generate_judgment_text(judgment, assign_license=assign_license)
        
        # PowerShellコマンドを生成（Entra ID用）
        # 注意: 現在はEntra ID用のコマンド生成を使用
        # オンプレAD用の場合は CommandGenerator.generate_command() を使用
        powershell_command = CommandGenerator.generate_entra_id_command(
            request_dict,
            assign_license=assign_license
        )
        
        logger.info(f"PowerShell生成完了 (AssignLicense: {assign_license})")
        
        return OnboardingResponse(
            status="success",
            judgment=judgment_text,
            powershell_command=powershell_command
        )
        
    except ValueError as e:
        logger.error(f"バリデーションエラー: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"予期しないエラー: {str(e)}")
        raise HTTPException(status_code=500, detail="サーバー内部エラーが発生しました")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

