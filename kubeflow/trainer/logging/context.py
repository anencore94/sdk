# Copyright 2025 The Kubeflow Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Context-aware logging utilities for Kubeflow SDK."""

from contextvars import ContextVar
import logging
from typing import Any, Optional

# Context variables for logging
_log_context: ContextVar[dict[str, Any]] = ContextVar("log_context", default=None)


class LogContext:
    """Context manager for adding structured context to log messages.

    This class allows adding contextual information that will be included
    in all log messages within the context scope.
    """

    def __init__(self, **kwargs: Any):
        """Initialize log context with key-value pairs.

        Args:
            **kwargs: Context key-value pairs to add to logs
        """
        self.context = kwargs
        self._previous_context: Optional[dict[str, Any]] = None

    def __enter__(self) -> "LogContext":
        """Enter the context and set context variables.

        Returns:
            Self for use in with statements
        """
        # Store previous context
        current_context = _log_context.get(None)
        self._previous_context = current_context if current_context is not None else {}

        # Merge with existing context
        merged_context = {**self._previous_context, **self.context}
        _log_context.set(merged_context)

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context and restore previous context.

        Args:
            exc_type: Exception type if any
            exc_val: Exception value if any
            exc_tb: Exception traceback if any
        """
        # Restore previous context
        if self._previous_context is not None:
            _log_context.set(self._previous_context)
        else:
            _log_context.set(None)


def get_log_context() -> dict[str, Any]:
    """Get current log context.

    Returns:
        Dictionary of current context variables
    """
    context = _log_context.get(None)
    return context if context is not None else {}


def set_log_context(**kwargs: Any) -> None:
    """Set log context variables.

    Args:
        **kwargs: Context key-value pairs to set
    """
    current_context = _log_context.get(None)
    base_context = current_context if current_context is not None else {}
    merged_context = {**base_context, **kwargs}
    _log_context.set(merged_context)


def clear_log_context() -> None:
    """Clear all log context variables."""
    _log_context.set(None)


class ContextualLogger:
    """Logger wrapper that automatically includes context in log messages."""

    def __init__(self, logger: logging.Logger):
        """Initialize contextual logger.

        Args:
            logger: Base logger instance
        """
        self._logger = logger

    def _add_context(self, record: logging.LogRecord) -> None:
        """Add context information to log record.

        Args:
            record: Log record to modify
        """
        context = get_log_context()
        for key, value in context.items():
            setattr(record, key, value)

    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log debug message with context."""
        self._logger.debug(msg, *args, extra=self._get_extra(), **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        """Log info message with context."""
        self._logger.info(msg, *args, extra=self._get_extra(), **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log warning message with context."""
        self._logger.warning(msg, *args, extra=self._get_extra(), **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        """Log error message with context."""
        self._logger.error(msg, *args, extra=self._get_extra(), **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        """Log critical message with context."""
        self._logger.critical(msg, *args, extra=self._get_extra(), **kwargs)

    def _get_extra(self) -> dict[str, Any]:
        """Get extra context information for log record.

        Returns:
            Dictionary of extra context information
        """
        return get_log_context()
