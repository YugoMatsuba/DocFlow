# ADR-005: API 設計方針

## 背景・解決したい課題

このプロダクトでは、ワークフロー定義そのものと、ワークフロー実行結果を別の概念として扱う必要がある。ワークフローは再利用される定義であり、Execution はその定義をもとに個別の入力ファイルで実行された履歴である。

そのため API でも、「ワークフローを作る・編集する責務」と「ワークフローを実行し、状態や結果を参照する責務」を分けたかった。また、MVP の段階でクライアント実装が複雑になりすぎないことも重要だった。

## 決定事項

**resource-oriented な API を採用し、`workflows` と `executions` を別 resource として扱う**。

現時点の主要エンドポイントは以下とする。

- `POST /api/workflows/`
- `GET /api/workflows/`
- `GET /api/workflows/{workflow_id}`
- `POST /api/workflows/{workflow_id}/nodes`
- `GET /api/workflows/{workflow_id}/validate`
- `POST /api/executions/?workflow_id={workflow_id}` + multipart file upload
- `GET /api/executions/`
- `GET /api/executions/{execution_id}`
- `GET /`
- `GET /health`

設計意図は以下である。

- Workflow と Execution を別 resource として表現する
- 非同期実行を自然に API モデルへ落とし込む
- 実行状態の参照や履歴取得を扱いやすくする
- ワークフロー編集系 API と実行系 API の責務を分ける

## 選択肢

### Option1: `workflows` と `executions` を分けた resource-oriented API

👍**Pros**

- 実行履歴を first-class resource として扱える
- 実行状態取得 API が自然に設計できる
- 非同期実行の表現に向いている
- 将来の一覧、再実行、監査ログ拡張にもつなげやすい

👎**Cons**

- `workflow_id` の受け渡し位置に設計判断が必要
- 単純な `/run` エンドポイントより数は増える

### Option2: `POST /workflows/{workflow_id}/run` のような RPC 寄り API

👍**Pros**

- 初見ではわかりやすい
- エンドポイントの意図が直感的
- 初期実装はしやすい

👎**Cons**

- Execution を独立 resource として扱いづらい
- 実行状態参照や履歴との整合が弱い
- 非同期処理を API モデルとして説明しづらい

### Option3: 汎用アクション API に寄せる

👍**Pros**

- 柔軟に見える
- 将来さまざまな操作を載せやすい

👎**Cons**

- API の意味が曖昧になりやすい
- 一貫性が下がりやすい
- クライアントとドキュメントの双方で理解しづらい

## 懸念事項・影響範囲

- **workflow_id の位置**: 現在はファイルアップロードを簡潔に扱うため、Execution 開始時は query parameter にしている
- **将来拡張**: 再実行、キャンセル、フィルタ付き一覧が必要になった場合も `executions` resource に追加しやすい
- **クライアント理解コスト**: Workflow 系と Execution 系の API を分けているため、責務は明確だが理解対象は増える
- **MVP とのバランス**: API 数はやや増えるが、非同期実行を表現するには妥当な複雑さと判断した
