import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logger(name="SaveLinks", log_file="app.log", level=logging.INFO):
    """Configures and returns a logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # dedicated format for logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # File Handler
    file_handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console Handler (only for warnings/errors to keep UI clean)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# Global logger instance to be used across the app
logger = setup_logger()
