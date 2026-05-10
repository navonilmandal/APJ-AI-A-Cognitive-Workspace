import logging
import sys
from backend.core.config import settings

def setup_logger(name: str):
    """Configures a standardized logger for the project."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Rotating File handler
        from logging.handlers import RotatingFileHandler
        log_file = settings.PROJECT_ROOT / "app.log"
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=5 * 1024 * 1024, # 5MB
            backupCount=3
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger
