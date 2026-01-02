// Import functionality for Preisliste

let importedPositionen = [];

// Import Modal
function showImportModal() {
    document.getElementById('importModal').classList.remove('hidden');
    document.getElementById('importUpload').classList.remove('hidden');
    document.getElementById('importPreview').classList.add('hidden');

    // Setup file input
    const fileInput = document.getElementById('importFileInput');
    fileInput.value = ''; // Reset
    fileInput.removeEventListener('change', handleImportFile);
    fileInput.addEventListener('change', handleImportFile);

    // Setup Drag & Drop
    const dropZone = document.getElementById('importZone');

    dropZone.ondragover = (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.style.borderColor = '#3498db';
        dropZone.style.background = 'rgba(52, 152, 219, 0.1)';
    };

    dropZone.ondragleave = (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.style.borderColor = '';
        dropZone.style.background = '';
    };

    dropZone.ondrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.style.borderColor = '';
        dropZone.style.background = '';

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files; // Transfer to input
            handleImportFile({ target: { files: files } });
        }
    };
}

function closeImportModal() {
    document.getElementById('importModal').classList.add('hidden');
    document.getElementById('importStatus').innerHTML = '';
    importedPositionen = [];
}

async function handleImportFile(event) {
    const file = event.target.files[0];
    if (!file) return;

    const statusDiv = document.getElementById('importStatus');
    statusDiv.innerHTML = '<p>🔄 Analysiere Datei...</p>';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const id = getMandantId();
        const response = await fetch(`${API_BASE_URL}/mandanten/${id}/preisliste/import`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            importedPositionen = result.positionen;
            showImportPreview(result.positionen);
        } else {
            statusDiv.innerHTML = `<p class="error">❌ ${result.error}</p>`;
        }
    } catch (error) {
        statusDiv.innerHTML = '<p class="error">❌ Fehler beim Import</p>';
    }
}

function showImportPreview(positionen) {
    document.getElementById('importUpload').classList.add('hidden');
    document.getElementById('importPreview').classList.remove('hidden');
    document.getElementById('importCount').textContent = positionen.length;

    const html = `
        <table class="op-table">
            <thead>
                <tr>
                    <th>Bezeichnung</th>
                    <th>Einheit</th>
                    <th>Preis</th>
                    <th>Kategorie</th>
                </tr>
            </thead>
            <tbody>
                ${positionen.map(pos => `
                    <tr>
                        <td>${pos.bezeichnung}</td>
                        <td>${pos.einheit}</td>
                        <td>${formatPrice(pos.einzelpreis)}</td>
                        <td>${pos.kategorie}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    document.getElementById('importTable').innerHTML = html;
}

async function confirmImport() {
    const statusDiv = document.getElementById('importStatus');
    statusDiv.innerHTML = '<p>💾 Speichere Positionen...</p>';

    try {
        const id = getMandantId();
        const response = await fetch(`${API_BASE_URL}/mandanten/${id}/preisliste/import/confirm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ positionen: importedPositionen })
        });

        const result = await response.json();

        if (result.success) {
            alert(`✅ ${result.count} Positionen erfolgreich importiert!`);
            closeImportModal();
            loadPreisliste(); // Refresh list
        } else {
            statusDiv.innerHTML = `<p class="error">❌ ${result.error}</p>`;
        }
    } catch (error) {
        statusDiv.innerHTML = '<p class="error">❌ Fehler beim Speichern</p>';
    }
}

// Export
window.showImportModal = showImportModal;
window.closeImportModal = closeImportModal;
window.handleImportFile = handleImportFile;
window.confirmImport = confirmImport;
