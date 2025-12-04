# Logging Module Documentation

This document describes the custom logging module that provides colored terminal output and file logging with full context information.

## Features

- **Colored terminal output** for different log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **File logging** with automatic rotation (10MB max, 5 backup files)
- **Full context information** including module name, function name, and line numbers
- **Runtime configuration** to change log levels and enable/disable outputs
- **Custom context support** to add additional information to log messages

## Quick Start

### Basic Usage

```python
from logger import get_logger, info, warning, error, set_level

# Get a logger instance
logger = get_logger(__name__)

# Log messages at different levels
logger.debug("Debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical issue")

# Use convenience functions
info("This is an info message")
warning("This is a warning message")
```

### Logging with Custom Context

```python
# Add context to a specific log message
logger.info("User logged in", context={"user_id": 12345, "ip": "192.168.1.1"})

# Add persistent context to all subsequent messages
logger.add_custom_context({"request_id": "abc123", "session": "xyz789"})
logger.info("Processing request")
logger.warning("Rate limit approaching")
logger.clear_custom_context()
```

### Runtime Configuration

```python
# Change log level at runtime
set_level("WARNING")  # Only show WARNING, ERROR, and CRITICAL

# Enable/disable console output
logger.disable_console()
logger.enable_console()

# Enable/disable file output
logger.disable_file()
logger.enable_file()
```

### Exception Logging

```python
try:
    # Some code that might raise an exception
    result = 1 / 0
except Exception:
    logger.exception("An error occurred during calculation")
```

## Log Levels and Colors

| Level | Color | Description |
|-------|-------|-------------|
| DEBUG | Cyan | Detailed information for debugging purposes |
| INFO | Green | General information about program execution |
| WARNING | Yellow | Something unexpected happened, but the software is still working |
| ERROR | Red | Serious problem occurred, software may not be able to perform some function |
| CRITICAL | Magenta | Serious error, the program itself may be unable to continue running |

## Configuration

The logging module can be configured through `settings.py`:

```python
# Log file paths
LOG_FILE_PATH = "logs/app.log"
LOG_DIR = "logs"

# Default log level
DEFAULT_LOG_LEVEL = "DEBUG"

# Log colors for terminal output
LOG_COLORS = {
    "DEBUG": "\033[36m",      # Cyan
    "INFO": "\033[32m",       # Green
    "WARNING": "\033[33m",    # Yellow
    "ERROR": "\033[31m",      # Red
    "CRITICAL": "\033[35m",   # Magenta
    "RESET": "\033[0m"        # Reset color
}
```

## File Structure

```
logs/
├── app.log          # Current log file
├── app.log.1        # First backup
├── app.log.2        # Second backup
└── ...              # Up to 5 backup files
```

## Log Format

### Console Output

```
15:30:45 [INFO] main:demonstrate_logging:25 - This is an info message
15:30:45 [WARNING] main:demonstrate_logging:26 - This is a warning message
```

### File Output

```
2023-12-03 15:30:45 - __main__ - INFO - main:demonstrate_logging:25 - This is an info message
2023-12-03 15:30:45 - __main__ - WARNING - main:demonstrate_logging:26 - This is a warning message
```

## API Reference

### Logger Class

#### Methods

- `debug(message, **kwargs)`: Log a debug message
- `info(message, **kwargs)`: Log an info message
- `warning(message, **kwargs)`: Log a warning message
- `error(message, **kwargs)`: Log an error message
- `critical(message, **kwargs)`: Log a critical message
- `exception(message, **kwargs)`: Log an exception with traceback
- `set_level(level)`: Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `enable_console()` / `disable_console()`: Enable/disable console output
- `enable_file()` / `disable_file()`: Enable/disable file output
- `add_custom_context(context)`: Add persistent context to all subsequent messages
- `clear_custom_context()`: Clear any persistent context

### Convenience Functions

- `get_logger(name=None)`: Get a logger instance
- `debug(message, **kwargs)`: Log a debug message using the default logger
- `info(message, **kwargs)`: Log an info message using the default logger
- `warning(message, **kwargs)`: Log a warning message using the default logger
- `error(message, **kwargs)`: Log an error message using the default logger
- `critical(message, **kwargs)`: Log a critical message using the default logger
- `exception(message, **kwargs)`: Log an exception using the default logger
- `set_level(level)`: Set the log level for the default logger
- `enable_console()` / `disable_console()`: Control console output for the default logger
- `enable_file()` / `disable_file()`: Control file output for the default logger

## Examples

See `main.py` for a complete example of how to use the logging module.
