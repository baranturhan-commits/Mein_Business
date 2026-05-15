
// --- LIEFERSCHEIN MODAL LOGIC (Merged) ---
console.log("Lieferschein Logic loaded");

window.LieferscheinModal = {
    init: function () {
    },

    open: function () {
        const modal = document.getElementById('lieferscheinModal');
        if (!modal) {
            console.error("Modal not found:IEFERSCHEIN");
            alert("Fehler: Lieferschein-Modal nicht gefunden!");
            return;
        }

        // Reset Steps
        document.querySelectorAll('#lieferscheinModal .step-content').forEach(el => el.classList.remove('active'));
        const step1 = document.getElementById('ls-step-1');
        if (step1) step1.classList.add('active');

        this.loadKunden();
        this.loadAngebote();

        modal.style.display = 'block';
        modal.classList.remove('hidden');
    },

    close: function () {
        const modal = document.getElementById('lieferscheinModal');
        if (modal) {
            modal.style.display = 'none';
            modal.classList.add('hidden');
        }
    },

    getApiBaseUrl: function () {
        // Fallback or Global
        if (typeof API_BASE_URL !== 'undefined') return API_BASE_URL;
        return 'https://meinbusiness-production.up.railway.app/api';
    },

    loadKunden: function () {
        const mandantId = new URLSearchParams(window.location.search).get('mandant') || new URLSearchParams(window.location.search).get('id');
        if (!mandantId) {
            alert("Kein Mandant ausgewählt! (URL Parameter 'id' oder 'mandant' fehlt)");
            return;
        }

        const url = `${this.getApiBaseUrl()}/mandanten/${mandantId}/kunden`;
        console.log("Fetching Kunden from: " + url);

        fetch(url)
            .then(res => {
                if (!res.ok) throw new Error("HTTP " + res.status);
                return res.json();
            })
            .then(data => {
                const select = document.getElementById('ls-kunde-select');
                if (!select) return;
                select.innerHTML = '<option value="">Bitte wählen...</option>';

                const list = data.kunden || [];
                list.forEach(k => {
                    const company = k.Firma || k.firma;
                    if (company) {
                        select.innerHTML += `<option value="${company}">${company}</option>`;
                    }
                });
            })
            .catch(err => {
                console.error(err);
                alert("Fehler Kunden laden: " + err);
            });
    },

    loadAngebote: function () {
        const mandantId = new URLSearchParams(window.location.search).get('mandant') || new URLSearchParams(window.location.search).get('id');
        if (!mandantId) return;

        const url = `${this.getApiBaseUrl()}/mandanten/${mandantId}/angebote`;

        fetch(url)
            .then(res => {
                if (!res.ok) throw new Error("HTTP " + res.status);
                return res.json();
            })
            .then(data => {
                const select = document.getElementById('ls-angebot-select');
                if (!select) return;
                select.innerHTML = '<option value="">Kein Angebot (Manuell)</option>';

                const list = data.angebote || [];

                list.forEach(a => {
                    const nr = a.Nummer || a.nummer;
                    const kunde = a.Kunde || a.kunde;
                    const datum = a.Datum || a.datum;

                    if (nr) {
                        select.innerHTML += `<option value="${nr}" data-kunde="${kunde}">${nr} - ${kunde} (${datum})</option>`;
                    }
                });
            })
            .catch(err => {
                console.error(err);
                alert("Fehler Angebote laden: " + err);
            });
    },

    onAngebotSelect: function () {
        const select = document.getElementById('ls-angebot-select');
        const nr = select.value;
        const kundeSelect = document.getElementById('ls-kunde-select');

        if (!nr) return;

        const option = select.options[select.selectedIndex];
        const kunde = option.getAttribute('data-kunde');
        if (kunde && kundeSelect) {
            kundeSelect.value = kunde;
        }

        // Fetch detailed positions
        const mandantId = new URLSearchParams(window.location.search).get('mandant') || new URLSearchParams(window.location.search).get('id');
        const url = `${this.getApiBaseUrl()}/mandanten/${mandantId}/angebot/${nr}`;

        fetch(url)
            .then(res => {
                if (!res.ok) throw new Error("Keine Details gefunden");
                return res.json();
            })
            .then(data => {
                const wrapper = document.getElementById('ls-positionen-wrapper');
                if (!wrapper) return;

                // Clear existing
                wrapper.innerHTML = '';

                if (data.positionen && data.positionen.length > 0) {
                    data.positionen.forEach(pos => {
                        this.addPosition(); // Adds empty row
                        const lastRow = wrapper.lastElementChild;
                        const descInput = lastRow.querySelector('.pos-desc');
                        const mengeInput = lastRow.querySelector('.pos-menge'); // Note: addPosition uses 'pos-menge'
                        const unitInput = lastRow.querySelector('.pos-einheit');

                        if (descInput) {
                            // Combine details if Preisliste
                            let text = pos.bezeichnung || pos.Bezeichnung;
                            if (pos.preis_pos) text = `Pos ${pos.preis_pos} (aus Preisliste)`; // Fallback if name missing
                            descInput.value = text;
                        }
                        if (mengeInput) mengeInput.value = pos.menge || 1;
                        if (unitInput) unitInput.value = pos.einheit || pos.Einheit || 'Stk';
                    });
                } else {
                    // Fallback if empty data
                    throw new Error("Keine Positionen im Daten-Objekt");
                }
            })
            .catch(err => {
                console.log("Fallback to legacy copy: " + err);
                // Fallback for old offers without JSON detail
                const wrapper = document.getElementById('ls-positionen-wrapper');
                if (wrapper) {
                    wrapper.innerHTML = ''; // Reset
                    this.addPosition();
                    const lastRow = wrapper.lastElementChild;
                    const descInput = lastRow.querySelector('.pos-desc');
                    const unitInput = lastRow.querySelector('.pos-einheit');

                    if (descInput) descInput.value = `Positionen gemäß Angebot ${nr}`;
                    if (unitInput) unitInput.value = "Psch";
                }
            });
    },

    addPosition: function () {
        const wrapper = document.getElementById('ls-positionen-wrapper');
        if (!wrapper) return;

        const div = document.createElement('div');
        div.className = 'position-row';
        div.style.marginBottom = "5px";
        div.style.display = "flex";
        div.style.gap = "5px";

        div.innerHTML = `
            <input type="text" placeholder="Beschreibung" class="pos-desc" required style="flex:2">
            <input type="number" placeholder="Menge" class="pos-menge" value="1" step="0.1" required style="width:80px">
            <input type="text" placeholder="Einheit" class="pos-einheit" value="Stk" style="width:60px">
            <button type="button" class="btn-icon" onclick="this.parentElement.remove()" style="padding:5px">🗑️</button>
        `;
        wrapper.appendChild(div);
    },

    submit: function () {
        const mandantId = new URLSearchParams(window.location.search).get('mandant') || new URLSearchParams(window.location.search).get('id');

        const kundeEl = document.getElementById('ls-kunde-select');
        const angebotEl = document.getElementById('ls-angebot-select');

        const kunde = kundeEl ? kundeEl.value : null;
        const angebot = angebotEl ? angebotEl.value : null;

        const positionen = [];
        document.querySelectorAll('#ls-positionen-wrapper .position-row').forEach(row => {
            const desc = row.querySelector('.pos-desc').value;
            const menge = row.querySelector('.pos-menge').value;
            const einheit = row.querySelector('.pos-einheit').value;

            if (desc) {
                positionen.push({
                    bezeichnung: desc,
                    menge: menge,
                    einheit: einheit
                });
            }
        });

        if (!kunde || positionen.length === 0) {
            alert("Bitte Kunde und mindestens eine Position angeben.");
            return;
        }

        const btn = document.querySelector('#lieferscheinModal .btn-primary');
        if (btn) btn.innerText = "Erstelle...";

        const url = `${this.getApiBaseUrl()}/mandanten/${mandantId}/lieferschein`;

        fetch(url, {
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
                if (btn) btn.innerText = "Lieferschein erstellen";

                if (data.success) {
                    const fullUrl = this.getApiBaseUrl().replace('/api', '') + data.pdf_path;
                    window.open(fullUrl, '_blank');
                    this.close();
                } else {
                    alert("Fehler: " + data.error);
                }
            })
            .catch(err => {
                if (btn) btn.innerText = "Lieferschein erstellen";
                alert("Fehler: " + err);
            });
    }
};
