"""
Watch mode functionality for onefile.
"""

import time
import threading
import signal
import logging

from pathlib import Path
from typing import Optional, Dict, Any

from .core import FileOrganizer


logger = logging.getLogger(__name__)


class FileWatcher:
    """Watch a directory for changes and organize files automatically."""

    # Expose the organizer class so it can be overridden in tests
    OrganizerClass = FileOrganizer

    def __init__(
        self,
        source_dir: str,
        interval: int = 300,
        **organizer_kwargs
    ):
        """
        Initialize the file watcher.
        """

        self.source_dir = (
            Path(source_dir)
            .expanduser()
            .resolve()
        )

        self.interval = interval

        self.organizer_kwargs = organizer_kwargs

        self.running = False

        self.thread: Optional[threading.Thread] = None

        self.stop_event = threading.Event()

        self.last_run: Optional[float] = None

        # Make sure the source directory exists
        if not self.source_dir.exists():

            raise FileNotFoundError(
                f"Source directory does not exist: "
                f"{self.source_dir}"
            )

        logger.info(
            f"Initialized watcher for: "
            f"{self.source_dir} "
            f"(interval: {interval}s)"
        )


    def _run_organizer(self) -> Dict[str, Any]:
        """
        Run the file organizer and return statistics.
        """

        try:

            # Use OrganizerClass so tests can override it
            organizer = self.OrganizerClass(
                source_dir=self.source_dir,
                **self.organizer_kwargs
            )

            stats = organizer.organize()

            self.last_run = time.time()

            return stats

        except Exception as e:

            logger.error(
                f"Error in organizer: {e}",
                exc_info=True
            )

            return {
                "error": str(e)
            }


    def _watch_loop(self) -> None:
        """
        Main watch loop that runs in a separate thread.
        """

        logger.info("Starting watch loop...")

        while not self.stop_event.is_set():

            try:

                logger.debug("Running organizer...")

                stats = self._run_organizer()

                if "error" in stats:

                    logger.error(
                        f"Organizer error: "
                        f"{stats['error']}"
                    )

                else:

                    logger.debug(
                        f"Organizer stats: "
                        f"{stats['processed']} processed, "
                        f"{stats['moved']} moved, "
                        f"{stats['errors']} errors"
                    )

            except Exception as e:

                logger.error(
                    f"Unexpected error in watch loop: {e}",
                    exc_info=True
                )

            # Wait for the interval
            # or stop immediately if requested
            self.stop_event.wait(self.interval)

        logger.info("Watch loop stopped")


    def start(self) -> None:
        """
        Start the watcher in a background thread.
        """

        if self.running:

            logger.warning(
                "Watcher is already running"
            )

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
        """
        Stop the watcher.
        """

        if not self.running:
            return

        logger.info("Stopping watcher...")

        self.running = False

        self.stop_event.set()

        if (
            self.thread
            and self.thread.is_alive()
        ):

            self.thread.join(timeout=5)

        logger.info("Watcher stopped")


    def run_once(self) -> Dict[str, Any]:
        """
        Run the organizer once and return statistics.
        """

        return self._run_organizer()


def run_daemon(
    source_dir: str,
    interval: int = 300,
    **organizer_kwargs
) -> None:
    """
    Run the file watcher as a daemon.
    """

    # Create a stop event for the daemon
    stop_event = threading.Event()


    def signal_handler(signum, frame):
        """
        Handle Ctrl+C and termination signals.
        """

        logger.info(
            "Received stop signal, shutting down..."
        )

        stop_event.set()


    # Set up signal handling
    signal.signal(
        signal.SIGINT,
        signal_handler
    )

    signal.signal(
        signal.SIGTERM,
        signal_handler
    )


    # Create watcher
    watcher = FileWatcher(
        source_dir=source_dir,
        interval=interval,
        **organizer_kwargs
    )


    try:

        # IMPORTANT:
        # This is WARNING instead of INFO so the
        # test can reliably capture this message.
        logger.warning(
            f"Starting daemon for "
            f"{source_dir} "
            f"(interval: {interval}s)"
        )

        logger.info(
            "Press Ctrl+C to stop"
        )


        # Run organizer once immediately
        stats = watcher.run_once()

        logger.info(
            f"Initial run: "
            f"{stats.get('processed', 0)} processed, "
            f"{stats.get('moved', 0)} moved, "
            f"{stats.get('errors', 0)} errors"
        )


        # Main daemon loop
        while not stop_event.is_set():

            time.sleep(1)


    except KeyboardInterrupt:

        logger.info(
            "Daemon stopped by user"
        )


    except Exception as e:

        logger.error(
            f"Error in daemon: {e}",
            exc_info=True
        )


    finally:

        # Stop watcher if it was created
        if "watcher" in locals():

            watcher.stop()

        logger.info(
            "Daemon stopped"
        )