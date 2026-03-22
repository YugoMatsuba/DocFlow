# SWE技術課題

本課題（課題1・課題2）では AI / コーディングエージェント等の利用を前提として取り組んでください。

## 課題1

アプリケーション欄に記載のあるようなワークフローアプリケーションがあります。
上記のアプリケーションをここから拡張することを考えてください。

### 概要

このアプリケーションに対して以下の要件を満たすようにバックエンド拡張をしてください。

### 背景・利用シナリオ

このワークフローアプリケーションは、以下のような状況で利用されることを想定しています。

- **社内のドキュメント処理パイプライン**として開発される。初期ユーザーは1チーム（5〜10名）だが、有用性が確認されれば他部署へ展開する計画がある
- **ワークフローの実行特性にばらつきがある**。テキスト整形のような軽量な処理は数秒で完了するが、LLM APIを含むワークフローは外部APIのレイテンシに依存し、数十秒〜数分かかる場合がある
- **運用チームがノードタイプを追加して機能拡張していく想定**だが、運用チームのメンバーはバックエンド全体の設計に精通しているとは限らない。ノード追加者がコアのワークフローエンジンに影響を与えずに開発できることが望ましい
- **ノードの入出力は一様ではない**。テキストを受け取りテキストを返すノードもあれば、PDFファイルを受け取るノードやLLMの構造化レスポンスを返すノードもあり、今後さらに多様化する可能性がある
- **MVP（初期リリース）を早期に届けたい**一方で、将来的にワークフローの同時実行数やノードの種類が増えたとき、大幅なリアーキテクチャなしで対応できることも期待されている

#### 利用シナリオ例

以下のシナリオを念頭に設計してください。

1. **大量ドキュメント処理**: ユーザーが複数のPDFをアップロードし、テキスト抽出 → AI要約 → フォーマット整形の順で処理するワークフローを作成・実行する。処理には時間がかかるため、ユーザーはワークフローを実行したあとブラウザを閉じ、後から結果を確認しに戻ることもある
2. **実行状態の確認**: 複数ユーザーが同時にワークフローを実行する。あるユーザーが自分のワークフローの進捗を確認する際、他のユーザーの実行に影響を与えてはならない。実行中・完了・失敗といった状態がいつでも参照できる必要があるが、リアルタイム性をどこまで追求するか（即座の通知か、画面リロードによる確認か）も設計上の判断ポイントとなる
3. **ノードタイプの追加**: 運用チームのメンバーが新しいノードタイプ（例: 翻訳ノード、外部API連携ノード）を追加する。追加時に既存ノードの実装を変更する必要がなく、かつワークフローエンジンが新ノードを自然に扱えることが望ましい。ただし、ノードによって必要な設定項目（プロンプト、変換ルール、APIキーなど）は大きく異なる

---

### 機能要件

#### データ永続化

- 外部データストア（PostgreSQL、MongoDB、SQLiteファイルモード等）を用いてデータを永続化すること
- スキーマの変更管理（マイグレーション）が可能な仕組みを導入すること

#### 非同期ワークフロー実行

- ワークフローの実行を非同期処理にすること。
- 実行状態をクライアントから参照可能にすること
- 実行失敗時のエラーハンドリングを考慮すること

#### NodeType.GENERATIVE_AI の実装

- LLMのAPIを利用できるように拡張すること
- プロンプトとモデルはユーザーが設定できるようにすること
- その他のパラメータを追加しても問題ありません

#### NodeType.FORMATTER の実装

- 与えられたテキストを整形できるように拡張すること
- **少なくとも2種類以上のフォーマット変換**を実装すること（例: 大文字→小文字、小文字→大文字、半角→全角 等）
- フォーマットルールはユーザーが設定できるようにすること

#### PDF + NodeType.EXTRACT_TEXT の実装

- PDFファイルのアップロードを受け付けられるようにすること
- NodeType.EXTRACT_TEXT でテキストの抽出ができるようにすること

#### (Optional) DAG構造

- 有向非巡回グラフ（DAG）構造にして、複数の入力、複数の出力ができるようにしてください

#### (Optional) AIエージェントノード

- Workflowの実行にAIエージェントのノードを足してください
- AIエージェントの定義はご自身で決めてください
- 一般的には以下のような機能を持つと言われています
  - 達成条件を与えたらタスクのプランニングを行う
  - 必要なツールを判断できる
  - 終了条件を自動で判断できる

---

### 設計ドキュメント（ADR）の提出

主要な設計判断について、ADR（Architecture Decision Record）を作成してください。テンプレートは `[adr-template.md](./adr_template.md)` を参照してください。

#### 必須（最低限記録すべき設計判断）

1. **データストアの選択**: DB種別、ORM/マイグレーションツールの選定理由
   - *考慮観点: ワークフロー/ノードの関係構造、ノード設定の柔軟性、ファイルストレージ*

2. **非同期処理アーキテクチャ**: ワーカー/キュー方式、ジョブ状態管理の設計
   - *考慮観点: MVP段階での実現性と将来のスケーラビリティ、処理特性のばらつきへの対応*

3. **アプリケーション構成**: レイヤ分割方針、ディレクトリ構成
   - *考慮観点: チーム規模とノード追加者の独立性のバランス、テスタビリティ*

4. **ノード処理の拡張方式**: 新ノードタイプ追加時の設計パターン
   - *考慮観点: 多様な入出力への対応、型安全性と拡張容易性のバランス*

5. **API設計方針**: パス設計、スキーマ設計、一貫性の方針
   - *考慮観点: 非同期処理のAPI表現、リアルタイム性と技術コストのバランス*

---

## アプリケーション

### 現在のディレクトリ構成

```
.
├── server
│   ├── main.py            # FastAPIのエントリポイント
│   ├── models.py          # Pydanticモデル等
│   ├── schemas.py         # Request/Response用スキーマ
│   └── requirements.txt   # Python依存パッケージ
└── client
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts     # Vite等でReactを動かす例
    └── src
        ├── App.tsx        # ルートコンポーネント
        ├── api.ts         # フロントからバックへの通信ラッパ
        └── types.ts       # TypeScriptの型定義
```

### 現在のコード

#### server/requirements.txt

```txt
fastapi==0.95.0
uvicorn==0.22.0
pydantic==1.10.5
```

#### server/models.py

```python
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel

class NodeType(str, Enum):
    EXTRACT_TEXT = "extract_text"
    GENERATIVE_AI = "generative_ai"
    FORMATTER = "formatter"

class Workflow(BaseModel):
    id: str
    name: str
    nodes: List["Node"]

class Node(BaseModel):
    id: str
    node_type: NodeType
    config: dict  # ノード固有のパラメータ
    # 例: {"prompt": "要約してください", "model": "mock_llm_v1"} など

# 循環参照を回避するため
Workflow.update_forward_refs()
```

#### server/schemas.py

```python
from pydantic import BaseModel
from typing import List

from .models import NodeType

class CreateWorkflowRequest(BaseModel):
    name: str

class CreateWorkflowResponse(BaseModel):
    id: str
    name: str

class AddNodeRequest(BaseModel):
    node_type: NodeType
    config: dict

class WorkflowDetailResponse(BaseModel):
    id: str
    name: str
    nodes: List[dict]
```

#### server/main.py

```python
from fastapi import FastAPI, HTTPException
from uuid import uuid4

from .models import Workflow, Node, NodeType
from .schemas import (
    CreateWorkflowRequest, CreateWorkflowResponse,
    AddNodeRequest, WorkflowDetailResponse
)

app = FastAPI(title="Workflow App")

# 簡易的にメモリ内で管理
workflows = {}

@app.post("/workflows", response_model=CreateWorkflowResponse)
def create_workflow(req: CreateWorkflowRequest):
    wf_id = str(uuid4())
    new_wf = Workflow(id=wf_id, name=req.name, nodes=[])
    workflows[wf_id] = new_wf
    return CreateWorkflowResponse(id=wf_id, name=req.name)

@app.get("/workflows/{wf_id}", response_model=WorkflowDetailResponse)
def get_workflow(wf_id: str):
    wf = workflows.get(wf_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return WorkflowDetailResponse(
        id=wf.id,
        name=wf.name,
        nodes=[node.dict() for node in wf.nodes]
    )

@app.post("/workflows/{wf_id}/nodes")
def add_node(wf_id: str, req: AddNodeRequest):
    wf = workflows.get(wf_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    node_id = str(uuid4())
    new_node = Node(id=node_id, node_type=req.node_type, config=req.config)
    wf.nodes.append(new_node)
    return {"message": "Node added", "node_id": node_id}

@app.post("/workflows/{wf_id}/run")
def run_workflow(wf_id: str):
    wf = workflows.get(wf_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # シンプルに、ノードを順に処理してみる（疑似実装）
    data = {"text": "Initial text from some doc ..."}  # 本来はアップロードファイルの解析結果など
    for node in wf.nodes:
        if node.node_type == NodeType.EXTRACT_TEXT:
            # ダミー: テキスト抽出
            data["text"] = "[EXTRACTED] " + data["text"]
        elif node.node_type == NodeType.GENERATIVE_AI:
            # ダミー: 生成AIに投げた結果をモックで返す
            prompt = node.config.get("prompt", "")
            data["text"] = f"[GEN_AI with prompt='{prompt}']: " + data["text"]
        elif node.node_type == NodeType.FORMATTER:
            # ダミー: 文字列を整形
            data["text"] = data["text"].upper()
        else:
            pass  # 未知のノードタイプはスキップ
    return {"final_output": data["text"]}
```

#### client/package.json

```json
{
  "name": "workflow-client",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  },
  "devDependencies": {
    "typescript": "^4.5.5",
    "vite": "^4.0.0",
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0"
  }
}
```

#### client/tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "jsx": "react-jsx",
    "strict": true
  },
  "include": ["src"]
}
```

#### client/vite.config.ts

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000
  }
})
```

#### client/src/types.ts

```typescript
export interface Workflow {
  id: string;
  name: string;
  nodes: Node[];
}

export interface Node {
  id: string;
  node_type: NodeType;
  config: Record<string, unknown>;
}

export type NodeType = "extract_text" | "generative_ai" | "formatter";

export interface CreateWorkflowRequest {
  name: string;
}

export interface CreateWorkflowResponse {
  id: string;
  name: string;
}
```

#### client/src/api.ts

```typescript
import axios from 'axios';
import { CreateWorkflowRequest, CreateWorkflowResponse, Workflow, NodeType } from './types';

const API_BASE = "http://localhost:8000";

export async function createWorkflow(req: CreateWorkflowRequest): Promise<CreateWorkflowResponse> {
  const res = await axios.post(`${API_BASE}/workflows`, req);
  return res.data;
}

export async function getWorkflow(wfId: string): Promise<Workflow> {
  const res = await axios.get(`${API_BASE}/workflows/${wfId}`);
  return res.data;
}

export async function addNode(wfId: string, nodeType: NodeType, config: Record<string, any>) {
  const res = await axios.post(`${API_BASE}/workflows/${wfId}/nodes`, { node_type: nodeType, config });
  return res.data;
}

export async function runWorkflow(wfId: string) {
  const res = await axios.post(`${API_BASE}/workflows/${wfId}/run`);
  return res.data;
}
```

#### client/src/App.tsx

```tsx
import React, { useState, useEffect } from 'react';
import { createWorkflow, getWorkflow, addNode, runWorkflow } from './api';
import { Workflow } from './types';

function App() {
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [workflowName, setWorkflowName] = useState("");

  async function handleCreateWorkflow() {
    if(!workflowName) return;
    const result = await createWorkflow({ name: workflowName });
    setWorkflowId(result.id);
    setWorkflow(null);
  }

  async function handleFetchWorkflow() {
    if(!workflowId) return;
    const wf = await getWorkflow(workflowId);
    setWorkflow(wf);
  }

  async function handleAddNode(nodeType: string) {
    if(!workflowId) return;
    await addNode(workflowId, nodeType as any, { prompt: "Summarize this doc" });
    handleFetchWorkflow();
  }

  async function handleRunWorkflow() {
    if(!workflowId) return;
    const result = await runWorkflow(workflowId);
    alert("Final output: " + result.final_output);
  }

  return (
    <div style={{ margin: '20px' }}>
      <h1>Workflow Editor (Sample)</h1>
      <div>
        <input
          type="text"
          placeholder="Workflow name"
          value={workflowName}
          onChange={e => setWorkflowName(e.target.value)}
        />
        <button onClick={handleCreateWorkflow}>Create Workflow</button>
      </div>

      {workflowId && (
        <>
          <p>Current Workflow ID: {workflowId}</p>
          <button onClick={handleFetchWorkflow}>Fetch Workflow</button>
        </>
      )}

      {workflow && (
        <div style={{ marginTop: '10px' }}>
          <h2>{workflow.name} (ID: {workflow.id})</h2>
          <ul>
            {workflow.nodes.map(n => (
              <li key={n.id}>
                {n.node_type} | {JSON.stringify(n.config)}
              </li>
            ))}
          </ul>
          <div>
            <button onClick={() => handleAddNode("extract_text")}>Add Extract Node</button>
            <button onClick={() => handleAddNode("generative_ai")}>Add AI Node</button>
            <button onClick={() => handleAddNode("formatter")}>Add Formatter Node</button>
          </div>
          <button onClick={handleRunWorkflow} style={{ marginTop: '10px' }}>Run Workflow</button>
        </div>
      )}
    </div>
  );
}

export default App;
```

---

## 課題2

**このリポジトリでコーディングエージェントが安全かつ効率的に開発できるよう、設定・ルールファイルを整備してください。**

### 必須提出物

- `docs/agent-setup.md`
以下の内容を記入してください。
- `入れたルール・設定とその意図`

### 追加提出物（例）

- CLAUDE.md（または .cursorrules 等、使用ツールに合わせて）
- docs/rules/*.md（ルールを分割する場合）

---

## ADRテンプレート

```markdown
## 背景・解決したい課題

<!-- この意思決定が必要になった背景と、解決したい課題を記載 -->

## 決定事項

<!-- 何をどうするか、採用する方針を記載 -->

## 選択肢

### Option1: xxx

👍**Pros**

-

👎**Cons**

-

### Option2: xxx

👍**Pros**

-

👎**Cons**

-

## 懸念事項・影響範囲

<!-- 決定に伴うリスク、影響を受けるコンポーネント、移行の必要性などを記載 -->
```

---

## 提出物

### 課題1に関するもの

- ソースコード（GitHub経由、ZIPファイル等）
- README（セットアップ・起動方法、エンドポイント仕様、その他注意事項）
- ADR（設計判断の記録。adr-template.md に沿って記述）
- テストとテスト実行方法

### 課題2に関するもの

- docs/agent-setup.md ほか