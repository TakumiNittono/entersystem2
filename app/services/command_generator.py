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
    
    # テンプレートファイル名（Entra ID用のみ）
    TEMPLATE_ENTRA = "create_entra_user_with_license.ps1"  # Entra ID用（統一）
    
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
        PowerShellコマンドを生成する（Entra ID用、AI判断結果に基づく）
        
        Args:
            request_data: リクエストデータ
            judgment: AI判断結果（ライセンス種別を含む）
            
        Returns:
            str: 生成されたPowerShellコマンド（スクリプト実行形式）
        """
        # 変数を準備
        employee_name = request_data.get("employee_name", "")
        company = request_data.get("company", "")
        department = request_data.get("department", "")
        
        # MailNicknameを生成（英数字のみ）
        mail_nickname = CommandGenerator.generate_sam_account_name(employee_name)
        
        # テナントドメインを生成（簡易版）
        company_domain_base = CommandGenerator.generate_company_domain(company)
        # onmicrosoft.com形式に変換
        tenant_domain = f"{company_domain_base.split('.')[0]}.onmicrosoft.com"
        
        # UserPrincipalNameを生成
        user_principal_name = f"{mail_nickname}@{tenant_domain}"
        
        # PowerShellスクリプトの実行コマンドを生成
        script_path = "create_entra_user_with_license.ps1"
        
        # AI判断結果からライセンスSKUを取得
        license_sku = judgment.license_sku
        license_enabled = judgment.license_enabled
        
        # AssignLicenseパラメータの文字列表現（AI判断で常にtrue）
        assign_license_str = "$true" if license_enabled else "$false"
        
        # スクリプト内の変数を設定するコマンドを生成
        command_lines = [
            "# ============================================================================",
            "# Entra ID ユーザー作成スクリプト実行",
            "# 生成日時: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "# AI判断結果に基づいて自動生成されました",
            "# ============================================================================",
            "",
            "# スクリプト内の変数を設定（必要に応じて編集してください）",
            f'$DisplayName = "{employee_name}"',
            f'$MailNickname = "{mail_nickname}"',
            f'$UserPrincipalName = "{user_principal_name}"',
            f'$Department = "{department}"',
            f'$UsageLocation = "JP"',
            f'$InitialPassword = "TempPassword123!"  # 実際のパスワードに変更してください',
            f'$LicenseSkuPartNumber = "{license_sku}"  # AI判断結果: {judgment.license_type}',
            "",
            "# スクリプトファイルのパス（スクリプトと同じディレクトリにある場合）",
            f'$ScriptPath = ".\\{script_path}"',
            "",
            "# ============================================================================",
            "# Dry-run モードで確認（推奨：まずはこちらで実行内容を確認）",
            "# ============================================================================",
            f'& $ScriptPath -DryRun $true -AssignLicense {assign_license_str}',
            "",
            "# ============================================================================",
            "# 実際に実行する場合（上記のDry-runで問題ないことを確認してから）",
            "# ============================================================================",
            f'# & $ScriptPath -DryRun $false -AssignLicense {assign_license_str}',
            "",
            "# ============================================================================",
            "# 注意事項",
            "# ============================================================================",
            "# 1. スクリプトを実行する前に、上記の変数を確認・編集してください",
            "# 2. 特に $InitialPassword は強力なパスワードに変更してください",
            f"# 3. ライセンス: {judgment.license_type} (SKU: {license_sku})",
            "# 4. テナント名（$UserPrincipalName の @ より後）を実際のテナント名に変更してください",
            "# 5. このコマンドは人がWindows PowerShellで実行してください（自動実行されません）"
        ]
        
        return "\n".join(command_lines)

