# Asynchronous Implementation Notes

## Goal

Implement asynchronous workflow execution for the MVP using `FastAPI BackgroundTasks`.

Do not introduce:

- Redis
- Celery
- worker processes
- polling

Keep the implementation lightweight.

## Current Behavior To Change

Current code has these issues:

- execution is created as `PENDING`
- background task changes it to `RUNNING` later
- execution row may not be committed before the response returns
- frontend polls execution list/detail
- frontend redirects to `/executions` after start, but does not use the returned execution object

## Target Behavior

Required flow:

1. user uploads PDF and starts execution
2. backend creates execution row with `RUNNING`
3. backend commits that row before returning the response
4. backend returns the created execution object immediately
5. backend continues processing in `BackgroundTasks`
6. background processing updates the same row to `COMPLETED` or `FAILED`
7. frontend shows the new execution immediately
8. later status changes are visible only after reload or revisit

Status values must be only:

- `RUNNING`
- `COMPLETED`
- `FAILED`

## Required Backend Changes

### 1. Remove `PENDING`

Update:

- `server/domain/enums/execution_status.py`
- `server/domain/entities/execution.py`
- DB check constraint / migration for execution status

Execution creation must start directly as `RUNNING`.

### 2. Create Execution As `RUNNING`

Update `server/domain/entities/execution.py`:

- `Execution.create(...)` must initialize `status=RUNNING`
- `start_execution()` is no longer needed in the normal MVP flow
- if kept, it must not be required during background execution startup

### 3. Commit Before Returning From `POST /executions`

Current problem:

- repository `create()` only does `flush()`
- session commit happens after the request dependency finishes
- a redirect followed by a new request may not see the row immediately

Update `server/api/routers/executions.py` so that the execution row is committed before returning the response.

Minimal acceptable approach:

- inject the DB session into the route
- call `await session.commit()` after `service.start_execution(...)`
- then register the background task
- then return the execution response

### 4. Keep `BackgroundTasks`, But Only For Dispatch

Keep:

- `background_tasks.add_task(...)`

Do not keep the heavy execution logic conceptually inside the HTTP endpoint forever.

At minimum, the actual workflow-running logic should be callable independently from the route.

Acceptable forms:

- a helper function
- a service method
- a dedicated execution runner module

The route should only:

- save file
- create execution row
- commit
- dispatch background work
- return response

### 5. Remove Redundant `RUNNING` Transition

If execution is created directly as `RUNNING`, then:

- `process_workflow_execution(...)` must not transition from `PENDING` to `RUNNING`

It should only:

- load execution/workflow
- process nodes
- set `COMPLETED` with `output_data`
- or set `FAILED` with `error_message`

## Required Frontend Changes

### 1. Remove Polling

Update:

- `client/src/components/ExecutionList.tsx`
- `client/src/components/ExecutionDetail.tsx`

Remove all `setInterval(...)` based polling.

Pages should load data:

- on mount
- on revisit
- on manual reload only

### 2. Use Returned Execution Immediately

Update `client/src/components/CreateExecution.tsx`:

- keep the returned execution from `startExecution(...)`
- redirect to `/executions`
- pass the returned execution through router state

### 3. Show New Execution Immediately In Execution List

Update `client/src/components/ExecutionList.tsx`:

- read the execution from router state
- insert it into the displayed list immediately
- avoid duplicates if the same execution already exists in fetched results

The newly started execution should be shown as `RUNNING` immediately after redirect.

### 4. No Automatic Status Refresh

Do not add polling replacement logic.

MVP behavior should be:

- execution appears immediately after start
- later status changes are visible after page reload

## Recommended File Targets

- `server/domain/enums/execution_status.py`
- `server/domain/entities/execution.py`
- `server/api/routers/executions.py`
- `server/services/execution_service.py`
- `server/infra/db/repositories/sqlalchemy_execution_repository.py`
- `server/alembic/versions/*`
- `client/src/components/CreateExecution.tsx`
- `client/src/components/ExecutionList.tsx`
- `client/src/components/ExecutionDetail.tsx`

## Acceptance Criteria

- `POST /api/executions` returns a persisted execution row with `RUNNING`
- the new execution is visible immediately after redirect to `/executions`
- execution list does not poll
- execution detail does not poll
- background processing updates the row to `COMPLETED` or `FAILED`
- updated status is visible after reload
