"""
Default file organization rules for onefile.
"""

from typing import Dict, List, Optional


# Default folder mapping based on file extensions
DEFAULT_RULES: Dict[str, List[str]] = {

    # Documents
    "Documents/PDFs": [".pdf"],

    "Documents/Word": [
        ".doc",
        ".docx",
        ".docm",
        ".dotx",
        ".dotm",
        ".odt"
    ],

    "Documents/Spreadsheets": [
        ".xls",
        ".xlsx",
        ".xlsm",
        ".xlsb",
        ".ods",
        ".csv"
    ],

    "Documents/Presentations": [
        ".ppt",
        ".pptx",
        ".pptm",
        ".ppsx",
        ".odp"
    ],

    "Documents/Text": [
        ".txt",
        ".rtf",
        ".md",
        ".markdown",
        ".tex",
        ".log"
    ],


    # Images
    "Images": [
        ".jpg",
        ".jpeg",
        ".jpe",
        ".jif",
        ".jfif",
        ".jfi",
        ".png",
        ".gif",
        ".webp",
        ".tiff",
        ".tif",
        ".psd",
        ".raw",
        ".arw",
        ".cr2",
        ".nrw",
        ".k25",
        ".bmp",
        ".dib",
        ".heif",
        ".heic",
        ".ind",
        ".indd",
        ".indt",
        ".svg",
        ".svgz",
        ".ai",
        ".eps"
    ],


    # Videos
    "Videos": [
        ".webm",
        ".mpg",
        ".mp2",
        ".mpeg",
        ".mpe",
        ".mpv",
        ".mp4",
        ".m4p",
        ".m4v",
        ".avi",
        ".wmv",
        ".mov",
        ".qt",
        ".flv",
        ".swf",
        ".avchd"
    ],


    # Audio
    "Audio": [
        ".aac",
        ".aif",
        ".aiff",
        ".flac",
        ".m4a",
        ".m4b",
        ".m4p",
        ".mp3",
        ".mpc",
        ".ogg",
        ".oga",
        ".wav",
        ".wma",
        ".wpl"
    ],


    # Archives
    "Archives": [
        ".7z",
        ".arj",
        ".deb",
        ".pkg",
        ".rar",
        ".rpm",
        ".tar.gz",
        ".z",
        ".zip"
    ],


    # Executables
    "Executables": [
        ".apk",
        ".bat",
        ".bin",
        ".cgi",
        ".pl",
        ".com",
        ".exe",
        ".gadget",
        ".jar",
        ".msi",
        ".wsf"
    ],


    # Development
    "Code/Python": [
        ".py",
        ".pyc",
        ".pyo",
        ".pyd",
        ".pyw",
        ".pyz",
        ".pyzw"
    ],

    "Code/Web": [
        ".html",
        ".htm",
        ".xhtml",
        ".php",
        ".asp",
        ".aspx",
        ".jsp"
    ],

    "Code/CSS": [
        ".css",
        ".scss",
        ".sass",
        ".less"
    ],

    "Code/JavaScript": [
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".mjs",
        ".cjs"
    ],

    "Code/JSON": [
        ".json",
        ".json5",
        ".jsonl"
    ],

    "Code/XML": [
        ".xml",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".conf"
    ],


    # Ebooks
    "Ebooks": [
        ".azw",
        ".azw3",
        ".azw4",
        ".azw8",
        ".cb7",
        ".cbr",
        ".cbt",
        ".cbz",
        ".epub",
        ".fb2",
        ".lit",
        ".lrf",
        ".mobi",
        ".pdb"
    ],
}


# Pattern-based rules
#
# IMPORTANT:
# Do not use "scr" here because filenames such as
# "script.py" contain "scr".
#
# A Python file must be classified as Code/Python.
PATTERN_RULES = [
    (
        "Screenshots/",
        [
            "screenshot",
            "screen_shot",
            "screen-shot"
        ]
    ),

    (
        "Downloads/",
        [
            "download",
            "dl"
        ]
    ),

    (
        "Invoices/",
        [
            "invoice",
            "bill",
            "receipt"
        ]
    ),

    (
        "Resumes/",
        [
            "resume",
            "cv",
            "curriculum"
        ]
    ),
]


def get_default_rules() -> Dict[str, List[str]]:
    """Return a copy of the default rules."""

    return {
        folder: extensions.copy()
        for folder, extensions in DEFAULT_RULES.items()
    }


def get_pattern_rules() -> list:
    """Return a copy of the pattern rules."""

    return [
        (folder, patterns.copy())
        for folder, patterns in PATTERN_RULES
    ]


def get_folder_for_extension(
    ext: str,
    custom_rules: Optional[Dict[str, List[str]]] = None
) -> str:
    """
    Get the appropriate folder for a file extension.

    Args:
        ext: File extension with leading dot, e.g. '.txt'

        custom_rules:
            Optional custom rules to override defaults.

    Returns:
        Folder path relative to the source directory.
    """

    # Check custom rules first
    if custom_rules:

        for folder, extensions in custom_rules.items():

            if ext.lower() in [
                extension.lower()
                for extension in extensions
            ]:
                return folder

    # Check default rules
    for folder, extensions in DEFAULT_RULES.items():

        if ext.lower() in [
            extension.lower()
            for extension in extensions
        ]:
            return folder

    # Unknown extension
    return "Others"


def get_folder_for_filename(filename: str) -> Optional[str]:
    """
    Get a folder based on filename patterns.

    Args:
        filename:
            The name of the file without its path.

    Returns:
        Folder path if a pattern matches, otherwise None.
    """

    filename_lower = filename.lower()

    for folder, patterns in PATTERN_RULES:

        if any(
            pattern in filename_lower
            for pattern in patterns
        ):
            return folder

    return None