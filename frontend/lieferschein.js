// lieferschein.js
console.log("Lieferschein Script loaded");
// alert("Script geladen!"); // Debugging
window.LieferscheinModal = {
    init: function () {
        // Event Listener für "Lieferschein erstellen" Button
        // Muss global verfügbar sein
    },

    open: function () {
        const modal = document.getElementById('lieferscheinModal');
        if (!modal) return;

        // Reset Steps
        document.querySelectorAll('#lieferscheinModal .step-content').forEach(el => el.classList.remove('active'));
        document.getElementById('ls-step-1').classList.add('active');

        LieferscheinModal.loadKunden();
        LieferscheinModal.loadAngebote(); // Für "Aus Angebot übernehmen"

        modal.style.display = 'block';
    },

    close: function () {
        document.getElementById('lieferscheinModal').style.display = 'none';
    },

    loadKunden: function () {
        const mandantId = new URLSearchParams(window.location.search).get('mandant');
        fetch(`/api/mandanten/${mandantId}/kunden`)
            .then(res => res.json())
            .then(data => {
                const select = document.getElementById('ls-kunde-select');
                select.innerHTML = '<option value="">Bitte wählen...</option>';
                (data.kunden || []).forEach(k => {
                    const company = k.Firma || k.firma;
                    if (company) {
                        select.innerHTML += `<option value="${company}">${company}</option>`;
                    }
                });
            });
    },

    loadAngebote: function () {
        const mandantId = new URLSearchParams(window.location.search).get('mandant');
        fetch(`/api/mandanten/${mandantId}/angebote`)
            .then(res => res.json())
            .then(data => {
                const select = document.getElementById('ls-angebot-select');
                select.innerHTML = '<option value="">Kein Angebot (Manuell)</option>';

                // Filtere Angebote? Oder alle anzeigen?
                (data.angebote || []).forEach(a => {
                    const nr = a.Nummer || a.nummer;
                    const kunde = a.Kunde || a.kunde;
                    const datum = a.Datum || a.datum;

                    if (nr) {
                        select.innerHTML += `<option value="${nr}" data-kunde="${kunde}">${nr} - ${kunde} (${datum})</option>`;
                    }
                });
            });
    },

    // Wenn Angebot gewählt wird -> Kunde vorausfüllen & Positionen laden (simuliert)
    onAngebotSelect: function () {
        const select = document.getElementById('ls-angebot-select');
        const nr = select.value;
        const kundeSelect = document.getElementById('ls-kunde-select');

        if (!nr) return;

        // Kunde setzen
        const option = select.options[select.selectedIndex];
        const kunde = option.getAttribute('data-kunde');
        if (kunde) {
            kundeSelect.value = kunde;
        }

        // TODO: Positionen aus Angebot laden wäre nice, aber backend gibt sie bei GET /angebote nicht mit zurück.
        // Wir müssten das PDF parsen oder Positionen extra speichern.
        // Workaround: Textfeld "Positionen werden aus Angebot übernommen"
        // Oder wir lassen den User Positionen einfach eintippen.
        // IMPROVEMENT: Wir sollten Positionen im Backend besser speichern (JSON File statt nur Excel).
        // Für jetzt: Manuelle Eingabe oder "Siehe Angebot".
    },

    addPosition: function () {
        const wrapper = document.getElementById('ls-positionen-wrapper');
        const searchInput = document.getElementById('ls-preissuche');

        const div = document.createElement('div');
        div.className = 'position-row';
        div.innerHTML = `
            <input type="text" placeholder="Beschreibung" class="pos-desc" required>
            <input type="number" placeholder="Menge" class="pos-menge" value="1" step="0.1" required>
            <input type="text" placeholder="Einheit" class="pos-einheit" value="Stk">
            <button type="button" class="btn-icon" onclick="this.parentElement.remove()">🗑️</button>
        `;
        wrapper.appendChild(div);
    },

    submit: function () {
        const mandantId = new URLSearchParams(window.location.search).get('mandant');

        const kunde = document.getElementById('ls-kunde-select').value;
        const angebot = document.getElementById('ls-angebot-select').value;

        const positionen = [];
        document.querySelectorAll('#ls-positionen-wrapper .position-row').forEach(row => {
            positionen.push({
                bezeichnung: row.querySelector('.pos-desc').value,
                menge: row.querySelector('.pos-menge').value,
                einheit: row.querySelector('.pos-einheit').value
            });
        });

        if (!kunde || positionen.length === 0) {
            alert("Bitte Kunde und mindestens eine Position angeben.");
            return;
        }

        fetch(`/api/mandanten/${mandantId}/lieferschein`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                kunde: kunde,
                angebot: angebot,
                positionen: positionen
            })
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    // PDF öffnen
                    window.open(data.pdf_path, '_blank');
                    LieferscheinModal.close();
                    // Refresh list if we have one (future sprint)
                } else {
                    alert("Fehler: " + data.error);
                }
            })
            .catch(err => alert("Fehler: " + err));
    }
};
