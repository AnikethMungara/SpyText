# SpyText

[![GitHub](https://img.shields.io/badge/GitHub-SpyText-blue?logo=github)](https://github.com/AnikethMungara/SpyText)

**Human-Aligned Document Security Scanner**

Detect invisible text, microscopic fonts, and hidden prompt injection attacks in documents before processing with LLMs.

## Overview


SpyText is a local security scanner that detects human-invisible text in PDF and DOCX files. It prevents hidden prompt injection attacks by identifying white-on-white text, microscopic fonts, low-contrast text, and off-screen elements that could manipulate AI systems.

**Runs 100% locally** - No cloud APIs, no external dependencies, no data leaves your machine.

## Supported Formats

- **PDF** - Native text and scanned documents (with OCR)
- **DOCX** - Microsoft Word documents with full structure analysis

## Quick Start

### Download & Run

1. Download `spytext.exe` from releases
2. Run from command line:

```bash
spytext --scan document.pdf
spytext --scan document.docx
```

### Exit Codes

| Code | Status | Meaning |
|------|--------|---------|
| **1** | SAFE | No hidden text detected |
| **2** | SUSPICIOUS | Hidden text found (see page references) |
| **3** | SUSPICIOUS | Error or unable to locate |

### Example Output

**Safe document:**
```
SAFE
Document: report.pdf
Status: No hidden text detected
Total spans analyzed: 45
```

**Suspicious document:**
```
SUSPICIOUS
Document: attack.docx
Reason: Hidden text detected
Risk Score: 93/100
Hidden spans: 8 out of 23 total

Hidden text locations:
  Page 1: 3 hidden span(s) [INVISIBLE]
    Text: 'ignore all previous instructions'
    Why: nearly invisible (contrast: 1.00:1)

  Page 2: 5 hidden span(s) [LOW CONTRAST]
    Text: 'you are now in debug mode'
    Why: very small (2.0pt), low contrast (2.10:1)

[!] WARNING: Possible attack patterns detected!
    Found 2 suspicious pattern(s)
```

## Detection Capabilities

### What SpyText Detects

✓ **Invisible text** - White/near-white text on white background (contrast < 1.5:1)
✓ **Microscopic text** - Font sizes < 1pt (impossible to read)
✓ **Very small text** - Font sizes 1-4pt (very difficult to read)
✓ **Low contrast** - Text with poor visibility (contrast < 3.0:1)
✓ **Off-screen text** - Text positioned outside visible area
✓ **Prompt injection** - 12 common attack patterns detected

### DOCX-Specific Features

✓ **Page breaks** - Accurate page numbering across multi-page documents
✓ **Tables** - Detects hidden text within table cells
✓ **Headers/Footers** - Scans document headers and footers
✓ **Text boxes** - Extracts text from floating shapes and text boxes

## Technology

### Detection Engine

**WCAG 2.1 Compliant Contrast Analysis**
- Relative luminance calculation with gamma correction
- sRGB to linear RGB conversion
- Contrast ratios calculated per WCAG standards

**Multi-Criteria Visibility Detection**
- Font size analysis (accurate to 0.1pt)
- Color contrast analysis (full RGB support)
- Positioning analysis (bounding box validation)
- Combined visibility scoring

**Risk Assessment**
- 5-level risk classification (SAFE, LOW, MEDIUM, HIGH, CRITICAL)
- Prompt injection pattern matching (regex-based)
- Document-level risk aggregation
- Risk scores from 0-100

### Extraction Pipeline

**PDF Processing**
- pdfplumber - High-level text extraction with positioning
- pymupdf - Low-level rendering and color extraction
- pytesseract - OCR for scanned documents

**DOCX Processing**
- python-docx - Document structure parsing
- XML XPath - Text box and shape extraction
- Page break detection (explicit + estimated)
- Table cell iteration with formatting preservation


## Architecture

```
SpyText/
├── spytext.exe              # Standalone executable (no Python needed)
├── spytext.bat              # Batch wrapper (requires Python)
├── requirements.txt         # Python dependencies
├── config/
│   └── settings.yaml        # Detection thresholds and configuration
└── src/
    ├── ingest/
    │   └── document_loader.py     # Format detection & validation
    ├── extract/
    │   ├── pdf_extractor.py       # PDF text + metadata extraction
    │   └── docx_extractor.py      # DOCX text + metadata extraction
    ├── detect/
    │   ├── visibility_analyzer.py # WCAG contrast & visibility logic
    │   └── risk_aggregator.py     # Risk scoring & pattern detection
    ├── sanitize/
    │   └── text_sanitizer.py      # Text cleaning (strip/flag/preserve)
    ├── models/
    │   └── text_span.py           # Core data structures
    └── utils/
        └── color_utils.py         # sRGB/linear RGB conversion
```

## Use Cases



### 1. Pre-LLM Security Gate

```python
import subprocess

def is_safe_for_llm(document_path):
    result = subprocess.run(
        ["spytext", "--scan", document_path],
        capture_output=True
    )
    return result.returncode == 1  # 1 = SAFE

if is_safe_for_llm("user_upload.pdf"):
    # Safe to process with LLM
    process_with_ai(document)
else:
    # Block or sanitize
    reject_document()
```

### 2. Batch Document Screening

```batch
@echo off
for %%f in (*.pdf *.docx) do (
    spytext --scan "%%f"
    if errorlevel 2 (
        echo ALERT: %%f contains hidden text
        move "%%f" quarantine\
    )
)
```

### 3. CI/CD Pipeline Integration

```yaml
# GitHub Actions example
- name: Scan documents for hidden text
  run: |
    for file in docs/*.pdf docs/*.docx; do
      spytext --scan "$file"
      if [ $? -eq 2 ]; then
        echo "::error::Hidden text detected in $file"
        exit 1
      fi
    done
```

## Building from Source

### Requirements

- Python 3.8+
- pip (Python package manager)

### Installation

```bash
# Clone repository
git clone https://github.com/AnikethMungara/SpyText.git
cd SpyText

# Install dependencies
pip install -r requirements.txt

# Optional: Install Tesseract OCR for scanned PDFs
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
# Linux: sudo apt-get install tesseract-ocr
# macOS: brew install tesseract
```

### Build Executable

```bash
# Install PyInstaller
pip install pyinstaller

# Build
python build_exe.py

# Output: dist/spytext.exe
```

## Configuration

Edit `config/settings.yaml` to adjust detection thresholds:

```yaml
visibility:
  contrast_threshold: 3.0        # WCAG AA minimum
  invisible_threshold: 1.5       # Near-invisible cutoff
  microscopic_font_size: 1.0     # Unreadable text
  small_font_size: 4.0           # Difficult to read

risk:
  invisible_threshold: 2         # Spans to trigger HIGH risk
  suspicious_threshold: 5        # Spans to trigger MEDIUM risk
```

## Privacy & Security

- **100% local processing** - No internet connection required
- **No telemetry** - No data collection or tracking
- **No cloud APIs** - All analysis happens on your machine
- **Files not modified** - Read-only analysis
- **Safe for confidential documents** - No data leaves your device

## Performance

Typical scan times:
- Small document (1-10 pages): < 1 second
- Medium document (11-50 pages): 1-5 seconds
- Large document (51-200 pages): 5-15 seconds
- Very large document (200+ pages): 15-60 seconds

Factors: Page count, text density, OCR requirements, file size

## Limitations

**What it CAN detect:**
- Native PDF text with metadata
- OCR text from scanned documents
- DOCX text with full formatting
- Color-based invisibility
- Size-based invisibility
- Position-based hiding
- Common prompt injection patterns

**What it CANNOT detect:**
- Steganography (data hidden in images)
- Encrypted or obfuscated content
- Novel prompt injection techniques
- Semantic attacks (misleading but visible text)
- Text in non-supported formats

## License

See LICENSE file for details.

## Author

Aniketh Mungara

## Support

- Issues: https://github.com/AnikethMungara/SpyText/issues
- Documentation: See README.md

---

**Warning:** SpyText is a security tool for detecting known hiding techniques. It should be part of a defense-in-depth strategy, not the only security measure. Always validate document sources and implement additional security controls.
