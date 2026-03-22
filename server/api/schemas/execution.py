from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from domain.enums.execution_status import ExecutionStatus

class ExecutionResponse(BaseModel):
    id: str
    workflow_id: str
    status: ExecutionStatus
    input_file_path: Optional[str]
    output_data: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True