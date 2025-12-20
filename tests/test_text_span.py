"""
Phase 1 tests for TextSpan data model.

These tests verify the basic structure is correct.
Phase 2+ will add extraction tests.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import TextSpan


def test_text_span_creation():
    """Test that TextSpan can be created with all fields."""
    span = TextSpan(
        text="Hello, world!",
        page_number=1,
        bbox=(10.0, 20.0, 100.0, 40.0),
        font_size=12.0,
        font_color=(0, 0, 0),
        background_color=(255, 255, 255)
    )

    assert span.text == "Hello, world!"
    assert span.page_number == 1
    assert span.bbox == (10.0, 20.0, 100.0, 40.0)
    assert span.font_size == 12.0
    assert span.font_color == (0, 0, 0)
    assert span.background_color == (255, 255, 255)


def test_text_span_optional_fields():
    """Test that TextSpan works with minimal fields."""
    span = TextSpan(
        text="Minimal span",
        page_number=1,
        bbox=(0.0, 0.0, 10.0, 10.0)
    )

    assert span.text == "Minimal span"
    assert span.page_number == 1
    assert span.bbox == (0.0, 0.0, 10.0, 10.0)
    assert span.font_size is None
    assert span.font_color is None
    assert span.background_color is None


def test_text_span_repr():
    """Test that TextSpan has readable string representation."""
    span = TextSpan(
        text="Test",
        page_number=1,
        bbox=(0.0, 0.0, 10.0, 10.0),
        font_size=10.0,
        font_color=(255, 0, 0),
        background_color=(255, 255, 255)
    )

    repr_str = repr(span)
    assert "TextSpan" in repr_str
    assert "page=1" in repr_str
    assert "Test" in repr_str


if __name__ == "__main__":
    print("Running Phase 1 tests...")
    test_text_span_creation()
    print("[PASS] test_text_span_creation")

    test_text_span_optional_fields()
    print("[PASS] test_text_span_optional_fields")

    test_text_span_repr()
    print("[PASS] test_text_span_repr")

    print("\nAll Phase 1 tests passed!")
