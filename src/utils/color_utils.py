"""
Color and contrast analysis utilities.

Phase 1: Stub only - no implementation yet.
Phase 3: IMPLEMENTED - WCAG contrast ratio calculations.
"""

from typing import Tuple


def _srgb_to_linear(channel: float) -> float:
    """
    Convert sRGB color channel to linear RGB.

    Applies gamma correction according to WCAG formula.

    Args:
        channel: sRGB channel value (0.0 to 1.0)

    Returns:
        Linear RGB value (0.0 to 1.0)
    """
    if channel <= 0.03928:
        return channel / 12.92
    else:
        return ((channel + 0.055) / 1.055) ** 2.4


def calculate_contrast_ratio(
    foreground: Tuple[int, int, int],
    background: Tuple[int, int, int]
) -> float:
    """
    Calculate WCAG contrast ratio between two colors.

    Phase 3: IMPLEMENTED - WCAG 2.1 contrast calculation

    Args:
        foreground: RGB color tuple (0-255 per channel)
        background: RGB color tuple (0-255 per channel)

    Returns:
        Contrast ratio (1.0 to 21.0, where 21.0 is maximum contrast)

    Reference:
        https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html
    """
    # Calculate relative luminance for both colors
    l1 = relative_luminance(foreground)
    l2 = relative_luminance(background)

    # Ensure l1 is the lighter color (higher luminance)
    if l1 < l2:
        l1, l2 = l2, l1

    # Calculate contrast ratio using WCAG formula
    # Add 0.05 to both values per WCAG specification
    contrast_ratio = (l1 + 0.05) / (l2 + 0.05)

    return contrast_ratio


def relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """
    Calculate relative luminance of an RGB color.

    Phase 3: IMPLEMENTED - WCAG 2.1 luminance calculation

    Args:
        rgb: RGB color tuple (0-255 per channel)

    Returns:
        Relative luminance (0.0 to 1.0)

    Reference:
        https://www.w3.org/WAI/GL/wiki/Relative_luminance
    """
    # Normalize RGB values to 0-1
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0

    # Apply gamma correction to each channel
    r_linear = _srgb_to_linear(r)
    g_linear = _srgb_to_linear(g)
    b_linear = _srgb_to_linear(b)

    # Calculate relative luminance using WCAG coefficients
    # These coefficients account for human eye sensitivity to different colors
    luminance = 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear

    return luminance


def is_low_contrast(
    foreground: Tuple[int, int, int],
    background: Tuple[int, int, int],
    threshold: float = 4.5
) -> bool:
    """
    Check if color pair is below WCAG contrast threshold.

    Phase 3: IMPLEMENTED - Uses WCAG contrast ratio

    Args:
        foreground: Text color (RGB)
        background: Background color (RGB)
        threshold: WCAG threshold (4.5 for normal text, 3.0 for large text)

    Returns:
        True if contrast is below threshold (suspicious/invisible)

    Reference:
        WCAG AA: 4.5:1 for normal text, 3.0:1 for large text
        WCAG AAA: 7.0:1 for normal text, 4.5:1 for large text
    """
    contrast = calculate_contrast_ratio(foreground, background)
    return contrast < threshold
