"""
判断ロジックサービス
雇用形態に基づいてユーザータイプ、ライセンスタイプを決定する
"""

from datetime import datetime, timedelta
from typing import Dict
from app.models import JudgmentResult


class JudgmentService:
    """判断ロジックを実装するサービス"""
    
    # 判断ルール定義
    JUDGMENT_RULES = {
        "正社員": {
            "user_type": "標準ユーザー",
            "license_type": "Microsoft 365 E3",
            "has_expiration": False
        },
        "派遣": {
            "user_type": "制限ユーザー",
            "license_type": "Microsoft 365 Basic",
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
        
        return JudgmentResult(
            employment_type=employment_type,
            user_type=rule["user_type"],
            license_type=rule["license_type"],
            has_expiration=rule["has_expiration"],
            expiration_date=expiration_date
        )
    
    @staticmethod
    def generate_judgment_text(judgment: JudgmentResult, assign_license: bool = False) -> str:
        """
        判断結果を文章で説明する
        
        Args:
            judgment: 判断結果
            assign_license: ライセンス付与の有無（デフォルト: False）
            
        Returns:
            str: 判断結果の説明文
        """
        if judgment.employment_type == "正社員":
            base_text = (
                f"このユーザーは正社員のため、{judgment.user_type}として作成します。"
            )
        else:  # 派遣
            base_text = (
                f"このユーザーは派遣社員のため、{judgment.user_type}として作成します。"
                f"また、契約終了日（{judgment.expiration_date}）に有効期限を設定します。"
            )
        
        # ライセンス付与の説明を追加
        if assign_license:
            base_text += f"\n\n{judgment.license_type} ライセンスを付与します。"
        else:
            base_text += "\n\n※ ライセンス付与はスキップされます（このテナントにはライセンスが存在しない想定です）。"
        
        return base_text

