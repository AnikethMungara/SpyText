# SpyText

[![GitHub](https://img.shields.io/badge/GitHub-SpyText-blue?logo=github)](https://github.com/AnikethMungara/SpyText)

**Human-Aligned Document Perception System**

A local system for detecting and handling human-invisible text in documents before content is passed to large language models. SpyText identifies white-on-white text, microscopic fonts, off-screen elements, and other perceptually hidden content that could enable prompt injection or safety violations.

## Purpose

SpyText ensures that large language models only receive content a human could reasonably perceive, preventing hidden prompt injection attacks and maintaining alignment between human oversight and automated processing.

## Core Principles

- Everything runs locally with no cloud APIs or external dependencies
- No LLM retraining required, works with any existing model
- Transparent detection and handling with full user visibility
- Human perception alignment through visual analysis
- Correctness and transparency prioritized over performance

## Project Structure

```
SpyText/
├── README.md                   # Project overview
├── INSTALLATION.md             # Installation guide
├── requirements.txt            # Python dependencies
├── config/
│   └── settings.yaml          # Configuration settings
├── src/
│   ├── cli.py                 # Command-line interface
│   ├── ingest/
│   │   └── document_loader.py # Document validation
│   ├── extract/
│   │   └── pdf_extractor.py   # Text extraction with metadata
│   ├── models/
│   │   └── text_span.py       # Core data model
│   └── utils/
│       └── color_utils.py     # Color and contrast analysis
├── tests/                      # Test suite
└── examples/                   # Example documents
```

## Quick Start

### Installation

See [INSTALLATION.md](INSTALLATION.md) for detailed setup instructions.

**Quick install:**

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Note:** Tesseract OCR is required for scanned document support. See installation guide for platform-specific instructions.

### Usage

**Analyze a document:**

```bash
python -m src.cli document.pdf
```

**View help:**

```bash
python -m src.cli --help
```

**View version:**

```bash
python -m src.cli --version
```

## Features

### Current Capabilities

- **Document Loading:** Validates and detects PDF and image formats
- **Text Extraction:** Native PDF text extraction with position and font metadata
- **OCR Support:** Automatic fallback to OCR for scanned documents
- **Metadata Capture:** Font size, text color, and background color for each text span
- **Color Analysis:** RGB color sampling for visibility assessment

### Planned Features

- Contrast ratio calculation using WCAG standards
- Microscopic text detection based on font size
- Off-screen element detection via bounding box analysis
- Risk aggregation and document-level safety assessment
- Configurable handling policies (strip, warn, or block suspicious content)

## Threat Model

### Defended Attack Vectors

1. **White-on-white text:** Text rendered with insufficient contrast (ratio less than 1.5)
2. **Microscopic text:** Font sizes below human-readable thresholds (less than 1pt)
3. **Off-screen positioning:** Text placed outside visible page boundaries
4. **Zero-opacity text:** Fully transparent or near-transparent text elements
5. **Hidden prompt injection:** Instruction-like patterns embedded in invisible text

### Out of Scope

- **Steganography:** Requires specialized detection beyond visual analysis
- **Adversarial images:** Requires computer vision model integration
- **Unicode exploits:** Zero-width characters and similar require different approaches

## Architecture

### Data Model

All extracted text is represented as `TextSpan` objects:

```python
@dataclass
class TextSpan:
    text: str                              # Extracted text content
    page_number: int                       # 1-indexed page number
    bbox: Tuple[float, float, float, float] # Bounding box (x0, y0, x1, y1)
    font_size: Optional[float]             # Font size in points
    font_color: Optional[Tuple[int, int, int]]      # RGB color
    background_color: Optional[Tuple[int, int, int]] # RGB color
```

### Extraction Pipeline

```
Document Input
    ↓
Document Loader (validation, format detection)
    ↓
PDF Extractor
    ├─→ Native Text Extraction (pdfplumber + pymupdf)
    └─→ OCR Fallback (pytesseract for scanned documents)
    ↓
TextSpan Objects (with complete metadata)
    ↓
[Future: Visibility Analysis]
    ↓
[Future: Risk Assessment]
    ↓
[Future: Safe Output Generation]
```

## Configuration

Edit `config/settings.yaml` to customize:

- **Extraction settings:** PDF processing method, OCR parameters
- **Visibility thresholds:** Contrast ratios, font sizes, bounding box rules
- **Risk assessment:** Aggregation rules, detection sensitivity
- **Output behavior:** Strip, warn, or block policies for suspicious content

Example configuration:

```yaml
extraction:
  pdf_method: "hybrid"  # Native + OCR fallback
  ocr:
    enabled: true
    language: "eng"
    dpi: 300

visibility:
  contrast:
    min_ratio: 4.5           # WCAG AA standard
    suspicious_ratio: 3.0
  font_size:
    min_readable: 8.0        # Points
    suspicious_size: 4.0
```

## Testing

Test documents are provided in `examples/`:

- `simple_text.pdf` - Normal readable text
- `white_on_white.pdf` - Hidden white text on white background
- `microscopic.pdf` - Text at 1pt and 4pt sizes
- `low_contrast.pdf` - Light gray text on white background

Run tests:

```bash
python tests/test_extraction.py
```

## Dependencies

All dependencies run locally without external API calls:

| Library | Purpose |
|---------|---------|
| pdfplumber | High-level PDF text extraction with positioning |
| pymupdf | Low-level PDF rendering and metadata access |
| Pillow | Image processing for visual analysis |
| pytesseract | OCR engine interface for scanned documents |
| opencv-python | Computer vision utilities for contrast detection |
| numpy | Numerical operations for color calculations |
| PyYAML | Configuration file parsing |
| rich | Terminal UI formatting |

## Success Criteria

1. **Correctness:** No invisible text is silently passed to language models
2. **Transparency:** All detection decisions are visible to users
3. **Local Operation:** No external network dependencies or API calls
4. **Human Alignment:** Only perceptually visible content is extracted
5. **Configurability:** Adjustable thresholds via settings file

## Development

### Design Philosophy

SpyText follows a phased development approach with strict boundaries:

- **Phase 1:** Project structure and data models
- **Phase 2:** Text extraction with metadata
- **Phase 3:** Visibility and salience detection
- **Phase 4:** Risk aggregation
- **Phase 5:** Testing and evaluation
- **Phase 6:** Output generation and safety policies

See `PHASE_STATUS.md` for detailed development status.

## Author

**Aniketh Mungara**

- GitHub: [@AnikethMungara](https://github.com/AnikethMungara)
- Project: [SpyText](https://github.com/AnikethMungara/SpyText)

### Contributing

Contributions are welcome. Please respect phase boundaries and maintain the principle of local-only operation. All new features must include tests and documentation.

## License

To be determined.

## Disclaimer

SpyText is a research project for AI safety. It provides a defense layer against visual prompt injection but should not be the sole security measure for LLM applications. Use in conjunction with other security best practices including input validation, output filtering, and prompt engineering safeguards.

## References

- [Web Content Accessibility Guidelines (WCAG) 2.1](https://www.w3.org/WAI/WCAG21/)
- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [Prompt Injection Defenses](https://simonwillison.net/2023/Apr/14/worst-that-can-happen/)

## Support

For installation issues, see [INSTALLATION.md](INSTALLATION.md).

For development questions, see phase documentation in `PHASE_STATUS.md`.
