// Documents Tab Logic
// Ensure API_BASE_URL is available
const DOCS_API_URL = (typeof API_BASE_URL !== 'undefined') ? API_BASE_URL : 'http://localhost:5000/api';

// Global Data Store for Filtering
let allDocumentsData = {
    angebote: [],
    lieferscheine: [],
    rechnungen: []
};

// Global Filter Function (called from HTML)
function applyDocFilter() {
    renderAngeboteList();
    renderLieferscheineList();
    renderRechnungenListDoc();
    // Also trigger expenses if available
    if (typeof applyAusgabenFilter === 'function') {
        applyAusgabenFilter();
    }
}

function loadDocuments() {
    console.log("Loading all documents...");
    // Fetch all data
    fetchAngebote();
    fetchLieferscheine();
    fetchRechnungen();
}

// --- Helper: Date Filtering ---
function isItemInFilter(item, dateField) {
    const monthSelect = document.getElementById('docFilterMonth');
    const yearSelect = document.getElementById('docFilterYear');

    // Default to show if no filter elements
    if (!monthSelect || !yearSelect) return true;

    const filterMonth = monthSelect.value;
    const filterYear = yearSelect.value;

    if (filterMonth === 'all' && filterYear === 'all') return true;

    let dateStr = item[dateField] || '';
    if (!dateStr && item.modified) {
        // Fallback for files: use modified timestamp
        dateStr = new Date(item.modified * 1000).toISOString();
    }

    // Parse Date
    // Supported formats: 'DD.MM.YYYY', 'YYYY-MM-DD', timestamp/ISO
    let d = null;
    if (typeof dateStr === 'string') {
        if (dateStr.includes('.')) {
            const parts = dateStr.split('.');
            if (parts.length === 3) d = new Date(parts[2], parts[1] - 1, parts[0]);
        } else {
            d = new Date(dateStr);
        }
    } else if (typeof dateStr === 'number') {
        d = new Date(dateStr * 1000);
    }

    if (!d || isNaN(d.getTime())) return false; // Hide invalid dates if filter active? Or show? Let's hide.

    const m = d.getMonth() + 1;
    const y = d.getFullYear();

    if (filterYear !== 'all' && String(y) !== String(filterYear)) return false;
    if (filterMonth !== 'all' && String(m) !== String(filterMonth)) return false;

    return true;
}

// --- ANGEBOTE ---
// --- ANGEBOTE ---
async function fetchAngebote() {
    try {
        const id = getMandantId();
        const res = await fetch(`${API_BASE_URL}/mandanten/${id}/angebote`);
        const data = await res.json();
        allDocumentsData.angebote = data.angebote || [];
        renderAngeboteList();
    } catch (e) {
        console.error(e);
    }
}

function renderAngeboteList() {
    const container = document.getElementById('doc-angebote-list');
    if (!container) return;

    const filtered = allDocumentsData.angebote.filter(a => isItemInFilter(a, a.date ? 'date' : 'datum'));

    if (filtered.length > 0) {
        container.innerHTML = filtered.map(a => `
            <div class="doc-item-compact" style="display: flex; justify-content: space-between; align-items: center;">
                <div style="flex-grow: 1; display: flex; align-items: center; cursor: pointer;" onclick="openPdf('${a.pdf_path}')">
                    <span class="doc-icon">📝</span>
                    <div class="doc-info">
                        <div class="doc-title">${a.nummer || 'Angebot'}</div>
                        <div class="doc-meta">${a.date || a.datum} | ${a.kunde}</div>
                    </div>
                </div>
                <button class="btn btn-icon btn-danger" onclick="deleteDocument('angebote', '${a.pdf_path}')" title="Löschen" style="margin-left: 10px; background: transparent; border: none; font-size: 1.2rem; cursor: pointer;">🗑️</button>
            </div>
        `).join('');
    } else {
        container.innerHTML = '<div class="empty-state">Keine Angebote</div>';
    }
}

// --- LIEFERSCHEINE ---
async function fetchLieferscheine() {
    try {
        const id = getMandantId();
        const res = await fetch(`${API_BASE_URL}/mandanten/${id}/lieferscheine`);
        const data = await res.json();
        allDocumentsData.lieferscheine = data.lieferscheine || [];
        renderLieferscheineList();
    } catch (e) {
        console.error(e);
    }
}

function renderLieferscheineList() {
    const containerFilled = document.getElementById('doc-lieferscheine-filled-list');
    const containerBlank = document.getElementById('doc-lieferscheine-blank-list');
    if (!containerFilled || !containerBlank) return;

    const filtered = allDocumentsData.lieferscheine.filter(l => isItemInFilter(l, 'datum'));

    const filled = [];
    const blank = [];

    filtered.forEach(l => {
        let isBlank = false;
        if (!l.items || l.items === '[]' || l.items.length === 0) {
            isBlank = true;
        }
        if (isBlank) blank.push(l);
        else filled.push(l);
    });

    // Render Filled
    if (filled.length > 0) {
        containerFilled.innerHTML = filled.map(l => createDocItem(l, '📋')).join('');
    } else {
        containerFilled.innerHTML = '<div class="empty-state small">Leer</div>';
    }

    // Render Blank
    if (blank.length > 0) {
        containerBlank.innerHTML = blank.map(l => createDocItem(l, '📄')).join('');
    } else {
        containerBlank.innerHTML = '<div class="empty-state small">Leer</div>';
    }
}

// --- RECHNUNGEN ---
async function fetchRechnungen() {
    try {
        const id = getMandantId();
        const res = await fetch(`${API_BASE_URL}/mandanten/${id}/rechnungen`);
        const data = await res.json();
        allDocumentsData.rechnungen = data.rechnungen || [];
        renderRechnungenListDoc();
    } catch (e) {
        console.error(e);
    }
}

function renderRechnungenListDoc() {
    const container = document.getElementById('doc-rechnungen-list');
    if (!container) return;

    // Filter using modified timestamp
    const filtered = allDocumentsData.rechnungen.filter(r => isItemInFilter(r, 'modified'));

    if (filtered.length > 0) {
        container.innerHTML = filtered.map(r => `
            <div class="doc-item-compact" onclick="openPdf('${r.path}')">
                <span class="doc-icon">🧾</span>
                <div class="doc-info">
                    <div class="doc-title">${r.name}</div>
                    <div class="doc-meta">${new Date(r.modified * 1000).toLocaleDateString()}</div>
                </div>
            </div>
        `).join('');
    } else {
        container.innerHTML = '<div class="empty-state">Keine Rechnungen</div>';
    }
}

function createDocItem(doc, icon) {
    return `
        <div class="doc-item-compact" style="display: flex; justify-content: space-between; align-items: center;">
            <div style="flex-grow: 1; display: flex; align-items: center; cursor: pointer;" onclick="openPdf('${doc.pdf_path}')">
                <span class="doc-icon">${icon}</span>
                <div class="doc-info">
                    <div class="doc-title">${doc.nummer || 'Dokument'}</div>
                    <div class="doc-meta">${doc.datum || ''} | ${doc.kunde || ''}</div>
                </div>
            </div>
            <button class="btn btn-icon btn-danger" onclick="deleteDocument('lieferscheine', '${doc.pdf_path}')" title="Löschen" style="margin-left: 10px; background: transparent; border: none; font-size: 1.2rem; cursor: pointer;">🗑️</button>
        </div>
    `;
}

async function deleteDocument(type, path) {
    if (!confirm(`Möchtest du dieses Dokument wirklich löschen?\nDiese Aktion kann nicht rückgängig gemacht werden.`)) return;
    
    const filename = path.split('/').pop();
    const id = getMandantId();
    
    try {
        const res = await fetch(`${DOCS_API_URL}/mandanten/${id}/${type}/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });
        const data = await res.json();
        if (data.success) {
            loadDocuments();
        } else {
            alert('❌ Fehler: ' + data.error);
        }
    } catch (e) {
        alert('Netzwerkfehler: ' + e);
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
    // Fallback if not defined yet
    console.warn("switchTab not found, mocking it");
    window.switchTab = function (tabName) {
        if (tabName === 'documents') loadDocuments();
    }
}

function getMandantId() {
    return new URLSearchParams(window.location.search).get('mandant') || new URLSearchParams(window.location.search).get('id');
}
