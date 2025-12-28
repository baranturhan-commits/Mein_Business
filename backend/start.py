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
        
        if cmd_info:
            rel_path, args = cmd_info
            full_path = os.path.join(BASE_DIR, rel_path)
            
            if os.path.exists(full_path):
                print(f"\n⚙️  Starte: {rel_path} {' '.join(args)} ...\n")
                try:
                    # Baue den kompletten Befehl: [python, script_path, arg1, arg2...]
                    # Versuche, das venv Python zu nutzen, falls vorhanden
                    venv_python = os.path.join(BASE_DIR, "venv", "Scripts", "python.exe")
                    
                    if os.path.exists(venv_python):
                        python_exe = venv_python
                    else:
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
