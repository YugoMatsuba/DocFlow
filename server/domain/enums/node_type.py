from enum import Enum

class NodeType(str, Enum):
    EXTRACT_TEXT = "EXTRACT_TEXT"
    GENERATIVE_AI = "GENERATIVE_AI"
    FORMATTER = "FORMATTER"