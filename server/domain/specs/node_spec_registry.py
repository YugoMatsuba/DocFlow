from typing import Dict
from .node_spec import NodeSpec, NodeIOType
from ..enums.node_type import NodeType


class NodeSpecRegistry:
    """Registry that maps node types to their specifications"""

    # Define the mapping from NodeType to NodeSpec
    _NODE_SPECS: Dict[NodeType, NodeSpec] = {
        NodeType.EXTRACT_TEXT: NodeSpec(
            node_type=NodeType.EXTRACT_TEXT,
            input_type=NodeIOType.PDF_FILE,
            output_type=NodeIOType.TEXT,
            required_config_keys=[],
        ),
        NodeType.GENERATIVE_AI: NodeSpec(
            node_type=NodeType.GENERATIVE_AI,
            input_type=NodeIOType.TEXT,
            output_type=NodeIOType.TEXT,
            required_config_keys=["prompt"],
        ),
        NodeType.FORMATTER: NodeSpec(
            node_type=NodeType.FORMATTER,
            input_type=NodeIOType.TEXT,
            output_type=NodeIOType.TEXT,
            required_config_keys=["format_type"],
        ),
    }

    @classmethod
    def get_spec(cls, node_type: NodeType) -> NodeSpec:
        """Get the node specification for a given node type

        Args:
            node_type: The type of node to get the spec for

        Returns:
            NodeSpec: The specification for the node type

        Raises:
            ValueError: If the node type is not supported
        """
        if node_type not in cls._NODE_SPECS:
            raise ValueError(f"Unsupported node type: {node_type}")

        return cls._NODE_SPECS[node_type]

    @classmethod
    def get_all_specs(cls) -> Dict[NodeType, NodeSpec]:
        """Get all registered node specifications

        Returns:
            Dict[NodeType, NodeSpec]: Dictionary mapping node types to their specs
        """
        return cls._NODE_SPECS.copy()

    @classmethod
    def is_supported(cls, node_type: NodeType) -> bool:
        """Check if a node type is supported

        Args:
            node_type: The node type to check

        Returns:
            bool: True if the node type is supported, False otherwise
        """
        return node_type in cls._NODE_SPECS