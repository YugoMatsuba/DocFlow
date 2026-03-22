from typing import Dict, Type
from typing import Any

from domain.enums.node_type import NodeType
from .base import BaseNodeProcessor
from .extract_text import ExtractTextProcessor
from .generative_ai import GenerativeAIProcessor
from .formatter import FormatterProcessor

class ProcessorRegistry:
    """Registry for mapping node types to processor implementations"""

    _processors: Dict[NodeType, Type[BaseNodeProcessor]] = {
        NodeType.EXTRACT_TEXT: ExtractTextProcessor,
        NodeType.GENERATIVE_AI: GenerativeAIProcessor,
        NodeType.FORMATTER: FormatterProcessor,
    }

    @classmethod
    def get_processor(cls, node_type: NodeType) -> BaseNodeProcessor:
        """Get processor instance for node type"""
        processor_class = cls._processors.get(node_type)

        if not processor_class:
            raise ValueError(f"No processor available for node type: {node_type}")

        return processor_class()

    @classmethod
    def get_supported_node_types(cls) -> list[NodeType]:
        """Get list of supported node types"""
        return list(cls._processors.keys())

    @classmethod
    def validate_config(cls, node_type: NodeType, config: Dict[str, Any]) -> None:
        """Validate configuration for a node type using its processor."""
        processor = cls.get_processor(node_type)
        processor.validate_config(config)

    @classmethod
    def register_processor(cls, node_type: NodeType, processor_class: Type[BaseNodeProcessor]):
        """Register a new processor for a node type"""
        cls._processors[node_type] = processor_class
