// Preislisten-Management Extensions

let allPositionen = [];
let editingPosition = null;

// Tab switching update
const originalSwitchTab = window.switchTab;
window.switchTab = function (tabName) {
    originalSwitchTab(tabName);
    if (tabName === 'preisliste') {
        loadPreisliste();
    }
};

// Load Preisliste
async function loadPreisliste() {
    try {
        const response = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/preisliste`);
        const data = await response.json();

        allPositionen = data.positionen || [];
        renderPreisliste(allPositionen);

    } catch (error) {
        console.error('Fehler beim Laden:', error);
        document.getElementById('preislisteTable').innerHTML = '<p class="error">Fehler beim Laden</p>';
    }
}

function renderPreisliste(positionen) {
    const table = document.getElementById('preislisteTable');

    if (positionen.length === 0) {
        table.innerHTML = '<p class="no-data">Keine Positionen vorhanden. Erstelle deine erste Position!</p>';
        return;
    }

    const html = `
        <table class="op-table">
            <thead>
                <tr>
                    <th>Pos</th>
                    <th>Bezeichnung</th>
                    <th>Einheit</th>
                    <th>Preis</th>
                    <th>Kategorie</th>
                    <th>Aktionen</th>
                </tr>
            </thead>
            <tbody>
                ${positionen.map(pos => `
                    <tr>
                        <td>${pos.Pos}</td>
                        <td>${pos.Bezeichnung}</td>
                        <td>${pos.Einheit}</td>
                        <td>${formatPrice(pos.Einzelpreis)}</td>
                        <td>${pos.Kategorie || '-'}</td>
                        <td>
                            <button class="btn btn-sm" onclick="editPosition(${pos.Pos})">✏️</button>
                            <button class="btn btn-sm btn-danger" onclick="deletePosition(${pos.Pos})">🗑️</button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    table.innerHTML = html;
}

// Position Modal
function showPositionModal(pos = null) {
    editingPosition = pos;
    document.getElementById('positionModal').classList.remove('hidden');

    if (pos) {
        // Edit mode
        const position = allPositionen.find(p => p.Pos == pos);
        if (position) {
            document.getElementById('positionModalTitle').textContent = 'Position bearbeiten';
            document.getElementById('positionId').value = pos;
            document.getElementById('positionBezeichnung').value = position.Bezeichnung;
            document.getElementById('positionEinheit').value = position.Einheit;
            document.getElementById('positionPreis').value = position.Einzelpreis;
            document.getElementById('positionKategorie').value = position.Kategorie || '';
        }
    } else {
        // New mode
        document.getElementById('positionModalTitle').textContent = 'Position hinzufügen';
        document.getElementById('positionForm').reset();
    }
}

function closePositionModal() {
    document.getElementById('positionModal').classList.add('hidden');
    document.getElementById('positionForm').reset();
    document.getElementById('positionStatus').innerHTML = '';
    editingPosition = null;
}

async function submitPosition(event) {
    event.preventDefault();

    const formData = {
        bezeichnung: document.getElementById('positionBezeichnung').value.trim(),
        einheit: document.getElementById('positionEinheit').value,
        einzelpreis: parseFloat(document.getElementById('positionPreis').value),
        kategorie: document.getElementById('positionKategorie').value.trim()
    };

    const statusDiv = document.getElementById('positionStatus');
    statusDiv.innerHTML = '<p>💾 Speichere...</p>';

    try {
        let response;

        if (editingPosition) {
            // Update
            response = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/preisliste/position/${editingPosition}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
        } else {
            // Create
            response = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/preisliste/position`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
        }

        const result = await response.json();

        if (result.success) {
            statusDiv.innerHTML = '<p class="success">✅ Gespeichert!</p>';
            setTimeout(() => {
                closePositionModal();
                loadPreisliste();
            }, 1000);
        } else {
            statusDiv.innerHTML = `<p class="error">❌ ${result.error}</p>`;
        }
    } catch (error) {
        statusDiv.innerHTML = '<p class="error">❌ Fehler beim Speichern</p>';
    }
}

function editPosition(pos) {
    showPositionModal(pos);
}

async function deletePosition(pos) {
    if (!confirm('Position wirklich löschen?')) return;

    try {
        const response = await fetch(`${API_BASE_URL}/mandanten/${mandantId}/preisliste/position/${pos}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            loadPreisliste();
        } else {
            alert('Fehler beim Löschen');
        }
    } catch (error) {
        alert('Fehler beim Löschen');
    }
}

// Utilities
function formatPrice(price) {
    return new Intl.NumberFormat('de-DE', {
        style: 'currency',
        currency: 'EUR'
    }).format(price);
}

// Export
window.loadPreisliste = loadPreisliste;
window.showPositionModal = showPositionModal;
window.closePositionModal = closePositionModal;
window.submitPosition = submitPosition;
window.editPosition = editPosition;
window.deletePosition = deletePosition;
