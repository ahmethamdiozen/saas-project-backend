import logging
import sys
from app.core.config import settings

def setup_logging():
    # Get log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Define log format
    # In production, you might want JSON format, but for now we'll use a clean, structured string format
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "[%(filename)s:%(lineno)d] - %(message)s"
    )
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
        force=True # Override any existing logging config
    )
    
    # Set levels for specific libraries to reduce noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    logger = logging.getLogger("saas_backend")
    logger.info(f"Logging initialized with level: {settings.LOG_LEVEL}")
    
    return logger

# Initialize logger instance
logger = setup_logging()
