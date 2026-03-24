from typing import Iterable, Optional


class ServiceError(Exception):
    """Base error carrying a user-safe message and optional internal context."""

    def __init__(self, public_message: str, *, log_message: Optional[str] = None):
        super().__init__(public_message)
        self.public_message = public_message
        self.log_message = log_message or public_message


class NotFoundError(ServiceError):
    """Raised when a requested domain object does not exist."""


class ValidationError(ServiceError):
    """Raised when client-provided input or workflow state is invalid."""

    def __init__(
        self,
        public_message: str,
        *,
        errors: Optional[Iterable[str]] = None,
        log_message: Optional[str] = None,
    ):
        super().__init__(public_message, log_message=log_message)
        self.errors = list(errors or [])


class ProcessingError(ServiceError):
    """Raised when background or integration processing fails."""

