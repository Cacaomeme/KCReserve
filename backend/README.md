# Backend (Flask + uv)

山小屋予約システムのバックエンドを [uv](https://github.com/astral-sh/uv) で管理します。Flask + SQLite をベースに、Alembic でスキーマをバージョン管理しながら予約・認証機能を実装していきます。

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

# Alembic: リビジョン作成（モデル変更後）
uv run alembic revision --autogenerate -m "change summary"

# Alembic: 最新リビジョンを適用
uv run alembic upgrade head
```

### 環境変数 (.env 推奨)
```
SECRET_KEY=change-me
JWT_SECRET_KEY=change-me
DATABASE_URL=sqlite:///instance/app.db
ALLOWED_ORIGINS=http://localhost:5173
```

## ディレクトリ構成 (抜粋)
```
backend/
├── app/
│   ├── __init__.py        # Flaskアプリ工場
│   ├── config.py          # 設定ロード
│   ├── database.py        # SQLAlchemyエンジン/Session
│   ├── main.py            # Flask実行エントリ
│   ├── models/
│   │   ├── reservation.py # Reservationテーブル定義
│   │   ├── user.py        # Userテーブル定義
│   │   └── whitelist.py   # Whitelistテーブル定義
│   ├── routes/
│   │   ├── auth.py        # 認証 + ホワイトリストAPI
│   │   ├── health.py      # ヘルスチェックAPI
│   │   └── reservations.py# 予約API
│   └── routes/
│       └── health.py      # ヘルスチェックAPI
├── migrations/            # Alembicリビジョン
│   └── versions/
├── tests/
│   └── test_health.py     # 最小テスト
├── pyproject.toml
└── README.md
```

## Alembic 初期化の流れ
1. `uv run alembic init migrations` … プロジェクト初期のみ実行。
2. `app/models/` にテーブル定義を追加し、`app/database.Base` を継承させる。
3. `uv run alembic revision --autogenerate -m "create <table>"` で差分を作成。
4. `uv run alembic upgrade head` で SQLite に適用。

`migrations/env.py` はアプリ設定 (`app.config`) を読み込み、`Base.metadata` をターゲットに自動生成するよう調整済みです。

### 定義済みテーブル概要
- `users`: ログイン可能なメンバー。`is_admin` フラグで管理者を判別。
- `whitelist_entries`: 招待メールアドレス。`is_admin_default` で初期権限を制御。
- `reservations`: 予約申請。`status` (pending/approved...) と `visibility` (public/anonymous) を持ちます。

### 実装済みAPI (抜粋)
- `POST /api/auth/register` … ホワイトリスト対象メールのみ登録可能。JWT アクセストークンを返却。
- `POST /api/auth/login` … 認証後に JWT を発行。
- `GET /api/auth/me` … JWT 必須。ログイン中ユーザー情報を返却。
- `GET /api/auth/whitelist-check?email=...` … UI用のホワイトリスト事前確認。
- `POST /api/reservations` … 認証済みユーザーが予約申請（pending）。
- `GET /api/reservations` … 公開カレンダー向け。管理者はクエリを指定せずとも全件取得。
- `GET /api/reservations/mine` … ログイン中ユーザーの予約履歴。
- `GET /api/admin/whitelist` … 管理者向けホワイトリスト一覧。
- `POST /api/admin/whitelist` … 管理者がメールを追加。
- `DELETE /api/admin/whitelist/<id>` … 管理者がエントリを削除。
- `PATCH /api/admin/reservations/<id>/status` … 管理者が承認/却下や公開設定を更新。

今後は `app` 配下にモデル、サービス、Blueprint を追加しながら機能を拡張します。
