
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

    // Filter
    let filtered = allAusgabenData;
    if (typeof isItemInFilter === 'function') {
        filtered = allAusgabenData.filter(row => isItemInFilter(row, 'Datum'));
    }

    if (filtered.length === 0) {
        list.innerHTML = '<div class="empty-state">Keine Ausgaben im gewählten Zeitraum</div>';
        return;
    }

    const html = `
        <table class="op-table">
            <thead>
                <tr>
                    <th>Datum</th>
                    <th>Firma / Zweck</th>
                    <th>Kategorie</th>
                    <th style="text-align: right">Betrag (Brutto)</th>
                    <th>Beleg</th>
                </tr>
            </thead>
            <tbody>
                ${filtered.map(row => `
                    <tr>
                        <td>${row.Datum || '-'}</td>
                        <td>
                            <strong>${row.Firma || ''}</strong><br>
                            <small>${row.Beschreibung || ''}</small>
                        </td>
                        <td><span class="badge">${row.Kategorie || 'Sonstiges'}</span></td>
                        <td style="text-align: right; font-weight: bold;">
                            ${formatMoney(row.Betrag_Brutto)}
                        </td>
                        <td>
                            ${renderBelegLink(getMandantId(), row.Beleg_Pfad)}
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    list.innerHTML = html;
}

function renderBelegLink(mandantId, filename) {
    if (!filename || filename === 'None') return '-';
    // Endpoint to serve image: /api/pdf/Mandanten/<id>/Ausgaben/Belege/<filename> 
    // (Assuming api_server serves static there)
    const url = `${USAGE_API_URL}/pdf/Mandanten/${mandantId}/Ausgaben/Belege/${filename}`;
    return `<a href="${url}" target="_blank" class="btn btn-icon small" title="Beleg ansehen">👁️</a>`;
}

function formatMoney(val) {
    if (!val) return '0,00 €';
    return parseFloat(val).toLocaleString('de-DE', { style: 'currency', currency: 'EUR' });
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
