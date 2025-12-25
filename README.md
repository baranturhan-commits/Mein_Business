# 💼 Mein Business - Business Automation Monorepo

Eine KI-gestützte Automatisierungslösung für kleine Unternehmen zur Verwaltung von Mahnwesen, Buchhaltung, Rechnungen und Controlling mit Google Gemini AI.

---

## 🏗️ Projekt-Struktur

Dieses Projekt ist als Monorepo organisiert:

```
Mein_Business/
├── backend/          # Python Business Automation Backend
│   ├── 01_Mahnwesen/        # Automatisches Mahnwesen
│   ├── 02_Buchhaltung/      # Buchhaltung & Belegverarbeitung
│   ├── 03_Rechnungen/       # Rechnungserstellung
│   ├── 04_Controlling/      # Finanz-Dashboard
│   └── README.md            # Backend Dokumentation
│
└── frontend/         # Web Interface (Coming Soon)
    └── ...
```

---

## 🚀 Quick Start

### Option 1: Clone from GitHub (Empfohlen)

```powershell
# Repository clonen
git clone https://github.com/baranturhan-commits/Mein_Business.git
cd Mein_Business

# Backend Setup
cd backend
pip install -r requirements.txt

# Cockpit starten
python start.py
```

### Option 2: Lokale Installation

Wenn du das Projekt direkt heruntergeladen hast:

```powershell
# In Backend-Verzeichnis wechseln
cd backend

# Abhängigkeiten installieren
pip install -r requirements.txt

# Cockpit starten
python start.py
```

---

## 🔄 Entwicklung & Synchronisation

### Änderungen committen & pushen
```powershell
git add .
git commit -m "Deine Änderungsnachricht"
git push
```

### Neueste Änderungen holen
```powershell
git pull
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
