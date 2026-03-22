from typing import Awaitable, Callable

from fastapi import BackgroundTasks

from services.execution_dispatcher import ExecutionDispatcher


class BackgroundTasksExecutionDispatcher(ExecutionDispatcher):
    """FastAPI BackgroundTasks adapter for execution dispatching."""

    def __init__(self, background_tasks: BackgroundTasks):
        self.background_tasks = background_tasks

    def dispatch(
        self,
        execution_id: str,
        execution_handler: Callable[[str], Awaitable[None]],
    ) -> None:
        self.background_tasks.add_task(execution_handler, execution_id)
