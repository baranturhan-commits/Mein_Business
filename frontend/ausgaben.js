
// Ausgaben Tab Logic
// Ensure API_BASE_URL is available
const USAGE_API_URL = (typeof API_BASE_URL !== 'undefined') ? API_BASE_URL : 'http://localhost:5000/api';

let allAusgabenData = [];

// Called from applyDocFilter in documents.js
function applyAusgabenFilter() {
    renderAusgaben();
}

function loadAusgaben() {
    fetchAusgaben();
}

async function fetchAusgaben() {
    try {
        const id = getMandantId();
        const response = await fetch(`${USAGE_API_URL}/mandanten/${id}/ausgaben`);
        const data = await response.json();
        allAusgabenData = data.ausgaben || [];
        renderAusgaben();
    } catch (error) {
        console.error("Error loading expenses:", error);
    }
}

function renderAusgaben() {
    const list = document.getElementById('ausgabenList');
    if (!list) return;

    // Filter temporär deaktiviert
    let filtered = allAusgabenData;
    /*
    if (typeof isItemInFilter === 'function') {
        filtered = allAusgabenData.filter(row => isItemInFilter(row, 'Datum'));
    }
    */

    if (filtered.length === 0) {
        list.innerHTML = '<div class="empty-state">Keine Ausgaben im gewählten Zeitraum</div>';
        return;
    }

    const html = `
            <table class="op-table">
                <thead>
                    <tr>
                        <th>Datum</th>
                        <th>Beleg-Nr.</th>
                        <th>Firma / Zweck</th>
                        <th>Kategorie</th>
                        <th style="text-align: right">Betrag (Brutto)</th>
                        <th>Beleg</th>
                    </tr>
                </thead>
                <tbody>
                    ${filtered.map((row, index) => {
        return `
                        <tr>
                            <td>${row.Datum || '-'}</td>
                            <td><small>${row['Beleg-Nr.'] || '-'}</small></td>
                            <td>
                                <strong>${row.Firma || ''}</strong><br>
                                <small>${row.Beschreibung || ''}</small>
                            </td>
                            <td><span class="badge">${row.Kategorie || 'Sonstiges'}</span></td>
                            <td style="text-align: right; font-weight: bold;">
                                ${formatMoney(row.Brutto || row.Betrag_Brutto)}
                            </td>
                            <td>
                                ${renderBelegButton(row, index)}
                            </td>
                        </tr>
                        `;
    }).join('')}
                </tbody>
            </table>
        `;
    list.innerHTML = html;
}

function renderBelegButton(row, index) {
    // Filename check
    const filename = row['PDF_Path'] || row['Beleg_Pfad'] || row['Beleg'];
    if (!filename || filename === 'None' || filename === '') return '<span style="color:#ccc">-</span>';

    const isPdf = filename.toLowerCase().endsWith('.pdf');
    const icon = isPdf ? '📄' : '🖼️';

    return `<button onclick="openBelegModal(${index})" class="btn btn-icon small" title="Details & Vorschau">${icon}</button>`;
}

function openBelegModal(index) {
    const row = allAusgabenData[index];
    if (!row) return;

    // 1. Details füllen
    const detailsContainer = document.getElementById('belegDataView');
    detailsContainer.innerHTML = `
            <div class="detail-row">
                <div class="detail-label">Datum</div>
                <div class="detail-value">${row.Datum || '-'}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Firma</div>
                <div class="detail-value">${row.Firma || '-'}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Beschreibung</div>
                <div class="detail-value">${row.Beschreibung || '-'}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Kategorie</div>
                <div class="detail-value"><span class="badge">${row.Kategorie || 'Sonstiges'}</span></div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Betrag (Brutto)</div>
                <div class="detail-value" style="color: var(--primary-color); font-size: 1.4rem;">
                    ${formatMoney(row.Brutto || row.Betrag_Brutto)}
                </div>
            </div>
             <div class="detail-row">
                <div class="detail-label">Netto / MwSt</div>
                <div class="detail-value" style="font-size: 0.9rem;">
                     ${formatMoney(row.Netto || row.Betrag_Netto)} + ${formatMoney(row.MwSt)} MwSt
                </div>
            </div>
        `;

    // 2. Bild / PDF laden
    const viewContainer = document.getElementById('belegView');
    let filename = row['PDF_Path'] || row['Beleg_Pfad'] || row['Beleg'];

    // Cleanup path
    if (filename && filename.includes('\\')) filename = filename.split('\\').pop();
    if (filename && filename.includes('/')) filename = filename.split('/').pop();

    const mandantId = getMandantId();
    // Pfadlogik: Immer in 'Belege'
    const url = `${USAGE_API_URL}/pdf/Mandanten/${mandantId}/Ausgaben/Belege/${filename}`;

    if (filename.toLowerCase().endsWith('.pdf')) {
        viewContainer.innerHTML = `<iframe src="${url}" title="Beleg PDF"></iframe>`;
    } else {
        viewContainer.innerHTML = `<img src="${url}" alt="Beleg Vorschau" onerror="this.onerror=null; this.src=''; this.parentElement.innerHTML='<p class=beleg-missing>Bild nicht gefunden<br><small>${filename}</small></p>'">`;
    }

    // 3. Modal zeigen
    document.getElementById('belegPreviewModal').style.display = 'flex';
}

// Global machen für HTML Zugriff
window.openBelegModal = openBelegModal;
window.closeBelegModal = function () {
    document.getElementById('belegPreviewModal').style.display = 'none';
    document.getElementById('belegView').innerHTML = ''; // Clear to stop video/audio/iframe
};

function formatMoney(val) {
    if (!val) return '0,00 €';
    // Handle "10,50" string or 10.50 float
    let num = val;
    if (typeof val === 'string') {
        num = parseFloat(val.replace(',', '.'));
    }
    if (isNaN(num)) return val;
    return num.toLocaleString('de-DE', { style: 'currency', currency: 'EUR' });
}

// Hook into switchTab
if (typeof window.switchTab === 'function') {
    const originalSwitchTab = window.switchTab;
    window.switchTab = function (tabName) {
        originalSwitchTab(tabName);
        if (tabName === 'ausgaben') {
            loadAusgaben();
        }
    }
}
