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
