import os
import sys
import subprocess

# Force UTF-8 for Windows consoles
sys.stdout.reconfigure(encoding='utf-8')

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    # 1. Ermittle das Basis-Verzeichnis (wo LIEGT dieses start.py?)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # --- AUTO-INSTALL DEPENDENCIES ---
    required_modules = ['pandas', 'openpyxl', 'reportlab']
    missing = []
    for mod in required_modules:
        try:
            __import__(mod)
        except ImportError:
            missing.append(mod)
            
    if missing:
        print(f"⚠️  Es fehlen benötigte Module: {', '.join(missing)}")
        print("Versuche automatische Installation...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing)
            print("✅ Installation erfolgreich! Bitte warten...")
            import time; time.sleep(2)
        except Exception as e:
            print(f"❌ Installation fehlgeschlagen: {e}")
            input("Drücken Sie Enter zum Beenden.")
            return
    # ---------------------------------

    while True:
        clear_screen()
        print(f"📂 Working Directory: {BASE_DIR}")
        print("🚀 BARAN TECH COCKPIT - AGENTUR MODE")
        print("------------------------------------")
        print("[1] 🏢 Neuen Mandanten anlegen")
        print("[2] 👤 Neuen Kunden für Mandanten anlegen")
        print("[3] 📄 Rechnung schreiben (startet 03_Rechnungen/invoice.py)")
        print("[4] 📧 Rechnungen versenden (startet 01_Mahnwesen/agent.py)")
        print("[5] 📸 Ausgaben scannen (startet 02_Buchhaltung/scanner.py)")
        print("[6] 💶 Zahlungseingänge prüfen (OP pflegen)")
        print("[7] 💰 Finanzen checken (startet 04_Controlling/finance_check.py)")
        print("[8] 📝 Angebot erstellen (startet 05_Angebote/offer.py)")
        print("[9] 🚚 Lieferschein / Protokoll (startet 06_Lieferscheine/delivery.py)")
        print("[x] Beenden")
        
        choice = input("\nAuswahl: ").strip().lower()
        
        if choice == 'x':
            print("👋 Bye!")
            break

        # Definition der Befehle
        # Format: (Script_Relative_Path, [Arguments_List])
        cmd_info = None
        
        if choice == '1':
            cmd_info = ("add_client.py", ["mandant"])
        elif choice == '2':
            cmd_info = ("add_client.py", ["kunde"])
        elif choice == '3':
            cmd_info = (os.path.join("03_Rechnungen", "invoice.py"), [])
        elif choice == '4':
            cmd_info = (os.path.join("01_Mahnwesen", "agent.py"), [])
        elif choice == '5':
            cmd_info = (os.path.join("02_Buchhaltung", "scanner.py"), [])
        elif choice == '6':
            cmd_info = (os.path.join("03_Rechnungen", "check_payments.py"), [])
        elif choice == '7':
            cmd_info = (os.path.join("04_Controlling", "finance_check.py"), [])
        elif choice == '8':
            cmd_info = (os.path.join("05_Angebote", "offer.py"), [])
        elif choice == '9':
            cmd_info = (os.path.join("06_Lieferscheine", "delivery.py"), [])
        
        if cmd_info:
            rel_path, args = cmd_info
            full_path = os.path.join(BASE_DIR, rel_path)
            
            if os.path.exists(full_path):
                print(f"\n⚙️  Starte: {rel_path} {' '.join(args)} ...\n")
                try:
                    # Baue den kompletten Befehl: [python, script_path, arg1, arg2...]
                    # Versuche, das venv Python zu nutzen, falls vorhanden
                    # Immer den aktuellen Interpreter nutzen (venv oder global, so wie start.py läuft)
                    python_exe = sys.executable
                    
                    cmd_list = [python_exe, full_path] + args
                    subprocess.call(cmd_list)
                except Exception as e:
                    print(f"❌ Fehler beim Ausführen: {e}")
            else:
                print(f"\n\033[91m❌ FEHLER: Datei nicht gefunden!\033[0m")
                print(f"Gesucht wurde: {full_path}")
        else:
            print("\nUngültige Auswahl.")
        
        input("\n[Enter] für Menü...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAbbruch.")
