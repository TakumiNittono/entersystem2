# Windows環境でのセットアップ・実行ガイド

このドキュメントは、Windows環境でBPO向け業務自動化AIデモシステムを実行するための詳細な手順です。

## 前提条件

- Windows 10/11
- Python 3.9以上（Python 3.14でも動作確認済み）
- PowerShell 5.1以上（Windowsに標準搭載）
- インターネット接続（依存パッケージのダウンロード用）

## セットアップ手順

### 1. Pythonのインストール確認

```powershell
# PowerShellで実行
python --version
```

Pythonがインストールされていない場合は、[Python公式サイト](https://www.python.org/downloads/)からダウンロードしてインストールしてください。

**重要**: インストール時に「Add Python to PATH」にチェックを入れてください。

### 2. プロジェクトのクローンまたはダウンロード

```powershell
# GitHubからクローンする場合
git clone https://github.com/TakumiNittono/entersystem2.git
cd entersystem2

# または、ZIPファイルをダウンロードして展開
```

### 3. 仮想環境の作成と有効化

```powershell
# PowerShellで実行（管理者権限は不要）

# 仮想環境を作成
python -m venv venv

# 仮想環境を有効化
venv\Scripts\activate

# プロンプトの前に (venv) が表示されれば成功
```

### 4. 依存パッケージのインストール

```powershell
# 仮想環境が有効化されている状態で実行

# pipを最新版にアップグレード
python -m pip install --upgrade pip

# 依存パッケージをインストール
pip install -r requirements.txt
```

### 5. 環境変数の設定

```powershell
# .env.exampleをコピーして.envファイルを作成
Copy-Item .env.example .env

# .envファイルを編集（メモ帳などで開く）
notepad .env
```

`.env`ファイルを編集して、以下を設定してください：

```
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
```

**注意**: `.env`ファイルは機密情報を含むため、Gitにコミットされません（`.gitignore`に含まれています）。

## 起動方法

### 方法1: Pythonモジュールとして起動（推奨）

```powershell
# 仮想環境が有効化されている状態で実行
python -m app.main
```

### 方法2: uvicornを直接使用

```powershell
# 仮想環境が有効化されている状態で実行
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 起動確認

起動が成功すると、以下のようなメッセージが表示されます：

```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
[2026-01-11 XX:XX:XX] [INFO] BPO業務自動化AIデモシステム v1.0.0 を起動しました
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## ブラウザでのアクセス

### ローカルアクセス

```
http://localhost:8000
```

### 同じネットワーク内の他のPCからアクセス

1. WindowsのIPアドレスを確認：
```powershell
ipconfig
# IPv4アドレスを確認（例: 192.168.1.100）
```

2. 他のPCのブラウザで以下にアクセス：
```
http://192.168.1.100:8000
```

**注意**: Windowsファイアウォールの警告が出る場合は、「アクセスを許可」を選択してください。

## Windowsファイアウォールの設定

初回起動時にWindowsファイアウォールの警告が出る場合：

1. 「プライベートネットワーク」と「パブリックネットワーク」の両方で「アクセスを許可」を選択
2. または、手動でポート8000を開放：
   - Windowsセキュリティ > ファイアウォール > 詳細設定
   - 受信の規則 > 新しい規則
   - ポート > TCP > 特定のローカルポート: 8000 > 接続を許可

## PowerShellスクリプトの実行

生成されたPowerShellコマンドは、Windows PowerShellで実行できます：

1. PowerShellを開く（管理者権限は不要）
2. 生成されたコマンドをコピー
3. PowerShellに貼り付け
4. Enterキーで実行

**Entra ID用スクリプトの場合**:
- Microsoft Graph PowerShellモジュールが必要です
- 初回実行時に `Install-Module -Name Microsoft.Graph -Scope CurrentUser` を実行してください

## トラブルシューティング

### Pythonが見つからない

```
'python' は、内部コマンドまたは外部コマンド、操作可能なプログラムまたはバッチ ファイルとして認識されていません。
```

**解決方法**:
1. Pythonがインストールされているか確認
2. 環境変数PATHにPythonが追加されているか確認
3. PowerShellを再起動

### ポート8000が使用中

```
ERROR: [Errno 48] error while attempting to bind on address ('0.0.0.0', 8000): address already in use
```

**解決方法**:
```powershell
# ポート8000を使用しているプロセスを確認
netstat -ano | findstr :8000

# プロセスIDを確認して終了（例: PIDが12345の場合）
taskkill /PID 12345 /F

# または、別のポートを使用
uvicorn app.main:app --port 8080
```

### モジュールが見つからない

```
ModuleNotFoundError: No module named 'fastapi'
```

**解決方法**:
1. 仮想環境が有効化されているか確認（プロンプトに `(venv)` が表示されているか）
2. 依存パッケージを再インストール：
```powershell
pip install -r requirements.txt
```

### 静的ファイルが読み込まれない

CSSや画像が表示されない場合：

1. `app/static/` ディレクトリが存在するか確認
2. FastAPIの起動ログでエラーが出ていないか確認
3. ブラウザのキャッシュをクリア（Ctrl+Shift+R）

## 停止方法

アプリケーションを停止するには：

1. PowerShellウィンドウで `Ctrl+C` を押す
2. または、PowerShellウィンドウを閉じる

## 次のステップ

- [README.md](README.md) のデモ手順を参照
- PowerShellスクリプトの実行方法を確認
- Entra ID用スクリプトの使用方法を確認

## サポート

問題が発生した場合は、GitHubのIssuesで報告してください。

