"""Logger setup for DocVault"""

import logging
import logging.handlers
import os

try:
    from ..config import LOG_DIR, LOG_FORMAT, LOG_LEVEL
except ImportError:
    from config import LOG_DIR, LOG_FORMAT, LOG_LEVEL

def setup_logger(name: str) -> logging.Logger:
    """
    Setup logger with file and console handlers.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Only add handlers if not already present
    if logger.hasHandlers():
        return logger
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    log_file = os.path.join(LOG_DIR, f"{name}.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
