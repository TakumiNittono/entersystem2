# Active Directory ユーザー作成（派遣社員）
# 生成日時: {generated_at}

$DisplayName = "{employee_name}"
$SamAccountName = "{sam_account_name}"
$UserPrincipalName = "{sam_account_name}@{company_domain}"
$Department = "{department}"
$AccountExpirationDate = "{contract_end_date}"

# Active Directory ユーザー作成（制限付き・有効期限あり）
New-ADUser -Name $DisplayName `
    -SamAccountName $SamAccountName `
    -UserPrincipalName $UserPrincipalName `
    -Department $Department `
    -Enabled $true `
    -PasswordNeverExpires $false `
    -AccountExpirationDate $AccountExpirationDate

# Microsoft 365 ライセンス付与（Basic）
Set-MgUserLicense -UserId $UserPrincipalName `
    -AddLicenses @{SkuId = "O365_BUSINESS_ESSENTIALS"} `
    -RemoveLicenses @()

Write-Host "ユーザー作成完了: $DisplayName ($UserPrincipalName)" -ForegroundColor Green
Write-Host "有効期限: $AccountExpirationDate" -ForegroundColor Yellow

