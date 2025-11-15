# Backend (Flask + uv)

山小屋予約システムのバックエンドを [uv](https://github.com/astral-sh/uv) で管理します。Flask と SQLite を使った API を提供し、今後の開発で予約・認証機能を追加していきます。

## 前提
- Windows PowerShell で `uv` が使える状態 (`uv --version`で確認)
- リポジトリ直下 `backend/` ディレクトリに移動済み

## よく使うコマンド
```powershell
# 依存関係のインストール（pyproject参照）
uv sync

# Flask開発サーバーを起動
uv run flask --app app.main run --debug

# 単発でPythonスクリプトを実行
uv run python main.py

# pytestでテスト
uv run pytest
```

### 環境変数 (.env 推奨)
```
SECRET_KEY=change-me
DATABASE_URL=sqlite:///instance/app.db
ALLOWED_ORIGINS=http://localhost:5173
```

## ディレクトリ構成 (抜粋)
```
backend/
├── app/
│   ├── __init__.py        # Flaskアプリ工場
│   ├── config.py          # 設定ロード
│   ├── main.py            # Flask実行エントリ
│   └── routes/
│       └── health.py      # ヘルスチェックAPI
├── tests/
│   └── test_health.py     # 最小テスト
├── pyproject.toml
└── README.md
```

今後は `app` 配下にモデル、サービス、Blueprint を追加しながら機能を拡張します。
