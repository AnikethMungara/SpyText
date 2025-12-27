// PDF Viewer functions

async function loadPDF(url) {
    try {
        pdfDoc = await pdfjsLib.getDocument(url).promise;
        document.getElementById('pageInfo').textContent = `Page 1 of ${pdfDoc.numPages}`;
        currentPage = 1;
        renderPage(currentPage);
        updatePageControls();
    } catch (error) {
        console.error('Error loading PDF:', error);
    }
}

async function renderPage(pageNum) {
    if (!pdfDoc) return;

    const page = await pdfDoc.getPage(pageNum);
    const viewport = page.getViewport({ scale: currentScale });

    canvas.height = viewport.height;
    canvas.width = viewport.width;

    const renderContext = {
        canvasContext: ctx,
        viewport: viewport
    };

    await page.render(renderContext).promise;
}

function updatePageControls() {
    document.getElementById('prevPage').disabled = currentPage <= 1;
    document.getElementById('nextPage').disabled = currentPage >= pdfDoc.numPages;
    document.getElementById('pageInfo').textContent = `Page ${currentPage} of ${pdfDoc.numPages}`;
    document.getElementById('zoomLevel').textContent = `${Math.round(currentScale * 100)}%`;
}

// Page navigation
document.getElementById('prevPage').addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        renderPage(currentPage);
        updatePageControls();
    }
});

document.getElementById('nextPage').addEventListener('click', () => {
    if (currentPage < pdfDoc.numPages) {
        currentPage++;
        renderPage(currentPage);
        updatePageControls();
    }
});

// Zoom controls
document.getElementById('zoomIn').addEventListener('click', () => {
    currentScale = Math.min(currentScale + 0.25, 3.0);
    renderPage(currentPage);
    updatePageControls();
});

document.getElementById('zoomOut').addEventListener('click', () => {
    currentScale = Math.max(currentScale - 0.25, 0.5);
    renderPage(currentPage);
    updatePageControls();
});
