"""
logger.py
---------
Centralized logging configuration for the TTS application.

Call `setup_logging()` once at application startup (in main.py).
All other modules use the standard `logging.getLogger(__name__)` pattern
and will automatically inherit this configuration.

Log format:
    2024-05-01 14:30:22 | INFO     | app.services.gtts_service | Synthesis complete | bytes=12400
"""

import logging
import sys
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_to_file: bool = False) -> None:
    """
    Configure the root logger for the application.

    Args:
        log_level:    Logging level string — "DEBUG" | "INFO" | "WARNING" | "ERROR".
        log_to_file:  If True, also writes logs to logs/app.log in addition to stdout.
                      Useful for debugging persistent issues in production.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Clean, readable format: timestamp | level | module | message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handlers: list[logging.Handler] = []

    # Always log to stdout (picked up by Streamlit's log pane)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    handlers.append(stream_handler)

    # Optionally write to a rotating log file
    if log_to_file:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True,  # Override any previously set handlers (e.g. from imports)
    )

    # Quieten noisy third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("gtts").setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logging initialised | level=%s | file=%s", log_level, log_to_file
    )


def get_logger(name: str) -> logging.Logger:
    """
    Convenience wrapper around logging.getLogger.

    Prefer using `logging.getLogger(__name__)` directly in each module.
    This helper is provided for callers who prefer explicit imports.

    Args:
        name: Logger name, typically the module's __name__.

    Returns:
        Configured Logger instance.
    """
    return logging.getLogger(name)
