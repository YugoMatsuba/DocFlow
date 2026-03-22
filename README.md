# LayerX Workflow Engine

PDFを入力として、複数ノードからなるワークフローを定義・実行できるドキュメント処理アプリケーションです。  
バックエンドは FastAPI、フロントエンドは React + Vite、永続化には PostgreSQL を利用しています。

## アプリケーション概要

- ワークフローを作成できる
- ワークフローにノードを追加できる
- PDF をアップロードしてワークフローを非同期実行できる
- 実行履歴、実行状態、結果、失敗理由を参照できる
- `EXTRACT_TEXT`、`GENERATIVE_AI`、`FORMATTER` の3種類のノードを利用できる

```mermaid
flowchart LR
    U[ユーザー] --> FE[React Frontend]
    FE --> API[FastAPI API]
    API --> DB[(PostgreSQL)]
    API --> FS[ローカルファイル保存<br/>server/uploads]
    API --> OA[OpenAI API]

    DB --> API
    FS --> API
    OA --> API
    API --> FE
```

## 現状の設計

現状はレイヤードアーキテクチャを採用し、`api`、`services`、`domain`、`infra` の責務を分離しています。  
ワークフロー実行の起動方式は `ExecutionDispatcher` で抽象化しており、MVP では `BackgroundTasks` 実装を利用しています。

### レイヤーごとの役割

#### `api`

- FastAPI の Router、Schema、Dependency Injection を担当
- HTTP リクエストを受けて、入力を application service に渡し、HTTP レスポンスへ変換する
- 具体的な非同期実行方式や DB 実装はここで直接扱わない

工夫したポイント:

- Router に業務ロジックを寄せすぎないようにし、HTTP の責務に集中させている
- 依存解決は `dependencies.py` に集約し、具体実装の差し替え箇所を明確にしている

#### `services`

- ユースケースのオーケストレーションを担当
- Workflow の作成・検証、Execution の作成・起動・状態更新を扱う
- ProcessorRegistry を使ってノード処理を実行し、Dispatcher を通じて非同期起動する

工夫したポイント:

- `ExecutionService` は `ExecutionDispatcher` 抽象に依存させ、起動方式の詳細を隠している
- ノード追加時に service 側へ巨大な分岐を書かなくて済むよう、processor と registry を組み合わせている

#### `domain`

- Entity、Enum、Repository interface、Rule、Spec を担当
- ワークフローの整合性やノード入出力制約など、業務上のルールを表現する

工夫したポイント:

- `WorkflowRules` にワークフローの検証ロジックを分離し、service の責務を軽くしている
- `NodeSpec` / `NodeSpecRegistry` にノードの入出力制約を切り出し、ルールと実装詳細を分離している
- Repository interface を domain 側に置き、上位層が DB 実装に直接依存しないようにしている

#### `infra`

- PostgreSQL への永続化、OpenAI API 呼び出し、ファイル保存、BackgroundTasks 実装などを担当
- domain / service が必要とする外部依存の具体実装を提供する

工夫したポイント:

- SQLAlchemy repository に DB 実装を閉じ込め、service は repository interface だけを見る構成にしている
- `BackgroundTasksExecutionDispatcher` を adapter として置き、FastAPI 固有の仕組みを service/Router から分離している
- `FileStorage`、`OpenAIClient` を分けて、I/O 系の責務を一点にまとめている

### 設計上の工夫

- **高凝集**: レイヤーごとに責務を分け、変更理由が異なるコードを同じ場所に集めすぎないようにしている
- **疎結合**: repository や dispatcher を抽象化し、具体実装の変更が上位層に波及しにくい構造にしている
- **MVP と将来拡張の両立**: 現時点では `BackgroundTasks` を使ってシンプルに実装しつつ、Dispatcher 抽象で将来のキュー移行余地を残している
- **ノード追加のしやすさ**: processor、registry、NodeSpec を分けることで、新しい NodeType 追加時の影響範囲を局所化している
- **ルールの明示**: ノードの入出力制約や workflow の成立条件を domain 側に寄せ、コード上で説明可能な形にしている

ワークフロー実行時の流れは以下です。

## ディレクトリ構成

```text
.
├── adr/                    # ADR
├── client/                 # React + Vite フロントエンド
│   ├── src/                # 画面、API クライアント、型定義
│   ├── package.json
│   └── vite.config.ts
├── docs/                   # エージェント運用資料、Spec テンプレート
├── server/                 # FastAPI バックエンド
│   ├── api/                # Router、Schema、DI
│   ├── domain/             # Entity、Rule、Spec、Repository interface
│   ├── infra/              # DB、外部 API、ファイル保存などの実装
│   ├── services/           # ユースケース実装、processor、dispatcher
│   ├── alembic/            # マイグレーション
│   ├── config/             # 設定管理
│   ├── main.py             # FastAPI エントリポイント
│   └── requirements.txt
├── CLAUDE.md               # エージェント向け開発ルール
└── README.md
```

## 技術スタック

- Backend: FastAPI, SQLAlchemy, Alembic
- Frontend: React, React Router, Vite, TypeScript
- Database: PostgreSQL
- File handling: Python multipart upload + ローカル保存
- PDF parsing: PyPDF2
- AI integration: OpenAI API

## 前提環境

- Python 3.9 以上
- Node.js 18 以上を推奨
- npm
- PostgreSQL

## セットアップ

### 1. PostgreSQL を用意する

ローカルで PostgreSQL を起動し、接続先 DB を作成してください。  
デフォルトでは以下を想定しています。

- DB 名: `layerx_workflow_db`
- ユーザー: `postgres`
- パスワード: `postgres`
- ポート: `5432`

必要に応じて `server/.env` 側で変更してください。

### 2. バックエンドをセットアップする

```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` の主な項目:

- `DATABASE_URL`
- `DATABASE_URL_SYNC`
- `UPLOAD_DIR`
- `MAX_FILE_SIZE`
- `OPENAI_API_KEY`

補足:

- `OPENAI_API_KEY` は `GENERATIVE_AI` ノードを使う場合に必要です
- `REDIS_URL` は将来拡張用で、現状の MVP 実装では利用していません

### 3. マイグレーションを適用する

```bash
cd server
source .venv/bin/activate
alembic upgrade head
```

### 4. バックエンドを起動する

```bash
cd server
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

起動後のURL:

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### 5. フロントエンドを起動する

```bash
cd client
npm install
npm run dev
```

起動後のURL:

- Frontend: `http://localhost:3000`

## 使い方

1. ワークフローを作成する
2. ワークフロー詳細画面でノードを追加する
3. 必要に応じてワークフローを検証する
4. 実行画面から PDF をアップロードして実行する
5. Execution 一覧または詳細画面で状態と結果を確認する

## 対応ノード

### `EXTRACT_TEXT`

- 入力: PDF ファイル
- 出力: 抽出済みテキスト

### `GENERATIVE_AI`

- 入力: テキスト
- 出力: 生成テキスト
- 主な設定:
  - `prompt`
  - `model`
  - `temperature`
  - `max_tokens`

### `FORMATTER`

- 入力: テキスト
- 出力: 整形済みテキスト
- 主な設定:
  - `format_type`
- 対応フォーマット:
  - `uppercase`
  - `lowercase`
  - `trim`
  - `replace`

## API 一覧

ベースパスは `/api` です。

### Workflow API

- `POST /api/workflows/`
- `GET /api/workflows/`
- `GET /api/workflows/{workflow_id}`
- `POST /api/workflows/{workflow_id}/nodes`
- `GET /api/workflows/{workflow_id}/validate`

### Execution API

- `POST /api/executions/?workflow_id={workflow_id}`
  - `multipart/form-data` で PDF ファイルをアップロード
- `GET /api/executions/`
- `GET /api/executions/{execution_id}`

## 現状の設計上のポイント

- 非同期実行は `BackgroundTasks` を利用した in-process 実装
- 将来のキュー移行に備え、実行起動方式は `ExecutionDispatcher` で抽象化
- ノード処理は `ProcessorRegistry` と各 Processor に分離
- ノードの入出力制約は `NodeSpec` と `WorkflowRules` で管理
- 実行結果と状態は DB に永続化

## ADR

設計判断は `adr/` 配下に記録しています。

- `001-database-selection`
- `002-asynchronous-processing`
- `003-software-architecture`
- `004-node-expansion`
- `005-api-design`
- `006-realtime`

## 補足

- アップロードされたファイルは `server/uploads/` に保存されます
- ログは `server/logs/` に出力されます
- 現在の CORS 設定は `http://localhost:3000` を許可しています
- アプリ起動時に `create_tables()` も呼ばれますが、スキーマ管理は Alembic を正としています
