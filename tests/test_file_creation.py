"""Test file creation in temporary directory."""
import os
import tempfile
from pathlib import Path

def test_temp_file_creation():
    """Test creating and verifying files in a temporary directory."""
    # Create a temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix="onefile_test_"))
    print(f"\nCreated test directory: {temp_dir}")
    
    # Create some test files
    test_files = {
        "test1.txt": "This is a test file",
        "test2.txt": "Another test file",
        "subdir/test3.txt": "Test file in subdirectory"
    }
    
    # Create files
    print("\nCreating test files:")
    for filename, content in test_files.items():
        file_path = temp_dir / filename
        print(f"- Creating {file_path}")
        
        # Create parent directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  Successfully created {file_path} (size: {file_path.stat().st_size} bytes)")
        except Exception as e:
            print(f"  ERROR creating {file_path}: {e}")
    
    # List all files in the directory
    print("\nListing all files in directory:")
    for root, dirs, files in os.walk(temp_dir):
        for name in files:
            file_path = Path(root) / name
            print(f"- {file_path.relative_to(temp_dir)} (exists: {file_path.exists()}, size: {file_path.stat().st_size} bytes)")
    
    # Clean up
    print(f"\nCleaning up test directory: {temp_dir}")
    for root, dirs, files in os.walk(temp_dir, topdown=False):
        for name in files:
            file_path = Path(root) / name
            try:
                file_path.unlink()
                print(f"- Deleted file: {file_path}")
            except Exception as e:
                print(f"- ERROR deleting {file_path}: {e}")
        for name in dirs:
            dir_path = Path(root) / name
            try:
                dir_path.rmdir()
                print(f"- Removed directory: {dir_path}")
            except Exception as e:
                print(f"- ERROR removing {dir_path}: {e}")
    
    # Verify cleanup
    assert not any(temp_dir.iterdir()), f"Directory {temp_dir} is not empty after cleanup"
    temp_dir.rmdir()
    print(f"Removed directory: {temp_dir}")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_temp_file_creation()
