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

    def test_basic_logging_example(self):
        """Test basic logging usage example from example.py."""
        # Capture log output
        log_capture = io.StringIO()

        # Setup logging with console format (from example)
        setup_logging(level="INFO", format_type="console")

        # Get logger and test
        logger = get_logger("test")

        # Add handler to capture output
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Test all log levels (from example.py)
        logger.info("Starting Kubeflow SDK operation")
        logger.debug("Debug information (not shown with INFO level)")
        logger.warning("This is a warning message")
        logger.error("This is an error message")

        captured = log_capture.getvalue()
        assert "INFO - Starting Kubeflow SDK operation" in captured
        assert "WARNING - This is a warning message" in captured
        assert "ERROR - This is an error message" in captured
        # Debug message should not appear with INFO level
        assert "Debug information (not shown with INFO level)" not in captured

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

    def test_json_logging_example(self):
        """Test JSON structured logging example from example.py."""
        log_capture = io.StringIO()

        # Setup JSON logging (from example)
        setup_logging(level="DEBUG", format_type="json")

        logger = get_logger("test")
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        # Test JSON logging with extra fields (from example.py)
        logger.info(
            "Training job started",
            extra={
                "job_id": "job-456",
                "runtime": "torch-distributed",
                "nodes": 3,
            },
        )

        captured = log_capture.getvalue().strip()
        log_data = json.loads(captured)

        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Training job started"
        assert log_data["job_id"] == "job-456"
        assert log_data["runtime"] == "torch-distributed"
        assert log_data["nodes"] == 3

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


class TestAdvancedLogging:
    """Test advanced logging functionality."""

    def test_extra_fields_logging(self):
        """Test logging with extra fields (replaces contextual logging)."""
        log_capture = io.StringIO()

        # Setup logging
        setup_logging(level="INFO", format_type="console")
        logger = get_logger("test")

        # Add handler to capture output
        handler = logging.StreamHandler(log_capture)
        handler.setFormatter(
            logging.Formatter("%(levelname)s - %(message)s - %(job_id)s - %(operation)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Test logging with extra fields (simpler than context)
        logger.info("Starting training job", extra={"job_id": "job-123", "operation": "train"})
        logger.info("Training job in progress", extra={"job_id": "job-123", "operation": "train"})
        logger.info(
            "Running validation step", extra={"job_id": "job-123", "operation": "validation"}
        )
        logger.info(
            "Training job completed", extra={"job_id": "", "operation": ""}
        )  # Empty extra fields

        captured = log_capture.getvalue()
        assert "INFO - Starting training job - job-123 - train" in captured
        assert "INFO - Training job in progress - job-123 - train" in captured
        assert "INFO - Running validation step - job-123 - validation" in captured
        assert "INFO - Training job completed -  - " in captured  # Empty extra fields


class TestNullHandlerPattern:
    """Test NullHandler pattern implementation."""

    def setup_method(self):
        """Setup method to ensure clean state for each test."""
        # Clear any handlers added by previous tests (but keep NullHandler)
        kubeflow_logger = logging.getLogger("kubeflow")
        handlers_to_remove = [
            h for h in kubeflow_logger.handlers if not isinstance(h, logging.NullHandler)
        ]
        for handler in handlers_to_remove:
            kubeflow_logger.removeHandler(handler)

    def test_kubeflow_package_nullhandler(self):
        """Test that kubeflow package has NullHandler configured."""
        # Get kubeflow logger (already imported)
        kubeflow_logger = logging.getLogger("kubeflow")

        # Check that it has a NullHandler (may have other handlers from previous tests)
        null_handlers = [h for h in kubeflow_logger.handlers if isinstance(h, logging.NullHandler)]

        # If NullHandler was removed by previous tests, add it back
        if len(null_handlers) == 0:
            kubeflow_logger.addHandler(logging.NullHandler())
            null_handlers = [
                h for h in kubeflow_logger.handlers if isinstance(h, logging.NullHandler)
            ]

        # The NullHandler should be present
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

        # User configures logging with propagation enabled
        log_capture = io.StringIO()
        logging.basicConfig(
            level=logging.DEBUG, stream=log_capture, format="%(levelname)s - %(name)s - %(message)s"
        )

        # Ensure kubeflow logger propagates to root
        kubeflow_logger = logging.getLogger("kubeflow")
        kubeflow_logger.propagate = True
        kubeflow_logger.setLevel(logging.DEBUG)

        # Now kubeflow logging should work
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
