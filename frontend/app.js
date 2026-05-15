// Mein Business - Frontend Application Logic
const API_BASE_URL = 'https://meinbusiness-production.up.railway.app/api';

// State
let allMandanten = [];
let dashboardData = null;

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing Mein Business Dashboard...');
    loadDashboard();
    updateLastUpdate();

    // Auto-refresh every 30 seconds
    setInterval(refreshData, 30000);
});

// Load Dashboard Data
async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard`);

        if (!response.ok) {
            throw new Error('API Server nicht erreichbar');
        }

        dashboardData = await response.json();

        // Update Summary
        updateSummary(dashboardData);

        // Load Mandanten
        allMandanten = dashboardData.mandanten_details || [];
        renderMandanten(allMandanten);

    } catch (error) {
        console.error('Fehler beim Laden:', error);
        showError('API Server nicht erreichbar. Starte: python backend/api_server.py');
    }
}

// Update Summary Cards
function updateSummary(data) {
    document.getElementById('totalMandanten').textContent = data.total_mandanten || 0;
    document.getElementById('totalEinnahmen').textContent = formatCurrency(data.total_einnahmen || 0);
    document.getElementById('totalOffen').textContent = formatCurrency(data.total_offen || 0);
}

// Render Mandanten Grid
function renderMandanten(mandanten) {
    const grid = document.getElementById('mandantenGrid');

    if (mandanten.length === 0) {
        grid.innerHTML = `
            <div class="loading">
                <p>Keine Mandanten gefunden</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = mandanten.map(mandant => createMandantCard(mandant)).join('');
}

// Create Mandant Card HTML
function createMandantCard(mandant) {
    const stats = mandant.stats || {};
    const einnahmen = stats.einnahmen || { total: 0, offen: 0 };
    const rechnungen = stats.rechnungen || {};
    const kunden = stats.kunden || 0;

    const total = einnahmen.total || 0;
    const offen = einnahmen.offen || 0;
    const bezahlt = total - offen;
    const percentPaid = total > 0 ? (bezahlt / total) * 100 : 100;

    const initial = mandant.name.charAt(0).toUpperCase();

    // Status Logik
    let statusClass = 'status-green'; // Alles gut
    let statusIcon = '🟢';
    let statusText = 'Alles erledigt';

    if (offen > 0) {
        // Hier könnte man noch prüfen wir alt die Rechnungen sind (wenn Backend das liefert)
        // Für jetzt: Offen > 0 ist Gelb, Offen > 1000 ist Rot (als Beispiel)
        if (offen > 1000) {
            statusClass = 'status-red';
            statusIcon = '🔴';
            statusText = 'Handlungsbedarf';
        } else {
            statusClass = 'status-yellow';
            statusIcon = '🟡';
            statusText = 'Zahlungen offen';
        }
    }

    return `
        <div class="mandant-card ${statusClass}" onclick="openMandantDetails('${mandant.id}')">
            <div class="mandant-header">
                <div class="mandant-avatar">${initial}</div>
                <div class="mandant-info">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3>${mandant.name}</h3>
                        <span title="${statusText}" style="cursor:help;">${statusIcon}</span>
                    </div>
                    <p class="mandant-id">${mandant.id}</p>
                </div>
            </div>
            
            <div class="mandant-stats">
                <div class="stat-item full-width" style="margin-bottom: 8px;">
                     <div style="display:flex; justify-content:space-between; font-size: 0.8em; margin-bottom: 2px; color: #aaa;">
                        <span>Fortschritt (Bezahlt)</span>
                        <span>${percentPaid.toFixed(0)}%</span>
                     </div>
                     <div style="width: 100%; height: 6px; background: #333; border-radius: 3px; overflow: hidden;">
                        <div style="width: ${percentPaid}%; height: 100%; background: var(--success); transition: width 0.3s;"></div>
                     </div>
                </div>

                <div class="stat-item">
                    <p class="stat-item-label">💰 Umsatz</p>
                    <p class="stat-item-value">${formatCurrency(total)}</p>
                </div>
                
                <div class="stat-item">
                    <p class="stat-item-label">⏳ Offen</p>
                    <p class="stat-item-value ${offen > 0 ? 'warning' : ''}">${formatCurrency(offen)}</p>
                </div>
                
                <div class="stat-item">
                    <p class="stat-item-label">📄 Rechnungen</p>
                    <p class="stat-item-value">${rechnungen.anzahl || 0}</p>
                </div>
                
                <div class="stat-item">
                    <p class="stat-item-label">👥 Kunden</p>
                    <p class="stat-item-value">${kunden}</p>
                </div>
            </div>
        </div>
    `;
}

// Filter Mandanten
function filterMandanten() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();

    const filtered = allMandanten.filter(mandant =>
        mandant.name.toLowerCase().includes(searchTerm) ||
        mandant.id.toLowerCase().includes(searchTerm)
    );

    renderMandanten(filtered);
}

// Open Mandant Details
function openMandantDetails(mandantId) {
    window.location.href = `detail.html?id=${mandantId}`;
}

// Refresh Data
async function refreshData() {
    console.log('🔄 Refreshing dashboard...');
    await loadDashboard();
    updateLastUpdate();
}

// Feierabend & Backup
async function finishWorkDay() {
    if (!confirm("🏁 Feierabend machen?\n\nDas System erstellt noch kurz ein Backup für dich.\nDanach kannst du den PC ausschalten.")) return;

    // Create custom overlay
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0'; overlay.style.left = '0';
    overlay.style.width = '100%'; overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(0,0,0,0.85)';
    overlay.style.zIndex = '9999';
    overlay.style.display = 'flex';
    overlay.style.flexDirection = 'column';
    overlay.style.justifyContent = 'center';
    overlay.style.alignItems = 'center';
    overlay.style.color = 'white';
    overlay.innerHTML = `
        <div class="spinner" style="width: 60px; height: 60px; border-width: 6px;"></div>
        <h2 style="margin-top: 20px;">Backup wird erstellt...</h2>
        <p>Bitte warten...</p>
    `;
    document.body.appendChild(overlay);

    try {
        const res = await fetch(`${API_BASE_URL}/backup/now`, { method: 'POST' });
        const data = await res.json();

        if (data.success) {
            overlay.innerHTML = `
                <div style="font-size: 80px;">✅</div>
                <h2>Fertig!</h2>
                <p>Backup: ${data.filename}</p>
                <p>Größe: ${data.size_mb} MB</p>
                <br>
                <h3>Schönen Feierabend! 👋</h3>
                <button class="btn btn-primary" onclick="location.reload()" style="margin-top: 20px;">Schließen</button>
            `;
        } else {
            overlay.innerHTML = `
                <div style="font-size: 80px;">❌</div>
                <h2>Fehler beim Backup</h2>
                <p>${data.error}</p>
                <button class="btn" onclick="location.reload()" style="margin-top: 20px;">Schließen</button>
            `;
        }
    } catch (e) {
        overlay.innerHTML = `
            <div style="font-size: 80px;">❌</div>
            <h2>Netzwerkfehler</h2>
            <p>${e}</p>
            <button class="btn" onclick="location.reload()" style="margin-top: 20px;">Schließen</button>
        `;
    }
}


// Feierabend & Backup
async function finishWorkDay() {
    if (!confirm("🛑 Feierabend machen?\n\nDas System erstellt noch kurz ein Backup für dich.\nDanach kannst du den PC ausschalten.")) return;

    // Create custom overlay
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0'; overlay.style.left = '0';
    overlay.style.width = '100%'; overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(0,0,0,0.85)';
    overlay.style.zIndex = '9999';
    overlay.style.display = 'flex';
    overlay.style.flexDirection = 'column';
    overlay.style.justifyContent = 'center';
    overlay.style.alignItems = 'center';
    overlay.style.color = 'white';
    overlay.innerHTML = `
        <div class="spinner" style="width: 60px; height: 60px; border-width: 6px;"></div>
        <h2 style="margin-top: 20px;">Backup wird erstellt...</h2>
        <p>Bitte warten...</p>
    `;
    document.body.appendChild(overlay);

    try {
        const res = await fetch(`${API_BASE_URL}/backup/now`, { method: 'POST' });
        const data = await res.json();

        if (data.success) {
            overlay.innerHTML = `
                <div style="font-size: 80px;">✅</div>
                <h2>Fertig!</h2>
                <p>Backup: ${data.filename}</p>
                <p>Größe: ${data.size_mb} MB</p>
                <br>
                <h3>Schönen Feierabend! 👋</h3>
                <button class="btn btn-primary" onclick="location.reload()" style="margin-top: 20px;">Schließen</button>
            `;
        } else {
            overlay.innerHTML = `
                <div style="font-size: 80px;">❌</div>
                <h2>Fehler beim Backup</h2>
                <p>${data.error}</p>
                <button class="btn" onclick="location.reload()" style="margin-top: 20px;">Schließen</button>
            `;
        }
    } catch (e) {
        overlay.innerHTML = `
            <div style="font-size: 80px;">❌</div>
            <h2>Netzwerkfehler</h2>
            <p>${e}</p>
            <button class="btn" onclick="location.reload()" style="margin-top: 20px;">Schließen</button>
        `;
    }
}

// Open Backend Scripts
function openBackend(module) {
    let command = '';

    switch (module) {
        case 'invoice':
            command = 'python backend/03_Rechnungen/invoice.py';
            break;
        case 'scanner':
            command = 'python backend/02_Buchhaltung/scanner.py';
            break;
        case 'payments':
            command = 'python backend/03_Rechnungen/check_payments.py';
            break;
        case 'finance':
            command = 'python backend/04_Controlling/finance_check.py';
            break;
    }

    alert(`Terminal öffnen und ausführen:\n\n${command}`);
    // In einer erweiterten Version könnten hier WebSockets verwendet werden
}

// Utility Functions
function formatCurrency(value) {
    return new Intl.NumberFormat('de-DE', {
        style: 'currency',
        currency: 'EUR'
    }).format(value);
}

function updateLastUpdate() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('de-DE');
    document.getElementById('lastUpdate').textContent = timeString;
}

function showError(message) {
    const grid = document.getElementById('mandantenGrid');
    grid.innerHTML = `
        <div class="loading">
            <p style="color: var(--danger);">❌ ${message}</p>
        </div>
    `;
}

// Mandant Modal
function showMandantModal() {
    document.getElementById('mandantModal').classList.remove('hidden');
}

function closeMandantModal() {
    document.getElementById('mandantModal').classList.add('hidden');
    document.getElementById('mandantForm').reset();
    document.getElementById('mandantStatus').innerHTML = '';
}

async function submitMandant(event) {
    event.preventDefault();

    const formData = {
        firma: document.getElementById('mandantFirma').value.trim(),
        unternehmensform: document.getElementById('mandantFormTyp').value,
        strasse: document.getElementById('mandantStrasse').value.trim(),
        ort: document.getElementById('mandantOrt').value.trim(),
        geschaeftsfuehrer: document.getElementById('mandantGF').value.trim(),
        ustid: document.getElementById('mandantUStId') ? document.getElementById('mandantUStId').value.trim() : '',
        steuernummer: document.getElementById('mandantSteuernummer') ? document.getElementById('mandantSteuernummer').value.trim() : '',
        iban: document.getElementById('mandantIBAN').value.trim(),
        bic: document.getElementById('mandantBIC').value.trim(),
        bank: document.getElementById('mandantBank').value.trim(),
        start_invoice_number: parseInt(document.getElementById('mandantStartNr')?.value) || 0
    };

    const statusDiv = document.getElementById('mandantStatus');
    statusDiv.innerHTML = '<p>🏢 Erstelle Mandanten...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/mandanten`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        const result = await response.json();

        if (result.success) {
            statusDiv.innerHTML = '<p class="success">✅ Mandant erfolgreich angelegt!</p>';
            setTimeout(() => {
                closeMandantModal();
                refreshData(); // Reload dashboard
            }, 1500);
        } else {
            statusDiv.innerHTML = `<p class="error">❌ ${result.error}</p>`;
        }
    } catch (error) {
        statusDiv.innerHTML = '<p class="error">❌ Fehler beim Erstellen</p>';
    }
}

// Export for console debugging
window.app = {
    loadDashboard,
    refreshData,
    createBackup,
    showMandantModal,
    closeMandantModal,
    submitMandant,
    allMandanten,
    dashboardData
};
