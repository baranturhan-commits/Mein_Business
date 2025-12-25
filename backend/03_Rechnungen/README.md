# 🧾 Invoice Generator V2

Der **Invoice Generator** wurde komplett überarbeitet, um Multi-Company-Support, verbesserte Ordnerstrukturen und ein professionelleres Layout zu bieten.

## 🚀 Neue Features (V2 Update)

### 1. 🏢 Multi-Company Support (Profil-Manager)
*   Verwalte **mehrere Firmen** in einer einzigen Installation.
*   Beim Start kannst du wählen:
    1.  Bestehendes Profil nutzen
    2.  `➕ Neue Firma anlegen`
*   Die Daten werden in `config.json` als Liste gespeichert.

### 2. 📂 Dynamische Ordnerstruktur & Dateinamen
*   Rechnungen werden automatisch sortiert:
    *   `./PDFs/[Firmenname]/`
*   **Dateinamen** enthalten jetzt das Datum für bessere Übersicht:
    *   `DD-MM-YYYY_Rechnung_[Nr].pdf`

### 3. 📅 Intelligente Datums-Logik
*   Die KI versucht, das Datum aus der Eingabe zu lesen.
*   **Fallback**: Wenn kein Datum erkannt wird (oder "FEHLT"), setzt das Skript automatisch das **heutige Datum** (`datetime.now()`). Keine leeren Datumsfelder mehr!

### 4. 🎨 Design & Layout (Clean Print)
*   **Kein HTML-Müll**: Alle `<b>` Tags wurden verbannt.
*   **Formatierung**:
    *   Reiner Text im Header (Rechnungs-Nr, Datum).
    *   Rechtsbündige Preise für perfekte Lesbarkeit.
    *   **"EUR"** statt "€"-Symbol, um Darstellungsfehler zu vermeiden.
    *   Spalten: `Pos. | Beschreibung | Menge | Einzelpreis | Gesamtpreis`.

### 5. 🤖 Verbesserte KI-Logik
*   **0,00 € Filter**: Positionen mit 0 Euro werden automatisch entfernt (außer "gratis" steht dabei).
*   **Adress-Check**: Wenn die Adresse fehlt, fragt das Terminal interaktiv nach, statt "FEHLT" ins PDF zu schreiben.

## 🛠️ Verwendung

1.  Starte das Skript:
    ```bash
    python invoice.py
    ```
2.  Wähle dein Firmen-Profil.
3.  Gib deinen Rechnungswunsch ein (z.B. "Rechnung an Müller für Beratung 3h a 100 Euro").
4.  Überprüfe die Vorschau und erstelle das PDF.

## ⚙️ Konfiguration
*   **API Key**: Wird fest im Skript (`invoice.py`) oben verwaltet.
*   **Daten**: In `config.json` gespeichert.

---
*Zuletzt aktualisiert: 19.12.2025*
