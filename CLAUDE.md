# LayerX Agent Rules

## 目的

このファイルは、コーディングエージェントが LayerX Workflow Engine を安全かつ効率的に開発するためのルールを定義する。

## リポジトリ概要

- `server/`: FastAPI バックエンド
- `client/`: React + Vite フロントエンド
- `adr/`: 設計判断の記録
- `README.md`: セットアップと全体像

## アーキテクチャの前提

- レイヤ構成は `api -> services -> domain <- infra`
- HTTP 入出力は `server/api/`
- ユースケースのオーケストレーションは `server/services/`
- エンティティ、ルール、抽象は `server/domain/`
- DB、外部API、ファイル保存は `server/infra/`
- 実行起動方式は `ExecutionDispatcher` で抽象化されている

## 最優先ルール

1. 既存の責務分離を壊さない
2. Router に業務ロジックを増やさない
3. 新しいノード追加時は既存ノードの分岐を増やしすぎない
4. 既存の ADR と README と矛盾する変更をしない
5. 不要な大規模リファクタを避け、MVPに必要な変更を優先する

## 実装ルール

### バックエンド

- API 層では HTTP ハンドリングに集中し、業務ロジックは `services` に寄せる
- DB アクセスは repository 経由を優先する
- 外部APIやファイルI/Oは `infra` に閉じ込める
- 例外は可能な限り意味のある単位で処理し、失敗時の `Execution` 状態更新を忘れない

### ワークフロー / ノード

- 新しい NodeType を追加する場合は以下をセットで見直す
  - `domain/enums/node_type.py`
  - `services/processors/`
  - `services/processors/registry.py`
  - `domain/specs/node_spec_registry.py`
  - 必要に応じて `domain/rules/workflow_rules.py`
- ノードごとの設定検証は processor 側に寄せる
- ノードの入出力制約は `NodeSpec` 側で明示する

### 非同期実行

- 実行起動方式を変える場合は Router ではなく Dispatcher 実装を優先して変更する
- `ExecutionService` は `ExecutionDispatcher` 抽象に依存させる
- `BackgroundTasks` や将来のキュー実装の詳細を Router に漏らさない

### フロントエンド

- API パスは `client/src/api.ts` に集約する
- 画面ごとの責務は `client/src/components/` に閉じ込める
- UI変更時は実際の API 仕様とズレないように注意する

## 変更時の確認ポイント

- 追加・変更した API が README と矛盾していないか
- 新規設定値が `.env.example` に反映されているか
- 実行状態や失敗時メッセージの整合が取れているか
- 既存の ADR で説明している設計意図に反していないか

## 推奨作業フロー

1. 先に関連ファイルを読む
2. 変更の影響範囲を把握する
3. 必要最小限の差分で実装する
4. 検証コマンドを実行する
5. README / ADR / テスト更新が必要か確認する

## 推奨確認コマンド

### バックエンド

```bash
cd server
python -m compileall .
```

```bash
cd server
uvicorn main:app --reload
```

### マイグレーション

```bash
cd server
alembic upgrade head
```

### フロントエンド

```bash
cd client
npm run build
```

## 避けるべきこと

- 未依頼の全面リネーム
- Router に大量の業務ロジックを追加すること
- `if/elif` の巨大分岐でノード追加を実装すること
- README や ADR を置き去りにすること
- 内部用ファイルやバックアップファイルを成果物に混ぜること

## エージェントへの期待

- 変更理由を説明できること
- 局所最適ではなく、今のアーキテクチャとの整合を意識すること
- MVPらしい実装速度と、将来変更しやすい構造のバランスを取ること
