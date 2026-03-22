# Asynchronous Execution Specification

## Objective

Define the asynchronous execution design for the MVP.

This specification must reflect the following decisions:

- the MVP must stay lightweight
- the implementation must avoid heavy infrastructure such as Redis and Celery for now
- workflow execution must still behave asynchronously from the user's perspective
- the code structure must remain easy to migrate later to a queue/worker model

This is an MVP-oriented asynchronous design, not a production-grade distributed job system.

## Decision Summary

For the MVP, asynchronous workflow execution must be implemented with:

- `FastAPI BackgroundTasks`
- database-persisted execution rows
- execution status stored in the database
- manual reload for status/result refresh

The MVP must not introduce:

- Redis
- Celery
- RabbitMQ
- client-side polling
- WebSocket or SSE

However, the implementation must be structured so that the dispatch mechanism can later be replaced by a queue/worker architecture with minimal changes to the core execution logic.

## Why This Is Still Asynchronous

This design is asynchronous because the heavy workflow processing does not happen before the API response.

The expected flow is:

1. create an execution row
2. persist and return that execution row immediately
3. continue workflow processing in the background
4. update the execution row later

This is different from synchronous behavior.

### Synchronous Shape

```text
request -> process everything -> return result
```

### Asynchronous Shape

```text
request -> create execution row -> return execution -> continue processing -> update execution row
```

The second flow is the behavior required here.

## MVP Constraints

The system is intended for:

- an MVP used by a small team first
- a personal-project level implementation scope
- a codebase that may later be expanded if the product proves useful

Because of that, the asynchronous design should prioritize:

- implementation simplicity
- clarity
- low operational overhead
- future migration potential

It should not prioritize:

- distributed job orchestration from day one
- sophisticated retry queues
- multi-service infrastructure

## Chosen MVP Architecture

### Current Asynchronous Mechanism

For the MVP, the API server will:

1. receive the execution request
2. save the uploaded PDF
3. create and persist an execution row in the database
4. return the execution row immediately
5. schedule background processing using `BackgroundTasks`

Then, after the HTTP response has been returned:

6. the background task will execute the workflow
7. the background task will update the execution row in the database

This means the background processing still runs inside the API application process, but only after the response has already been sent.

### Important Limitation

This is lighter than a queue/worker model, but it is not a fully separated asynchronous runtime.

It means:

- the API server and the background task still belong to the same app runtime
- if the API process dies, the in-flight task is vulnerable
- long-running and high-concurrency workloads are less robust than in a worker model

This tradeoff is acceptable for the MVP.

## Status Model

Execution status must have only these three values:

- `RUNNING`
- `COMPLETED`
- `FAILED`

`PENDING` must not be used in the active MVP execution lifecycle.

### Meaning

- `RUNNING`
  The execution was accepted, persisted, and background processing is underway or about to start immediately.
- `COMPLETED`
  The workflow completed successfully and `output_data` has been persisted.
- `FAILED`
  The workflow failed and `error_message` has been persisted.

## Core Product Behavior

### On Execution Start

When a user starts a workflow execution:

1. the frontend sends `POST /api/executions` with `workflow_id` and a PDF file
2. the backend saves the uploaded file
3. the backend creates an execution row with status `RUNNING`
4. the backend commits that row before returning the response
5. the backend returns the execution object to the frontend
6. the backend starts background execution logic after the response

The returned object is not a fake placeholder.

It must be:

- a real persisted execution row
- queryable from the database
- visible in execution list/detail endpoints

### After Execution Start

After the response is returned:

- the frontend can show the execution immediately
- the backend continues processing in the background
- when the user reloads later, the status can change to `COMPLETED` or `FAILED`

## Frontend Behavior

### No Polling

The frontend must not poll execution status.

That means:

- no repeated `GET /executions`
- no repeated `GET /executions/{id}`
- no interval-based refresh

### Reload-Based Refresh

The frontend should:

- show the returned execution immediately after start
- rely on page reload or manual revisit to observe status changes later

This is enough for the MVP and is explicitly acceptable given the project scope.

### Immediate User Experience

After starting execution:

- redirect to the execution list page
- insert the newly returned execution into the list immediately
- show its status as `RUNNING`

Later:

- on reload, the list fetches the persisted rows again
- if the execution finished, the status and output are updated from the database

## Backend Structural Requirements

### 1. Separate Execution Runner From Endpoint

The endpoint must not directly contain the full workflow execution logic.

Instead, the code must be split into:

- endpoint logic
- execution runner logic

The endpoint is responsible for:

- accepting the request
- validating the request
- saving the file
- creating the execution row
- dispatching execution
- returning the persisted execution

The execution runner is responsible for:

- loading the execution and workflow from the database
- running node processors in order
- updating final execution status and result

This separation is necessary because future queue/worker migration depends on it.

### 2. Execution Runner Must Be HTTP-Agnostic

The execution runner must be designed so that it can be called from:

- a FastAPI background task now
- a worker process later

That means it should not depend on:

- `Request`
- `Response`
- `BackgroundTasks`
- route-specific context

It should ideally look like:

```python
async def run_execution(execution_id: str) -> None:
    ...
```

or a service method with the same role.

### 3. Dispatch Must Be Replaceable

The API route should only decide how to dispatch execution, not how to execute it internally.

For the MVP:

```python
background_tasks.add_task(run_execution, execution.id)
```

For a future queue/worker system:

```python
queue.enqueue({"execution_id": execution.id})
```

The execution runner itself should remain the same.

## Database Behavior

### Execution Row Must Be Persisted Before Response

The execution row must be committed before the response is returned.

This is important because:

- the frontend may redirect immediately to the execution list
- the execution list must be able to read the newly created row
- a row that is only flushed but not committed may not be visible to a new request

This rule also applies conceptually to workflow creation and other create-and-redirect flows.

### Database Is the Source of Truth

The execution state must always be represented in the database.

The database row must be the authoritative record for:

- execution existence
- current status
- output
- error message
- timestamps

Neither the frontend nor the in-memory process state should be treated as the source of truth.

## Queue/Worker Migration Strategy

### Why We Are Not Implementing Queue/Worker Now

For this MVP, adopting Redis and Celery would be too heavy because it adds:

- Redis setup and operation
- worker process management
- queue infrastructure
- retry and failure semantics
- more development and debugging overhead

That cost is not justified for the current scope.

### Why We Still Design For It

The system may later be used by more teams and more users.

So even though we are not implementing queue/worker now, the code should make that migration straightforward.

### What Will Change Later

When migrating to a queue/worker model, the primary change should be in dispatch, not in core workflow execution.

The future flow will be:

1. API creates and persists execution row
2. API pushes job metadata into a queue
3. a worker process pulls the job
4. the worker executes the same execution runner
5. the worker updates the same execution row in the database

### What Gets Queued

The queue should not store executable code.

It should store lightweight job metadata such as:

- `execution_id`

Optionally:

- `workflow_id`
- retry metadata
- enqueue timestamp

The worker then loads everything else from the database and storage.

### What Stays The Same After Migration

These parts should ideally remain unchanged:

- execution table structure
- status transitions
- workflow loading logic
- node processors
- execution runner logic
- output/error persistence model

### What Changes After Migration

These parts should change:

- dispatch mechanism
- infrastructure setup
- worker process bootstrap
- queue configuration

This is exactly why the runner must be separated from the endpoint now.

## File-Level Design Guidance

The implementation should move toward the following separation of concerns:

- `api/routers/executions.py`
  Accept request, create execution, dispatch execution, return response

- `services/execution_service.py`
  Create execution rows, load executions, update status, and host or coordinate the execution runner

- `services/processors/*`
  Execute node-specific logic only

- `infra/storage/file_storage.py`
  Save and read uploaded PDF files

- `infra/db/repositories/sqlalchemy_execution_repository.py`
  Persist execution rows and updates

The execution runner should not live as heavy route-local logic forever.

## Required MVP State Transitions

### On Start

- create execution row with `RUNNING`
- commit it
- return it

### On Success

- set `COMPLETED`
- write `output_data`
- set `updated_at`
- set `completed_at`

### On Failure

- set `FAILED`
- write `error_message`
- set `updated_at`
- set `completed_at`

## Acceptance Criteria

The asynchronous MVP implementation is correct when:

- `POST /api/executions` returns immediately with a persisted execution row
- the returned execution row has status `RUNNING`
- the frontend can show the new execution immediately after redirect
- the backend continues processing after the response
- the background task updates the same execution row to `COMPLETED` or `FAILED`
- execution list/detail do not poll
- execution status changes become visible after reload
- the execution runner can later be called by something other than a FastAPI endpoint

## ADR Framing

The ADR for asynchronous processing should state:

- BackgroundTasks is chosen for MVP practicality and low infrastructure overhead
- execution state is persisted in the database from the start
- the execution runner is separated from the HTTP endpoint
- future migration to queue/worker is expected to replace only the dispatch mechanism and surrounding infrastructure

## Summary

For the MVP:

- implement asynchronous execution with `BackgroundTasks`
- persist execution rows immediately
- return real execution data immediately
- continue processing after the response
- refresh status by reload, not polling
- keep execution logic separate from the endpoint so a future queue/worker migration remains easy
