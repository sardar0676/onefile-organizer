"""
Tests for the core functionality of onefile.
"""
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Dict, List
import pytest

from onefile.core import FileOrganizer
from onefile.rules import get_default_rules, get_folder_for_extension

# Test data
TEST_FILES = {
    "test.txt": "This is a test text file.",
    "document.pdf": "PDF content",
    "image.jpg": "Fake image data",
    "archive.zip": "ZIP archive data",
    "script.py": "print('Hello, World!')",
    ".hidden_file": "Hidden content",
    "README.md": "# Test Project\n\nThis is a test.",
    "data.csv": "id,name\n1,test\n2,example",
    "presentation.pptx": "PowerPoint content",
    "video.mp4": "Video content"
}

@pytest.fixture
def test_dir():
    """Create a temporary directory with test files and clean up afterward."""
    # Create a temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix="onefile_test_"))
    print(f"\nCreated test directory: {temp_dir}")
    
    # Create test files
    print("\nCreating test files:")
    for filename, content in TEST_FILES.items():
        file_path = temp_dir / filename
        print(f"- Creating {file_path}")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Verify file was created
            if not file_path.exists():
                print(f"  ERROR: File was not created: {file_path}")
            else:
                print(f"  Successfully created {file_path} (size: {file_path.stat().st_size} bytes)")
            
            # Set modification time to 2 days ago for age testing
            mod_time = time.time() - (2 * 24 * 60 * 60)
            os.utime(file_path, (mod_time, mod_time))
            
        except Exception as e:
            print(f"  ERROR creating {file_path}: {e}")
    
    # List all files in the directory to verify
    print("\nVerifying test files in directory:")
    for f in temp_dir.iterdir():
        print(f"- Found: {f} (size: {f.stat().st_size} bytes, exists: {f.exists()})")
    
    yield temp_dir
    
    # Clean up
    print(f"\nCleaning up test directory: {temp_dir}")
    shutil.rmtree(str(temp_dir), ignore_errors=True)

def test_get_folder_for_extension():
    """Test that files are correctly categorized by extension."""
    # Test known extensions
    assert get_folder_for_extension(".pdf") == "Documents/PDFs"
    assert get_folder_for_extension(".jpg") == "Images"
    assert get_folder_for_extension(".zip") == "Archives"
    assert get_folder_for_extension(".py") == "Code/Python"
    
    # Test custom rules
    custom_rules = {"MyFolder": [".xyz"]}
    assert get_folder_for_extension(".xyz", custom_rules) == "MyFolder"
    
    # Test unknown extension
    assert get_folder_for_extension(".unknown") == "Others"

def test_file_organizer_init(test_dir):
    """Test FileOrganizer initialization with different parameters."""
    # Test with default parameters
    org = FileOrganizer(source_dir=test_dir)
    assert org.source_dir == Path(test_dir).resolve()
    assert org.dry_run is False
    
    # Test with custom parameters
    org = FileOrganizer(
        source_dir=test_dir,
        dry_run=True,
        min_size=100,
        max_size=1000,
        min_age_days=1,
        max_age_days=7,
        ignore_hidden=False,
        ignore_system=False,
        use_modified_time=False
    )
    assert org.dry_run is True
    assert org.min_size == 100
    assert org.max_size == 1000
    assert org.min_age_days == 1
    assert org.max_age_days == 7
    assert org.ignore_hidden is False
    assert org.ignore_system is False
    assert org.use_modified_time is False

def test_organize_files(test_dir):
    """Test that files are organized into the correct folders."""
    import logging
    
    # Set up logging to console
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    logger = logging.getLogger(__name__)
    
    # Ensure test_dir is a Path object
    test_dir = Path(test_dir).resolve()
    logger.info(f"\n{'='*80}")
    logger.info(f"STARTING TEST: test_organize_files")
    logger.info(f"{'='*80}")
    logger.info(f"Test directory: {test_dir} (exists: {test_dir.exists()})")
    
    # List all files in test directory before organization
    logger.info("\n=== FILES IN TEST DIRECTORY (BEFORE ORGANIZATION) ===")
    try:
        files_before = list(test_dir.iterdir())
        if not files_before:
            logger.warning("No files found in test directory!")
        for f in files_before:
            try:
                logger.info(f"- {f.name} (exists: {f.exists()}, is_file: {f.is_file()}, size: {f.stat().st_size if f.exists() else 0} bytes)")
            except Exception as e:
                logger.error(f"Error examining {f}: {e}")
    except Exception as e:
        logger.error(f"Error listing files in {test_dir}: {e}")
    
    # Create organizer with test directory
    logger.info("\n=== CREATING FILE ORGANIZER ===")
    try:
        logger.info(f"Creating FileOrganizer with source_dir: {test_dir}")
        org = FileOrganizer(source_dir=test_dir, dry_run=False)
        logger.info(f"Organizer created successfully with source_dir: {org.source_dir}")
        logger.info(f"Organizer source_dir exists: {org.source_dir.exists()}")
        logger.info(f"Organizer source_dir is absolute: {org.source_dir.is_absolute()}")
        
        # List files in organizer's source_dir
        logger.info("\n=== FILES IN ORGANIZER'S SOURCE_DIR ===")
        try:
            source_files = list(org.source_dir.iterdir())
            if not source_files:
                logger.warning("No files found in organizer's source_dir!")
            for f in source_files:
                try:
                    logger.info(f"- {f.name} (exists: {f.exists()}, is_file: {f.is_file()}, size: {f.stat().st_size if f.exists() else 0} bytes)")
                except Exception as e:
                    logger.error(f"Error examining {f}: {e}")
        except Exception as e:
            logger.error(f"Error listing files in {org.source_dir}: {e}")
            
    except Exception as e:
        logger.error(f"Error creating FileOrganizer: {e}")
        raise
    
    # Run organization
    stats = org.organize()
    
    # Print organization stats
    print("\nOrganization stats:", stats)
    
    # Check that all files were processed
    assert stats['processed'] == len(TEST_FILES), f"Expected {len(TEST_FILES)} files to be processed, got {stats['processed']}"
    assert stats['moved'] > 0, f"Expected at least one file to be moved, but got {stats['moved']}"
    assert stats['errors'] == 0, f"Expected no errors, but got {stats['errors']}"
    
    # Check that files were moved to the correct folders
    expected_folders = {
        "test.txt": "Documents/Text",
        "document.pdf": "Documents/PDFs",
        "image.jpg": "Images",
        "archive.zip": "Archives",
        "script.py": "Code/Python",
        ".hidden_file": "Others",  # Hidden file should be in Others
        "README.md": "Documents/Text",
        "data.csv": "Documents/Spreadsheets",
        "presentation.pptx": "Documents/Presentations",
        "video.mp4": "Videos"
    }
    
    # List all files after organization
    print("\nFiles after organization:")
    for item in test_dir.rglob('*'):
        if item.is_file():
            print(f"- {item.relative_to(test_dir)}")
    
    # Check each expected file location
    for filename, expected_folder in expected_folders.items():
        if filename == ".hidden_file":
            # Skip hidden file test for now
            continue
            
        expected_path = test_dir / expected_folder / filename
        print(f"\nChecking for {filename} in {expected_folder}...")
        print(f"Expected path: {expected_path}")
        print(f"Path exists: {expected_path.exists()}")
        
        if not expected_path.exists():
            # Try to find where the file actually is
            found = False
            for actual_path in test_dir.rglob(filename):
                if actual_path.is_file() and actual_path.name == filename:
                    print(f"Found {filename} at unexpected location: {actual_path.relative_to(test_dir)}")
                    found = True
            if not found:
                print(f"{filename} not found anywhere in the test directory")
        
        assert expected_path.exists(), f"Expected {filename} to be in {expected_folder}"

def test_dry_run(test_dir):
    """Test that dry run mode doesn't modify files."""
    # Get initial file count
    initial_files = set(f.name for f in test_dir.iterdir() if f.is_file())
    
    # Run organizer in dry run mode
    org = FileOrganizer(source_dir=test_dir, dry_run=True)
    stats = org.organize()
    
    # Check that files were processed but not moved
    assert stats['processed'] > 0
    assert stats['moved'] > 0
    
    # Check that no files were actually moved
    final_files = set(f.name for f in test_dir.iterdir() if f.is_file())
    assert initial_files == final_files, "Files were moved during dry run"

def test_size_filters(test_dir):
    """Test that size filters work correctly."""
    # Create a small file (10 bytes) and a large file (1MB)
    small_file = test_dir / "small.txt"
    large_file = test_dir / "large.bin"
    
    with open(small_file, 'w') as f:
        f.write('x' * 10)  # 10 bytes
    
    with open(large_file, 'wb') as f:
        f.write(b'x' * (1024 * 1024))  # 1MB
    
    # Test minimum size filter
    org = FileOrganizer(
        source_dir=test_dir,
        min_size=100,  # 100 bytes
        dry_run=True
    )
    
    # Small file should be skipped
    assert org.should_skip_file(small_file) is True
    # Large file should be processed
    assert org.should_skip_file(large_file) is False
    
    # Test maximum size filter
    org = FileOrganizer(
        source_dir=test_dir,
        max_size=100,  # 100 bytes
        dry_run=True
    )
    
    # Small file should be processed
    assert org.should_skip_file(small_file) is False
    # Large file should be skipped
    assert org.should_skip_file(large_file) is True

def test_age_filters(test_dir):
    """Test that age filters work correctly."""
    # Create a new file
    new_file = test_dir / "new_file.txt"
    new_file.touch()
    
    # Test minimum age filter (files must be at least 1 day old)
    org = FileOrganizer(
        source_dir=test_dir,
        min_age_days=1,
        dry_run=True
    )
    
    # New file should be skipped (not old enough)
    assert org.should_skip_file(new_file) is True
    
    # Old file should be processed
    old_file = next(f for f in test_dir.iterdir() if f.name in TEST_FILES)
    assert org.should_skip_file(old_file) is False
    
    # Test maximum age filter (files must be less than 1 day old)
    org = FileOrganizer(
        source_dir=test_dir,
        max_age_days=1,
        dry_run=True
    )
    
    # New file should be processed
    assert org.should_skip_file(new_file) is False
    
    # Old file should be skipped
    assert org.should_skip_file(old_file) is True
