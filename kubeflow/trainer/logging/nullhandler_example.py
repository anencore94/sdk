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

"""Example demonstrating NullHandler pattern for Kubeflow SDK logging.

This example shows how the SDK uses NullHandler by default to avoid logging noise,
and how users can override this by configuring their own logging.
"""

import logging

# Import the SDK - this will automatically configure NullHandler
from kubeflow.trainer import LocalProcessBackendConfig, TrainerClient


def demonstrate_nullhandler_pattern():
    """Demonstrate the NullHandler pattern in action."""

    print("=== NullHandler Pattern Demonstration ===\n")

    # 1. Default behavior - no logging output (NullHandler active)
    print("1. Default SDK behavior (no user logging configuration):")
    print("   - SDK calls will not produce any logging output")
    print("   - NullHandler prevents logging noise")

    # Use LocalProcess backend to avoid Kubernetes config issues
    config = LocalProcessBackendConfig()
    TrainerClient(backend_config=config)
    print("   - TrainerClient initialized silently")

    # 2. User configures logging - NullHandler is overridden
    print("\n2. User configures logging (DEBUG level):")
    print("   - User's configuration overrides NullHandler")
    print("   - SDK debug messages will now appear")

    # Configure logging for the demonstration
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Now SDK calls will produce debug output
    config = LocalProcessBackendConfig()
    TrainerClient(backend_config=config)
    print("   - TrainerClient initialized with debug logging visible")

    # 3. Show different log levels
    print("\n3. Different log levels:")
    print("   - Setting to INFO level - only INFO and above will show")

    # Reset and configure for INFO level
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    config = LocalProcessBackendConfig()
    TrainerClient(backend_config=config)
    print("   - DEBUG messages are suppressed, INFO+ messages visible")


def demonstrate_sdk_integration():
    """Show how users integrate the SDK with their own logging configuration."""

    print("\n=== SDK Integration Example ===\n")

    # Simulate a user application
    print("User application configuring logging:")

    # User sets up their application logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
    )

    # User's application logger
    app_logger = logging.getLogger("my_app")
    app_logger.info("Starting my application")

    # SDK calls will now respect user's logging configuration
    app_logger.info("Creating TrainerClient...")
    config = LocalProcessBackendConfig()
    TrainerClient(backend_config=config)

    app_logger.info("Application completed")


if __name__ == "__main__":
    demonstrate_nullhandler_pattern()
    demonstrate_sdk_integration()
