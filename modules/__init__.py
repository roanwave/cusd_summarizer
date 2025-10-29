"""CUSD Email Summarizer - Module Package"""

__version__ = '1.0.0'
__author__ = 'Development Team'

from .cusd_summarizer import CUSDSummarizer
from .config_manager import get_config, Config
from .logger import setup_logging, get_logger

__all__ = [
    'CUSDSummarizer',
    'get_config',
    'Config',
    'setup_logging',
    'get_logger'
]
