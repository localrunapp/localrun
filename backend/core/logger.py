import logging
import sys
from typing import Optional

# Hot reload test - modified at 2025-11-20 12:18


def setup_logger(
    name: str,
    level: Optional[int] = None,
    log_format: str = "[%(asctime)s - %(levelname)s] %(message)s",
) -> logging.Logger:
    """
    Setup and configure a logger with stdout handler and trace_id support.

    Args:
        name: Logger name (usually __name__)
        level: Log level (defaults to INFO)
        log_format: Log format string

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Default to INFO level
    if level is None:
        level = logging.INFO

    logger.setLevel(level)

    # Create stdout handler with standard formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False

    return logger


def log(
    severity: str,
    module: str,
    message: str,
    metadata: Optional[dict] = None,
    store: bool = False,
    console: bool = True,
) -> Optional[str]:
    """
    Unified logging function with flexible destination control.

    Args:
        severity: Log severity level (info, warning, error, debug)
        module: Module/category of the log
        message: Log message
        metadata: Optional metadata dict (can include tags, trace, server_id, etc.)
        store: If True, saves to database (default: False)
        console: If True, outputs to console (default: True)

    Returns:
        Log ID if store=True, None otherwise

    Examples:
        # Debug only (console only)
        log("debug", "auth", "Processing login")

        # Metrics (database only)
        log("info", "metrics", "API request", 
            metadata={"tags": ["api"], "duration_ms": 45},
            store=True, console=False)

        # Important events (both)
        log("error", "services", "Tunnel failed",
            metadata={"tags": ["tunnel"], "trace": "req_123"},
            store=True, console=True)
    """
    if metadata is None:
        metadata = {}

    log_id = None

    # Store in database if requested
    if store:
        # Import here to avoid circular dependency
        from app.repositories.log_repository import log_manager

        # Extract special fields from metadata
        server_id = metadata.get("server_id")
        server_name = metadata.get("server_name")

        log_id = log_manager.log(
            category=module,
            level=severity,
            message=message,
            server_id=server_id,
            server_name=server_name,
            metadata=metadata,
        )

    # Output to console if requested
    if console:
        logger = logging.getLogger(module)

        # Format message with relevant metadata
        log_msg = message

        # Add tags if present
        if "tags" in metadata and metadata["tags"]:
            tags_str = ", ".join(metadata["tags"])
            log_msg += f" [tags: {tags_str}]"

        # Add trace if present
        if "trace" in metadata:
            log_msg += f" [trace: {metadata['trace']}]"

        # Log according to severity
        severity_lower = severity.lower()
        if severity_lower == "debug":
            logger.debug(log_msg)
        elif severity_lower == "info":
            logger.info(log_msg)
        elif severity_lower == "warning":
            logger.warning(log_msg)
        elif severity_lower == "error":
            logger.error(log_msg)
        else:
            logger.info(log_msg)

    return log_id
