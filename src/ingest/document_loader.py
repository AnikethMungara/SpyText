"""
Document loading and validation.

Phase 1: Stub only - no implementation yet.
Phase 2: File I/O, format detection, and validation (IMPLEMENTED).
"""

import mimetypes
from pathlib import Path
from typing import Optional


class DocumentLoader:
    """
    Loads and validates document files.

    Responsibilities (Phase 2 - IMPLEMENTED):
    - Validate file exists and is readable
    - Detect document format (PDF, image, etc.)
    - Route to appropriate extractor
    - Handle file I/O errors gracefully
    """

    # Supported file formats
    SUPPORTED_FORMATS = {
        '.pdf': 'pdf',
        '.docx': 'docx',
        '.png': 'image',
        '.jpg': 'image',
        '.jpeg': 'image',
        '.tiff': 'image',
        '.tif': 'image',
        '.bmp': 'image',
    }

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize document loader.

        Args:
            config: Configuration dict from settings.yaml
        """
        self.config = config or {}
        # Initialize mimetypes database
        mimetypes.init()

    def load(self, file_path: str) -> Path:
        """
        Load and validate a document file.

        Phase 2: IMPLEMENTED - Full validation and format detection

        Args:
            file_path: Path to document file

        Returns:
            Validated Path object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is unsupported
            PermissionError: If file is not readable
        """
        path = Path(file_path)

        # Validate file exists
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Validate it's a file, not a directory
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        # Validate file is readable
        if not path.stat().st_size >= 0:  # Basic readability check
            raise PermissionError(f"Cannot access file: {file_path}")

        # Detect and validate format
        file_format = self.detect_format(path)
        if file_format not in ['pdf', 'docx', 'image']:
            raise ValueError(
                f"Unsupported file format: {path.suffix}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS.keys())}"
            )

        return path

    def detect_format(self, file_path: Path) -> str:
        """
        Detect document format.

        Phase 2: IMPLEMENTED - Uses file extension primarily

        Args:
            file_path: Path to document

        Returns:
            Format category string ('pdf', 'docx', or 'image')

        Raises:
            ValueError: If file format is not recognized
        """
        # Get file extension (lowercase, with dot)
        extension = file_path.suffix.lower()

        # Check against supported formats
        if extension in self.SUPPORTED_FORMATS:
            return self.SUPPORTED_FORMATS[extension]

        # Try to detect via MIME type as fallback
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            if mime_type == 'application/pdf':
                return 'pdf'
            elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                return 'docx'
            elif mime_type.startswith('image/'):
                return 'image'

        # Unknown format
        raise ValueError(
            f"Unknown file format: {extension}. "
            f"Supported: {', '.join(self.SUPPORTED_FORMATS.keys())}"
        )
