import os

# Get the project root directory (parent of src)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

INPUT_DIRECTORY = os.path.join(PROJECT_ROOT, "data", "input")

MODEL_GENAI = ""
MODEL_REQUESTY = ""
REQUESTY_BASE_URL = os.environ.get("REQUESTY_BASE_URL", "")
GENAI_API_KEY = os.environ.get("GENAI_API_KEY", "")

# Available AI models for GenAI processor (Google's GenAI)
GENAI_MODELS = {
    "1": "gemini-3-pro-preview",
    "2": "gemini-flash-latest",
}

# Available AI models for Requesty processor
REQUESTY_MODELS = {
    "1": "vertex/gemini-3-pro-preview",
    "2": "azure/gpt-5.1",
    "3": "bedrock/claude-opus-4-5",
    "4": "bedrock/claude-sonnet-4@eu-west-1",
    "5": "coding/gemini-2.5-flash@europe-west1",
    "6": "google/gemini-2.5-pro",
    "7": "google/gemini-3-pro-preview",
    "8": "vertex/gemini-2.5-flash@europe-west1",
}

# Legacy alias for backward compatibility
AVAILABLE_MODELS = REQUESTY_MODELS


# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {"format": "%(levelname)s - %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": os.path.join(PROJECT_ROOT, "data", "logs", "app.log"),
            "maxBytes": 10485760,  # 10 MB
            "backupCount": 5,
            "encoding": "utf8",
        },
    },
    "loggers": {
        "": {"level": "DEBUG", "handlers": ["console", "file"], "propagate": False}
    },
}

# Log file paths
LOG_FILE_PATH = os.path.join(PROJECT_ROOT, "data", "logs", "app.log")
LOG_DIR = os.path.join(PROJECT_ROOT, "data", "logs")

# Default log level
DEFAULT_LOG_LEVEL = "DEBUG"

# Log colors for terminal output
LOG_COLORS = {
    "DEBUG": "\033[36m",  # Cyan
    "INFO": "\033[32m",  # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
    "CRITICAL": "\033[35m",  # Magenta
    "RESET": "\033[0m",  # Reset color
}
