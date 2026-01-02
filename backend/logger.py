"""
Centralized Logging System for Mein Business
Provides consistent logging across all modules
"""

import logging
import os
from datetime import datetime
from pathlib import Path

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Create log filename with current date
log_filename = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()  # Also print to console
    ]
)

def get_logger(name):
    """
    Get a logger instance for a specific module
    
    Usage:
        from logger import get_logger
        logger = get_logger(__name__)
        logger.info("Message here")
    """
    return logging.getLogger(name)

# Default logger for quick usage
logger = get_logger('mein_business')

if __name__ == '__main__':
    # Test logging
    logger.info("✅ Logging system initialized")
    logger.warning("⚠️ This is a warning")
    logger.error("❌ This is an error")
    print(f"\n📁 Log file created: {log_filename}")
