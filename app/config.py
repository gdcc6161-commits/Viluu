# app/config.py
import os
from typing import Optional

class BotConfig:
    """Configuration class for bot automation and debugging settings."""
    
    def __init__(self):
        # Timing and automation settings
        self.polling_interval = int(os.getenv('BOT_POLLING_INTERVAL', '15'))  # seconds
        self.retry_delay = int(os.getenv('BOT_RETRY_DELAY', '700'))  # milliseconds  
        self.follow_up_hours = int(os.getenv('BOT_FOLLOW_UP_HOURS', '4'))  # hours
        self.page_load_timeout = int(os.getenv('BOT_PAGE_LOAD_TIMEOUT', '20000'))  # milliseconds
        
        # Debug and automation levels
        self.debug_level = int(os.getenv('BOT_DEBUG_LEVEL', '1'))  # 0=minimal, 1=normal, 2=verbose
        self.auto_skip_manual = os.getenv('BOT_AUTO_SKIP_MANUAL', 'false').lower() == 'true'
        self.auto_continue = os.getenv('BOT_AUTO_CONTINUE', 'false').lower() == 'true'
        
        # Status reporting
        self.show_status_updates = self.debug_level >= 1
        self.show_detailed_logs = self.debug_level >= 2
    
    def log_debug(self, message: str, level: int = 1):
        """Log debug message if debug level is sufficient."""
        if self.debug_level >= level:
            print(f"🔧 DEBUG: {message}")
    
    def log_status(self, message: str):
        """Log status message if status updates are enabled.""" 
        if self.show_status_updates:
            print(f"ℹ️  {message}")
    
    def log_verbose(self, message: str):
        """Log verbose message if detailed logging is enabled."""
        if self.show_detailed_logs:
            print(f"📝 VERBOSE: {message}")

# Global config instance
config = BotConfig()