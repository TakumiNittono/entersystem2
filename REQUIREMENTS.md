# BPO向け業務自動化AI デモシステム 要件定義書

## 1. プロジェクト概要

### 1.1 目的
人が毎日PowerShellで行っているインフラ業務（入社処理など）について、AIが「判断＋PowerShellコマンド生成」までを行い、実行はWindows上で人が行う"半自動"デモシステムを構築する。

### 1.2 対象ユーザー
- **主要ユーザー**: 営業担当者（デモ実施者）
- **デモ対象**: 顧客（BPOサービス導入検討者）
- **技術ユーザー**: 現場エンジニア（システム理解・カスタマイズ）

### 1.3 システムの位置づけ
- **完全自動化システムではない**
- **既存のBPO運用を壊さずAIを差し込む設計**
- **営業用PoC / デモ用途**
- **実行は人が行う設計（セキュリティレビュー通過を重視）**

---

## 2. システムアーキテクチャ

### 2.1 全体構成

```
┌─────────────┐
│  ブラウザ   │ (ユーザー入力)
└──────┬──────┘
       │ HTTP/HTTPS
       ▼
┌─────────────────┐
│   FastAPI       │ (Python)
│   - 入力受付    │
│   - AI判断      │
│   - コマンド生成│
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   OpenAI API    │ (GPT-4/GPT-3.5)
│   - コマンド生成│
└─────────────────┘

【出力】
┌─────────────────┐
│   画面表示      │
│   - 判断結果    │
│   - PowerShell  │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   PowerShell    │ (Windows)
│   - 手動実行    │
└─────────────────┘
```

### 2.2 技術スタック

| 項目 | 技術 | バージョン | 備考 |
|------|------|-----------|------|
| バックエンド | FastAPI | 0.104+ | Python 3.9+ |
| フロントエンド | Jinja2テンプレート | - | シンプルなHTML |
| AI | OpenAI API | - | gpt-4 または gpt-3.5-turbo |
| 実行環境 | Windows PowerShell | 5.1+ | 手動実行 |
| ログ | Python logging | - | 標準ライブラリ |

### 2.3 セキュリティ制約（絶対遵守）

#### 2.3.1 実行制約
- ❌ **AI（FastAPI）は PowerShell を実行しない**
- ❌ **OS操作、WinRM、SSH 等は一切使わない**
- ❌ **リモート実行機能は実装しない**
- ✅ **AIは「判断・文章・コード生成のみ」**
- ✅ **実行は Windows の PowerShell で人が Enter を押す**

#### 2.3.2 セキュリティ要件
- APIキーは環境変数で管理（コードに直接記載しない）
- 入力値のサニタイズ（XSS対策）
- HTTPS推奨（本番環境）
- ログに機密情報を含めない（マスク処理）

---

## 3. 機能要件

### 3.1 デモ対象業務

#### 業務1: 入社処理（Onboarding）

**業務フロー**:
1. 新入社員情報を入力
2. AIが雇用形態に基づいて判断
3. PowerShellコマンドを生成
4. 人がコマンドをコピーして実行

### 3.2 入力フォーム

#### 3.2.1 入力項目

| 項目名 | フィールド名 | 型 | 必須 | 選択肢/制約 | 説明 |
|--------|------------|-----|------|------------|------|
| 顧客名 | `company` | string | ✅ | 1-100文字 | 顧客企業名 |
| タスク種別 | `task_type` | string | ✅ | "onboarding" | 固定値（将来拡張用） |
| 従業員名 | `employee_name` | string | ✅ | 1-50文字 | 新入社員の氏名 |
| 雇用形態 | `employment_type` | string | ✅ | "正社員" / "派遣" | ラジオボタン |
| 部署 | `department` | string | ✅ | 1-50文字 | 所属部署名 |

#### 3.2.2 入力バリデーション

- 必須項目チェック
- 文字数制限チェック
- 特殊文字のサニタイズ
- エラーメッセージの日本語表示

### 3.3 AI判断ロジック

#### 3.3.1 判断ルール（入社処理）

| 雇用形態 | ユーザータイプ | ライセンス | 有効期限 | 備考 |
|---------|--------------|-----------|---------|------|
| 正社員 | 標準ユーザー | Microsoft 365 E3 | なし | フルアクセス |
| 派遣 | 制限ユーザー | Microsoft 365 Basic | あり（契約終了日） | 制限付きアクセス |

#### 3.3.2 判断結果の説明文フォーマット

**正社員の場合**:
```
このユーザーは正社員のため、標準ユーザーとして作成し、
Microsoft 365 E3 ライセンスを付与します。
```

**派遣の場合**:
```
このユーザーは派遣社員のため、制限ユーザーとして作成し、
Microsoft 365 Basic ライセンスを付与します。
また、契約終了日（YYYY-MM-DD）に有効期限を設定します。
```

### 3.4 PowerShellコマンド生成

#### 3.4.1 生成ルール

- **テンプレートベース**: 事前定義されたテンプレートを使用
- **変数展開**: 入力値から変数を展開
- **実行可能形式**: そのままコピー&ペーストで実行可能
- **エラーハンドリング**: 基本的なエラーチェックを含める

#### 3.4.2 コマンドテンプレート

**正社員（標準ユーザー + M365 E3）**:
```powershell
# Active Directory ユーザー作成
$DisplayName = "{employee_name}"
$SamAccountName = "{sam_account_name}"
$UserPrincipalName = "{sam_account_name}@{company_domain}"
$Department = "{department}"

New-ADUser -Name $DisplayName `
    -SamAccountName $SamAccountName `
    -UserPrincipalName $UserPrincipalName `
    -Department $Department `
    -Enabled $true `
    -PasswordNeverExpires $false

# Microsoft 365 ライセンス付与
Set-MgUserLicense -UserId $UserPrincipalName `
    -AddLicenses @{SkuId = "ENTERPRISEPACK"} `
    -RemoveLicenses @()
```

**派遣（制限ユーザー + M365 Basic + 有効期限）**:
```powershell
# Active Directory ユーザー作成（制限付き）
$DisplayName = "{employee_name}"
$SamAccountName = "{sam_account_name}"
$UserPrincipalName = "{sam_account_name}@{company_domain}"
$Department = "{department}"
$AccountExpirationDate = "{contract_end_date}"

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
```

#### 3.4.3 変数マッピング

| テンプレート変数 | 入力値 | 変換ルール |
|----------------|--------|-----------|
| `{employee_name}` | `employee_name` | そのまま使用 |
| `{sam_account_name}` | `employee_name` | ローマ字変換（簡易版: 英数字のみ） |
| `{company_domain}` | `company` | ドメイン形式に変換（例: "example.com"） |
| `{department}` | `department` | そのまま使用 |
| `{contract_end_date}` | - | 派遣の場合のみ、デフォルトで1年後 |

### 3.5 出力画面

#### 3.5.1 表示項目

1. **AI判断結果（文章）**
   - 判断理由の説明
   - 適用される設定の説明

2. **生成されたPowerShellコマンド**
   - コードブロック形式で表示
   - コピーボタン付き（クリップボードにコピー）
   - シンタックスハイライト（オプション）

3. **入力値の確認表示**（オプション）
   - 入力した値のサマリー

#### 3.5.2 UI要件

- **シンプルで分かりやすいデザイン**
- **レスポンシブ対応**（タブレットでも見られる）
- **コピーボタン**（ワンクリックでコピー）
- **実行ボタンは作らない**（セキュリティ要件）

### 3.6 ログ機能

#### 3.6.1 ログ出力項目

| 項目 | 出力内容 | 出力タイミング |
|------|---------|--------------|
| 入力JSON | リクエストボディ全体 | リクエスト受信時 |
| 判断結果 | 雇用形態、ユーザータイプ、ライセンス | 判断完了時 |
| 生成コマンド | PowerShellコマンド全文 | 生成完了時 |
| エラー | エラーメッセージ、スタックトレース | エラー発生時 |

#### 3.6.2 ログ形式

```
[YYYY-MM-DD HH:MM:SS] [INFO] 入力受信: {"company": "...", ...}
[YYYY-MM-DD HH:MM:SS] [INFO] 判断結果: 正社員 -> 標準ユーザー + M365 E3
[YYYY-MM-DD HH:MM:SS] [INFO] PowerShell生成完了
```

---

## 4. 非機能要件

### 4.1 パフォーマンス

- APIレスポンス時間: 5秒以内（OpenAI API呼び出し含む）
- 同時接続数: 10ユーザー程度（デモ用途のため）

### 4.2 可用性

- デモ用途のため、高可用性は不要
- エラーハンドリングは実装（適切なエラーメッセージ表示）

### 4.3 保守性

- コードは読みやすく、コメントを適切に記載
- 設定値は環境変数または設定ファイルで管理
- テンプレートは外部ファイル化（将来の拡張性）

### 4.4 拡張性

- 他の業務（退職処理、異動処理など）を追加しやすい設計
- 判断ルールを設定ファイルで管理可能にする

---

## 5. ディレクトリ構成

```
entersystem2/
├── README.md                 # 起動方法・デモ手順
├── REQUIREMENTS.md          # 本要件定義書
├── requirements.txt          # Python依存パッケージ
├── .env.example             # 環境変数テンプレート
├── .gitignore
│
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPIアプリケーション
│   ├── config.py            # 設定管理
│   ├── models.py            # データモデル（Pydantic）
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py    # OpenAI API呼び出し
│   │   └── command_generator.py  # PowerShell生成
│   ├── templates/
│   │   ├── index.html       # 入力フォーム
│   │   └── result.html      # 結果表示
│   └── static/
│       └── style.css        # CSS（オプション）
│
└── templates/
    └── powershell/          # PowerShellテンプレート
        ├── onboarding_regular.ps1
        └── onboarding_contract.ps1
```

---

## 6. API仕様

### 6.1 エンドポイント

#### POST `/api/onboarding`

**リクエストボディ**:
```json
{
  "company": "株式会社サンプル",
  "task_type": "onboarding",
  "employee_name": "山田 太郎",
  "employment_type": "正社員",
  "department": "営業部"
}
```

**レスポンス** (成功時):
```json
{
  "status": "success",
  "judgment": "このユーザーは正社員のため、標準ユーザーとして作成し、Microsoft 365 E3 ライセンスを付与します。",
  "powershell_command": "# Active Directory ユーザー作成\n$DisplayName = \"山田 太郎\"\n..."
}
```

**レスポンス** (エラー時):
```json
{
  "status": "error",
  "message": "エラーメッセージ"
}
```

### 6.2 エラーハンドリング

| HTTPステータス | エラー内容 | レスポンス |
|--------------|-----------|-----------|
| 400 | バリデーションエラー | エラーメッセージ + 詳細 |
| 500 | サーバーエラー | 汎用エラーメッセージ |
| 503 | OpenAI API エラー | API接続エラーメッセージ |

---

## 7. デモシナリオ

### 7.1 デモ準備

1. FastAPIサーバーを起動
2. ブラウザで `http://localhost:8000` にアクセス
3. PowerShellを開いておく（実行用）

### 7.2 デモ手順

#### シナリオ1: 正社員の入社処理

1. **入力画面で以下を入力**:
   - 顧客名: "株式会社デモ"
   - 従業員名: "佐藤 花子"
   - 雇用形態: "正社員"
   - 部署: "開発部"

2. **「生成」ボタンをクリック**

3. **結果画面で確認**:
   - AI判断結果を確認
   - 生成されたPowerShellコマンドを確認

4. **PowerShellで実行**（デモでは実際には実行しない）:
   - コマンドをコピー
   - PowerShellに貼り付け
   - Enterキーで実行（デモでは説明のみ）

#### シナリオ2: 派遣社員の入社処理

1. **入力画面で以下を入力**:
   - 顧客名: "株式会社デモ"
   - 従業員名: "鈴木 一郎"
   - 雇用形態: "派遣"
   - 部署: "営業部"

2. **「生成」ボタンをクリック**

3. **結果画面で確認**:
   - 正社員と異なる判断結果を確認
   - 制限ユーザー + Basicライセンス + 有効期限設定を確認

---

## 8. セキュリティ考慮事項

### 8.1 入力値サニタイズ

- HTMLエスケープ（XSS対策）
- SQLインジェクション対策（DB使用時）
- コマンドインジェクション対策（変数展開時の検証）

### 8.2 APIキー管理

- `.env`ファイルで管理
- `.gitignore`に追加
- 本番環境では環境変数またはシークレット管理サービスを使用

### 8.3 ログ管理

- 機密情報（APIキー、パスワード等）はログに出力しない
- 個人情報は必要最小限のみログに記録

---

## 9. 今後の拡張案

### 9.1 追加可能な業務

- 退職処理（Offboarding）
- 異動処理（Transfer）
- 権限変更（Permission Change）
- ライセンス変更（License Update）

### 9.2 機能拡張

- 複数ユーザーの一括処理
- コマンド実行履歴の保存
- テンプレートのカスタマイズ機能
- 多言語対応

---

## 10. 制約事項・注意事項

### 10.1 重要な制約

- **このシステムは完全自動化システムではない**
- **実行は人が行う設計である**
- **既存のBPO運用を壊さずAIを差し込む思想である**
- **セキュリティレビューを通る設計にする**

### 10.2 デモ時の注意点

- 実際のActive DirectoryやMicrosoft 365には接続しない
- デモ環境で動作確認を行う
- エラーメッセージは適切に表示する

### 10.3 技術的制約

- OpenAI APIの利用制限に注意
- レート制限の考慮
- APIキーのコスト管理

---

## 11. プロジェクトフェーズと進捗管理

### 11.1 フェーズ概要

| フェーズ | 名称 | 期間目安 | 状態 | 進捗率 |
|---------|------|---------|------|--------|
| Phase 1 | 環境構築・基盤整備 | 1-2日 | ⬜ 未着手 | 0% |
| Phase 2 | コア機能実装 | 2-3日 | ⬜ 未着手 | 0% |
| Phase 3 | AI連携・コマンド生成 | 2-3日 | ⬜ 未着手 | 0% |
| Phase 4 | UI実装・表示機能 | 1-2日 | ⬜ 未着手 | 0% |
| Phase 5 | テスト・デモ準備 | 1-2日 | ⬜ 未着手 | 0% |

**凡例**: 
- ⬜ 未着手 / 🔵 進行中 / ✅ 完了 / 🔴 ブロック

**フェーズ依存関係図**:
```
Phase 1 (環境構築)
    │
    ├─→ Phase 2 (コア機能)
    │       │
    │       ├─→ Phase 3 (AI連携)
    │       │
    │       └─→ Phase 4 (UI実装)
    │               │
    │               └─→ Phase 5 (テスト・デモ準備)
    │
    └─→ Phase 4 (UI実装) [並行可能]
            │
            └─→ Phase 5 (テスト・デモ準備)
```

**並行実行可能なフェーズ**:
- Phase 3 と Phase 4 は Phase 2 完了後、並行して進められる

---

### 11.2 Phase 1: 環境構築・基盤整備

**目的**: 開発環境のセットアップとプロジェクト基盤の構築

**期間**: 1-2日

**タスクリスト**:

- [ ] Python仮想環境の作成
- [ ] 依存パッケージのインストール（requirements.txt作成）
- [ ] ディレクトリ構造の作成
- [ ] FastAPIプロジェクトの初期化（`app/main.py`の基本構造）
- [ ] 設定管理の実装（`app/config.py`）
  - [ ] 環境変数の読み込み
  - [ ] OpenAI APIキーの設定
- [ ] `.env.example`の作成
- [ ] `.gitignore`の設定
- [ ] ログ設定の実装
- [ ] 基本的なエラーハンドリングの実装

**成果物**:
- [ ] `requirements.txt`
- [ ] `.env.example`
- [ ] `.gitignore`
- [ ] `app/__init__.py`
- [ ] `app/main.py`（基本構造のみ）
- [ ] `app/config.py`
- [ ] ログ設定ファイル

**依存関係**: なし

**進捗状況**: ⬜ 未着手

**備考**: このフェーズで基盤が整うと、以降の開発がスムーズに進む

---

### 11.3 Phase 2: コア機能実装

**目的**: 入力受付、バリデーション、判断ロジックの実装

**期間**: 2-3日

**タスクリスト**:

- [ ] データモデルの実装（`app/models.py`）
  - [ ] リクエストモデル（Pydantic）
  - [ ] レスポンスモデル（Pydantic）
- [ ] 入力バリデーションの実装
  - [ ] 必須項目チェック
  - [ ] 文字数制限チェック
  - [ ] 特殊文字のサニタイズ
- [ ] 判断ロジックの実装（`app/services/judgment_service.py`）
  - [ ] 雇用形態による分岐処理
  - [ ] 判断結果の生成（文章）
  - [ ] ユーザータイプの決定
  - [ ] ライセンスタイプの決定
- [ ] APIエンドポイントの実装（`POST /api/onboarding`）
  - [ ] リクエスト受信
  - [ ] バリデーション実行
  - [ ] 判断ロジック呼び出し
  - [ ] レスポンス返却
- [ ] エラーハンドリングの強化
  - [ ] バリデーションエラーの処理
  - [ ] エラーレスポンスの統一

**成果物**:
- [ ] `app/models.py`
- [ ] `app/services/judgment_service.py`
- [ ] `app/main.py`（APIエンドポイント実装）
- [ ] エラーハンドリング機能

**依存関係**: Phase 1完了

**進捗状況**: ⬜ 未着手

**備考**: AI連携なしでも動作確認可能な状態にする

---

### 11.4 Phase 3: AI連携・コマンド生成

**目的**: OpenAI API連携とPowerShellコマンド生成機能の実装

**期間**: 2-3日

**タスクリスト**:

- [ ] OpenAI API連携の実装（`app/services/ai_service.py`）
  - [ ] APIクライアントの実装
  - [ ] プロンプト設計
  - [ ] API呼び出し処理
  - [ ] エラーハンドリング（API接続エラー等）
- [ ] PowerShellテンプレートの作成
  - [ ] `templates/powershell/onboarding_regular.ps1`（正社員用）
  - [ ] `templates/powershell/onboarding_contract.ps1`（派遣用）
- [ ] コマンド生成サービスの実装（`app/services/command_generator.py`）
  - [ ] テンプレート読み込み
  - [ ] 変数展開ロジック
    - [ ] `{employee_name}` → 入力値
    - [ ] `{sam_account_name}` → ローマ字変換
    - [ ] `{company_domain}` → ドメイン形式変換
    - [ ] `{department}` → 入力値
    - [ ] `{contract_end_date}` → 日付計算（派遣の場合）
  - [ ] コマンド生成処理
- [ ] 判断ロジックとコマンド生成の統合
- [ ] ログ出力の実装
  - [ ] 入力JSONのログ出力
  - [ ] 判断結果のログ出力
  - [ ] 生成コマンドのログ出力

**成果物**:
- [ ] `app/services/ai_service.py`
- [ ] `app/services/command_generator.py`
- [ ] `templates/powershell/onboarding_regular.ps1`
- [ ] `templates/powershell/onboarding_contract.ps1`
- [ ] ログ出力機能

**依存関係**: Phase 2完了

**進捗状況**: ⬜ 未着手

**備考**: OpenAI APIキーが必要。モックで動作確認も可能

---

### 11.5 Phase 4: UI実装・表示機能

**目的**: ユーザーインターフェースの実装と結果表示機能

**期間**: 1-2日

**タスクリスト**:

- [ ] HTMLテンプレートの実装
  - [ ] `app/templates/index.html`（入力フォーム）
    - [ ] フォーム項目の実装
    - [ ] バリデーション（フロントエンド）
    - [ ] エラーメッセージ表示
  - [ ] `app/templates/result.html`（結果表示）
    - [ ] AI判断結果の表示
    - [ ] PowerShellコマンドの表示（コードブロック）
    - [ ] コピーボタンの実装（JavaScript）
- [ ] CSSの実装（`app/static/style.css`）
  - [ ] シンプルで分かりやすいデザイン
  - [ ] レスポンシブ対応
  - [ ] コードブロックのスタイリング
- [ ] FastAPIのテンプレート統合
  - [ ] Jinja2テンプレートエンジンの設定
  - [ ] 静的ファイルの配信設定
- [ ] フロントエンド機能の実装
  - [ ] フォーム送信処理
  - [ ] ローディング表示
  - [ ] エラー表示
  - [ ] コピーボタン機能（クリップボードAPI）

**成果物**:
- [ ] `app/templates/index.html`
- [ ] `app/templates/result.html`
- [ ] `app/static/style.css`
- [ ] JavaScript（インラインまたは別ファイル）

**依存関係**: Phase 2完了（Phase 3は並行可能）

**進捗状況**: ⬜ 未着手

**備考**: モックデータでUI確認可能

---

### 11.6 Phase 5: テスト・デモ準備

**目的**: 動作確認、ドキュメント作成、デモ準備

**期間**: 1-2日

**タスクリスト**:

- [ ] 単体テストの実装（オプション）
  - [ ] 判断ロジックのテスト
  - [ ] コマンド生成のテスト
  - [ ] バリデーションのテスト
- [ ] 統合テスト・動作確認
  - [ ] エンドツーエンドの動作確認
  - [ ] エラーケースの確認
  - [ ] ログ出力の確認
- [ ] README.mdの作成
  - [ ] プロジェクト概要
  - [ ] 環境構築手順
  - [ ] 起動方法
  - [ ] デモ手順
  - [ ] 注意事項（完全自動化ではない旨）
- [ ] デモシナリオの確認
  - [ ] シナリオ1（正社員）の動作確認
  - [ ] シナリオ2（派遣）の動作確認
- [ ] セキュリティチェック
  - [ ] APIキーの管理確認
  - [ ] 入力サニタイズ確認
  - [ ] ログの機密情報確認
- [ ] パフォーマンス確認
  - [ ] APIレスポンス時間の確認
  - [ ] エラーハンドリングの確認

**成果物**:
- [ ] `README.md`
- [ ] テスト結果レポート（オプション）
- [ ] デモ用サンプルデータ
- [ ] 動作確認済みシステム

**依存関係**: Phase 1-4完了

**進捗状況**: ⬜ 未着手

**備考**: デモ前に必ず全機能の動作確認を行う

---

### 11.7 進捗管理表

**全体進捗**: 0% (0/5 フェーズ完了)

| フェーズ | 状態 | 進捗率 | 開始日 | 完了日 | 担当者 | 備考 |
|---------|------|--------|--------|--------|--------|------|
| Phase 1 | ⬜ 未着手 | 0% | - | - | - | - |
| Phase 2 | ⬜ 未着手 | 0% | - | - | - | - |
| Phase 3 | ⬜ 未着手 | 0% | - | - | - | - |
| Phase 4 | ⬜ 未着手 | 0% | - | - | - | - |
| Phase 5 | ⬜ 未着手 | 0% | - | - | - | - |

**ブロッカー・課題**:
- （現在なし）

**次のアクション**:
- Phase 1の開始準備

**進捗更新方法**:
1. 各フェーズの状態を更新（⬜ → 🔵 → ✅）
2. 進捗率を更新（完了タスク数 / 全タスク数 × 100）
3. 開始日・完了日を記録
4. ブロッカーがある場合は「ブロッカー・課題」セクションに記載

---

### 11.8 マイルストーン

| マイルストーン | 目標日 | 状態 | 成果物 |
|--------------|--------|------|--------|
| M1: 環境構築完了 | - | ⬜ 未達成 | Phase 1完了 |
| M2: コア機能完成 | - | ⬜ 未達成 | Phase 2完了 |
| M3: AI連携完成 | - | ⬜ 未達成 | Phase 3完了 |
| M4: UI完成 | - | ⬜ 未達成 | Phase 4完了 |
| M5: デモ準備完了 | - | ⬜ 未達成 | Phase 5完了 |

---

## 12. 成果物

### 12.1 必須成果物

- [ ] FastAPIアプリケーション（`app/main.py`）
- [ ] HTMLテンプレート（`app/templates/`）
- [ ] PowerShellテンプレート（`templates/powershell/`）
- [ ] README.md（起動方法・デモ手順）
- [ ] requirements.txt（依存パッケージ）
- [ ] .env.example（環境変数テンプレート）

### 12.2 推奨成果物

- [ ] 設定ファイル（`app/config.py`）
- [ ] ログ設定ファイル
- [ ] デモ用サンプルデータ

---

## 13. 承認・レビュー

### 13.1 レビューポイント

- [ ] セキュリティ要件の遵守確認
- [ ] 入力バリデーションの実装確認
- [ ] エラーハンドリングの実装確認
- [ ] ログ出力の実装確認
- [ ] デモシナリオの動作確認

### 13.2 承認者

- 技術リーダー
- セキュリティ担当者
- 営業担当者（デモ確認）

---

## 付録A: 用語集

| 用語 | 説明 |
|------|------|
| BPO | Business Process Outsourcing（業務プロセスアウトソーシング） |
| PoC | Proof of Concept（概念実証） |
| WinRM | Windows Remote Management |
| M365 | Microsoft 365 |
| AD | Active Directory |

---

## 付録B: 参考資料

- FastAPI公式ドキュメント: https://fastapi.tiangolo.com/
- OpenAI API ドキュメント: https://platform.openai.com/docs
- PowerShell Active Directory モジュール: https://docs.microsoft.com/powershell/module/activedirectory/

---

**文書バージョン**: 1.0  
**最終更新日**: 2024年  
**作成者**: BPO向け業務自動化AIプロジェクトチーム

