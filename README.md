# 📂 OneFile - The Ultimate File Organizer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI](https://img.shields.io/pypi/v/onefile-organizer)](https://pypi.org/project/onefile-organizer/)
[![GitHub stars](https://img.shields.io/github/stars/Aditya-Ranjan1234/onefile?style=social)](https://github.com/Aditya-Ranjan1234/onefile)

OneFile is a powerful, configurable file organization tool that automatically sorts your files into appropriate folders based on their types, names, and other attributes. It's designed to help you keep your digital life organized with minimal effort.

OneFile is a powerful, configurable file organization tool that automatically sorts your files into appropriate folders based on their types, names, and other attributes. It can run as a one-time organizer or as a background daemon that watches for new files.

## ✨ Features

- **Smart File Organization**: Automatically sorts files into appropriate folders by type (documents, images, videos, etc.)
- **Custom Rules**: Define your own file organization rules using simple JSON configuration
- **Watch Mode**: Run as a daemon to automatically organize files as they appear
- **Duplicate Detection**: Identify and handle duplicate files using content hashing
- **Flexible Filtering**: Filter files by size, age, and other attributes
- **MIME Type Detection**: Advanced file type detection beyond just extensions
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Safe Operations**: Dry-run mode to preview changes before applying them
- **Progress Tracking**: Real-time progress updates for large operations
- **Logging**: Comprehensive logging for troubleshooting and auditing

## 📦 Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Install from PyPI (Recommended)

```bash
pip install onefile-organizer
```

### Install from Source (Development)

1. Clone the repository:
   ```bash
   git clone https://github.com/Aditya-Ranjan1234/onefile.git
   cd onefile
   ```

2. Install the package in development mode with all dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

   Or for production use:
   ```bash
   pip install -e .
   ```
   
### System Dependencies

For MIME type detection, you'll need:

- **Windows**: No additional dependencies needed (uses `python-magic-bin`)
- **macOS/Linux**: Install `libmagic` using your package manager:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install libmagic1
  
  # Fedora
  sudo dnf install file-devel
  
  # macOS (using Homebrew)
  brew install libmagic
  ```

## 🚀 Quick Start

### Organize Files Once

Organize files in a directory with a single command:

```bash
onefile --src ~/Downloads --once
```

**Example Output:**
```
[INFO] Starting OneFile v1.0.0
[INFO] Source directory: /home/user/Downloads
[INFO] Destination directory: /home/user/Downloads (same as source)
[INFO] Processing 15 files...
[INFO] Documents/PDFs: 3 files moved
[INFO] Images: 5 files moved
[INFO] Videos: 2 files moved
[INFO] Archives: 3 files moved
[INFO] Other: 2 files skipped
[INFO] Organization complete. Processed: 15, Moved: 13, Skipped: 2, Errors: 0
```

### Watch a Directory

Automatically organize files as they appear in a directory:

```bash
onefile --src ~/Downloads --watch --interval 300
```

This will check the directory every 300 seconds (5 minutes) for new files and organize them automatically.

### Dry Run (Preview Changes)

Preview what changes would be made without actually moving any files:

```bash
onefile --src ~/Downloads --once --dry-run
```

**Example Output:**
```
[DRY RUN] Would move: /home/user/Downloads/report.pdf -> /home/user/Downloads/Documents/PDFs/report.pdf
[DRY RUN] Would move: /home/user/Downloads/photo.jpg -> /home/user/Downloads/Images/photo.jpg
[DRY RUN] Would skip (duplicate): /home/user/Downloads/photo (1).jpg
[INFO] Dry run complete. Would process: 10 files (8 moved, 2 skipped)
```

## 🔧 Advanced Usage

### Configuration File

Create a `onefile_config.json` file in your home directory or specify a custom path:

```json
{
  "rules": {
    "Documents/PDFs": [".pdf", ".xps", ".oxps"],
    "Documents/Books": [".epub", ".mobi", ".azw3"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".svg"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
    "Code": [".py", ".js", ".html", ".css", ".java", ".c", ".cpp", ".h", ".sh", ".bat"],
    "Executables": [".exe", ".msi", ".dmg", ".pkg", ".appimage", ".deb", ".rpm"]
  },
  "options": {
    "recursive": false,
    "overwrite_existing": false,
    "skip_existing": true,
    "preserve_filenames": true,
    "date_format": "%Y-%m-%d",
    "log_level": "INFO"
  }
}
```

### Using Configuration

```bash
# Use default config location (~/.config/onefile/config.json)
onefile --src ~/Downloads --once

# Specify custom config file
onefile --src ~/Downloads --once --config ./custom_config.json

# Override specific options from command line
onefile --src ~/Downloads --once --no-skip-existing --min-size 1M
```

### Advanced Filtering

```bash
# Filter by size (supports K, M, G suffixes)
onefile --src ~/Downloads --min-size 100K --max-size 10M

# Filter by age (in days)
onefile --src ~/Downloads --min-age 1 --max-age 30

# Only process specific file types
onefile --src ~/Downloads --extensions .pdf,.docx,.xlsx

# Exclude hidden files and system files
onefile --src ~/Downloads --no-hidden --no-system
```

### Handling Duplicates

```bash
# Skip duplicate files (default)
onefile --src ~/Downloads --duplicates skip

# Rename duplicate files with a suffix
onefile --src ~/Downloads --duplicates rename

# Move duplicates to a separate folder
onefile --src ~/Downloads --duplicates move --duplicates-dir _duplicates

# Delete duplicate files (use with caution!)
onefile --src ~/Downloads --duplicates delete
```

### Watch Mode Options

```bash
# Watch directory and process new files as they appear
onefile --src ~/Downloads --watch

# Set polling interval in seconds (default: 300)
onefile --src ~/Downloads --watch --interval 60

# Process existing files on startup
onefile --src ~/Downloads --watch --process-existing

# Run in background as a daemon (Unix-like systems)
nohup onefile --src ~/Downloads --watch --daemon &
```

### Output and Logging

```bash
# Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
onefile --src ~/Downloads --log-level DEBUG

# Output results to a JSON file
onefile --src ~/Downloads --output results.json

# Generate a report after processing
onefile --src ~/Downloads --report report.html
```

### Programmatic Usage

You can also use OneFile as a Python library:

```python
from onefile.core import FileOrganizer

# Create an organizer instance
organizer = FileOrganizer(
    source_dir="~/Downloads",
    min_size="1M",
    max_size="100M",
    min_age_days=1,
    dry_run=True
)

# Run the organizer
stats = organizer.organize()
print(f"Processed {stats['processed']} files, moved {stats['moved']}")
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📊 Sample Output

### Organizing Files
```
$ onefile --src ~/Downloads --once
[INFO] Starting OneFile v1.0.0
[INFO] Source directory: /home/user/Downloads
[INFO] Destination directory: /home/user/Downloads
[INFO] Loading configuration from: /home/user/.config/onefile/config.json
[INFO] Processing 15 files...
[INFO] Created directory: /home/user/Downloads/Documents/PDFs
[INFO] Moved: report.pdf -> Documents/PDFs/report.pdf
[INFO] Moved: document.pdf -> Documents/PDFs/document.pdf
[INFO] Created directory: /home/user/Downloads/Images
[INFO] Moved: photo1.jpg -> Images/photo1.jpg
[INFO] Moved: screenshot.png -> Images/screenshot.png
[INFO] Skipped duplicate: photo1 (1).jpg
[INFO] Created directory: /home/user/Downloads/Archives
[INFO] Moved: archive.zip -> Archives/archive.zip
[INFO] Organization complete. Processed: 15, Moved: 12, Skipped: 3, Errors: 0
[INFO] Time taken: 2.34s
```

### Watching a Directory
```
$ onefile --src ~/Downloads --watch --interval 60
[INFO] Starting OneFile v1.0.0 in watch mode
[INFO] Watching directory: /home/user/Downloads
[INFO] Check interval: 60 seconds
[INFO] Press Ctrl+C to stop
[INFO] Detected new file: /home/user/Downloads/document.pdf
[INFO] Moved: document.pdf -> Documents/PDFs/document.pdf
[INFO] Detected new file: /home/user/Downloads/photo.jpg
[INFO] Moved: photo.jpg -> Images/photo.jpg
```

## 🛠️ Development

### Setting Up Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/Aditya-Ranjan1234/onefile.git
   cd onefile
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # Unix/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=onefile --cov-report=html

# Run a specific test
pytest tests/test_core.py -v
```

### Building the Package

```bash
# Build source distribution and wheel
python -m build

# Check package metadata
twine check dist/*

# Upload to TestPyPI (for testing)
twine upload --repository-url https://test.pypi.org/legacy/ dist/*

# Upload to PyPI (production)
twine upload dist/*
```

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please make sure to update tests as appropriate and ensure your code follows the project's style guidelines.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📬 Contact

Aditya Ranjan - [GitHub](https://github.com/Aditya-Ranjan1234) - [Email](mailto:adityaranjan@email.com)

Project Link: [https://github.com/Aditya-Ranjan1234/onefile](https://github.com/Aditya-Ranjan1234/onefile)

## 🙏 Acknowledgments

- [python-magic](https://github.com/ahupp/python-magic) - For MIME type detection
- [Click](https://click.palletsprojects.com/) - For the beautiful command line interface
- [PyYAML](https://pyyaml.org/) - For configuration file parsing
- [tqdm](https://github.com/tqdm/tqdm) - For progress bars
- [colorama](https://github.com/tartley/colorama) - For cross-platform colored terminal output
