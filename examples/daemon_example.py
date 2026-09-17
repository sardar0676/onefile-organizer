"""
Daemon usage example for the onefile library.

This script demonstrates how to use the onefile library to create a custom
daemon that watches a directory for changes and organizes files automatically.
"""
import os
import sys
import signal
import logging
import argparse
from pathlib import Path
from typing import Dict, Any

# Add the parent directory to the path so we can import onefile
sys.path.insert(0, str(Path(__file__).parent.parent))

from onefile.watcher import FileWatcher
from onefile.rules import get_default_rules

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('onefile_daemon.log')
    ]
)
logger = logging.getLogger(__name__)

class CustomFileWatcher:
    """Custom file watcher with additional features."""
    
    def __init__(self, source_dir: str, interval: int = 60):
        """Initialize the custom file watcher."""
        self.source_dir = Path(source_dir).expanduser().resolve()
        self.interval = interval
        self.running = False
        self.watcher = None
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Initialized watcher for: {self.source_dir} (interval: {interval}s)")
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals."""
        logger.info(f"Received signal {signal.Signals(signum).name}, shutting down...")
        self.stop()
    
    def on_organize_complete(self, stats: Dict[str, Any]) -> None:
        """Callback when organization is complete."""
        logger.info(
            f"Organization complete - "
            f"Processed: {stats.get('processed', 0)}, "
            f"Moved: {stats.get('moved', 0)}, "
            f"Errors: {stats.get('errors', 0)}"
        )
    
    def start(self) -> None:
        """Start the watcher."""
        if self.running:
            logger.warning("Watcher is already running")
            return
        
        # Custom rules
        custom_rules = get_default_rules()
        
        # Add custom rules for specific file patterns
        custom_rules["Ebooks"] = [
            ".epub", ".mobi", ".azw3", ".pdf", ".djvu"
        ]
        
        # Add custom rules for development files
        custom_rules["Code/Python"] = [
            ".py", ".pyc", ".pyo", ".pyd", ".pyw", ".pyz"
        ]
        
        # Configure the watcher
        self.watcher = FileWatcher(
            source_dir=str(self.source_dir),
            interval=self.interval,
            custom_rules=custom_rules,
            min_size="1K",  # Skip files smaller than 1KB
            max_size="1G",  # Skip files larger than 1GB
            min_age_days=0,  # Process files of any age
            ignore_hidden=True,
            ignore_system=True,
        )
        
        logger.info("Starting watcher...")
        self.running = True
        self.watcher.start()
        
        try:
            # Keep the main thread alive
            while self.running:
                # You could add additional monitoring/health checks here
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Watcher stopped by user")
        except Exception as e:
            logger.error(f"Error in watcher: {e}", exc_info=True)
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the watcher."""
        if not self.running:
            return
            
        logger.info("Stopping watcher...")
        self.running = False
        
        if self.watcher:
            self.watcher.stop()
        
        logger.info("Watcher stopped")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Custom file organization daemon')
    parser.add_argument(
        '--src',
        type=str,
        default="~/Downloads",
        help='Source directory to watch (default: ~/Downloads)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in seconds (default: 60)'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Set log level
    logging.getLogger().setLevel(args.log_level)
    
    # Create and start the watcher
    watcher = CustomFileWatcher(
        source_dir=args.src,
        interval=args.interval
    )
    
    try:
        watcher.start()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
