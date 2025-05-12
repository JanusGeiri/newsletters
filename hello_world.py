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

    # Write to file
    output_file = Path('hello_world.txt')
    try:
        with open(output_file, 'w') as f:
            f.write(message)
        logger.info(f"Successfully wrote to {output_file}")
    except Exception as e:
        logger.error(f"Error writing to file: {e}")


if __name__ == "__main__":
    main()
