
// Protocol Scanner & Invoice Generation Logic

function showProtocolUploadModal() {
    const modal = document.getElementById('importModal');
    if (!modal) return;

    // Set Mode
    window.IMPORT_MODE = 'PROTOCOL';

    // Customize UI
    modal.querySelector('h2').innerText = "📠 Protokoll Scan -> Rechnung";
    const status = document.getElementById('importStatus');
    status.innerHTML = '';

    // Show Modal
    modal.classList.remove('hidden');

    // Hijack File Input
    const input = document.getElementById('importFileInput');
    input.onchange = async function (e) {
        if (window.IMPORT_MODE !== 'PROTOCOL') return;
        const file = e.target.files[0];
        if (!file) return;

        await scanProtocol(file);
    }
}

async function scanProtocol(file) {
    const status = document.getElementById('importStatus');
    status.innerHTML = '<div class="loading"><div class="spinner"></div><p>🤖 KI analysiert Handschrift...</p></div>';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const mandantId = new URLSearchParams(window.location.search).get('mandant') || new URLSearchParams(window.location.search).get('id');
        const res = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/protocol/scan`, {
            method: 'POST',
            body: formData
        });

        const data = await res.json();

        if (data.success) {
            status.innerHTML = '✅ Analyse fertig!';
            closeImportModal();
            showInvoiceEditor(data.items);
        } else {
            status.innerHTML = `<p class="error">❌ Fehler: ${data.error}</p>`;
        }

    } catch (err) {
        status.innerHTML = `<p class="error">❌ Netzwerkfehler: ${err}</p>`;
    }
}

// Reuse Angebot Modal for Invoice Editing?
// It's similar but we need "Rechnung erstellen" title and action.
// Let's create a dynamic Invoice Editor Overlay using the Angebot Modal structure if possible, 
// or just modify showAngebotModal to accept initial items and mode.

function showInvoiceEditor(scannedItems) {
    // 1. Open Angebot Modal
    showAngebotModal(); // This resets everything

    // 2. Customize Title
    document.querySelector('#angebotModal h2').innerText = "💰 Rechnung aus Protokoll";
    document.querySelector('#angebot-step-3 button.btn-primary').innerText = "Rechnung erstellen";
    document.querySelector('#angebot-step-3 button.btn-primary').onclick = submitInvoiceFromProtocol;

    // 3. Skip to Step 2 (Positions)
    // Wait for modal to init? 
    setTimeout(() => {
        // Pre-fill items
        window.angebotPositionen = scannedItems.map(item => ({
            bezeichnung: item.bezeichnung,
            menge: item.menge || 1,
            einheit: item.einheit || 'Stk',
            einzelpreis: 0.00 // User must enter price
        }));

        renderPositionenEditor();
        showAngebotStep(2);

        // Add a hint
        const list = document.getElementById('positionenList');
        const hint = document.createElement('div');
        hint.innerHTML = `<p style="background:#e3f2fd; padding:10px; border-radius:5px; margin-bottom:10px;">
            ℹ️ <b>Bitte Preise nachtragen!</b><br>
            Die KI hat ${scannedItems.length} Positionen gefunden. Bitte überprüfe die Mengen und trage die Einzelpreise ein.
        </p>`;
        list.prepend(hint);

        // Also modify the list rendering to show Input Fields for Price directly?
        // standard renderPositionenEditor (in angebot.js) shows text only?
        // Let's override renderPositionenEditor temporally or modify it to support inline editing?
        // For now, user has to delete and re-add? No that's bad UX.
        // Let's just modify the items array directly from the UI?

        // Easier: Just alert user to check.
        // We really need an editable table for this workflow.
        // Let's inject a custom editor into the list container.
        renderEditableInvoiceTable();

    }, 100);
}

function renderEditableInvoiceTable() {
    const list = document.getElementById('positionenList');

    let html = `
    <table class="op-table">
        <thead>
            <tr>
                <th>Menge</th>
                <th>Einheit</th>
                <th>Beschreibung</th>
                <th>Einzelpreis (€)</th>
                <th></th>
            </tr>
        </thead>
        <tbody>
    `;

    window.angebotPositionen.forEach((pos, idx) => {
        html += `
        <tr>
            <td><input type="number" class="inv-qty" data-idx="${idx}" value="${pos.menge}" step="0.1" style="width:60px"></td>
            <td><input type="text" class="inv-unit" data-idx="${idx}" value="${pos.einheit}" style="width:50px"></td>
            <td><input type="text" class="inv-desc" data-idx="${idx}" value="${pos.bezeichnung}" style="width:100%"></td>
            <td><input type="number" class="inv-price" data-idx="${idx}" value="${pos.einzelpreis}" step="0.01" style="width:80px" placeholder="0.00"></td>
            <td><button class="btn btn-sm btn-danger" onclick="removeInvPos(${idx})">🗑️</button></td>
        </tr>
        `;
    });

    html += `</tbody></table>
    <div style="margin-top:10px; text-align:right">
        <b>Zwischensumme: <span id="inv-subtotal">0.00</span> €</b>
    </div>`;

    list.innerHTML = html;

    // Add Listeners to update array
    list.querySelectorAll('input').forEach(input => {
        input.addEventListener('change', (e) => {
            const idx = e.target.getAttribute('data-idx');
            const field = e.target.className.split('-')[1]; // qty, unit, desc, price
            const val = e.target.value;

            if (field === 'qty') window.angebotPositionen[idx].menge = parseFloat(val);
            if (field === 'unit') window.angebotPositionen[idx].einheit = val;
            if (field === 'desc') window.angebotPositionen[idx].bezeichnung = val;
            if (field === 'price') window.angebotPositionen[idx].einzelpreis = parseFloat(val);

            updateInvTotals();
        });
    });

    updateInvTotals();
}

function updateInvTotals() {
    let sum = 0;
    window.angebotPositionen.forEach(p => {
        sum += (p.menge || 0) * (p.einzelpreis || 0);
    });
    const el = document.getElementById('inv-subtotal');
    if (el) el.innerText = sum.toFixed(2);
}

window.removeInvPos = function (idx) {
    window.angebotPositionen.splice(idx, 1);
    renderEditableInvoiceTable();
}

async function submitInvoiceFromProtocol() {
    // Validate
    if (!window.selectedKunde) {
        alert("Bitte Kunde in Schritt 1 wählen!");
        return;
    }

    if (window.angebotPositionen.length === 0) {
        alert("Keine Positionen!");
        return;
    }

    // Check for 0 prices
    const zeroPrices = window.angebotPositionen.filter(p => !p.einzelpreis || p.einzelpreis === 0);
    if (zeroPrices.length > 0) {
        if (!confirm(`Warnung: ${zeroPrices.length} Positionen haben 0,00€ Preis. Fortfahren?`)) return;
    }

    const statusDiv = document.getElementById('angebotStatus');
    statusDiv.innerHTML = '<p>📄 Erstelle Rechnung...</p>';

    try {
        const mandantId = new URLSearchParams(window.location.search).get('mandant') || new URLSearchParams(window.location.search).get('id');

        const response = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/rechnung`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                kunde: window.selectedKunde,
                items: window.angebotPositionen
            })
        });

        const result = await response.json();

        if (result.success) {
            statusDiv.innerHTML = `<p class="success">✅ Rechnung ${result.nummer} erstellt!</p>`;

            // Open PDF
            // API returns relative web path e.g. /api/pdf/...
            // We need full URL for window.open if on another port? 
            // Usually relative works if generated correctly.
            // But API returned full path?
            // Let's use the result.pdf_path directly if it starts with /api

            let url = result.pdf_path;
            if (!url.startsWith('http')) {
                url = API_BASE_URL.replace('/api', '') + url;
            }

            window.open(url, '_blank');

            setTimeout(() => {
                closeAngebotModal();
            }, 2000);
        } else {
            statusDiv.innerHTML = `<p class="error">❌ ${result.error}</p>`;
        }
    } catch (error) {
        statusDiv.innerHTML = `<p class="error">❌ Fehler: ${error}</p>`;
    }
}
