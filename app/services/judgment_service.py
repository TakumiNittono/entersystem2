"""
判断ロジックサービス
雇用形態に基づいてユーザータイプ、ライセンスタイプを決定する
"""

from datetime import datetime, timedelta
from typing import Dict
from app.models import JudgmentResult


class JudgmentService:
    """判断ロジックを実装するサービス（AI判断のみ）"""
    
    # 判断ルール定義（固定ルール）
    JUDGMENT_RULES = {
        "正社員": {
            "user_type": "標準ユーザー",
            "license_type": "Microsoft 365 E3",
            "license_sku": "ENTERPRISEPACK",
            "has_expiration": False
        },
        "派遣": {
            "user_type": "制限ユーザー",
            "license_type": "Microsoft 365 Basic",
            "license_sku": "BASICPACK",
            "has_expiration": True
        }
    }
    
    @staticmethod
    def judge(request_data: Dict) -> JudgmentResult:
        """
        雇用形態に基づいて判断を行う
        
        Args:
            request_data: リクエストデータ（辞書形式）
            
        Returns:
            JudgmentResult: 判断結果
        """
        employment_type = request_data.get("employment_type")
        
        if employment_type not in JudgmentService.JUDGMENT_RULES:
            raise ValueError(f"不正な雇用形態: {employment_type}")
        
        rule = JudgmentService.JUDGMENT_RULES[employment_type]
        
        # 有効期限の計算（派遣の場合のみ）
        expiration_date = None
        if rule["has_expiration"]:
            # デフォルトで1年後を設定
            expiration_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        
        # UI表示用の説明文を生成
        if employment_type == "正社員":
            explanation = (
                f"このユーザーは【{employment_type}】のため、"
                f"{rule['license_type']}を付与する{rule['user_type']}として作成します。"
            )
        else:  # 派遣
            explanation = (
                f"このユーザーは【{employment_type}】のため、"
                f"{rule['license_type']}を付与する{rule['user_type']}として作成します。"
                f"また、契約終了日（{expiration_date}）に有効期限を設定します。"
            )
        
        return JudgmentResult(
            employment_type=employment_type,
            user_type=rule["user_type"],
            license_type=rule["license_type"],
            license_sku=rule["license_sku"],
            license_enabled=True,  # AI判断では常にライセンスを付与
            has_expiration=rule["has_expiration"],
            expiration_date=expiration_date,
            explanation=explanation
        )
    
    @staticmethod
    def generate_judgment_text(judgment: JudgmentResult) -> str:
        """
        AI判断結果をUI表示用の文章で説明する
        
        Args:
            judgment: 判断結果
            
        Returns:
            str: UI表示用の説明文
        """
        # judgment.explanationをそのまま使用（既にUI表示用に生成済み）
        return judgment.explanation

