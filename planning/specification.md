# Architecture Refactoring Specification

## Objective

Refactor the current backend architecture into a simpler MVP-oriented layered architecture while preserving existing functionality.

The refactor must:

- Keep the current user-visible functionality working
- Preserve the current API behavior as much as reasonably possible
- Keep the current workflow execution flow:
  - create workflow
  - add nodes
  - upload PDF
  - run workflow asynchronously
  - persist execution status and output
  - retrieve execution list/detail
- Simplify architectural boundaries and reduce unnecessary indirection
- Keep the codebase extensible for future node types and stronger async infrastructure

This refactor is not a rewrite. It is a structural simplification with behavior preservation.

## Target Architecture

The target backend directory structure must be:

```text
server/
├── main.py                              # FastAPI application entrypoint. Wires app startup, router registration, and top-level app configuration.
├── config/
│   └── settings.py                      # Centralized environment/config loader for DB, OpenAI, upload directory, and app-level settings.
├── api/
│   ├── routers/
│   │   ├── workflows.py                 # HTTP endpoints for workflow CRUD-like operations, node addition, and workflow validation.
│   │   └── executions.py                # HTTP endpoints for execution start, PDF upload, execution list, and execution detail retrieval.
│   ├── schemas/
│   │   ├── workflow.py                  # Request/response schemas used by workflow routes. Defines API-facing payload shapes only.
│   │   └── execution.py                 # Request/response schemas used by execution routes. Keeps transport models separate from domain entities.
│   └── dependencies.py                  # FastAPI dependency wiring. Binds domain repository interfaces to infra implementations.
├── domain/
│   ├── entities/
│   │   ├── workflow.py                  # Core Workflow entity. Owns workflow-level behavior such as structure handling and aggregate consistency.
│   │   ├── node.py                      # Core Node entity. Represents one workflow step and its configuration at the domain level.
│   │   └── execution.py                 # Core Execution entity. Tracks execution state transitions and execution-related domain data.
│   ├── enums/
│   │   ├── node_type.py                 # Canonical enum for supported workflow node types across the system.
│   │   └── execution_status.py          # Canonical enum for execution lifecycle states such as PENDING/RUNNING/COMPLETED/FAILED.
│   ├── repositories/
│   │   ├── workflow_repository.py       # Repository interface for workflow persistence. Consumed by services and implemented in infra.
│   │   └── execution_repository.py      # Repository interface for execution persistence. Consumed by services and implemented in infra.
│   └── rules/
│       └── workflow_rules.py            # Pure domain validation rules for workflow composition, node flow ordering, and I/O compatibility constraints.
├── services/
│   ├── workflow_service.py              # Application service for workflow use cases: create, list, get, add node, validate.
│   ├── execution_service.py             # Application service for execution orchestration: create execution, run workflow, update status, persist output.
│   └── processors/
│       ├── base.py                      # Base processor contract and shared processor behavior used by all node processors.
│       ├── extract_text.py              # Runtime logic for EXTRACT_TEXT nodes. Converts PDF input into extracted text.
│       ├── generative_ai.py             # Runtime logic for GENERATIVE_AI nodes. Builds prompts and delegates raw API calls to infra.ai.openai_client.
│       ├── formatter.py                 # Runtime logic for FORMATTER nodes. Applies configured text formatting/transformation rules.
│       └── registry.py                  # NodeType-to-processor mapping/resolution. Keeps processor lookup centralized and explicit.
├── infra/
│   ├── db/
│   │   ├── base.py                      # SQLAlchemy declarative base and shared DB model foundation.
│   │   ├── database.py                  # Database engine/session setup and DB connection helpers.
│   │   ├── models/
│   │   │   ├── workflow.py              # SQLAlchemy persistence models for workflows and nodes. Defines table-level DB representation.
│   │   │   └── execution.py             # SQLAlchemy persistence model for workflow executions and persisted execution results/status.
│   │   └── repositories/
│   │       ├── sqlalchemy_workflow_repository.py   # SQLAlchemy implementation of the workflow repository interface.
│   │       └── sqlalchemy_execution_repository.py  # SQLAlchemy implementation of the execution repository interface.
│   ├── ai/
│   │   └── openai_client.py             # Raw OpenAI transport/client implementation. Encapsulates HTTP request details away from processor logic.
│   └── storage/
│       └── file_storage.py              # File storage helper for saving uploaded PDFs, returning paths, and optionally cleaning up failed uploads.
├── alembic/
│   ├── env.py                           # Alembic environment configuration used to run database migrations.
│   └── versions/                        # Migration revision files that track schema evolution.
└── uploads/                             # Local PDF storage directory used by the MVP for uploaded source files.
```

### Directory Structure Notes

- `main.py` should stay extremely small. It is only for app composition.
- `api/` is the transport layer. It is not allowed to own business rules.
- `domain/` should stay intentionally lean. Entities and rules belong here, but not runtime integration logic.
- `domain/repositories/` should contain interfaces only, never SQLAlchemy code.
- `services/` is the application/use-case layer and the main orchestration layer.
- `services/processors/` exists because node behavior is runtime application logic, not HTTP logic and not raw infrastructure code.
- `infra/` is where persistence and external system integrations live.
- `uploads/` is an implementation detail of the MVP. The rest of the code should interact with it through `infra/storage/file_storage.py`, not by scattering file path logic across routers and services.

## Current vs Target Architecture

This refactor is intentionally not a greenfield redesign. It is a simplification of the current backend structure into a clearer layered architecture for the MVP.

### Current Backend Structure

The current backend structure is approximately:

```text
server/
├── main.py
├── config/
│   ├── settings.py
│   ├── database.py
│   └── logging.py
├── presentation/
│   ├── routers/
│   │   ├── workflows.py
│   │   └── executions.py
│   ├── schemas/
│   │   └── common.py
│   └── middleware/
├── application/
│   ├── dtos/
│   │   ├── workflow_dtos.py
│   │   └── execution_dtos.py
│   ├── services/
│   │   ├── workflow_service.py
│   │   └── execution_service.py
│   ├── processors/
│   │   ├── base_processor.py
│   │   ├── extract_text_processor.py
│   │   ├── generative_ai_processor.py
│   │   ├── formatter_processor.py
│   │   └── processor_factory.py
│   └── tasks/
├── domain/
│   ├── entities/
│   │   ├── workflow.py
│   │   ├── node.py
│   │   ├── execution.py
│   │   └── execution 2.py
│   ├── enums/
│   │   ├── node_type.py
│   │   └── execution_status.py
│   ├── repositories/
│   │   ├── base_repository.py
│   │   ├── workflow_repository.py
│   │   └── execution_repository.py
│   └── processors/
├── infrastructure/
│   ├── dependencies.py
│   ├── di/
│   │   └── repository_factory.py
│   ├── db/
│   │   ├── base.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── workflow_model.py
│   │   │   └── execution_model.py
│   │   └── repositories/
│   │       ├── workflow_repository_impl.py
│   │       └── execution_repository_impl.py
│   └── external/
├── alembic/
│   ├── env.py
│   └── versions/
└── uploads/
```

### Current Architecture Summary

Current high-level dependency shape:

```text
main.py
  -> presentation
  -> application
  -> domain
  -> infrastructure
  -> config
```

Current issues to address:

- transport concerns live under `presentation/`, but API-facing schemas are split between `presentation/schemas` and `application/dtos`
- DB runtime setup is split across `config/database.py` and `infrastructure/db/database.py`
- dependency wiring is spread across `infrastructure/dependencies.py` and `infrastructure/di/repository_factory.py`
- runtime node logic exists under `application/processors/`, while there is also a `domain/processors/` package that adds confusion
- validation and workflow constraints are not clearly centralized
- there are signs of duplicate or stray files such as `domain/entities/execution 2.py`
- some directories exist mainly as indirection rather than because they represent a clear responsibility

### Target Architecture Summary

Target high-level dependency shape:

```text
main.py
  -> api
  -> services
  -> domain
  -> infra
  -> config
```

Target intent:

- `api` = HTTP transport only
- `services` = use-case orchestration and runtime node execution
- `domain` = business concepts, invariants, and repository interfaces
- `infra` = database, file storage, and external API implementations

### Key Structural Differences

#### 1. `presentation/` becomes `api/`

Reason:

- `api` is a clearer and more direct name for the HTTP layer in this MVP
- it makes the transport layer easier to identify quickly

Impact:

- routers move from `presentation/routers/` to `api/routers/`
- API-facing schemas move into `api/schemas/`

#### 2. `application/dtos/` is removed

Reason:

- API DTOs and transport schemas are serving nearly the same purpose
- keeping both creates duplication and more files than needed for the MVP

Impact:

- request/response models should live in `api/schemas/`
- domain entities should not be used directly as HTTP schemas unless explicitly intentional

#### 3. `application/services/` becomes `services/`

Reason:

- the shorter name improves readability
- it keeps the application/use-case layer explicit without unnecessary nesting

Impact:

- use-case orchestration files remain, but the path is simpler

#### 4. `application/processors/` moves into `services/processors/`

Reason:

- processors represent runtime node behavior used during workflow execution
- this is application logic, not pure domain modeling and not infrastructure

Impact:

- execution service becomes the clear orchestrator of processor invocation
- processor lookup and execution concerns stay close to workflow runtime logic

#### 5. `domain/rules/` is introduced

Reason:

- workflow constraints and node I/O validation should have a single explicit home
- currently these rules are at risk of being scattered across entities, routers, and services

Impact:

- ordering rules
- input/output compatibility rules
- workflow validation rules

should be centralized in `domain/rules/workflow_rules.py`

#### 6. `domain/repositories/` remains as interfaces

Reason:

- this keeps the architecture layered and supports dependency inversion
- services depend on repository contracts, not SQLAlchemy-specific implementations

Impact:

- repository interfaces remain in the domain
- concrete SQLAlchemy implementations live in `infra/db/repositories/`

#### 7. `infrastructure/` becomes `infra/`

Reason:

- shorter, cleaner, easier to scan
- keeps the MVP structure compact without changing the architectural intent

Impact:

- persistence, storage, and external clients all move under `infra/`

#### 8. Dependency wiring moves closer to the API layer

Reason:

- FastAPI dependency binding is primarily an application composition concern
- the current split between `infrastructure/dependencies.py` and `infrastructure/di/repository_factory.py` adds extra indirection

Impact:

- create `api/dependencies.py`
- bind repository interfaces to concrete implementations there
- remove unnecessary DI layering unless it has a concrete benefit

#### 9. Database setup is consolidated

Reason:

- DB connection/runtime setup should not be split across multiple locations without a strong reason

Impact:

- `config/settings.py` should only provide configuration values
- `infra/db/database.py` should own engine/session setup
- `infra/db/base.py` should own shared SQLAlchemy base concerns

#### 10. Raw OpenAI integration is separated from processor logic

Reason:

- processor logic should focus on node behavior and prompt construction
- raw HTTP/API transport logic should be isolated

Impact:

- create `infra/ai/openai_client.py`
- `services/processors/generative_ai.py` should depend on that client

#### 11. File storage logic is centralized

Reason:

- routers should not own upload path construction, save/delete behavior, or storage policies

Impact:

- create `infra/storage/file_storage.py`
- use it for saving uploaded PDFs and cleanup operations

#### 12. Redundant or low-value directories should be removed

Examples:

- `domain/processors/` if unused
- `application/tasks/` if unused
- `infrastructure/external/` if empty or functionally replaced by `infra/ai/`
- `presentation/middleware/` if it does not contain meaningful middleware

#### 13. Concrete repository names should be implementation-explicit

Reason:

- names like `workflow_repository_impl.py` are generic but vague
- the concrete implementation technology should be obvious from the file name

Impact:

- use names such as:
  - `sqlalchemy_workflow_repository.py`
  - `sqlalchemy_execution_repository.py`

### What Improves In the Target Structure

- fewer overlapping layers
- clearer boundaries between transport, orchestration, domain, and infrastructure
- less dependency scattering
- easier to explain and maintain
- easier to extend node types without touching unrelated layers
- easier to defend in ADRs as a pragmatic MVP architecture

### What Must Stay Functionally Equivalent

The refactor must not lose the following behaviors:

- workflow creation
- workflow retrieval/listing
- node addition and workflow validation
- PDF upload
- asynchronous execution start
- execution persistence
- execution status retrieval
- execution output persistence
- OpenAI integration
- formatter processing
- Alembic migration support

### Refactoring Interpretation

The target structure is not meant to make the codebase “more abstract.” It is meant to make it:

- simpler
- more legible
- less duplicated
- still layered
- still DDD-inspired
- more scalable than an ad hoc MVP, without becoming over-engineered

## Architectural Intent

This architecture must remain layered and DDD-inspired, but much simpler than the current version.

### Layer Responsibilities

#### `api/`

Purpose:

- Define HTTP routes
- Define request/response schemas
- Translate HTTP requests into service calls
- Translate application errors into HTTP errors

Rules:

- Do not place business logic here
- Do not place database access logic here
- Do not place OpenAI logic here
- File upload endpoints may receive files here, but file handling should be delegated to infrastructure or services

#### `domain/`

Purpose:

- Define core business concepts
- Keep entities and enums consistent
- Hold workflow/node validation rules that are pure domain rules
- Define persistence contracts through repository interfaces

Rules:

- Keep this layer simple
- Do not put HTTP concerns here
- Do not put ORM or SQLAlchemy models here
- Do not call OpenAI or file storage here
- Do not include FastAPI or persistence-specific DTOs here
- Repository interfaces are allowed here because they are contracts, not implementations

#### `services/`

Purpose:

- Hold application/use-case logic
- Orchestrate workflow creation and workflow execution
- Execute node processors in workflow order
- Manage status transitions for executions

Rules:

- This is where workflow runtime logic belongs
- Processors belong here because they contain runtime logic for each node type
- Services may depend on domain and infrastructure
- Services should not contain raw SQLAlchemy model definitions

#### `infra/`

Purpose:

- Implement persistence
- Implement file storage
- Implement external API clients

Rules:

- SQLAlchemy models and repository implementations live here
- OpenAI HTTP calls live here
- File save/read/delete helper logic lives here
- This layer can depend on config and domain

### Repository Interface Pattern

This refactor should explicitly use repository interfaces.

Design rule:

- `domain/repositories/*` defines abstract repository contracts
- `services/*` depends on those contracts
- `infra/db/repositories/*` provides SQLAlchemy-based implementations
- `api/dependencies.py` binds interface types to concrete instances

This keeps the architecture layered while avoiding unnecessary interfaces for everything else.

Only repositories must use this interface/implementation split in the MVP target architecture.

## Core Design Principles

### 1. Keep One Authoritative Shape Per Business Concept

The refactor must eliminate shape duplication and inconsistency.

There must be one authoritative definition for:

- `Workflow`
- `Node`
- `Execution`
- `NodeType`
- `ExecutionStatus`

Do not keep multiple competing entity definitions across different layers.

### 2. Keep Routers Thin

Routers should do only the following:

- parse input
- call a service
- return response
- map errors to HTTP status codes

Routers must not:

- construct workflow runtime logic
- directly orchestrate node execution
- embed OpenAI call logic
- embed PDF extraction logic

### 3. Keep Domain Simple

The domain should focus on:

- entities
- enums
- invariants
- node flow and validation rules

The domain should not become a “god layer.”

### 4. Keep Processors in `services/processors`

Processors represent the executable logic for each workflow node type.

They are used by the execution service to process a workflow step-by-step.

Examples:

- `extract_text.py`: PDF path -> extracted text
- `generative_ai.py`: text -> generated text
- `formatter.py`: text -> formatted text

### 5. Keep Infrastructure Replaceable

The architecture should support replacing:

- `BackgroundTasks` with Celery/Redis later
- local file storage with S3 later
- direct OpenAI API calls with another provider later

The MVP implementation can remain simple, but the structure should not block future replacement.

## Functional Requirements To Preserve

The refactor must preserve the following existing functionality.

### Workflows

- Create workflow
- List workflows
- Get workflow detail
- Add node to workflow
- Validate workflow

### Executions

- Upload a PDF and start an execution
- Save uploaded file to the server
- Create execution record in the database
- Execute workflow asynchronously in the background
- Move status through:
  - `PENDING`
  - `RUNNING`
  - `COMPLETED`
  - `FAILED`
- Persist output data
- Persist error message on failure
- List executions
- Get execution detail
- Allow users to confirm updated execution status or result by manually reloading the page and fetching the latest persisted data

### Node Types

- `EXTRACT_TEXT`
- `GENERATIVE_AI`
- `FORMATTER`

### Integrations

- PostgreSQL persistence
- Alembic migrations
- OpenAI API integration
- PDF extraction

## Detailed File Responsibilities

### `server/main.py`

Must:

- create FastAPI app
- register routers
- configure CORS if needed
- initialize startup hooks if needed

Must not:

- contain business logic
- contain repository logic
- contain execution orchestration logic

### `server/config/settings.py`

Must:

- centralize environment/config access
- include DB settings
- include OpenAI API key
- include upload directory settings

### `server/api/dependencies.py`

Must:

- create FastAPI dependency providers
- provide DB session access to repository implementations
- bind `domain.repositories.*` interfaces to `infra.db.repositories.*` implementations
- provide service instances to routers

Must not:

- contain business logic
- contain raw SQL queries
- duplicate repository behavior

### `server/api/routers/workflows.py`

Must handle:

- create workflow
- list workflows
- get workflow
- add node
- validate workflow
- optional delete if still kept

Must depend on:

- `services.workflow_service`

### `server/api/routers/executions.py`

Must handle:

- start execution with PDF upload
- list executions
- get execution detail

For MVP:

- execution status/result retrieval only needs to support manual reload or manual re-request
- polling-based client updates are not required

The route may accept `UploadFile`, but must not own workflow execution logic.

### `server/api/schemas/workflow.py`

Must contain:

- request and response models for workflow APIs
- node creation schema
- workflow detail/list schema

### `server/api/schemas/execution.py`

Must contain:

- execution response schema
- any upload/start execution request schema if needed

### `server/domain/entities/workflow.py`

Must define:

- workflow entity
- workflow behavior relevant to workflow structure

Examples:

- add node
- validate workflow composition

### `server/domain/entities/node.py`

Must define:

- node entity
- node configuration accessors if needed

Must not contain infrastructure concerns.

### `server/domain/entities/execution.py`

Must define:

- execution entity
- status transition helpers

Examples:

- start execution
- complete execution
- fail execution

### `server/domain/enums/node_type.py`

Must define the canonical node type enum values used consistently across the system.

### `server/domain/enums/execution_status.py`

Must define the canonical execution status enum values used consistently across the system.

### `server/domain/repositories/workflow_repository.py`

Must define the abstract contract for workflow persistence.

Examples:

- create workflow
- get workflow
- list workflows
- add node
- support workflow retrieval patterns needed by services

It must not contain SQLAlchemy implementation details.

### `server/domain/repositories/execution_repository.py`

Must define the abstract contract for execution persistence.

Examples:

- create execution
- get execution
- list executions
- update status
- persist output and error state

It must not contain SQLAlchemy implementation details.

### `server/domain/rules/workflow_rules.py`

Must define pure validation logic for workflow/node constraints.

Examples:

- valid workflow node ordering
- input/output compatibility rules between nodes
- required presence of `EXTRACT_TEXT` before text-consuming nodes when workflow input is PDF

### `server/services/workflow_service.py`

Must orchestrate workflow use cases:

- create workflow
- add node
- list/get workflow
- validate workflow

### `server/services/execution_service.py`

Must orchestrate execution use cases:

- create execution record
- start background execution
- update status
- retrieve execution detail/list
- run processors in correct order

This is the main application orchestration point for workflow runs.

### `server/services/processors/base.py`

Must define the processor contract.

Example responsibilities:

- processor interface/base class
- common validation/error helpers

### `server/services/processors/extract_text.py`

Must:

- take a PDF file path or equivalent runtime input
- extract text from the PDF
- return extracted text

### `server/services/processors/generative_ai.py`

Must:

- construct prompt from node configuration
- pass final prompt to `infra.ai.openai_client`
- return generated text

Important:

- The processor must correctly inject prior node output into the prompt
- Placeholder handling must be explicit and deterministic
- Avoid ambiguous placeholder conventions

### `server/services/processors/formatter.py`

Must:

- transform text according to node configuration
- support at least two formatting rules as required by the challenge

### `server/services/processors/registry.py`

Must:

- map `NodeType` to processor implementation
- provide a clean single place for processor resolution

### `server/infra/db/models/workflow.py`

Must contain SQLAlchemy models for:

- workflow table
- node table

### `server/infra/db/models/execution.py`

Must contain SQLAlchemy model for execution table.

### `server/infra/db/repositories/sqlalchemy_workflow_repository.py`

Must implement the `domain.repositories.workflow_repository` contract using SQLAlchemy.

Must implement persistence for:

- create/list/get workflow
- add node
- workflow validation support queries if needed

### `server/infra/db/repositories/sqlalchemy_execution_repository.py`

Must implement the `domain.repositories.execution_repository` contract using SQLAlchemy.

Must implement persistence for:

- create execution
- get execution
- list executions
- update status/output/error

### `server/infra/ai/openai_client.py`

Must:

- contain raw OpenAI HTTP/API client logic
- isolate API transport details from processor logic

Must not:

- know workflow orchestration
- know FastAPI request objects

### `server/infra/storage/file_storage.py`

Must:

- save uploaded PDFs
- return stable path references
- optionally provide delete helper for cleanup on failures

## Domain Constraints To Implement

This refactor must explicitly design and implement workflow/node constraints.

### Required Constraint Categories

#### 1. Node Order Constraints

The workflow must enforce valid node order according to the actual input/output flow.

Example:

- if the workflow starts from a PDF upload, the first processing step should be `EXTRACT_TEXT` before text-based processors consume the content

#### 2. Input/Output Compatibility Constraints

Each node type must have a defined expected input type and output type.

Minimum conceptual types:

- `pdf_file`
- `text`

Optional future types:

- `json`
- `structured_response`

Minimum compatibility rules:

- `EXTRACT_TEXT`: `pdf_file -> text`
- `GENERATIVE_AI`: `text -> text`
- `FORMATTER`: `text -> text`

Workflow validation must reject incompatible sequences.

#### 3. Node Configuration Constraints

Each node must validate its own configuration.

Examples:

- `GENERATIVE_AI` requires `prompt`
- `FORMATTER` requires `format_type`
- `FORMATTER` must support at least two valid format operations

#### 4. Execution Input Constraints

Execution start logic must validate that uploaded input is compatible with the workflow.

Example:

- if execution starts with a PDF upload, workflows that expect text directly without extraction should be rejected unless explicitly supported

## Async Execution Requirements

The current functionality of async execution must remain, but the implementation should be cleaner.

For MVP:

- using FastAPI `BackgroundTasks` is acceptable
- execution state must be persisted in DB
- client must be able to fetch execution status later
- users may reload the page or revisit the list/detail screen later to see updated status and output
- polling is not required
- WebSocket/SSE is not required

The code structure should make future migration to a queue-based worker model easier.

Therefore:

- background execution orchestration should be isolated in service logic
- router should only trigger execution start
- execution status transitions should be explicit and centralized
- execution list/detail endpoints must return the latest persisted execution state when the client reloads or manually re-requests the page

## OpenAI Integration Requirements

The refactor must preserve and improve OpenAI integration.

Required fixes:

- prompt building must reliably include previous node output
- prompt placeholder behavior must be clearly defined
- avoid “same answer every time” bugs caused by fixed prompt content or missing placeholder replacement

Recommended placeholder convention:

- `{{input}}`

If more placeholders are supported, document them clearly and implement them deterministically.

## Data Persistence Requirements

The refactor must preserve:

- PostgreSQL storage
- Alembic migration compatibility
- execution status persistence
- workflow/node persistence

The refactor must not revert to in-memory-only behavior.

## Migration / Refactoring Rules

### Refactor Rules

- Move files into the target structure
- Rename modules to match the target structure
- Update imports consistently
- Remove redundant abstractions that do not provide value for the MVP
- Keep behavior stable while restructuring

### Things To Remove or Collapse

The refactor should simplify these patterns where present:

- redundant DTO layers that only mirror API schemas
- DI/factory complexity that is unnecessary for FastAPI-based dependency injection
- duplicate entity definitions
- scattered validation logic

The refactor should keep these abstraction patterns:

- repository interfaces in `domain/repositories/`
- repository implementations in `infra/db/repositories/`
- dependency binding in `api/dependencies.py`

### Things That Must Not Be Lost

- asynchronous execution behavior
- execution persistence
- PDF upload and extraction
- OpenAI integration
- formatter behavior
- workflow and node creation behavior

## Acceptance Criteria

The refactor is complete only if all of the following are true.

### Architecture

- Code is reorganized into the target directory structure
- Each module matches its defined responsibility
- Duplicate entity shapes are removed
- The architecture is simpler to follow than the current structure

### Functional

- A workflow can be created
- Nodes can be added
- A PDF can be uploaded to start execution
- Execution status becomes `PENDING`, then `RUNNING`, then `COMPLETED` or `FAILED`
- Extracted text flows into the generative AI processor
- Generated output flows into the formatter if configured
- Final output is persisted
- Execution list and detail endpoints still work

### Validation

- Invalid node sequences are rejected
- Invalid node configurations are rejected
- Invalid execution/workflow combinations are rejected

### Operational

- App still starts successfully
- Migrations still work
- Existing API behavior remains usable by the current frontend with minimal or no changes
- Execution status and results remain viewable through normal page reload/manual revisit behavior

## Non-Goals

The refactor does not need to implement:

- full distributed job queue architecture
- WebSocket or SSE real-time updates
- client-side polling for execution status updates
- DAG execution
- AI agent node
- major frontend redesign

These can remain future work.

## Deliverable Expectation For Claude Code

Claude Code should:

1. Refactor the backend to the target structure
2. Preserve current behavior
3. Fix inconsistent models and imports
4. Keep the code runnable
5. Keep the architecture simpler, more concise, and still layered

The result should feel like a pragmatic MVP architecture, not a heavy enterprise architecture.
