from abc import ABC, abstractmethod
from typing import Awaitable, Callable


class ExecutionDispatcher(ABC):
    """Application-facing interface for scheduling execution processing."""

    @abstractmethod
    def dispatch(
        self,
        execution_id: str,
        execution_handler: Callable[[str], Awaitable[None]],
    ) -> None:
        """Schedule asynchronous processing for the given execution."""
