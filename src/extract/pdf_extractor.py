"""
PDF text extraction with metadata.

Phase 1: Stub only - no implementation yet.
Phase 2: IMPLEMENTED - Native text extraction with pdfplumber and pymupdf.
Phase 2: IMPLEMENTED - OCR fallback for scanned documents with pytesseract.
"""

from pathlib import Path
from typing import List, Optional, Tuple
import logging

import pdfplumber
import fitz  # pymupdf
from PIL import Image
import pytesseract
import numpy as np

from src.models import TextSpan

logger = logging.getLogger(__name__)


class PDFExtractor:
    """
    Extract text and metadata from PDF files.

    Responsibilities (Phase 2 - IMPLEMENTED):
    - Extract native text with positioning
    - Capture font size, color, background
    - Handle both text-based and scanned PDFs
    - Preserve document structure
    """

    # Threshold for detecting scanned PDFs (ratio of image area to page area)
    SCANNED_IMAGE_RATIO_THRESHOLD = 0.7

    # Minimum extractable text characters to consider native extraction successful
    MIN_NATIVE_TEXT_LENGTH = 50

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize PDF extractor.

        Args:
            config: Configuration dict from settings.yaml
        """
        self.config = config or {}
        self.ocr_enabled = self.config.get('extraction', {}).get('ocr', {}).get('enabled', True)
        self.ocr_dpi = self.config.get('extraction', {}).get('ocr', {}).get('dpi', 300)
        self.ocr_lang = self.config.get('extraction', {}).get('ocr', {}).get('language', 'eng')

    def extract(self, pdf_path: Path) -> List[TextSpan]:
        """
        Extract all text spans from a PDF with metadata.

        Phase 2: IMPLEMENTED - Full extraction pipeline with OCR fallback

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of TextSpan objects with full metadata

        Raises:
            ValueError: If PDF is invalid or corrupted
        """
        logger.info(f"Extracting text from PDF: {pdf_path}")

        try:
            # Try native text extraction first
            spans = self._extract_native_text(pdf_path)

            # Check if we got enough text
            total_text = ''.join(span.text for span in spans)

            # If native extraction yielded little/no text, try OCR
            if len(total_text.strip()) < self.MIN_NATIVE_TEXT_LENGTH:
                if self._is_scanned(pdf_path) and self.ocr_enabled:
                    logger.info("PDF appears to be scanned or has minimal text, using OCR")
                    spans = self._extract_ocr_text(pdf_path)
                else:
                    logger.warning(
                        f"PDF has minimal text ({len(total_text)} chars) "
                        f"and OCR is {'disabled' if not self.ocr_enabled else 'not needed'}"
                    )

            logger.info(f"Extracted {len(spans)} text spans from {pdf_path.name}")
            return spans

        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {e}") from e

    def _extract_native_text(self, pdf_path: Path) -> List[TextSpan]:
        """
        Extract native text (non-scanned PDF).

        Phase 2: IMPLEMENTED - Uses pdfplumber for text + pymupdf for metadata

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of TextSpan objects
        """
        spans = []

        # Open with pdfplumber for text extraction
        with pdfplumber.open(pdf_path) as pdf:
            # Also open with pymupdf for color/font metadata
            doc_fitz = fitz.open(str(pdf_path))

            for page_num, page in enumerate(pdf.pages, start=1):
                # Get corresponding pymupdf page
                fitz_page = doc_fitz[page_num - 1]

                # Extract characters with detailed metadata
                chars = page.chars

                if not chars:
                    continue

                # Group characters into text spans (by similar properties)
                # For Phase 2, we'll extract each word as a span
                words = page.extract_words(extra_attrs=['fontname', 'size'])

                for word in words:
                    text = word['text']
                    x0, y0, x1, y1 = word['x0'], word['top'], word['x1'], word['bottom']
                    font_size = word.get('size', None)

                    # Get color information from pymupdf
                    # Sample the character color from the first character in the word
                    font_color, bg_color = self._get_colors_at_position(
                        fitz_page, (x0, y0, x1, y1)
                    )

                    # Create TextSpan
                    span = TextSpan(
                        text=text,
                        page_number=page_num,
                        bbox=(x0, y0, x1, y1),
                        font_size=font_size,
                        font_color=font_color,
                        background_color=bg_color
                    )
                    spans.append(span)

            doc_fitz.close()

        return spans

    def _extract_ocr_text(self, pdf_path: Path) -> List[TextSpan]:
        """
        Extract text via OCR (scanned PDF).

        Phase 2: IMPLEMENTED - Uses pytesseract for OCR

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of TextSpan objects
        """
        spans = []

        # Open PDF with pymupdf
        doc = fitz.open(str(pdf_path))

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Render page to image at specified DPI
            mat = fitz.Matrix(self.ocr_dpi / 72, self.ocr_dpi / 72)
            pix = page.get_pixmap(matrix=mat)

            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Run OCR with bounding box data
            ocr_data = pytesseract.image_to_data(
                img,
                lang=self.ocr_lang,
                output_type=pytesseract.Output.DICT
            )

            # Scale factor to convert OCR coordinates back to PDF coordinates
            scale = 72 / self.ocr_dpi

            # Extract words with bounding boxes
            n_boxes = len(ocr_data['text'])
            for i in range(n_boxes):
                text = ocr_data['text'][i].strip()
                conf = int(ocr_data['conf'][i])

                # Skip low-confidence and empty results
                if conf < 30 or not text:
                    continue

                # Get bounding box (scale back to PDF coordinates)
                x0 = ocr_data['left'][i] * scale
                y0 = ocr_data['top'][i] * scale
                w = ocr_data['width'][i] * scale
                h = ocr_data['height'][i] * scale
                x1 = x0 + w
                y1 = y0 + h

                # Sample colors from the image at this location
                font_color, bg_color = self._sample_colors_from_image(
                    img,
                    (ocr_data['left'][i], ocr_data['top'][i],
                     ocr_data['left'][i] + ocr_data['width'][i],
                     ocr_data['top'][i] + ocr_data['height'][i])
                )

                # Create TextSpan (OCR doesn't give us font size reliably)
                span = TextSpan(
                    text=text,
                    page_number=page_num + 1,
                    bbox=(x0, y0, x1, y1),
                    font_size=None,  # OCR can't determine font size
                    font_color=font_color,
                    background_color=bg_color
                )
                spans.append(span)

        doc.close()
        return spans

    def _is_scanned(self, pdf_path: Path) -> bool:
        """
        Detect if PDF is scanned (image-based).

        Phase 2: IMPLEMENTED - Heuristic based on image coverage

        Args:
            pdf_path: Path to PDF file

        Returns:
            True if PDF appears to be scanned
        """
        doc = fitz.open(str(pdf_path))

        total_page_area = 0
        total_image_area = 0

        for page in doc:
            # Get page dimensions
            page_rect = page.rect
            page_area = page_rect.width * page_rect.height
            total_page_area += page_area

            # Get images on page
            image_list = page.get_images(full=True)

            for img in image_list:
                # Get image bounding box
                xref = img[0]
                try:
                    # Get image rectangles on page
                    img_rects = page.get_image_rects(xref)
                    for rect in img_rects:
                        img_area = rect.width * rect.height
                        total_image_area += img_area
                except:
                    # If we can't get image rect, assume it covers a significant area
                    total_image_area += page_area * 0.5

        doc.close()

        if total_page_area == 0:
            return False

        # If images cover more than threshold of the pages, likely scanned
        image_ratio = total_image_area / total_page_area
        return image_ratio > self.SCANNED_IMAGE_RATIO_THRESHOLD

    def _get_colors_at_position(
        self,
        fitz_page: fitz.Page,
        bbox: Tuple[float, float, float, float]
    ) -> Tuple[Optional[Tuple[int, int, int]], Optional[Tuple[int, int, int]]]:
        """
        Extract text and background colors at a specific position.

        Phase 2: IMPLEMENTED - Samples colors from rendered page

        Args:
            fitz_page: pymupdf Page object
            bbox: Bounding box (x0, y0, x1, y1)

        Returns:
            Tuple of (font_color, background_color) as RGB tuples, or (None, None)
        """
        try:
            # Render a small area around the text to sample colors
            # Use moderate DPI for color sampling
            mat = fitz.Matrix(2, 2)  # 2x zoom = 144 DPI
            pix = fitz_page.get_pixmap(matrix=mat, clip=fitz.Rect(bbox))

            # Convert to numpy array for color analysis
            img_array = np.frombuffer(pix.samples, dtype=np.uint8)
            img_array = img_array.reshape(pix.height, pix.width, pix.n)

            # If RGBA, convert to RGB
            if pix.n == 4:
                img_array = img_array[:, :, :3]

            # Sample foreground (darkest pixels - likely text)
            # and background (most common color)
            if img_array.size > 0:
                # Flatten to get all pixels
                pixels = img_array.reshape(-1, 3)

                # Background: most common color (mode)
                # Simple approach: use mean color as background
                bg_color = tuple(int(c) for c in pixels.mean(axis=0))

                # Foreground: darkest pixels (bottom 10%)
                brightness = pixels.sum(axis=1)
                dark_threshold = np.percentile(brightness, 10)
                dark_pixels = pixels[brightness <= dark_threshold]

                if len(dark_pixels) > 0:
                    fg_color = tuple(int(c) for c in dark_pixels.mean(axis=0))
                else:
                    fg_color = (0, 0, 0)  # Default to black

                return fg_color, bg_color

        except Exception as e:
            logger.debug(f"Could not extract colors at position: {e}")

        return None, None

    def _sample_colors_from_image(
        self,
        img: Image.Image,
        bbox: Tuple[int, int, int, int]
    ) -> Tuple[Optional[Tuple[int, int, int]], Optional[Tuple[int, int, int]]]:
        """
        Sample text and background colors from a PIL Image.

        Phase 2: IMPLEMENTED - Used for OCR color extraction

        Args:
            img: PIL Image object
            bbox: Bounding box in image coordinates (x0, y0, x1, y1)

        Returns:
            Tuple of (font_color, background_color) as RGB tuples
        """
        try:
            x0, y0, x1, y1 = bbox
            # Crop to the bounding box
            cropped = img.crop((x0, y0, x1, y1))

            # Convert to numpy array
            img_array = np.array(cropped)

            if img_array.size == 0:
                return None, None

            # Flatten to get all pixels
            pixels = img_array.reshape(-1, 3)

            # Background: mean color
            bg_color = tuple(int(c) for c in pixels.mean(axis=0))

            # Foreground: darkest pixels
            brightness = pixels.sum(axis=1)
            dark_threshold = np.percentile(brightness, 10)
            dark_pixels = pixels[brightness <= dark_threshold]

            if len(dark_pixels) > 0:
                fg_color = tuple(int(c) for c in dark_pixels.mean(axis=0))
            else:
                fg_color = (0, 0, 0)

            return fg_color, bg_color

        except Exception as e:
            logger.debug(f"Could not sample colors from image: {e}")
            return None, None
