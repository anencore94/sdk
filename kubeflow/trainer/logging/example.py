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

"""Example usage of Kubeflow SDK logging system."""

from .config import get_logger, setup_logging
from .context import ContextualLogger, LogContext


def example_basic_logging():
    """Example of basic logging usage."""
    # Setup logging
    setup_logging(level="INFO", format_type="console")

    # Get logger
    logger = get_logger(__name__)

    # Log messages
    logger.info("Starting Kubeflow SDK operation")
    logger.debug("Debug information (not shown with INFO level)")
    logger.warning("This is a warning message")
    logger.error("This is an error message")


def example_contextual_logging():
    """Example of contextual logging usage."""
    # Setup logging
    setup_logging(level="INFO", format_type="detailed")

    # Get contextual logger
    logger = ContextualLogger(get_logger(__name__))

    # Use context manager
    with LogContext(job_id="job-123", operation="train", backend="kubernetes"):
        logger.info("Starting training job")
        logger.info("Training job in progress")

        # Nested context
        with LogContext(step="validation"):
            logger.info("Running validation step")

    logger.info("Training job completed")


def example_json_logging():
    """Example of JSON structured logging."""
    # Setup JSON logging
    setup_logging(level="DEBUG", format_type="json")

    logger = get_logger(__name__)

    # Log with extra fields
    logger.info(
        "Training job started",
        extra={
            "job_id": "job-456",
            "runtime": "torch-distributed",
            "nodes": 3,
        },
    )


if __name__ == "__main__":
    print("=== Basic Logging Example ===")
    example_basic_logging()

    print("\n=== Contextual Logging Example ===")
    example_contextual_logging()

    print("\n=== JSON Logging Example ===")
    example_json_logging()
