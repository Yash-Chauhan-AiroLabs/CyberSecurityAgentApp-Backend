"""
Logger configuration for the application.
"""

import logging
from logging.handlers import RotatingFileHandler


# Define Logger & Logging Strat
def get_logger():
    
    """
    This function returns the logger for the application. It sets a handler that logs to a file, 
    and sets the logging level to INFO. If the logger already has a handler, it does not add another one.

    Returns:
        logger: The logger for the application
    """
    
    logger = logging.getLogger('uvicorn.info')
    logger.setLevel(logging.INFO)
    
    # Setting a handler for logging to a file
    handler = RotatingFileHandler("app.log", maxBytes=2000, backupCount=5)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    if not logger.hasHandlers():
        logger.addHandler(handler)

    return logger

# Global logger instance
logger = get_logger()