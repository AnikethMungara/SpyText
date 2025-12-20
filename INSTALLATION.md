# Installation Guide

## System Requirements

### Software Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Tesseract OCR engine (for scanned document support)

### Operating System Support

SpyText is designed to run on:
- Windows 10/11
- macOS 10.14 or later
- Linux (Ubuntu 20.04+, Debian 10+, or equivalent)

## Installing Tesseract OCR

Tesseract is required for optical character recognition of scanned documents.

### Windows

1. Download the latest installer from the [UB Mannheim Tesseract repository](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run the installer (tesseract-ocr-w64-setup-v5.x.x.exe)
3. During installation, note the installation path (typically `C:\Program Files\Tesseract-OCR`)
4. Add Tesseract to your system PATH:
   - Open System Properties > Environment Variables
   - Add the Tesseract installation directory to the PATH variable
5. Verify installation:
   ```cmd
   tesseract --version
   ```

### macOS

Install via Homebrew:

```bash
brew install tesseract
```

Verify installation:
```bash
tesseract --version
```

### Linux (Debian/Ubuntu)

Install via apt:

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

Verify installation:
```bash
tesseract --version
```

### Linux (Fedora/RHEL)

Install via dnf/yum:

```bash
sudo dnf install tesseract
# or
sudo yum install tesseract
```

## Installing SpyText

### Step 1: Clone or Download

If using git:
```bash
git clone <repository-url>
cd SpyText
```

Or download and extract the source archive.

### Step 2: Create Virtual Environment

Creating a virtual environment isolates SpyText dependencies from your system Python installation.

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal prompt.

### Step 3: Install Python Dependencies

With the virtual environment activated:

```bash
pip install -r requirements.txt
```

This will install:
- pdfplumber (PDF text extraction)
- pymupdf (PDF rendering and metadata)
- Pillow (image processing)
- pytesseract (OCR interface)
- opencv-python (computer vision)
- numpy (numerical operations)
- PyYAML (configuration)
- rich (CLI formatting)
- reportlab (test PDF generation)

### Step 4: Verify Installation

Run the CLI help command:

```bash
python -m src.cli --help
```

You should see the SpyText banner and usage information.

## Configuration

### Default Configuration

SpyText uses `config/settings.yaml` for configuration. The default settings are optimized for general use.

### Tesseract Language Data

By default, Tesseract includes English language data. To add support for other languages:

**Windows:**
1. Download language data from [tessdata repository](https://github.com/tesseract-ocr/tessdata)
2. Place `.traineddata` files in `C:\Program Files\Tesseract-OCR\tessdata`

**macOS:**
```bash
brew install tesseract-lang
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr-<lang>
# Example for French:
sudo apt-get install tesseract-ocr-fra
```

Update `config/settings.yaml`:
```yaml
extraction:
  ocr:
    language: "eng+fra"  # Multiple languages
```

## Troubleshooting

### Tesseract Not Found

**Error:** `pytesseract.pytesseract.TesseractNotFoundError`

**Solution:**
1. Verify Tesseract is installed: `tesseract --version`
2. Ensure Tesseract is in your PATH
3. On Windows, you may need to set the tesseract command path explicitly in your code

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'pdfplumber'`

**Solution:**
1. Ensure virtual environment is activated
2. Reinstall dependencies: `pip install -r requirements.txt`

### Permission Errors

**Error:** Permission denied when accessing files

**Solution:**
1. Ensure you have read permissions for input documents
2. On Linux/macOS, check file permissions: `ls -l <file>`
3. Adjust permissions if needed: `chmod 644 <file>`

### OCR Quality Issues

**Issue:** Poor text recognition from scanned documents

**Solution:**
1. Increase DPI in `config/settings.yaml`:
   ```yaml
   extraction:
     ocr:
       dpi: 600  # Higher quality, slower
   ```
2. Ensure scanned images are clear and high-resolution
3. Install additional language data if needed

## Updating

To update SpyText dependencies:

```bash
# Activate virtual environment first
pip install --upgrade -r requirements.txt
```

## Uninstallation

### Remove Virtual Environment

**Windows:**
```cmd
deactivate
rmdir /s venv
```

**macOS/Linux:**
```bash
deactivate
rm -rf venv
```

### Remove Tesseract (Optional)

**Windows:**
- Use "Add or Remove Programs" in Control Panel

**macOS:**
```bash
brew uninstall tesseract
```

**Linux:**
```bash
sudo apt-get remove tesseract-ocr
```

## Next Steps

After installation, see:
- [README.md](README.md) for project overview
- [config/settings.yaml](config/settings.yaml) for configuration options
- Run `python -m src.cli --help` for usage information
