from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel
from uuid import uuid4
from ..enums.execution_status import ExecutionStatus

class Execution(BaseModel):
    id: str
    workflow_id: str
    status: ExecutionStatus = ExecutionStatus.RUNNING
    input_file_path: Optional[str] = None
    output_data: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @classmethod
    def create(
        cls,
        workflow_id: str,
        input_file_path: Optional[str] = None
    ) -> "Execution":
        """Factory method to create a new execution"""
        now = datetime.utcnow()
        return cls(
            id=str(uuid4()),
            workflow_id=workflow_id,
            input_file_path=input_file_path,
            status=ExecutionStatus.RUNNING,
            created_at=now,
            updated_at=now
        )


    def complete_execution(self, output_data: Optional[str] = None) -> None:
        """Mark execution as completed with output"""
        if not self.is_running():
            raise ValueError(f"Cannot complete execution in {self.status} status")

        self.status = ExecutionStatus.COMPLETED
        self.output_data = output_data
        now = datetime.utcnow()
        self.updated_at = now
        self.completed_at = now

    def fail_execution(self, error_message: str) -> None:
        """Mark execution as failed with error message"""
        if self.is_completed():
            raise ValueError("Cannot fail already completed execution")

        self.status = ExecutionStatus.FAILED
        self.error_message = error_message
        now = datetime.utcnow()
        self.updated_at = now
        self.completed_at = now

    def is_completed(self) -> bool:
        """Check if execution is completed (successfully or failed)"""
        return self.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]

    def is_running(self) -> bool:
        """Check if execution is currently running"""
        return self.status == ExecutionStatus.RUNNING


    def is_successful(self) -> bool:
        """Check if execution completed successfully"""
        return self.status == ExecutionStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if execution failed"""
        return self.status == ExecutionStatus.FAILED

    def get_duration_seconds(self) -> Optional[float]:
        """Get execution duration in seconds"""
        if self.completed_at:
            return (self.completed_at - self.created_at).total_seconds()
        elif self.status == ExecutionStatus.RUNNING:
            return (datetime.utcnow() - self.created_at).total_seconds()
        return None

    def validate_execution(self) -> List[str]:
        """Validate the execution and return list of validation errors"""
        errors = []

        if not self.workflow_id:
            errors.append("Execution must have a workflow_id")

        if self.is_completed() and not self.completed_at:
            errors.append("Completed execution must have completed_at timestamp")

        if self.is_failed() and not self.error_message:
            errors.append("Failed execution must have error_message")

        return errors

    def is_valid(self) -> bool:
        """Check if the execution is valid"""
        return len(self.validate_execution()) == 0

    def __str__(self) -> str:
        duration = f" ({self.get_duration_seconds():.2f}s)" if self.get_duration_seconds() else ""
        return f"Execution(id={self.id}, status={self.status.value}{duration})"