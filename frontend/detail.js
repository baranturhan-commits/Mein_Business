// Detail Page Logic
const API_BASE_URL = 'https://meinbusiness-production.up.railway.app/api';
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
        const files = Array.from(e.dataTransfer.files);
        if (files.length > 0) {
            handleBatchUpload(files);
        }
    });

    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        if (files.length > 0) {
            handleBatchUpload(files);
        }
    });
});

// Load Mandant Details
async function loadMandantDetails() {
    try {
        const response = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/stats`);
        const stats = await response.json();

        currentMandant = stats;
        window.isKleingewerbe = (stats.unternehmensform === 'Kleingewerbe');

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
// --- Batch Upload Logic ---

async function handleBatchUpload(files) {
    const statusDiv = document.getElementById('uploadStatus');
    const totalFiles = files.length;

    // Initial UI
    statusDiv.innerHTML = `
        <div class="batch-progress">
            <p><strong>📦 Upload ${totalFiles} Datei(en)...</strong></p>
            <div class="progress-bar">
                <div class="progress-fill" id="uploadProgressBar" style="width: 0%"></div>
            </div>
            <p id="uploadProgressText">0 von ${totalFiles} hochgeladen</p>
        </div>
        <div id="uploadResults" style="margin-top: 10px;"></div>
    `;

    const results = [];

    // Process sequentially
    for (let i = 0; i < totalFiles; i++) {
        const file = files[i];
        const progress = Math.round(((i + 1) / totalFiles) * 100);

        // Update UI
        document.getElementById('uploadProgressText').textContent = `Lade ${i + 1} von ${totalFiles}: ${file.name}`;

        try {
            const result = await uploadSingleFile(file);
            results.push({
                filename: file.name,
                success: result.success,
                message: result.message || result.error
            });
        } catch (error) {
            results.push({
                filename: file.name,
                success: false,
                message: "Netzwerkfehler"
            });
        }

        document.getElementById('uploadProgressBar').style.width = `${progress}%`;
    }

    // Finalize
    document.getElementById('uploadProgressBar').style.width = '100%';
    document.getElementById('uploadProgressText').textContent = `✅ Fertig!`;

    // Show Summary
    displayUploadResults(results);

    // Refresh lists if available
    if (typeof loadAusgaben === 'function') loadAusgaben();
}

async function uploadSingleFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mandant_id', mandantId);
    formData.append('category', 'Sonstiges'); // Default category

    const response = await fetch(`${API_BASE_URL}/upload/beleg`, {
        method: 'POST',
        body: formData
    });
    return await response.json();
}

function displayUploadResults(results) {
    const container = document.getElementById('uploadResults');
    const successCount = results.filter(r => r.success).length;
    const failCount = results.length - successCount;

    let html = `
        <div style="margin-top:10px; max-height:200px; overflow-y:auto; font-size:0.9rem;">
            <p><strong>Ergebnis:</strong> ${successCount} OK, ${failCount} Fehler</p>
            <ul style="list-style:none; padding:0;">
    `;

    results.forEach(r => {
        const icon = r.success ? '✅' : '❌';
        const color = r.success ? 'var(--success)' : 'var(--danger)';
        html += `<li style="color:${color}; margin-bottom:4px; display:flex; gap:5px;"><span>${icon}</span> <span><b>${r.filename}</b>: ${r.message}</span></li>`;
    });

    html += `</ul></div>`;

    if (results.length > 0) {
        html += `<button class="btn btn-sm btn-secondary" onclick="closeUploadModal()" style="margin-top:10px; width:100%">Schließen</button>`;
    }

    container.innerHTML = html;
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

// Backup Trigger
async function triggerManualBackup() {
    if (!confirm("Jetzt vollständiges Backup erstellen?")) return;

    try {
        const res = await fetch(`${API_BASE_URL}/backup/now`, { method: 'POST' });
        const data = await res.json();

        if (data.success) {
            alert(`✅ Backup erfolgreich!\nDatei: ${data.filename}\nGröße: ${data.size_mb} MB`);
        } else {
            alert("❌ Fehler: " + data.error);
        }
    } catch (e) {
        alert("❌ Netzwerkfehler: " + e);
    }
}

function formatDate(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString('de-DE');
}
