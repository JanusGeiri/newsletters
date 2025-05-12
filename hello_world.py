#!/usr/bin/env python3
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Print hello world and write it to a file."""
    message = "Hello World"

    # Print to console
    print(message)
    logger.info(f"Printed to console: {message}")


if __name__ == "__main__":
    main()
