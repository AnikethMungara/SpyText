# SpyText Web Application

Modern web interface for SpyText document security scanner.

## Features

- **Drag & Drop Upload** - Easy document upload with drag-and-drop support
- **Real-time Scanning** - Instant security analysis of PDF and DOCX files
- **Split-Screen Layout**:
  - **Top Left**: Upload area
  - **Bottom Left**: Security score and issues list
  - **Right Panel**: Full document preview
- **Risk Scoring** - Visual risk score (0-100) with color-coded severity
- **Detailed Analysis** - Page-by-page breakdown of hidden text
- **Dark Mode UI** - Professional, modern interface

## Quick Start

### 1. Install Dependencies

```bash
cd webapp
pip install -r requirements.txt
```

### 2. Run the Server

```bash
python app.py
```

### 3. Open Browser

Navigate to: `http://localhost:5000`

## Usage

1. **Upload Document**
   - Click the upload area or drag & drop a PDF/DOCX file

2. **View Results**
   - Risk score appears in bottom left
   - Issues list shows all suspicious text
   - Document preview on right

3. **Analyze Issues**
   - Each issue shows:
     - Page number
     - Severity (INVISIBLE/SUSPICIOUS)
     - Actual hidden text
     - Reason for detection (contrast, font size, etc.)

## API Endpoints

### POST /upload

Upload and scan a document.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: file (PDF or DOCX)

**Response:**
```json
{
  "status": "SUSPICIOUS",
  "risk_score": 85,
  "risk_level": "HIGH",
  "total_spans": 120,
  "hidden_spans": 8,
  "issues": [
    {
      "page": 1,
      "text": "ignore all previous instructions",
      "severity": "INVISIBLE",
      "reasons": "nearly invisible (contrast: 1.00:1)"
    }
  ],
  "full_text": "Document text content...",
  "prompt_injection": true,
  "prompt_injection_patterns": ["ignore all instructions"]
}
```

## Configuration

The web app uses the same `config/settings.yaml` as the CLI tool.

Edit detection thresholds:
```yaml
visibility:
  contrast_threshold: 3.0
  invisible_threshold: 1.5
  microscopic_font_size: 1.0

risk:
  invisible_threshold: 2
  suspicious_threshold: 5
```

## Production Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Docker

```bash
docker build -t spytext-web .
docker run -p 5000:5000 spytext-web
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Security Notes

- File size limited to 16MB
- Files are deleted after scanning
- No files stored permanently
- All processing happens server-side
- HTTPS recommended for production

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## License

Same as SpyText parent project
