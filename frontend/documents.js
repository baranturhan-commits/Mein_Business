// Documents Tab Logic
// Ensure API_BASE_URL is available
const DOCS_API_URL = (typeof API_BASE_URL !== 'undefined') ? API_BASE_URL : 'http://localhost:5000/api';

function loadDocuments() {
    console.log("Loading all documents...");
    loadAngeboteList();
    loadLieferscheineList();
    loadRechnungenListDoc();
}

async function loadAngeboteList() {
    const container = document.getElementById('doc-angebote-list'); // Updated ID
    if (!container) return;

    try {
        const id = getMandantId();
        const res = await fetch(`${API_BASE_URL}/mandanten/${id}/angebote`);
        const data = await res.json();

        if (data.angebote && data.angebote.length > 0) {
            container.innerHTML = data.angebote.map(a => `
                <div class="doc-item" onclick="openPdf('${a.pdf_path}')">
                    <span class="icon">📝</span>
                    <div class="doc-info">
                        <strong>${a.nummer || 'Angebot'}</strong>
                        <small>${a.date || a.datum} | ${a.kunde}</small>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<div class="empty-state">Keine Angebote</div>';
        }
    } catch (e) {
        console.error(e);
        container.innerHTML = `<div class="error">Fehler: ${e.message}</div>`;
    }
}

async function loadLieferscheineList() {
    const container = document.getElementById('doc-lieferscheine-list'); // Updated ID
    if (!container) return;

    try {
        const id = getMandantId();
        const res = await fetch(`${API_BASE_URL}/mandanten/${id}/lieferscheine`);
        const data = await res.json();

        if (data.lieferscheine && data.lieferscheine.length > 0) {
            container.innerHTML = data.lieferscheine.map(l => `
                <div class="doc-item" onclick="openPdf('${l.pdf_path}')">
                    <span class="icon">📋</span>
                    <div class="doc-info">
                        <strong>${l.nummer || 'Lieferschein'}</strong>
                        <small>${l.datum} | ${l.kunde}</small>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<div class="empty-state">Keine Protokolle</div>';
        }
    } catch (e) {
        console.error(e);
        container.innerHTML = `<div class="error">Fehler: ${e.message}</div>`;
    }
}

async function loadRechnungenListDoc() {
    const container = document.getElementById('doc-rechnungen-list'); // Updated ID
    if (!container) return;

    try {
        const id = getMandantId();
        const res = await fetch(`${API_BASE_URL}/mandanten/${id}/rechnungen`);
        const data = await res.json();

        if (data.rechnungen && data.rechnungen.length > 0) {
            container.innerHTML = data.rechnungen.map(r => `
                <div class="doc-item" onclick="openPdf('${r.path}')">
                    <span class="icon">🧾</span>
                    <div class="doc-info">
                        <strong>${r.name}</strong>
                        <small>${new Date(r.modified * 1000).toLocaleDateString()}</small>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<div class="empty-state">Keine Rechnungen</div>';
        }
    } catch (e) {
        console.error(e);
        container.innerHTML = `<div class="error">Fehler: ${e.message}</div>`;
    }
}

function openPdf(path) {
    if (!path) return;
    let url = path;
    if (!url.startsWith('http')) {
        url = API_BASE_URL.replace('/api', '') + path;
    }
    window.open(url, '_blank');
}

// Safer Tab Hook
if (typeof window.switchTab === 'function') {
    const originalSwitchTab = window.switchTab;
    window.switchTab = function (tabName) {
        originalSwitchTab(tabName);
        if (tabName === 'documents') {
            loadDocuments();
        }
    }
} else {
    // Fallback if not defined yet (less likely with correct script order)
    console.warn("switchTab not found, mocking it");
    window.switchTab = function (tabName) {
        if (tabName === 'documents') loadDocuments();
    }
}

function getMandantId() {
    return new URLSearchParams(window.location.search).get('mandant') || new URLSearchParams(window.location.search).get('id');
}
