# =========================================
# Entra ID ユーザー作成（正社員）
# Generated at: {generated_at}
# =========================================

$DisplayName = "{employee_name}"
$UserPrincipalName = "{sam_account_name}@{company_domain}"
$MailNickname = "{sam_account_name}"
$Department = "{department}"
$UsageLocation = "JP"
$TempPassword = (New-Guid).Guid

Write-Host "[INFO] Entra ID ユーザーを作成します（Dry-run前提）"

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

$sku = Get-MgSubscribedSku | Where-Object { $_.SkuPartNumber -eq "ENTERPRISEPACK" }

if ($sku) {
  Set-MgUserLicense `
    -UserId $newUser.Id `
    -AddLicenses @{ SkuId = $sku.SkuId } `
    -RemoveLicenses @()

  Write-Host "[SUCCESS] Microsoft 365 E3 ライセンスを付与しました"
} else {
  Write-Host "[WARN] E3 ライセンスが見つからないためスキップしました"
}

Write-Host "[SUCCESS] ユーザー作成完了: $DisplayName ($UserPrincipalName)" -ForegroundColor Green
