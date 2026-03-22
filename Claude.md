# LayerX Workflow System - Architecture Documentation

## Overview

This document defines the software architecture for the LayerX workflow processing system. The system is built using Clean Architecture principles with a focus on extensibility, testability, and maintainability for MVP delivery while supporting future scalability.

## Architecture Principles

### 1. **Layer Separation**
- **Presentation Layer**: HTTP endpoints, request/response handling
- **Application Layer**: Business logic orchestration, service coordination
- **Domain Layer**: Core business entities, rules, and interfaces
- **Infrastructure Layer**: External dependencies, database implementations

### 2. **Dependency Direction**
```
Presentation → Application → Domain ← Infrastructure
```
- Inner layers define interfaces, outer layers implement them
- Domain layer has no external dependencies
- Infrastructure layer implements domain interfaces

### 3. **Design Patterns**
- **Repository Pattern**: Data access abstraction
- **Strategy Pattern**: Pluggable node processors
- **Factory Pattern**: Node processor instantiation
- **Command Pattern**: Async workflow execution
- **Dependency Injection**: Loose coupling via FastAPI DI

## Directory Structure

```
server/
├── main.py
├── config/
│   └── settings.py
├── presentation/
│   ├── routers/
│   │   ├── workflows.py
│   │   ├── executions.py
│   │   └── files.py
│   ├── schemas/
│   │   ├── workflow.py
│   │   ├── execution.py
│   │   └── common.py
│   └── middleware/
│       └── error_handler.py
├── application/
│   ├── services/
│   │   ├── workflow_service.py
│   │   ├── execution_service.py
│   │   └── file_service.py
│   └── processors/
│       ├── base_processor.py
│       ├── text_extractor.py
│       ├── ai_processor.py
│       └── formatter.py
├── domain/
│   ├── entities/
│   │   ├── workflow.py
│   │   ├── node.py
│   │   └── execution.py
│   ├── repositories/
│   │   ├── workflow_repository.py
│   │   ├── execution_repository.py
│   └── enums/
│       ├── node_type.py
│       └── execution_status.py
└── infrastructure/
    ├── db/
    │   ├── session.py
    │   ├── models/
    │   │   ├── workflow_model.py
    │   │   ├── node_model.py
    │   │   ├── execution_model.py
    │   └── repositories/
    │       ├── workflow_repository_impl.py
    │       ├── execution_repository_impl.py
    ├── external/
    │   ├── openai_client.py
    │   └── pdf_processor.py
    └── tasks/
```

## Core Components

### 1. **Domain Entities**

#### Workflow Entity (Aggregate Root)
```python
class Workflow:
    id: str
    name: str
    nodes: List[Node]
    created_at: datetime
    updated_at: datetime

    def add_node(self, node: Node) -> None
    def remove_node(self, node_id: str) -> None
    def reorder_nodes(self, node_ids: List[str]) -> None
```

#### Node Entity
```python
class Node:
    id: str
    workflow_id: str
    node_type: NodeType
    config: Dict[str, Any]
    order_index: int

    def validate_config(self) -> None
```

#### Execution Entity
```python
class Execution:
    id: str
    workflow_id: str
    input_text: str
    output_text: Optional[str]
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
```

### 2. **Repository Interfaces**

#### Workflow Repository
```python
class WorkflowRepository(ABC):
    @abstractmethod
    async def create(self, workflow: Workflow) -> Workflow

    @abstractmethod
    async def get_by_id(self, workflow_id: str) -> Optional[Workflow]

    @abstractmethod
    async def update(self, workflow: Workflow) -> Workflow

    @abstractmethod
    async def delete(self, workflow_id: str) -> None

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Workflow]
```

### 3. **Node Processors (Strategy Pattern)**

#### Base Processor Interface
```python
class BaseNodeProcessor(ABC):
    @abstractmethod
    async def process(self, input_data: str, config: Dict[str, Any]) -> str

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> None

    @abstractmethod
    def get_required_config_keys(self) -> List[str]
```

#### Processor Factory
```python
class ProcessorFactory:
    _processors = {
        NodeType.EXTRACT_TEXT: TextExtractorProcessor,
        NodeType.GENERATIVE_AI: AIProcessor,
        NodeType.FORMATTER: FormatterProcessor,
    }

    @classmethod
    def create_processor(cls, node_type: NodeType) -> BaseNodeProcessor:
        return cls._processors[node_type]()
```

## Development Guidelines

### 1. **Adding New Node Types**

To add a new node type safely:

1. **Define the enum value**:
```python
# domain/enums/node_type.py
class NodeType(str, Enum):
    EXTRACT_TEXT = "extract_text"
    GENERATIVE_AI = "generative_ai"
    FORMATTER = "formatter"
    NEW_TYPE = "new_type"  # Add here
```

2. **Create processor implementation**:
```python
# domain/processors/new_type_processor.py
class NewTypeProcessor(BaseNodeProcessor):
    async def process(self, input_data: str, config: Dict[str, Any]) -> str:
        # Implementation here
        pass

    def validate_config(self, config: Dict[str, Any]) -> None:
        # Validation logic
        pass

    def get_required_config_keys(self) -> List[str]:
        return ["required_key1", "required_key2"]
```

3. **Register in factory**:
```python
# domain/processors/__init__.py
ProcessorFactory._processors[NodeType.NEW_TYPE] = NewTypeProcessor
```

4. **Add external dependencies if needed**:
```python
# infrastructure/external/new_service_client.py
class NewServiceClient:
    # External API integration
    pass
```

### 2. **Repository Pattern Usage**

#### In Services (Application Layer)
```python
class WorkflowService:
    def __init__(self, workflow_repo: WorkflowRepository):
        self.workflow_repo = workflow_repo

    async def create_workflow(self, name: str) -> Workflow:
        workflow = Workflow(id=str(uuid4()), name=name, nodes=[])
        return await self.workflow_repo.create(workflow)
```

#### Dependency Injection (FastAPI)
```python
# main.py
def get_workflow_repository() -> WorkflowRepository:
    return WorkflowRepositoryImpl(get_database_session())

def get_workflow_service(
    repo: WorkflowRepository = Depends(get_workflow_repository)
) -> WorkflowService:
    return WorkflowService(repo)
```

### 3. **Error Handling Conventions**

#### Domain Exceptions
```python
# domain/exceptions.py
class WorkflowNotFoundError(Exception):
    pass

class InvalidNodeConfigError(Exception):
    pass

class ExecutionFailedError(Exception):
    pass
```

#### Global Error Handler
```python
# presentation/middleware/error_handler.py
@app.exception_handler(WorkflowNotFoundError)
async def workflow_not_found_handler(request: Request, exc: WorkflowNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"detail": "Workflow not found"}
    )
```

### 4. **Testing Strategies**

#### Unit Tests (Domain Layer)
```python
# tests/domain/test_workflow.py
def test_workflow_add_node():
    workflow = Workflow(id="test", name="Test Workflow", nodes=[])
    node = Node(id="node1", workflow_id="test", node_type=NodeType.FORMATTER, config={})

    workflow.add_node(node)

    assert len(workflow.nodes) == 1
    assert workflow.nodes[0].id == "node1"
```

#### Integration Tests (Repository Layer)
```python
# tests/infrastructure/test_workflow_repository.py
@pytest.mark.asyncio
async def test_create_workflow(workflow_repo: WorkflowRepository):
    workflow = Workflow(id="test", name="Test", nodes=[])

    result = await workflow_repo.create(workflow)

    assert result.id == "test"
    assert result.name == "Test"
```

#### API Tests (Presentation Layer)
```python
# tests/presentation/test_workflow_router.py
@pytest.mark.asyncio
async def test_create_workflow_endpoint(client: AsyncClient):
    response = await client.post(
        "/workflows",
        json={"name": "Test Workflow"}
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Test Workflow"
```

## Database Design

### PostgreSQL Schema (3 Tables)

```sql
-- Workflows table
CREATE TABLE workflows (
    id VARCHAR PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Nodes table
CREATE TABLE nodes (
    id VARCHAR PRIMARY KEY,
    workflow_id VARCHAR REFERENCES workflows(id) ON DELETE CASCADE,
    node_type VARCHAR NOT NULL CHECK (node_type IN ('extract_text', 'generative_ai', 'formatter')),
    config JSONB NOT NULL DEFAULT '{}',
    order_index INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(workflow_id, order_index)
);

-- Workflow executions table (consolidated)
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

## Configuration Management

### Environment Settings
```python
# config/settings.py
class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    OPENAI_API_KEY: Optional[str]
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB

    class Config:
        env_file = ".env"
```

## Async Processing

### Celery Task Definition
```python
# application/tasks/workflow_execution.py
@celery_app.task(bind=True)
def execute_workflow_task(self, workflow_id: str, execution_id: str):
    try:
        # Get workflow and execution from database
        # Process each node sequentially
        # Update execution status
        pass
    except Exception as exc:
        # Handle errors and update execution status
        raise self.retry(exc=exc, countdown=60, max_retries=3)
```

## Code Quality Standards

### 1. **Type Hints**
- All functions must have complete type annotations
- Use `typing` module for complex types
- Prefer `Optional[T]` over `Union[T, None]`

### 2. **Linting Configuration**
```python
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py39']

[tool.isort]
profile = "black"
multi_line_output = 3

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### 3. **Testing Coverage**
- Minimum 80% code coverage
- All domain entities must be unit tested
- All API endpoints must have integration tests
- Repository implementations must have database tests

## Extension Points

### 1. **Adding File Processing**
When PDF functionality is needed:
1. Add `file_model.py` in infrastructure/db/models/
2. Implement `FileRepository` interface
3. Create `FileService` in application layer
4. Add file upload endpoints in presentation layer

### 2. **Adding Real-time Updates**
For WebSocket support:
1. Add WebSocket router in presentation layer
2. Create notification service in application layer
3. Integrate with Redis pub/sub for real-time updates

### 3. **Adding Authentication**
When user management is needed:
1. Add user entities in domain layer
2. Create authentication middleware
3. Add user context to services
4. Update database schema with user relationships

## MVP Scope

### Included in MVP:
- ✅ Workflow CRUD operations
- ✅ Node management within workflows
- ✅ Text-based input processing
- ✅ Three node types: text extraction, AI processing, formatting
- ✅ Async execution with status tracking
- ✅ PostgreSQL persistence
- ✅ Error handling and recovery

### Future Enhancements:
- 📋 PDF file upload and processing
- 📋 Real-time execution updates
- 📋 User authentication and authorization
- 📋 DAG-based workflow structure
- 📋 AI agent nodes with tool integration
- 📋 Workflow templates and sharing
- 📋 Performance monitoring and analytics

This architecture provides a solid foundation for the LayerX workflow system MVP while maintaining clear paths for future enhancements and team scalability.