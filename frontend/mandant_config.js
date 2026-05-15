
// Mandant Configuration Management

function getMandantIdForConfig() {
    const params = new URLSearchParams(window.location.search);
    return params.get('id'); // Corrected parameter name
}

function getApiUrlForConfig() {
    if (window.location.protocol === 'file:') {
        return 'http://localhost:5000/api';
    }
    return `${window.location.protocol}//${window.location.hostname}:5000/api`;
}

function openConfigModal() {
    const modal = document.getElementById('editConfigModal');
    if (!modal) return;
    modal.style.display = 'flex';
    loadMandantConfig();
}

function closeConfigModal() {
    const modal = document.getElementById('editConfigModal');
    if (modal) modal.style.display = 'none';
}

async function loadMandantConfig() {
    const id = getMandantIdForConfig();
    if (!id) return;

    try {
        const response = await fetch(`${getApiUrlForConfig()}/mandanten/${id}/config`);
        const config = await response.json();

        if (config.error) {
            alert('Fehler beim Laden der Konfiguration: ' + config.error);
            return;
        }

        // Fill Fields
        document.getElementById('cfgFirma').value = config.firma || '';
        document.getElementById('cfgMandantenNr').value = config.mandantennummer || '';

        const formTypEl = document.getElementById('cfgFormTyp');
        if (formTypEl) {
            formTypEl.value = config.unternehmensform || 'Einzelunternehmen';
        }

        document.getElementById('cfgGF').value = config.geschaeftsfuehrer || '';
        document.getElementById('cfgUStId').value = config.ustid || '';
        document.getElementById('cfgSteuernummer').value = config.steuernummer || '';

        const currentLogo = config.logo || 'Kein Logo';
        const logoEl = document.getElementById('cfgCurrentLogo');
        if (logoEl) logoEl.textContent = currentLogo;

        // Reset File Input
        const fileInput = document.getElementById('cfgLogoFile');
        if (fileInput) fileInput.value = '';

        if (config.adresse) {
            document.getElementById('cfgStrasse').value = config.adresse.strasse || '';
            document.getElementById('cfgOrt').value = config.adresse.ort || '';
        }

        if (config.bank) {
            document.getElementById('cfgBankName').value = config.bank.name || '';
            document.getElementById('cfgIBAN').value = config.bank.iban || '';
            document.getElementById('cfgBIC').value = config.bank.bic || '';
        }

        // SMTP
        if (config.smtp) {
            document.getElementById('cfgSmtpServer').value = config.smtp.server || '';
            document.getElementById('cfgSmtpPort').value = config.smtp.port || '';
            document.getElementById('cfgSmtpUser').value = config.smtp.user || '';
            document.getElementById('cfgSmtpPass').value = config.smtp.pass || '';
            document.getElementById('cfgSmtpSender').value = config.smtp.sender || '';
        } else {
            // Reset if empty
            document.getElementById('cfgSmtpServer').value = '';
            document.getElementById('cfgSmtpPort').value = '';
            document.getElementById('cfgSmtpUser').value = '';
            document.getElementById('cfgSmtpPass').value = '';
            document.getElementById('cfgSmtpSender').value = '';
        }

    } catch (e) {
        console.error('Config Load Error:', e);
        alert('Fehler beim Laden der Daten.');
    }
}

async function saveMandantConfig() {
    const id = getMandantIdForConfig();
    if (!id) return;

    const data = {
        firma: document.getElementById('cfgFirma').value,
        mandantennummer: document.getElementById('cfgMandantenNr').value,
        unternehmensform: document.getElementById('cfgFormTyp') ? document.getElementById('cfgFormTyp').value : 'Einzelunternehmen',
        geschaeftsfuehrer: document.getElementById('cfgGF').value,
        ustid: document.getElementById('cfgUStId').value,
        steuernummer: document.getElementById('cfgSteuernummer').value,
        // logo is handled via file upload
        adresse: {
            strasse: document.getElementById('cfgStrasse').value,
            ort: document.getElementById('cfgOrt').value
        },
        bank: {
            name: document.getElementById('cfgBankName').value,
            iban: document.getElementById('cfgIBAN').value,
            bic: document.getElementById('cfgBIC').value
        },
        smtp: {
            server: document.getElementById('cfgSmtpServer').value,
            port: document.getElementById('cfgSmtpPort').value,
            user: document.getElementById('cfgSmtpUser').value,
            pass: document.getElementById('cfgSmtpPass').value,
            sender: document.getElementById('cfgSmtpSender').value
        }
    };

    try {
        const response = await fetch(`${getApiUrlForConfig()}/mandanten/${id}/config`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        if (!result.success) {
            alert('Fehler beim Speichern der Daten: ' + (result.error || 'Unbekannt'));
            return;
        }

        // 2. Upload Logo if selected
        const fileInput = document.getElementById('cfgLogoFile');
        if (fileInput && fileInput.files.length > 0) {
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            const uploadResponse = await fetch(`${getApiUrlForConfig()}/mandanten/${id}/logo`, {
                method: 'POST',
                body: formData
            });
            const uploadResult = await uploadResponse.json();
            if (!uploadResult.success) {
                alert('Daten gespeichert, aber Logo-Upload fehlgeschlagen: ' + (uploadResult.error || 'Unbekannt'));
                // Don't return, still close and reload
            }
        }

        alert('Erfolgreich gespeichert!');
        closeConfigModal();
        location.reload();

    } catch (e) {
        console.error('Config Save Error:', e);
        alert('Fehler beim Speichern.');
    }
}

async function deleteMandant() {
    const id = getMandantIdForConfig();
    if (!id) return;

    if (confirm("Möchtest du diesen Mandanten wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden und alle Rechnungen, Angebote und Kundendaten werden unwiderruflich gelöscht!")) {
        try {
            const response = await fetch(`${getApiUrlForConfig()}/mandanten/${id}`, {
                method: 'DELETE'
            });

            const result = await response.json();
            if (result.success) {
                alert('Mandant erfolgreich gelöscht.');
                window.location.href = 'index.html'; // Redirect to dashboard
            } else {
                alert('Fehler beim Löschen: ' + (result.error || 'Unbekannt'));
            }
        } catch (e) {
            console.error('Delete Mandant Error:', e);
            alert('Fehler beim Löschen des Mandanten.');
        }
    }
}

// Close on outside click
window.onclick = function (event) {
    const modal = document.getElementById('editConfigModal');
    if (event.target == modal) {
        closeConfigModal();
    }
}
