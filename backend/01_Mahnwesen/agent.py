import os
import sys
import json
import csv
import smtplib
import shutil
import datetime
import difflib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Force UTF-8 for Console
sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIG & PATHS ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
MANDANTEN_DIR = os.path.join(BASE_DIR, "Mandanten")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# Log File remains local to the script for simplicity
LOG_FILE = os.path.join(SCRIPT_DIR, "versand_log.csv")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# --- LOGGING ---
def log_action(filename, recipient, status, mandant):
    try:
        file_exists = os.path.exists(LOG_FILE)
        with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            if not file_exists:
                writer.writerow(['Zeitstempel', 'Mandant', 'Dateiname', 'Empfänger', 'Status'])
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([timestamp, mandant, filename, recipient, status])
    except Exception as e:
        print(f"⚠️  Log-Fehler: {e}")

# --- MANDANTEN & FILES ---
def list_mandanten():
    if not os.path.exists(MANDANTEN_DIR):
        print(f"❌ '{MANDANTEN_DIR}' nicht gefunden.")
        return []
    items = [d for d in os.listdir(MANDANTEN_DIR) if os.path.isdir(os.path.join(MANDANTEN_DIR, d))]
    return sorted(items)

def load_kunden(mandant_path):
    csv_path = os.path.join(mandant_path, "kunden.csv")
    customers = []
    if os.path.exists(csv_path):
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    if row.get('Firma') and row.get('Email'): 
                        customers.append(row)
        except Exception as e:
            print(f"⚠️  CSV Fehler: {e}")
    return customers

def load_einnahmen(mandant_path):
    """
    Lädt alle Rechnungen aus einnahmen.csv und gibt nur offene zurück.
    """
    csv_path = os.path.join(mandant_path, "einnahmen.csv")
    all_invoices = []
    open_invoices = []
    
    if not os.path.exists(csv_path):
        return all_invoices, open_invoices
    
    try:
        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                all_invoices.append(row)
                # Status-Spalte prüfen (Standard: Offen bei Fehlen)
                status = row.get('Status', 'Offen').strip()
                if status == 'Offen':
                    open_invoices.append(row)
    except Exception as e:
        print(f"⚠️  Fehler beim Lesen von einnahmen.csv: {e}")
    
    return all_invoices, open_invoices

def find_pdfs(mandant_path, open_invoice_numbers=None):
    """
    Sucht rekursiv nach PDFs im 'Rechnungen' Ordner des Mandanten.
    Ignoriert den 'Gesendet' Ordner.
    Filtert nach Rechnungsnummern, wenn open_invoice_numbers angegeben ist.
    """
    rechnungen_dir = os.path.join(mandant_path, "Rechnungen")
    pdf_files = []
    
    if not os.path.exists(rechnungen_dir):
        return []

    for root, dirs, files in os.walk(rechnungen_dir):
        # Exclude 'Gesendet' directory
        if "Gesendet" in dirs:
            dirs.remove("Gesendet")
            
        for file in files:
            if file.lower().endswith(".pdf"):
                full_path = os.path.join(root, file)
                
                # Filter by invoice numbers if provided
                if open_invoice_numbers:
                    # Check if any of the open invoice numbers is in the filename
                    if any(inv_nr in file for inv_nr in open_invoice_numbers):
                        pdf_files.append(full_path)
                else:
                    pdf_files.append(full_path)
                
    return pdf_files

# --- CONFIG / SMTP ---
def get_smtp_config():
    """
    Versucht, SMTP-Daten aus der config.json zu laden. 
    Nimmt den ersten verfügbaren Eintrag oder fragt nach.
    """
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except: pass
    
    # Check for profiles with smtp
    found_smtp = None
    if 'profiles' in config and isinstance(config['profiles'], list):
        for p in config['profiles']:
            if 'smtp' in p and p['smtp'].get('server'):
                found_smtp = p['smtp']
                break
    
    if found_smtp:
        return found_smtp
        
    print("\n⚠️  Keine SMTP-Konfiguration gefunden.")
    print("Bitte einmalig eingeben (wird zentral gespeichert):")
    
    new_smtp = {}
    new_smtp['server'] = input("SMTP Server: ").strip()
    new_smtp['port'] = input("SMTP Port: ").strip()
    new_smtp['email'] = input("Email: ").strip()
    new_smtp['password'] = input("Passwort: ").strip()
    
    # Save simply as a "Default" profile if list empty, else append/update
    if 'profiles' not in config: config['profiles'] = []
    if not config['profiles']:
        config['profiles'].append({'firma': 'Default Agentur', 'smtp': new_smtp})
    else:
        config['profiles'][0]['smtp'] = new_smtp
        
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print("✅ Gespeichert.")
    except Exception as e:
        print(f"❌ Fehler beim Speichern: {e}")
        
    return new_smtp

# --- MATCHING ---
def match_customer(filename, customers):
    fn_clean = filename.lower().replace('_', ' ').replace('-', ' ')
    
    best_match = None
    max_score = 0
    
    for cust in customers:
        raw_name = cust.get('Firma', '')
        if not raw_name: continue
        
        cust_clean = raw_name.lower().replace('_', ' ').replace('-', ' ').strip()
        
        # 1. Exact Substring
        if cust_clean in fn_clean:
            return cust
            
        # 2. Fuzzy
        score = difflib.SequenceMatcher(None, cust_clean, fn_clean).ratio()
        if score > 0.6 and score > max_score:
            max_score = score
            best_match = cust
            
    return best_match

# --- MAILING ---
def send_mail(smtp_conf, recipient, subject, body, attachment_path):
    msg = MIMEMultipart()
    msg['From'] = smtp_conf['email']
    msg['To'] = recipient
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'html'))
    
    if attachment_path:
        filename = os.path.basename(attachment_path)
        try:
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename= {filename}")
            msg.attach(part)
        except Exception as e:
            print(f"❌ Anhang-Fehler: {e}")
            return False
            
    try:
        server = smtplib.SMTP(smtp_conf['server'], int(smtp_conf['port']))
        server.starttls()
        server.login(smtp_conf['email'], smtp_conf['password'])
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"❌ SMTP Send Error: {e}")
        return False

# --- MAIN ---
def main():
    clear_screen()
    print("📧 AGENTUR MAHNWESEN BOT")
    print("=========================")
    
    # 1. Mandant wählen
    mandanten = list_mandanten()
    if not mandanten:
        print("❌ Keine Mandanten gefunden.")
        return
        
    print("Für welchen Mandanten möchtest du versenden?")
    for i, m in enumerate(mandanten, 1):
        print(f"[{i}] {m}")
        
    choice = input("\nAuswahl: ").strip()
    if not choice.isdigit(): return
    idx = int(choice) - 1
    if not (0 <= idx < len(mandanten)): return
    
    selected_mandant = mandanten[idx]
    mandant_path = os.path.join(MANDANTEN_DIR, selected_mandant)
    
    print(f"\n📂 Lade Daten für: {selected_mandant} ...")
    
    # 2. Load Data
    customers = load_kunden(mandant_path)
    
    # Lade Einnahmen und filtere nach Status
    all_invoices, open_invoices = load_einnahmen(mandant_path)
    
    print(f"\n📊 RECHNUNGS-STATUS:")
    print(f"   Gesamt: {len(all_invoices)} Rechnungen")
    print(f"   ✅ Bezahlt: {len(all_invoices) - len(open_invoices)}")
    print(f"   ⏳ Offen: {len(open_invoices)}")
    
    if not open_invoices:
        print("\n🎉 Super! Alle Rechnungen sind bezahlt!")
        print("   Es gibt nichts zu mahnen.")
        input("\n[Enter] zum Beenden...")
        return
    
    # Extrahiere Rechnungsnummern der offenen Rechnungen
    open_invoice_numbers = [inv['Rechnungsnummer'] for inv in open_invoices if 'Rechnungsnummer' in inv]
    
    print(f"\n⚠️  Folgende Rechnungen sind noch offen:")
    for inv in open_invoices:
        inv_nr = inv.get('Rechnungsnummer', 'N/A')
        kunde = inv.get('Kunde', 'N/A')
        betrag = inv.get('Betrag_Brutto', 'N/A')
        datum = inv.get('Datum', 'N/A')
        print(f"   - {inv_nr} | {kunde} | {betrag}€ | vom {datum}")
    
    # Lade nur PDFs für offene Rechnungen
    pdfs = find_pdfs(mandant_path, open_invoice_numbers)
    
    if not pdfs:
        print("\n⚠️  Keine PDFs für offene Rechnungen gefunden.")
        print("   Hinweis: PDFs sollten die Rechnungsnummer im Dateinamen haben.")
        return
        
    print(f"\n🔎 {len(pdfs)} PDF(s) für offene Rechnungen gefunden.")
    
    # 3. SMTP Config
    smtp_conf = get_smtp_config()
    if not smtp_conf: return
    
    # 4. Processing Loop
    print("\n---------------------------------------------------")
    print(f"{'DATEI':<30} | {'EMPFÄNGER':<30}")
    print("---------------------------------------------------")
    
    matches = []
    for pdf in pdfs:
        fname = os.path.basename(pdf)
        cust = match_customer(fname, customers)
        recipient = cust['Email'] if cust else "???"
        print(f"{fname[:28]:<30} | {recipient:<30}")
        if cust:
            matches.append((pdf, cust))
            
    if not matches:
        print("\n❌ Keine Zuordnungen möglich.")
        return
        
    print(f"\n🚀 {len(matches)} Emails bereit zum Senden.")
    if input("Starten? (j/n): ").lower() != 'j':
        print("Abbruch.")
        return
        
    # 5. Sending
    sent_dir = os.path.join(mandant_path, "Rechnungen", "Gesendet")
    if not os.path.exists(sent_dir): os.makedirs(sent_dir)
    
    print("\nVersende...")
    for pdf_path, cust in matches:
        fname = os.path.basename(pdf_path)
        
        # Email Content
        subj = f"Rechnung von {selected_mandant.replace('_', ' ')}"
        anrede = cust.get('Anrede', 'Sehr geehrte Damen und Herren')
        body = f"""
        <html><body>
        <p>{anrede},</p>
        <p>anbei erhalten Sie Ihre Rechnung.</p>
        <p>Mit freundlichen Grüßen<br>{selected_mandant.replace('_', ' ')}</p>
        </body></html>
        """
        
        print(f"📤 Sende {fname} an {cust['Email']} ... ", end="")
        if send_mail(smtp_conf, cust['Email'], subj, body, pdf_path):
            print("✅ OK")
            log_action(fname, cust['Email'], "SENT", selected_mandant)
            
            # Move to Sent
            try:
                shutil.move(pdf_path, os.path.join(sent_dir, fname))
            except Exception as e:
                print(f" (Move Error: {e})")
        else:
            print("❌ FEHLER")
            log_action(fname, cust['Email'], "ERROR", selected_mandant)
            
    print("\n🏁 Vorgang abgeschlossen.")
    input("[Enter] zum Beenden...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAbbruch.")