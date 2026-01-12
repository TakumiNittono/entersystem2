"""
PowerShellコマンド生成サービス
テンプレートベースでPowerShellコマンドを生成する
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict
from app.models import JudgmentResult


class CommandGenerator:
    """PowerShellコマンド生成クラス"""
    
    # テンプレートディレクトリのパス
    TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates" / "powershell"
    
    # テンプレートファイル名
    TEMPLATE_REGULAR = "onboarding_regular.ps1"  # 正社員用
    TEMPLATE_CONTRACT = "onboarding_contract.ps1"  # 派遣用
    
    @staticmethod
    def generate_sam_account_name(employee_name: str) -> str:
        """
        従業員名からSamAccountNameを生成（簡易版）
        
        Args:
            employee_name: 従業員名（例: "山田 太郎"）
            
        Returns:
            str: SamAccountName（例: "yamada.taro"）
        """
        # 日本語名をローマ字に変換する簡易実装
        # 実際の運用では、より正確なローマ字変換ライブラリを使用することを推奨
        name = employee_name.strip()
        
        # スペースを削除
        name = name.replace(" ", "").replace("　", "")
        
        # 簡易的な変換テーブル（実際の運用ではより完全な変換が必要）
        # ここでは英数字のみを許可し、その他は削除
        name = re.sub(r'[^a-zA-Z0-9]', '', name)
        
        # 小文字に変換
        name = name.lower()
        
        # 空の場合はデフォルト値を返す
        if not name:
            name = "user"
        
        # 最大20文字に制限（Active Directoryの制限）
        name = name[:20]
        
        return name
    
    @staticmethod
    def generate_company_domain(company: str) -> str:
        """
        顧客名からドメイン名を生成
        
        Args:
            company: 顧客名（例: "株式会社サンプル"）
            
        Returns:
            str: ドメイン名（例: "sample.co.jp"）
        """
        # 会社名からドメインを生成する簡易実装
        # 実際の運用では、会社名とドメインのマッピングテーブルを使用することを推奨
        
        # 会社名の前後の「株式会社」「有限会社」などを削除
        domain_base = re.sub(r'^(株式会社|有限会社|合同会社|合資会社|合名会社)', '', company)
        domain_base = re.sub(r'(株式会社|有限会社|合同会社|合資会社|合名会社)$', '', domain_base)
        
        # 英数字以外を削除
        domain_base = re.sub(r'[^a-zA-Z0-9]', '', domain_base)
        
        # 小文字に変換
        domain_base = domain_base.lower()
        
        # 空の場合はデフォルト値を返す
        if not domain_base:
            domain_base = "company"
        
        # ドメイン形式に変換（簡易版: .co.jpを追加）
        return f"{domain_base}.co.jp"
    
    @staticmethod
    def load_template(template_name: str) -> str:
        """
        PowerShellテンプレートを読み込む
        
        Args:
            template_name: テンプレートファイル名
            
        Returns:
            str: テンプレート内容
            
        Raises:
            FileNotFoundError: テンプレートファイルが見つからない場合
        """
        template_path = CommandGenerator.TEMPLATE_DIR / template_name
        
        if not template_path.exists():
            raise FileNotFoundError(f"テンプレートファイルが見つかりません: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def generate_command(
        request_data: Dict,
        judgment: JudgmentResult
    ) -> str:
        """
        PowerShellコマンドを生成する
        
        Args:
            request_data: リクエストデータ
            judgment: 判断結果
            
        Returns:
            str: 生成されたPowerShellコマンド
        """
        # テンプレートを選択
        if judgment.employment_type == "正社員":
            template_name = CommandGenerator.TEMPLATE_REGULAR
        else:  # 派遣
            template_name = CommandGenerator.TEMPLATE_CONTRACT
        
        # テンプレートを読み込む
        template = CommandGenerator.load_template(template_name)
        
        # 変数を準備
        employee_name = request_data.get("employee_name", "")
        company = request_data.get("company", "")
        department = request_data.get("department", "")
        
        # 変数変換
        sam_account_name = CommandGenerator.generate_sam_account_name(employee_name)
        company_domain = CommandGenerator.generate_company_domain(company)
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 変数をマッピング
        variables = {
            "{employee_name}": employee_name,
            "{sam_account_name}": sam_account_name,
            "{company_domain}": company_domain,
            "{department}": department,
            "{generated_at}": generated_at,
        }
        
        # 派遣の場合は有効期限も追加
        if judgment.expiration_date:
            variables["{contract_end_date}"] = judgment.expiration_date
        
        # テンプレート内の変数を置換
        command = template
        for key, value in variables.items():
            command = command.replace(key, str(value))
        
        return command

