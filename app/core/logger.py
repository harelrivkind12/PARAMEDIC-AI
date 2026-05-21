import logging
from app.core.config import get_settings

def get_logger(name: str) -> logging.Logger:
    """
    Helper function to get a configured logger with the given name.
    Log level dynamically adjusts based on the app's debug setting.
    """
   
    logger = logging.getLogger(name)
    
    # Prevent adding multiple handlers if the logger already exists
    if not logger.handlers:
        settings = get_settings()
        
        # Standard output (terminal/console)
        handler = logging.StreamHandler()
        
        # The format
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Dynamically set level based on the debug flag
        log_level = logging.DEBUG if settings.debug else logging.INFO
        logger.setLevel(log_level)
        
    return logger