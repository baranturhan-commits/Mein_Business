"""
Automatisches Backup-System für Mein Business
Erstellt ZIP-Archive aller wichtigen Daten
"""

import os
import zipfile
from datetime import datetime
from pathlib import Path
import shutil

def create_backup():
    """Erstellt ein vollständiges Backup aller Mandanten-Daten"""
    
    # Basis-Pfade
    backend_dir = Path(__file__).parent
    backup_dir = backend_dir / 'Backups'
    backup_dir.mkdir(exist_ok=True)
    
    # Backup-Dateiname mit Timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_filename = backup_dir / f'backup_{timestamp}.zip'
    
    print(f"📦 Erstelle Backup: {backup_filename.name}")
    
    # Ordner und Dateien die gesichert werden sollen
    backup_targets = [
        'Mandanten',
        '01_Mahnwesen',
        '02_Buchhaltung',
        '03_Rechnungen',
        '04_Controlling',
        '05_Angebote',
        '06_Lieferscheine',
        'config.json',
        'add_client.py',
        'start.py',
        'excel_utils.py'
    ]
    
    # Ausschließen
    exclude_patterns = [
        '__pycache__',
        '.pyc',
        'venv',
        '.venv',
        'logs',
        'Backups'
    ]
    
    def should_exclude(path_str):
        """Prüft ob ein Pfad ausgeschlossen werden soll"""
        return any(pattern in path_str for pattern in exclude_patterns)
    
    # ZIP erstellen
    with zipfile.ZipFile(backup_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        files_added = 0
        
        for target in backup_targets:
            target_path = backend_dir / target
            
            if not target_path.exists():
                print(f"  ⚠️  Überspringe (nicht gefunden): {target}")
                continue
            
            if target_path.is_file():
                # Einzelne Datei
                if not should_exclude(str(target_path)):
                    zipf.write(target_path, target_path.relative_to(backend_dir))
                    files_added += 1
                    print(f"  ✅ Datei: {target}")
            
            elif target_path.is_dir():
                # Kompletter Ordner
                for root, dirs, files in os.walk(target_path):
                    # Ausschließen von Ordnern
                    dirs[:] = [d for d in dirs if not should_exclude(d)]
                    
                    for file in files:
                        file_path = Path(root) / file
                        if not should_exclude(str(file_path)):
                            arcname = file_path.relative_to(backend_dir)
                            zipf.write(file_path, arcname)
                            files_added += 1
                
                print(f"  ✅ Ordner: {target}")
    
    # Statistik
    backup_size = backup_filename.stat().st_size / (1024 * 1024)  # MB
    
    print(f"\n✅ Backup erfolgreich erstellt!")
    print(f"📁 Speicherort: {backup_filename}")
    print(f"📊 Dateien: {files_added}")
    print(f"💾 Größe: {backup_size:.2f} MB")
    
    # Alte Backups aufräumen (behalte nur die letzten 10)
    cleanup_old_backups(backup_dir)
    
    return backup_filename

def cleanup_old_backups(backup_dir, keep_count=10):
    """Löscht alte Backups, behält nur die neuesten"""
    
    backups = sorted(backup_dir.glob('backup_*.zip'), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if len(backups) > keep_count:
        print(f"\n🧹 Räume alte Backups auf (behalte {keep_count} neueste)")
        for old_backup in backups[keep_count:]:
            print(f"  🗑️  Lösche: {old_backup.name}")
            old_backup.unlink()

def restore_backup(backup_file):
    """Stellt ein Backup wieder her"""
    
    backup_path = Path(backup_file)
    if not backup_path.exists():
        print(f"❌ Backup nicht gefunden: {backup_file}")
        return False
    
    backend_dir = Path(__file__).parent
    
    print(f"📂 Entpacke Backup: {backup_path.name}")
    print("⚠️  ACHTUNG: Bestehende Dateien werden überschrieben!")
    
    confirm = input("Fortfahren? (ja/nein): ").strip().lower()
    if confirm != 'ja':
        print("❌ Wiederherstellung abgebrochen")
        return False
    
    with zipfile.ZipFile(backup_path, 'r') as zipf:
        zipf.extractall(backend_dir)
    
    print("✅ Backup erfolgreich wiederhergestellt!")
    return True

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--restore':
        # Wiederherstellungs-Modus
        if len(sys.argv) < 3:
            print("❌ Fehler: Backup-Datei angeben")
            print("Verwendung: python backup.py --restore <backup_datei.zip>")
        else:
            restore_backup(sys.argv[2])
    else:
        # Backup erstellen
        create_backup()
