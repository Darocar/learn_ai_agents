"""
Logging Configuration for Learn AI Agents

This module provides centralized logging configuration with:
- Pretty formatting with colors
- Structured log messages
- Different log levels for different components
- Timestamped messages
"""

import logging
import sys


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{self.BOLD}{levelname}{self.RESET}"

        # Format the message
        formatted = super().format(record)

        return formatted


def setup_logging(level: int = logging.INFO, log_format: str | None = None, use_colors: bool = True) -> None:
    """
    Setup application-wide logging configuration.

    Args:
        level: Logging level (default: INFO)
        log_format: Custom log format string (optional)
        use_colors: Whether to use colored output (default: True)
    """
    if log_format is None:
        log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    # Create formatter
    formatter: logging.Formatter
    if use_colors and sys.stderr.isatty():
        formatter = ColoredFormatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    else:
        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
