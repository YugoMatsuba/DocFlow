from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from .base_repository import BaseRepository
from ..entities.execution import Execution
from ..enums.execution_status import ExecutionStatus

class ExecutionRepository(BaseRepository[Execution], ABC):
    """Repository interface for Workflow Execution operations"""

    @abstractmethod
    async def get_by_workflow_id(self, workflow_id: str, limit: int = 100, offset: int = 0) -> List[Execution]:
        """Get all executions for a specific workflow"""
        pass

    @abstractmethod
    async def get_by_status(self, status: ExecutionStatus, limit: int = 100, offset: int = 0) -> List[Execution]:
        """Get executions by status"""
        pass

    @abstractmethod
    async def get_running_executions(self) -> List[Execution]:
        """Get all currently running executions"""
        pass

    @abstractmethod
    async def get_latest_execution(self, workflow_id: str) -> Optional[Execution]:
        """Get the most recent execution for a workflow"""
        pass

    @abstractmethod
    async def update_status(self, execution_id: str, status: ExecutionStatus, error_message: Optional[str] = None) -> bool:
        """Update execution status"""
        pass

    @abstractmethod
    async def update_output(self, execution_id: str, output_text: str) -> bool:
        """Update execution output text"""
        pass

    @abstractmethod
    async def mark_as_completed(self, execution_id: str, output_text: str) -> bool:
        """Mark execution as completed with output"""
        pass

    @abstractmethod
    async def mark_as_failed(self, execution_id: str, error_message: str) -> bool:
        """Mark execution as failed with error message"""
        pass

    @abstractmethod
    async def get_executions_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100,
        offset: int = 0
    ) -> List[Execution]:
        """Get executions within a date range"""
        pass