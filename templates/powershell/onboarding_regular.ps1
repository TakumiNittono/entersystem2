# Active Directory ユーザー作成（正社員）
# 生成日時: {generated_at}

$DisplayName = "{employee_name}"
$SamAccountName = "{sam_account_name}"
$UserPrincipalName = "{sam_account_name}@{company_domain}"
$Department = "{department}"

# Active Directory ユーザー作成
New-ADUser -Name $DisplayName `
    -SamAccountName $SamAccountName `
    -UserPrincipalName $UserPrincipalName `
    -Department $Department `
    -Enabled $true `
    -PasswordNeverExpires $false

# Microsoft 365 ライセンス付与（E3）
Set-MgUserLicense -UserId $UserPrincipalName `
    -AddLicenses @{SkuId = "ENTERPRISEPACK"} `
    -RemoveLicenses @()

Write-Host "ユーザー作成完了: $DisplayName ($UserPrincipalName)" -ForegroundColor Green

