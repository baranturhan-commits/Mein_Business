// Invoice Modal Logic

const InvoiceModal = {
    modalId: 'invoiceModal',
    items: [],

    // Self-contained helpers
    getApiUrl: function () {
        return (typeof API_BASE_URL !== 'undefined') ? API_BASE_URL : 'http://localhost:5000/api';
    },

    getId: function () {
        const p = new URLSearchParams(window.location.search);
        return p.get('id') || p.get('mandant');
    },

    open: function () {
        document.getElementById(this.modalId).classList.remove('hidden');
        this.loadCustomers();
        this.loadOffers();
        this.loadNextNumber();
        this.renderItems();
    },

    close: function () {
        document.getElementById(this.modalId).classList.add('hidden');
        this.items = [];
        document.getElementById('inv-items-wrapper').innerHTML = '';
        document.getElementById('inv-total-netto').textContent = '0.00 €';
        document.getElementById('inv-protocol-input').value = '';
        document.getElementById('inv-import-status').innerHTML = '';
        // Reset Dates
        document.getElementById('inv-leistungs-von').value = '';
        document.getElementById('inv-leistungs-bis').value = '';
    },

    // --- Load Next Invoice Number ---
    loadNextNumber: async function () {
        const el = document.getElementById('inv-next-number');
        if (!el) return;
        try {
            const id = this.getId();
            const res = await fetch(`${this.getApiUrl()}/mandanten/${id}/rechnung/next-number`);
            const data = await res.json();
            el.textContent = data.next_number || '?';
        } catch (e) {
            el.textContent = '–';
        }
    },

    // --- Save Counter ---
    saveCounter: async function () {
        const input = document.getElementById('inv-counter-input');
        const val = parseInt(input.value);
        if (!val || val < 1) return alert('Bitte eine gültige Zahl ab 1 eingeben.');

        try {
            const id = this.getId();
            const res = await fetch(`${this.getApiUrl()}/mandanten/${id}/rechnung/set-counter`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ count: val })
            });
            const data = await res.json();
            if (data.success) {
                input.value = '';
                this.loadNextNumber(); // Refresh preview
            } else {
                alert('Fehler: ' + data.error);
            }
        } catch (e) {
            alert('Fehler: ' + e.message);
        }
    },

    // --- Data Loading ---
    loadCustomers: async function () {
        const select = document.getElementById('inv-kunde-select');
        select.innerHTML = '<option value="">Lade...</option>';
        try {
            const id = this.getId();
            if (!id) throw new Error("Keine Mandant ID gefunden");

            const url = `${this.getApiUrl()}/mandanten/${id}/kunden`;
            console.log("Invoice: Loading customers from", url);

            const res = await fetch(url);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);

            const data = await res.json();

            let html = '<option value="">- Kunde wählen -</option>';
            (data.kunden || []).forEach(k => {
                const firma = k.Firma || k.firma;
                html += `<option value="${firma}">${firma}</option>`;
            });
            select.innerHTML = html;
        } catch (e) {
            console.error("Fehler beim Laden der Kunden:", e);
            select.innerHTML = '<option value="">Fehler beim Laden (siehe Konsole)</option>';
        }
    },

    loadOffers: async function () {
        const select = document.getElementById('inv-angebot-select');
        select.innerHTML = '<option value="">Lade...</option>';
        try {
            const id = this.getId();
            if (!id) throw new Error("Keine Mandant ID gefunden");

            const url = `${this.getApiUrl()}/mandanten/${id}/angebote`;

            const res = await fetch(url);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);

            const data = await res.json();

            let html = '<option value="">- Kein Angebot gewählt -</option>';
            (data.angebote || []).forEach(a => {
                html += `<option value="${a.nummer}">${a.nummer} | ${a.kunde} (${a.datum || a.date})</option>`;
            });
            select.innerHTML = html;
        } catch (e) {
            console.error("Fehler beim Laden der Angebote:", e);
            select.innerHTML = '<option value="">Fehler beim Laden</option>';
        }
    },

    // --- Smart Import ---
    runSmartImport: async function () {
        const fileInput = document.getElementById('inv-protocol-input');
        const offerSelect = document.getElementById('inv-angebot-select');
        const statusDiv = document.getElementById('inv-import-status');

        if (!fileInput.files[0]) {
            statusDiv.innerHTML = '<span style="color:red">Bitte ein Protokoll auswählen!</span>';
            return;
        }

        const offerId = offerSelect.value; // e.g. "2025-001"
        const file = fileInput.files[0];

        statusDiv.innerHTML = '<span>🔄 Analysiere Datei & gleiche mit Angebot ab...</span>';

        const formData = new FormData();
        formData.append('file', file);
        if (offerId) {
            formData.append('angebot_nr', offerId);
        }

        try {
            const id = this.getId();
            const res = await fetch(`${this.getApiUrl()}/mandanten/${id}/protocol/scan`, {
                method: 'POST',
                body: formData
            });
            const result = await res.json();

            if (result.success && result.items) {
                // Merge items
                if (this.items.length === 0) {
                    this.items = result.items;
                } else {
                    this.items = [...this.items, ...result.items];
                }
                this.renderItems();
                statusDiv.innerHTML = `<span style="color:green">✅ ${result.items.length} Positionen importiert!</span>`;

                // Set customer from offer if selected
                if (offerId) {
                    const k = document.querySelector(`#inv-angebot-select option[value="${offerId}"]`).text;
                    const customerName = k.split('|')[1].trim().split('(')[0].trim();
                    // Try to set select
                    const custSelect = document.getElementById('inv-kunde-select');
                    for (let i = 0; i < custSelect.options.length; i++) {
                        if (custSelect.options[i].value === customerName) {
                            custSelect.selectedIndex = i;
                            break;
                        }
                    }
                }
            } else {
                statusDiv.innerHTML = `<span style="color:red">Fehler: ${result.error || 'Keine Daten'}</span>`;
            }
        } catch (e) {
            statusDiv.innerHTML = `<span style="color:red">Fehler: ${e.message}</span>`;
        }
    },

    // --- Items Management ---
    addPosition: function () {
        this.items.push({
            bezeichnung: '',
            menge: 1,
            einheit: 'Stk',
            einzelpreis: 0
        });
        this.renderItems();
    },

    removePosition: function (index) {
        this.items.splice(index, 1);
        this.renderItems();
    },

    updateItem: function (index, field, value) {
        this.items[index][field] = value;
        this.calcTotal();
    },

    renderItems: function () {
        const wrapper = document.getElementById('inv-items-wrapper');

        // Helper to safely format numbers
        const fmt = (v) => (v || 0);

        wrapper.innerHTML = this.items.map((item, index) => `
            <div class="form-row" style="background: rgba(255,255,255,0.05); padding: 10px; margin-bottom: 5px; border-radius: 4px;">
                <div class="form-group" style="flex: 2;">
                    <input type="text" placeholder="Bezeichnung" value="${item.bezeichnung || ''}" 
                        onchange="InvoiceModal.updateItem(${index}, 'bezeichnung', this.value)">
                </div>
                <div class="form-group" style="flex: 0.5;">
                    <input type="number" placeholder="Menge" value="${fmt(item.menge)}" step="0.1"
                        onchange="InvoiceModal.updateItem(${index}, 'menge', parseFloat(this.value))">
                </div>
                <div class="form-group" style="flex: 0.5;">
                    <input type="text" placeholder="Einh." value="${item.einheit || 'Stk'}"
                        onchange="InvoiceModal.updateItem(${index}, 'einheit', this.value)">
                </div>
                <div class="form-group" style="flex: 0.8;">
                    <input type="number" placeholder="Preis" value="${fmt(item.einzelpreis)}" step="0.01"
                        onchange="InvoiceModal.updateItem(${index}, 'einzelpreis', parseFloat(this.value))">
                </div>
                <button class="btn btn-danger small" onclick="InvoiceModal.removePosition(${index})" style="height: 38px;">🗑️</button>
            </div>
        `).join('');
        this.calcTotal();
    },

    calcTotal: function () {
        let total = 0;
        this.items.forEach(i => {
            const m = parseFloat(i.menge) || 0;
            const p = parseFloat(i.einzelpreis) || 0;
            total += m * p;
        });
        // Try to find formatPrice global, else fallback
        const fmtMoney = (typeof formatPrice === 'function') ? formatPrice : (v) => v.toFixed(2) + ' €';
        document.getElementById('inv-total-netto').textContent = fmtMoney(total);
    },

    submit: async function () {
        const kunde = document.getElementById('inv-kunde-select').value;
        const lVon = document.getElementById('inv-leistungs-von').value; // YYYY-MM-DD
        const lBis = document.getElementById('inv-leistungs-bis').value;

        // Convert Dates to German Format DD.MM.YYYY
        const formatDate = (d) => {
            if (!d) return '';
            const [y, m, d_] = d.split('-');
            return `${d_}.${m}.${y}`;
        };
        if (!kunde) return alert("Bitte Kunden wählen!");
        if (this.items.length === 0) return alert("Bitte Positionen hinzufügen!");

        // Calculate Total Netto
        let totalNetto = 0;
        this.items.forEach(i => {
            const m = parseFloat(i.menge) || 0;
            const p = parseFloat(i.einzelpreis) || 0;
            totalNetto += m * p;
        });

        // 1. Check for Duplicates
        try {
            const id = this.getId();
            const checkRes = await fetch(`${this.getApiUrl()}/mandanten/${id}/check-duplicate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    kunde: kunde,
                    total: totalNetto
                })
            });
            const checkResult = await checkRes.json();

            if (checkResult.duplicate && checkResult.matches.length > 0) {
                const match = checkResult.matches[0];
                const msg = `⚠️ ACHTUNG: MÖGLICHES DUPLIKAT! ⚠️\n\n` +
                    `Es gibt bereits eine ähnliche Rechnung:\n` +
                    `- Rechnung: ${match.nummer}\n` +
                    `- Kunde: ${match.kunde}\n` +
                    `- Betrag: ${match.betrag.toFixed(2)} €\n` +
                    `- Datum: ${match.datum} (vor ${match.days_ago} Tagen)\n\n` +
                    `Möchten Sie diese Rechnung TROTZDEM erstellen?`;

                if (!confirm(msg)) {
                    return; // Abbruch
                }
            }
        } catch (e) {
            console.warn("Duplikat-Check fehlgeschlagen (ignoriere):", e);
        }

        // 2. Submit Real Invoice
        const payload = {
            kunde: kunde,
            leistungs_von: formatDate(lVon),
            leistungs_bis: formatDate(lBis),
            items: this.items
        };

        try {
            const id = this.getId();
            const res = await fetch(`${this.getApiUrl()}/mandanten/${id}/rechnung`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await res.json();

            if (result.success) {
                alert(`Rechnung ${result.nummer} erstellt!`);
                this.close();
                window.location.reload(); // Refresh lists
            } else {
                alert("Fehler: " + result.error);
            }
        } catch (e) {
            alert("Fehler: " + e);
        }
    }
};
