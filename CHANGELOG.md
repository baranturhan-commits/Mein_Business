# 📝 Projekt-Geschichte - Mein Business

> Diese Datei zeigt, wie das Projekt entstanden ist und was alles gemacht wurde.

---

## 🎯 Was ist dieses Projekt?

**Name:** Mein Business - Automatisiertes Geschäftssystem  
**Was macht es:** Hilft bei Buchhaltung, Rechnungen und Mahnungen - automatisch!  
**Programmiersprache:** Python 3.8+  
**Wo gespeichert:** https://github.com/baranturhan-commits/Mein_Business  
**Entwickler:** Baran Turhan

**Einfach erklärt:**
- Das Programm schreibt Rechnungen automatisch
- Es sendet Mahnungen an Kunden, die nicht bezahlt haben
- Es verwaltet mehrere Firmen (Mandanten) gleichzeitig
- Alles läuft auf deinem Computer

---

## 📅 Wie das Projekt gewachsen ist

### Phase 1: Initial Development (Dez 2024 - Dez 19, 2025)

**Zeitraum:** Vor GitHub-Integration

**Entwickelte Module:**

1. **01_Mahnwesen** - Automatisches Mahnwesen
   - KI-gestützte Extraktion von Schuldnerinformationen
   - Automatische PDF-Generierung von Mahnungen
   - E-Mail-Versand mit PDF-Anhang
   - CSV-basierte Mahnlisten-Verwaltung
   - Test-Server für lokales E-Mail-Testing

2. **02_Buchhaltung** - Buchhaltungs-Modul
   - Intelligente Belegverarbeitung (Bild & PDF)
   - Scanner für Eingangsbelege mit Auto-Archivierung
   - KI-gestützte Kategorisierung via Gemini
   - Duplikat-Erkennung
   - Ausgaben-Tracking via CSV

3. **03_Rechnungen** - Rechnungserstellung
   - Invoice Generator V2
   - Multi-Company Verwaltung
   - KI-Parsing von natürlicher Sprache
   - Automatische Sortierung in Ordner
   - PDF-Generierung mit FPDF

4. **04_Controlling** - Finanz-Dashboard
   - Baran Finance Report im Terminal
   - Einnahmen vs. Ausgaben Vergleich
   - MwSt-Rechner
   - Excel-Report-Generierung

**Technologie:**
- Google Gemini AI (gemini-2.0-flash)
- FPDF für PDF-Generierung
- Python Standard Library

---

### Phase 2: Mehrere Firmen gleichzeitig verwalten (Dez 20, 2025)

**Problem:** Bisher konnte das Programm nur EINE Firma verwalten  
**Lösung:** Umgebaut für MEHRERE Firmen (= "Mandanten")

**Was ist ein Mandant?**
- Stell dir vor, du bist Buchhalter für 3 verschiedene Firmen
- Jede Firma braucht ihre eigenen Rechnungen, Kunden, Einstellungen
- Ein "Mandant" = Eine dieser Firmen

**Wie funktioniert das jetzt:**

1. **Neue Ordnerstruktur:**
   ```
   Mandanten/
   ├── Firma_A/
   │   ├── Rechnungen/      # Nur Rechnungen von Firma A
   │   ├── Kunden/          # Nur Kunden von Firma A
   │   └── Einstellungen    # Logo, Bankdaten von Firma A
   └── Firma_B/
       ├── Rechnungen/      # Nur Rechnungen von Firma B
       └── ...
   ```

2. **Automatische Rechnungsnummern:**
   - Jede Firma hat eigene Nummern
   - Firma A: 2025-001, 2025-002, 2025-003...
   - Firma B: 2025-001, 2025-002, 2025-003...
   - Die Nummern starten jedes Jahr bei 001

3. **Eigene Konfiguration pro Firma:**
   - Firmenname
   - Logo
   - Bankverbindung
   - Geschäftsführer

**Beispiel:**
- Du hast 2 Mandanten: "Baran Tech Solutions" und "Elektroniker Testbetrieb"
- Jeder hat eigene Ordner, Rechnungen, Kunden
- Das Programm fragt dich: "Für welchen Mandanten?"

---

### Phase 3: Scanner kann jetzt auch Mandanten (Dez 22, 2025)

**Was wurde gemacht:**
Der Beleg-Scanner wurde erweitert, damit er mit mehreren Firmen umgehen kann.

**Wie es jetzt funktioniert:**
1. Du scannst eine Quittung (z.B. Tankbeleg)
2. Computer fragt: "Für welchen Mandanten?" → Du wählst z.B. "Elektroniker Testbetrieb"
3. Computer fragt: "Welche Kategorie?" → Du wählst z.B. "Tanken"
4. Computer speichert den Beleg in: `Mandanten/Elektroniker_Testbetrieb/Ausgaben/Tanken/`
5. Falls der Ordner nicht existiert, wird er automatisch erstellt

---

### Phase 5: Zahlungseingangs-Management & Intelligentes Mahnwesen (Dez 26, 2025)

**Problem:** 
- Wir schreiben Rechnungen, aber wissen nicht, ob das Geld jemals angekommen ist
- Risiko: Kunden mahnen, die schon bezahlt haben (sehr peinlich!)
- Keine Übersicht über offene Forderungen

**Lösung: OP-Pflege System (Offene Posten)**

#### Was wurde implementiert:

**1. Status-Spalte in `einnahmen.csv`**
- Neue Spalte: `Status` mit Werten `Offen` oder `Bezahlt`
- Standard bei neuen Rechnungen: `Offen`
- Beispiel:
  ```csv
  Rechnungsnummer;Datum;Kunde;Beschreibung;Betrag_Netto;Betrag_Brutto;Status
  2025-003;22.12.2025;Oma_Erna;Heizung ANBAU;600.00;714.00;Offen
  ```

**2. [check_payments.py](backend/03_Rechnungen/check_payments.py) - Neues Tool erstellt**

Ein interaktives Tool zum Verwalten von Zahlungseingängen:

Features:
- 📊 Übersicht: Zeigt Anzahl und Summen (Gesamt / Offen / Bezahlt)
- 🔍 Interaktive Prüfung aller offenen Rechnungen
- ✅ Status-Update: Markiert Rechnungen als "Bezahlt"
- 💰 Summenberechnung der offenen Forderungen
- 🔄 Rückwärtskompatibel: Funktioniert auch mit alten CSV-Dateien

Workflow:
1. Mandant auswählen
2. Übersicht aller Rechnungen ansehen
3. Für jede offene Rechnung entscheiden: Bezahlt? (j/n/s)
4. Finale Übersicht mit Summen

**3. [invoice.py](backend/03_Rechnungen/invoice.py) - Angepasst**
- Neue Rechnungen bekommen automatisch Status `Offen`
- CSV-Header um `Status`-Spalte erweitert

**4. [agent.py](backend/01_Mahnwesen/agent.py) - Intelligentes Mahnwesen**

Das Mahnwesen wurde SMART gemacht:

Neue Funktionen:
- `load_einnahmen()`: Lädt CSV und filtert nach Status
- `find_pdfs()`: Erweitert um Filterung nach Rechnungsnummern
- Zeigt Status-Übersicht VOR dem Versenden
- Stoppt automatisch, wenn alles bezahlt ist

**WICHTIG:** Nur noch Rechnungen mit Status "Offen" werden gemahnt!

Beispiel-Output:
```
📊 RECHNUNGS-STATUS:
   Gesamt: 5 Rechnungen
   ✅ Bezahlt: 3
   ⏳ Offen: 2

⚠️  Folgende Rechnungen sind noch offen:
   - 2025-003 | Oma_Erna | 714.00€ | vom 22.12.2025
   - 2025-007 | Meier_GmbH | 1250.00€ | vom 24.12.2025

🔎 2 PDF(s) für offene Rechnungen gefunden.
```

Wenn alles bezahlt ist:
```
🎉 Super! Alle Rechnungen sind bezahlt!
   Es gibt nichts zu mahnen.
```

**5. [start.py](backend/start.py) - Menü erweitert**
- Neue Option: `[6] 💶 Zahlungseingänge prüfen (OP pflegen)`
- Direkt aus dem Hauptmenü aufrufbar

#### Vorteile des neuen Systems:

| Vorher | Nachher |
|--------|---------|
| ❌ Keine Ahnung, ob bezahlt | ✅ Klarer Status: Offen/Bezahlt |
| ❌ Risiko: Bezahlte Kunden mahnen | ✅ Nur offene Rechnungen mahnen |
| ❌ Manuell im Kontoauszug suchen | ✅ Zentrale Übersicht |
| ❌ Peinliche Situationen | ✅ Professionell |

#### Workflow in der Praxis:

```
1. Rechnung schreiben (invoice.py)
   └─> Status: "Offen" ✅
   
2. Wöchentliche OP-Pflege (check_payments.py)
   └─> Kontoauszug prüfen
   └─> Geld da? → "Bezahlt" setzen ✅
   
3. Mahnungen versenden (agent.py)
   └─> Nur offene Rechnungen werden gemahnt ✅
   └─> Bezahlte Kunden werden IGNORIERT 🎉
```

#### Getestet:
✅ Neue Rechnung mit Status "Offen" erstellt  
✅ Status auf "Bezahlt" geändert  
✅ Mahnwesen zeigt nur offene Rechnungen  
✅ Mahnwesen stoppt bei bezahlten Rechnungen  
✅ Summenberechnung funktioniert  
✅ Migration alter Einträge ohne Status  

#### Geänderte Dateien:
1. `backend/03_Rechnungen/invoice.py` - Status-Spalte hinzugefügt
2. `backend/03_Rechnungen/check_payments.py` - **NEU erstellt**
3. `backend/01_Mahnwesen/agent.py` - Intelligentes Filtern implementiert
4. `backend/start.py` - Menü-Option hinzugefügt
5. `backend/Mandanten/*/einnahmen.csv` - Status-Spalte hinzugefügt

**Zeitraum:** 26.12.2025, 15:36 - 15:52  
**Entwickler:** Baran Turhan (mit Antigravity AI)

---

### Phase 4: Professionelles Setup (Dez 25, 2025)

**Was heute passiert ist:**  
Das Projekt wurde professionell aufgesetzt, damit man gut damit arbeiten kann.

#### Was wir heute gemacht haben (15:00 - 15:45):

**1. Projekt analysiert und aufgeräumt (15:00)**
- Alle Dateien durchgeschaut
- `requirements.txt` erstellt (Liste aller benötigten Programme)
- `.gitignore` erstellt (sagt Git, welche Dateien ignoriert werden sollen)

**2. Ordner neu organisiert (15:00-15:03)**
**Problem:** Alles war in einem Ordner durcheinander  
**Lösung:** Aufgeteilt in `backend/` und `frontend/`

Vorher:
```
Mein_Business/
├── agent.py
├── scanner.py
├── invoice.py
└── ... (alles gemischt)
```

Nachher:
```
Mein_Business/
├── backend/       # Python-Programme
│   ├── 01_Mahnwesen/
│   ├── 02_Buchhaltung/
│   └── ...
└── frontend/      # Zukünftig: Webseite
```

**3. Git und GitHub eingerichtet (15:03-15:15)**

**Was ist Git?**
- Ein Programm, das sich alle Änderungen merkt
- Wie eine Zeitmaschine für deinen Code
- Du kannst zu jeder alten Version zurück

**Was ist GitHub?**
- Eine Website, wo dein Code gespeichert wird
- Wie Dropbox, aber für Programmierer
- Du kannst von jedem Computer darauf zugreifen

**Was wir gemacht haben:**
- Git installiert
- Eingestellt, wer ich bin (Name: Baran Turhan, E-Mail: baran.turhan@outlook.de)
- Projekt auf GitHub hochgeladen
- Link: https://github.com/baranturhan-commits/Mein_Business

**Probleme gelöst:**
- Fehlende Ordner wurden hinzugefügt (mit `.gitkeep` Dateien)
- PDFs waren blockiert → `.gitignore` angepasst
- Jetzt ist alles komplett online gesichert

**4. Virtuelle Umgebung eingerichtet (15:40-15:42)**

**Was ist eine virtuelle Umgebung?**
- Ein eigener Bereich nur für dieses Projekt
- Verhindert, dass sich verschiedene Projekte stören
- Best Practice bei Python-Entwicklung

**Was gemacht wurde:**
- `backend/venv/` erstellt (die virtuelle Umgebung)
- `frontend/` Ordner vorbereitet (für später)
- README mit Anleitung aktualisiert

**5. Dokumentation geschrieben (15:44-jetzt)**

**Dateien erstellt:**
- `CHANGELOG.md` - Diese Datei hier! Die ganze Geschichte des Projekts
- `DEVELOPER_NOTES.md` - Schnelle Hilfe für Git-Befehle
- `SESSION_PROMPT.md` - Vorlage für neue KI-Sessions

**Warum?**
Damit in Zukunft jeder (auch KI-Assistenten in neuen Sessions) sofort versteht, wie das Projekt funktioniert.

---

## 🏗️ Aktuelle Projekt-Struktur

```
Mein_Business/
├── backend/
│   ├── 01_Mahnwesen/
│   ├── 02_Buchhaltung/
│   ├── 03_Rechnungen/
│   ├── 04_Controlling/
│   ├── Mandanten/
│   │   ├── Baran_Tech_Solutions/
│   │   └── Elektroniker_Testbetrieb/
│   ├── venv/                    # Virtuelle Umgebung (lokal)
│   ├── start.py
│   ├── requirements.txt
│   └── ...
├── frontend/                     # Platzhalter
├── .gitignore
├── README.md
└── CHANGELOG.md                  # Diese Datei
```

---

## 📊 Aktueller Stand (heute: 25.12.2025, 15:45)

**Wie viel ist online:**
- 6 Versionen (Commits) auf GitHub gespeichert
- 37 Dateien im Backend
- 1 Haupt-Branch („main")

**Die letzten Änderungen:**
1. CHANGELOG vereinfacht (diese Änderung gerade)
2. Virtuelle Umgebung + Dokumentation hinzugefügt
3. Projektstruktur in README aktualisiert
4. README mit GitHub-Infos aktualisiert
5. .gitignore für Mandanten-Struktur gefixt
6. Erste Version online gestellt

---

## 🔧 Verwendete Programme & Bibliotheken

**Backend (Python-Teil):**
- Python 3.8+ = Die Programmiersprache
- Google Gemini AI = Liest Texte intelligent (KI)
- FPDF = Erstellt PDF-Dateien

**Entwicklung:**
- Git = Versionskontrolle ("Zeitmaschine für Code")
- GitHub = Online-Speicher für Code
- Virtuelle Umgebung (venv) = Projektbereich isoliert von anderen Projekten
- VS Code / Cursor = Programme zum Code schreiben

**Geplant (Frontend = Webseite):**
- React / Next.js = JavaScript-Framework
- TypeScript = JavaScript mit Typsicherheit
- TailwindCSS = Modernes Styling

---

## 💡 Was ich gelernt habe

**Wichtige Erkenntnisse:**
1. **Mandanten überall:** Alle Programmteile müssen mit mehreren Firmen umgehen können
2. **Leere Ordner:** Git sieht leere Ordner nicht → `.gitkeep` Dateien reinlegen
3. **PDFs in Git:** Mandanten-Rechnungen SOLLEN gespeichert werden, temporäre PDFs NICHT
4. **Virtuelle Umgebung:** Immer verwenden! Verhindert Chaos zwischen Projekten
5. **Dokumentation:** Für KI-Sessions ist eine gute Geschichte wichtig

---

## 📞 Für neue KI-Sessions (Wichtig!)

**Wenn ein KI-Assistent in einer neuen Session hilft:**

1. **Lies zuerst diese Datei (CHANGELOG.md)** - Sie gibt dir den vollständigen Kontext
2. **Dann lies die README.md** - Für Setup-Anweisungen
3. **Bei Git-Problemen:** DEVELOPER_NOTES.md

**Wichtige Dateien:**
- `backend/start.py` = Hauptprogramm (Startpunkt)
- `backend/config.json` = Einstellungen (VORSICHT: Passwörter drin!)
- `backend/Mandanten/*/mandant_config.json` = Einstellungen pro Firma

**Entwicklungs-Philosophie:**
- Sauberer Code ist besser als schnelle Lösungen
- Dokumentation gehört dazu
- Git-Versionen sollen lesbar sein
- Virtuelle Umgebung = Pflicht

---

**Letzte Aktualisierung:** 2025-12-26 15:52  
**Bearbeitet von:** Baran Turhan (mit Antigravity AI)  
**Version:** 2.1 - OP-Pflege & Intelligentes Mahnwesen hinzugefügt

