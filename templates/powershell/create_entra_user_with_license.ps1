<#
.SYNOPSIS
    Microsoft Entra ID ユーザー作成と Microsoft 365 ライセンス付与ツール

.DESCRIPTION
    Azure VM（Windows）上で動作する、Entra ID ユーザー作成と Microsoft 365 E3 ライセンス付与を
    安全に実行する PowerShell スクリプトです。
    
    - オンプレミス Active Directory は使用しません
    - Microsoft Entra ID（Azure AD）ネイティブのみを使用
    - Microsoft Graph PowerShell SDK を使用
    - Dry-run モードで事前確認が可能
    - 半自動実行モデル（人が実行）

.PARAMETER DryRun
    Dry-run モードの有効/無効を指定します。
    $true: 実行内容を表示するのみ（実際には実行しない）
    $false: 実際にユーザー作成とライセンス付与を実行

.EXAMPLE
    # Dry-run モードで実行（推奨：まずはこちらで確認）
    .\create_entra_user_with_license.ps1 -DryRun $true

.EXAMPLE
    # 実際に実行
    .\create_entra_user_with_license.ps1 -DryRun $false

.NOTES
    作成日: 2026-01-11
    バージョン: 1.0.0
    要件: Microsoft.Graph モジュールが必要
    必要な権限: User.ReadWrite.All, Directory.ReadWrite.All, Organization.Read.All
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [bool]$DryRun
)

# ============================================================================
# 設定セクション
# ============================================================================

# ユーザー情報の定義
$DisplayName = "山田 太郎"
$MailNickname = "yamada.taro"  # UserPrincipalName の @ より前の部分
$UserPrincipalName = "$MailNickname@yourtenant.onmicrosoft.com"  # テナント名を変更してください
$Department = "営業部"
$UsageLocation = "JP"  # 日本
$InitialPassword = "TempPassword123!"  # 初期パスワード（強力なパスワードを推奨）

# ライセンス情報
$LicenseSkuPartNumber = "ENTERPRISEPACK"  # Microsoft 365 E3

# ============================================================================
# 関数定義
# ============================================================================

function Write-InfoMessage {
    <#
    .SYNOPSIS
        情報メッセージを表示
    #>
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-SuccessMessage {
    <#
    .SYNOPSIS
        成功メッセージを表示
    #>
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-WarningMessage {
    <#
    .SYNOPSIS
        警告メッセージを表示
    #>
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-ErrorMessage {
    <#
    .SYNOPSIS
        エラーメッセージを表示
    #>
    param([string]$Message)
    Write-Error "[ERROR] $Message"
}

function Test-MgGraphConnection {
    <#
    .SYNOPSIS
        Microsoft Graph への接続を確認
    #>
    try {
        $context = Get-MgContext
        if ($null -eq $context) {
            return $false
        }
        return $true
    }
    catch {
        return $false
    }
}

function Connect-ToMicrosoftGraph {
    <#
    .SYNOPSIS
        Microsoft Graph に接続
    #>
    Write-InfoMessage "Microsoft Graph への接続を開始します..."
    
    # 必要なスコープを定義
    $RequiredScopes = @(
        "User.ReadWrite.All",
        "Directory.ReadWrite.All",
        "Organization.Read.All"
    )
    
    try {
        # Microsoft Graph に接続
        Connect-MgGraph -Scopes $RequiredScopes -NoWelcome
        
        # 接続確認
        $context = Get-MgContext
        if ($null -eq $context) {
            Write-ErrorMessage "Microsoft Graph への接続に失敗しました"
            exit 1
        }
        
        Write-SuccessMessage "Microsoft Graph に接続しました"
        Write-InfoMessage "接続テナント: $($context.TenantId)"
        Write-InfoMessage "接続ユーザー: $($context.Account)"
        
        return $true
    }
    catch {
        Write-ErrorMessage "Microsoft Graph への接続中にエラーが発生しました: $($_.Exception.Message)"
        exit 1
    }
}

function Test-UserExists {
    <#
    .SYNOPSIS
        ユーザーの存在確認
    #>
    param([string]$UserPrincipalName)
    
    try {
        $user = Get-MgUser -Filter "userPrincipalName eq '$UserPrincipalName'" -ErrorAction SilentlyContinue
        if ($null -ne $user) {
            return $true
        }
        return $false
    }
    catch {
        Write-ErrorMessage "ユーザー存在確認中にエラーが発生しました: $($_.Exception.Message)"
        return $false
    }
}

function Get-LicenseSkuId {
    <#
    .SYNOPSIS
        ライセンス SKU ID を取得
    #>
    param([string]$SkuPartNumber)
    
    try {
        Write-InfoMessage "利用可能なライセンス SKU を取得しています..."
        $skus = Get-MgSubscribedSku
        
        # 指定された SKU Part Number を検索
        $targetSku = $skus | Where-Object { $_.SkuPartNumber -eq $SkuPartNumber }
        
        if ($null -eq $targetSku) {
            Write-ErrorMessage "指定されたライセンス SKU '$SkuPartNumber' が見つかりません"
            Write-InfoMessage "利用可能な SKU 一覧:"
            $skus | ForEach-Object {
                Write-Host "  - $($_.SkuPartNumber): $($_.SkuId)" -ForegroundColor Gray
            }
            return $null
        }
        
        Write-SuccessMessage "ライセンス SKU を取得しました: $($targetSku.SkuPartNumber) (ID: $($targetSku.SkuId))"
        return $targetSku.SkuId
    }
    catch {
        Write-ErrorMessage "ライセンス SKU 取得中にエラーが発生しました: $($_.Exception.Message)"
        return $null
    }
}

function New-EntraUser {
    <#
    .SYNOPSIS
        Entra ID ユーザーを作成
    #>
    param(
        [string]$DisplayName,
        [string]$UserPrincipalName,
        [string]$MailNickname,
        [string]$Department,
        [string]$UsageLocation,
        [string]$Password
    )
    
    try {
        Write-InfoMessage "Entra ID ユーザーを作成しています..."
        
        # パスワードプロファイルを作成
        $PasswordProfile = @{
            Password = $Password
            ForceChangePasswordNextSignIn = $true  # 初回ログイン時にパスワード変更を強制
        }
        
        # ユーザー作成パラメータ
        $UserParams = @{
            DisplayName = $DisplayName
            UserPrincipalName = $UserPrincipalName
            MailNickname = $MailNickname
            Department = $Department
            UsageLocation = $UsageLocation
            PasswordProfile = $PasswordProfile
            AccountEnabled = $true
        }
        
        # ユーザー作成
        $newUser = New-MgUser @UserParams
        
        Write-SuccessMessage "ユーザーを作成しました: $($newUser.DisplayName) ($($newUser.UserPrincipalName))"
        Write-InfoMessage "ユーザー ID: $($newUser.Id)"
        
        return $newUser
    }
    catch {
        Write-ErrorMessage "ユーザー作成中にエラーが発生しました: $($_.Exception.Message)"
        return $null
    }
}

function Set-UserLicense {
    <#
    .SYNOPSIS
        ユーザーにライセンスを付与
    #>
    param(
        [string]$UserId,
        [string]$SkuId
    )
    
    try {
        Write-InfoMessage "ユーザーにライセンスを付与しています..."
        
        # ライセンス付与パラメータ
        $LicenseParams = @{
            UserId = $UserId
            AddLicenses = @(
                @{
                    SkuId = $SkuId
                }
            )
            RemoveLicenses = @()
        }
        
        # ライセンス付与
        Set-MgUserLicense @LicenseParams
        
        Write-SuccessMessage "ライセンスを付与しました: $SkuId"
        return $true
    }
    catch {
        Write-ErrorMessage "ライセンス付与中にエラーが発生しました: $($_.Exception.Message)"
        return $false
    }
}

function Show-DryRunPreview {
    <#
    .SYNOPSIS
        Dry-run モードでの実行内容プレビューを表示
    #>
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  DRY-RUN モード: 実行内容プレビュー" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "【実行される操作】" -ForegroundColor Cyan
    Write-Host "1. ユーザー存在確認" -ForegroundColor White
    Write-Host "   UserPrincipalName: $UserPrincipalName" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "2. Entra ID ユーザー作成" -ForegroundColor White
    Write-Host "   DisplayName: $DisplayName" -ForegroundColor Gray
    Write-Host "   UserPrincipalName: $UserPrincipalName" -ForegroundColor Gray
    Write-Host "   MailNickname: $MailNickname" -ForegroundColor Gray
    Write-Host "   Department: $Department" -ForegroundColor Gray
    Write-Host "   UsageLocation: $UsageLocation" -ForegroundColor Gray
    Write-Host "   AccountEnabled: True" -ForegroundColor Gray
    Write-Host "   ForceChangePasswordNextSignIn: True" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "3. ライセンス SKU 取得" -ForegroundColor White
    Write-Host "   SkuPartNumber: $LicenseSkuPartNumber" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "4. Microsoft 365 ライセンス付与" -ForegroundColor White
    Write-Host "   ライセンス: $LicenseSkuPartNumber (Microsoft 365 E3)" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  実際には実行されません" -ForegroundColor Yellow
    Write-Host "  実行するには -DryRun `$false を指定してください" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host ""
}

function Show-ExecutionResult {
    <#
    .SYNOPSIS
        実行結果を表示
    #>
    param(
        [object]$User,
        [string]$SkuPartNumber
    )
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  実行結果" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    if ($null -ne $User) {
        Write-SuccessMessage "ユーザー作成: 成功"
        Write-Host "  表示名: $($User.DisplayName)" -ForegroundColor White
        Write-Host "  UPN: $($User.UserPrincipalName)" -ForegroundColor White
        Write-Host "  ユーザー ID: $($User.Id)" -ForegroundColor White
        Write-Host "  部署: $($User.Department)" -ForegroundColor White
        Write-Host "  ライセンス: $SkuPartNumber (Microsoft 365 E3)" -ForegroundColor White
        Write-Host ""
        Write-WarningMessage "初期パスワード: $InitialPassword"
        Write-WarningMessage "初回ログイン時にパスワード変更が求められます"
    }
    else {
        Write-ErrorMessage "ユーザー作成: 失敗"
    }
    
    Write-Host ""
}

# ============================================================================
# メイン処理
# ============================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Entra ID ユーザー作成ツール" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Dry-run モードの表示
if ($DryRun) {
    Write-WarningMessage "Dry-run モード: 有効（実際には実行しません）"
}
else {
    Write-WarningMessage "Dry-run モード: 無効（実際に実行します）"
}
Write-Host ""

# Microsoft Graph への接続確認
if (-not (Test-MgGraphConnection)) {
    Write-InfoMessage "Microsoft Graph に接続されていません。接続を開始します..."
    Connect-ToMicrosoftGraph
}
else {
    $context = Get-MgContext
    Write-InfoMessage "既に Microsoft Graph に接続されています"
    Write-InfoMessage "接続テナント: $($context.TenantId)"
    Write-InfoMessage "接続ユーザー: $($context.Account)"
    Write-Host ""
}

# Dry-run モードの場合
if ($DryRun) {
    Show-DryRunPreview
    Write-InfoMessage "Dry-run モードのため、実際の操作は実行されませんでした"
    exit 0
}

# ============================================================================
# 実際の実行処理（Dry-run = false の場合のみ）
# ============================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  実際の実行を開始します" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 1. ユーザー存在確認
Write-InfoMessage "ユーザーの存在確認を実行しています..."
if (Test-UserExists -UserPrincipalName $UserPrincipalName) {
    Write-ErrorMessage "ユーザー '$UserPrincipalName' は既に存在します"
    Write-InfoMessage "処理を中断します"
    exit 1
}
Write-SuccessMessage "ユーザー '$UserPrincipalName' は存在しません（作成可能）"
Write-Host ""

# 2. ライセンス SKU ID を取得
$SkuId = Get-LicenseSkuId -SkuPartNumber $LicenseSkuPartNumber
if ($null -eq $SkuId) {
    Write-ErrorMessage "ライセンス SKU ID の取得に失敗しました"
    Write-InfoMessage "処理を中断します"
    exit 1
}
Write-Host ""

# 3. Entra ID ユーザーを作成
$newUser = New-EntraUser `
    -DisplayName $DisplayName `
    -UserPrincipalName $UserPrincipalName `
    -MailNickname $MailNickname `
    -Department $Department `
    -UsageLocation $UsageLocation `
    -Password $InitialPassword

if ($null -eq $newUser) {
    Write-ErrorMessage "ユーザー作成に失敗しました"
    Write-InfoMessage "処理を中断します"
    exit 1
}
Write-Host ""

# 4. ライセンスを付与
$licenseResult = Set-UserLicense -UserId $newUser.Id -SkuId $SkuId
if (-not $licenseResult) {
    Write-ErrorMessage "ライセンス付与に失敗しました"
    Write-WarningMessage "ユーザーは作成されましたが、ライセンスは付与されていません"
    Write-WarningMessage "手動でライセンスを付与してください: $($newUser.UserPrincipalName)"
    exit 1
}
Write-Host ""

# 5. 実行結果を表示
Show-ExecutionResult -User $newUser -SkuPartNumber $LicenseSkuPartNumber

Write-SuccessMessage "すべての処理が正常に完了しました"
Write-Host ""

