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

#### 3. IDE installieren (VS Code oder Cursor)

**VS Code (Empfohlen für Anfänger):**
1. Download: https://code.visualstudio.com/
2. Installiere + folgende Extensions:
   - Python (Microsoft)
   - GitLens
   - Pylance

**Cursor (Empfohlen für AI-Entwicklung):**
1. Download: https://cursor.sh/
2. Basiert auf VS Code, aber mit KI-Integration

---

#### 4. Google Gemini API-Key besorgen

1. Gehe zu: https://aistudio.google.com/app/apikey
2. Melde dich mit Google-Account an
3. Klicke "Create API Key"
4. Kopiere den Key (sicher aufbewahren!)

---

#### 5. Projekt clonen & einrichten

**In VS Code/Cursor:**
1. Öffne Terminal (`` Strg+` ``)
2. Führe folgende Befehle aus:

```powershell
# Repository clonen
git clone https://github.com/baranturhan-commits/Mein_Business.git
cd Mein_Business

# Backend-Ordner öffnen in IDE
code backend  # für VS Code
# oder: cursor backend  # für Cursor

# Virtuelle Umgebung erstellen
cd backend
python -m venv venv

# Virtuelle Umgebung aktivieren
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Dependencies installieren
pip install -r requirements.txt
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
- [ ] IDE installiert (VS Code oder Cursor)
- [ ] Git konfiguriert (Name & E-Mail)
- [ ] Projekt geclont
- [ ] Virtuelle Umgebung erstellt (`backend/venv/`)
- [ ] Dependencies installiert
- [ ] GitHub-Authentifizierung funktioniert
- [ ] Google Gemini API-Key vorhanden

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
- **Mahnwesen**: KI-gestützte Mahnung mit PDF-Generierung
- **Buchhaltung**: Intelligente Belegverarbeitung
- **Rechnungen**: Automatische Rechnungserstellung
- **Controlling**: Finanz-Dashboard

Siehe [backend/README.md](backend/README.md) für Details.

### 💻 Frontend (Geplant)
Moderne Web-Oberfläche für:
- Dashboard-Übersicht
- Manuelle Dateneingabe
- Visualisierung von Finanzdaten
- Verwaltung von Mandanten und Kunden

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

**Version:** 2.0  
**Letztes Update:** 2025-12-25
