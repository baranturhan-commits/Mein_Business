/**
 * wartung.js – Wartungsprotokoll-Verwaltung
 * Struktur analog zu recurring.js (Manager-Objekt mit init, load, render).
 * Kommuniziert mit dem Flask-Backend über die Wartungs-API-Endpunkte.
 */

const API_BASE_URL_WARTUNG = 'https://meinbusiness-production.up.railway.app/api';

const WartungManager = {

    // --- Zustand ---
    mandantId: null,
    protokolle: [],

    // -------------------------------------------------------
    // Initialisierung
    // -------------------------------------------------------
    init: function () {
        // Mandant-ID aus URL-Parameter lesen (wie in detail.js)
        const urlParams = new URLSearchParams(window.location.search);
        this.mandantId = urlParams.get('id');

        if (!this.mandantId) {
            console.error('WartungManager: Kein Mandant in URL gefunden.');
            return;
        }

        // Tab-Inhalt aufbauen und Daten laden
        this._renderContainer();
        this.ladeKunden();
        this.ladeProtokolle();
    },

    // -------------------------------------------------------
    // Tab-Container initial rendern (Formular + Liste)
    // -------------------------------------------------------
    _renderContainer: function () {
        const tab = document.getElementById('tab-wartung');
        if (!tab) return;

        tab.innerHTML = `
            <section class="mandanten-section">
                <div class="section-header">
                    <h2>🔧 Wartungsprotokolle</h2>
                    <button class="btn btn-primary" onclick="WartungManager.toggleFormular()">
                        <span class="icon">➕</span> Neues Protokoll
                    </button>
                </div>

                <!-- Eingabe-Formular (standardmäßig versteckt) -->
                <div id="wartungFormularWrapper" style="display:none;">
                    <div class="modal-content" style="position:relative; margin-bottom:20px; padding:20px; border-radius:12px; background:var(--surface,#1e1e3a);">
                        <h3 style="margin-bottom:16px;">📋 Neues Wartungsprotokoll erfassen</h3>

                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">

                            <!-- Kunde -->
                            <div class="form-group">
                                <label>Kunde *</label>
                                <select id="wKunde" class="form-input" style="background:var(--surface-2,#2a2a4a); color:white; border:1px solid rgba(255,255,255,0.2); border-radius:8px; padding:8px 12px; width:100%;">
                                    <option value="">-- Kunden laden... --</option>
                                </select>
                            </div>

                            <!-- Datum -->
                            <div class="form-group">
                                <label>Datum der Wartung *</label>
                                <input type="date" id="wDatum" class="form-input"
                                    value="${new Date().toISOString().split('T')[0]}"
                                    style="background:var(--surface-2,#2a2a4a); color:white; border:1px solid rgba(255,255,255,0.2); border-radius:8px; padding:8px 12px; width:100%;">
                            </div>

                            <!-- Techniker -->
                            <div class="form-group">
                                <label>Techniker *</label>
                                <input type="text" id="wTechniker" class="form-input" placeholder="z.B. Max Muster"
                                    style="background:var(--surface-2,#2a2a4a); color:white; border:1px solid rgba(255,255,255,0.2); border-radius:8px; padding:8px 12px; width:100%;">
                            </div>

                            <!-- Anlage -->
                            <div class="form-group">
                                <label>Anlage / Gerät *</label>
                                <select id="wAnlage" class="form-input"
                                    style="background:var(--surface-2,#2a2a4a); color:white; border:1px solid rgba(255,255,255,0.2); border-radius:8px; padding:8px 12px; width:100%;">
                                    <option value="Kessel">Kessel</option>
                                    <option value="Brenner">Brenner</option>
                                    <option value="Pumpe">Pumpe</option>
                                    <option value="Sonstiges">Sonstiges</option>
                                </select>
                            </div>
                        </div>

                        <!-- Checkboxen -->
                        <div style="margin:16px 0;">
                            <p style="font-weight:600; margin-bottom:10px;">Durchgeführte Prüfungen:</p>
                            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
                                <label class="checkbox-label" style="display:flex; align-items:center; gap:8px; cursor:pointer;">
                                    <input type="checkbox" id="wDruckOk"> Druck geprüft
                                </label>
                                <label class="checkbox-label" style="display:flex; align-items:center; gap:8px; cursor:pointer;">
                                    <input type="checkbox" id="wDichtheitsOk"> Dichtheit geprüft
                                </label>
                                <label class="checkbox-label" style="display:flex; align-items:center; gap:8px; cursor:pointer;">
                                    <input type="checkbox" id="wFilterOk"> Filter gereinigt
                                </label>
                                <label class="checkbox-label" style="display:flex; align-items:center; gap:8px; cursor:pointer;">
                                    <input type="checkbox" id="wSicherheitsventilOk"> Sicherheitsventil geprüft
                                </label>
                            </div>
                        </div>

                        <!-- Befund -->
                        <div class="form-group" style="margin-bottom:12px;">
                            <label>Befund / Feststellungen</label>
                            <textarea id="wBefund" rows="4" placeholder="Beschreibung der Wartungsergebnisse..."
                                style="background:var(--surface-2,#2a2a4a); color:white; border:1px solid rgba(255,255,255,0.2); border-radius:8px; padding:8px 12px; width:100%; resize:vertical;"></textarea>
                        </div>

                        <!-- Nächste Wartung -->
                        <div class="form-group" style="margin-bottom:16px;">
                            <label>Nächste Wartung fällig am</label>
                            <input type="date" id="wNaechsteWartung" class="form-input"
                                style="background:var(--surface-2,#2a2a4a); color:white; border:1px solid rgba(255,255,255,0.2); border-radius:8px; padding:8px 12px; width:100%;">
                        </div>

                        <!-- Status-Meldung -->
                        <div id="wartungFormStatus" style="margin-bottom:10px;"></div>

                        <!-- Aktions-Buttons -->
                        <div style="display:flex; gap:10px;">
                            <button class="btn btn-primary" onclick="WartungManager.speichern()">
                                💾 Protokoll speichern
                            </button>
                            <button class="btn btn-outline" onclick="WartungManager.toggleFormular()">
                                Abbrechen
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Protokoll-Liste -->
                <div id="wartungListe" class="op-list">
                    <div class="loading">
                        <div class="spinner"></div>
                        <p>Lade Protokolle...</p>
                    </div>
                </div>
            </section>
        `;
    },

    // -------------------------------------------------------
    // Formular ein-/ausblenden
    // -------------------------------------------------------
    toggleFormular: function () {
        const wrapper = document.getElementById('wartungFormularWrapper');
        if (!wrapper) return;
        wrapper.style.display = wrapper.style.display === 'none' ? 'block' : 'none';
    },

    // -------------------------------------------------------
    // Kundenliste für Dropdown laden
    // -------------------------------------------------------
    ladeKunden: async function () {
        try {
            const token = await this._getToken();
            const res = await fetch(
                `${API_BASE_URL_WARTUNG}/mandanten/${this.mandantId}/kunden`,
                { headers: { 'Authorization': `Bearer ${token}` } }
            );
            const data = await res.json();
            const kunden = data.kunden || [];

            const select = document.getElementById('wKunde');
            if (!select) return;

            select.innerHTML = '<option value="">-- Kunde wählen --</option>';
            kunden.forEach(k => {
                const name = k.Firma || k.firma || '';
                if (name) {
                    const opt = document.createElement('option');
                    opt.value = name;
                    opt.textContent = name;
                    select.appendChild(opt);
                }
            });
        } catch (e) {
            console.warn('WartungManager: Kunden konnten nicht geladen werden:', e);
        }
    },

    // -------------------------------------------------------
    // Protokolle vom Backend laden
    // -------------------------------------------------------
    ladeProtokolle: async function () {
        const liste = document.getElementById('wartungListe');
        if (!liste) return;

        liste.innerHTML = '<div class="loading"><div class="spinner"></div><p>Lade Protokolle...</p></div>';

        try {
            const token = await this._getToken();
            const res = await fetch(
                `${API_BASE_URL_WARTUNG}/mandanten/${this.mandantId}/wartung/protokolle`,
                { headers: { 'Authorization': `Bearer ${token}` } }
            );
            const data = await res.json();

            if (data.error) {
                liste.innerHTML = `<p class="error">Fehler: ${data.error}</p>`;
                return;
            }

            this.protokolle = data.protokolle || [];
            this.renderListe(this.protokolle);

        } catch (e) {
            console.error('WartungManager: Fehler beim Laden:', e);
            liste.innerHTML = `<p class="error">Verbindungsfehler: ${e.message}</p>`;
        }
    },

    // -------------------------------------------------------
    // Protokoll-Liste rendern
    // -------------------------------------------------------
    renderListe: function (protokolle) {
        const liste = document.getElementById('wartungListe');
        if (!liste) return;

        if (!protokolle || protokolle.length === 0) {
            liste.innerHTML = '<div class="no-data"><p>Noch keine Wartungsprotokolle vorhanden.</p></div>';
            return;
        }

        // Checkbox-Symbole für die Tabellenansicht
        const cb = (val) => val ? '☑' : '☐';

        let html = `
            <table class="op-table">
                <thead>
                    <tr>
                        <th>Datum</th>
                        <th>Kunde</th>
                        <th>Anlage</th>
                        <th>Techniker</th>
                        <th>Prüfungen</th>
                        <th>Nächste Wartung</th>
                        <th>PDF</th>
                    </tr>
                </thead>
                <tbody>
        `;

        protokolle.forEach(p => {
            // Datum formatieren (YYYY-MM-DD → DD.MM.YYYY)
            const datumFormatiert = this._formatDatum(p.datum || '');
            const naechsteFormatiert = this._formatDatum(p.naechste_wartung || '');

            // Überfälligkeits-Prüfung
            const heute = new Date().toISOString().split('T')[0];
            const ueberFaellig = p.naechste_wartung && p.naechste_wartung < heute;
            const faelligStyle = ueberFaellig ? 'color:var(--danger,#e74c3c); font-weight:bold;' : '';
            const faelligBadge = ueberFaellig ? ' <span class="badge-overdue">⚠️ Fällig</span>' : '';

            html += `
                <tr>
                    <td>${datumFormatiert}</td>
                    <td><strong>${this._escape(p.kunde || '')}</strong></td>
                    <td>${this._escape(p.anlage || '')}</td>
                    <td>${this._escape(p.techniker || '')}</td>
                    <td style="font-size:13px; line-height:1.6;">
                        ${cb(p.druck_ok)} Druck<br>
                        ${cb(p.dichtheit_ok)} Dichtheit<br>
                        ${cb(p.filter_ok)} Filter<br>
                        ${cb(p.sicherheitsventil_ok)} Sicherheitsv.
                    </td>
                    <td style="${faelligStyle}">
                        ${naechsteFormatiert || '—'}${faelligBadge}
                    </td>
                    <td>
                        <button class="btn btn-sm btn-secondary"
                            onclick="WartungManager.downloadPdf('${p.id}')">
                            📄 PDF
                        </button>
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        liste.innerHTML = html;
    },

    // -------------------------------------------------------
    // Protokoll speichern (POST)
    // -------------------------------------------------------
    speichern: async function () {
        const statusEl = document.getElementById('wartungFormStatus');

        // Eingaben auslesen
        const kunde = document.getElementById('wKunde')?.value;
        const datum = document.getElementById('wDatum')?.value;
        const techniker = document.getElementById('wTechniker')?.value?.trim();
        const anlage = document.getElementById('wAnlage')?.value;
        const druckOk = document.getElementById('wDruckOk')?.checked || false;
        const dichtheitsOk = document.getElementById('wDichtheitsOk')?.checked || false;
        const filterOk = document.getElementById('wFilterOk')?.checked || false;
        const sicherheitsventilOk = document.getElementById('wSicherheitsventilOk')?.checked || false;
        const befund = document.getElementById('wBefund')?.value?.trim() || '';
        const naechsteWartung = document.getElementById('wNaechsteWartung')?.value || '';

        // Pflichtfeld-Prüfung
        if (!kunde || !datum || !techniker || !anlage) {
            if (statusEl) statusEl.innerHTML = '<p class="error">⚠️ Bitte alle Pflichtfelder ausfüllen (Kunde, Datum, Techniker, Anlage).</p>';
            return;
        }

        if (statusEl) statusEl.innerHTML = '<p style="color:#aaa;">Speichern...</p>';

        const payload = {
            datum,
            techniker,
            kunde,
            anlage,
            druck_ok: druckOk,
            dichtheit_ok: dichtheitsOk,
            filter_ok: filterOk,
            sicherheitsventil_ok: sicherheitsventilOk,
            befund,
            naechste_wartung: naechsteWartung
        };

        try {
            const token = await this._getToken();
            const res = await fetch(
                `${API_BASE_URL_WARTUNG}/mandanten/${this.mandantId}/wartung/protokoll`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify(payload)
                }
            );
            const result = await res.json();

            if (result.success) {
                if (statusEl) statusEl.innerHTML = '<p style="color:#2ecc71;">✅ Protokoll erfolgreich gespeichert!</p>';
                // Formular zurücksetzen
                this._resetFormular();
                // Liste neu laden
                await this.ladeProtokolle();
                // Formular nach 1,5 Sekunden schließen
                setTimeout(() => this.toggleFormular(), 1500);
            } else {
                if (statusEl) statusEl.innerHTML = `<p class="error">Fehler: ${result.error}</p>`;
            }
        } catch (e) {
            console.error('WartungManager: Speichern fehlgeschlagen:', e);
            if (statusEl) statusEl.innerHTML = `<p class="error">Verbindungsfehler: ${e.message}</p>`;
        }
    },

    // -------------------------------------------------------
    // PDF für ein Protokoll herunterladen
    // -------------------------------------------------------
    downloadPdf: async function (protokollId) {
        try {
            const token = await this._getToken();
            const url = `${API_BASE_URL_WARTUNG}/mandanten/${this.mandantId}/wartung/protokoll/${protokollId}/pdf`;

            // PDF via fetch laden und als Download öffnen
            const res = await fetch(url, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (!res.ok) {
                const err = await res.json();
                alert(`Fehler beim PDF-Download: ${err.error || res.statusText}`);
                return;
            }

            const blob = await res.blob();
            const blobUrl = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = blobUrl;
            link.download = `Wartungsprotokoll_${protokollId}.pdf`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(blobUrl);

        } catch (e) {
            console.error('WartungManager: PDF-Download fehlgeschlagen:', e);
            alert(`PDF-Download fehlgeschlagen: ${e.message}`);
        }
    },

    // -------------------------------------------------------
    // Hilfsfunktionen
    // -------------------------------------------------------

    /** Formularfelder zurücksetzen */
    _resetFormular: function () {
        ['wKunde', 'wDatum', 'wTechniker', 'wAnlage', 'wBefund', 'wNaechsteWartung'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = id === 'wDatum' ? new Date().toISOString().split('T')[0] : '';
        });
        ['wDruckOk', 'wDichtheitsOk', 'wFilterOk', 'wSicherheitsventilOk'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.checked = false;
        });
    },

    /** Firebase-Token holen (wenn verfügbar) */
    _getToken: async function () {
        try {
            if (typeof firebase !== 'undefined' && firebase.auth) {
                const user = firebase.auth().currentUser;
                if (user) return await user.getIdToken();
            }
            // Fallback: kein Token (für lokale Entwicklung)
            return '';
        } catch (e) {
            return '';
        }
    },

    /** Datum von YYYY-MM-DD zu DD.MM.YYYY formatieren */
    _formatDatum: function (datumStr) {
        if (!datumStr) return '';
        try {
            const [y, m, d] = datumStr.split('-');
            if (y && m && d) return `${d}.${m}.${y}`;
        } catch (_) {}
        return datumStr;
    },

    /** HTML-Sonderzeichen escapen */
    _escape: function (str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }
};
