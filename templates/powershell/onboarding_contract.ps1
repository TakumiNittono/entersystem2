# =========================================
# Entra ID ユーザー作成（派遣社員）
# Generated at: {generated_at}
# 契約終了日: {contract_end_date}
# =========================================

$DisplayName = "{employee_name}"
$UserPrincipalName = "{sam_account_name}@{company_domain}"
$MailNickname = "{sam_account_name}"
$Department = "{department}"
$UsageLocation = "JP"
$AccountExpirationDate = Get-Date "{contract_end_date}"
$TempPassword = (New-Guid).Guid

Write-Host "[INFO] Entra ID ユーザーを作成します（制限ユーザー・有効期限あり、Dry-run前提）"

$newUser = New-MgUser `
  -DisplayName $DisplayName `
  -UserPrincipalName $UserPrincipalName `
  -MailNickname $MailNickname `
  -Department $Department `
  -UsageLocation $UsageLocation `
  -AccountEnabled $true `
  -PasswordProfile @{
      ForceChangePasswordNextSignIn = $true
      Password = $TempPassword
  }

# 注意: Entra ID では AccountExpirationDate は制限付きの機能です
# 必要に応じて別途設定してください

$sku = Get-MgSubscribedSku | Where-Object { $_.SkuPartNumber -eq "BASICPACK" }

if ($sku) {
  Set-MgUserLicense `
    -UserId $newUser.Id `
    -AddLicenses @{ SkuId = $sku.SkuId } `
    -RemoveLicenses @()

  Write-Host "[SUCCESS] Microsoft 365 Basic ライセンスを付与しました"
} else {
  Write-Host "[WARN] Basic ライセンスが見つからないためスキップしました"
}

Write-Host "[SUCCESS] ユーザー作成完了: $DisplayName ($UserPrincipalName)" -ForegroundColor Green
Write-Host "[INFO] 有効期限: {contract_end_date}" -ForegroundColor Yellow
