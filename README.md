# 💼 Mein Business - Business Automation Monorepo

Eine KI-gestützte Automatisierungslösung für kleine Unternehmen zur Verwaltung von Mahnwesen, Buchhaltung, Rechnungen und Controlling mit Google Gemini AI.

---

## 🏗️ Projekt-Struktur

Dieses Projekt ist als Monorepo organisiert:

```
Mein_Business/
├── .gitignore                  # Git ignore rules (root)
├── README.md                   # Projekt-Übersicht (diese Datei)
│
├── backend/                    # Python Business Automation Backend
│   ├── 01_Mahnwesen/          # Automatisches Mahnwesen
│   │   ├── agent.py           # Hauptprogramm für Mahnungen
│   │   ├── mahnliste.csv      # Mahnliste
│   │   └── versand_log.csv    # E-Mail-Versandprotokoll
│   │
│   ├── 02_Buchhaltung/        # Buchhaltung & Belegverarbeitung
│   │   ├── scanner.py         # Beleg-Scanner mit KI-Analyse
│   │   ├── list_models.py     # Gemini Modell-Übersicht
│   │   └── Ausgaben/          # Gescannte Belege
│   │
│   ├── 03_Rechnungen/         # Rechnungserstellung
│   │   ├── invoice.py         # Invoice Generator V2
│   │   ├── check_payments.py  # Zahlungseingangs-Checker (OP-Pflege)
│   │   ├── logo.png           # Firmenlogo
│   │   ├── Einnahmen.csv      # Einnahmen-Tracking
│   │   └── README.md          # Rechnungs-Dokumentation
│   │
│   ├── 04_Controlling/        # Finanz-Dashboard
│   │   ├── finance_check.py   # Finanz-Dashboard
│   │   └── Reports/           # Generierte Reports
│   │
│   ├── Mandanten/             # Multi-Tenant Verwaltung
│   │   ├── Baran_Tech_Solutions/
│   │   │   ├── counter.json        # Rechnungsnummern
│   │   │   ├── kunden.csv          # Kundenliste
│   │   │   └── Rechnungen/         # Generierte Rechnungen
│   │   │       └── [Kunde]/        # Nach Kunde sortiert
│   │   │
│   │   └── Elektroniker_Testbetrieb/
│   │       ├── counter.json
│   │       ├── kunden.csv
│   │       ├── einnahmen.csv
│   │       ├── mandant_config.json # Mandanten-Konfiguration
│   │       ├── Rechnungen/         # Generierte Rechnungen
│   │       ├── Kunden/             # Kundenordner
│   │       └── Ausgaben/           # Ausgaben-Belege
│   │
│   ├── PDFs/                  # Allgemeine PDF-Ablage
│   ├── Archiv/                # Archivierte Dateien
│   ├── _ARCHIV/               # Alte Scripts (nicht in Git)
│   │
│   ├── start.py               # 🚀 Hauptmenü / Cockpit
│   ├── add_client.py          # Mandanten/Kunden anlegen
│   ├── organize_and_start.py  # Setup-Script
│   ├── config.json            # Globale Konfiguration
│   ├── kunden.csv             # Kundenliste
│   ├── requirements.txt       # Python Dependencies
│   ├── .gitignore            # Backend Git-Regeln
│   └── README.md             # Backend-Dokumentation
│
└── frontend/                  # Web Interface (Coming Soon)
    └── ...                    # Zukünftig: React/Next.js App
```

---

## 💻 Entwicklungsumgebung einrichten

### Auf einem neuen Laptop/PC starten

Folge diesen Schritten, um das Projekt auf einem neuen Rechner zu entwickeln:

#### 1. Python installieren

**Windows:**
1. Gehe zu: https://www.python.org/downloads/
2. Lade Python 3.8+ herunter
3. **WICHTIG:** Hake "Add Python to PATH" an!
4. Installiere mit Standardoptionen
5. Prüfe Installation:
   ```powershell
   python --version
   ```

**macOS:**
```bash
# Mit Homebrew
brew install python@3.11
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

---

#### 2. Git installieren

**Windows (Option A - Winget):**
```powershell
winget install --id Git.Git -e --source winget
```

**Windows (Option B - Manuell):**
1. Download: https://git-scm.com/download/win
2. Installiere mit Standardeinstellungen

**macOS:**
```bash
brew install git
```

**Linux:**
```bash
sudo apt install git
```

**Git konfigurieren:**
```powershell
git config --global user.name "Dein Name"
git config --global user.email "deine@email.de"
```

---

#### 3. IDE installieren - Google Antigravity

**Google Antigravity (Empfohlen - das nutzen wir!):**

Antigravity ist eine KI-gestützte Entwicklungsumgebung von Google mit integriertem Gemini AI.

**Wichtig zu Tokens/API-Keys:**

✅ **Bestehende Tokens KÖNNEN weitergenutzt werden!**

- Dein Google Gemini API-Key bleibt gleich auf allen Geräten
- Einmal erstellt, kannst du ihn überall verwenden
- **NICHT** neu erstellen, sondern den bestehenden Key kopieren

**Wo findest du deinen bestehenden Key?**
1. Gehe zu: https://aistudio.google.com/app/apikey
2. Melde dich an (gleiches Google-Konto wie hier)
3. Dein Key wird angezeigt - kopieren & auf neuem Laptop verwenden

**Antigravity Setup:**
1. Antigravity ist webbasiert - kein Download nötig
2. Öffne Antigravity in deinem Browser
3. Melde dich mit deinem Google-Account an
4. Dein Workspace wird automatisch synchronisiert

**Alternative IDEs (falls nötig):**

<details>
<summary>VS Code (Empfohlen für Offline-Entwicklung)</summary>

1. Download: https://code.visualstudio.com/
2. Installiere + folgende Extensions:
   - Python (Microsoft)
   - GitLens
   - Pylance
</details>

<details>
<summary>Cursor (Alternative mit AI-Funktionen)</summary>

1. Download: https://cursor.sh/
2. Basiert auf VS Code, aber mit KI-Integration
</details>

---

#### 4. Google Gemini API-Key

**Falls du noch KEINEN Key hast:**
1. Gehe zu: https://aistudio.google.com/app/apikey
2. Melde dich mit Google-Account an
3. Klicke "Create API Key"
4. Kopiere den Key (sicher aufbewahren!)

**Falls du bereits einen Key hast (wie hier):**
- ✅ Nutze denselben Key auf dem neuen Laptop
- ✅ KEINE neue Erstellung nötig
- ✅ Ein Key funktioniert auf allen Geräten

---

#### 5. Projekt clonen & einrichten

**Mit Antigravity:**
1. Öffne Antigravity
2. Gehe zu deinem Workspace
3. Terminal öffnen
4. Führe folgende Befehle aus:

```powershell
# Repository clonen
git clone https://github.com/baranturhan-commits/Mein_Business.git
cd Mein_Business/backend

# Virtuelle Umgebung erstellen
python -m venv venv

# Virtuelle Umgebung aktivieren
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Dependencies installieren
pip install -r requirements.txt
```

**Mit VS Code/Cursor (Alternative):**
```powershell
# Projekt öffnen
code backend  # für VS Code
# oder: cursor backend  # für Cursor

# Dann gleiche Schritte wie oben
```

---

#### 6. GitHub-Authentifizierung einrichten

**In der IDE:**
1. Öffne Source Control (Strg+Shift+G)
2. Klicke "Sign in with GitHub"
3. Browser öffnet sich → Anmelden
4. Erlaube Zugriff

Jetzt kannst du direkt aus der IDE pushen/pullen!

---

#### 7. API-Key in config.json eintragen (falls nötig)

```powershell
# Öffne config.json
code backend/config.json
```

Trage deinen Gemini API-Key ein (falls gefragt).

**⚠️ ACHTUNG:** Nie den API-Key zu Git committen!

---

### ✅ Setup-Checkliste

- [ ] Python 3.8+ installiert (`python --version`)
- [ ] Git installiert (`git --version`)
- [ ] Git konfiguriert (Name & E-Mail)
- [ ] Antigravity-Workspace eingerichtet (oder VS Code/Cursor)
- [ ] Projekt geclont
- [ ] Virtuelle Umgebung erstellt (`backend/venv/`)
- [ ] Dependencies installiert
- [ ] GitHub-Authentifizierung funktioniert
- [ ] Google Gemini API-Key vorhanden (bestehender Key kann genutzt werden!)

---

## 🚀 Quick Start

### Voraussetzungen

- Python 3.8 oder höher
- Git (für Versionskontrolle)
- Google Gemini API-Key

---

### Option 1: Clone from GitHub (Empfohlen)

```powershell
# 1. Repository clonen
git clone https://github.com/baranturhan-commits/Mein_Business.git
cd Mein_Business

# 2. Backend Setup mit virtueller Umgebung
cd backend

# Virtuelle Umgebung erstellen
python -m venv venv

# Virtuelle Umgebung aktivieren
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Dependencies installieren
pip install -r requirements.txt

# 3. Cockpit starten
python start.py
```

---

### Option 2: Lokale Installation

Wenn du das Projekt direkt heruntergeladen hast:

```powershell
# In Backend-Verzeichnis wechseln
cd backend

# Virtuelle Umgebung erstellen
python -m venv venv

# Virtuelle Umgebung aktivieren
venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements.txt

# Cockpit starten
python start.py
```

> **💡 Tipp:** Die virtuelle Umgebung sollte bei jeder Entwicklungssession aktiviert werden:
> ```powershell
> cd backend
> venv\Scripts\activate
> ```

---

## 🔄 Entwicklung & Synchronisation

### Täglicher Workflow

```powershell
# 1. Virtuelle Umgebung aktivieren (falls nicht aktiv)
cd backend
venv\Scripts\activate

# 2. Neueste Änderungen holen
git pull

# 3. Entwickeln...
python start.py

# 4. Änderungen committen & pushen
git add .
git commit -m "Deine Änderungsnachricht"
git push
```

### Neue Dependencies hinzufügen

```powershell
# In aktivierter venv
pip install package-name

# requirements.txt aktualisieren
pip freeze > requirements.txt

# Committen
git add requirements.txt
git commit -m "Add package-name dependency"
git push
```

---

## 📦 Module

### 🔔 Backend
Vollständige Python-basierte Business-Automatisierung:
- **Angebote**: Professionelle Angebotserstellung (PDF & Excel)
- **Lieferscheine**: Abnahmeprotokolle (auch als Blanko-Formular für die Baustelle)
- **Mahnwesen**: KI-gestützte Mahnung mit PDF-Generierung (nur offene Rechnungen)
- **Buchhaltung**: Intelligente Belegverarbeitung
- **Rechnungen**: Automatische Rechnungserstellung mit Status-Tracking
- **Ausgaben**: KI-Belegscanner & Kosten-Tracking
- **Preisliste**: Zentrale Verwaltung von Produkten & Dienstleistungen
- **OP-Pflege**: Zahlungseingangs-Management (Offen/Bezahlt)
- **Mitarbeiter**: Personalverwaltung & Lohnabrechnungen (PDF)
- **Controlling**: Finanz-Dashboard

Siehe [backend/README.md](backend/README.md) für Details.

### 💻 Frontend (Live!)
Moderne Web-Oberfläche unter `http://localhost:5000`:
- **Dashboard-Übersicht**: Schnellzugriff auf alle Bereiche
- **Dokumente**: Angebote, Lieferscheine, Rechnungen verwalten
- **Ausgaben**: Belege scannen (KI) und verwalten
- **Preisliste**: Artikel/Dienstleistungen pflegen
- **Kunden**: Adressbuch verwalten
- **OP-Check**: Zahlungseingänge prüfen

---

## 🛠️ Technologie-Stack

**Backend:**
- Python 3.8+
- Google Gemini AI
- FPDF (PDF-Generierung)

**Versionskontrolle:**
- Git & GitHub
- Repository: [github.com/baranturhan-commits/Mein_Business](https://github.com/baranturhan-commits/Mein_Business)

**Frontend (Geplant):**
- TBD (React/Vue/Next.js)

---

## 📝 Lizenz & Hinweise

Dieses Projekt ist für den privaten/geschäftlichen Gebrauch.

**Wichtige Hinweise:**
- Google Gemini API-Key geheim halten
- Bei SMTP: App-Passwörter verwenden
- Datenschutz beachten bei E-Mail-Versand

---

**Version:** 3.1
**Letztes Update:** 2026-01-02 17:35
