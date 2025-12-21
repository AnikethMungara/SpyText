"""
Core data models for SpyText.

TextSpan represents a single piece of extracted text with all metadata
needed to assess human visibility.
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from src.detect.visibility_analyzer import VisibilityStatus


@dataclass
class TextSpan:
    """
    Represents a single span of text extracted from a document.

    All visual properties are captured to enable visibility analysis.

    Attributes:
        text: The actual text content
        page_number: 1-indexed page number where text appears
        bbox: Bounding box as (x0, y0, x1, y1) in document coordinates
        font_size: Font size in points (if available)
        font_color: RGB color tuple (0-255 per channel) of text
        background_color: RGB color tuple of background behind text
        visibility_status: Classification of visibility (Phase 3+)
        contrast_ratio: WCAG contrast ratio (Phase 3+)
    """
    text: str
    page_number: int
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    font_size: Optional[float] = None
    font_color: Optional[Tuple[int, int, int]] = None  # RGB
    background_color: Optional[Tuple[int, int, int]] = None  # RGB

    # Phase 3: Visibility analysis results
    visibility_status: Optional['VisibilityStatus'] = None
    contrast_ratio: Optional[float] = None

    def __repr__(self) -> str:
        """Human-readable representation for debugging."""
        color_info = ""
        if self.font_color and self.background_color:
            color_info = f" fg={self.font_color} bg={self.background_color}"

        size_info = f" size={self.font_size}pt" if self.font_size else ""

        text_preview = self.text[:50] + "..." if len(self.text) > 50 else self.text

        return (
            f"TextSpan(page={self.page_number}, "
            f"text='{text_preview}'{size_info}{color_info})"
        )
