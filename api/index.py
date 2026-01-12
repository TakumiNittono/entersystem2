"""
Vercel用のエントリーポイント
FastAPIアプリケーションをVercelのサーバーレス関数として実行
"""

from app.main import app

# Vercel用のエクスポート
handler = app

