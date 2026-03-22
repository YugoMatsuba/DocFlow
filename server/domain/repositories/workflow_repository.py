from abc import ABC, abstractmethod
from typing import List, Optional
from .base_repository import BaseRepository
from ..entities.workflow import Workflow
from ..entities.node import Node

class WorkflowRepository(BaseRepository[Workflow], ABC):
    """Repository interface for Workflow aggregate operations"""

    @abstractmethod
    async def get_with_nodes(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow with all its nodes loaded"""
        pass

    @abstractmethod
    async def add_node(self, workflow_id: str, node: Node) -> Node:
        """Add a node to a workflow"""
        pass

    @abstractmethod
    async def remove_node(self, workflow_id: str, node_id: str) -> bool:
        """Remove a node from a workflow"""
        pass

    @abstractmethod
    async def reorder_nodes(self, workflow_id: str, node_ids: List[str]) -> bool:
        """Reorder nodes in a workflow"""
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Workflow]:
        """Get workflow by name"""
        pass

    @abstractmethod
    async def list_active(self, limit: int = 100, offset: int = 0) -> List[Workflow]:
        """List all active workflows"""
        pass