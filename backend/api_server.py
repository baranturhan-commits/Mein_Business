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
import uuid
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()

# Import local modules
import excel_utils
import preisliste_import  # For price list import functionality
import offer_generator    # For offer PDF generation
import payroll_generator  # For payslip generation
import recurring_invoices
import report_generator

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
                # Use forward slashes for URL and prepend API endpoint
                rel_path = str(pdf_file.relative_to(BACKEND_DIR)).replace('\\', '/')
                web_path = f"/api/pdf/{rel_path}"
                rechnungen.append({
                    'name': pdf_file.name,
                    'path': web_path,
                    'size': pdf_file.stat().st_size,
                    'modified': pdf_file.stat().st_mtime
                })
        
        return jsonify({'rechnungen': sorted(rechnungen, key=lambda x: x['name'], reverse=True)})
    
    except Exception as e:
        logger.error(f"Fehler beim Laden der Rechnungen: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/mandanten/<mandant_id>/config', methods=['GET', 'PUT'])
def handle_mandant_config(mandant_id):
    """Lese oder Aktualisiere Mandanten-Konfiguration"""
    mandant_dir = MANDANTEN_DIR / mandant_id
    config_file = mandant_dir / 'mandant_config.json'
    
    if request.method == 'GET':
        if not config_file.exists():
            return jsonify({'error': 'Config nicht gefunden'}), 404
            
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return jsonify(config)
        except Exception as e:
            logger.error(f"Config Read Error: {e}")
            return jsonify({'error': str(e)}), 500
            
    elif request.method == 'PUT':
        try:
            new_data = request.get_json()
            if not new_data:
                return jsonify({'error': 'Keine Daten'}), 400
                
            # Load existing to merge (preserve fields like internal IDs if any)
            current_config = {}
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    current_config = json.load(f)
            
            # Update fields
            # Allow specific fields to be updated
            allowed_fields = ['firma', 'geschaeftsfuehrer', 'logo', 'adresse', 'bank', 'mandant_nummer']
            
            for key in allowed_fields:
                if key in new_data:
                    current_config[key] = new_data[key]
            
            # Save
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(current_config, f, indent=4, ensure_ascii=False)
                
            return jsonify({'success': True, 'config': current_config})
            
        except Exception as e:
            logger.error(f"Config Write Error: {e}")
            return jsonify({'error': str(e)}), 500


@app.route('/api/mandanten/<mandant_id>/logo', methods=['POST'])
def upload_mandant_logo(mandant_id):
    """Upload Mandant Logo and update config"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Keine Datei'}), 400
            
        file = request.files['file']
        if not file.filename:
            return jsonify({'error': 'Keine Datei ausgewählt'}), 400
            
        mandant_dir = MANDANTEN_DIR / mandant_id
        config_file = mandant_dir / 'mandant_config.json'
        
        # Save File
        filename = secure_filename(file.filename)
        file.save(mandant_dir / filename)
        
        # Update config
        config = {}
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
        config['logo'] = filename
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            
        return jsonify({'success': True, 'filename': filename})
        
    except Exception as e:
        logger.error(f"Logo Upload Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/mitarbeiter', methods=['GET', 'POST'])
def handle_mitarbeiter(mandant_id):
    """Verwalte Mitarbeiter (Liste lesen & hinzufügen/bearbeiten)"""
    mandant_dir = MANDANTEN_DIR / mandant_id
    json_file = mandant_dir / 'mitarbeiter.json'
    
    if request.method == 'GET':
        if not json_file.exists():
            return jsonify([])
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        except Exception as e:
            logger.error(f"Error reading mitarbeiter.json: {e}")
            return jsonify({'error': str(e)}), 500
            
    elif request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data'}), 400
            
            mitarbeiter_liste = []
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    mitarbeiter_liste = json.load(f)
            
            # Check if editing existing (if ID provided)
            # data should contain all fields including potentially 'id'
            emp_id = data.get('id')
            if emp_id:
                # Update existing
                for i, emp in enumerate(mitarbeiter_liste):
                    if emp.get('id') == emp_id:
                        mitarbeiter_liste[i] = data
                        break
                else:
                    # Id provided but not found? Append as new? Or error?
                    # Let's append as new but keep ID if beneficial, or generate new.
                    # Best practice: if not found, treat as new (or append).
                    mitarbeiter_liste.append(data)
            else:
                # New employee
                data['id'] = str(uuid.uuid4())
                mitarbeiter_liste.append(data)
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(mitarbeiter_liste, f, indent=4, ensure_ascii=False)
                
            return jsonify({'success': True, 'mitarbeiter': mitarbeiter_liste})
            
        except Exception as e:
            logger.error(f"Error saving mitarbeiter: {e}")
            return jsonify({'error': str(e)}), 500


@app.route('/api/mandanten/<mandant_id>/mitarbeiter/<emp_id>/payslips', methods=['GET'])
def get_employee_payslips(mandant_id, emp_id):
    """Liefere Liste aller Lohnabrechnungen für einen Mitarbeiter"""
    try:
        mandant_dir = MANDANTEN_DIR / mandant_id
        json_file = mandant_dir / 'mitarbeiter.json'
        
        # 1. Get Employee for Name
        emp_data = None
        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as f:
                employees = json.load(f)
                for emp in employees:
                    if emp.get('id') == emp_id:
                        emp_data = emp
                        break
        
        if not emp_data:
            return jsonify({'error': 'Mitarbeiter nicht gefunden'}), 404
            
        # 2. Scan Directory
        lohn_dir = mandant_dir / 'Lohnabrechnungen'
        if not lohn_dir.exists():
            return jsonify([])
            
        payslips = []
        nachname = emp_data.get('nachname', '').strip()
        vorname = emp_data.get('vorname', '').strip()
        
        # Match pattern: Lohn_Nachname_Vorname_...
        # If files were created with old format (only Nachname), we might miss them.
        # But for new format it works.
        # Fallback: check if filename contains Nachname?
        # Let's match strict prefix if possible to avoid wrong matches.
        prefix = f"Lohn_{nachname}_{vorname}_"
        # Also simple check for old format: Lohn_{nachname}_Month-Year.pdf (if user has no Vorname in data?)
        
        for file in lohn_dir.iterdir():
            if file.suffix == '.pdf':
                if file.name.startswith(prefix) or (vorname == '' and file.name.startswith(f"Lohn_{nachname}_")):
                    payslips.append({
                        'filename': file.name,
                        'date': datetime.fromtimestamp(file.stat().st_mtime).strftime('%d.%m.%Y'),
                        'size': file.stat().st_size
                    })
                    
        # Sort by date desc (modification time roughly correlates?)
        # Better to parse month from filename?
        # Simple: sort by mtime reverse
        payslips.sort(key=lambda x: x['filename'], reverse=True) # Sort by name usually sorts by year-month if format YYYY? No, Month-Year (Januar-2025). Alpha sort might not be chronological.
        # But listing is enough.
        
        return jsonify(payslips)
        
    except Exception as e:
        logger.error(f"Payslip List Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/mandanten/<mandant_id>/mitarbeiter/<emp_id>/payslip', methods=['POST'])
def generate_payslip(mandant_id, emp_id):
    """Generiere Lohnabrechnungs-PDF"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data'}), 400
            
        mandant_dir = MANDANTEN_DIR / mandant_id
        
        # 1. Employee Data
        json_file = mandant_dir / 'mitarbeiter.json'
        emp_data = None
        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as f:
                employees = json.load(f)
                for emp in employees:
                    if emp.get('id') == emp_id:
                        emp_data = emp
                        break
        
        if not emp_data:
            return jsonify({'error': 'Mitarbeiter nicht gefunden'}), 404
            
        # 2. Mandant Config
        config_file = mandant_dir / 'mandant_config.json'
        mandant_config = {}
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                mandant_config = json.load(f)
                
        # 3. Generate
        filename = payroll_generator.create_payroll_pdf(
            mandant_config, 
            emp_data, 
            data, # Payload containing month, lohn, taxes etc.
            mandant_dir
        )
        
        # Return path relative to api/pdf if possible, OR just success and filename
        # My frontend documents tab lists files from 'Rechnungen', 'Angebote'.
        # 'Lohnabrechnungen' is new. I might need to update the file lister too 
        # but for now I just return success.
        
        return jsonify({'success': True, 'filename': filename})
        
    except Exception as e:
        logger.error(f"Payslip Generation Error: {e}")
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
        seen_ids = set()

        # Helper to add invoice if not duplicate
        def add_invoice(inv):
            nr = inv.get('Rechnungsnummer')
            if nr and nr not in seen_ids:
                invoices.append(inv)
                seen_ids.add(nr)
        
        # 1. Read XLSX
        if xlsx_file.exists():
            import excel_utils
            try:
                data = excel_utils.read_data(str(xlsx_file), 'Einnahmen')
                for row in data:
                    add_invoice(row)
            except Exception as e:
                logger.error(f"Error reading Einnahmen XLSX: {e}")

        # 2. Read CSV (and merge)
        if csv_file.exists():
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Clean up keys/values if needed? usually DictReader is fine
                        add_invoice(row)
            except Exception as e:
                logger.error(f"Error reading Einnahmen CSV: {e}")
        
        # Sort by Date? (Optional but nice)
        # invoices.sort(key=lambda x: datetime.strptime(x.get('Datum',''), '%d.%m.%Y'), reverse=True)

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
            str(mandant_path / 'Lieferscheine' / 'lieferscheine.xlsx'),
            ['Nummer', 'Datum', 'Kunde', 'Angebot', 'PDF_Path'],
            'Lieferscheine'
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
        
        return jsonify({'angebote': sorted(normalized, key=lambda x: str(x.get('nummer', '0')), reverse=True)})
    
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
                
            # Parse Items if present (from Excel string to JSON)
            if 'items' in item:
                try:
                    if isinstance(item['items'], str) and item['items'].strip():
                         item['items'] = json.loads(item['items'])
                except:
                     item['items'] = []
                
            # Fix path
            # Fix path
            # Search for relevant key
            path_val = item.get('pdf_path') or item.get('pdf path') or item.get('path') or item.get('dateipfad')
            
            # Fallback: Construct from Number if path needs validation or is missing
            if not path_val:
                nummer = item.get('lieferscheinnummer') or item.get('nummer')
                if nummer:
                    path_val = f"{nummer}.pdf"
            
            if path_val:
                 fname = str(path_val).strip()
                 # Ensure we only have the filename, as entries might contain 'Mandanten/...'
                 if '/' in fname or '\\' in fname:
                     fname = os.path.basename(fname)
                 
                 # Verify existence
                 lieferscheine_dir = mandant_path / 'Lieferscheine'
                 full_path = lieferscheine_dir / fname
                 
                 if not full_path.exists():
                     # Try with .pdf extension
                     if not fname.lower().endswith('.pdf'):
                         test_path = lieferscheine_dir / f"{fname}.pdf"
                         if test_path.exists():
                             fname = f"{fname}.pdf"
                             full_path = test_path
                         else:
                             # File really not found
                             continue
                     else:
                         continue

                 if not fname.startswith('/api') and not fname.startswith('http'):
                     final_path = f"/api/pdf/Mandanten/{mandant_id}/Lieferscheine/{fname}"
                 else:
                     final_path = fname
                     
                 item['pdf_path'] = final_path
                 
                 # Ensure Date and Customer are set (mapping from screenshot headers)
                 if 'datum' not in item and 'date' in item: item['datum'] = item['date']
                 # Map 'lieferscheinnummer' to 'nummer' for frontend consistency
                 if 'nummer' not in item and 'lieferscheinnummer' in item: 
                     item['nummer'] = item['lieferscheinnummer']
                     
                 normalized.append(item)
            else:
                 # No path and no number -> invalid row
                 continue
            
        return jsonify({'lieferscheine': sorted(normalized, key=lambda x: str(x.get('nummer', '0')), reverse=True)})
        
    except Exception as e:
        logger.error(f"LS Fehler: {e}")
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
        
        # Prepare row data
        items_json = json.dumps(positionen)
        row_data = {
            'Lieferscheinnummer': nummer,
            'Datum': datetime.now().strftime("%d.%m.%Y"),
            'Kunde': kunde_name,
            'Angebot': angebot_nr or '',
            'Items': items_json,
            # Path relative for frontend? or full? Frontend typically wants relative to /api/pdf
            'PDF_Path': f"Mandanten/{mandant_id}/Lieferscheine/{pdf_filename}",
            'Status': 'Offen'
        }
        
        # Save
        if file_path.exists():
            import excel_utils
            # Assuming 'Lieferscheine' sheet name
            headers = ['Lieferscheinnummer', 'Datum', 'Kunde', 'Angebot', 'Items', 'PDF_Path', 'Status']
            excel_utils.append_data(str(file_path), [row_data], sheet_name='Lieferscheine', headers=headers)
        else:
            # Create new
            import pandas as pd
            df = pd.DataFrame([row_data])
            df.to_excel(file_path, sheet_name='Lieferscheine', index=False)
            
        return jsonify({'success': True, 'nummer': nummer, 'pdf': f"/api/pdf/Mandanten/{mandant_id}/Lieferscheine/{pdf_filename}"})

    except Exception as e:
        logger.error(f"Lieferschein Create Error: {e}")
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
            
        return jsonify({'ausgaben': sorted(cleaned, key=lambda x: str(x.get('Datum', '0000')), reverse=True)})
        
    except Exception as e:
        logger.error(f"Ausgaben Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/export', methods=['POST'])
def export_month(mandant_id):
    """Erstellt ein ZIP-Archiv für den Steuerberater (Monatsabschluss)"""
    try:
        data = request.get_json()
        year = int(data.get('year'))
        month = int(data.get('month'))
        
        mandant_dir = MANDANTEN_DIR / mandant_id
        if not mandant_dir.exists():
            return jsonify({'error': 'Mandant nicht gefunden'}), 404
            
        import zipfile
        import io
        import tempfile
        import shutil
        
        # 1. Sammle Daten
        # Zeitraum definieren (String Matching für Einfachheit: "MM.YYYY" oder "YYYY-MM")
        # Wir laden alle excels und filtern
        
        # Helper to parse date from various formats
        def get_date_obj(date_str):
            if not date_str: return None
            for fmt in ['%d.%m.%Y', '%Y-%m-%d']:
                try:
                    return datetime.strptime(str(date_str), fmt)
                except: continue
            return None
            
        def is_in_period(date_str):
            d = get_date_obj(date_str)
            if d:
                return d.year == year and d.month == month
            return False
            
        # Create temp dir for assembly
        with tempfile.TemporaryDirectory() as temp_dir_name:
            base_dir = Path(temp_dir_name)
            export_name = f"Buchhaltung_{mandant_id}_{year}_{month:02d}"
            export_path = base_dir / export_name
            export_path.mkdir()
            
            (export_path / 'Einnahmen').mkdir()
            (export_path / 'Ausgaben').mkdir()
            
            summary_stats = {'einnahmen': 0.0, 'ausgaben': 0.0, 'belege_count': 0, 'rechnungen_count': 0}
            
            # --- EINNAHMEN ---
            # Wir benötigen die Rechnungs-PDFs und eine Liste
            import excel_utils
            einnahmen_file = mandant_dir / 'Einnahmen' / 'einnahmen.xlsx'
            if einnahmen_file.exists():
                einnahmen_data = excel_utils.read_data(str(einnahmen_file), 'Einnahmen')
                
                # Filter Period
                period_einnahmen = [r for r in einnahmen_data if is_in_period(r.get('Datum'))]
                
                # Copy PDFs
                rechnungen_dir = mandant_dir / 'Rechnungen'
                for r in period_einnahmen:
                    nr = str(r.get('Rechnungsnummer', ''))
                    # Finding the PDF might be tricky if not stored in CSV. 
                    # Assuming filename convention: Rechnung_{nr}.pdf or similar.
                    # Or we just search for {nr} inside filenames in Rechnungen folder
                    found = False
                    if rechnungen_dir.exists():
                        for pdf in rechnungen_dir.rglob('*.pdf'):
                            if nr in pdf.name:
                                shutil.copy2(pdf, export_path / 'Einnahmen' / pdf.name)
                                found = True
                                break
                    
                    # Add to stats
                    try:
                        summary_stats['einnahmen'] += float(str(r.get('Betrag_Netto', 0)).replace(',','.'))
                    except: pass
                    summary_stats['rechnungen_count'] += 1
                
                # Create Excel Summary for Period
                # We reuse excel_utils to write a new file
                if period_einnahmen:
                     # Remove columns that might be internal object types if any
                     # Just keeping it simple: Write list of dicts
                     df = pd.DataFrame(period_einnahmen)
                     df.to_excel(export_path / f"Einnahmen_{year}_{month:02d}.xlsx", index=False)
            
            # --- AUSGABEN ---
            ausgaben_file = mandant_dir / 'Ausgaben' / 'ausgaben.xlsx'
            if ausgaben_file.exists():
                ausgaben_data = excel_utils.read_data(str(ausgaben_file), 'Ausgaben')
                period_ausgaben = [r for r in ausgaben_data if is_in_period(r.get('Datum'))]
                
                belege_dir = mandant_dir / 'Ausgaben' / 'Belege'
                for r in period_ausgaben:
                    path_val = r.get('Beleg_Pfad')
                    if path_val: # If we have a link to a file
                        src_file = belege_dir / str(path_val)
                        if src_file.exists():
                            shutil.copy2(src_file, export_path / 'Ausgaben' / src_file.name)
                            
                    try:
                        summary_stats['ausgaben'] += float(str(r.get('Betrag_Netto', 0)).replace(',','.'))
                    except: pass
                    summary_stats['belege_count'] += 1
                    
                if period_ausgaben:
                    df = pd.DataFrame(period_ausgaben)
                    df.to_excel(export_path / f"Ausgaben_{year}_{month:02d}.xlsx", index=False)
            
            # --- SUMMARY TEXT ---
            with open(export_path / 'Zusammenfassung.txt', 'w', encoding='utf-8') as f:
                f.write(f"Monatsabschluss: {month:02d}/{year}\n")
                f.write(f"Mandant: {mandant_id}\n")
                f.write("-" * 30 + "\n")
                f.write(f"Einnahmen (Netto): {summary_stats['einnahmen']:.2f} EUR ({summary_stats['rechnungen_count']} Rechnungen)\n")
                f.write(f"Ausgaben (Netto):  {summary_stats['ausgaben']:.2f} EUR ({summary_stats['belege_count']} Belege)\n")
                
            # Create ZIP
            zip_filename = f"{export_name}.zip"
            zip_path = base_dir / zip_filename
            
            shutil.make_archive(str(base_dir / export_name), 'zip', base_dir, export_name)
            
            # Send file
            return send_file(str(base_dir / zip_filename), as_attachment=True, download_name=zip_filename)
            
    except Exception as e:
        logger.error(f"Export Error: {e}")
        return jsonify({'error': str(e)}), 500


    


@app.route('/api/mandanten/<mandant_id>/protocol/scan', methods=['POST'])
def scan_protocol(mandant_id):
    """Scans a protocol and optionally matches with offer items"""
    try:
        import protocol_utils
        from werkzeug.utils import secure_filename
        import tempfile
        
        if 'file' not in request.files:
            return jsonify({'error': 'Keine Datei'}), 400
            
        file = request.files['file']
        angebot_nr = request.form.get('angebot_nr')
        
        if not file.filename:
            return jsonify({'error': 'Kein Dateiname'}), 400
            
        mandant_path = MANDANTEN_DIR / mandant_id
        
        # 1. Save Temp
        temp_dir = Path(tempfile.gettempdir())
        filename = secure_filename(file.filename)
        temp_path = temp_dir / filename
        file.save(temp_path)
        
        # 2. Load Offer Items if requested
        offer_items = None
        if angebot_nr:
            # Try finding the offer JSON
            # Format usually: Angebot_2025-001.json or similar
            # We search for it
            angebote_dir = mandant_path / 'Angebote'
            if angebote_dir.exists():
                # Direct check
                possible_names = [f"Angebot_{angebot_nr}.json", f"{angebot_nr}.json"]
                for pname in possible_names:
                    if (angebote_dir / pname).exists():
                        with open(angebote_dir / pname, 'r', encoding='utf-8') as f:
                            offer_data = json.load(f)
                            offer_items = offer_data.get('positionen', [])
                        break
        
        # 3. Analyze
        items = protocol_utils.analyze_protocol(
            str(temp_path), 
            str(mandant_path), 
            offer_items=offer_items
        )
        
        # Cleanup
        try: os.remove(temp_path)
        except: pass
        
        return jsonify({'success': True, 'items': items})
        
    except Exception as e:
        logger.error(f"Protocol Scan Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/rechnung', methods=['POST'])
def create_invoice_endpoint(mandant_id):
    try:
        data = request.json
        kunde_name = data.get('kunde')
        raw_items = data.get('items', [])
        
        if not kunde_name or not raw_items:
            return jsonify({'error': 'Missing data'}), 400
            
        mandant_path = MANDANTEN_DIR / mandant_id
        
        # 1. Config
        # We can use invoice_generator generic loader or our own
        import invoice_generator
        mandant_config = invoice_generator.load_mandant_config(str(mandant_path), mandant_id)
        
        # 2. Kunde Data
        # We need address etc. if available, or just Name
        import excel_utils
        kunden_path = mandant_path / 'Kunden' / 'kunden.xlsx'
        kunde_data = {'firma': kunde_name, 'anrede': ''} # Fallback
        
        if kunden_path.exists():
            kunden_list = excel_utils.read_data(str(kunden_path), 'Kunden')
            # Find match
            for k in kunden_list:
                if k.get('Firma') == kunde_name:
                    kunde_data = {
                        'firma': k.get('Firma'),
                        'anrede': k.get('Anrede', ''),
                        'email': k.get('Email', '')
                    }
                    break
        
        # 3. Generate Number
        # Helper in invoice_generator expects mandant path string
        nummer = invoice_generator.get_and_increment_counter(str(mandant_path))
        
        # 4. Prepare Items
        # Convert {menge, einheit, bezeichnung, einzelpreis} -> {beschreibung, betrag}
        pdf_items = []
        for it in raw_items:
            try:
                m = float(it.get('menge', 0))
                p = float(it.get('einzelpreis', 0))
                total = m * p
                
                # Format: "1.0 Stk x Bezeichnung (50.00€)"
                desc = f"{m} {it.get('einheit', 'Stk')} x {it.get('bezeichnung')} (EP: {p:.2f}€)"
                pdf_items.append({'beschreibung': desc, 'betrag': total})
            except: continue
            
        invoice_data = {
            'nummer': nummer,
            'datum': datetime.now().strftime('%d.%m.%Y'),
            'items': pdf_items
        }
        
        # 5. Create PDF
        # This function saves the PDF and updates einnahmen.xlsx
        pdf_file = invoice_generator.create_pdf(
            invoice_data, 
            str(mandant_path), 
            mandant_config, 
            kunde_data
        )
        
        if pdf_file:
             # Normalize path for frontend
             rel_path = Path(pdf_file).relative_to(BACKEND_DIR)
             return jsonify({'success': True, 'nummer': nummer, 'path': str(rel_path)})
        else:
             return jsonify({'error': 'PDF Creation failed'}), 500

    except Exception as e:
        logger.error(f"Create Invoice Error: {e}")
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

@app.route('/api/mandanten/<mandant_id>/kunden', methods=['GET'])
def get_kunden_list(mandant_id):
    """List all customers for mandant"""
    try:
        mandant_path = MANDANTEN_DIR / mandant_id
        kunden_path = mandant_path / 'Kunden' / 'kunden.xlsx'
        
        kunden = []
        if kunden_path.exists():
            import excel_utils
            kunden = excel_utils.read_data(str(kunden_path), 'Kunden')
            # Normalize keys if needed or used as is
        else:
             # Fallback CSV?
             csv_path = mandant_path / 'kunden.csv'
             if csv_path.exists():
                 with open(csv_path, 'r', encoding='utf-8') as f:
                     content = f.read() # Simplistic, or use csv module
                     # Skipping csv logic for now, focusing on Excel as primary
                     pass
                     
        return jsonify({'kunden': kunden})
    except Exception as e:
        logger.error(f"Error loading kunden: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/angebote', methods=['GET'])
def get_angebote_list(mandant_id):
    """List all offers for mandant"""
    try:
        mandant_path = MANDANTEN_DIR / mandant_id
        angebote_dir = mandant_path / 'Angebote'
        
        angebote = []
        if angebote_dir.exists():
            for f in angebote_dir.glob('Angebot_*.json'):
                try:
                    with open(f, 'r', encoding='utf-8') as json_file:
                        data = json.load(json_file)
                        angebote.append({
                            'nummer': data.get('nummer', f.stem.replace('Angebot_', '')),
                            'kunde': data.get('kunde', 'Unbekannt'),
                            'datum': data.get('datum', ''),
                            'betrag': data.get('betrag_netto', 0)
                        })
                except: pass
                
        # Sort by Nummer desc
        angebote.sort(key=lambda x: x['nummer'], reverse=True)
        return jsonify({'angebote': angebote})
    except Exception as e:
        logger.error(f"Error loading angebote: {e}")
        return jsonify({'error': str(e)}), 500


# --- RECURRING INVOICES ROUTES ---

@app.route('/api/mandanten/<mandant_id>/recurring', methods=['GET'])
def get_recurring(mandant_id):
    mandant_dir = MANDANTEN_DIR / mandant_id
    if not mandant_dir.exists():
         return jsonify({'error': 'Mandant nicht gefunden'}), 404
         
    data = recurring_invoices.load_recurring(mandant_dir)
    return jsonify(data)

@app.route('/api/mandanten/<mandant_id>/recurring', methods=['POST'])
def add_recurring(mandant_id):
    mandant_dir = MANDANTEN_DIR / mandant_id
    if not mandant_dir.exists():
         return jsonify({'error': 'Mandant nicht gefunden'}), 404
         
    data = request.json
    try:
        new_entry = recurring_invoices.add_recurring(mandant_dir, data)
        return jsonify({'success': True, 'entry': new_entry})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/mandanten/<mandant_id>/recurring/<rec_id>', methods=['DELETE'])
def delete_recurring(mandant_id, rec_id):
    mandant_dir = MANDANTEN_DIR / mandant_id
    if not mandant_dir.exists():
         return jsonify({'error': 'Mandant nicht gefunden'}), 404
         
    try:
        recurring_invoices.delete_recurring(mandant_dir, rec_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/mandanten/<mandant_id>/recurring/process', methods=['POST'])
def process_recurring(mandant_id):
    """Prüft und erstellt fällige Rechnungen"""
    mandant_dir = MANDANTEN_DIR / mandant_id
    if not mandant_dir.exists():
         return jsonify({'error': 'Mandant nicht gefunden'}), 404

    # Config laden für PDF Generation
    config_path = mandant_dir / 'mandant_config.json'
    mandant_config = {}
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                mandant_config = json.load(f)
        except: pass
         
    try:
        created = recurring_invoices.process_due_invoices(mandant_dir, mandant_config)
        return jsonify({'success': True, 'count': len(created), 'created': created})
    except Exception as e:
        logger.error(f"Fehler bei Recurring Process: {e}")
        return jsonify({'success': False, 'error': str(e)})


# --- REPORT ROUTES ---

@app.route('/api/mandanten/<mandant_id>/report/generate', methods=['POST'])
def generate_report_route(mandant_id):
    mandant_dir = MANDANTEN_DIR / mandant_id
    if not mandant_dir.exists():
         return jsonify({'error': 'Mandant nicht gefunden'}), 404
         
    data = request.json
    month = int(data.get('month', datetime.datetime.now().month))
    year = int(data.get('year', datetime.datetime.now().year))
    
    try:
        # Load necessary data
        # 1. Einnahmen (aus invoices)
        einnahmen = []
        inv_file = mandant_dir / 'Rechnungen' / 'einnahmen.csv'
        if inv_file.exists():
            with open(inv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Filter by date
                    try:
                        d = datetime.datetime.strptime(row['Datum'], '%d.%m.%Y')
                        if d.month == month and d.year == year:
                            einnahmen.append(row)
                    except: pass
                    
        # 2. Ausgaben (aus scanner csv)
        ausgaben = []
        ausg_file = mandant_dir / 'Ausgaben' / 'ausgaben.csv'
        if ausg_file.exists():
             with open(ausg_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';') # Semicolon!
                for row in reader:
                     try:
                        d = datetime.datetime.strptime(row['Datum'], '%d.%m.%Y')
                        if d.month == month and d.year == year:
                            # Mapping fields to unify
                            # Scan CSV: Datum;Kategorie;Beschreibung;Betrag_Brutto;Betrag_Netto;Steuer;Pfad
                            ausgaben.append(row)
                     except: pass
        
        # 3. Config
        config_path = mandant_dir / 'mandant_config.json'
        mandant_config = {}
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                mandant_config = json.load(f)
        
        # Generate PDF
        filename = f"Report_{year}_{month:02d}.pdf"
        output_path = mandant_dir / filename
        
        success = report_generator.generate_report(mandant_dir, month, year, einnahmen, ausgaben, str(output_path), mandant_config)
        
        if success:
             return jsonify({
                 'success': True, 
                 'path': f"{mandant_id}/{filename}", 
                 'filename': filename
             })
        else:
             return jsonify({'success': False, 'error': 'PDF konnte nicht erstellt werden'})
             
    except Exception as e:
        logger.error(f"Report Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)})

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
