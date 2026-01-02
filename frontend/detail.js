// Detail Page Logic
const API_BASE_URL = 'http://localhost:5000/api';
const urlParams = new URLSearchParams(window.location.search);
const mandantId = urlParams.get('id');

let currentMandant = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    if (!mandantId) {
        alert('Kein Mandant ausgewählt!');
        window.location.href = 'index.html';
        return;
    }

    loadMandantDetails();
    loadRechnungen();

    // Upload Zone Events
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');

    uploadZone.addEventListener('click', () => fileInput.click());
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });
    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });
});

// Load Mandant Details
async function loadMandantDetails() {
    try {
        const response = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/stats`);
        const stats = await response.json();

        currentMandant = stats;

        // Update Title
        document.getElementById('mandantName').textContent = mandantId.replace('_', ' ');

        // Render Stats
        const statsHtml = `
            <div class="stat-card">
                <div class="stat-icon green">💰</div>
                <div class="stat-content">
                    <p class="stat-label">Einnahmen Total</p>
                    <h2 class="stat-value">${formatCurrency(stats.einnahmen.total)}</h2>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon orange">⏳</div>
                <div class="stat-content">
                    <p class="stat-label">Offen</p>
                    <h2 class="stat-value warning">${formatCurrency(stats.einnahmen.offen)}</h2>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon blue">📄</div>
                <div class="stat-content">
                    <p class="stat-label">Rechnungen</p>
                    <h2 class="stat-value">${stats.rechnungen.anzahl}</h2>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon purple">👥</div>
                <div class="stat-content">
                    <p class="stat-label">Kunden</p>
                    <h2 class="stat-value">${stats.kunden}</h2>
                </div>
            </div>
        `;

        document.getElementById('detailStats').innerHTML = statsHtml;

    } catch (error) {
        console.error('Fehler beim Laden:', error);
    }
}

// Load Rechnungen
async function loadRechnungen() {
    try {
        const response = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/rechnungen`);
        const data = await response.json();

        const list = document.getElementById('rechnungenList');

        if (data.rechnungen.length === 0) {
            list.innerHTML = '<p class="no-data">Keine Rechnungen gefunden</p>';
            return;
        }

        const html = data.rechnungen.map(rechnung => `
            <div class="rechnung-item" onclick="viewPdf('${rechnung.path}', '${rechnung.name}')">
                <div class="rechnung-icon">📄</div>
                <div class="rechnung-info">
                    <h4>${rechnung.name}</h4>
                    <p>${formatFileSize(rechnung.size)} • ${formatDate(rechnung.modified)}</p>
                </div>
                <button class="btn btn-icon">👁️</button>
            </div>
        `).join('');

        list.innerHTML = html;

    } catch (error) {
        console.error('Fehler beim Laden der Rechnungen:', error);
        document.getElementById('rechnungenList').innerHTML = '<p class="error">Fehler beim Laden</p>';
    }
}

// File Upload
async function handleFileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mandant_id', mandantId);
    formData.append('category', 'Sonstiges');

    const statusDiv = document.getElementById('uploadStatus');
    statusDiv.innerHTML = '<p>📤 Uploading...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/upload/beleg`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            statusDiv.innerHTML = '<p class="success">✅ ' + result.message + '</p>';
            setTimeout(() => {
                closeUploadModal();
                statusDiv.innerHTML = '';
            }, 2000);
        } else {
            statusDiv.innerHTML = '<p class="error">❌ ' + result.error + '</p>';
        }
    } catch (error) {
        statusDiv.innerHTML = '<p class="error">❌ Upload fehlgeschlagen</p>';
    }
}

// View PDF
function viewPdf(path, name) {
    const viewer = document.getElementById('pdfViewer');
    document.getElementById('pdfTitle').textContent = name;
    viewer.src = `${API_BASE_URL}/pdf/${path}`;
    document.getElementById('pdfModal').classList.remove('hidden');
}

// Modals
function showUploadModal() {
    document.getElementById('uploadModal').classList.remove('hidden');
}

function closeUploadModal() {
    document.getElementById('uploadModal').classList.add('hidden');
    document.getElementById('uploadStatus').innerHTML = '';
}

function closePdfModal() {
    document.getElementById('pdfModal').classList.add('hidden');
    document.getElementById('pdfViewer').src = '';
}

// Utilities
function formatCurrency(value) {
    return new Intl.NumberFormat('de-DE', {
        style: 'currency',
        currency: 'EUR'
    }).format(value);
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
}

function formatDate(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString('de-DE');
}
