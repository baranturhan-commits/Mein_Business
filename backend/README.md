# 💼 Mein Business - Automatisierte Buchhaltungs- und Mahnwesen-Lösung

Eine KI-gestützte Automatisierungslösung für kleine Unternehmen zur Verwaltung von Mahnwesen und Buchhaltung mit Google Gemini AI.

---

## 📋 Inhaltsverzeichnis

- [Überblick](#-überblick)
- [Features](#-features)
- [Projektstruktur](#-projektstruktur)
- [Installation](#-installation)
- [Module](#-module)
- [Verwendung](#-verwendung)
- [Konfiguration](#-konfiguration)
- [Entwicklung](#-entwicklung)

---

## 🎯 Überblick

Dieses Projekt bietet eine vollständige Automatisierungslösung für:
- **Automatisches Mahnwesen** mit KI-gestützter Textanalyse
- **Buchhaltung** mit intelligenter Belegverarbeitung
- **PDF-Generierung** für professionelle Mahnungen
- **E-Mail-Versand** von Zahlungserinnerungen
- **Test-Server** für lokales E-Mail-Testing

---

## ✨ Features

### 🔔 Mahnwesen (01_Mahnwesen)
- ✅ KI-gestützte Extraktion von Schuldnerinformationen aus Text
- ✅ Automatische PDF-Generierung von Mahnungen
- ✅ E-Mail-Versand mit PDF-Anhang
- ✅ Validierung von E-Mail-Adressen
- ✅ CSV-basierte Mahnlisten-Verwaltung
- ✅ Test-Server für lokales E-Mail-Testing

### 📊 Buchhaltung (02_Buchhaltung)
- ✅ Intelligente Belegverarbeitung (Bild & PDF)
- ✅ Ausgaben-Tracking via CSV
- ✅ Scanner für Eingangsbelege mit Auto-Archivierung
- ✅ KI-gestützte Kategorisierung
- ✅ KI-gestützte Kategorisierung
- ✅ Duplikat-Erkennung

### 🧾 Rechnungen (03_Rechnungen)
- ✅ **Invoice Generator V2**: Automatische Rechnungserstellung
- ✅ **Multi-Company**: Verwaltung mehrerer Firmenprofile
- ✅ **KI-Parsing**: Verwandelt "Beratung 3h a 100€" in formschöne PDFs
- ✅ **Auto-Sortierung**: Dynamische Ordner nach Firmen & Datum

### 📈 Controlling (04_Controlling)
- ✅ **Baran Finance Report**: Dashboard im Terminal
- ✅ **Finanz-Check**: Vergleicht Einnahmen vs. Ausgaben
- ✅ **MwSt-Rechner**: Zeigt die aktuelle Zahllast an

---

## 📁 Projektstruktur

```
Mein_Business/
│
├── 01_Mahnwesen/              # Mahnwesen-Modul
│   ├── agent.py               # Hauptprogramm für Mahnungen
│   ├── debug_server.py        # Test-SMTP-Server + Web-Interface
│   ├── run_mail_server.bat    # Schnellstart für Test-Server
│   ├── test_models.py         # API-Tests
│   ├── mahnliste.csv          # Mahnliste
│   └── Ausgang_Rechnungen/    # Generierte Rechnungen
│
├── 02_Buchhaltung/            # Buchhaltungs-Modul
│   ├── scanner.py             # Beleg-Scanner
│   ├── list_models.py         # Modell-Übersicht
│   ├── Ausgaben.csv           # Ausgaben-Tracking
│   └── Eingang_Belege/        # Eingehende Belege
│
├── 03_Rechnungen/             # Rechnungs-Modul
│   ├── invoice.py             # Invoice Generator V2
│   ├── config.json            # Firmen-Profile
│   ├── Einnahmen.csv          # Einnahmen-Tracking
│   └── PDFs/                  # Generierte Rechnungen
│
├── 04_Controlling/            # Controlling-Modul
│   └── finance_check.py       # Finanz-Dashboard
│
├── Archiv/                    # Archivierte Dateien
├── IDEA.md                    # Ideen-Sammlung
└── README.md                  # Diese Datei
```

---

## 🚀 Installation

### Voraussetzungen

- Python 3.8 oder höher
- Google Gemini API Key
- (Optional) SMTP-Server für echte E-Mails

### 1. Repository klonen/öffnen

```bash
cd C:\Users\Baran\OneDrive\Arbeit\Mein_Business
```

### 2. Abhängigkeiten installieren

```bash
pip install google-generativeai fpdf
```

### 3. API-Key konfigurieren

Öffne `01_Mahnwesen/agent.py` und trage deinen Google API-Key ein:

```python
GOOGLE_API_KEY = "DEIN_API_KEY_HIER"
```

---

## 📦 Module

### 🔔 Mahnwesen

#### `agent.py` - Hauptprogramm
Intelligenter Agent für automatisches Mahnwesen:

**Funktionen:**
- Extrahiert Schuldnerinformationen aus natürlicher Sprache
- Generiert professionelle PDF-Mahnungen
- Versendet E-Mails mit PDF-Anhang
- Validiert E-Mail-Adressen automatisch

**Beispiel-Verwendung:**
```bash
cd 01_Mahnwesen
python agent.py
```

```
📧 Bitte gib deine Absender-E-Mail-Adresse ein: firma@example.com
📝 Deine Notiz: Max Mustermann (max@example.com) schuldet 150 Euro
```

#### `debug_server.py` - Test-Server
Lokaler SMTP-Server für E-Mail-Testing:

**Features:**
- SMTP-Server auf `localhost:1025`
- Web-Interface auf `http://localhost:8080`
- Zeigt empfangene E-Mails im Browser an
- Perfekt für Tests ohne echten E-Mail-Versand

**Starten:**
```bash
cd 01_Mahnwesen
python debug_server.py
```
Dann öffne: http://localhost:8080

---

### 📊 Buchhaltung

#### `scanner.py` - Beleg-Scanner
Intelligenter Scanner für Eingangsbelege:

**Funktionen:**
- Scannt und analysiert Belege (Bilder & PDFs)
- Extrahiert relevante Informationen
- Speichert Ausgaben in CSV
- Archiviert bearbeitete Dateien automatisch in `erledigt/`
- Benennt Dateien um (YYYY-MM-DD_Firma_Betrag)
- Warnt vor Duplikaten

**Verwendung:**
```bash
cd 02_Buchhaltung
python scanner.py
```

#### `Ausgaben.csv` - Ausgaben-Tracking
CSV-Datei zur Verwaltung aller Ausgaben.

---

### 🧾 Rechnungen

#### `invoice.py` - Invoice Generator V2
Dein Assistent für professionelle Rechnungen.

**Starten:**
```bash
cd 03_Rechnungen
python invoice.py
```
**Features:**
- Fragt dich nach deiner Firma (oder legt neue an).
- Versteht natürliche Sprache: `Rechnung an Adobe für Photoshop-Workshop 2 Tage a 800 EUR`
- Fragt fehlende Adressen automatisch ab.
- Speichert saubere PDFs (`Datum_Rechnung_Nr.pdf`) im Firmenordner.

---

### 📈 Controlling

#### `finance_check.py` - Finanz-Dashboard
Dein Überblick über Einnahmen, Ausgaben und Gewinn.

**Starten:**
```bash
cd 04_Controlling
python finance_check.py
```
**Features:**
- Liest automatisch `Einnahmen.csv` und `Ausgaben.csv`.
- Berechnet Gewinn (Netto) und Umsatzsteuer-Zahllast.
- Robust gegen Formatierungsfehler (Währungszeichen etc.).

---

## 🎮 Verwendung

### Schnellstart: Mahnungen versenden

1. **Test-Server starten** (für lokales Testing):
   ```bash
   cd 01_Mahnwesen
   python debug_server.py
   ```

2. **In neuem Terminal: Agent starten**:
   ```bash
   cd 01_Mahnwesen
   python agent.py
   ```

3. **Eingabe tätigen**:
   ```
   📧 Absender-E-Mail: deine@email.de
   📝 Notiz: Max Mustermann (max@example.com) schuldet 250 Euro
   ```

4. **Ergebnis prüfen**:
   - PDF wird erstellt: `Mahnung_Max_Mustermann.pdf`
   - E-Mail wird versendet (sichtbar auf http://localhost:8080)

### Für Produktiv-Einsatz

Passe die SMTP-Einstellungen in `agent.py` an:

```python
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_PASSWORD = 'dein_app_passwort'
```

---

## ⚙️ Konfiguration

### E-Mail-Server Einstellungen (`agent.py`)

```python
# Lokales Testing
SMTP_SERVER = 'localhost'
SMTP_PORT = 1025
EMAIL_PASSWORD = ''

# Gmail (Beispiel)
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_PASSWORD = 'dein_app_passwort'
```

### Google Gemini API

Aktuell verwendetes Modell: `gemini-2.0-flash`

Ändere das Modell in `agent.py`:
```python
model = genai.GenerativeModel('gemini-2.0-flash')
```

---

## 🛠️ Entwicklung

### Neue Ideen hinzufügen

Nutze die `IDEA.md` für neue Feature-Ideen:

```markdown
### #idee [NUMMER] - [TITEL]
**Datum:** 2025-12-17
**Status:** 🔵 Neu
**Beschreibung:** ...
```

### Projekt erweitern

Die modulare Struktur ermöglicht einfache Erweiterungen:

1. Neues Modul erstellen (z.B. `03_Rechnungswesen/`)
2. Ähnliche Struktur wie bestehende Module verwenden
3. Google Gemini für KI-Funktionen nutzen

---

## 📝 Lizenz & Hinweise

Dieses Projekt ist für den privaten/geschäftlichen Gebrauch.

**Wichtige Hinweise:**
- Google Gemini API-Key geheim halten
- Bei SMTP: App-Passwörter verwenden (nicht Standard-Passwort)
- Datenschutz beachten bei E-Mail-Versand

---

## 🤝 Support & Kontakt

Bei Fragen oder Problemen:
1. Prüfe die Logs in der Konsole
2. Teste mit `debug_server.py`
3. Überprüfe API-Key und SMTP-Einstellungen

---

## 🚧 Roadmap

Siehe `IDEA.md` für geplante Features, z.B.:
- 🔄 Automatische Dateiorganisation
- 🤖 KI-basierte Kategorisierung
- 📧 Erweiterte E-Mail-Templates
- 📊 Dashboard für Übersicht

---

**Version:** 1.0  
**Letztes Update:** 2025-12-19
