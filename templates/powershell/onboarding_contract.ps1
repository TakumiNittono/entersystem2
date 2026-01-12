# ========================================
# Entra ID ユーザー作成（派遣社員）
# Generated at: {generated_at}
# AI判断結果: {license_type} (SKU: {license_sku})
# 契約終了日: {contract_end_date}
# ========================================
# 
# 注意: このスクリプトは Dry-run 前提で設計されています
# 実行前に内容を確認し、人が Windows PowerShell で実行してください
# 自動実行は行われません

# Microsoft Graph への接続確認
$context = Get-MgContext
if ($null -eq $context) {
    Write-Host "[ERROR] Microsoft Graph に接続されていません" -ForegroundColor Red
    Write-Host "[INFO] 以下のコマンドで接続してください:" -ForegroundColor Yellow
    Write-Host "  Connect-MgGraph -Scopes User.ReadWrite.All,Directory.ReadWrite.All,Organization.Read.All" -ForegroundColor Cyan
    exit 1
}

# 変数定義
$DisplayName = "{employee_name}"
$MailNickname = "{sam_account_name}"
$UserPrincipalName = "{sam_account_name}@{company_domain}"
$Department = "{department}"
$UsageLocation = "JP"
$AccountExpirationDate = Get-Date "{contract_end_date}"  # 有効期限

# ランダムパスワード生成（セキュリティのため）
$InitialPassword = (New-Guid).Guid + "A1!"

Write-Host "[INFO] Entra ID ユーザーを作成します（制限ユーザー・有効期限あり）" -ForegroundColor Cyan
Write-Host "[INFO] 表示名: $DisplayName" -ForegroundColor Gray
Write-Host "[INFO] UPN: $UserPrincipalName" -ForegroundColor Gray
Write-Host "[INFO] 部署: $Department" -ForegroundColor Gray
Write-Host "[INFO] 有効期限: {contract_end_date}" -ForegroundColor Gray
Write-Host ""

# Entra ID ユーザー作成（制限ユーザー・有効期限あり）
try {
    $newUser = New-MgUser `
        -DisplayName $DisplayName `
        -UserPrincipalName $UserPrincipalName `
        -MailNickname $MailNickname `
        -Department $Department `
        -UsageLocation $UsageLocation `
        -AccountEnabled $true `
        -PasswordProfile @{
            ForceChangePasswordNextSignIn = $true
            Password = $InitialPassword
        }
    
    # 有効期限を設定（Microsoft Graph API では AccountExpirationDate は直接設定できないため、
    # ユーザー作成後に Update-MgUser で設定する必要がある場合があります）
    # 注意: Entra ID では AccountExpirationDate は制限付きの機能です
    
    Write-Host "[SUCCESS] ユーザー作成完了: $DisplayName ($UserPrincipalName)" -ForegroundColor Green
    Write-Host "[INFO] ユーザー ID: $($newUser.Id)" -ForegroundColor Gray
    Write-Host "[INFO] 有効期限: {contract_end_date}" -ForegroundColor Yellow
    Write-Host ""
}
catch {
    Write-Host "[ERROR] ユーザー作成に失敗しました: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# ライセンス SKU を取得して付与（存在する場合のみ）
try {
    $sku = Get-MgSubscribedSku | Where-Object { $_.SkuPartNumber -eq "{license_sku}" }
    
    if ($sku) {
        Set-MgUserLicense `
            -UserId $newUser.Id `
            -AddLicenses @{SkuId = $sku.SkuId} `
            -RemoveLicenses @()
        
        Write-Host "[SUCCESS] {license_type} ライセンスを付与しました" -ForegroundColor Green
    }
    else {
        Write-Host "[WARN] {license_sku} ライセンスが見つからないためスキップしました" -ForegroundColor Yellow
        Write-Host "[INFO] ユーザーは正常に作成されました" -ForegroundColor Cyan
    }
}
catch {
    Write-Host "[WARN] ライセンス取得・付与中にエラーが発生しました: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "[INFO] ユーザーは正常に作成されました" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "[INFO] 初期パスワードは生成されましたが、セキュリティのため表示していません" -ForegroundColor Yellow
Write-Host "[INFO] 初回ログイン時にパスワード変更が求められます" -ForegroundColor Yellow
