# ADR-005: API設計方針

## 背景・解決したい課題

このプロダクトでは、ワークフロー定義そのものと、ワークフロー実行結果を別の概念として扱う必要がある。ワークフローは再利用される定義であり、Execution はその定義をもとに個別の入力ファイルで実行された履歴である。

そのため、API設計でも「ワークフローを作る/更新する責務」と「ワークフローを実行し、その状態を追う責務」を分離したい。また、MVPの段階でクライアント実装が複雑になりすぎないことも重要だった。

## 決定事項

**Resource-oriented なAPI設計を採用し、`workflows` と `executions` を分けた**。

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
- Workflow と Execution を別 resource として扱う
- 実行状態の参照や履歴取得を自然な API にする
- ワークフローの作成・編集と、実行・状態確認のユースケースを分離する
- MVPでは操作数を絞り、クライアントが理解しやすい構成にする

## 選択肢

### Option1: `workflows` と `executions` を分けた resource-oriented API

👍**Pros**
- 実行履歴を first-class resource として扱える
- 実行状態取得APIが自然に設計できる
- 非同期実行の表現に向いている
- 将来の一覧、再実行、監査ログ拡張にもつなげやすい

👎**Cons**
- `workflow_id` の受け渡し方に少し設計判断が必要
- シンプルな `/run` エンドポイントより数は増える

### Option2: `POST /workflows/{workflow_id}/run` のようなRPC寄りAPI

👍**Pros**
- 初学者にはわかりやすい
- エンドポイントが直感的
- 最初の実装はしやすい

👎**Cons**
- Execution を独立した resource として扱いづらい
- 実行状態の参照や履歴との整合が弱い
- 非同期処理を resource model で表現しづらい

### Option3: 汎用アクションAPIに寄せる

👍**Pros**
- 柔軟に見える
- 将来いろいろな操作を載せやすい

👎**Cons**
- APIの意味が曖昧になりやすい
- REST寄りの一貫性が下がる
- クライアントとドキュメント双方で理解しづらい

## 懸念事項・影響範囲

- **workflow_id の位置**: 現在はファイルアップロードを簡潔に扱うため、Execution開始時は query parameter にしている
- **将来の拡張**: 再実行、キャンセル、フィルタ付き一覧が必要になった場合は `executions` resource に自然に追加しやすい
- **一貫性**: Workflow操作とExecution操作を別resourceにしているため、用途ごとの責務は明確だが、クライアント側には2系統のAPI理解が必要
- **MVP判断**: 今のAPI数はやや増えるが、非同期実行の表現としては妥当で説明しやすい
