from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from uuid import uuid4
from .node import Node

class Workflow(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    nodes: List[Node] = []
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True

    @classmethod
    def create(cls, name: str, description: Optional[str] = None) -> "Workflow":
        """Factory method to create a new workflow"""
        now = datetime.utcnow()
        return cls(
            id=str(uuid4()),
            name=name,
            description=description,
            nodes=[],
            created_at=now,
            updated_at=now,
            is_active=True
        )

    def add_node(self, node: Node) -> None:
        """Add a node to the workflow"""
        if self.has_node(node.id):
            raise ValueError(f"Node with id {node.id} already exists in workflow")

        node.order = len(self.nodes)
        self.nodes.append(node)
        self.updated_at = datetime.utcnow()

    def remove_node(self, node_id: str) -> bool:
        """Remove a node from the workflow"""
        original_length = len(self.nodes)
        self.nodes = [node for node in self.nodes if node.id != node_id]

        if len(self.nodes) < original_length:
            # Reorder remaining nodes
            for i, node in enumerate(self.nodes):
                node.order = i
            self.updated_at = datetime.utcnow()
            return True
        return False

    def reorder_nodes(self, node_ids: List[str]) -> bool:
        """Reorder nodes based on provided node IDs"""
        if len(node_ids) != len(self.nodes):
            return False

        # Validate all node IDs exist
        existing_node_ids = {node.id for node in self.nodes}
        if set(node_ids) != existing_node_ids:
            return False

        # Create a mapping of node_id to node
        node_map = {node.id: node for node in self.nodes}

        # Reorder nodes and update order
        self.nodes = []
        for i, node_id in enumerate(node_ids):
            node = node_map[node_id]
            node.order = i
            self.nodes.append(node)

        self.updated_at = datetime.utcnow()
        return True

    def has_node(self, node_id: str) -> bool:
        """Check if workflow has a node with the given ID"""
        return any(node.id == node_id for node in self.nodes)

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID"""
        return next((node for node in self.nodes if node.id == node_id), None)

    def get_ordered_nodes(self) -> List[Node]:
        """Get nodes ordered by their order"""
        return sorted(self.nodes, key=lambda x: x.order)

    def validate_workflow(self) -> List[str]:
        """Validate the workflow and return list of validation errors"""
        from domain.rules.workflow_rules import WorkflowRules

        errors = []

        if not self.name or not self.name.strip():
            errors.append("Workflow name is required")

        # Check for duplicate node IDs
        node_ids = [node.id for node in self.nodes]
        if len(node_ids) != len(set(node_ids)):
            errors.append("Workflow contains duplicate node IDs")

        # Use domain rules for comprehensive validation
        domain_errors = WorkflowRules.validate_workflow(self)
        errors.extend(domain_errors)

        return errors

    def is_valid(self) -> bool:
        """Check if the workflow is valid"""
        return len(self.validate_workflow()) == 0

    def __str__(self) -> str:
        return f"Workflow(id={self.id}, name='{self.name}', nodes={len(self.nodes)})"