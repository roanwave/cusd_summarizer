"""Logging configuration for CUSD Email Summarizer."""
import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_file: str = None,
    log_level: str = "INFO",
    console_output: bool = True
) -> logging.Logger:
    """Configure logging for the application.
    
    Args:
        log_file: Path to log file. If None, logs to console only.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        console_output: Whether to output logs to console.
        
    Returns:
        Configured logger instance.
    """
    # Create logger
    logger = logging.getLogger('cusd_summarizer')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get logger instance.
    
    Args:
        name: Logger name. If None, returns root cusd_summarizer logger.
        
    Returns:
        Logger instance.
    """
    if name:
        return logging.getLogger(f'cusd_summarizer.{name}')
    return logging.getLogger('cusd_summarizer')
