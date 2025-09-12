"""
Logging module for VILUU bot.
Provides centralized logging functionality with automatic log rotation.
"""
import os
import logging
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional


# Create logs directory if it doesn't exist
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)


class VILUULogger:
    """Centralized logger for VILUU bot operations."""
    
    def __init__(self):
        self.logger = logging.getLogger('VILUU_BOT')
        self.logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers if logger already configured
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup file and console handlers for logging."""
        
        # File handler with rotation (max 5MB, keep 5 files)
        log_file = os.path.join(LOG_DIR, 'viluu_bot.log')
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)
    
    def error(self, message: str, exception: Optional[Exception] = None):
        """Log error message with optional exception details."""
        if exception:
            self.logger.error(f"{message} - {str(exception)}")
        else:
            self.logger.error(message)
    
    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
    
    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)
    
    def success(self, message: str):
        """Log success message (as info with success indicator)."""
        self.logger.info(f"✅ {message}")
    
    def failure(self, message: str):
        """Log failure message (as error with failure indicator)."""
        self.logger.error(f"❌ {message}")


# Global logger instance
logger = VILUULogger()


def log_startup():
    """Log application startup."""
    logger.info("=" * 50)
    logger.info("VILUU Bot gestartet")
    logger.info(f"Zeitstempel: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)


def log_shutdown():
    """Log application shutdown."""
    logger.info("VILUU Bot beendet")
    logger.info("=" * 50)


def log_ai_request(provider: str, success: bool, response_time: Optional[float] = None):
    """Log AI request details."""
    if success:
        time_str = f" ({response_time:.2f}s)" if response_time else ""
        logger.success(f"KI-Anfrage erfolgreich - {provider.upper()}{time_str}")
    else:
        logger.failure(f"KI-Anfrage fehlgeschlagen - {provider.upper()}")


def log_message_processing(direction: str, message_count: int):
    """Log message processing activities."""
    logger.info(f"Nachrichten verarbeitet: {message_count} ({direction})")


def log_error_with_retry(error_msg: str, attempt: int, max_attempts: int):
    """Log error with retry information."""
    logger.warning(f"Fehler (Versuch {attempt}/{max_attempts}): {error_msg}")


def log_browser_action(action: str, success: bool = True):
    """Log browser-related actions."""
    if success:
        logger.info(f"Browser-Aktion: {action}")
    else:
        logger.error(f"Browser-Aktion fehlgeschlagen: {action}")