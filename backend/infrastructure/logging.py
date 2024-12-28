"""Logging configuration."""
import logging
import sys
from typing import Any

import structlog


def get_logger(name: str = None) -> Any:
    """Get a structured logger instance.
    
    Args:
        name: Optional logger name
        
    Returns:
        structlog.BoundLogger: Configured logger instance
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True
    )

    return structlog.get_logger(name) 