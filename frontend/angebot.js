// Angebots-Erstellung - Multi-Step Modal

let angebotStep = 1;
let selectedKunde = null;
let angebotPositionen = [];
let alleKunden = [];
let allePreisliste = [];

// Angebot Modal
async function showAngebotModal() {
    document.getElementById('angebotModal').classList.remove('hidden');
    angebotStep = 1;
    selectedKunde = null;
    angebotPositionen = [];
    document.getElementById('ang-leistungs-von').value = '';
    document.getElementById('ang-leistungs-bis').value = '';

    // Load Kunden & Preisliste
    await loadDataForAngebot();

    showAngebotStep(1);
}

function closeAngebotModal() {
    document.getElementById('angebotModal').classList.add('hidden');
    document.getElementById('angebotStatus').innerHTML = '';
}

async function loadDataForAngebot() {
    try {
        // Load Kunden
        const kundenResp = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/kunden`);
        const kundenData = await kundenResp.json();
        alleKunden = kundenData.kunden || [];

        // Load Preisliste
        const preisResp = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/preisliste`);
        const preisData = await preisResp.json();
        allePreisliste = preisData.positionen || [];

    } catch (error) {
        console.error('Fehler beim Laden:', error);
    }
}

function showAngebotStep(step) {
    angebotStep = step;

    // Hide all steps
    document.querySelectorAll('.angebot-step').forEach(s => s.classList.add('hidden'));

    // Show current step
    document.getElementById(`angebot-step-${step}`).classList.remove('hidden');

    // Render content
    if (step === 1) renderKundenAuswahl();
    if (step === 2) renderPositionenEditor();
    if (step === 3) renderAngebotPreview();
}

function renderKundenAuswahl() {
    const container = document.getElementById('kundenAuswahl');

    if (alleKunden.length === 0) {
        container.innerHTML = '<p>Keine Kunden vorhanden. Bitte erst Kunde anlegen!</p>';
        return;
    }

    const html = alleKunden.map(kunde => `
        <div class="kunde-option ${selectedKunde === kunde.Firma ? 'selected' : ''}" 
             onclick="selectKunde('${kunde.Firma}')">
            <h4>${kunde.Firma}</h4>
            <p>${kunde.Email || ''}</p>
        </div>
    `).join('');

    container.innerHTML = html;
}

function selectKunde(firma) {
    selectedKunde = firma;
    renderKundenAuswahl();
}

function nextToPositionen() {
    if (!selectedKunde) {
        alert('Bitte Kunde auswählen!');
        return;
    }
    showAngebotStep(2);
}

function renderPositionenEditor() {
    const list = document.getElementById('positionenList');

    const html = angebotPositionen.map((pos, idx) => `
        <div class="position-item">
            <span>${pos.menge}x ${pos.bezeichnung} @ ${pos.einzelpreis}€ = ${(pos.menge * pos.einzelpreis).toFixed(2)}€</span>
            <button class="btn btn-sm btn-danger" onclick="removePosition(${idx})">🗑️</button>
        </div>
    `).join('');

    list.innerHTML = html || '<p>Keine Positionen</p>';

    // Render Preisliste-Dropdown
    const select = document.getElementById('preislistenSelect');
    select.innerHTML = '<option value="">-- Position auswählen --</option>' +
        allePreisliste.map(pos =>
            `<option value="${pos.Pos}">${pos.Bezeichnung} (${pos.Einzelpreis}€/${pos.Einheit})</option>`
        ).join('');
}

function addPositionFromPreisliste() {
    const select = document.getElementById('preislistenSelect');
    const menge = parseFloat(document.getElementById('positionMenge').value) || 1;

    const posId = select.value;
    if (!posId) {
        alert('Bitte Position auswählen!');
        return;
    }

    const preisPos = allePreisliste.find(p => p.Pos == posId);
    if (!preisPos) return;

    angebotPositionen.push({
        bezeichnung: preisPos.Bezeichnung,
        menge: menge,
        einheit: preisPos.Einheit,
        einzelpreis: parseFloat(preisPos.Einzelpreis)
    });

    // Reset
    select.value = '';
    document.getElementById('positionMenge').value = '1';

    renderPositionenEditor();
}

function removePosition(idx) {
    angebotPositionen.splice(idx, 1);
    renderPositionenEditor();
}

function nextToPreview() {
    if (angebotPositionen.length === 0) {
        alert('Bitte mindestens eine Position hinzufügen!');
        return;
    }
    showAngebotStep(3);
}

function renderAngebotPreview() {
    let netto = 0;
    const posHtml = angebotPositionen.map(pos => {
        const gesamt = pos.menge * pos.einzelpreis;
        netto += gesamt;
        return `<tr>
            <td>${pos.bezeichnung}</td>
            <td>${pos.menge} ${pos.einheit}</td>
            <td>${pos.einzelpreis.toFixed(2)}€</td>
            <td>${gesamt.toFixed(2)}€</td>
        </tr>`;
    }).join('');

    const mwst = window.isKleingewerbe ? 0 : (netto * 0.19);
    const brutto = netto + mwst;

    const mwstRow = window.isKleingewerbe
        ? `<tr><td colspan="3">MwSt 0%:</td><td>${mwst.toFixed(2)}€</td></tr>`
        : `<tr><td colspan="3">MwSt 19%:</td><td>${mwst.toFixed(2)}€</td></tr>`;

    const html = `
        <h4>Kunde: ${selectedKunde}</h4>
        <table class="op-table">
            <thead>
                <tr><th>Bezeichnung</th><th>Menge</th><th>Einzel</th><th>Gesamt</th></tr>
            </thead>
            <tbody>
                ${posHtml}
                <tr><td colspan="3"><b>Netto:</b></td><td><b>${netto.toFixed(2)}€</b></td></tr>
                ${mwstRow}
                <tr><td colspan="3"><b>Brutto:</b></td><td><b>${brutto.toFixed(2)}€</b></td></tr>
            </tbody>
        </table>
    `;

    document.getElementById('angebotPreview').innerHTML = html;
}

async function submitAngebot() {
    const statusDiv = document.getElementById('angebotStatus');
    statusDiv.innerHTML = '<p>📄 Erstelle Angebot...</p>';

    try {
        const response = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/angebot`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                kunde: selectedKunde,
                leistungs_von: document.getElementById('ang-leistungs-von').value,
                leistungs_bis: document.getElementById('ang-leistungs-bis').value,
                positionen: angebotPositionen
            })
        });

        const result = await response.json();

        if (result.success) {
            statusDiv.innerHTML = `<p class="success">✅ Angebot ${result.nummer} erstellt! (${result.brutto.toFixed(2)}€)</p>`;

            // Open PDF with full URL
            const fullUrl = API_BASE_URL.replace('/api', '') + result.pdf_path;
            window.open(fullUrl, '_blank');

            setTimeout(() => {
                closeAngebotModal();
            }, 2000);
        } else {
            statusDiv.innerHTML = `<p class="error">❌ ${result.error}</p>`;
        }
    } catch (error) {
        statusDiv.innerHTML = '<p class="error">❌ Fehler beim Erstellen</p>';
    }
}

// Export
window.showAngebotModal = showAngebotModal;
window.closeAngebotModal = closeAngebotModal;
window.selectKunde = selectKunde;
window.nextToPositionen = nextToPositionen;
window.addPositionFromPreisliste = addPositionFromPreisliste;
window.removePosition = removePosition;
window.nextToPreview = nextToPreview;
window.submitAngebot = submitAngebot;
window.showAngebotStep = showAngebotStep;
