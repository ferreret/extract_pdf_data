import logging
import logging.handlers
import os
import sys
import glob
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union

from settings import LOGGING_CONFIG, LOG_FILE_PATH, LOG_DIR, LOG_COLORS


class CustomLogRecord(logging.LogRecord):
    """Custom LogRecord that supports additional context."""
    
    def __init__(self, name, level, pathname, lineno, msg, args, exc_info=None, func=None, sinfo=None, **kwargs):
        super().__init__(name, level, pathname, lineno, msg, args, exc_info, func, sinfo)
        # Store any additional attributes
        for key, value in kwargs.items():
            setattr(self, key, value)


logging.setLogRecordFactory(CustomLogRecord)


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter to add colors to log levels for terminal output.
    """
    
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super().__init__(fmt, datefmt)
        self.colors = LOG_COLORS
    
    def format(self, record):
        # Add color to the levelname
        levelname = record.levelname
        if levelname in self.colors:
            record.levelname = f"{self.colors[levelname]}{levelname}{self.colors['RESET']}"
        
        # Format the message
        formatted_message = super().format(record)
        
        # Reset levelname to original value (without colors) for file handlers
        record.levelname = levelname
        
        return formatted_message


class ContextFormatter(logging.Formatter):
    """
    Custom formatter to include detailed context information.
    """
    
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super().__init__(fmt, datefmt)
    
    def format(self, record) -> str:
        # Add custom context if available
        if hasattr(record, 'custom_context'):
            record.msg = f"[{record.custom_context}] {record.msg}"  # type: ignore
        
        return super().format(record)


class DateRotatingFileHandler(logging.handlers.BaseRotatingHandler):
    """
    Custom file handler that creates daily log files with format yyyyMMdd.log
    and only keeps the last 5 days of logs.
    """
    
    def __init__(self, log_dir: str = LOG_DIR, encoding: str = 'utf8'):
        self.log_dir = log_dir
        self.encoding = encoding
        self.current_date = datetime.now().strftime('%Y%m%d')
        self.current_file_path = os.path.join(log_dir, f"{self.current_date}.log")
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Clean up old log files (older than 5 days)
        self._cleanup_old_logs()
        
        super().__init__(
            self.current_file_path,
            mode='a',
            encoding=encoding,
            delay=False
        )
    
    def _cleanup_old_logs(self):
        """Remove log files older than 5 days."""
        cutoff_date = datetime.now() - timedelta(days=5)
        
        # Find all log files matching the pattern yyyyMMdd.log
        log_pattern = os.path.join(self.log_dir, "*.log")
        log_files = glob.glob(log_pattern)
        
        for log_file in log_files:
            # Extract date from filename
            basename = os.path.basename(log_file)
            date_part = basename.split('.')[0]
            
            try:
                file_date = datetime.strptime(date_part, '%Y%m%d')
                if file_date < cutoff_date:
                    os.remove(log_file)
            except ValueError:
                # Skip files that don't match the expected date format
                continue
    
    def _get_current_date(self):
        """Get current date string in yyyyMMdd format."""
        return datetime.now().strftime('%Y%m%d')
    
    def shouldRollover(self, record):
        """Check if we should rollover to a new log file."""
        current_date = self._get_current_date()
        return current_date != self.current_date
    
    def doRollover(self):
        """Perform rollover to a new log file."""
        # Close current file
        if self.stream:
            self.stream.close()
        
        # Update current date and file path
        self.current_date = self._get_current_date()
        self.current_file_path = os.path.join(self.log_dir, f"{self.current_date}.log")
        
        # Clean up old logs
        self._cleanup_old_logs()
        
        # Open new file
        self.mode = 'a'
        self.stream = self._open()


class Logger:
    """
    A logger class that provides both colored console output and file logging
    with full context information and runtime configuration options.
    """
    
    def __init__(self, name: Optional[str] = None, log_file: str = LOG_FILE_PATH):
        self.name = name or __name__
        self.log_file = log_file
        self.logger = logging.getLogger(self.name)
        self.console_handler = None
        self.file_handler = None
        self._setup_logger()
    
    def _setup_logger(self):
        """Set up the logger with console and file handlers."""
        # Only set up handlers if they don't exist yet
        if not self.logger.handlers:
            # Set the log level
            self.logger.setLevel(logging.DEBUG)
            
            # Prevent propagation to parent loggers to avoid duplicates
            self.logger.propagate = False
            
            # Create console handler with colored formatter
            self.console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = ColoredFormatter(
                fmt='%(asctime)s [%(levelname)s] %(module)s:%(funcName)s:%(lineno)d - %(message)s',
                datefmt='%H:%M:%S'
            )
            self.console_handler.setFormatter(console_formatter)
            self.logger.addHandler(self.console_handler)
            
            # Create logs directory if it doesn't exist
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            
            # Create file handler with date-based rotation using our custom handler
            self.file_handler = DateRotatingFileHandler(
                log_dir=os.path.dirname(self.log_file),
                encoding='utf8'
            )
            file_formatter = ContextFormatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            self.file_handler.setFormatter(file_formatter)
            self.logger.addHandler(self.file_handler)
    
    def debug(self, message: str, **kwargs):
        """Log a debug message."""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log an info message."""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log a warning message."""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log an error message."""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log a critical message."""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log an exception with traceback."""
        kwargs['exc_info'] = True
        self._log(logging.ERROR, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal method to log a message with optional context."""
        # Add custom context if provided
        if 'context' in kwargs:
            extra = {'custom_context': kwargs['context']}
            self.logger.log(level, message, extra=extra, exc_info=kwargs.get('exc_info', False))
        else:
            self.logger.log(level, message, exc_info=kwargs.get('exc_info', False))
    
    def set_level(self, level: str):
        """
        Set the logging level at runtime.
        
        Args:
            level: One of 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
        """
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        if level.upper() in level_map:
            self.logger.setLevel(level_map[level.upper()])
            if self.console_handler:
                self.console_handler.setLevel(level_map[level.upper()])
            if self.file_handler:
                self.file_handler.setLevel(level_map[level.upper()])
        else:
            raise ValueError(f"Invalid log level: {level}. Valid levels are: {list(level_map.keys())}")
    
    def enable_console(self):
        """Enable console output."""
        if self.console_handler and self.console_handler not in self.logger.handlers:
            self.logger.addHandler(self.console_handler)
    
    def disable_console(self):
        """Disable console output."""
        if self.console_handler and self.console_handler in self.logger.handlers:
            self.logger.removeHandler(self.console_handler)
    
    def enable_file(self):
        """Enable file output."""
        if self.file_handler and self.file_handler not in self.logger.handlers:
            self.logger.addHandler(self.file_handler)
    
    def disable_file(self):
        """Disable file output."""
        if self.file_handler and self.file_handler in self.logger.handlers:
            self.logger.removeHandler(self.file_handler)
    
    def add_custom_context(self, context: Dict[str, Any]):
        """
        Add custom context that will be included in all subsequent log messages.
        
        Args:
            context: Dictionary of context information
        """
        context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
        self._context = context_str
    
    def clear_custom_context(self):
        """Clear any custom context."""
        self._context = None


# Create a default logger instance
default_logger = Logger(__name__)


def get_logger(name: Optional[str] = None) -> Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Name for the logger. If None, uses the calling module's name.
    
    Returns:
        Logger instance
    """
    logger_name = name or __name__
    # Check if we already have a logger with this name in the logging module
    existing_logger = logging.getLogger(logger_name)
    if existing_logger.handlers:
        # Return a Logger instance that wraps the existing logger
        logger = Logger.__new__(Logger)
        logger.name = logger_name
        logger.logger = existing_logger
        logger.console_handler = None
        logger.file_handler = None
        return logger
    else:
        # Create a new Logger instance
        return Logger(logger_name)


# Convenience functions that use the default logger
def debug(message: str, **kwargs):
    """Log a debug message using the default logger."""
    default_logger.debug(message, **kwargs)


def info(message: str, **kwargs):
    """Log an info message using the default logger."""
    default_logger.info(message, **kwargs)


def warning(message: str, **kwargs):
    """Log a warning message using the default logger."""
    default_logger.warning(message, **kwargs)


def error(message: str, **kwargs):
    """Log an error message using the default logger."""
    default_logger.error(message, **kwargs)


def critical(message: str, **kwargs):
    """Log a critical message using the default logger."""
    default_logger.critical(message, **kwargs)


def exception(message: str, **kwargs):
    """Log an exception with traceback using the default logger."""
    default_logger.exception(message, **kwargs)


def set_level(level: str):
    """Set the logging level for the default logger."""
    default_logger.set_level(level)


def enable_console():
    """Enable console output for the default logger."""
    default_logger.enable_console()


def disable_console():
    """Disable console output for the default logger."""
    default_logger.disable_console()


def enable_file():
    """Enable file output for the default logger."""
    default_logger.enable_file()


def disable_file():
    """Disable file output for the default logger."""
    default_logger.disable_file()