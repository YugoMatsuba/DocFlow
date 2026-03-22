# Agent Spec Template

AIエージェントに機能実装や修正を依頼するときに使うテンプレート。

---

## 1. 背景

この変更が必要になった背景を書く。

例:
- 実行方式の責務が Router に漏れている
- 新しいノードを追加したい
- README と実装がズレている

## 2. 目的

この変更で達成したいことを書く。

例:
- `ExecutionDispatcher` を導入して非同期起動方式を抽象化したい
- `TRANSLATE` ノードを追加したい
- 実行一覧画面から状態確認しやすくしたい

## 3. スコープ

今回やることを明記する。

例:
- `ExecutionDispatcher` interface を追加する
- `BackgroundTasksExecutionDispatcher` を追加する
- Router の `BackgroundTasks` 直接依存を外す

## 4. 非スコープ

今回やらないことを書く。

例:
- ワーカーキューへの移行はしない
- DAG 対応はしない
- 認証機能は追加しない

## 5. 変更対象ファイル

変更対象として想定しているファイルを書く。

例:
- `server/api/routers/executions.py`
- `server/services/execution_service.py`
- `server/api/dependencies.py`
- `server/services/execution_dispatcher.py`

## 6. 設計方針

実装時に守ってほしい設計上の制約を書く。

例:
- Router に業務ロジックを増やさない
- 既存のレイヤ構成を維持する
- 新しい具体依存は抽象の背後に隠す
- 既存の ADR と矛盾しないようにする

## 7. 実装要件

必要な具体要件を書く。

例:
- `dispatch(execution_id, handler)` を持つ dispatcher を追加する
- 現行実装では `BackgroundTasks` を使う
- `process_workflow_execution()` は現状のまま利用する
- README に構成変更を反映する

## 8. 受け入れ条件

この変更が完了したと判断する条件を書く。

例:
- Router が `background_tasks.add_task(...)` を直接呼んでいない
- `ExecutionService` が dispatcher 抽象を経由して非同期起動する
- 既存 API が壊れていない
- 構文エラーがない

## 9. 検証方法

最低限やってほしい確認を書く。

例:

```bash
cd server
python -m compileall .
```

```bash
cd client
npm run build
```

必要なら追加:
- API の手動確認
- `alembic upgrade head`
- 特定エンドポイントの疎通確認

## 10. ドキュメント更新要否

以下を更新する必要があるかを書く。

- README
- ADR
- `.env.example`
- テスト

## 11. 補足コンテキスト

実装者が知っておくと良い背景や判断を書く。

例:
- 今は MVP なので過度な抽象化は避けたい
- 将来キュー移行したいが、今は `BackgroundTasks` 維持でよい
- 課題提出向けなので説明可能性を重視したい

---

## 記入例

### 背景

Execution の非同期実行方式が Router に漏れているため、将来キューへ移行するときに API 層まで変更が波及しやすい。

### 目的

非同期実行起動方式を抽象化し、Router が `ExecutionService` にのみ依存する形へ整理したい。

### スコープ

- `ExecutionDispatcher` interface を追加
- `BackgroundTasksExecutionDispatcher` を追加
- `ExecutionService` から dispatcher を使う
- Router から `BackgroundTasks` 直接依存を除去

### 非スコープ

- Redis / Celery の導入
- `process_workflow_execution()` の大規模分離
- execution status の enum 再設計
