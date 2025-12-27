// SpyText Web App - Client-side JavaScript

const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const scanningIndicator = document.getElementById('scanningIndicator');
const noResults = document.getElementById('noResults');
const resultsContainer = document.getElementById('resultsContainer');
const documentPlaceholder = document.getElementById('documentPlaceholder');
const documentViewer = document.getElementById('documentViewer');

// PDF.js viewer state
let pdfDoc = null;
let currentPage = 1;
let currentScale = 1.0;
const canvas = document.getElementById('pdfCanvas');
const ctx = canvas.getContext('2d');

// Upload area click
uploadArea.addEventListener('click', () => {
    fileInput.click();
});

// File input change
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

// Drag and drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');

    if (e.dataTransfer.files.length > 0) {
        handleFile(e.dataTransfer.files[0]);
    }
});

// Handle file upload and scanning
function handleFile(file) {
    // Validate file type
    const validExtensions = ['pdf', 'docx'];
    const fileExtension = file.name.split('.').pop().toLowerCase();

    if (!validExtensions.includes(fileExtension)) {
        alert('Invalid file type. Please upload a PDF or DOCX file.');
        return;
    }

    // Show scanning indicator
    uploadArea.style.display = 'none';
    scanningIndicator.style.display = 'flex';

    // Create form data
    const formData = new FormData();
    formData.append('file', file);

    // Upload and scan
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Hide scanning indicator
        scanningIndicator.style.display = 'none';
        uploadArea.style.display = 'flex';

        if (data.error) {
            alert(`Error: ${data.error}`);
            return;
        }

        // Debug logging
        console.log('Server response:', data);
        console.log('File type:', data.file_type);
        console.log('File URL:', data.file_url);

        // Display results
        displayResults(data);
    })
    .catch(error => {
        scanningIndicator.style.display = 'none';
        uploadArea.style.display = 'flex';
        alert(`Error: ${error.message}`);
    });
}

// Display scan results
function displayResults(data) {
    // Hide placeholder, show results
    noResults.style.display = 'none';
    resultsContainer.style.display = 'block';
    documentPlaceholder.style.display = 'none';
    documentViewer.style.display = 'flex';

    // Update risk score
    const scoreValue = document.getElementById('scoreValue');
    const scoreCircle = document.getElementById('scoreCircle');
    const statusBadge = document.getElementById('statusBadge');
    const riskLevel = document.getElementById('riskLevel');

    scoreValue.textContent = data.risk_score;

    // Set color based on risk
    scoreCircle.className = 'score-circle';
    statusBadge.className = 'status-badge';

    if (data.status === 'SAFE') {
        scoreCircle.classList.add('safe');
        statusBadge.classList.add('safe');
        statusBadge.textContent = 'SAFE';
        riskLevel.textContent = 'No security issues detected';
    } else if (data.risk_score >= 70) {
        scoreCircle.classList.add('critical');
        statusBadge.classList.add('critical');
        statusBadge.textContent = 'CRITICAL';
        riskLevel.textContent = data.risk_level;
    } else {
        scoreCircle.classList.add('suspicious');
        statusBadge.classList.add('suspicious');
        statusBadge.textContent = 'SUSPICIOUS';
        riskLevel.textContent = data.risk_level;
    }

    // Update stats
    document.getElementById('totalSpans').textContent = data.total_spans;
    document.getElementById('hiddenSpans').textContent = data.hidden_spans;

    // Update issues list
    const issuesList = document.getElementById('issuesList');
    issuesList.innerHTML = '';

    if (data.issues && data.issues.length > 0) {
        data.issues.forEach(issue => {
            const issueItem = document.createElement('div');
            issueItem.className = `issue-item ${issue.severity.toLowerCase()}`;

            issueItem.innerHTML = `
                <div class="issue-header">
                    <span class="issue-page">Page ${issue.page}</span>
                    <span class="issue-severity ${issue.severity.toLowerCase()}">${issue.severity}</span>
                </div>
                <div class="issue-text">${escapeHtml(issue.text)}</div>
                <div class="issue-reasons">${issue.reasons}</div>
            `;

            issuesList.appendChild(issueItem);
        });
    } else {
        issuesList.innerHTML = '<p style="color: #666; font-size: 0.9rem;">No suspicious text detected</p>';
    }

    // Add prompt injection warning if detected
    if (data.prompt_injection) {
        const warningItem = document.createElement('div');
        warningItem.className = 'issue-item invisible';
        warningItem.innerHTML = `
            <div class="issue-header">
                <span class="issue-page">⚠️ WARNING</span>
                <span class="issue-severity invisible">ATTACK DETECTED</span>
            </div>
            <div class="issue-text">Possible prompt injection patterns detected!</div>
            <div class="issue-reasons">Patterns: ${data.prompt_injection_patterns.join(', ')}</div>
        `;
        issuesList.insertBefore(warningItem, issuesList.firstChild);
    }

    // Display document based on file type
    const documentTitle = document.getElementById('documentTitle');
    const pdfViewer = document.getElementById('pdfViewer');
    const textViewer = document.getElementById('textViewer');
    const documentContent = document.getElementById('documentContent');

    documentTitle.textContent = data.filename || 'Document Preview';

    console.log('Checking file type for viewer...');
    console.log('data.file_type:', data.file_type);
    console.log('data.file_url:', data.file_url);
    console.log('Is PDF?', data.file_type === 'pdf' && data.file_url);

    if (data.file_type === 'pdf' && data.file_url) {
        console.log('Loading PDF viewer...');
        // Show PDF viewer
        pdfViewer.style.display = 'flex';
        textViewer.style.display = 'none';

        // Load PDF
        loadPDF(data.file_url);
    } else {
        console.log('Loading text viewer for DOCX...');
        // Show text viewer for DOCX
        pdfViewer.style.display = 'none';
        textViewer.style.display = 'block';

        console.log('Full text length:', data.full_text ? data.full_text.length : 0);

        if (data.full_text && data.full_text.trim()) {
            // Check if it contains page markers
            if (data.full_text.includes('--- Page')) {
                // Split by page markers
                const sections = data.full_text.split(/--- Page \d+ ---/);
                documentContent.innerHTML = sections
                    .map((section, idx) => {
                        if (idx === 0 && !section.trim()) return '';
                        const pageNum = idx;
                        return `
                            ${idx > 0 ? `<div class="page-break">Page ${pageNum}</div>` : ''}
                            <div class="page-content">${escapeHtml(section.trim())}</div>
                        `;
                    })
                    .join('');
            } else {
                // Just display as continuous text
                documentContent.innerHTML = `<div class="page-content">${escapeHtml(data.full_text)}</div>`;
            }
        } else {
            documentContent.innerHTML = '<p style="color: #666; font-style: italic;">No text content available</p>';
        }
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
