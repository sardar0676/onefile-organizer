"""
Tests for the watcher functionality of onefile.
"""
import os
import shutil
import tempfile
import time
import threading
from pathlib import Path
from typing import Dict, List
import pytest

from onefile.watcher import FileWatcher
from onefile.core import FileOrganizer

# Test data
TEST_FILES = {
    "test1.txt": "Test file 1",
    "test2.jpg": "Fake image",
    "test3.pdf": "PDF content"
}

@pytest.fixture
def test_dir():
    """
    Create a temporary directory with test files.
    """
    temp_dir = tempfile.mkdtemp(prefix="onefile_watcher_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)

class TestFileWatcher:
    ""Test the FileWatcher class."""
    
    def test_watcher_initialization(self, test_dir):
        ""Test that the watcher initializes correctly."""
        watcher = FileWatcher(source_dir=test_dir, interval=10)
        
        assert watcher.source_dir == Path(test_dir).resolve()
        assert watcher.interval == 10
        assert watcher.running is False
        assert watcher.thread is None
    
    def test_watcher_start_stop(self, test_dir):
        ""Test starting and stopping the watcher."""
        watcher = FileWatcher(source_dir=test_dir, interval=1)
        
        # Start the watcher in a separate thread
        watcher.start()
        
        # Check that the watcher is running
        assert watcher.running is True
        assert watcher.thread is not None
        assert watcher.thread.is_alive()
        
        # Wait a moment to ensure the watcher is running
        time.sleep(0.5)
        
        # Stop the watcher
        watcher.stop()
        
        # Check that the watcher is stopped
        assert watcher.running is False
        assert watcher.thread is not None
        assert not watcher.thread.is_alive()
    
    def test_watcher_organize_files(self, test_dir):
        ""Test that the watcher organizes files."""
        # Create test files
        for filename, content in TEST_FILES.items():
            file_path = test_dir / filename
            with open(file_path, 'w') as f:
                f.write(content)
        
        # Create a watcher with a short interval
        watcher = FileWatcher(
            source_dir=test_dir,
            interval=1,
            dry_run=False
        )
        
        # Start the watcher
        watcher.start()
        
        try:
            # Wait for the watcher to process files
            time.sleep(1.5)  # Slightly more than the interval
            
            # Check that files were organized
            expected_folders = {
                "test1.txt": "Documents/Text",
                "test2.jpg": "Images",
                "test3.pdf": "Documents/PDFs"
            }
            
            for filename, expected_folder in expected_folders.items():
                expected_path = test_dir / expected_folder / filename
                assert expected_path.exists(), f"Expected {filename} to be in {expected_folder}"
                
        finally:
            # Always stop the watcher
            watcher.stop()
    
    def test_watcher_interval(self, test_dir):
        ""Test that the watcher respects the interval."""
        # Create a test file
        test_file = test_dir / "test.txt"
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        # Track how many times the organizer runs
        organizer_runs = 0
        
        # Create a custom organizer class to track runs
        class TrackingFileOrganizer(FileOrganizer):
            def organize(self):
                nonlocal organizer_runs
                organizer_runs += 1
                return super().organize()
        
        # Replace the default organizer class
        original_organizer = FileWatcher.OrganizerClass
        FileWatcher.OrganizerClass = TrackingFileOrganizer
        
        try:
            # Create a watcher with a short interval
            watcher = FileWatcher(
                source_dir=test_dir,
                interval=0.5,  # Very short interval for testing
                dry_run=True
            )
            
            # Start the watcher
            watcher.start()
            
            try:
                # Wait for a moment
                time.sleep(1.5)  # Should trigger the organizer 2-3 times
                
                # Check that the organizer ran the expected number of times
                assert 2 <= organizer_runs <= 3, f"Expected 2-3 organizer runs, got {organizer_runs}"
                
            finally:
                # Always stop the watcher
                watcher.stop()
                
        finally:
            # Restore the original organizer class
            FileWatcher.OrganizerClass = original_organizer
    
    def test_watcher_error_handling(self, test_dir, caplog):
        ""Test that the watcher handles errors gracefully."""
        # Create a test file
        test_file = test_dir / "test.txt"
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        # Create a custom organizer that raises an exception
        class FailingFileOrganizer(FileOrganizer):
            def organize(self):
                raise RuntimeError("Test error")
        
        # Replace the default organizer class
        original_organizer = FileWatcher.OrganizerClass
        FileWatcher.OrganizerClass = FailingFileOrganizer
        
        try:
            # Create a watcher with a short interval
            watcher = FileWatcher(
                source_dir=test_dir,
                interval=0.1,  # Very short interval for testing
                dry_run=True
            )
            
            # Clear any existing log captures
            caplog.clear()
            
            # Start the watcher
            watcher.start()
            
            try:
                # Wait for a moment to allow the watcher to run
                time.sleep(0.3)
                
                # Check that the error was logged
                assert any("Error in organizer" in record.message for record in caplog.records), \
                    "Expected error to be logged"
                
            finally:
                # Stop the watcher
                watcher.stop()
                
        finally:
            # Restore the original organizer class
            FileWatcher.OrganizerClass = original_organizer

def test_run_daemon(test_dir, monkeypatch, capsys):
    ""Test the run_daemon function."""
    # Create a test file
    test_file = test_dir / "test.txt"
    with open(test_file, 'w') as f:
        f.write("Test content")
    
    # Track if the daemon was started
    daemon_started = False
    
    # Mock the signal handler
    def mock_signal(signum, handler):
        pass
    
    # Mock the time.sleep to break the loop after a short delay
    def mock_sleep(seconds):
        nonlocal daemon_started
        if daemon_started:
            raise KeyboardInterrupt("Test interrupt")
        daemon_started = True
    
    # Apply the mocks
    monkeypatch.setattr('signal.signal', mock_signal)
    monkeypatch.setattr('time.sleep', mock_sleep)
    
    # Import the run_daemon function after applying mocks
    from onefile.watcher import run_daemon
    
    # Run the daemon with a short interval
    run_daemon(
        source_dir=str(test_dir),
        interval=0.1,
        dry_run=True
    )
    
    # Check that the daemon was started
    assert daemon_started, "Daemon did not start"
    
    # Check the output
    captured = capsys.readouterr()
    assert "Starting daemon for" in captured.out
    assert "Daemon stopped" in captured.out
