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

"""Custom log formatters for Kubeflow SDK."""

from datetime import datetime, timezone
import json
import logging
from typing import Optional


class StructuredFormatter(logging.Formatter):
    """JSON structured formatter for Kubeflow SDK logs.

    This formatter outputs logs in JSON format, making them suitable for
    log aggregation systems like ELK stack, Fluentd, etc.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON formatted log string
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
            }:
                log_entry[key] = value

        return json.dumps(log_entry, ensure_ascii=False)


class ContextFormatter(logging.Formatter):
    """Context-aware formatter that includes operation context in logs.

    This formatter adds contextual information like job_id, operation_type,
    and other relevant metadata to log messages.
    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        include_context: bool = True,
    ):
        """Initialize context formatter.

        Args:
            fmt: Log format string
            datefmt: Date format string
            include_context: Whether to include context information
        """
        if fmt is None:
            fmt = "%(asctime)s - %(name)s - %(levelname)s - %(context)s - %(message)s"

        super().__init__(fmt, datefmt)
        self.include_context = include_context

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with context information.

        Args:
            record: Log record to format

        Returns:
            Formatted log string with context
        """
        # Add context information
        context_parts = []

        # Add job_id if available
        if hasattr(record, "job_id"):
            context_parts.append(f"job_id={record.job_id}")

        # Add operation type if available
        if hasattr(record, "operation"):
            context_parts.append(f"operation={record.operation}")

        # Add backend type if available
        if hasattr(record, "backend"):
            context_parts.append(f"backend={record.backend}")

        # Set context string
        if context_parts and self.include_context:
            record.context = " | ".join(context_parts)
        else:
            record.context = "general"

        return super().format(record)
