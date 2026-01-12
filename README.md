# BPO向け業務自動化AIデモシステム

BPO向け業務自動化AIデモシステムは、人が毎日PowerShellで行っているインフラ業務（入社処理など）について、AIが「判断＋PowerShellコマンド生成」までを行い、実行はWindows上で人が行う"半自動"デモシステムです。

## ⚠️ 重要な注意事項

**このシステムは完全自動化システムではありません。**

- AI（FastAPI）は PowerShell を実行しません
- OS操作、WinRM、SSH 等は一切使いません
- AIは「判断・文章・コード生成のみ」を行います
- **実行は Windows の PowerShell で人が Enter を押して行います**
- 既存のBPO運用を壊さずAIを差し込む思想で設計されています
- セキュリティレビューを通る設計になっています

## システム構成

- **バックエンド**: FastAPI（Python）
- **フロントエンド**: FastAPIのHTMLテンプレート（シンプルなUI）
- **実行環境**: Windows（ブラウザ＋PowerShell）
- **コマンド生成**: テンプレートベース（PowerShellテンプレートを使用）
- **用途**: 営業用PoC / デモ

## 機能

### 入社処理（Onboarding）

新入社員情報を入力すると、システムが雇用形態に基づいて判断し、適切なPowerShellコマンドを生成します。

- **正社員**: 標準ユーザー + Microsoft 365 E3
- **派遣**: 制限ユーザー + Microsoft 365 Basic + 有効期限設定

## セットアップ

### 1. 前提条件

- Python 3.9以上（3.14でも動作確認済み）
- pip（Pythonパッケージマネージャー）
- OpenAI APIキー（設定ファイルの読み込み用、現在はテンプレートベースで動作）

### 2. 環境構築

```bash
# プロジェクトディレクトリに移動
cd entersystem2

# Python仮想環境を作成（推奨）
python -m venv venv

# 仮想環境を有効化
# Windowsの場合:
venv\Scripts\activate
# macOS/Linuxの場合:
source venv/bin/activate

# 依存パッケージをインストール
pip install -r requirements.txt
```

### 3. 環境変数の設定

`.env.example`を参考に、`.env`ファイルを作成してください：

```bash
# .env.exampleをコピー
cp .env.example .env
```

`.env`ファイルを編集して、OpenAI APIキーを設定してください：

```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
```

## 起動方法

### 開発モードで起動

```bash
# 仮想環境が有効化されていることを確認
# FastAPIアプリケーションを起動
python -m app.main

# または uvicorn を直接使用
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### ブラウザでアクセス

起動後、以下のURLにアクセスしてください：

```
http://localhost:8000
```

## デモ手順

### シナリオ1: 正社員の入社処理

1. ブラウザで `http://localhost:8000` にアクセス
2. 入力フォームに以下を入力：
   - 顧客名: "株式会社デモ"
   - 従業員名: "佐藤 花子"
   - 雇用形態: "正社員"
   - 部署: "開発部"
3. 「PowerShellコマンドを生成」ボタンをクリック
4. 生成されたPowerShellコマンドを確認
5. コマンドをコピーして、Windows PowerShellで実行（デモでは実際には実行しない）

### シナリオ2: 派遣社員の入社処理

1. 入力フォームに以下を入力：
   - 顧客名: "株式会社デモ"
   - 従業員名: "鈴木 一郎"
   - 雇用形態: "派遣"
   - 部署: "営業部"
2. 「PowerShellコマンドを生成」ボタンをクリック
3. 正社員と異なる判断結果（制限ユーザー + Basicライセンス + 有効期限設定）を確認

## プロジェクト構成

```
entersystem2/
├── README.md                 # 本ファイル
├── REQUIREMENTS.md          # 要件定義書
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
│   │   ├── judgment_service.py  # 判断ロジック
│   │   └── command_generator.py  # PowerShell生成
│   ├── templates/
│   │   └── index.html       # 入力フォーム・結果表示
│   └── static/
│       └── style.css        # CSS
│
└── templates/
    └── powershell/          # PowerShellテンプレート
        ├── onboarding_regular.ps1
        └── onboarding_contract.ps1
```

## APIエンドポイント

### POST `/api/onboarding`

入社処理のPowerShellコマンドを生成します。

**リクエスト例**:
```json
{
  "company": "株式会社サンプル",
  "task_type": "onboarding",
  "employee_name": "山田 太郎",
  "employment_type": "正社員",
  "department": "営業部"
}
```

**レスポンス例**:
```json
{
  "status": "success",
  "judgment": "このユーザーは正社員のため、標準ユーザーとして作成し、Microsoft 365 E3 ライセンスを付与します。",
  "powershell_command": "# Active Directory ユーザー作成\n..."
}
```

### GET `/health`

ヘルスチェックエンドポイントです。

## ログ

アプリケーションのログは標準出力に出力されます。以下の情報が記録されます：

- 入力JSON（リクエスト受信時）
- 判断結果（雇用形態、ユーザータイプ、ライセンス）
- 生成されたPowerShellコマンド（生成完了時）
- エラー情報（エラー発生時）

ログ形式：
```
[YYYY-MM-DD HH:MM:SS] [INFO] 入力受信: {"company": "...", ...}
[YYYY-MM-DD HH:MM:SS] [INFO] 判断結果: 正社員 -> 標準ユーザー + Microsoft 365 E3
[YYYY-MM-DD HH:MM:SS] [INFO] PowerShell生成完了
```

## トラブルシューティング

### OpenAI APIキーが設定されていない

現在の実装ではテンプレートベースでコマンドを生成するため、OpenAI APIキーは必須ではありませんが、設定ファイルの読み込みでエラーが出る場合は`.env`ファイルに`OPENAI_API_KEY`を設定してください（ダミー値でも可）。

### ポート8000が既に使用されている

`.env`ファイルで`PORT`を変更するか、起動時にポートを指定してください：

```bash
uvicorn app.main:app --port 8080
```

### モジュールが見つからない

仮想環境が有効化されているか確認してください。また、`pip install -r requirements.txt`で依存パッケージがインストールされているか確認してください。

## ライセンス

このプロジェクトは営業用PoC / デモ用途です。

## 参考資料

- [FastAPI公式ドキュメント](https://fastapi.tiangolo.com/)
- [OpenAI API ドキュメント](https://platform.openai.com/docs)
- [PowerShell Active Directory モジュール](https://docs.microsoft.com/powershell/module/activedirectory/)

