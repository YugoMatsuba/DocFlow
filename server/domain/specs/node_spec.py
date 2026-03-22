from enum import Enum
from typing import List
from pydantic import BaseModel
from ..enums.node_type import NodeType


class NodeIOType(str, Enum):
    """Defines the input/output data types for workflow nodes"""
    PDF_FILE = "pdf_file"
    TEXT = "text"


class NodeSpec(BaseModel):
    """Specification for a node type including I/O types and configuration requirements"""
    node_type: NodeType
    input_type: NodeIOType
    output_type: NodeIOType
    required_config_keys: List[str]

    class Config:
        frozen = True  # Make instances immutable