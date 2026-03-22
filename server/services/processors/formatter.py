from typing import Dict, Any, List

from .base import BaseNodeProcessor

class FormatterProcessor(BaseNodeProcessor):
    """Processor for formatting text data"""

    async def process(self, input_data: str, config: Dict[str, Any]) -> str:
        """Process text formatting operation"""
        try:
            format_type = config.get("format_type")

            if format_type == "uppercase":
                return input_data.upper()
            elif format_type == "lowercase":
                return input_data.lower()
            elif format_type == "trim":
                return input_data.strip()
            elif format_type == "replace":
                find = config.get("find", "")
                replace_with = config.get("replace_with", "")
                return input_data.replace(find, replace_with)
            else:
                raise ValueError(f"Unsupported format type: {format_type}")

        except Exception as e:
            raise Exception(f"Formatting error: {str(e)}")

    def validate_config(self, config: Dict[str, Any]) -> None:
        """Validate node configuration"""
        if "format_type" not in config:
            raise ValueError("format_type is required in configuration")

        format_type = config["format_type"]
        valid_types = ["uppercase", "lowercase", "trim", "replace"]
        if format_type not in valid_types:
            raise ValueError(f"format_type must be one of: {', '.join(valid_types)}")

        if format_type == "replace":
            if "find" not in config:
                raise ValueError("find is required when format_type is 'replace'")
            if "replace_with" not in config:
                raise ValueError("replace_with is required when format_type is 'replace'")

    def get_required_config_keys(self) -> List[str]:
        """Return list of required configuration keys"""
        return ["format_type"]