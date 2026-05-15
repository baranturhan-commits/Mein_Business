// Detail Page Extensions - OP-Check & Kunden Management

// Global State
let allInvoices = [];
let allKunden = [];
let paymentChanges = {};

// Tab Switching
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));

    // Show selected tab
    document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');

    // Load data if needed
    if (tabName === 'op') {
        loadOPCheck();
    } else if (tabName === 'kunden') {
        loadKunden();
    } else if (tabName === 'mitarbeiter') {
        if (typeof MitarbeiterManager !== 'undefined') MitarbeiterManager.loadList();
    } else if (tabName === 'ausgaben') {
        if (typeof AusgabenManager !== 'undefined') AusgabenManager.init();
    }
}

// OP-Check Functions
async function loadOPCheck() {
    try {
        const response = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/einnahmen`);
        const data = await response.json();

        allInvoices = data.invoices || [];
        renderOPCheck(allInvoices);

    } catch (error) {
        console.error('Fehler beim Laden:', error);
        document.getElementById('opCheckList').innerHTML = '<p class="error">Fehler beim Laden</p>';
    }
}

function renderOPCheck(invoices) {
    const list = document.getElementById('opCheckList');

    if (invoices.length === 0) {
        list.innerHTML = '<p class="no-data">Keine Rechnungen vorhanden</p>';
        return;
    }

    const html = `
        <table class="op-table">
            <thead>
                <tr>
                    <th>Status</th>
                    <th>Rechnung</th>
                    <th>Datum</th>
                    <th>Kunde</th>
                    <th>Betrag</th>
                    <th>Aktion</th>
                </tr>
            </thead>
            <tbody>
                ${invoices.map(inv => {
        const overdue = isOverdue(inv.Datum, inv.Status);
        const rowClass = inv.Status === 'Bezahlt' ? 'status-paid' : (overdue ? 'status-overdue' : 'status-open');

        return `
                    <tr class="${rowClass}">
                        <td>
                            <label class="checkbox-label">
                                <input type="checkbox" 
                                       id="inv-${inv.Rechnungsnummer}"
                                       ${inv.Status === 'Bezahlt' ? 'checked' : ''}
                                       onchange="togglePaymentStatus('${inv.Rechnungsnummer}', this.checked)">
                                <span>${inv.Status}</span>
                            </label>
                            ${overdue ? '<br><span class="badge-overdue">Überfällig</span>' : ''}
                        </td>
                        <td>${inv.Rechnungsnummer}</td>
                        <td>${inv.Datum}</td>
                        <td>${inv.Kunde}</td>
                        <td>${inv.Betrag_Brutto}€</td>
                        <td>
                            ${inv.Status === 'Offen' ?
                `<button class="btn btn-sm btn-warning" onclick="createMahnung('${inv.Rechnungsnummer}')">⚠️ Mahnung</button>
                 <button class="btn btn-sm btn-info" onclick="sendMahnungEmail('${inv.Rechnungsnummer}')" style="margin-left:5px;">📧 Senden</button>`
                : '-'}
                        </td>
                    </tr>
                    `
    }).join('')}
            </tbody>
        </table>
    `;

    list.innerHTML = html;
}

function isOverdue(dateStr, status) {
    if (status === 'Bezahlt' || !dateStr) return false;

    try {
        // Parse DD.MM.YYYY
        const parts = dateStr.split('.');
        if (parts.length !== 3) return false;

        const invDate = new Date(parts[2], parts[1] - 1, parts[0]);
        const now = new Date();

        // 14 Tage Zahlungsziel
        const diffTime = Math.abs(now - invDate);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        return (now > invDate && diffDays > 14);
    } catch (e) { return false; }
}

async function createMahnung(invoiceNum) {
    if (!confirm(`Mahnung für Rechnung ${invoiceNum} erstellen?`)) return;

    const mandantId = getMandantIdFromUrl();

    try {
        const res = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/invoices/generate-reminder`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                invoice_num: invoiceNum,
                level: 1 // Default to 1st reminder
            })
        });

        const data = await res.json();

        if (data.success && data.pdf_path) {
            // Open PDF
            if (window.viewPdf) {
                // Determine filename from path
                const parts = data.pdf_path.split('/');
                const filename = parts[parts.length - 1];
                window.viewPdf(data.pdf_path, filename);
            } else {
                window.open(`${API_BASE_URL.replace('/api', '')}${data.pdf_path}`, '_blank');
            }
            alert('Mahnung erfolgreich erstellt!');
        } else {
            alert('Fehler: ' + (data.error || 'Unbekannter Fehler'));
        }
    } catch (e) {
        console.error('Fehler:', e);
        alert('Netzwerkfehler beim Erstellen der Mahnung.');
    }
}

async function sendMahnungEmail(invoiceNum) {
    if (!confirm(`Mahnung für Rechnung ${invoiceNum} per E-Mail an den Kunden senden?`)) return;

    const mandantId = getMandantIdFromUrl();

    try {
        const res = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/invoices/send-reminder`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                invoice_num: invoiceNum,
                level: 1
            })
        });

        const data = await res.json();

        if (data.success) {
            alert(data.message || 'Mahnung erfolgreich versendet!');
        } else {
            alert('Fehler beim Senden: ' + (data.error || 'Unbekannter Fehler'));
        }
    } catch (e) {
        console.error('Fehler beim Senden:', e);
        alert('Netzwerkfehler beim Senden der Email.');
    }
}


function togglePaymentStatus(rechnungNr, isPaid) {
    const newStatus = isPaid ? 'Bezahlt' : 'Offen';
    paymentChanges[rechnungNr] = newStatus;

    // Visual feedback
    const label = document.querySelector(`#inv-${rechnungNr} + span`);
    if (label) {
        label.textContent = newStatus;
    }
}

async function savePaymentStatus() {
    if (Object.keys(paymentChanges).length === 0) {
        alert('Keine Änderungen zum Speichern');
        return;
    }

    try {
        for (const [rechnungNr, status] of Object.entries(paymentChanges)) {
            await fetch(`${API_BASE_URL}/mandanten/${mandantId}/einnahmen/${rechnungNr}/status`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status })
            });
        }

        alert(`✅ ${Object.keys(paymentChanges).length} Änderung(en) gespeichert!`);
        paymentChanges = {};

        // Reload
        loadOPCheck();
        // Refresh detail stats if available
        if (typeof loadMandantDetails === 'function') loadMandantDetails();

    } catch (error) {
        alert('❌ Fehler beim Speichern: ' + error.message);
    }
}

// --- Bank Upload Logic ---
function triggerBankUpload() {
    document.getElementById('bankUploadInput').click();
}

async function handleBankUpload(input) {
    if (!input.files || input.files.length === 0) return;

    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);

    // UI Feedback
    const btn = document.querySelector('[onclick="triggerBankUpload()"]');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<div class="spinner" style="width:16px;height:16px;"></div> Scanning...';
    btn.disabled = true;

    try {
        const mandantId = getMandantIdFromUrl();
        const res = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/op-check/scan`, {
            method: 'POST',
            body: formData
        });

        const data = await res.json();

        if (data.success) {
            let matchCount = 0;
            let matchDetails = [];

            data.matches.forEach(match => {
                const invId = match.invoice_id;
                const checkbox = document.getElementById(`inv-${invId}`);

                // Only check if not already checked
                if (checkbox && !checkbox.checked) {
                    checkbox.checked = true;
                    togglePaymentStatus(invId, true); // Trigger change tracking
                    matchCount++;
                    matchDetails.push(invId);
                }
            });

            if (matchCount > 0) {
                alert(`✅ ${matchCount} Rechnungen gefunden und markiert:\n\n${matchDetails.join('\n')}\n\nBitte "Änderungen speichern" klicken!`);
            } else {
                alert(`ℹ️ Keine offenen Rechnungen gefunden.\n(${data.transactions_found} Transaktionen gescannt)`);
            }
        } else {
            alert('❌ Fehler: ' + (data.error || 'Server Error'));
        }
    } catch (e) {
        console.error(e);
        alert('❌ Netzwerkfehler beim Upload');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
        input.value = ''; // Reset
    }
}


// Kunden Functions
async function loadKunden() {
    try {
        const response = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/kunden`);
        const data = await response.json();

        allKunden = data.kunden || [];
        renderKunden(allKunden);

    } catch (error) {
        console.error('Fehler beim Laden:', error);
        document.getElementById('kundenList').innerHTML = '<p class="error">Fehler beim Laden</p>';
    }
}

function renderKunden(kunden) {
    const list = document.getElementById('kundenList');

    if (kunden.length === 0) {
        list.innerHTML = '<p class="no-data">Keine Kunden vorhanden</p>';
        return;
    }

    const html = kunden.map(kunde => `
        <div class="kunde-card">
            <div class="kunde-icon">👤</div>
            <div class="kunde-info">
                <h4>${kunde.Firma}</h4>
                <p>${kunde.Email || 'Keine Email'}</p>
                <p class="kunde-anrede">${kunde.Anrede}</p>
            </div>
        </div>
    `).join('');

    list.innerHTML = html;
}

// Kunde Modal
function showKundeModal() {
    document.getElementById('kundeModal').classList.remove('hidden');
}

function closeKundeModal() {
    document.getElementById('kundeModal').classList.add('hidden');
    document.getElementById('kundeForm').reset();
    document.getElementById('kundeStatus').innerHTML = '';
}

async function submitKunde(event) {
    event.preventDefault();

    const firma = document.getElementById('kundeFirma').value.trim();
    const email = document.getElementById('kundeEmail').value.trim();
    const anrede = document.getElementById('kundeAnrede').value;
    const strasse = document.getElementById('kundeStrasse').value.trim();
    const plz = document.getElementById('kundePlz').value.trim();
    const ort = document.getElementById('kundeOrt').value.trim();

    const statusDiv = document.getElementById('kundeStatus');
    statusDiv.innerHTML = '<p>📤 Erstelle Kunde...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/kunden`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ firma, email, anrede, strasse, plz, ort })
        });

        const result = await response.json();

        if (result.success) {
            statusDiv.innerHTML = '<p class="success">✅ Kunde erstellt!</p>';
            setTimeout(() => {
                closeKundeModal();
                loadKunden(); // Refresh list
            }, 1500);
        } else {
            statusDiv.innerHTML = `<p class="error">❌ ${result.error}</p>`;
        }
    } catch (error) {
        statusDiv.innerHTML = '<p class="error">❌ Fehler beim Erstellen</p>';
    }
}

// Add to window for global access
window.switchTab = switchTab;
window.loadOPCheck = loadOPCheck;
window.savePaymentStatus = savePaymentStatus;
window.triggerBankUpload = triggerBankUpload;
window.handleBankUpload = handleBankUpload;
window.loadKunden = loadKunden;
window.showKundeModal = showKundeModal;
window.closeKundeModal = closeKundeModal;
window.submitKunde = submitKunde;
// Export Modal Logic
function showExportModal() {
    const m = document.getElementById('exportModal');
    if (m) m.classList.remove('hidden');
    // Set current date
    const now = new Date();
    const mSelect = document.getElementById('exportMonth');
    const ySelect = document.getElementById('exportYear');
    if (mSelect) mSelect.value = now.getMonth() + 1; // 1-12
    if (ySelect) ySelect.value = now.getFullYear();
}

function closeExportModal() {
    const m = document.getElementById('exportModal');
    if (m) m.classList.add('hidden');
    const status = document.getElementById('exportStatus');
    if (status) status.innerHTML = '';
}

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

async function startReport() {
    const month = document.getElementById('exportMonth').value;
    const year = document.getElementById('exportYear').value;
    const status = document.getElementById('exportStatus');
    const mandantId = getMandantIdFromUrl();

    if (!status) return;
    status.innerHTML = '<div class="spinner"></div> PDF Report wird generiert...';

    try {
        const response = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/report/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ month, year })
        });

        const data = await response.json();

        if (data.success) {
            status.innerHTML = '<p class="success">✅ Report erstellt!</p>';
            closeExportModal();
            // Assuming viewPdf is global from detail.js
            if (window.viewPdf) {
                window.viewPdf(data.path, data.filename);
            } else {
                // Fallback: Open in new tab
                window.open(`${API_BASE_URL}/pdf/${data.path}`, '_blank');
            }
        } else {
            status.innerHTML = `<p class="error">❌ Fehler: ${data.error}</p>`;
        }
    } catch (error) {
        status.innerHTML = `<p class="error">❌ Netzwerkfehler: ${error}</p>`;
    }
}

async function startExport() {
    const month = document.getElementById('exportMonth').value;
    const year = document.getElementById('exportYear').value;
    const status = document.getElementById('exportStatus');
    const mandantId = getMandantIdFromUrl();

    if (!status) return;
    status.innerHTML = '<div class="spinner"></div> Export wird erstellt...';

    try {
        const response = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/export`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ month, year })
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Buchhaltung_${mandantId}_${year}_${month}.zip`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            status.innerHTML = '<div class="success">Export erfolgreich heruntergeladen!</div>';
            setTimeout(closeExportModal, 2000);
        } else {
            const err = await response.json();
            throw new Error(err.error || 'Server Fehler');
        }
    } catch (e) {
        console.error(e);
        status.innerHTML = `<div class="error">Fehler: ${e.message}</div>`;
    }
}


// Report & Export Logic
async function startReport() {
    const month = document.getElementById('exportMonth').value;
    const year = document.getElementById('exportYear').value;
    const status = document.getElementById('exportStatus');
    const mandantId = getMandantIdFromUrl();

    if (!status) return;
    status.innerHTML = '<div class="spinner"></div> PDF Report wird generiert...';

    try {
        const response = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/report/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ month, year })
        });

        const data = await response.json();

        if (data.success) {
            status.innerHTML = '<p class="success">✅ Report erstellt!</p>';
            // Close modal after delay
            // setTimeout(closeExportModal, 1500); 
            // Better: Open PDF
            if (window.viewPdf) {
                // If we have a viewPdf helper
                // window.viewPdf(data.path, data.filename);
            }
            window.open(`https://meinbusiness-production.up.railway.app/api/pdf/${data.path}`, '_blank');
        } else {
            status.innerHTML = `<p class="error">❌ Fehler: ${data.error}</p>`;
        }
    } catch (error) {
        status.innerHTML = `<p class="error">❌ Netzwerkfehler: ${error}</p>`;
    }
}

// Feierabend
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

// Helper needed if not available globally
function getMandantIdFromUrl() {
    return new URLSearchParams(window.location.search).get('mandant') || new URLSearchParams(window.location.search).get('id');
}
