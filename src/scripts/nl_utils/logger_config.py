import logging
import os
from datetime import datetime

# Global variable to track if root logger is configured
_root_logger_configured = False


def get_module_name(name):
    """Extract the module name from __name__.

    Args:
        name (str): The __name__ value from the module

    Returns:
        str: The last part of the module name after splitting by '.'
    """
    return name.split('.')[-1]


def setup_logger(name='NO_NAME_PROVIDED', log_file_base=None, configure_debug=False):
    """Set up and return a logger instance.

    Args:
        name (str): Name of the logger
        log_file_base (str): Base name for the log file. If None, will use timestamp.

    Returns:
        logging.Logger: Configured logger instance
    """
    global _root_logger_configured

    # Create logs directory if it doesn't exist
    os.makedirs('src/logs', exist_ok=True)

    # Configure root logger first if not already configured
    if not _root_logger_configured:
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # Create file handler with timestamp if no base name provided
        if log_file_base is None:
            log_file_base = f'newsletter_{datetime.now().strftime("%Y_%m_%d___%H_%M_%S")}.log'

        log_file = os.path.join('src/logs', log_file_base)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(
            logging.INFO if not configure_debug else logging.DEBUG)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(
            logging.INFO if not configure_debug else logging.DEBUG)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)-25s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to root logger
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        # Suppress file_cache warning
        logging.getLogger(
            'googleapiclient.discovery_cache').setLevel(logging.ERROR)

        _root_logger_configured = True

    # Get the named logger
    nl_logger = logging.getLogger(name)
    nl_logger.propagate = True  # Ensure messages propagate to root logger
    return nl_logger


def get_logger(name='newsletter'):
    """Get a logger instance with the same configuration.

    Args:
        name (str): Name of the logger

    Returns:
        logging.Logger: Configured logger instance
    """
    nl_logger = logging.getLogger(name)
    nl_logger.propagate = True  # Ensure messages propagate to root logger
    return nl_logger


if __name__ == '__main__':
    # Example usage
    logger = setup_logger(name='config_test')
    logger.info("This is a test log from logger_config.py")
