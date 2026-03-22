from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseNodeProcessor(ABC):
    """Base class for all node processors"""

    @abstractmethod
    async def process(self, input_data: str, config: Dict[str, Any]) -> str:
        """Process the node with given input data and return processed output"""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> None:
        """Validate node configuration, raise exception if invalid"""
        pass

    @abstractmethod
    def get_required_config_keys(self) -> List[str]:
        """Return list of required configuration keys for this processor"""
        pass