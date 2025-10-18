"""
Structured Logging for Yuho

Provides consistent logging across all Yuho components with proper log levels,
formatting, and output options.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class YuhoLogger:
    """Centralized logging for Yuho application"""

    _instance: Optional['YuhoLogger'] = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls):
        """Singleton pattern for logger"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize logger if not already initialized"""
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(self, level: int = logging.INFO):
        """Set up the logger with formatters and handlers"""
        self._logger = logging.getLogger('yuho')
        self._logger.setLevel(level)

        # Prevent duplicate handlers
        if self._logger.handlers:
            return

        # Console handler with color support
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        # Formatter for console
        console_formatter = ColoredFormatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)

        self._logger.addHandler(console_handler)

    def set_level(self, level: str):
        """Set logging level dynamically"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL,
        }
        if self._logger and level.upper() in level_map:
            self._logger.setLevel(level_map[level.upper()])

    def add_file_handler(self, log_file: Path):
        """Add file handler for persistent logging"""
        if not self._logger:
            return

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        # Detailed formatter for file
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)

        self._logger.addHandler(file_handler)

    def debug(self, message: str, *args, **kwargs):
        """Log debug message"""
        if self._logger:
            self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """Log info message"""
        if self._logger:
            self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log warning message"""
        if self._logger:
            self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Log error message"""
        if self._logger:
            self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """Log critical message"""
        if self._logger:
            self._logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs):
        """Log exception with traceback"""
        if self._logger:
            self._logger.exception(message, *args, **kwargs)


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output"""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }

    def format(self, record):
        """Format log record with colors"""
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            )

        # Format the message
        message = super().format(record)

        return message


# Global logger instance
logger = YuhoLogger()


# Convenience functions
def debug(message: str, *args, **kwargs):
    """Log debug message (convenience function)"""
    logger.debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs):
    """Log info message (convenience function)"""
    logger.info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    """Log warning message (convenience function)"""
    logger.warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs):
    """Log error message (convenience function)"""
    logger.error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs):
    """Log critical message (convenience function)"""
    logger.critical(message, *args, **kwargs)


def exception(message: str, *args, **kwargs):
    """Log exception with traceback (convenience function)"""
    logger.exception(message, *args, **kwargs)

