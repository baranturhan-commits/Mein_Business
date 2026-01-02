"""
API Server für Mein Business Admin Dashboard
Flask-basierte REST API für Frontend-Zugriff
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from pathlib import Path
import json
import csv
from datetime import datetime
from dotenv import load_dotenv
import os
import pandas as pd

# Load environment variables
load_dotenv()

# Import local modules
import excel_utils
import preisliste_import  # For price list import functionality
import offer_generator    # For offer PDF generation

# Import logger
from logger import get_logger
logger = get_logger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Paths
BACKEND_DIR = Path(__file__).parent
MANDANTEN_DIR = BACKEND_DIR / 'Mandanten'

@app.route('/')
def index():
    """Health check"""
    return jsonify({
        'status': 'online',
        'service': 'Mein Business API',
        'version': '1.0'
    })

@app.route('/api/mandanten', methods=['GET'])
def get_mandanten():
    """Liste aller Mandanten mit Basisinformationen"""
    try:
        mandanten = []
        
        if not MANDANTEN_DIR.exists():
            return jsonify({'mandanten': []})
        
        for mandant_dir in MANDANTEN_DIR.iterdir():
            if not mandant_dir.is_dir():
                continue
            
            # Lade Mandanten-Config
            config_file = mandant_dir / 'mandant_config.json'
            mandant_info = {
                'id': mandant_dir.name,
                'name': mandant_dir.name.replace('_', ' '),
                'path': str(mandant_dir)
            }
            
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    mandant_info['name'] = config.get('firmenname', mandant_info['name'])
                    mandant_info['config'] = config
            
            mandanten.append(mandant_info)
        
        logger.info(f"Mandanten geladen: {len(mandanten)}")
        return jsonify({'mandanten': mandanten})
    
    except Exception as e:
        logger.error(f"Fehler beim Laden der Mandanten: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/stats', methods=['GET'])
def get_mandant_stats(mandant_id):
    """Detaillierte Statistiken für einen Mandanten"""
    try:
        mandant_dir = MANDANTEN_DIR / mandant_id
        
        if not mandant_dir.exists():
            return jsonify({'error': 'Mandant nicht gefunden'}), 404
        
        stats = {
            'mandant_id': mandant_id,
            'einnahmen': get_einnahmen_stats(mandant_dir),
            'ausgaben': get_ausgaben_stats(mandant_dir),
            'rechnungen': get_rechnungen_stats(mandant_dir),
            'kunden': get_kunden_count(mandant_dir)
        }
        
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Fehler beim Laden der Stats für {mandant_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_einnahmen_stats(mandant_dir):
    """Statistiken aus einnahmen.xlsx oder einnahmen.csv"""
    # Prüfe xlsx in Einnahmen/
    xlsx_file = mandant_dir / 'Einnahmen' / 'einnahmen.xlsx'
    csv_file = mandant_dir / 'Einnahmen' / 'einnahmen.csv'
    old_csv = mandant_dir / 'einnahmen.csv'
    
    if not (xlsx_file.exists() or csv_file.exists() or old_csv.exists()):
        return {'total': 0, 'offen': 0, 'bezahlt': 0, 'anzahl': 0}
    
    total = 0
    offen = 0
    bezahlt = 0
    count = 0
    
    try:
        data = None
        if xlsx_file.exists():
            import excel_utils
            data = excel_utils.read_data(str(xlsx_file), 'Einnahmen')
            
        elif csv_file.exists():
            with open(csv_file, 'r', encoding='utf-8') as f:
                 data = list(csv.DictReader(f))
                 
        elif old_csv.exists():
             with open(old_csv, 'r', encoding='utf-8') as f:
                 data = list(csv.DictReader(f))
        
        if data:
            for row in data:
                count += 1
                try:
                    # Clean number string (1.234,56 -> 1234.56 or 1234.56 -> 1234.56)
                    raw_current = str(row.get('Betrag_Netto', 0))
                    # Fallback to Brutto if Netto empty?
                    if not raw_current or raw_current == 'None':
                         raw_current = str(row.get('Betrag_Brutto', 0))
                         
                    # Replace German comma if present
                    if ',' in raw_current and '.' in raw_current:
                         # 1.000,50 -> Remove dot, replace comma
                         raw_current = raw_current.replace('.', '').replace(',', '.')
                    elif ',' in raw_current:
                         # 100,50 -> 100.50
                         raw_current = raw_current.replace(',', '.')
                         
                    betrag = float(raw_current)
                    
                    total += betrag
                    status = row.get('Status', 'Offen')
                    if status == 'Offen':
                        offen += betrag
                    else:
                        bezahlt += betrag
                except Exception as ex:
                    # logger.warning(f"Parse Error row: {ex}")
                    pass
    except Exception as e:
        logger.error(f"Error reading stats: {e}")
        pass
    
    return {
        'total': round(total, 2),
        'offen': round(offen, 2),
        'bezahlt': round(bezahlt, 2),
        'anzahl': count
    }

def get_ausgaben_stats(mandant_dir):
    """Statistiken aus Ausgaben"""
    ausgaben_dir = mandant_dir / 'Ausgaben'
    
    if not ausgaben_dir.exists():
        return {'total': 0, 'anzahl': 0}
    
    # Zähle einfach die Anzahl der Belege
    count = sum(1 for _ in ausgaben_dir.rglob('*.*') if _.is_file())
    
    return {
        'anzahl': count,
        'total': 0  # Könnte später aus CSV gelesen werden
    }

def get_rechnungen_stats(mandant_dir):
    """Statistiken aus Rechnungen-Ordner"""
    rechnungen_dir = mandant_dir / 'Rechnungen'
    
    if not rechnungen_dir.exists():
        return {'anzahl': 0}
    
    count = sum(1 for _ in rechnungen_dir.rglob('*.pdf') if _.is_file())
    
    return {'anzahl': count}

def get_kunden_count(mandant_dir):
    """Anzahl Kunden"""
    kunden_dir = mandant_dir / 'Kunden'
    xlsx_file = kunden_dir / 'kunden.xlsx'
    
    if xlsx_file.exists():
        import excel_utils
        try:
            data = excel_utils.read_data(str(xlsx_file), "Kunden")
            return len(data)
        except: return 0
        
    kunden_file = mandant_dir / 'kunden.csv'
    
    if not kunden_file.exists():
        return 0
    
    try:
        with open(kunden_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return max(0, len(lines) - 1)
    except:
        return 0

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """Dashboard-Übersicht über alle Mandanten"""
    try:
        mandanten_response = get_mandanten()
        mandanten_data = mandanten_response.get_json()
        
        dashboard = {
            'total_mandanten': len(mandanten_data.get('mandanten', [])),
            'total_einnahmen': 0,
            'total_ausgaben': 0,
            'total_offen': 0,
            'mandanten_details': []
        }
        
        for mandant in mandanten_data.get('mandanten', []):
            stats_response = get_mandant_stats(mandant['id'])
            stats = stats_response.get_json()
            
            dashboard['total_einnahmen'] += stats['einnahmen']['total']
            dashboard['total_offen'] += stats['einnahmen']['offen']
            
            dashboard['mandanten_details'].append({
                'id': mandant['id'],
                'name': mandant['name'],
                'stats': stats
            })
        
        return jsonify(dashboard)
    
    except Exception as e:
        logger.error(f"Fehler beim Laden des Dashboards: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/backup', methods=['POST'])
def trigger_backup():
    """Backup manuell auslösen"""
    try:
        import backup
        backup_file = backup.create_backup()
        
        return jsonify({
            'success': True,
            'backup_file': str(backup_file),
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Fehler beim Backup: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/rechnungen', methods=['GET'])
def get_mandant_rechnungen(mandant_id):
    """Liste aller Rechnungen für einen Mandanten"""
    try:
        mandant_dir = MANDANTEN_DIR / mandant_id
        rechnungen_dir = mandant_dir / 'Rechnungen'
        
        if not rechnungen_dir.exists():
            return jsonify({'rechnungen': []})
        
        rechnungen = []
        for pdf_file in rechnungen_dir.rglob('*.pdf'):
            if 'Gesendet' not in str(pdf_file):
                # Use forward slashes for URL
                rel_path = str(pdf_file.relative_to(BACKEND_DIR)).replace('\\', '/')
                rechnungen.append({
                    'name': pdf_file.name,
                    'path': rel_path,
                    'size': pdf_file.stat().st_size,
                    'modified': pdf_file.stat().st_mtime
                })
        
        return jsonify({'rechnungen': rechnungen})
    
    except Exception as e:
        logger.error(f"Fehler beim Laden der Rechnungen: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/pdf/<path:filepath>', methods=['GET'])
def serve_pdf(filepath):
    """Liefert PDF-Dateien aus"""
    try:
        # Normalize path for Windows
        filepath_clean = filepath.replace('/', os.sep)
        full_path = BACKEND_DIR / filepath_clean
        
        logger.info(f"PDF Request: {filepath} -> {full_path}")
        
        if not full_path.exists():
            logger.error(f"PDF nicht gefunden: {full_path}")
            return jsonify({'error': 'Datei nicht gefunden'}), 404
        
        from flask import send_file
        return send_file(full_path, mimetype='application/pdf')
    
    except Exception as e:
        logger.error(f"Fehler beim PDF-Abruf: {str(e)}")
        return jsonify({'error': str(e)}), 500



@app.route('/api/mandanten/<mandant_id>/einnahmen', methods=['GET'])
def get_mandant_einnahmen(mandant_id):
    """Liste aller Rechnungen mit Status"""
    try:
        mandant_dir = MANDANTEN_DIR / mandant_id
        xlsx_file = mandant_dir / 'Einnahmen' / 'einnahmen.xlsx'
        csv_file = mandant_dir / 'Einnahmen' / 'einnahmen.csv'
        
        invoices = []
        
        if xlsx_file.exists():
            import excel_utils
            data = excel_utils.read_data(str(xlsx_file), 'Einnahmen')
            invoices = data
        elif csv_file.exists():
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                invoices = list(reader)
        
        logger.info(f"Einnahmen geladen: {len(invoices)} Rechnungen")
        return jsonify({'invoices': invoices})
    
    except Exception as e:
        logger.error(f"Fehler beim Laden der Einnahmen: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/einnahmen/<rechnung_nr>/status', methods=['PUT'])
def update_invoice_status(mandant_id, rechnung_nr):
    """Aktualisiert den Status einer Rechnung"""
    try:
        data = request.get_json()
        new_status = data.get('status', 'Offen')
        
        mandant_dir = MANDANTEN_DIR / mandant_id
        xlsx_file = mandant_dir / 'Einnahmen' / 'einnahmen.xlsx'
        csv_file = mandant_dir / 'Einnahmen' / 'einnahmen.csv'
        
        if xlsx_file.exists():
            import excel_utils
            excel_utils.update_status(
                str(xlsx_file),
                'Rechnungsnummer',
                rechnung_nr,
                'Status',
                new_status
            )
        elif csv_file.exists():
            # CSV Update
            rows = []
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for row in reader:
                    if row.get('Rechnungsnummer') == rechnung_nr:
                        row['Status'] = new_status
                    rows.append(row)
            
            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        
        logger.info(f"Status aktualisiert: {mandant_id}/{rechnung_nr} → {new_status}")
        return jsonify({'success': True, 'status': new_status})
    
    except Exception as e:
        logger.error(f"Fehler beim Status-Update: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten', methods=['POST'])
def create_mandant():
    """Erstellt einen neuen Mandanten"""
    try:
        data = request.get_json()
        
        # Required fields
        firma = data.get('firma', '').strip()
        if not firma:
            return jsonify({'error': 'Firmenname ist erforderlich'}), 400
        
        # Optional fields
        strasse = data.get('strasse', '').strip()
        ort = data.get('ort', '').strip()
        geschaeftsfuehrer = data.get('geschaeftsfuehrer', '').strip()
        iban = data.get('iban', '').strip()
        bic = data.get('bic', '').strip()
        bank = data.get('bank', '').strip()
        
        # Clean name for folder
        import re
        safe_name = firma.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
        safe_name = safe_name.replace('Ä', 'Ae').replace('Ö', 'Oe').replace('Ü', 'Ue')
        safe_name = safe_name.strip().replace(' ', '_')
        safe_name = re.sub(r'[^\w\-_]', '', safe_name)
        
        mandant_path = MANDANTEN_DIR / safe_name
        
        if mandant_path.exists():
            return jsonify({'error': f'Mandant "{safe_name}" existiert bereits'}), 400
        
        # Create directory structure
        mandant_path.mkdir(parents=True)
        (mandant_path / 'Rechnungen').mkdir()
        (mandant_path / 'Angebote').mkdir()
        (mandant_path / 'Lieferscheine').mkdir()
        (mandant_path / 'Kunden').mkdir()
        (mandant_path / 'Einnahmen').mkdir()
        (mandant_path / 'Ausgaben').mkdir()
        (mandant_path / 'Reports').mkdir()
        
        # Create config
        config = {
            'firma': firma,
            'adresse': {'strasse': strasse, 'ort': ort},
            'geschaeftsfuehrer': geschaeftsfuehrer,
            'bank': {'iban': iban, 'bic': bic, 'name': bank},
            'logo': None
        }
        
        with open(mandant_path / 'mandant_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        # Initialize Excel files
        import excel_utils
        excel_utils.init_file(
            str(mandant_path / 'Kunden' / 'kunden.xlsx'),
            ['Firma', 'Email', 'Anrede'],
            'Kunden'
        )
        excel_utils.init_file(
            str(mandant_path / 'Einnahmen' / 'einnahmen.xlsx'),
            ['Rechnungsnummer', 'Datum', 'Kunde', 'Beschreibung', 'Betrag_Netto', 'Betrag_Brutto', 'Status'],
            'Einnahmen'
        )
        excel_utils.init_file(
            str(mandant_path / 'Ausgaben' / 'ausgaben.xlsx'),
            ['Datum', 'Beleg-Nr.', 'Firma', 'Beschreibung', 'Kategorie', 'Netto', 'MwSt', 'Brutto'],
            'Ausgaben'
        )
        excel_utils.init_file(
            str(mandant_path / 'preisliste.xlsx'),
            ['Pos', 'Bezeichnung', 'Einheit', 'Einzelpreis', 'Kategorie'],
            'Preisliste'
        )
        
        logger.info(f"Mandant erstellt: {safe_name}")
        return jsonify({'success': True, 'mandant_id': safe_name, 'config': config})
    
    except Exception as e:
        logger.error(f"Fehler beim Anlegen des Mandanten: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/kunden', methods=['GET'])
def get_mandant_kunden(mandant_id):
    """Liste aller Kunden eines Mandanten"""
    try:
        mandant_dir = MANDANTEN_DIR / mandant_id
        kunden_xlsx = mandant_dir / 'Kunden' / 'kunden.xlsx'
        kunden_csv = mandant_dir / 'Kunden' / 'kunden.csv'
        
        kunden = []
        
        if kunden_xlsx.exists():
            import excel_utils
            data = excel_utils.read_data(str(kunden_xlsx), 'Kunden')
            kunden = data
        elif kunden_csv.exists():
            with open(kunden_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                kunden = list(reader)
        
        return jsonify({'kunden': kunden})
    
    except Exception as e:
        logger.error(f"Fehler beim Laden der Kunden: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/kunden', methods=['POST'])
def create_kunde(mandant_id):
    """Erstellt einen neuen Kunden"""
    try:
        data = request.get_json()
        firma = data.get('firma', '').strip()
        email = data.get('email', '').strip()
        anrede = data.get('anrede', 'Sehr geehrte Damen und Herren')
        
        if not firma:
            return jsonify({'error': 'Firma ist erforderlich'}), 400
        
        mandant_dir = MANDANTEN_DIR / mandant_id
        kunden_xlsx = mandant_dir / 'Kunden' / 'kunden.xlsx'
        
        # Prepare data
        kunde_data = {
            'Firma': firma,
            'Email': email,
            'Anrede': anrede
        }
        
        # Save to Excel
        import excel_utils
        excel_utils.append_data(
            str(kunden_xlsx),
            kunde_data,
            'Kunden',
            ['Firma', 'Email', 'Anrede']
        )
        
        logger.info(f"Kunde erstellt: {mandant_id}/{firma}")
        return jsonify({'success': True, 'kunde': kunde_data})
    
    except Exception as e:
        logger.error(f"Fehler beim Anlegen des Kunden: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ===== PREISLISTE ENDPOINTS =====

@app.route('/api/mandanten/<mandant_id>/preisliste', methods=['GET'])
def get_preisliste(mandant_id):
    """Liste aller Preislisten-Positionen"""
    try:
        mandant_dir = MANDANTEN_DIR / mandant_id
        preisliste_file = mandant_dir / 'preisliste.xlsx'
        
        if not preisliste_file.exists():
            return jsonify({'positionen': []})
        
        import excel_utils
        data = excel_utils.read_data(str(preisliste_file), 'Preisliste')
        
        return jsonify({'positionen': data})
    
    except Exception as e:
        logger.error(f"Fehler beim Laden der Preisliste: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/preisliste/position', methods=['POST'])
def add_preisliste_position(mandant_id):
    """Fügt eine Position zur Preisliste hinzu"""
    try:
        data = request.get_json()
        
        bezeichnung = data.get('bezeichnung', '').strip()
        einheit = data.get('einheit', 'Stk').strip()
        einzelpreis = float(data.get('einzelpreis', 0))
        kategorie = data.get('kategorie', 'Sonstiges').strip()
        
        if not bezeichnung:
            return jsonify({'error': 'Bezeichnung ist erforderlich'}), 400
        
        mandant_dir = MANDANTEN_DIR / mandant_id
        preisliste_file = mandant_dir / 'preisliste.xlsx'
        
        # Get next position number
        import excel_utils
        existing = excel_utils.read_data(str(preisliste_file), 'Preisliste')
        next_pos = len(existing) + 1
        
        position_data = {
            'Pos': next_pos,
            'Bezeichnung': bezeichnung,
            'Einheit': einheit,
            'Einzelpreis': einzelpreis,
            'Kategorie': kategorie
        }
        
        excel_utils.append_data(
            str(preisliste_file),
            position_data,
            'Preisliste',
            ['Pos', 'Bezeichnung', 'Einheit', 'Einzelpreis', 'Kategorie']
        )
        
        logger.info(f"Preislisten-Position hinzugefügt: {mandant_id}/{bezeichnung}")
        return jsonify({'success': True, 'position': position_data})
    
    except Exception as e:
        logger.error(f"Fehler beim Hinzufügen der Position: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/preisliste/position/<int:pos>', methods=['PUT'])
def update_preisliste_position(mandant_id, pos):
    """Aktualisiert eine Preislisten-Position"""
    try:
        data = request.get_json()
        
        mandant_dir = MANDANTEN_DIR / mandant_id
        preisliste_file = mandant_dir / 'preisliste.xlsx'
        
        import excel_utils
        positions = excel_utils.read_data(str(preisliste_file), 'Preisliste')
        
        # Find and update position
        updated = False
        for p in positions:
            if int(p.get('Pos', 0)) == pos:
                p['Bezeichnung'] = data.get('bezeichnung', p.get('Bezeichnung'))
                p['Einheit'] = data.get('einheit', p.get('Einheit'))
                p['Einzelpreis'] = float(data.get('einzelpreis', p.get('Einzelpreis', 0)))
                p['Kategorie'] = data.get('kategorie', p.get('Kategorie'))
                updated = True
                break
        
        if not updated:
            return jsonify({'error': 'Position nicht gefunden'}), 404
        
        # Write back
        excel_utils.write_data(
            str(preisliste_file),
            positions,
            'Preisliste',
            ['Pos', 'Bezeichnung', 'Einheit', 'Einzelpreis', 'Kategorie']
        )
        
        logger.info(f"Position {pos} aktualisiert: {mandant_id}")
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/preisliste/position/<int:pos>', methods=['DELETE'])
def delete_preisliste_position(mandant_id, pos):
    """Löscht eine Preislisten-Position"""
    try:
        mandant_dir = MANDANTEN_DIR / mandant_id
        preisliste_file = mandant_dir / 'preisliste.xlsx'
        
        import excel_utils
        positions = excel_utils.read_data(str(preisliste_file), 'Preisliste')
        
        # Filter out the position
        positions = [p for p in positions if int(p.get('Pos', 0)) != pos]
        
        # Renumber positions
        for idx, p in enumerate(positions, 1):
            p['Pos'] = idx
        
        # Write back
        excel_utils.write_data(
            str(preisliste_file),
            positions,
            'Preisliste',
            ['Pos', 'Bezeichnung', 'Einheit', 'Einzelpreis', 'Kategorie']
        )
        
        logger.info(f"Position {pos} gelöscht: {mandant_id}")
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f"Fehler beim Löschen: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/preisliste/import', methods=['POST'])
def import_preisliste(mandant_id):
    """Importiert Preisliste aus verschiedenen Formaten"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Keine Datei'}), 400
        
        file = request.files['file']
        if not file.filename:
            return jsonify({'error': 'Kein Dateiname'}), 400
        
        # Save temporarily
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        temp_file = temp_dir / file.filename
        file.save(temp_file)
        
        # Import using parser
        import preisliste_import
        positionen = preisliste_import.import_preisliste(str(temp_file))
        
        # Clean up
        temp_file.unlink()
        
        logger.info(f"Preisliste importiert: {len(positionen)} Positionen")
        return jsonify({
            'success': True,
            'positionen': positionen,
            'count': len(positionen)
        })
    
    except Exception as e:
        logger.error(f"Fehler beim Import: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/preisliste/import/confirm', methods=['POST'])
def confirm_import_preisliste(mandant_id):
    """Bestätigt und speichert importierte Positionen"""
    try:
        data = request.get_json()
        positionen = data.get('positionen', [])
        
        if not positionen:
            return jsonify({'error': 'Keine Positionen'}), 400
        
        mandant_dir = MANDANTEN_DIR / mandant_id
        preisliste_file = mandant_dir / 'preisliste.xlsx'
        
        import excel_utils
        
        # Get current max position
        existing = excel_utils.read_data(str(preisliste_file), 'Preisliste')
        next_pos = len(existing) + 1
        
        # Add all positions
        for pos_data in positionen:
            position = {
                'Pos': next_pos,
                'Bezeichnung': pos_data.get('bezeichnung', ''),
                'Einheit': pos_data.get('einheit', 'Stk'),
                'Einzelpreis': float(pos_data.get('einzelpreis', 0)),
                'Kategorie': pos_data.get('kategorie', 'Sonstiges')
            }
            
            excel_utils.append_data(
                str(preisliste_file),
                position,
                'Preisliste',
                ['Pos', 'Bezeichnung', 'Einheit', 'Einzelpreis', 'Kategorie']
            )
            next_pos += 1
        
        logger.info(f"{len(positionen)} Positionen importiert: {mandant_id}")
        return jsonify({'success': True, 'count': len(positionen)})
    
    except Exception as e:
        logger.error(f"Fehler beim Speichern: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ===== ANGEBOT ENDPOINTS =====

@app.route('/api/mandanten/<mandant_id>/angebote', methods=['GET'])
def get_angebote(mandant_id):
    """Liste aller Angebote"""
    try:
        mandant_dir = MANDANTEN_DIR / mandant_id
        angebote_file = mandant_dir / 'Angebote' / 'angebote.xlsx'
        
        if not angebote_file.exists():
            return jsonify({'angebote': []})
        
        import excel_utils
        data = excel_utils.read_data(str(angebote_file), 'Angebote')
        
        # Normalize keys (Nummer -> nummer, PDF_Path -> pdf_path)
        normalized = []
        for row in data:
            item = {}
            for k, v in row.items():
                key = k.lower()
                if key == 'pdf_path': key = 'pdf_path' # Ensure specific underscore style if needed
                item[key] = v
                
            # Add path prefix if missing
            if 'pdf_path' in item:
                 # It's usually just filename in Excel based on current save logic
                 # Frontend needs /api/pdf/Mandanten/<id>/Angebote/<filename>
                 fname = item['pdf_path']
                 if not fname.startswith('/api'):
                     item['pdf_path'] = f"/api/pdf/Mandanten/{mandant_id}/Angebote/{fname}"
            
            normalized.append(item)
        
        return jsonify({'angebote': normalized})
    
    except Exception as e:
        logger.error(f"Fehler beim Laden der Angebote: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/angebot/<nummer>', methods=['GET'])
def get_angebot_details(mandant_id, nummer):
    """Details eines Angebots (inkl. Positionen)"""
    try:
        mandant_dir = MANDANTEN_DIR / mandant_id
        json_file = mandant_dir / 'Angebote' / f"Angebot_{nummer}.json"
        
        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        
        return jsonify({'error': 'Angebot-Details nicht gefunden'}), 404
    
    except Exception as e:
        logger.error(f"Fehler: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/angebot', methods=['POST'])
def create_angebot(mandant_id):
    """Erstellt ein neues Angebot"""
    try:
        data = request.get_json()
        
        kunde_name = data.get('kunde', '')
        positionen = data.get('positionen', [])
        
        if not kunde_name or not positionen:
            return jsonify({'error': 'Kunde und Positionen sind erforderlich'}), 400
        
        mandant_dir = MANDANTEN_DIR / mandant_id
        angebote_dir = mandant_dir / 'Angebote'
        
        # Ensure directory exists (fixes Errno 2)
        angebote_dir.mkdir(parents=True, exist_ok=True)
        
        # Load config
        config_file = mandant_dir / 'mandant_config.json'
        mandant_config = {}
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                mandant_config = json.load(f)
        
        # Generate number
        import offer_generator
        nummer = offer_generator.get_and_increment_offer_counter(str(mandant_dir))
        
        # Create PDF with timestamp
        timestamp = int(datetime.now().timestamp())
        pdf_filename = f"Angebot_{nummer}_{timestamp}.pdf"
        pdf_path = angebote_dir / pdf_filename
        
        brutto, netto = offer_generator.create_offer_pdf(
            str(mandant_dir),
            mandant_config,
            kunde_name,
            positionen,
            str(pdf_path),
            nummer
        )
        
        # Save to Excel
        import excel_utils
        angebot_data = {
            'Nummer': nummer,
            'Datum': datetime.now().strftime('%Y-%m-%d'),
            'Kunde': kunde_name,
            'Netto': f"{netto:.2f}",
            'Brutto': f"{brutto:.2f}",
            'Status': 'Offen',
            'PDF_Path': str(pdf_filename)
        }
        
        angebote_file = angebote_dir / 'angebote.xlsx'
        excel_utils.append_data(
            str(angebote_file),
            angebot_data,
            'Angebote',
            ['Nummer', 'Datum', 'Kunde', 'Netto', 'Brutto', 'Status', 'PDF_Path']
        )
        
        # Save Details as JSON for Lieferschein (NEW)
        json_path = angebote_dir / f"Angebot_{nummer}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'nummer': nummer,
                'kunde': kunde_name,
                'positionen': positionen,
                'datum': datetime.now().isoformat()
            }, f, indent=4)
        
        logger.info(f"Angebot erstellt: {mandant_id}/{nummer}")
        return jsonify({
            'success': True,
            'nummer': nummer,
            'pdf_path': f"/api/pdf/Mandanten/{mandant_id}/Angebote/{pdf_filename}",
            'brutto': brutto
        })
    
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Angebots: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/lieferscheine', methods=['GET'])
def get_lieferscheine(mandant_id):
    try:
        mandant_path = MANDANTEN_DIR / mandant_id
        if not mandant_path.exists():
            return jsonify({'error': 'Mandant nicht gefunden'}), 404
            
        file_path = mandant_path / 'Lieferscheine' / 'lieferscheine.xlsx'
        if not file_path.exists():
             return jsonify({'lieferscheine': []})
             
        import excel_utils
        data = excel_utils.read_data(str(file_path), 'Lieferscheine')
        
        # Normalize
        normalized = []
        for row in data:
            item = {}
            for k, v in row.items():
                item[k.lower()] = v
                
            # Fix path
            if 'pdf_path' in item:
                 fname = item['pdf_path']
                 if not fname.startswith('/api'):
                     item['pdf_path'] = f"/api/pdf/Mandanten/{mandant_id}/Lieferscheine/{fname}"
            normalized.append(item)
            
        return jsonify({'lieferscheine': normalized})
        
    except Exception as e:
        logger.error(f"LS Fehler: {e}")
        return jsonify({'error': str(e)}), 500

        # Read specific excel/json for deliveries if exists, or scan directory
        # For simplicity, returning empty list or scanning PDFs if excel not handy
        # But we initialized 'lieferscheine.xlsx' in add_client?
        # Let's check if we did. usage says YES.
        
        file_path = mandant_path / 'Lieferscheine' / 'lieferscheine.xlsx'
        lieferscheine = []
        if file_path.exists():
            lieferscheine = excel_utils.read_data(file_path)
            
        return jsonify({'lieferscheine': lieferscheine})
    except Exception as e:
        logger.error(f"Fehler beim Laden der Lieferscheine: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/lieferschein', methods=['POST'])
def create_lieferschein(mandant_id):
    try:
        data = request.get_json()
        mandant_path = MANDANTEN_DIR / mandant_id
        if not mandant_path.exists():
            return jsonify({'error': 'Mandant nicht gefunden'}), 404

        kunde_name = data.get('kunde')
        angebot_nr = data.get('angebot') # optional
        positionen = data.get('positionen', [])

        if not kunde_name or not positionen:
            return jsonify({'error': 'Kunde und Positionen erforderlich'}), 400

        # Load Mandant Config
        config_path = mandant_path / 'mandant_config.json'
        mandant_config = {}
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                mandant_config = json.load(f)

        # Generate Number
        import delivery_generator
        nummer = delivery_generator.get_and_increment_delivery_counter(str(mandant_path))
        
        # Create PDF
        lieferscheine_dir = mandant_path / 'Lieferscheine'
        lieferscheine_dir.mkdir(exist_ok=True)
        
        # Create PDF with timestamp to avoid locking
        timestamp = int(datetime.now().timestamp())
        pdf_filename = f"Lieferschein_{nummer}_{timestamp}.pdf"
        output_path = lieferscheine_dir / pdf_filename
        
        delivery_generator.create_delivery_pdf(
            mandant_path=str(mandant_path),
            mandant_config=mandant_config,
            kunde_name=kunde_name,
            positionen=positionen,
            output_path=str(output_path),
            nummer=nummer,
            angebot_nr=angebot_nr
        )

        # Save to Excel
        file_path = mandant_path / 'Lieferscheine' / 'lieferscheine.xlsx'
        
        # Check explicit columns of lieferscheine.xlsx to match appends
        # Default Init was: ['Nummer', 'Datum', 'Kunde', 'Angebot', 'PDF_Path'] (Hypothetical - assuming standard)
        # Verify columns in add_client or just write blindly? 
        # Safer: use excel_utils.append_row
        
        new_row = {
            'Nummer': nummer,
            'Datum': datetime.now().strftime('%Y-%m-%d'),
            'Kunde': kunde_name,
            'Angebot': angebot_nr if angebot_nr else '',
            'PDF_Path': pdf_filename
        }
        
        # Note: excel_utils might require matching columns.
        # If headers match keys, we are good.
        excel_utils.append_data(file_path, new_row, sheet_name="Lieferscheine")

        return jsonify({
            'success': True,
            'nummer': nummer,
            'pdf_path': f"/api/pdf/Mandanten/{mandant_id}/Lieferscheine/{pdf_filename}"
        })

    except Exception as e:
        logger.error(f"Fehler Lieferschein: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/mandanten/<mandant_id>/protocol/scan', methods=['POST'])
def scan_protocol(mandant_id):
    """Scans uploaded protocol and returns invoice items"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Keine Datei'}), 400
            
        file = request.files['file']
        if not file.filename:
            return jsonify({'error': 'Kein Dateiname'}), 400

        # Save temporarily
        import tempfile
        temp_dir = Path(tempfile.gettempdir())
        temp_path = temp_dir / file.filename
        file.save(temp_path)
        
        # Analyze
        import protocol_utils
        mandant_path = MANDANTEN_DIR / mandant_id
        items = protocol_utils.analyze_protocol(str(temp_path), str(mandant_path))
        
        # Cleanup
        try:
            temp_path.unlink()
        except: pass
        
        return jsonify({
            'success': True,
            'items': items
        })
        
    except Exception as e:
        logger.error(f"Scan Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/mandanten/<mandant_id>/rechnung', methods=['POST'])
def create_invoice(mandant_id):
    """Generates Invoice PDF using invoice_generator.py logic"""
    try:
        data = request.get_json()
        kunde_name = data.get('kunde', '')
        # items [{'bezeichnung': '...', 'menge': 1, 'einzelpreis': 10, 'gesamt': 10}]
        raw_items = data.get('items', [])
        
        if not kunde_name or not raw_items:
            return jsonify({'error': 'Kunde und Positionen erforderlich'}), 400
            
        mandant_dir = MANDANTEN_DIR / mandant_id
        
        # Load Config
        import invoice_generator
        config = invoice_generator.load_mandant_config(str(mandant_dir), mandant_id)
        
        # Prepare Client Data
        # We need client address details. Try to load from kunden.xlsx or just use name?
        # invoice_generator expects {'firma': '...', 'anrede': '...'}
        # Let's try to find the client in the DB to get full details
        kunden = invoice_generator.load_kunden(str(mandant_dir))
        kunde_data = next((k for k in kunden if k['firma'] == kunde_name), None)
        
        if not kunde_data:
            # Fallback if not found
            kunde_data = {'firma': kunde_name, 'anrede': ''}
            
        # Generate Number
        inv_nr = invoice_generator.get_and_increment_counter(str(mandant_dir))
        
        # Format Items for Generator
        # Generator expects: [{'beschreibung': '...', 'betrag': float}]
        # We transform our detailed items into this format
        formatted_items = []
        for item in raw_items:
            menge = float(item.get('menge', 0))
            preis = float(item.get('einzelpreis', 0))
            gesamt = menge * preis
            
            # Formatting style: "2.0x Beratung (@ 50.00 €)"
            # Check unit
            einheit = item.get('einheit', 'Stk')
            bezeichnung = item.get('bezeichnung', '')
            
            desc = f"{menge} {einheit} {bezeichnung} (Einzel: {preis:.2f}€)"
            formatted_items.append({
                'beschreibung': desc,
                'betrag': gesamt
            })
            
        invoice_data = {
            'nummer': inv_nr,
            'datum': datetime.now().strftime("%d.%m.%Y"),
            'items': formatted_items
        }
        
        # Generate PDF
        pdf_path = invoice_generator.create_pdf(invoice_data, str(mandant_dir), config, kunde_data)
        
        if pdf_path:
            # Explicitly save to Einnahmen (Fixing silent failure in generator)
            try:
                import excel_utils
                einnahmen_dir = mandant_dir / 'Einnahmen'
                einnahmen_dir.mkdir(parents=True, exist_ok=True)
                xlsx_path = einnahmen_dir / 'einnahmen.xlsx'
                
                # Format for Excel
                # Items description as comma list
                desc_text = ", ".join([i['beschreibung'] for i in formatted_items])
                
                excel_row = {
                    "Rechnungsnummer": inv_nr,
                    "Datum": datetime.now().strftime("%d.%m.%Y"),
                    "Kunde": kunde_data.get('firma', kunde_name),
                    "Beschreibung": desc_text,
                    "Betrag_Netto": f"{sum(x['betrag'] for x in formatted_items):.2f}",
                    "Betrag_Brutto": f"{sum(x['betrag'] for x in formatted_items) * 1.19:.2f}",
                    "Status": "Offen"
                }
                
                headers = ["Rechnungsnummer", "Datum", "Kunde", "Beschreibung", "Betrag_Netto", "Betrag_Brutto", "Status"]
                excel_utils.append_data(str(xlsx_path), excel_row, "Einnahmen", headers)
                
            except Exception as e:
                logger.error(f"Excel Write Error: {e}")
            
            # Prepare relative path for frontend
            rel_path = Path(pdf_path).relative_to(MANDANTEN_DIR) 
            web_path = f"/api/pdf/Mandanten/{str(rel_path).replace(os.sep, '/')}"
            
            return jsonify({
                'success': True,
                'nummer': inv_nr,
                'pdf_path': web_path,
                'brutto': sum(x['betrag'] for x in formatted_items) * 1.19
            })
        else:
            return jsonify({'error': 'PDF Generierung fehlgeschlagen'}), 500
            
    except Exception as e:
        logger.error(f"Invoice Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# --- EXPENSES (AUSGABEN) ---

@app.route('/api/mandanten/<mandant_id>/ausgaben', methods=['GET'])
def get_ausgaben(mandant_id):
    try:
        mandant_dir = MANDANTEN_DIR / mandant_id
        if not mandant_dir.exists():
            return jsonify({'error': 'Mandant nicht gefunden'}), 404
            
        xlsx_file = mandant_dir / 'Ausgaben' / 'ausgaben.xlsx'
        import excel_utils
        
        # Read Data
        # Ensure we have a file
        if not xlsx_file.exists():
             return jsonify({'ausgaben': []})
             
        data = excel_utils.read_data(str(xlsx_file), 'Ausgaben')
        
        # Add Clean Data
        cleaned = []
        for row in data:
            # Fix potential None values for JSON
            item = {}
            for k, v in row.items():
                if pd.isna(v): v = None
                item[k] = v
            cleaned.append(item)
            
        return jsonify({'ausgaben': cleaned})
        
    except Exception as e:
        logger.error(f"Ausgaben Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload/beleg', methods=['POST'])
def upload_beleg():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Keine Datei'}), 400
            
        file = request.files['file']
        mandant_id = request.form.get('mandant_id')
        category = request.form.get('category', 'Sonstiges')
        
        if not mandant_id or not file.filename:
            return jsonify({'error': 'Fehlende Daten'}), 400

        mandant_dir = MANDANTEN_DIR / mandant_id
        if not mandant_dir.exists():
            return jsonify({'error': 'Mandant nicht gefunden'}), 404
            
        # 1. Save File
        belege_dir = mandant_dir / 'Ausgaben' / 'Belege'
        belege_dir.mkdir(parents=True, exist_ok=True)
        
        # Timestamp to avoid overwrites
        timestamp = int(datetime.now().timestamp())
        safe_name = f"{timestamp}_{file.filename}"
        file_path = belege_dir / safe_name
        file.save(file_path)
        
        # 2. Analyze with AI
        import receipt_utils
        data = receipt_utils.analyze_receipt(str(file_path))
        
        if not data:
            data = {
                'datum': datetime.now().strftime('%d.%m.%Y'),
                'betrag': 0.0,
                'firma': 'Unbekannt',
                'kategorie': category,
                'beschreibung': 'Manueller Check nötig'
            }
            
        # 3. Save to Excel
        xlsx_path = mandant_dir / 'Ausgaben' / 'ausgaben.xlsx'
        import excel_utils
        
        # Calc taxes (approx)
        betrag = float(data.get('betrag', 0)) if data.get('betrag') else 0.0
        netto = betrag / 1.19
        
        row = {
            'Datum': data.get('datum'),
            'Firma': data.get('firma'),
            'Kategorie': data.get('kategorie', category),
            'Beschreibung': data.get('beschreibung'),
            'Betrag_Netto': f"{netto:.2f}",
            'Betrag_Brutto': f"{betrag:.2f}",
            'Beleg_Pfad': str(safe_name),
            'Status': 'Bezahlt'
        }
        
        excel_utils.append_data(
            str(xlsx_path),
            row,
            'Ausgaben',
            ['Datum', 'Firma', 'Kategorie', 'Beschreibung', 'Betrag_Netto', 'Betrag_Brutto', 'Status', 'Beleg_Pfad']
        )
        
        return jsonify({
            'success': True,
            'message': f"Beleg erfasst: {data.get('betrag')}€ ({data.get('firma')})",
            'data': data
        })

    except Exception as e:
        logger.error(f"Beleg Upload Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Restart Trigger
    logger.info("🚀 Starting API Server...")
    print("\n" + "="*50)
    print("🚀 Mein Business API Server")
    print("="*50)
    print("📡 API läuft auf: http://localhost:5000")
    print("📊 Dashboard: http://localhost:5000/api/dashboard")
    print("🏢 Mandanten: http://localhost:5000/api/mandanten")
    print("\n💡 Öffne das Frontend in deinem Browser")
    print("="*50 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
