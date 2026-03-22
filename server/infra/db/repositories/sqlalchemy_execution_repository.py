from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_

from domain.repositories.execution_repository import ExecutionRepository
from domain.entities.execution import Execution
from domain.enums.execution_status import ExecutionStatus
from ..models.execution import WorkflowExecutionModel

class SQLAlchemyExecutionRepository(ExecutionRepository):
    """SQLAlchemy implementation of ExecutionRepository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, execution: Execution) -> Execution:
        """Create a new execution"""
        db_execution = WorkflowExecutionModel(
            id=execution.id,
            workflow_id=execution.workflow_id,
            input_file_path=execution.input_file_path,
            output_data=execution.output_data,
            status=execution.status.value,
            created_at=execution.created_at or datetime.utcnow(),
            updated_at=execution.updated_at or datetime.utcnow(),
            completed_at=execution.completed_at,
            error_message=execution.error_message,
        )

        self.session.add(db_execution)
        await self.session.flush()
        await self.session.refresh(db_execution)

        return self._to_domain(db_execution)

    async def get_by_id(self, execution_id: str) -> Optional[Execution]:
        """Get execution by ID"""
        stmt = select(WorkflowExecutionModel).where(WorkflowExecutionModel.id == execution_id)
        result = await self.session.execute(stmt)
        db_execution = result.scalar_one_or_none()

        return self._to_domain(db_execution) if db_execution else None

    async def update(self, execution: Execution) -> Execution:
        """Update an existing execution"""
        stmt = (
            update(WorkflowExecutionModel)
            .where(WorkflowExecutionModel.id == execution.id)
            .values(
                input_file_path=execution.input_file_path,
                output_data=execution.output_data,
                updated_at=datetime.utcnow(),
                status=execution.status.value,
                completed_at=execution.completed_at,
                error_message=execution.error_message,
                )
            .returning(WorkflowExecutionModel)
        )
        result = await self.session.execute(stmt)
        db_execution = result.scalar_one()

        return self._to_domain(db_execution)

    async def delete(self, execution_id: str) -> bool:
        """Delete execution by ID"""
        stmt = delete(WorkflowExecutionModel).where(WorkflowExecutionModel.id == execution_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Execution]:
        """List all executions with pagination"""
        stmt = (
            select(WorkflowExecutionModel)
            .offset(offset)
            .limit(limit)
            .order_by(WorkflowExecutionModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        db_executions = result.scalars().all()

        return [self._to_domain(exec) for exec in db_executions]

    async def get_by_workflow_id(self, workflow_id: str, limit: int = 100, offset: int = 0) -> List[Execution]:
        """Get all executions for a specific workflow"""
        stmt = (
            select(WorkflowExecutionModel)
            .where(WorkflowExecutionModel.workflow_id == workflow_id)
            .offset(offset)
            .limit(limit)
            .order_by(WorkflowExecutionModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        db_executions = result.scalars().all()

        return [self._to_domain(exec) for exec in db_executions]

    async def get_by_status(self, status: ExecutionStatus, limit: int = 100, offset: int = 0) -> List[Execution]:
        """Get executions by status"""
        stmt = (
            select(WorkflowExecutionModel)
            .where(WorkflowExecutionModel.status == status.value)
            .offset(offset)
            .limit(limit)
            .order_by(WorkflowExecutionModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        db_executions = result.scalars().all()

        return [self._to_domain(exec) for exec in db_executions]

    async def get_running_executions(self) -> List[Execution]:
        """Get all currently running executions"""
        stmt = (
            select(WorkflowExecutionModel)
            .where(WorkflowExecutionModel.status == ExecutionStatus.RUNNING.value)
            .order_by(WorkflowExecutionModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        db_executions = result.scalars().all()

        return [self._to_domain(exec) for exec in db_executions]

    async def get_latest_execution(self, workflow_id: str) -> Optional[Execution]:
        """Get the most recent execution for a workflow"""
        stmt = (
            select(WorkflowExecutionModel)
            .where(WorkflowExecutionModel.workflow_id == workflow_id)
            .order_by(WorkflowExecutionModel.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        db_execution = result.scalar_one_or_none()

        return self._to_domain(db_execution) if db_execution else None

    async def update_status(self, execution_id: str, status: ExecutionStatus, error_message: Optional[str] = None) -> bool:
        """Update execution status"""
        values = {"status": status.value}

        if status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]:
            values["completed_at"] = datetime.utcnow()

        if error_message:
            values["error_message"] = error_message

        stmt = (
            update(WorkflowExecutionModel)
            .where(WorkflowExecutionModel.id == execution_id)
            .values(**values)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def update_output(self, execution_id: str, output_text: str) -> bool:
        """Update execution output text"""
        stmt = (
            update(WorkflowExecutionModel)
            .where(WorkflowExecutionModel.id == execution_id)
            .values(output_data=output_text)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def mark_as_completed(self, execution_id: str, output_text: str) -> bool:
        """Mark execution as completed with output"""
        stmt = (
            update(WorkflowExecutionModel)
            .where(WorkflowExecutionModel.id == execution_id)
            .values(
                status=ExecutionStatus.COMPLETED.value,
                output_data=output_text,
                completed_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def mark_as_failed(self, execution_id: str, error_message: str) -> bool:
        """Mark execution as failed with error message"""
        stmt = (
            update(WorkflowExecutionModel)
            .where(WorkflowExecutionModel.id == execution_id)
            .values(
                status=ExecutionStatus.FAILED.value,
                error_message=error_message,
                completed_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def get_executions_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100,
        offset: int = 0
    ) -> List[Execution]:
        """Get executions within a date range"""
        stmt = (
            select(WorkflowExecutionModel)
            .where(
                and_(
                    WorkflowExecutionModel.created_at >= start_date,
                    WorkflowExecutionModel.created_at <= end_date
                )
            )
            .offset(offset)
            .limit(limit)
            .order_by(WorkflowExecutionModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        db_executions = result.scalars().all()

        return [self._to_domain(exec) for exec in db_executions]

    def _to_domain(self, db_execution: WorkflowExecutionModel) -> Execution:
        """Convert SQLAlchemy model to domain entity"""
        if not db_execution:
            return None

        return Execution(
            id=db_execution.id,
            workflow_id=db_execution.workflow_id,
            input_file_path=db_execution.input_file_path,
            output_data=db_execution.output_data,
            status=ExecutionStatus(db_execution.status),
            created_at=db_execution.created_at,
            updated_at=db_execution.updated_at,
            completed_at=db_execution.completed_at,
            error_message=db_execution.error_message
        )
