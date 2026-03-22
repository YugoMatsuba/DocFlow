# Database Design Plan for LayerX Workflow System

## Executive Summary

This document outlines the database architecture and data storage strategy for the LayerX workflow processing system. The MVP system processes text input through configurable workflows with AI text generation and formatting capabilities.

## Current State Analysis

### Existing Implementation
- **Storage**: In-memory dictionary (`workflows = {}`)
- **Persistence**: None - data lost on server restart
- **Models**: Simple Pydantic models (Workflow, Node)
- **Limitations**: No concurrent access, no execution history, no file management

### Business Requirements (MVP Scope)
- Persistent workflow storage
- Async execution tracking with status monitoring
- Direct text input processing (no file upload)
- Execution history and audit trails
- Concurrent user access
- Simple processing with status management

## Data Requirements Analysis

### Core Entities (MVP Scope - 3 Tables)

#### 1. Workflows
**Purpose**: Define processing pipelines
**Data**:
- Metadata (id, name, timestamps)
- Relationship to nodes and executions
- Simple workflow configuration

#### 2. Nodes
**Purpose**: Individual processing steps
**Data**:
- Processing type (extract_text, generative_ai, formatter)
- Configuration parameters (flexible JSON structure)
- Execution order within workflow
- Node-specific settings

#### 3. WorkflowExecutions
**Purpose**: Track processing sessions with direct text input
**Data**:
- Execution status (pending, running, completed, failed)
- Input text (user-provided)
- Output text (processed result)
- Timing information (start, end)
- Error messages and debugging info

**MVP Simplification**: Removed file storage and individual node result tracking to focus on core workflow processing. Users input text directly rather than uploading files.

### Data Relationships (Simplified MVP)

```
Workflow (1) ────── (N) Node
    │
    └── (1) ────── (N) WorkflowExecution
```

**Simplified Architecture**: Direct relationships with consolidated execution data, removing the complexity of individual node results and file storage.

## Database Technology Selection

### SQL vs NoSQL Analysis

#### PostgreSQL (Recommended) ✅

**Strengths:**
- **ACID Compliance**: Critical for workflow execution state consistency
- **Complex Relationships**: Natural fit for workflow → nodes → executions hierarchy
- **JSON/JSONB Support**: Flexible storage for node configurations while maintaining structure
- **Full-Text Search**: Workflow metadata and content searching
- **Mature Ecosystem**: Excellent tooling (SQLAlchemy, Alembic, pgAdmin)
- **Performance**: Efficient indexing and query optimization
- **Concurrent Access**: Multi-user support with proper locking

**Use Cases:**
- Transactional workflow state management
- Complex queries for execution analytics
- Referential integrity between entities
- Audit trails and compliance reporting

#### MongoDB (Not Recommended) ❌

**Limitations for this use case:**
- **No ACID across collections**: Risk of inconsistent execution state
- **Weak relationships**: Difficult to maintain workflow integrity
- **Complex queries**: Limited aggregation for execution analytics
- **No foreign keys**: Manual referential integrity maintenance

#### Redis (Complementary)

**Recommended for:**
- Async job queue (Celery task management)
- Real-time execution status updates
- Session caching and temporary data
- Performance metrics collection

### Hybrid Architecture Decision

**Primary Database**: PostgreSQL
- All persistent application data
- Transactional workflow operations
- Long-term storage and analytics

**Cache/Queue Layer**: Redis
- Celery task queue
- Real-time status updates
- Session management
- Performance optimization

**Text Processing**: Direct Input
- Users provide text input directly through API
- No file storage complexity in MVP
- Processed results stored in workflow_executions table

## Detailed Data Model Design

### Table Specifications

#### workflows
```sql
CREATE TABLE workflows (
    id VARCHAR PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    user_id VARCHAR, -- Future user management
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);
```

#### nodes
```sql
CREATE TABLE nodes (
    id VARCHAR PRIMARY KEY,
    workflow_id VARCHAR REFERENCES workflows(id) ON DELETE CASCADE,
    node_type VARCHAR NOT NULL CHECK (node_type IN ('extract_text', 'generative_ai', 'formatter')),
    config JSONB NOT NULL DEFAULT '{}',
    order_index INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(workflow_id, order_index)
);
```

#### workflow_executions (MVP - Consolidated)
```sql
CREATE TABLE workflow_executions (
    id VARCHAR PRIMARY KEY,
    workflow_id VARCHAR REFERENCES workflows(id) ON DELETE CASCADE,
    input_text TEXT NOT NULL,
    output_text TEXT,
    status VARCHAR NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    execution_context JSONB DEFAULT '{}'
);
```

**MVP Simplification**: The complex execution_results and file_storage tables have been removed. All execution data is consolidated in the workflow_executions table for simplicity.

### Indexing Strategy

#### Performance Indexes (MVP)
```sql
-- Workflow lookups
CREATE INDEX idx_workflows_created ON workflows(created_at DESC);

-- Node ordering and lookups
CREATE INDEX idx_nodes_workflow_order ON nodes(workflow_id, order_index);

-- Execution tracking
CREATE INDEX idx_executions_workflow_status ON workflow_executions(workflow_id, status);
CREATE INDEX idx_executions_status_started ON workflow_executions(status, started_at DESC);
```

#### Full-Text Search (MVP)
```sql
-- Workflow content search
CREATE INDEX idx_workflows_search ON workflows USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));

-- Execution input/output text search
CREATE INDEX idx_executions_text_search ON workflow_executions USING gin(to_tsvector('english', COALESCE(input_text, '') || ' ' || COALESCE(output_text, '')));
```

## Repository Pattern Architecture

### Design Principles
- **Separation of Concerns**: Data access logic isolated from business logic
- **Dependency Injection**: Repositories injected into services
- **Interface Contracts**: Abstract base classes define operations
- **Transaction Management**: Consistent database transaction handling
- **Error Handling**: Standardized exception handling and logging

### Repository Structure

#### Base Repository
```python
# repositories/base.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T')

class BaseRepository(Generic[T], ABC):
    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model

    async def create(self, **kwargs) -> T: ...
    async def get_by_id(self, id: str) -> Optional[T]: ...
    async def update(self, id: str, **kwargs) -> Optional[T]: ...
    async def delete(self, id: str) -> bool: ...
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[T]: ...
```

#### Specialized Repositories (MVP)

**WorkflowRepository**
- Workflow CRUD operations
- Node management within workflows
- Workflow validation and business rules
- Workflow templates and configuration

**ExecutionRepository**
- Execution lifecycle management with consolidated data
- Status tracking and updates
- Text input/output processing
- Execution history and analytics
- Error handling and recovery

## Service Integration Architecture

### Service Layer Design
```
Controllers (FastAPI)
    ↓
Services (Business Logic)
    ↓
Repositories (Data Access)
    ↓
Database (PostgreSQL)
```

### Key Services (MVP)

#### WorkflowService
- Workflow orchestration and validation
- Node configuration management
- Workflow template operations
- Business rule enforcement

#### ExecutionService
- Text processing coordination
- Execution state management
- Progress tracking and notifications
- Error handling and recovery
- Direct text input/output handling

## Migration Strategy

### Phase 1: Foundation (Week 1)
- PostgreSQL setup with Docker Compose
- Basic SQLAlchemy models
- Database connection and session management
- Initial migration scripts

### Phase 2: Core Implementation (Week 2)
- Repository pattern implementation
- Basic CRUD operations
- Service layer integration
- API endpoint updates

### Phase 3: MVP Features (Week 3)
- Text input processing
- Async execution tracking
- Error handling and recovery
- Basic performance optimization

### Phase 4: Production Readiness (Week 4)
- Comprehensive indexing
- Backup and recovery procedures
- Monitoring and alerting
- Load testing and optimization

## Operational Considerations

### Backup Strategy (MVP)
- **Daily backups** of PostgreSQL with point-in-time recovery
- **Automated backup verification** and restoration testing
- **Simple backup procedures** focused on database only

### Monitoring and Observability (MVP)
- **Database performance metrics** (query time, connection pool usage)
- **Execution monitoring** (success rates, processing times)
- **Text processing metrics** (throughput, error rates)
- **Application logs** with structured logging and error tracking

### Scalability Planning
- **Read replicas** for analytical queries and reporting
- **Connection pooling** for efficient database resource usage
- **Horizontal scaling** preparation with proper indexing
- **Caching strategy** with Redis for frequently accessed data

### Security Considerations
- **Database encryption** at rest and in transit
- **Access control** with role-based permissions
- **File upload security** with virus scanning and type validation
- **Audit logging** for compliance and security monitoring

## Success Metrics

### Performance Targets (MVP)
- **Database query response time**: < 100ms for 95% of queries
- **Workflow execution throughput**: > 50 concurrent executions
- **Text processing**: < 2 seconds for typical text inputs
- **System availability**: 99.5% uptime

### Data Integrity Measures (MVP)
- **Zero data loss** during normal operations
- **Consistent execution state** across all workflow steps
- **Input/output text validation** and sanitization
- **Referential integrity** maintained across workflow relationships

This simplified database design provides a solid foundation for the LayerX workflow MVP, focusing on core functionality while maintaining the ability to scale and add complexity in future iterations. The 3-table architecture balances simplicity with functionality, enabling rapid development and testing of the core workflow processing capabilities.