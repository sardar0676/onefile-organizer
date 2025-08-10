"""
Watch mode functionality for onefile.
"""
import time
import threading
import signal
import logging
from pathlib import Path
from typing import Optional, Callable, Dict, Any

from .core import FileOrganizer

logger = logging.getLogger(__name__)

class FileWatcher:
    """Watch a directory for changes and organize files automatically."""
    
    def __init__(
        self,
        source_dir: str,
        interval: int = 300,
        **organizer_kwargs
    ):
        """
        Initialize the file watcher.
        
        Args:
            source_dir: Directory to watch
            interval: Time between checks in seconds
            **organizer_kwargs: Additional arguments to pass to FileOrganizer
        """
        self.source_dir = Path(source_dir).expanduser().resolve()
        self.interval = interval
        self.organizer_kwargs = organizer_kwargs
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.last_run: Optional[float] = None
        
        # Ensure source directory exists
        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory does not exist: {self.source_dir}")
        
        logger.info(f"Initialized watcher for: {self.source_dir} (interval: {interval}s)")
    
    def _run_organizer(self) -> Dict[str, Any]:
        """Run the file organizer and return stats."""
        try:
            organizer = FileOrganizer(
                source_dir=self.source_dir,
                **self.organizer_kwargs
            )
            stats = organizer.organize()
            self.last_run = time.time()
            return stats
        except Exception as e:
            logger.error(f"Error in organizer: {e}", exc_info=True)
            return {'error': str(e)}
    
    def _watch_loop(self) -> None:
        """Main watch loop that runs in a separate thread."""
        logger.info("Starting watch loop...")
        
        while not self.stop_event.is_set():
            try:
                logger.debug("Running organizer...")
                stats = self._run_organizer()
                
                if 'error' in stats:
                    logger.error(f"Organizer error: {stats['error']}")
                else:
                    logger.debug(
                        f"Organizer stats: {stats['processed']} processed, "
                        f"{stats['moved']} moved, {stats['errors']} errors"
                    )
                
            except Exception as e:
                logger.error(f"Unexpected error in watch loop: {e}", exc_info=True)
            
            # Wait for the interval or until stopped
            self.stop_event.wait(self.interval)
        
        logger.info("Watch loop stopped")
    
    def start(self) -> None:
        """Start the watcher in a background thread."""
        if self.running:
            logger.warning("Watcher is already running")
            return
        
        self.running = True
        self.stop_event.clear()
        
        # Start the watch loop in a daemon thread
        self.thread = threading.Thread(
            target=self._watch_loop,
            daemon=True,
            name="OneFileWatcher"
        )
        self.thread.start()
        
        logger.info("Watcher started")
    
    def stop(self) -> None:
        """Stop the watcher."""
        if not self.running:
            return
        
        logger.info("Stopping watcher...")
        self.running = False
        self.stop_event.set()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
            
        logger.info("Watcher stopped")
    
    def run_once(self) -> Dict[str, Any]:
        """Run the organizer once and return stats."""
        return self._run_organizer()


def run_daemon(
    source_dir: str,
    interval: int = 300,
    **organizer_kwargs
) -> None:
    """
    Run the file watcher as a daemon.
    
    This function will run indefinitely until interrupted with Ctrl+C.
    
    Args:
        source_dir: Directory to watch
        interval: Time between checks in seconds
        **organizer_kwargs: Additional arguments to pass to FileOrganizer
    """
    # Set up signal handling
    stop_event = threading.Event()
    
    def signal_handler(signum, frame):
        logger.info("Received stop signal, shutting down...")
        stop_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start the watcher
    watcher = FileWatcher(
        source_dir=source_dir,
        interval=interval,
        **organizer_kwargs
    )
    
    try:
        # Run the watcher in the main thread
        logger.info(f"Starting daemon for {source_dir} (interval: {interval}s)")
        logger.info("Press Ctrl+C to stop")
        
        # Initial run
        stats = watcher.run_once()
        logger.info(
            f"Initial run: {stats.get('processed', 0)} processed, "
            f"{stats.get('moved', 0)} moved, {stats.get('errors', 0)} errors"
        )
        
        # Main loop
        while not stop_event.is_set():
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Daemon stopped by user")
    except Exception as e:
        logger.error(f"Error in daemon: {e}", exc_info=True)
    finally:
        # Clean up
        if 'watcher' in locals():
            watcher.stop()
        
        logger.info("Daemon stopped")
