
const RecurringManager = {

    // --- State ---
    currentMandantId: null,

    init: function () {
        const urlParams = new URLSearchParams(window.location.search);
        this.currentMandantId = urlParams.get('id');

        if (this.currentMandantId) {
            this.loadRecurring();
        }
    },

    // --- API Interactions ---

    loadRecurring: async function () {
        try {
            const list = document.getElementById('recurringList');
            if (!list) return;

            list.innerHTML = '<div class="loading"><div class="spinner"></div><p>Lade Abos...</p></div>';

            const res = await fetch(`https://meinbusiness-production.up.railway.app/api/mandanten/${this.currentMandantId}/recurring`);
            const data = await res.json();

            this.renderList(data);

        } catch (e) {
            console.error("Error loading recurring:", e);
            document.getElementById('recurringList').innerHTML = `<p class="error">Fehler: ${e}</p>`;
        }
    },

    saveRecurring: async function () {
        const kundeSelect = document.getElementById('recKunde');
        const kunde = kundeSelect.value;
        const beschreibung = document.getElementById('recDesc').value;
        const betrag = document.getElementById('recAmount').value;
        const interval = document.getElementById('recInterval').value;
        const start = document.getElementById('recStart').value;

        if (!kunde || !beschreibung || !betrag || !start) {
            alert("Bitte alle Felder ausfüllen!");
            return;
        }

        const payload = {
            kunde: kunde,
            beschreibung: beschreibung,
            betrag: betrag,
            intervall: interval,
            start_datum: start
        };

        try {
            const res = await fetch(`https://meinbusiness-production.up.railway.app/api/mandanten/${this.currentMandantId}/recurring`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await res.json();

            if (result.success) {
                alert("✅ Abo erfolgreich angelegt!");
                this.closeModal();
                this.loadRecurring();
            } else {
                alert("Fehler: " + result.error);
            }
        } catch (e) {
            alert("Fehler: " + e);
        }
    },

    deleteRecurring: async function (id) {
        if (!confirm("Möchten Sie dieses Abo wirklich löschen?")) return;

        try {
            const res = await fetch(`https://meinbusiness-production.up.railway.app/api/mandanten/${this.currentMandantId}/recurring/${id}`, {
                method: 'DELETE'
            });
            const result = await res.json();

            if (result.success) {
                this.loadRecurring();
            } else {
                alert("Fehler beim Löschen: " + result.error);
            }
        } catch (e) {
            alert("Systemfehler: " + e);
        }
    },

    // --- UI Helpers ---

    renderList: function (data) {
        const list = document.getElementById('recurringList');
        if (!data || data.length === 0) {
            list.innerHTML = '<div class="no-data"><p>Keine wiederkehrenden Rechnungen gefunden.</p></div>';
            return;
        }

        let html = '<table class="op-table"><thead><tr><th>Kunde</th><th>Beschreibung</th><th>Betrag</th><th>Intervall</th><th>Nächste Fälligkeit</th><th>Aktion</th></tr></thead><tbody>';

        data.forEach(entry => {
            // Check status (fällig?)
            const today = new Date().toISOString().split('T')[0];
            const isDue = entry.naechste_faelligkeit <= today;
            const dueStyle = isDue ? 'color: var(--danger); font-weight: bold;' : '';
            const dueText = isDue ? '⚠️ FÄLLIG' : '';

            html += `
                <tr>
                    <td><strong>${entry.kunde}</strong></td>
                    <td>${entry.beschreibung}</td>
                    <td>${parseFloat(entry.betrag).toFixed(2)} €</td>
                    <td>${this.formatInterval(entry.intervall)}</td>
                    <td style="${dueStyle}">${this.formatDate(entry.naechste_faelligkeit)} ${dueText}</td>
                    <td>
                        <button class="btn btn-sm btn-danger" onclick="RecurringManager.deleteRecurring('${entry.id}')">🗑️</button>
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        list.innerHTML = html;
    },

    openModal: function () {
        document.getElementById('recurringModal').style.display = 'flex';
        // Kunden laden (Reuse Logic from detail.js or invoice.js logic)
        // Einfachheitshalber laden wir die Kundenliste hier frisch, wenn möglich
        // Aber wir greifen auf die globale Variable 'allKunden' zu, falls verfügbar in detail.js
        this.populateKundenSelect();

        // Default datum heute
        document.getElementById('recStart').value = new Date().toISOString().split('T')[0];
    },

    closeModal: function () {
        document.getElementById('recurringModal').style.display = 'none';
        document.getElementById('recForm').reset();
    },

    populateKundenSelect: async function () {
        const select = document.getElementById('recKunde');
        select.innerHTML = '<option value="">Lade Kunden...</option>';

        try {
            const res = await fetch(`https://meinbusiness-production.up.railway.app/api/mandanten/${this.currentMandantId}/kunden`);
            const data = await res.json();

            // API returns { kunden: [...] }
            const kundenList = data.kunden || [];

            let html = '<option value="">Bitte wählen...</option>';
            kundenList.forEach(k => {
                html += `<option value="${k.Firma || k.firma}">${k.Firma || k.firma}</option>`;
            });
            select.innerHTML = html;
        } catch (e) {
            console.error(e);
            select.innerHTML = '<option>Fehler beim Laden</option>';
        }
    },

    formatInterval: function (val) {
        const map = {
            'monatlich': '📅 Monatlich',
            'quartalsweise': '🗓️ Quartalsweise',
            'jaehrlich': '🎄 Jährlich'
        };
        return map[val] || val;
    },

    formatDate: function (dateStr) {
        if (!dateStr) return "-";
        const parts = dateStr.split('-');
        if (parts.length !== 3) return dateStr;
        return `${parts[2]}.${parts[1]}.${parts[0]}`;
    }
};

// Auto-Init if on detail page
if (window.location.pathname.endsWith('detail.html')) {
    document.addEventListener('DOMContentLoaded', () => {
        // Starte Init verzögert, damit ID da ist
        setTimeout(() => RecurringManager.init(), 500);
    });
}
