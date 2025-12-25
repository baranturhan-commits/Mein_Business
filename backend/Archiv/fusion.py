import csv
import smtplib
from email.message import EmailMessage
import os
import sys
import io

# Windows Console Encoding Fix
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("🚀 SYSTEM STARTET: Fusion-Protokoll aktiviert...")

# 1. Wir erstellen erst einmal frische Daten (damit es garantiert klappt)
# ---------------------------------------------------------------------
csv_dateiname = "mahnliste.csv"
kunden_daten = [
    ["Name", "Email", "Schulden"],
    ["Herr Mueller", "mueller@beispiel.de", "500 Euro"],
    ["Frau Schmidt", "schmidt@test.com", "120 Euro"],
    ["Firma Bau-Gigant", "info@bau-gigant.de", "9.000 Euro"]
]

# Datei schreiben
with open(csv_dateiname, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file, delimiter=';')
    writer.writerows(kunden_daten)

print(f"✅ Schritt 1: Datei '{csv_dateiname}' wurde erstellt.")


# 2. Jetzt lesen wir die Daten und feuern die Emails ab
# ---------------------------------------------------------------------
print("⏳ Schritt 2: Lese Daten und sende Emails...")

try:
    # Wir öffnen die Verbindung zum Post-Server (muss im anderen Terminal laufen!)
    with smtplib.SMTP('localhost', 1025) as server:
        
        # Wir öffnen die CSV-Datei zum Lesen
        with open(csv_dateiname, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=';')
            
            # Die Schleife: Für JEDEN Kunden in der Liste...
            for kunde in reader:
                print(f"   -> Bearbeite: {kunde['Name']}...")
                
                # Email bauen (personalisierter Text!)
                msg = EmailMessage()
                msg['Subject'] = f"WICHTIG: Offene Rechnung über {kunde['Schulden']}"
                msg['From'] = "buchhaltung@deine-firma.de"
                msg['To'] = kunde['Email']
                
                inhalt = f"""\
Hallo {kunde['Name']},

uns ist aufgefallen, dass der Betrag von {kunde['Schulden']} noch offen ist.
Bitte ueberweisen Sie das Geld sofort, sonst schicken wir unseren KI-Anwalt vorbei.

Mit freundlichen Grueßen,
Dein Automatisierungs-System
"""
                msg.set_content(inhalt)
                
                # Absenden
                server.send_message(msg)

    print("\n✅ FERTIG! Alle 3 Emails wurden versendet.")
    print("👉 Schau jetzt schnell in das ANDERE Terminal-Fenster!")

except ConnectionRefusedError:
    print("\n❌ ALARM: Der Server (Briefkasten) ist zu!")
    print("Hast du das andere Terminal noch offen? (Der Befehl 'py -m aiosmtpd...')")
except Exception as e:
    print(f"\n❌ Fehler: {e}")