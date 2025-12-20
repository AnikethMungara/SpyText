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
