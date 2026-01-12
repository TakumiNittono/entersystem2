# ========================================
# Entra ID ユーザー作成（正社員）
# Generated at: {generated_at}
# ========================================

$DisplayName = "{employee_name}"
$UserPrincipalName = "{sam_account_name}@{company_domain}"
$Department = "{department}"
$UsageLocation = "JP"

Write-Host "[INFO] Entra ID ユーザーを作成します (Dry-run前提)"

# Entra ID ユーザー作成
$newUser = New-MgUser `
  -DisplayName $DisplayName `
  -UserPrincipalName $UserPrincipalName `
  -MailNickname "{sam_account_name}" `
  -Department $Department `
  -UsageLocation $UsageLocation `
  -AccountEnabled:$true `
  -PasswordProfile @{
      ForceChangePasswordNextSignIn = $true
      Password = "TempP@ssw0rd!"
  }

# Microsoft 365 E3 ライセンス付与
$sku = Get-MgSubscribedSku | Where-Object { $_.SkuPartNumber -eq "ENTERPRISEPACK" }

if ($sku) {
    Set-MgUserLicense `
      -UserId $newUser.Id `
      -AddLicenses @{SkuId = $sku.SkuId} `
      -RemoveLicenses @()
    Write-Host "[SUCCESS] Microsoft 365 E3 ライセンスを付与しました"
} else {
    Write-Host "[WARN] E3 ライセンスが存在しません。スキップします"
}

Write-Host "[SUCCESS] Entra ID ユーザー作成完了: $DisplayName ($UserPrincipalName)" -ForegroundColor Green
