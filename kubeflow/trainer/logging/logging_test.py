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

"""Unit tests for Kubeflow SDK logging system."""

import io
import json
import logging
import sys

import pytest

from kubeflow.trainer.logging.config import get_logger, setup_logging
from kubeflow.trainer.logging.context import ContextualLogger, LogContext
from kubeflow.trainer.logging.formatters import StructuredFormatter


class TestLoggingConfig:
    """Test logging configuration functionality."""

    def test_get_logger(self):
        """Test get_logger returns properly named logger."""
        logger = get_logger("test_module")
        assert logger.name == "kubeflow.test_module"

    def test_get_logger_with_kubeflow_prefix(self):
        """Test get_logger handles existing kubeflow prefix."""
        logger = get_logger("kubeflow.trainer.test")
        assert logger.name == "kubeflow.trainer.test"

    def test_setup_logging_console_format(self):
        """Test console logging setup."""
        # Capture log output
        log_capture = io.StringIO()

        # Setup logging with console format
        setup_logging(level="INFO", format_type="console")

        # Get logger and test
        logger = get_logger("test")

        # Add handler to capture output
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info("Test message")

        captured = log_capture.getvalue()
        assert "INFO - Test message" in captured

    def test_setup_logging_json_format(self):
        """Test JSON logging setup."""
        log_capture = io.StringIO()

        # Setup JSON logging
        setup_logging(level="DEBUG", format_type="json")

        logger = get_logger("test")
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.info("Test message", extra={"key": "value"})

        captured = log_capture.getvalue().strip()
        log_data = json.loads(captured)

        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert log_data["key"] == "value"

    def test_setup_logging_file_output(self):
        """Test file logging setup."""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Setup logging with file output
            setup_logging(level="INFO", format_type="console", log_file=temp_path)

            logger = get_logger("test")
            logger.info("File test message")

            # Read file content
            with open(temp_path) as f:
                content = f.read()

            assert "File test message" in content
        finally:
            os.unlink(temp_path)


class TestLogContext:
    """Test LogContext functionality."""

    def test_log_context_basic(self):
        """Test basic LogContext functionality."""
        with LogContext(job_id="test-job", operation="train"):
            # Context should be available
            from kubeflow.trainer.logging.context import get_log_context

            context = get_log_context()
            assert context["job_id"] == "test-job"
            assert context["operation"] == "train"

        # Context should be cleared after exit
        context = get_log_context()
        assert context == {}

    def test_log_context_nested(self):
        """Test nested LogContext functionality."""
        with LogContext(job_id="outer-job"):
            with LogContext(operation="inner-op"):
                # Get context using the module function
                context = (
                    LogContext().get_log_context()
                    if hasattr(LogContext(), "get_log_context")
                    else {}
                )
                from kubeflow.trainer.logging.context import get_log_context

                context = get_log_context()
                assert context["job_id"] == "outer-job"
                assert context["operation"] == "inner-op"

            # Inner context should be removed, outer should remain
            from kubeflow.trainer.logging.context import get_log_context

            context = get_log_context()
            assert context["job_id"] == "outer-job"
            assert "operation" not in context

    def test_log_context_merge(self):
        """Test LogContext merging with existing context."""
        from kubeflow.trainer.logging.context import set_log_context

        # Set initial context
        set_log_context(existing_key="existing_value")

        with LogContext(new_key="new_value"):
            from kubeflow.trainer.logging.context import get_log_context

            context = get_log_context()
            assert context["existing_key"] == "existing_value"
            assert context["new_key"] == "new_value"


class TestContextualLogger:
    """Test ContextualLogger functionality."""

    def test_contextual_logger_basic(self):
        """Test basic ContextualLogger functionality."""
        log_capture = io.StringIO()

        # Setup logger
        logger = get_logger("test")
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s - %(job_id)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Create contextual logger
        contextual_logger = ContextualLogger(logger)

        with LogContext(job_id="test-job"):
            contextual_logger.info("Test message")

        captured = log_capture.getvalue()
        assert "INFO - Test message - test-job" in captured

    def test_contextual_logger_without_context(self):
        """Test ContextualLogger without context."""
        log_capture = io.StringIO()

        logger = get_logger("test")
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        contextual_logger = ContextualLogger(logger)
        contextual_logger.info("Test message without context")

        captured = log_capture.getvalue()
        assert "INFO - Test message without context" in captured


class TestNullHandlerPattern:
    """Test NullHandler pattern implementation."""

    def test_kubeflow_package_nullhandler(self):
        """Test that kubeflow package has NullHandler configured."""
        # Clear any existing logging configuration
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # Clear any existing handlers on kubeflow logger
        kubeflow_logger = logging.getLogger("kubeflow")
        for handler in kubeflow_logger.handlers[:]:
            kubeflow_logger.removeHandler(handler)

        # Import kubeflow package to trigger NullHandler setup

        # Check that it has a NullHandler
        null_handlers = [h for h in kubeflow_logger.handlers if isinstance(h, logging.NullHandler)]
        # The NullHandler should be added to the logger when kubeflow package is imported
        assert len(null_handlers) > 0, (
            f"kubeflow package should have NullHandler configured, "
            f"found handlers: {kubeflow_logger.handlers}"
        )

    def test_nullhandler_suppresses_logs(self):
        """Test that NullHandler suppresses logs by default."""
        # Import kubeflow to trigger NullHandler setup

        # Capture any output that might leak through
        log_capture = io.StringIO()

        # Setup basic logging to capture any output
        logging.basicConfig(
            level=logging.DEBUG, stream=log_capture, format="%(levelname)s - %(message)s"
        )

        # Get kubeflow logger and try to log
        kubeflow_logger = logging.getLogger("kubeflow")
        kubeflow_logger.debug("This should be suppressed by NullHandler")

        # Check that no output was captured (NullHandler working)
        captured = log_capture.getvalue()
        assert "This should be suppressed by NullHandler" not in captured

    def test_user_configuration_overrides_nullhandler(self):
        """Test that user logging configuration overrides NullHandler."""
        # Clear any existing handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # Import kubeflow to setup NullHandler

        # User configures logging
        log_capture = io.StringIO()
        logging.basicConfig(
            level=logging.DEBUG, stream=log_capture, format="%(levelname)s - %(name)s - %(message)s"
        )

        # Now kubeflow logging should work
        kubeflow_logger = logging.getLogger("kubeflow")
        kubeflow_logger.debug("This should now be visible")

        captured = log_capture.getvalue()
        # The logging should work when user configures it
        assert "This should now be visible" in captured or "DEBUG" in captured


class TestStructuredFormatter:
    """Test StructuredFormatter functionality."""

    def test_structured_formatter_basic(self):
        """Test basic StructuredFormatter functionality."""
        formatter = StructuredFormatter()

        # Create a log record
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Format the record
        formatted = formatter.format(record)

        # Parse as JSON
        log_data = json.loads(formatted)

        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert log_data["logger"] == "test.logger"
        assert log_data["line"] == 42

    def test_structured_formatter_with_extra(self):
        """Test StructuredFormatter with extra fields."""
        formatter = StructuredFormatter()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Add extra fields
        record.job_id = "test-job-123"
        record.operation = "train"

        formatted = formatter.format(record)
        log_data = json.loads(formatted)

        assert log_data["job_id"] == "test-job-123"
        assert log_data["operation"] == "train"

    def test_structured_formatter_with_exception(self):
        """Test StructuredFormatter with exception information."""
        formatter = StructuredFormatter()

        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name="test.logger",
                level=logging.ERROR,
                pathname="/test/path",
                lineno=42,
                msg="Test message",
                args=(),
                exc_info=sys.exc_info(),
            )

            formatted = formatter.format(record)
            log_data = json.loads(formatted)

            assert log_data["level"] == "ERROR"
            assert "exception" in log_data
            assert "ValueError: Test exception" in log_data["exception"]


if __name__ == "__main__":
    pytest.main([__file__])
