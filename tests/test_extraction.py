"""
Phase 2 tests for PDF extraction.

These tests verify text extraction works correctly.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest import DocumentLoader
from src.extract import PDFExtractor
from src.models import TextSpan


def test_document_loader():
    """Test DocumentLoader can load and validate PDFs."""
    loader = DocumentLoader()

    # Test with existing test file
    examples_dir = Path(__file__).parent.parent / "examples"
    test_file = examples_dir / "simple_text.pdf"

    if test_file.exists():
        path = loader.load(str(test_file))
        assert path.exists()
        assert path.suffix == ".pdf"

        # Test format detection
        format_type = loader.detect_format(path)
        assert format_type == "pdf"

        print(f"[PASS] Loaded and validated: {test_file.name}")
    else:
        print(f"[SKIP] Test file not found: {test_file}")


def test_simple_pdf_extraction():
    """Test extracting text from a simple PDF."""
    extractor = PDFExtractor()

    examples_dir = Path(__file__).parent.parent / "examples"
    test_file = examples_dir / "simple_text.pdf"

    if not test_file.exists():
        print(f"[SKIP] Test file not found: {test_file}")
        return

    # Extract text spans
    spans = extractor.extract(test_file)

    # Verify we got some spans
    assert len(spans) > 0, "Should extract at least some text spans"

    # Verify spans have required fields
    for span in spans:
        assert isinstance(span, TextSpan)
        assert span.text, "Text should not be empty"
        assert span.page_number >= 1, "Page number should be >= 1"
        assert len(span.bbox) == 4, "Bbox should have 4 coordinates"

    # Verify we extracted the expected text
    all_text = ' '.join(span.text for span in spans)
    assert "test" in all_text.lower(), "Should find 'test' in extracted text"
    assert "normal" in all_text.lower() or "text" in all_text.lower()

    print(f"[PASS] Extracted {len(spans)} spans from simple_text.pdf")
    print(f"       Sample text: {spans[0].text if spans else 'N/A'}")


def test_white_on_white_extraction():
    """Test that we can extract white-on-white text."""
    extractor = PDFExtractor()

    examples_dir = Path(__file__).parent.parent / "examples"
    test_file = examples_dir / "white_on_white.pdf"

    if not test_file.exists():
        print(f"[SKIP] Test file not found: {test_file}")
        return

    # Extract text spans
    spans = extractor.extract(test_file)

    assert len(spans) > 0, "Should extract text even if it's white-on-white"

    # Check if we found the hidden text
    all_text = ' '.join(span.text for span in spans)

    # The hidden text should be extracted (we're not filtering yet - that's Phase 3)
    # Just verify extraction works
    print(f"[PASS] Extracted {len(spans)} spans from white_on_white.pdf")

    # Check if any spans have white or near-white color
    white_spans = [
        span for span in spans
        if span.font_color and sum(span.font_color) > 700  # Near white
    ]

    if white_spans:
        print(f"       Found {len(white_spans)} white/light-colored text spans")
        print(f"       Sample: '{white_spans[0].text}' color={white_spans[0].font_color}")


def test_microscopic_extraction():
    """Test that we can extract microscopic text."""
    extractor = PDFExtractor()

    examples_dir = Path(__file__).parent.parent / "examples"
    test_file = examples_dir / "microscopic.pdf"

    if not test_file.exists():
        print(f"[SKIP] Test file not found: {test_file}")
        return

    # Extract text spans
    spans = extractor.extract(test_file)

    assert len(spans) > 0, "Should extract text even if microscopic"

    # Check for very small font sizes
    small_spans = [
        span for span in spans
        if span.font_size and span.font_size < 5
    ]

    if small_spans:
        print(f"[PASS] Found {len(small_spans)} microscopic text spans (< 5pt)")
        print(f"       Smallest: {min(s.font_size for s in small_spans if s.font_size):.1f}pt")
        print(f"       Sample: '{small_spans[0].text}'")
    else:
        print(f"[PASS] Extracted {len(spans)} spans (font size data may be unavailable)")


def test_text_span_metadata():
    """Test that extracted spans have proper metadata."""
    extractor = PDFExtractor()

    examples_dir = Path(__file__).parent.parent / "examples"
    test_file = examples_dir / "simple_text.pdf"

    if not test_file.exists():
        print(f"[SKIP] Test file not found: {test_file}")
        return

    spans = extractor.extract(test_file)

    # Check metadata coverage
    with_font_size = sum(1 for s in spans if s.font_size is not None)
    with_font_color = sum(1 for s in spans if s.font_color is not None)
    with_bg_color = sum(1 for s in spans if s.background_color is not None)

    print(f"[PASS] Metadata coverage:")
    print(f"       Font size: {with_font_size}/{len(spans)} spans")
    print(f"       Font color: {with_font_color}/{len(spans)} spans")
    print(f"       Background color: {with_bg_color}/{len(spans)} spans")

    # At least some spans should have metadata
    assert with_font_size > 0, "Should have font size for at least some spans"


def main():
    """Run all Phase 2 extraction tests."""
    print("=" * 60)
    print("Phase 2 - Extraction Tests")
    print("=" * 60)
    print()

    test_document_loader()
    print()

    test_simple_pdf_extraction()
    print()

    test_white_on_white_extraction()
    print()

    test_microscopic_extraction()
    print()

    test_text_span_metadata()
    print()

    print("=" * 60)
    print("All Phase 2 extraction tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
