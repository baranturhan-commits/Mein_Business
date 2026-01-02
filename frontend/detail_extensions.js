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
                </tr>
            </thead>
            <tbody>
                ${invoices.map(inv => `
                    <tr class="${inv.Status === 'Offen' ? 'status-open' : 'status-paid'}">
                        <td>
                            <label class="checkbox-label">
                                <input type="checkbox" 
                                       id="inv-${inv.Rechnungsnummer}"
                                       ${inv.Status === 'Bezahlt' ? 'checked' : ''}
                                       onchange="togglePaymentStatus('${inv.Rechnungsnummer}', this.checked)">
                                <span>${inv.Status}</span>
                            </label>
                        </td>
                        <td>${inv.Rechnungsnummer}</td>
                        <td>${inv.Datum}</td>
                        <td>${inv.Kunde}</td>
                        <td>${inv.Betrag_Brutto}€</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    list.innerHTML = html;
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
        loadMandantDetails(); // Refresh stats

    } catch (error) {
        alert('❌ Fehler beim Speichern: ' + error.message);
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

    const statusDiv = document.getElementById('kundeStatus');
    statusDiv.innerHTML = '<p>📤 Erstelle Kunde...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/kunden`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ firma, email, anrede })
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
window.loadKunden = loadKunden;
window.showKundeModal = showKundeModal;
window.closeKundeModal = closeKundeModal;
window.submitKunde = submitKunde;
window.togglePaymentStatus = togglePaymentStatus;
