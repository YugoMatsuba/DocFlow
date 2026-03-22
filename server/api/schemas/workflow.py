from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from domain.enums.node_type import NodeType

class CreateWorkflowRequest(BaseModel):
    name: str
    description: Optional[str] = None

class AddNodeRequest(BaseModel):
    name: str
    node_type: NodeType
    configuration: Dict[str, Any]
    order: Optional[int] = None

class NodeResponse(BaseModel):
    id: str
    name: str
    node_type: NodeType
    configuration: Dict[str, Any]
    order: int
    created_at: datetime

    class Config:
        from_attributes = True

class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    nodes: List[NodeResponse]
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True