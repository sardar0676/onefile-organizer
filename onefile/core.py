"""
Core functionality for the onefile organizer.

This module provides the main file organization logic, including file operations,
filtering, and organization rules application.
"""
import os
import shutil
import logging
import time
import hashlib
import filecmp
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Callable, Any
from datetime import datetime, timedelta
import mimetypes

try:
    import magic  # python-magic-bin on Windows, python-magic on other platforms
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    logger.warning("python-magic not found. Using basic MIME type detection.")

from . import rules

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('onefile.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize MIME type detection
if HAS_MAGIC:
    mime = magic.Magic(mime=True)
else:
    # Fallback to built-in mimetypes if magic is not available
    mime = None
    # Ensure mimetypes has our custom types
    mimetypes.add_type('application/x-rar-compressed', '.cbr')
    mimetypes.add_type('application/x-cbr', '.cbr')
    mimetypes.add_type('application/epub+zip', '.epub')
    mimetypes.add_type('application/x-mobipocket-ebook', '.mobi')
    mimetypes.add_type('application/x-msdownload', '.exe')
    mimetypes.add_type('application/x-msi', '.msi')
    mimetypes.add_type('application/x-iso9660-image', '.iso')

class FileOrganizer:
    """
    Main class for organizing files with advanced features.
    
    This class provides functionality to organize files based on various criteria
    including file type, size, age, and custom rules. It also includes features
    for duplicate detection and conflict resolution.
    """
    
    def __init__(
        self,
        source_dir: Union[str, Path],
        dry_run: bool = False,
        custom_rules: Optional[Dict[str, List[str]]] = None,
        min_size: Optional[Union[int, str]] = None,  # in bytes or with suffix (e.g., '10M')
        max_size: Optional[Union[int, str]] = None,  # in bytes or with suffix
        min_age_days: Optional[int] = None,
        max_age_days: Optional[int] = None,
        ignore_hidden: bool = True,
        ignore_system: bool = True,
        use_modified_time: bool = True,
        detect_duplicates: bool = True,
        duplicate_action: str = 'rename',  # 'rename', 'skip', 'overwrite', 'delete'
        conflict_resolution: str = 'rename',  # 'rename', 'overwrite', 'skip'
        max_filename_length: int = 255,  # Maximum filename length (0 for no limit)
        preserve_original: bool = False,  # Keep original files (copy instead of move)
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,  # Callback for progress updates
    ):
        """Initialize the file organizer with advanced options.
        
        Args:
            source_dir: Directory to organize
            dry_run: If True, simulate file operations without making changes
            custom_rules: Custom file organization rules
            min_size: Minimum file size (e.g., '1K', '10M', '1G' or bytes)
            max_size: Maximum file size
            min_age_days: Minimum file age in days
            max_age_days: Maximum file age in days
            ignore_hidden: Skip hidden files/directories
            ignore_system: Skip system files (Windows only)
            use_modified_time: Use modification time instead of creation time for age checks
            detect_duplicates: Enable duplicate file detection
            duplicate_action: Action for duplicate files ('rename', 'skip', 'overwrite', 'delete')
            conflict_resolution: How to handle filename conflicts ('rename', 'overwrite', 'skip')
            max_filename_length: Maximum allowed filename length (0 for no limit)
            preserve_original: Keep original files (copy instead of move)
            callback: Callback function for progress updates
        """
        self.source_dir = Path(source_dir).expanduser().resolve()
        self.dry_run = dry_run
        self.custom_rules = custom_rules or {}
        self.min_size = self._parse_size(min_size) if isinstance(min_size, str) else min_size
        self.max_size = self._parse_size(max_size) if isinstance(max_size, str) else max_size
        self.min_age_days = min_age_days
        self.max_age_days = max_age_days
        self.ignore_hidden = ignore_hidden
        self.ignore_system = ignore_system
        self.use_modified_time = use_modified_time
        self.detect_duplicates = detect_duplicates
        self.duplicate_action = duplicate_action.lower()
        self.conflict_resolution = conflict_resolution.lower()
        self.max_filename_length = max_filename_length
        self.preserve_original = preserve_original
        self.callback = callback
        
        # Stats and tracking
        self.files_processed = 0
        self.files_moved = 0
        self.files_copied = 0
        self.files_skipped = 0
        self.duplicates_found = 0
        self.errors = 0
        self.duplicate_hashes: Dict[str, List[Path]] = {}
        
        # Ensure source directory exists
        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory does not exist: {self.source_dir}")
        
        # Validate actions
        if self.duplicate_action not in ('rename', 'skip', 'overwrite', 'delete'):
            raise ValueError(f"Invalid duplicate_action: {self.duplicate_action}")
        if self.conflict_resolution not in ('rename', 'overwrite', 'skip'):
            raise ValueError(f"Invalid conflict_resolution: {self.conflict_resolution}")
        
        logger.info(f"Initialized organizer for: {self.source_dir}")
        if self.dry_run:
            logger.info("DRY RUN MODE: No files will be moved")
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string with units (e.g., 1K, 2M, 3G) to bytes."""
        if not size_str:
            return 0
            
        size_str = size_str.upper().strip()
        if size_str.endswith('K'):
            return int(size_str[:-1]) * 1024
        elif size_str.endswith('M'):
            return int(size_str[:-1]) * 1024 * 1024
        elif size_str.endswith('G'):
            return int(size_str[:-1]) * 1024 * 1024 * 1024
        else:
            # Assume bytes if no unit specified
            return int(size_str)
    
    def _get_file_hash(self, file_path: Path, block_size: int = 65536) -> str:
        """Calculate MD5 hash of a file."""
        hasher = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                buf = f.read(block_size)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = f.read(block_size)
            return hasher.hexdigest()
        except (IOError, OSError) as e:
            logger.error(f"Error reading file for hashing: {file_path} - {e}")
            return ""
    
    def _is_duplicate(self, file_path: Path) -> bool:
        """Check if a file is a duplicate based on its content hash."""
        if not self.detect_duplicates:
            return False
            
        file_hash = self._get_file_hash(file_path)
        if not file_hash:
            return False
            
        if file_hash in self.duplicate_hashes:
            # Add this file to the duplicates list
            self.duplicate_hashes[file_hash].append(file_path)
            self.duplicates_found += 1
            logger.info(f"Duplicate found: {file_path}")
            return True
        else:
            # First time seeing this hash
            self.duplicate_hashes[file_hash] = [file_path]
            return False
    
    def _handle_duplicate(self, file_path: Path) -> bool:
        """Handle a duplicate file based on the duplicate_action setting."""
        if not self.detect_duplicates:
            return False
            
        file_hash = self._get_file_hash(file_path)
        if not file_hash or file_hash not in self.duplicate_hashes:
            return False
            
        original_file = self.duplicate_hashes[file_hash][0]
        
        if self.duplicate_action == 'skip':
            logger.info(f"Skipping duplicate: {file_path}")
            return True
            
        elif self.duplicate_action == 'delete':
            logger.info(f"Deleting duplicate: {file_path}")
            if not self.dry_run:
                try:
                    file_path.unlink()
                    return True
                except Exception as e:
                    logger.error(f"Error deleting duplicate file {file_path}: {e}")
                    return False
                    
        elif self.duplicate_action == 'overwrite':
            # This will be handled in the file move/copy operation
            return False
            
        return False
    
    def _get_safe_filename(self, file_path: Path, dest_dir: Path) -> Path:
        """Generate a safe filename that doesn't conflict with existing files."""
        if not file_path.exists():
            return file_path
            
        # If overwrite is enabled and the file exists, return the same path
        if self.conflict_resolution == 'overwrite':
            return file_path
            
        # If skip is enabled and the file exists, return None to indicate skipping
        if self.conflict_resolution == 'skip':
            return None
            
        # Default: rename the file
        counter = 1
        name_parts = file_path.stem, file_path.suffix
        
        while True:
            new_name = f"{name_parts[0]}_{counter}{name_parts[1]}"
            new_path = dest_dir / new_name
            
            # Check if the new path is too long
            if self.max_filename_length > 0 and len(new_name) > self.max_filename_length:
                # Truncate the filename while keeping the extension
                max_stem_length = self.max_filename_length - len(name_parts[1]) - len(str(counter)) - 1
                if max_stem_length < 1:
                    max_stem_length = 1
                truncated_stem = name_parts[0][:max_stem_length]
                new_name = f"{truncated_stem}_{counter}{name_parts[1]}"
                new_path = dest_dir / new_name
            
            if not new_path.exists():
                return new_path
                
            counter += 1
    
    def _move_file(self, src: Path, dest: Path) -> bool:
        """Move or copy a file with proper error handling."""
        try:
            if self.preserve_original:
                if not self.dry_run:
                    shutil.copy2(src, dest)
                logger.debug(f"Copied: {src} -> {dest}")
                self.files_copied += 1
            else:
                if not self.dry_run:
                    shutil.move(str(src), str(dest))
                logger.debug(f"Moved: {src} -> {dest}")
                self.files_moved += 1
            return True
            
        except (OSError, IOError) as e:
            logger.error(f"Error moving file {src} to {dest}: {e}")
            self.errors += 1
            return False
    
    def _update_progress(self, current: int, total: int, status: str = '') -> None:
        """Update progress if a callback is provided."""
        if self.callback:
            progress = {
                'current': current,
                'total': total,
                'status': status,
                'moved': self.files_moved,
                'copied': self.files_copied,
                'skipped': self.files_skipped,
                'duplicates': self.duplicates_found,
                'errors': self.errors
            }
            try:
                self.callback(progress)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
    
    def should_skip_file(self, file_path: Path) -> bool:
        """Determine if a file should be skipped based on filters.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            bool: True if the file should be skipped, False otherwise
        """
        try:
            # Skip directories and non-existent files
            if not file_path.is_file():
                return True
                
            # Skip hidden files if configured
            if self.ignore_hidden and file_path.name.startswith('.'):
                logger.debug(f"Skipping hidden file: {file_path}")
                return True
                
            # Skip system files if configured (Windows only)
            if self.ignore_system and os.name == 'nt' and file_path.name.endswith(('.sys', '.dll', '.exe')):
                logger.debug(f"Skipping system file: {file_path}")
                return True
                
            # Check file size filters
            file_size = file_path.stat().st_size
            if self.min_size is not None and file_size < self.min_size:
                logger.debug(f"Skipping {file_path}: Size ({file_size} bytes) < min_size ({self.min_size} bytes)")
                return True
            if self.max_size is not None and file_size > self.max_size:
                logger.debug(f"Skipping {file_path}: Size ({file_size} bytes) > max_size ({self.max_size} bytes)")
                return True
                
            # Check file age filters
            if self.min_age_days is not None or self.max_age_days is not None:
                stat_info = file_path.stat()
                file_time = stat_info.st_mtime if self.use_modified_time else stat_info.st_ctime
                file_date = datetime.fromtimestamp(file_time).date()
                days_old = (datetime.now().date() - file_date).days
                
                if self.min_age_days is not None and days_old < self.min_age_days:
                    logger.debug(f"Skipping {file_path}: Age ({days_old} days) < min_age_days ({self.min_age_days} days)")
                    return True
                if self.max_age_days is not None and days_old > self.max_age_days:
                    logger.debug(f"Skipping {file_path}: Age ({days_old} days) > max_age_days ({self.max_age_days} days)")
                    return True
                    
            # Check for duplicates if enabled
            if self.detect_duplicates and self._is_duplicate(file_path):
                return self._handle_duplicate(file_path)
                
            return False
            
        except (OSError, PermissionError) as e:
            logger.error(f"Error checking file {file_path}: {e}")
            self.errors += 1
            return True
                
        return False
    
    def get_destination_folder(self, file_path: Path) -> str:
        """Determine the destination folder for a file."""
        # First check filename patterns
        folder = rules.get_folder_for_filename(file_path.name)
        if folder:
            return folder
            
        # Then check extension
        ext = file_path.suffix.lower()
        if ext:
            folder = rules.get_folder_for_extension(ext, self.custom_rules)
            if folder != "Others":
                return folder
        
        # Default to Others
        return "Others"
    
    def ensure_unique_filename(self, dest_path: Path) -> Path:
        """Ensure the destination filename is unique by adding a counter if needed."""
        if not dest_path.exists():
            return dest_path
            
        counter = 1
        while True:
            new_name = f"{dest_path.stem}_{counter}{dest_path.suffix}"
            new_path = dest_path.with_name(new_name)
            if not new_path.exists():
                return new_path
            counter += 1
    
    def organize_file(self, file_path: Path) -> bool:
        """Organize a single file."""
        self.files_processed += 1
        
        try:
            if self.should_skip_file(file_path):
                self.files_skipped += 1
                logger.debug(f"Skipping file: {file_path}")
                return False
                
            # Get destination folder
            dest_folder_name = self.get_destination_folder(file_path)
            dest_folder = self.source_dir / dest_folder_name
            
            # Create destination folder if it doesn't exist
            if not dest_folder.exists():
                logger.info(f"Creating folder: {dest_folder}")
                if not self.dry_run:
                    dest_folder.mkdir(parents=True, exist_ok=True)
            
            # Determine destination path
            dest_path = dest_folder / file_path.name
            
            # Handle duplicate filenames
            if dest_path.exists() and dest_path != file_path:
                dest_path = self.ensure_unique_filename(dest_path)
            
            # Skip if already in the right place
            if dest_path == file_path:
                logger.debug(f"File already in correct location: {file_path}")
                return False
                
            # Move the file
            logger.info(f"Moving: {file_path} → {dest_path}")
            if not self.dry_run:
                try:
                    shutil.move(str(file_path), str(dest_path))
                    self.files_moved += 1
                    return True
                except Exception as e:
                    logger.error(f"Error moving file {file_path}: {e}")
                    self.errors += 1
                    return False
            else:
                self.files_moved += 1
                return True
                
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            self.errors += 1
            return False
    
    def organize(self) -> Dict[str, int]:
        """Organize all files in the source directory."""
        logger.info(f"Starting organization of: {self.source_dir}")
        start_time = time.time()
        
        # Reset stats
        self.files_processed = 0
        self.files_moved = 0
        self.files_skipped = 0
        self.errors = 0
        
        # Process all files in the source directory (non-recursive)
        for item in self.source_dir.iterdir():
            if item.is_file():
                self.organize_file(item)
        
        # Log summary
        elapsed = time.time() - start_time
        logger.info(
            f"Organization complete. "
            f"Processed: {self.files_processed}, "
            f"Moved: {self.files_moved}, "
            f"Skipped: {self.files_skipped}, "
            f"Errors: {self.errors}, "
            f"Time: {elapsed:.2f}s"
        )
        
        return {
            'processed': self.files_processed,
            'moved': self.files_moved,
            'skipped': self.files_skipped,
            'errors': self.errors,
            'elapsed_seconds': elapsed
        }

def organize_folder(
    source_dir: Union[str, Path],
    dry_run: bool = False,
    **kwargs
) -> Dict[str, int]:
    """
    Convenience function to organize a folder with default settings.
    
    Args:
        source_dir: Directory to organize
        dry_run: If True, don't actually move any files
        **kwargs: Additional arguments to pass to FileOrganizer
        
    Returns:
        Dict with statistics about the operation
    """
    organizer = FileOrganizer(source_dir=source_dir, dry_run=dry_run, **kwargs)
    return organizer.organize()
