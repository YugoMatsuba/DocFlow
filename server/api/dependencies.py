from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from infra.db.database import get_db_session
from infra.db.repositories.sqlalchemy_workflow_repository import SQLAlchemyWorkflowRepository
from infra.db.repositories.sqlalchemy_execution_repository import SQLAlchemyExecutionRepository
from domain.repositories.workflow_repository import WorkflowRepository
from domain.repositories.execution_repository import ExecutionRepository
from services.workflow_service import WorkflowService
from services.execution_service import ExecutionService

def get_workflow_repository(
    session: AsyncSession = Depends(get_db_session)
) -> WorkflowRepository:
    """Get workflow repository implementation"""
    return SQLAlchemyWorkflowRepository(session)

def get_execution_repository(
    session: AsyncSession = Depends(get_db_session)
) -> ExecutionRepository:
    """Get execution repository implementation"""
    return SQLAlchemyExecutionRepository(session)

def get_workflow_service(
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository)
) -> WorkflowService:
    """Get workflow service with injected dependencies"""
    return WorkflowService(workflow_repo)

def get_execution_service(
    execution_repo: ExecutionRepository = Depends(get_execution_repository),
    workflow_repo: WorkflowRepository = Depends(get_workflow_repository)
) -> ExecutionService:
    """Get execution service with injected dependencies"""
    return ExecutionService(execution_repo, workflow_repo)