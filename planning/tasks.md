# Task 1 Implementation Plan

## 1. Database Persistence

### 1.1 Database Setup
- [ ] PostgreSQL setup (create docker-compose.yml)
- [ ] SQLAlchemy + Alembic integration
- [ ] Database connection configuration
- [ ] Environment variable management (.env)

### 1.2 Database Model Design
- [ ] Workflow table
  - id, name, created_at, updated_at
- [ ] Node table
  - id, workflow_id, node_type, config, order
- [ ] WorkflowExecution table
  - id, workflow_id, status, started_at, completed_at, error_message
- [ ] ExecutionResult table
  - id, execution_id, node_id, input_data, output_data, status

### 1.3 Migration
- [ ] Create initial migration files
- [ ] Migration execution commands

## 2. Async Workflow Execution

### 2.1 Job Queue Setup
- [ ] Redis setup (docker-compose.yml)
- [ ] Celery configuration
- [ ] Worker process setup

### 2.2 Execution State Management
- [ ] Execution status Enum (PENDING, RUNNING, COMPLETED, FAILED)
- [ ] Start execution API: `POST /workflows/{id}/execute`
- [ ] Check execution status API: `GET /executions/{id}`
- [ ] Execution history API: `GET /workflows/{id}/executions`

### 2.3 Job Execution Engine
- [ ] Celery task definition
- [ ] Workflow execution processing
- [ ] Progress update handling

## 3. PDF Input Support

### 3.1 File Upload
- [ ] PDF upload API: `POST /files/upload`
- [ ] File storage configuration (uploads/ folder)
- [ ] File information management (FileStorage table)

### 3.2 Workflow Input Configuration
- [ ] Input file specification when executing workflow
- [ ] File reference API: `GET /files/{id}`

## 4. Node Implementation

### 4.1 NodeType.EXTRACT_TEXT
- [ ] PDF reading (PyPDF2 or pdfplumber)
- [ ] Text extraction processing
- [ ] Output data format standardization

### 4.2 NodeType.GENERATIVE_AI
- [ ] OpenAI API setup
- [ ] Prompt configuration UI
- [ ] Model selection (gpt-3.5-turbo, gpt-4, etc.)
- [ ] API rate limit handling
- [ ] Error handling

### 4.3 NodeType.FORMATTER
- [ ] Format type definition
  - UPPERCASE (uppercase conversion)
  - LOWERCASE (lowercase conversion)
  - TRIM (whitespace removal)
  - REPLACE (string replacement)
- [ ] User-configurable formatting rules

## 5. Error Handling

### 5.1 Execution Failure Processing
- [ ] Node execution failure handling
- [ ] Error message storage
- [ ] Execution stop processing

### 5.2 API Integration
- [ ] Error state response
- [ ] Failure reason display

## 6. Extensible Architecture

### 6.1 Node Execution Foundation
- [ ] BaseNodeExecutor abstract class
- [ ] Node execution factory pattern
- [ ] Plugin-style node addition

### 6.2 Configuration Management
- [ ] Unified interface for node-specific settings
- [ ] Validation functionality

## Technology Stack Selection Rationale

### Database: PostgreSQL
- JSON field support (node config storage)
- ACID transactions
- High reliability

### ORM: SQLAlchemy 2.0
- Async support
- Migration (Alembic)
- Type safety

### Job Queue: Celery + Redis
- Distributed processing support
- Retry functionality
- Monitoring tools (Flower)

### File Processing
- PyPDF2: Lightweight, basic text extraction
- pdfplumber: Complex layout support

## Directory Structure (Planned)

```
server/
├── alembic/                 # Migration
├── app/
│   ├── __init__.py
│   ├── config.py           # Configuration
│   ├── database.py         # DB setup
│   ├── models/             # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── workflow.py
│   │   ├── execution.py
│   │   └── file_storage.py
│   ├── schemas/            # Pydantic schemas
│   ├── api/                # API endpoints
│   │   ├── __init__.py
│   │   ├── workflows.py
│   │   ├── executions.py
│   │   └── files.py
│   ├── core/               # Core logic
│   │   ├── __init__.py
│   │   ├── workflow_engine.py
│   │   └── node_executors/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── extract_text.py
│   │       ├── generative_ai.py
│   │       └── formatter.py
│   └── tasks/              # Celery tasks
│       ├── __init__.py
│       └── workflow_execution.py
├── uploads/                # File storage
├── docker-compose.yml      # PostgreSQL, Redis
├── alembic.ini            # Alembic configuration
└── requirements.txt
```

## Development Order

1. **Week 1**: Database setup + basic models
2. **Week 2**: Async execution foundation + API
3. **Week 3**: PDF processing + node implementation
4. **Week 4**: Error handling + extensible foundation

## MVP Feature Scope

Minimum viable functionality:
- [x] Workflow CRUD
- [x] 3 node type implementations
- [x] PDF → Text extraction → AI summary → Uppercase conversion
- [x] Async execution + status check
- [x] Error handling