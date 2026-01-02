
const MitarbeiterManager = {
    // Helper for API URL (handling file:// protocol)
    getApiUrl: function () {
        if (window.location.protocol === 'file:') {
            return 'http://localhost:5000/api';
        }
        return `${window.location.protocol}//${window.location.hostname}:5000/api`;
    },

    getMandantId: function () {
        const params = new URLSearchParams(window.location.search);
        return params.get('id');
    },

    // --- LISTING ---
    loadList: async function () {
        const id = this.getMandantId();
        if (!id) return;

        const container = document.getElementById('mitarbeiterList');
        // container.innerHTML = '<p class="loading">Lade Mitarbeiter...</p>'; // Don't wipe if not needed, but good for feedback

        try {
            const response = await fetch(`${this.getApiUrl()}/mandanten/${id}/mitarbeiter`);
            const data = await response.json();

            if (response.ok) {
                this.renderList(data);
            } else {
                container.innerHTML = '<p class="error">Fehler beim Laden.</p>';
            }
        } catch (e) {
            console.error(e);
            container.innerHTML = '<p class="error">Verbindungsfehler.</p>';
        }
    },

    renderList: function (list) {
        const container = document.getElementById('mitarbeiterList');
        if (!list || list.length === 0) {
            container.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #888;">Keine Mitarbeiter angelegt.</p>';
            return;
        }

        container.innerHTML = list.map(emp => `
            <div class="mandant-card" style="position: relative;">
                <div class="mandant-header">
                    <div class="mandant-avatar" style="background: linear-gradient(135deg, #FF9966, #FF5E62);">
                        ${(emp.vorname || 'M')[0]}${(emp.nachname || 'A')[0]}
                    </div>
                    <div class="mandant-info">
                        <h3>${emp.vorname} ${emp.nachname}</h3>
                        <p class="mandant-id">Pers.Nr: ${emp.personalnummer || '-'}</p>
                    </div>
                </div>
                <div class="mandant-stats">
                    <div class="stat-item">
                        <div class="stat-item-label">Eintritt</div>
                        <div class="stat-item-value">${emp.eintritt || '-'}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-item-label">StKl</div>
                        <div class="stat-item-value">${emp.steuerklasse || '-'}</div>
                    </div>
                </div>
                <div style="margin-top: 15px; display: flex; gap: 10px;">
                    <button class="btn btn-sm btn-outline" onclick='MitarbeiterManager.openEditModal(${JSON.stringify(emp).replace(/'/g, "&#39;")})'>
                        ✏️ Bearbeiten
                    </button>
                    <button class="btn btn-sm btn-primary" onclick='MitarbeiterManager.openPayslipModal(${JSON.stringify(emp).replace(/'/g, "&#39;")})'>
                        📄 Lohn
                    </button>
                </div>
            </div>
        `).join('');
    },

    // --- EDIT MODAL ---
    openEditModal: function (emp = null) {
        const modal = document.getElementById('editMitarbeiterModal');
        modal.style.display = 'flex';

        // Reset or Fill
        document.getElementById('empId').value = emp ? emp.id : '';
        document.getElementById('empVorname').value = emp ? emp.vorname : '';
        document.getElementById('empNachname').value = emp ? emp.nachname : '';
        document.getElementById('empStrasse').value = emp ? emp.strasse : '';
        document.getElementById('empOrt').value = emp ? emp.ort : '';
        document.getElementById('empPersNr').value = emp ? emp.personalnummer : '';
        document.getElementById('empGeb').value = emp ? emp.geburtsdatum : '';
        document.getElementById('empEintritt').value = emp ? emp.eintritt : '';
        document.getElementById('empStKl').value = emp ? emp.steuerklasse : '-';
        document.getElementById('empSV').value = emp ? emp.sv_nummer : '';
        document.getElementById('empIBAN').value = emp ? emp.iban : '';
    },

    closeEditModal: function () {
        document.getElementById('editMitarbeiterModal').style.display = 'none';
    },

    saveMitarbeiter: async function () {
        const id = this.getMandantId();
        if (!id) return;

        const empData = {
            id: document.getElementById('empId').value || null, // null for new
            vorname: document.getElementById('empVorname').value,
            nachname: document.getElementById('empNachname').value,
            strasse: document.getElementById('empStrasse').value,
            ort: document.getElementById('empOrt').value,
            personalnummer: document.getElementById('empPersNr').value,
            geburtsdatum: document.getElementById('empGeb').value,
            eintritt: document.getElementById('empEintritt').value,
            steuerklasse: document.getElementById('empStKl').value,
            sv_nummer: document.getElementById('empSV').value,
            iban: document.getElementById('empIBAN').value
        };

        try {
            const response = await fetch(`${this.getApiUrl()}/mandanten/${id}/mitarbeiter`, {
                method: 'POST', // Handle create and update
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(empData)
            });

            if (response.ok) {
                alert('Mitarbeiter gespeichert.');
                this.closeEditModal();
                this.loadList();
            } else {
                alert('Fehler beim Speichern.');
            }
        } catch (e) {
            console.error(e);
            alert('Fehler beim Speichern.');
        }
    },

    // --- PAYSLIP MODAL ---
    openPayslipModal: function (emp) {
        if (!emp) return;
        this.currentEmpId = emp.id;

        const modal = document.getElementById('payslipModal');
        modal.style.display = 'flex';

        document.getElementById('slipEmpName').textContent = `${emp.vorname} ${emp.nachname}`;
        document.getElementById('slipEmpId').value = emp.id;

        // Reset fields
        document.getElementById('slipBrutto').value = '';
        document.getElementById('slipBonus').value = '0.00';
        document.getElementById('slipTaxLohn').value = '0.00';
        document.getElementById('slipTaxSV').value = '0.00';
        // Reset Hourly
        if (document.getElementById('slipHourlyRate')) document.getElementById('slipHourlyRate').value = '';
        if (document.getElementById('slipHours')) document.getElementById('slipHours').value = '';

        this.updatePreview();
        this.loadHistory(emp.id); // Load History
    },

    closePayslipModal: function () {
        document.getElementById('payslipModal').style.display = 'none';
        this.currentEmpId = null;
    },

    loadHistory: async function (empId) {
        const id = this.getMandantId();
        const container = document.getElementById('slipHistoryList');
        if (!container) return;
        container.innerHTML = '<span style="color:#888;">Lade Historie...</span>';

        try {
            const response = await fetch(`${this.getApiUrl()}/mandanten/${id}/mitarbeiter/${empId}/payslips`);

            if (!response.ok) {
                throw new Error(`Server-Fehler: ${response.status}`);
            }

            const files = await response.json();

            if (Array.isArray(files) && files.length > 0) {
                container.innerHTML = files.map(f => {
                    const pdfUrl = `${this.getApiUrl().replace('/api', '/api/pdf')}/Mandanten/${id}/Lohnabrechnungen/${f.filename}`;
                    // Remove prefix 'Lohn_' and everything after date for display?
                    // filename: Lohn_Name_Vorname_Month-Year.pdf
                    // Display: Name Vorname Month-Year
                    return `
                    <div style="padding: 5px; border-bottom: 1px solid #333; cursor: pointer; display: flex; justify-content: space-between; align-items: center;" 
                         onclick="window.open('${pdfUrl}', '_blank')">
                        <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 70%;">📄 ${f.filename.replace(/^Lohn_/, '').replace('.pdf', '')}</span>
                        <span style="color:#888; font-size: 0.8em;">${f.date}</span>
                    </div>`;
                }).join('');
            } else {
                container.innerHTML = '<span style="color:#666;">Keine Abrechnungen gefunden.</span>';
            }
        } catch (e) {
            console.error(e);
            container.innerHTML = `<span style="color:red; font-size:0.9em;">Fehler: ${e.message}</span>`;
        }
    },

    updatePreview: function () {
        const brutto = parseFloat(document.getElementById('slipBrutto').value) || 0;
        const bonus = parseFloat(document.getElementById('slipBonus').value) || 0;
        const tax = parseFloat(document.getElementById('slipTaxLohn').value) || 0;
        const sv = parseFloat(document.getElementById('slipTaxSV').value) || 0;

        const totalBrutto = brutto + bonus;
        const netto = totalBrutto - tax - sv;

        document.getElementById('slipNettoPreview').textContent = `${netto.toFixed(2)} €`;
    },

    generatePayslip: async function () {
        const id = this.getMandantId();
        const empId = this.currentEmpId;
        if (!id || !empId) return;

        const payload = {
            monat: document.getElementById('slipMonth').value,
            jahr: document.getElementById('slipYear').value,
            brutto: document.getElementById('slipBrutto').value,
            bonus: document.getElementById('slipBonus').value,
            abzuege: {
                'Lohnsteuer': document.getElementById('slipTaxLohn').value,
                'Sozialversicherung (AG)': document.getElementById('slipTaxSV').value
            }
        };

        try {
            const response = await fetch(`${this.getApiUrl()}/mandanten/${id}/mitarbeiter/${empId}/payslip`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            if (result.success) {
                const pdfPath = `Mandanten/${id}/Lohnabrechnungen/${result.filename}`;
                window.open(`${this.getApiUrl().replace('/api', '/api/pdf')}/${pdfPath}`, '_blank');
                // Refresh History
                this.loadHistory(empId);
            } else {
                alert('Fehler: ' + result.error);
            }
        } catch (e) {
            console.error(e);
            alert('Fehler beim Erstellen.');
        }
    }
};

// Auto-Calculation hook
document.addEventListener('DOMContentLoaded', () => {
    // Brutto/Netto Preview
    ['slipBrutto', 'slipBonus', 'slipTaxLohn', 'slipTaxSV'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('input', () => MitarbeiterManager.updatePreview());
    });

    // Hourly Wage Calculator
    ['slipHourlyRate', 'slipHours'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('input', () => {
            const rate = parseFloat(document.getElementById('slipHourlyRate').value) || 0;
            const hours = parseFloat(document.getElementById('slipHours').value) || 0;
            if (rate > 0 && hours > 0) {
                document.getElementById('slipBrutto').value = (rate * hours).toFixed(2);
                MitarbeiterManager.updatePreview();
            }
        });
    });
});
