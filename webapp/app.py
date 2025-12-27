"""
SpyText Web Application
Flask-based web interface for document security scanning
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import yaml
import base64

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest import DocumentLoader
from src.extract import PDFExtractor
from src.extract.docx_extractor import DOCXExtractor
from src.detect import VisibilityAnalyzer, VisibilityStatus, RiskAggregator, RiskLevel

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'uploads'
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)

# Enable CORS for development
from flask import after_this_request

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

ALLOWED_EXTENSIONS = {'pdf', 'docx'}


def load_config():
    """Load configuration from settings.yaml."""
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def scan_document(file_path):
    """
    Scan document and return analysis results.

    Returns:
        dict with keys: status, risk_level, risk_score, total_spans,
                       hidden_spans, suspicious_spans, issues, full_text
    """
    config = load_config()

    try:
        # Load and extract
        loader = DocumentLoader(config)
        doc_path = loader.load(str(file_path))

        # Select appropriate extractor
        file_format = loader.detect_format(doc_path)
        if file_format == 'pdf':
            extractor = PDFExtractor(config)
        elif file_format == 'docx':
            extractor = DOCXExtractor(config)
        else:
            raise ValueError(f"Unsupported format: {file_format}")

        spans = extractor.extract(doc_path)

        # Analyze visibility
        analyzer = VisibilityAnalyzer(config)
        for span in spans:
            span.visibility_status = analyzer.analyze(span)
            span.contrast_ratio = analyzer.get_contrast_ratio(span)

        # Aggregate risk
        aggregator = RiskAggregator(config)
        risk_report = aggregator.analyze(spans)

        # Count visibility statuses
        visible_count = sum(1 for s in spans if s.visibility_status == VisibilityStatus.VISIBLE)
        suspicious_count = sum(1 for s in spans if s.visibility_status == VisibilityStatus.SUSPICIOUS)
        invisible_count = sum(1 for s in spans if s.visibility_status == VisibilityStatus.INVISIBLE)

        # Get hidden spans (invisible or suspicious)
        hidden_spans = [s for s in spans if s.visibility_status in
                       [VisibilityStatus.SUSPICIOUS, VisibilityStatus.INVISIBLE]]

        # Group by page and consolidate consecutive spans
        issues_by_page = {}
        for span in hidden_spans:
            page = span.page_number
            if page not in issues_by_page:
                issues_by_page[page] = []

            # Determine why it's hidden
            reasons = []
            if span.contrast_ratio and span.contrast_ratio < 1.5:
                reasons.append(f"nearly invisible (contrast: {span.contrast_ratio:.2f}:1)")
            elif span.contrast_ratio and span.contrast_ratio < 3.0:
                reasons.append(f"low contrast ({span.contrast_ratio:.2f}:1)")

            if span.font_size and span.font_size < 1.0:
                reasons.append(f"microscopic ({span.font_size}pt)")
            elif span.font_size and span.font_size < 4.0:
                reasons.append(f"very small ({span.font_size}pt)")

            issues_by_page[page].append({
                'text': span.text,
                'severity': 'INVISIBLE' if span.visibility_status == VisibilityStatus.INVISIBLE else 'SUSPICIOUS',
                'reasons': reasons,
                'bbox': span.bbox
            })

        # Consolidate issues - merge consecutive spans on same page with same severity
        for page in issues_by_page:
            consolidated = []
            current_group = None

            for issue in issues_by_page[page]:
                if current_group is None:
                    current_group = {
                        'text': issue['text'],
                        'severity': issue['severity'],
                        'reasons': set(issue['reasons'])
                    }
                elif issue['severity'] == current_group['severity']:
                    # Same severity - merge
                    current_group['text'] += ' ' + issue['text']
                    current_group['reasons'].update(issue['reasons'])
                else:
                    # Different severity - save current and start new
                    consolidated.append({
                        'text': current_group['text'],
                        'severity': current_group['severity'],
                        'reasons': list(current_group['reasons'])
                    })
                    current_group = {
                        'text': issue['text'],
                        'severity': issue['severity'],
                        'reasons': set(issue['reasons'])
                    }

            # Add the last group
            if current_group:
                consolidated.append({
                    'text': current_group['text'],
                    'severity': current_group['severity'],
                    'reasons': list(current_group['reasons'])
                })

            issues_by_page[page] = consolidated

        # Calculate risk score (0-100)
        risk_score = 0
        if invisible_count > 0:
            risk_score += min(invisible_count * 20, 60)
        if suspicious_count > 0:
            risk_score += min(suspicious_count * 5, 20)
        if risk_report.prompt_injection_detected:
            risk_score += 20
        risk_score = min(risk_score, 100)

        # Build issues list
        issues = []
        for page in sorted(issues_by_page.keys()):
            for issue in issues_by_page[page]:
                issues.append({
                    'page': page,
                    'text': issue['text'][:100] + ('...' if len(issue['text']) > 100 else ''),
                    'severity': issue['severity'],
                    'reasons': ', '.join(issue['reasons'])
                })

        # Get full document text for display with better formatting
        full_text_parts = []
        current_page = 1
        for span in spans:
            if span.page_number != current_page:
                full_text_parts.append(f"\n--- Page {span.page_number} ---\n")
                current_page = span.page_number
            full_text_parts.append(span.text)

        full_text = ' '.join(full_text_parts)

        # Determine status
        if len(hidden_spans) == 0 and not risk_report.prompt_injection_detected:
            status = 'SAFE'
        else:
            status = 'SUSPICIOUS'

        return {
            'status': status,
            'risk_level': risk_report.risk_level.value.upper(),
            'risk_score': risk_score,
            'total_spans': len(spans),
            'visible_spans': visible_count,
            'suspicious_spans': suspicious_count,
            'invisible_spans': invisible_count,
            'hidden_spans': len(hidden_spans),
            'issues': issues,
            'full_text': full_text,
            'prompt_injection': risk_report.prompt_injection_detected,
            'prompt_injection_patterns': risk_report.prompt_injection_patterns if risk_report.prompt_injection_detected else []
        }

    except Exception as e:
        return {
            'status': 'ERROR',
            'error': str(e),
            'risk_score': 0,
            'total_spans': 0,
            'issues': []
        }


@app.route('/')
def index():
    """Render main page."""
    print("DEBUG: Index page requested")
    return render_template('index.html')

@app.route('/test')
def test():
    """Test endpoint."""
    print("DEBUG: Test endpoint called")
    return jsonify({
        'message': 'Server is working!',
        'file_type': 'pdf',
        'file_url': '/test/file.pdf'
    })


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and scanning."""
    try:
        print("DEBUG: Upload endpoint called")

        if 'file' not in request.files:
            print("DEBUG: No file in request")
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        print(f"DEBUG: File received: {file.filename}")

        if file.filename == '':
            print("DEBUG: Empty filename")
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            print(f"DEBUG: Invalid file type: {file.filename}")
            return jsonify({'error': 'Invalid file type. Only PDF and DOCX allowed'}), 400

        # Save file with unique name to avoid conflicts
        filename = secure_filename(file.filename)
        import time
        unique_filename = f"{int(time.time())}_{filename}"
        filepath = app.config['UPLOAD_FOLDER'] / unique_filename
        print(f"DEBUG: Saving to: {filepath}")
        file.save(filepath)

        # Scan document
        print("DEBUG: Starting scan...")
        result = scan_document(filepath)
        print(f"DEBUG: Scan complete. Result type: {type(result)}")
        print(f"DEBUG: Result keys BEFORE: {list(result.keys())}")

        # Add file info to result
        print("DEBUG: Adding file info...")
        result['filename'] = filename
        result['file_url'] = f'/view/{unique_filename}'
        result['file_type'] = 'pdf' if filename.lower().endswith('.pdf') else 'docx'

        print(f"DEBUG: File type set to: {result['file_type']}")
        print(f"DEBUG: File URL set to: {result['file_url']}")
        print(f"DEBUG: Result keys AFTER: {list(result.keys())}")

        print("DEBUG: Returning jsonify...")
        return jsonify(result)
    except Exception as e:
        print(f"DEBUG: EXCEPTION in upload_file: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/view/<filename>')
def view_file(filename):
    """Serve uploaded file for viewing."""
    filepath = app.config['UPLOAD_FOLDER'] / secure_filename(filename)
    if filepath.exists():
        return send_file(filepath, mimetype='application/pdf' if filename.endswith('.pdf') else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    return "File not found", 404


if __name__ == '__main__':
    print("\n" + "="*60)
    print("SpyText Web App Starting...")
    print("="*60)
    print(f"URL: http://localhost:5000")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print("="*60 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
