import os
import sys
import shutil

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def archive_junk():
    print("\n🧹 1. Aufräumen (Archivieren)...")
    archive_dir = os.path.join(SCRIPT_DIR, "_ARCHIV")
    
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        print(f"   📂 Archiv-Ordner erstellt: {archive_dir}")

    files_to_move = [
        "setup_sandbox.py", 
        "create_kunden_csv.py", 
        "reset_config.py", 
        "cleanup_junk.py", 
        "list_models.py", 
        "IDEA.md"
    ]
    
    for filename in files_to_move:
        src = os.path.join(SCRIPT_DIR, filename)
        dst = os.path.join(archive_dir, filename)
        
        if os.path.exists(src):
            try:
                shutil.move(src, dst)
                print(f"   📦 Verschoben: {filename}")
            except Exception as e:
                print(f"   ❌ Fehler bei {filename}: {e}")
        # else: print(f"   ℹ️  Nicht da: {filename}")

def fix_logo():
    print("\n🔧 2. Logo-Fix...")
    logo_dir = os.path.join(SCRIPT_DIR, "03_Rechnungen")
    wrong_name = os.path.join(logo_dir, "logo.png.png")
    correct_name = os.path.join(logo_dir, "logo.png")
    
    if os.path.exists(wrong_name):
        try:
            if os.path.exists(correct_name):
                # Target exists, maybe delete wrong one? Or backup?
                # User asked to rename. If target exists, overwrite or warn.
                # Safe: Remove target, rename wrong.
                os.remove(correct_name)
            os.rename(wrong_name, correct_name)
            print("   ✅ logo.png.png -> logo.png korrigiert")
        except Exception as e:
            print(f"   ❌ Fehler beim Umbenennen: {e}")
    else:
        print("   ✅ Keine 'logo.png.png' gefunden (alles ok).")

def create_cockpit_script():
    print("\n🚀 3. Erstelle Cockpit (start.py)...")
    start_py_path = os.path.join(SCRIPT_DIR, "start.py")
    
    code = r'''import os
import sys
import subprocess

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    while True:
        clear_screen()
        print("🚀 BARAN TECH COCKPIT")
        print("---------------------")
        print("[1] 👥 Neuen Kunden anlegen (startet add_client.py)")
        print("[2] 📄 Rechnung schreiben (startet 03_Rechnungen/invoice.py)")
        print("[3] 📧 Rechnungen versenden (startet 01_Mahnwesen/agent.py)")
        print("[4] 📸 Ausgaben scannen (startet 02_Buchhaltung/scanner.py)")
        print("[5] 💰 Finanzen checken (startet 04_Controlling/finance_check.py)")
        print("[x] Beenden")
        
        choice = input("\nAuswahl: ").strip().lower()
        
        cmd = None
        if choice == '1':
            cmd = "python add_client.py"
        elif choice == '2':
            cmd = "python 03_Rechnungen/invoice.py"
        elif choice == '3':
            cmd = "python 01_Mahnwesen/agent.py"
        elif choice == '4':
            cmd = "python 02_Buchhaltung/scanner.py"
        elif choice == '5':
            cmd = "python 04_Controlling/finance_check.py"
        elif choice == 'x':
            print("👋 Bye!")
            break
        
        if cmd:
            print(f"\n⚙️  Starte: {cmd} ...\n")
            try:
                # Use os.system to keep it in same console easily or subprocess.call
                subprocess.call(cmd, shell=True)
            except Exception as e:
                print(f"❌ Fehler: {e}")
            
            input("\n[Enter] für Menü...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAbbruch.")
'''
    try:
        with open(start_py_path, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"   ✅ {start_py_path} erstellt.")
    except Exception as e:
        print(f"   ❌ Fehler beim Erstellen von start.py: {e}")

def main():
    print("🛠️  ORGANIZE & START SETUP")
    archive_junk()
    fix_logo()
    create_cockpit_script()
    print("\n✨ Alles erledigt! Starte jetzt: python start.py")

if __name__ == "__main__":
    main()
