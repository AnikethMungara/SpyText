"""
Visibility analysis for text spans.

Phase 3: IMPLEMENTED - Analyzes text visibility based on multiple criteria.
"""

from enum import Enum
from typing import Optional
from pathlib import Path

from src.models import TextSpan
from src.utils.color_utils import calculate_contrast_ratio


class VisibilityStatus(Enum):
    """
    Classification of text span visibility.

    Values:
        VISIBLE: Text is easily visible to humans
        SUSPICIOUS: Text has characteristics that may indicate hiding attempts
        INVISIBLE: Text is effectively invisible to humans
        UNKNOWN: Unable to determine visibility (missing metadata)
    """
    VISIBLE = "visible"
    SUSPICIOUS = "suspicious"
    INVISIBLE = "invisible"
    UNKNOWN = "unknown"


class VisibilityAnalyzer:
    """
    Analyzes text spans to determine human visibility.

    Phase 3: IMPLEMENTED - Multi-criteria visibility detection:
    - Contrast ratio (WCAG-based)
    - Font size
    - Bounding box position
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize visibility analyzer.

        Args:
            config: Configuration dict from settings.yaml
        """
        self.config = config or {}

        # Get thresholds from config
        visibility_config = self.config.get('visibility', {})

        # Contrast thresholds
        contrast_config = visibility_config.get('contrast', {})
        self.min_contrast = contrast_config.get('min_ratio', 4.5)
        self.suspicious_contrast = contrast_config.get('suspicious_ratio', 3.0)
        self.invisible_contrast = contrast_config.get('invisible_ratio', 1.5)

        # Font size thresholds
        font_config = visibility_config.get('font_size', {})
        self.min_readable_size = font_config.get('min_readable', 8.0)
        self.suspicious_size = font_config.get('suspicious_size', 4.0)
        self.invisible_size = font_config.get('invisible_size', 1.0)

        # Bounding box checks
        bbox_config = visibility_config.get('bbox', {})
        self.check_off_screen = bbox_config.get('check_off_screen', True)
        self.check_zero_area = bbox_config.get('check_zero_area', True)

    def analyze(self, span: TextSpan, page_width: float = 612, page_height: float = 792) -> VisibilityStatus:
        """
        Analyze a text span and classify its visibility.

        Args:
            span: TextSpan to analyze
            page_width: Page width in points (default: US Letter = 612pt)
            page_height: Page height in points (default: US Letter = 792pt)

        Returns:
            VisibilityStatus classification
        """
        # Check for missing metadata
        if not self._has_required_metadata(span):
            return VisibilityStatus.UNKNOWN

        # Check multiple visibility criteria
        # Any INVISIBLE criterion makes the whole span invisible
        # Any SUSPICIOUS criterion (without INVISIBLE) makes it suspicious

        contrast_status = self._check_contrast(span)
        if contrast_status == VisibilityStatus.INVISIBLE:
            return VisibilityStatus.INVISIBLE

        size_status = self._check_font_size(span)
        if size_status == VisibilityStatus.INVISIBLE:
            return VisibilityStatus.INVISIBLE

        bbox_status = self._check_bounding_box(span, page_width, page_height)
        if bbox_status == VisibilityStatus.INVISIBLE:
            return VisibilityStatus.INVISIBLE

        # If any check is suspicious, mark as suspicious
        if (contrast_status == VisibilityStatus.SUSPICIOUS or
            size_status == VisibilityStatus.SUSPICIOUS or
            bbox_status == VisibilityStatus.SUSPICIOUS):
            return VisibilityStatus.SUSPICIOUS

        # All checks passed
        return VisibilityStatus.VISIBLE

    def _has_required_metadata(self, span: TextSpan) -> bool:
        """
        Check if span has minimum required metadata for analysis.

        Args:
            span: TextSpan to check

        Returns:
            True if span has required metadata
        """
        # For basic visibility, we need colors
        # Font size is helpful but not strictly required (OCR may not have it)
        return (span.font_color is not None and
                span.background_color is not None)

    def _check_contrast(self, span: TextSpan) -> VisibilityStatus:
        """
        Check text contrast against background.

        Args:
            span: TextSpan with color metadata

        Returns:
            VisibilityStatus based on contrast
        """
        if span.font_color is None or span.background_color is None:
            return VisibilityStatus.UNKNOWN

        contrast = calculate_contrast_ratio(span.font_color, span.background_color)

        # Invisible: contrast below 1.5 (nearly identical colors)
        if contrast < self.invisible_contrast:
            return VisibilityStatus.INVISIBLE

        # Suspicious: contrast below 3.0 (poor visibility)
        if contrast < self.suspicious_contrast:
            return VisibilityStatus.SUSPICIOUS

        # WCAG recommends 4.5:1 for normal text
        # Below this is suboptimal but not necessarily malicious
        if contrast < self.min_contrast:
            return VisibilityStatus.SUSPICIOUS

        return VisibilityStatus.VISIBLE

    def _check_font_size(self, span: TextSpan) -> VisibilityStatus:
        """
        Check if font size is readable.

        Args:
            span: TextSpan with font size metadata

        Returns:
            VisibilityStatus based on font size
        """
        if span.font_size is None:
            # OCR text may not have font size
            # Don't penalize for missing data
            return VisibilityStatus.VISIBLE

        size = span.font_size

        # Invisible: microscopic text (< 1pt)
        if size < self.invisible_size:
            return VisibilityStatus.INVISIBLE

        # Suspicious: very small text (< 4pt)
        if size < self.suspicious_size:
            return VisibilityStatus.SUSPICIOUS

        # Suboptimal but potentially legitimate: small text (< 8pt)
        if size < self.min_readable_size:
            return VisibilityStatus.SUSPICIOUS

        return VisibilityStatus.VISIBLE

    def _check_bounding_box(
        self,
        span: TextSpan,
        page_width: float,
        page_height: float
    ) -> VisibilityStatus:
        """
        Check if bounding box indicates off-screen or zero-area text.

        Args:
            span: TextSpan with bounding box
            page_width: Page width in points
            page_height: Page height in points

        Returns:
            VisibilityStatus based on bounding box
        """
        x0, y0, x1, y1 = span.bbox

        # Check for zero-area bounding box
        if self.check_zero_area:
            width = x1 - x0
            height = y1 - y0

            if width <= 0 or height <= 0:
                return VisibilityStatus.INVISIBLE

        # Check for off-screen positioning
        if self.check_off_screen:
            # Text completely outside page bounds
            if x1 < 0 or y1 < 0 or x0 > page_width or y0 > page_height:
                return VisibilityStatus.INVISIBLE

            # Text partially outside bounds (suspicious but not necessarily invisible)
            if x0 < 0 or y0 < 0 or x1 > page_width or y1 > page_height:
                return VisibilityStatus.SUSPICIOUS

        return VisibilityStatus.VISIBLE

    def get_contrast_ratio(self, span: TextSpan) -> Optional[float]:
        """
        Get the contrast ratio for a span.

        Args:
            span: TextSpan with color metadata

        Returns:
            Contrast ratio or None if metadata missing
        """
        if span.font_color is None or span.background_color is None:
            return None

        return calculate_contrast_ratio(span.font_color, span.background_color)
