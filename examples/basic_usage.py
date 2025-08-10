"""
Basic usage example for the onefile library.

This script demonstrates how to use the onefile library to organize files
programmatically.
"""
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import onefile
sys.path.insert(0, str(Path(__file__).parent.parent))

from onefile.core import FileOrganizer
from onefile.rules import get_default_rules

def main():
    # Configuration
    source_dir = os.path.expanduser("~/Downloads")  # Organize the Downloads folder
    dry_run = True  # Set to False to actually move files
    
    # Custom rules (optional)
    custom_rules = get_default_rules()
    custom_rules["MyCustomFolder"] = [".myext", ".another_ext"]
    
    print(f"Organizing files in: {source_dir}")
    if dry_run:
        print("DRY RUN MODE: No files will be moved")
    
    # Create and configure the organizer
    organizer = FileOrganizer(
        source_dir=source_dir,
        dry_run=dry_run,
        custom_rules=custom_rules,
        min_size="10K",  # Skip files smaller than 10KB
        max_size="100M",  # Skip files larger than 100MB
        min_age_days=1,   # Only process files older than 1 day
        ignore_hidden=True,
        ignore_system=True,
    )
    
    # Run the organizer
    stats = organizer.organize()
    
    # Print results
    print("\nOrganization complete!")
    print(f"Processed: {stats['processed']} files")
    print(f"Moved: {stats['moved']} files")
    print(f"Skipped: {stats['skipped']} files")
    print(f"Errors: {stats['errors']} files")
    print(f"Time taken: {stats['elapsed_seconds']:.2f} seconds")

if __name__ == "__main__":
    main()
