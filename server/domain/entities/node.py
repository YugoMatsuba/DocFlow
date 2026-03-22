from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, validator
from uuid import uuid4
from ..enums.node_type import NodeType
from ..specs.node_spec_registry import NodeSpecRegistry

class Node(BaseModel):
    id: str
    name: str
    workflow_id: str
    node_type: NodeType
    configuration: Dict[str, Any]
    order: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @validator('configuration')
    def configuration_must_be_dict(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Node configuration must be a dictionary')
        return v

    @classmethod
    def create(
        cls,
        name: str,
        node_type: NodeType,
        configuration: Dict[str, Any],
        workflow_id: str,
        order: int = 0
    ) -> "Node":
        """Factory method to create a new node"""
        node = cls(
            id=str(uuid4()),
            name=name,
            workflow_id=workflow_id,
            node_type=node_type,
            configuration=configuration,
            order=order,
            created_at=datetime.utcnow()
        )
        # Validate the configuration
        node.validate_configuration()
        return node

    def validate_configuration(self) -> None:
        """Validate only node-level common invariants.

        Node-type-specific configuration validation is handled by processors.
        """
        return None

    def get_required_configuration_keys(self) -> list[str]:
        """Get list of required configuration keys for this node type"""
        try:
            spec = NodeSpecRegistry.get_spec(self.node_type)
            return spec.required_config_keys
        except ValueError:
            # Fallback to empty list for unknown node types
            return []

    def get_optional_configuration_keys(self) -> list[str]:
        """Get list of optional configuration keys for this node type"""
        if self.node_type == NodeType.EXTRACT_TEXT:
            return []
        elif self.node_type == NodeType.GENERATIVE_AI:
            return ['model', 'temperature', 'max_tokens']
        elif self.node_type == NodeType.FORMATTER:
            return ['find', 'replace_with']  # For replace format type
        return []

    def update_configuration(self, new_configuration: Dict[str, Any]) -> None:
        """Update node configuration with node-level validation only"""
        # Create a temporary node to validate the new configuration
        temp_node = Node(
            id=self.id,
            name=self.name,
            workflow_id=self.workflow_id,
            node_type=self.node_type,
            configuration=new_configuration,
            order=self.order,
            created_at=self.created_at
        )
        temp_node.validate_configuration()

        # If validation passes, update the actual configuration
        self.configuration = new_configuration

    def is_valid(self) -> bool:
        """Check if node-level validation passes"""
        try:
            self.validate_configuration()
            return True
        except ValueError:
            return False

    def __str__(self) -> str:
        return f"Node(id={self.id}, name='{self.name}', type={self.node_type.value}, order={self.order})"
