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

# Import logger
from logger import get_logger
logger = get_logger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Paths
BACKEND_DIR = Path(__file__).resolve().parent
MANDANTEN_DIR = BACKEND_DIR / 'Mandanten'

FRONTEND_DIR = BACKEND_DIR.parent / 'frontend'

# Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

# Initialize Firebase Admin
try:
    # Try Application Default Credentials first (for Cloud Run)
    firebase_admin.initialize_app()
    logger.info("🔥 Firebase Admin SDK initialized with ADC")
except:
    # Fallback to service account key file (for local development)
    service_account_path = BACKEND_DIR / 'service-account-key.json'
    if service_account_path.exists():
        cred = credentials.Certificate(str(service_account_path))
        firebase_admin.initialize_app(cred)
        logger.info("🔥 Firebase Admin SDK initialized with Service Account Key")
    else:
        logger.warning("⚠️ Firebase Admin SDK not initialized - no credentials found")

# Authentication decorator
from functools import wraps

def require_auth(f):
    """Decorator to require Firebase authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.warning(f"Unauthorized access attempt to {request.path}")
            return jsonify({'error': 'Unauthorized - No token provided'}), 401
        
        # Extract token
        id_token = auth_header.split('Bearer ')[1]
        
        try:
            # Verify the token
            decoded_token = firebase_auth.verify_id_token(id_token)
            request.user = decoded_token  # Attach user info to request
            logger.info(f"Authenticated user: {decoded_token.get('email')}")
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return jsonify({'error': 'Unauthorized - Invalid token'}), 401
    
    return decorated_function

@app.route('/api/health')
def health_check():
    """Health check"""
    return jsonify({
        'status': 'online',
        'service': 'Mein Business API',
        'version': '1.0'
    })

@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(FRONTEND_DIR, path)

@app.route('/api/mandanten', methods=['GET'])
def get_mandanten():
    """Liste aller Mandanten mit Basisinformationen"""
    try:
        mandanten = []
        
        if not MANDANTEN_DIR.exists():
            return jsonify({'mandanten': []})
        
        for mandant_dir in MANDANTEN_DIR.iterdir():
            if not mandant_dir.is_dir() or mandant_dir.name.startswith('.') or mandant_dir.name == 'lost+found':
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
        
        unternehmensform = "Standard"
        mandant_config_path = mandant_dir / 'mandant_config.json'
        if mandant_config_path.exists():
            try:
                import json
                with open(mandant_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    unternehmensform = config.get('unternehmensform', 'Standard')
            except: pass
            
        stats = {
            'mandant_id': mandant_id,
            'unternehmensform': unternehmensform,
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
            # Load existing PDFs to filter deleted ones
            rechnungen_dir = mandant_dir / 'Rechnungen'
            existing_pdfs = set()
            if rechnungen_dir.exists():
                for pdf in rechnungen_dir.rglob('*.pdf'):
                    existing_pdfs.add(pdf.stem)
                    existing_pdfs.add(pdf.name)

            for row in data:
                # Check if PDF exists
                nr = str(row.get('Rechnungsnummer', ''))
                nr_safe = nr.replace('-', '_').replace(' ', '_')
                found = any(nr in p or nr_safe in p for p in existing_pdfs)
                if not found and nr:
                    continue # Skip if PDF was deleted
                
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
            allowed_fields = ['firma', 'mandantennummer', 'unternehmensform', 'geschaeftsfuehrer', 'logo', 'adresse', 'bank', 'smtp', 'ustid', 'steuernummer']
            
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
        filepath_clean = filepath.lstrip('/').lstrip('\\').replace('/', os.sep)
        full_path = BACKEND_DIR / filepath_clean
        
        print(f"DEBUG PDF REQUEST: '{filepath}'")
        print(f"DEBUG FULL PATH:   '{full_path}'")
        print(f"DEBUG EXISTS?:     {full_path.exists()}")
        
        logger.info(f"PDF Request: {filepath} -> {full_path}")
        
        if not full_path.exists():
            logger.error(f"PDF nicht gefunden: {full_path}")
            return jsonify({'error': f'Datei nicht gefunden: {full_path}'}), 404
        
        from flask import send_file
        # Determine mimetype based on extension
        mimetype = None
        if full_path.suffix.lower() == '.pdf':
            mimetype = 'application/pdf'
        elif full_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            mimetype = 'image/jpeg' if full_path.suffix.lower() in ['.jpg', '.jpeg'] else 'image/png'
            
        return send_file(full_path, mimetype=mimetype)
    
    except Exception as e:
        logger.error(f"Fehler beim PDF-Abruf: {str(e)}")
        return jsonify({'error': str(e)}), 500



@app.route('/api/mandanten/<mandant_id>/check-duplicate', methods=['POST'])
def check_duplicate_invoice(mandant_id):
    """Prüft auf ähnliche Rechnungen (Duplikat-Warnung)"""
    try:
        data = request.get_json()
        kunde_name = data.get('kunde', '').strip()
        new_total = float(data.get('total', 0))
        
        # Einstellungen
        DAYS_THRESHOLD = 30
        AMOUNT_TOLERANCE = 0.50 # 50 cent toleranz
        
        mandant_dir = MANDANTEN_DIR / mandant_id
        xlsx_file = mandant_dir / 'Einnahmen' / 'einnahmen.xlsx'
        csv_file = mandant_dir / 'Einnahmen' / 'einnahmen.csv'
        
        invoices = []
        if xlsx_file.exists():
            import excel_utils
            invoices = excel_utils.read_data(str(xlsx_file), 'Einnahmen')
        elif csv_file.exists():
            with open(csv_file, 'r', encoding='utf-8') as f:
                invoices = list(csv.DictReader(f))
                
        matches = []
        now = datetime.now()
        
        for inv in invoices:
            # 1. Check Kunde (fuzzy or exact)
            inv_kunde = inv.get('Kunde', '')
            if kunde_name.lower() not in inv_kunde.lower() and inv_kunde.lower() not in kunde_name.lower():
                continue
                
            # 2. Check Amount
            try:
                # Parse amount (handle Deutsche Formate 1.000,00)
                raw_amt = str(inv.get('Betrag_Netto', '0')).replace('.', '').replace(',', '.')
                old_total = float(raw_amt)
                
                if abs(old_total - new_total) > AMOUNT_TOLERANCE:
                    continue
            except:
                continue
                
            # 3. Check Date
            try:
                inv_date_str = inv.get('Datum', '')
                inv_date = datetime.strptime(inv_date_str, '%d.%m.%Y')
                days_diff = (now - inv_date).days
                
                if days_diff <= DAYS_THRESHOLD:
                    matches.append({
                        'nummer': inv.get('Rechnungsnummer'),
                        'datum': inv_date_str,
                        'kunde': inv_kunde,
                        'betrag': old_total,
                        'days_ago': days_diff
                    })
            except:
                continue

        return jsonify({
            'duplicate': len(matches) > 0,
            'matches': matches
        })

    except Exception as e:
        logger.error(f"Fehler Check-Duplicate: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/rechnungen', methods=['GET'])
def get_mandant_rechnungen_files(mandant_id):
    """Listet alle Rechnungs-PDFs aus dem Rechnungen-Ordner auf"""
    try:
        mandant_dir = MANDANTEN_DIR / mandant_id
        rechnungen_dir = mandant_dir / 'Rechnungen'
        
        if not rechnungen_dir.exists():
            return jsonify({'rechnungen': []})
            
        files = []
        # Scan all PDF files in Rechnungen directory and subdirectories
        for f in rechnungen_dir.rglob('*.pdf'):
            try:
                stat = f.stat()
                # Create path relative to backend dir for the PDF serving endpoint
                # Format: "Mandanten/ID/Rechnungen/File.pdf" or "Mandanten/ID/Rechnungen/Subdir/File.pdf"
                rel_path = str(f.relative_to(BACKEND_DIR)).replace('\\', '/')
                
                files.append({
                    'name': f.name,
                    'path': rel_path,
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
            except Exception as e:
                logger.error(f"Error reading file {f}: {e}")
                continue
                
        # Sort by modification time descending (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        logger.info(f"Found {len(files)} invoice PDFs for {mandant_id}")
        return jsonify({'rechnungen': files})

    except Exception as e:
        logger.error(f"Fehler beim Laden der Rechnungs-Dateien: {str(e)}")
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
        
        # Filter out invoices whose PDF was deleted from the Rechnungen folder
        rechnungen_dir = mandant_dir / 'Rechnungen'
        if rechnungen_dir.exists():
            existing_pdfs = set()
            for pdf in rechnungen_dir.rglob('*.pdf'):
                existing_pdfs.add(pdf.stem)
                existing_pdfs.add(pdf.name)
            
            filtered = []
            for inv in invoices:
                nr = str(inv.get('Rechnungsnummer', ''))
                # Normalize: RE-001-2026-02-001 -> RE_001_2026_02_001
                nr_safe = nr.replace('-', '_').replace(' ', '_')
                # Check if any PDF contains this invoice number
                found = any(nr in p or nr_safe in p for p in existing_pdfs)
                if found or not nr:
                    filtered.append(inv)
            
            logger.info(f"Einnahmen: {len(invoices)} total, {len(filtered)} mit vorhandener PDF")
            invoices = filtered
        
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
        unternehmensform = data.get('unternehmensform', 'Einzelunternehmen').strip()
        strasse = data.get('strasse', '').strip()
        ort = data.get('ort', '').strip()
        geschaeftsfuehrer = data.get('geschaeftsfuehrer', '').strip()
        ustid = data.get('ustid', '').strip()
        steuernummer = data.get('steuernummer', '').strip()
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
            'unternehmensform': unternehmensform,
            'adresse': {'strasse': strasse, 'ort': ort},
            'geschaeftsfuehrer': geschaeftsfuehrer,
            'ustid': ustid,
            'steuernummer': steuernummer,
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
        
        # Initialize invoice counter if start number provided
        start_nr = int(data.get('start_invoice_number', 0))
        if start_nr > 0:
            from datetime import date as _date
            counter_data = {
                "year": str(_date.today().year),
                "month": f"{_date.today().month:02d}",
                "count": start_nr - 1
            }
            with open(mandant_path / 'counter.json', 'w', encoding='utf-8') as f:
                json.dump(counter_data, f, indent=4)
            logger.info(f"Counter initialisiert: Start bei {start_nr}")
        
        logger.info(f"Mandant erstellt: {safe_name}")
        return jsonify({'success': True, 'mandant_id': safe_name, 'config': config})
    
    except Exception as e:
        logger.error(f"Fehler beim Anlegen des Mandanten: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>', methods=['DELETE'])
def delete_mandant(mandant_id):
    """Löscht einen Mandanten komplett"""
    try:
        mandant_path = MANDANTEN_DIR / mandant_id
        if not mandant_path.exists():
            return jsonify({'error': 'Mandant nicht gefunden'}), 404
        
        import shutil
        import uuid
        import os
        
        # 1. Sofort umbenennen, damit es in der UI nicht mehr auftaucht! (Versteckter Ordner)
        trash_path = MANDANTEN_DIR / f".deleted_{mandant_id}_{uuid.uuid4().hex[:8]}"
        try:
            mandant_path.rename(trash_path)
            mandant_path = trash_path  # Now try to delete the trash path
        except Exception as e:
            logger.warning(f"Konnte Mandant nicht umbenennen (File Lock?): {e}")
            # We continue and try to delete directly anyway
        
        # 2. Normaler Löschversuch
        try:
            # Versuche read-only flags zu entfernen
            import stat
            def remove_readonly(func, path, excinfo):
                try:
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                except:
                    pass
            shutil.rmtree(mandant_path, onerror=remove_readonly)
        except Exception:
            pass
            
        # Falls immer noch da: Windows/Linux CMD Fallback
        if mandant_path.exists():
            import subprocess
            try:
                if os.name == 'nt':
                    subprocess.run(f'rmdir /s /q "{str(mandant_path)}"', shell=True)
                else:
                    subprocess.run(['rm', '-rf', str(mandant_path)])
            except Exception:
                pass
        
        if mandant_path.exists():
            logger.warning("Ordner konnte wegen Dateisperre nicht komplett gelöscht werden, ist aber versteckt.")
            # Wir geben trotzdem Erfolg zurück, da der Ordner umbenannt/versteckt wurde
            # und für den User unsichtbar ist.
            
        logger.info(f"Mandant gelöscht/versteckt: {mandant_id}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Mandanten {mandant_id}: {str(e)}")
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
        strasse = data.get('strasse', '').strip()
        plz = data.get('plz', '').strip()
        ort = data.get('ort', '').strip()
        
        if not firma and not email:
            return jsonify({'error': 'Bitte gib zumindest einen Namen/Firma oder eine Email an'}), 400
            
        if not firma:
            firma = email # Fallback für die Anzeige in der Liste
        
        mandant_dir = MANDANTEN_DIR / mandant_id
        kunden_xlsx = mandant_dir / 'Kunden' / 'kunden.xlsx'
        kunden_xlsx.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare data
        kunde_data = {
            'Firma': firma,
            'Email': email,
            'Anrede': anrede,
            'Strasse': strasse,
            'PLZ': plz,
            'Ort': ort
        }
        
        # Save to Excel
        import excel_utils
        excel_utils.append_data(
            str(kunden_xlsx),
            kunde_data,
            'Kunden',
            ['Firma', 'Email', 'Anrede', 'Strasse', 'PLZ', 'Ort']
        )
        
        logger.info(f"Kunde erstellt: {mandant_id}/{firma}")
        return jsonify({'success': True, 'kunde': kunde_data})
    
    except Exception as e:
        logger.error(f"Fehler beim Anlegen des Kunden: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/kunden/<path:firma>', methods=['DELETE'])
def delete_kunde(mandant_id, firma):
    """Löscht einen Kunden"""
    try:
        mandant_dir = MANDANTEN_DIR / mandant_id
        kunden_xlsx = mandant_dir / 'Kunden' / 'kunden.xlsx'
        
        import excel_utils
        success = excel_utils.delete_row(str(kunden_xlsx), 'Firma', firma, 'Kunden')
        
        if success:
            logger.info(f"Kunde gelöscht: {mandant_id}/{firma}")
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Kunde nicht gefunden'}), 404
            
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Kunden: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/kunden/<path:firma>', methods=['PUT'])
def update_kunde(mandant_id, firma):
    """Aktualisiert einen Kunden"""
    try:
        data = request.get_json()
        new_firma = data.get('firma', '').strip()
        email = data.get('email', '').strip()
        
        if not new_firma and not email:
            return jsonify({'error': 'Bitte gib zumindest einen Namen/Firma oder eine Email an'}), 400
            
        if not new_firma:
            new_firma = email
            
        mandant_dir = MANDANTEN_DIR / mandant_id
        kunden_xlsx = mandant_dir / 'Kunden' / 'kunden.xlsx'
        
        kunde_data = {
            'Firma': new_firma,
            'Email': email,
            'Anrede': data.get('anrede', 'Sehr geehrte Damen und Herren'),
            'Strasse': data.get('strasse', '').strip(),
            'PLZ': data.get('plz', '').strip(),
            'Ort': data.get('ort', '').strip()
        }
        
        import excel_utils
        success = excel_utils.update_row(str(kunden_xlsx), 'Firma', firma, kunde_data, 'Kunden')
        
        if success:
            logger.info(f"Kunde aktualisiert: {mandant_id}/{firma}")
            return jsonify({'success': True, 'kunde': kunde_data})
        else:
            return jsonify({'error': 'Kunde nicht gefunden'}), 404
            
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren des Kunden: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/mandanten/<mandant_id>/recurring', methods=['GET'])
def get_recurring(mandant_id):
    """Liste aller Abos"""
    try:
        import recurring_invoices
        mandant_dir = MANDANTEN_DIR / mandant_id
        data = recurring_invoices.load_recurring(mandant_dir)
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error loading recurring: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/recurring', methods=['POST'])
def add_recurring(mandant_id):
    """Neues Abo anlegen"""
    try:
        data = request.get_json()
        import recurring_invoices
        mandant_dir = MANDANTEN_DIR / mandant_id
        
        entry = recurring_invoices.add_recurring(mandant_dir, data)
        return jsonify({'success': True, 'entry': entry})
        
    except Exception as e:
        logger.error(f"Error adding recurring: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/recurring/<entry_id>', methods=['DELETE'])
def delete_recurring(mandant_id, entry_id):
    """Abo löschen"""
    try:
        import recurring_invoices
        mandant_dir = MANDANTEN_DIR / mandant_id
        recurring_invoices.delete_recurring(mandant_dir, entry_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/recurring/process', methods=['POST'])
def process_recurring(mandant_id):
    """Manuell Abos prüfen und ausführen"""
    try:
        import recurring_invoices
        mandant_dir = MANDANTEN_DIR / mandant_id
        
        # Load Config
        config_file = mandant_dir / 'mandant_config.json'
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        created = recurring_invoices.process_due_invoices(mandant_dir, config)
        
        return jsonify({
            'success': True, 
            'count': len(created),
            'invoices': [str(p) for p in created]
        })
        
    except Exception as e:
        logger.error(f"Error processing recurring: {e}")
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
    """Liste aller Angebote - scannt PDFs direkt aus Ordner"""
    try:
        mandant_dir = MANDANTEN_DIR / mandant_id
        angebote_dir = mandant_dir / 'Angebote'
        
        if not angebote_dir.exists():
            return jsonify({'angebote': []})
        
        # Scan ALL PDFs in directory
        all_pdfs = {}
        for pdf_file in angebote_dir.rglob('*.pdf'):
            try:
                stat = pdf_file.stat()
                rel_path = pdf_file.relative_to(angebote_dir)
                
                # Extract info from filename
                name = pdf_file.stem
                nummer = name
                # Try to extract structured number (e.g., ANG-001-2026-001)
                if '-' in name:
                    nummer = name  # Use full name as nummer
                
                all_pdfs[str(rel_path)] = {
                    'nummer': nummer,
                    'filename': pdf_file.name,
                    'pdf_path': f"/api/pdf/Mandanten/{mandant_id}/Angebote/{rel_path}".replace('\\', '/'),
                    'datum': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d'),
                    'kunde': '',  # Will be filled from Excel if available
                    'status': 'Offen',
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                }
            except Exception as e:
                logger.error(f"Error reading PDF {pdf_file}: {e}")
                continue
        
        # Try to enrich with Excel data
        angebote_file = mandant_dir / 'Angebote' / 'angebote.xlsx'
        if angebote_file.exists():
            try:
                import excel_utils
                data = excel_utils.read_data(str(angebote_file), 'Angebote')
                
                for row in data:
                    item = {k.lower(): v for k, v in row.items()}
                    nummer = item.get('nummer') or ''
                    kunde = item.get('kunde') or ''
                    status = item.get('status') or 'Offen'
                    datum = item.get('datum') or ''
                    
                    # Try to match with PDF by nummer
                    for key, pdf_info in all_pdfs.items():
                        if nummer and nummer in pdf_info['nummer']:
                            pdf_info['kunde'] = kunde
                            pdf_info['status'] = status
                            if datum:
                                pdf_info['datum'] = str(datum)
                            break
            except Exception as e:
                logger.warning(f"Could not read Excel: {e}")
        
        # Convert to list and sort by date
        result = list(all_pdfs.values())
        result.sort(key=lambda x: x.get('modified', 0), reverse=True)
        
        logger.info(f"Found {len(result)} Angebote for {mandant_id}")
        return jsonify({'angebote': result})
    
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
        nummer = offer_generator.get_and_increment_offer_counter(str(mandant_dir), mandant_config)
        
        # Create PDF with timestamp
        timestamp = int(datetime.now().timestamp())
        pdf_filename = f"{nummer}.pdf"
        pdf_path = angebote_dir / pdf_filename
        
        leistungs_von = data.get('leistungs_von', '')
        leistungs_bis = data.get('leistungs_bis', '')
        
        # Retrieve address from kunden.xlsx if exists
        kunde_adresse = ""
        import excel_utils
        kunden_path = mandant_dir / 'Kunden' / 'kunden.xlsx'
        if kunden_path.exists():
            kunden_list = excel_utils.read_data(str(kunden_path), 'Kunden')
            for k in kunden_list:
                if k.get('Firma') == kunde_name:
                    adr_parts = []
                    if k.get('Strasse'): adr_parts.append(str(k.get('Strasse')))
                    
                    plz = k.get('PLZ', '')
                    if isinstance(plz, float) and plz.is_integer():
                        plz = str(int(plz))
                    elif isinstance(plz, str) and plz.endswith('.0'):
                        plz = plz[:-2]
                    else:
                        plz = str(plz)
                        
                    plz_ort = f"{plz} {k.get('Ort', '')}".strip()
                    if plz_ort: adr_parts.append(plz_ort)
                    kunde_adresse = '<br/>'.join(adr_parts)
                    break
                    
        brutto, netto = offer_generator.create_offer_pdf(
            str(mandant_dir),
            mandant_config,
            kunde_name,
            positionen,
            str(pdf_path),
            nummer,
            leistungs_von=leistungs_von,
            leistungs_bis=leistungs_bis,
            kunde_adresse=kunde_adresse
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
    """Liste aller Lieferscheine/Protokolle - scannt auch PDFs direkt"""
    try:
        mandant_path = MANDANTEN_DIR / mandant_id
        if not mandant_path.exists():
            return jsonify({'error': 'Mandant nicht gefunden'}), 404
            
        lieferscheine_dir = mandant_path / 'Lieferscheine'
        if not lieferscheine_dir.exists():
            return jsonify({'lieferscheine': []})
        
        # Scan ALL PDFs in directory (including subdirectories)
        all_pdfs = {}
        for pdf_file in lieferscheine_dir.rglob('*.pdf'):
            try:
                stat = pdf_file.stat()
                rel_path = pdf_file.relative_to(lieferscheine_dir)
                
                # Extract info from filename
                name = pdf_file.stem
                # Try to extract number from filename like "Lieferschein_PROT-2026-001_..."
                nummer = name
                if '_' in name:
                    parts = name.split('_')
                    if len(parts) >= 2:
                        nummer = parts[1]  # e.g., "PROT-2026-001"
                
                all_pdfs[str(rel_path)] = {
                    'nummer': nummer,
                    'filename': pdf_file.name,
                    'pdf_path': f"/api/pdf/Mandanten/{mandant_id}/Lieferscheine/{rel_path}".replace('\\', '/'),
                    'datum': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d'),
                    'kunde': '',  # Will be filled from Excel if available
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                }
            except Exception as e:
                logger.error(f"Error reading PDF {pdf_file}: {e}")
                continue
        
        # Try to enrich with Excel data
        file_path = mandant_path / 'Lieferscheine' / 'lieferscheine.xlsx'
        if file_path.exists():
            try:
                import excel_utils
                data = excel_utils.read_data(str(file_path), 'Lieferscheine')
                
                for row in data:
                    # Normalize keys
                    item = {k.lower(): v for k, v in row.items()}
                    nummer = item.get('lieferscheinnummer') or item.get('nummer') or ''
                    kunde = item.get('kunde') or ''
                    datum = item.get('datum') or ''
                    
                    # Try to match with PDF
                    for key, pdf_info in all_pdfs.items():
                        if nummer and nummer in pdf_info['nummer']:
                            pdf_info['kunde'] = kunde
                            if datum:
                                pdf_info['datum'] = str(datum)
                            break
            except Exception as e:
                logger.warning(f"Could not read Excel: {e}")
        
        # Convert to list and sort by date
        result = list(all_pdfs.values())
        result.sort(key=lambda x: x.get('modified', 0), reverse=True)
        
        logger.info(f"Found {len(result)} Lieferscheine for {mandant_id}")
        return jsonify({'lieferscheine': result})
        
    except Exception as e:
        logger.error(f"LS Fehler: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/lieferscheine/sync', methods=['POST'])
def sync_lieferscheine(mandant_id):
    """Synchronisiert alle PDFs im Lieferscheine-Ordner mit der Excel-Tabelle"""
    try:
        mandant_path = MANDANTEN_DIR / mandant_id
        if not mandant_path.exists():
            return jsonify({'error': 'Mandant nicht gefunden'}), 404
            
        lieferscheine_dir = mandant_path / 'Lieferscheine'
        file_path = lieferscheine_dir / 'lieferscheine.xlsx'
        
        if not lieferscheine_dir.exists():
            return jsonify({'error': 'Lieferscheine-Ordner nicht gefunden'}), 404
        
        # Read existing Excel entries
        import excel_utils
        existing_entries = set()
        if file_path.exists():
            try:
                data = excel_utils.read_data(str(file_path), 'Lieferscheine')
                for row in data:
                    # Get the PDF path/filename
                    pdf_path = row.get('PDF_Path') or row.get('pdf_path') or ''
                    if pdf_path:
                        existing_entries.add(str(pdf_path))
                    # Also track by number
                    nummer = row.get('Lieferscheinnummer') or row.get('Nummer') or row.get('nummer') or ''
                    if nummer:
                        existing_entries.add(str(nummer))
            except Exception as e:
                logger.warning(f"Could not read existing Excel: {e}")
        
        # Scan all PDFs
        added = 0
        for pdf_file in lieferscheine_dir.rglob('*.pdf'):
            filename = pdf_file.name
            
            # Check if already in Excel
            if filename in existing_entries:
                continue
            
            # Extract info from filename
            name = pdf_file.stem
            nummer = name
            if '_' in name:
                parts = name.split('_')
                if len(parts) >= 2:
                    nummer = parts[1]
            
            if nummer in existing_entries:
                continue
            
            # Extract customer name from subdirectory if exists
            rel_path = pdf_file.relative_to(lieferscheine_dir)
            kunde = ''
            if len(rel_path.parts) > 1:
                kunde = rel_path.parts[0]  # Parent folder name as customer
            
            # Add to Excel
            stat = pdf_file.stat()
            new_row = {
                'Lieferscheinnummer': nummer,
                'Datum': datetime.fromtimestamp(stat.st_mtime).strftime('%d.%m.%Y'),
                'Kunde': kunde,
                'AngebotRef': '',
                'Status': 'Offen',
                'Items': ''
            }
            
            try:
                excel_utils.append_data(str(file_path), new_row, sheet_name="Lieferscheine")
                added += 1
                existing_entries.add(filename)
                existing_entries.add(nummer)
            except Exception as e:
                logger.error(f"Could not add {filename} to Excel: {e}")
        
        logger.info(f"Synced Lieferscheine for {mandant_id}: {added} new entries added")
        return jsonify({
            'success': True,
            'added': added,
            'message': f'{added} neue Einträge hinzugefügt'
        })
        
    except Exception as e:
        logger.error(f"Sync Fehler: {e}")
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
        nummer = delivery_generator.get_and_increment_delivery_counter(str(mandant_path), mandant_config)
        
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

@app.route('/api/mandanten/<mandant_id>/rechnung/next-number', methods=['GET'])
def get_next_invoice_number(mandant_id):
    """Zeigt die nächste Rechnungsnummer an (ohne zu inkrementieren)"""
    try:
        mandant_path = MANDANTEN_DIR / mandant_id
        if not mandant_path.exists():
            return jsonify({'error': 'Mandant nicht gefunden'}), 404
        
        import invoice_generator
        mandant_config = invoice_generator.load_mandant_config(str(mandant_path), mandant_id)
        
        # Peek at counter without incrementing
        counter_file = mandant_path / 'counter.json'
        today = datetime.now()
        current_year = str(today.year)
        current_month = f"{today.month:02d}"
        
        mandanten_nr = mandant_config.get('mandantennummer', '000')
        
        count = 0
        if counter_file.exists():
            try:
                with open(counter_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if str(data.get('year')) == current_year and str(data.get('month')) == current_month:
                    count = data.get('count', 0)
            except: pass
        
        next_count = count + 1
        next_number = f"RE-{mandanten_nr}-{current_year}-{current_month}-{next_count:03d}"
        
        return jsonify({'next_number': next_number, 'count': next_count})
    except Exception as e:
        logger.error(f"Next number error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/rechnung/set-counter', methods=['PUT'])
def set_invoice_counter(mandant_id):
    """Setzt den Rechnungszähler auf einen bestimmten Wert"""
    try:
        data = request.get_json()
        new_count = int(data.get('count', 0))
        if new_count < 1:
            return jsonify({'error': 'Zähler muss mindestens 1 sein'}), 400
        
        mandant_path = MANDANTEN_DIR / mandant_id
        if not mandant_path.exists():
            return jsonify({'error': 'Mandant nicht gefunden'}), 404
        
        counter_file = mandant_path / 'counter.json'
        today = datetime.now()
        
        counter_data = {
            "year": str(today.year),
            "month": f"{today.month:02d}",
            "count": new_count - 1  # -1 weil get_and_increment +1 macht
        }
        
        with open(counter_file, 'w', encoding='utf-8') as f:
            json.dump(counter_data, f, indent=4)
        
        logger.info(f"Counter für {mandant_id} auf {new_count} gesetzt")
        return jsonify({'success': True, 'next_count': new_count})
    except Exception as e:
        logger.error(f"Set counter error: {e}")
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
                    adr_parts = []
                    if k.get('Strasse'): adr_parts.append(str(k.get('Strasse')))
                    
                    plz = k.get('PLZ', '')
                    if isinstance(plz, float) and plz.is_integer():
                        plz = str(int(plz))
                    elif isinstance(plz, str) and plz.endswith('.0'):
                        plz = plz[:-2]
                    else:
                        plz = str(plz)
                        
                    plz_ort = f"{plz} {k.get('Ort', '')}".strip()
                    if plz_ort: adr_parts.append(plz_ort)
                    
                    kunde_data = {
                        'firma': k.get('Firma'),
                        'anrede': k.get('Anrede', ''),
                        'email': k.get('Email', ''),
                        'adresse': '<br/>'.join(adr_parts) if adr_parts else ''
                    }
                    break
        
        # 3. Generate Number
        # Helper in invoice_generator expects mandant path string
        nummer = invoice_generator.get_and_increment_counter(str(mandant_path), mandant_config)
        
        # 4. Prepare Items
        # Convert {menge, einheit, bezeichnung, einzelpreis} -> {menge, einheit, beschreibung, einzelpreis}
        pdf_items = []
        for it in raw_items:
            try:
                m = float(it.get('menge', 0))
                p = float(it.get('einzelpreis', 0))
                # total = m * p # Calculated in generator
                
                pdf_items.append({
                    'menge': m,
                    'einheit': it.get('einheit', 'Stk'),
                    'beschreibung': it.get('bezeichnung', ''),
                    'einzelpreis': p
                })
            except: continue
            
        invoice_data = {
            'nummer': nummer,
            'datum': datetime.now().strftime('%d.%m.%Y'),
            'leistungs_von': data.get('leistungs_von', ''),
            'leistungs_bis': data.get('leistungs_bis', ''),
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

@app.route('/api/mandanten/<mandant_id>/report/generate', methods=['POST'])
def generate_report_endpoint(mandant_id):
    """Generates monthly report PDF"""
    try:
        data = request.json
        year_str = str(data.get('year'))
        month_str = str(data.get('month'))
        
        try:
            year = int(year_str)
            month = int(month_str)
        except:
             return jsonify({'error': 'Invalid Date'}), 400
             
        mandant_path = MANDANTEN_DIR / mandant_id
        if not mandant_path.exists():
            return jsonify({'error': 'Mandant nicht gefunden'}), 404
            
        # 1. Gather Data
        import excel_utils
        
        # Einnahmen
        einnahmen = []
        path_in = mandant_path / 'Einnahmen' / 'einnahmen.xlsx'
        if path_in.exists():
            all_in = excel_utils.read_data(str(path_in), 'Einnahmen')
            einnahmen = filter_by_month(all_in, year, month)
            
        # Ausgaben
        ausgaben = []
        path_out = mandant_path / 'Ausgaben' / 'ausgaben.xlsx'
        if path_out.exists():
            all_out = excel_utils.read_data(str(path_out), 'Ausgaben')
            ausgaben = filter_by_month(all_out, year, month)
            
        # 2. Config
        import json
        config_path = mandant_path / 'mandant_config.json'
        config = {}
        if config_path.exists():
            with open(config_path,'r',encoding='utf-8') as f:
                config = json.load(f)
                
        # 3. Generate PDF
        import report_generator
        
        output_dir = mandant_path / 'Controlling' / 'Reports'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"Report_{year}_{month:02d}.pdf"
        output_path = output_dir / filename
        
        report_generator.generate_report(
            str(mandant_path),
            month,
            year,
            einnahmen,
            ausgaben,
            str(output_path),
            config
        )
        
        # Verify creation
        if not output_path.exists():
             raise Exception("PDF File was not created by generator")

        # 4. Return
        # Frontend expects path relative to /api/pdf/ or raw path?
        # serve_pdf route is /api/pdf/<path:filepath>
        # If we return "Mandanten/...", frontend might use it directly.
        # But frontend logic (viewPdf) appends it to API_BASE_URL + '/pdf/'?
        # Let's check frontend. But based on error, it requested /api/pdf/Mandanten...
        # Wait, serve_pdf receives "api/pdf/Mandanten..." as filepath!
        # This means the URL was /api/pdf/api/pdf/Mandanten...
        # So frontend likely converts path to URL incorrectly OR we returned absolute path?
        
        # Current return: /api/pdf/Mandanten/...
        # Browser requests: /api/pdf/api/pdf/Mandanten...
        # This implies frontend does: base + path.
        # IF path already has /api/pdf, and base has /api/pdf?
        
        # Change to return "Mandanten/..." (clean relative path)
        rel_path = f"Mandanten/{mandant_id}/Controlling/Reports/{filename}"
        return jsonify({
            'success': True,
            'path': rel_path,
            'filename': filename
        })

    except Exception as e:
        logger.error(f"Report Gen Error: {e}")
        return jsonify({'error': str(e)}), 500

def filter_by_month(data, year, month):
    filtered = []
    for row in data:
        d_str = row.get('Datum')
        if not d_str: continue
        
        try:
            # Try formats
            dt = None
            for fmt in ['%Y-%m-%d', '%d.%m.%Y']:
                try: 
                    dt = datetime.strptime(str(d_str), fmt)
                    break 
                except: pass
            
            if dt and dt.year == year and dt.month == month:
                filtered.append(row)
        except: pass
    return filtered

# --- BACKUP SYSTEM ---
import threading
import time
from datetime import datetime

# Lazy import to avoid circular issues if any, or just standard import
# import backup  <-- assumed available in same dir

def run_scheduler():
    """Background thread checks time for daily backup"""
    logger.info("⏰ Scheduler gestartet (Backup täglich um 23:00)")
    last_run = None
    
    while True:
        now = datetime.now()
        # Run at 23:00
        if now.hour == 23 and now.minute == 0:
            today = now.strftime('%Y-%m-%d')
            if last_run != today:
                try:
                    logger.info("⏰ Starte automatisches Backup...")
                    import backup
                    backup.create_backup()
                    last_run = today
                except Exception as e:
                    logger.error(f"Auto-Backup failed: {e}")
                    
        time.sleep(30) # Check every 30s

# Start Scheduler
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

@app.route('/api/backup/now', methods=['POST'])
def trigger_backup():
    """Manuelles Backup auslösen"""
    try:
        import backup
        backup_file = backup.create_backup()
        return jsonify({
            'success': True,
            'message': 'Backup erfolgreich erstellt!',
            'filename': str(backup_file.name),
            'size_mb': round(backup_file.stat().st_size / (1024*1024), 2)
        })
    except Exception as e:
        logger.error(f"Backup Fehler: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

import dunning_generator

@app.route('/api/mandanten/<mandant_id>/invoices/generate-reminder', methods=['POST'])
def generate_invoice_reminder(mandant_id):
    """Generiert Mahnung PDF"""
    try:
        data = request.get_json()
        invoice_num = data.get('invoice_num')
        level = int(data.get('level', 1))
        
        if not invoice_num:
            return jsonify({'error': 'Rechnungsnummer erforderlich'}), 400

        mandant_dir = MANDANTEN_DIR / mandant_id
        if not mandant_dir.exists():
            return jsonify({'error': 'Mandant nicht gefunden'}), 404
            
        # 1. Load Invoice Data
        # Try to find in einnahmen.xlsx
        einnahmen_file = mandant_dir / 'Einnahmen' / 'einnahmen.xlsx'
        invoice_data = {}
        
        if einnahmen_file.exists():
            import excel_utils
            invoices = excel_utils.read_data(str(einnahmen_file), 'Einnahmen')
            for inv in invoices:
                curr_num = str(inv.get('Rechnungsnummer', inv.get('nummer', '')))
                if curr_num == invoice_num:
                    invoice_data = {
                        'nummer': curr_num,
                        'datum': inv.get('Datum', inv.get('datum', '')),
                        'kunde': inv.get('Kunde', inv.get('kunde', '')),
                        'betrag': inv.get('Betrag_Brutto', inv.get('betrag_brutto', inv.get('Gesamtbetrag', 0)))
                    }
                    break
        
        if not invoice_data:
             invoice_data = {
                'nummer': invoice_num,
                'datum': datetime.now().strftime("%d.%m.%Y"),
                'kunde': 'Kunde',
                'betrag': 0.00
             }

        # 2. Load Mandant Config
        config_path = mandant_dir / 'mandant_config.json'
        mandant_config = {}
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                mandant_config = json.load(f)

        # 3. Generate PDF
        mahnungen_dir = mandant_dir / 'Mahnungen'
        mahnungen_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = int(datetime.now().timestamp())
        # Sanitize filename
        safe_num = str(invoice_num).replace('/', '_').replace('\\', '_').strip()
        filename = f"Mahnung_{level}_{safe_num}_{timestamp}.pdf"
        output_path = mahnungen_dir / filename
        
        success = dunning_generator.create_dunning_pdf(
            str(mandant_dir), 
            mandant_config, 
            invoice_data, 
            str(output_path), 
            dunning_level=level
        )
        
        if success:
             web_path = f"Mandanten/{mandant_id}/Mahnungen/{filename}"
             return jsonify({'success': True, 'pdf_path': web_path})
        else:
             return jsonify({'error': 'Fehler bei PDF Erstellung'}), 500

    except Exception as e:
        logger.error(f"Dunning Error: {e}")
        return jsonify({'error': str(e)}), 500

# --- EMAIL & DUNNING ---
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

def send_email_with_attachments(to_email, subject, body, attachment_paths, mandant_config):
    """Sende Email mit mehreren Anhängen via SMTP (Mandanten-Config)"""
    smtp_config = mandant_config.get('smtp', {})
    
    smtp_server = smtp_config.get('server')
    smtp_port = int(smtp_config.get('port', 587))
    smtp_user = smtp_config.get('user')
    smtp_pass = smtp_config.get('pass')
    smtp_sender = smtp_config.get('sender') or mandant_config.get('firma', 'Buchhaltung')
    
    if not smtp_server or not smtp_user or not smtp_pass:
        raise Exception("SMTP Config Missing: Bitte in 'Mandant bearbeiten' die Email-Zugangsdaten (SMTP) hinterlegen.")

    sender_email = smtp_user
    msg = MIMEMultipart()
    # Use calibrated sender name if provided
    msg['From'] = f"{smtp_sender} <{sender_email}>"
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    for path in attachment_paths:
        p = Path(path)
        if p.exists():
            with open(p, "rb") as f:
                attach = MIMEApplication(f.read(), _subtype="pdf")
                attach.add_header('Content-Disposition', 'attachment', filename=p.name)
                msg.attach(attach)
        else:
            logger.warning(f"Attachment not found: {path}")

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

@app.route('/api/mandanten/<mandant_id>/invoices/send-reminder', methods=['POST'])
def send_invoice_reminder(mandant_id):
    """Sende Mahnung per E-Mail (Mahnung + Originalrechnung)"""
    try:
        data = request.get_json()
        invoice_num = data.get('invoice_num')
        level = int(data.get('level', 1))
        
        if not invoice_num:
            return jsonify({'error': 'Rechnungsnummer erforderlich'}), 400

        mandant_dir = MANDANTEN_DIR / mandant_id
        if not mandant_dir.exists():
            return jsonify({'error': 'Mandant nicht gefunden'}), 404
            
        # 1. Load Data & Config
        config_path = mandant_dir / 'mandant_config.json'
        mandant_config = {}
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                mandant_config = json.load(f)

        # Load Invoice Data
        einnahmen_file = mandant_dir / 'Einnahmen' / 'einnahmen.xlsx'
        invoice_data = {}
        if einnahmen_file.exists():
            import excel_utils
            invoices = excel_utils.read_data(str(einnahmen_file), 'Einnahmen')
            for inv in invoices:
                curr_num = str(inv.get('Rechnungsnummer', inv.get('nummer', '')))
                if curr_num == invoice_num:
                    invoice_data = {
                        'nummer': curr_num,
                        'datum': inv.get('Datum', inv.get('datum', '')),
                        'kunde': inv.get('Kunde', inv.get('kunde', '')),
                        'betrag': inv.get('Betrag_Brutto', inv.get('betrag_brutto', inv.get('Gesamtbetrag', 0)))
                    }
                    break
        
        if not invoice_data:
             return jsonify({'error': f'Rechnung {invoice_num} nicht gefunden'}), 404

        kunde_name = invoice_data.get('kunde')
        kunde_email = None
        
        # Lookup Email form Customers
        kunden_file = mandant_dir / 'Kunden' / 'kunden.xlsx'
        if kunden_file.exists():
            kunden = excel_utils.read_data(str(kunden_file), 'Kunden')
            for k in kunden:
                if k.get('Firma') == kunde_name:
                    kunde_email = k.get('Email')
                    break
        
        if not kunde_email:
            kunde_email = data.get('email')
        
        if not kunde_email:
             return jsonify({'error': f'Keine E-Mail-Adresse für Kunde "{kunde_name}" gefunden'}), 400

        # 2. Files to Attach
        attachments = []
        
        # A) Mahnung PDF (Re-Generate)
        import dunning_generator
        mahnungen_dir = mandant_dir / 'Mahnungen'
        mahnungen_dir.mkdir(parents=True, exist_ok=True)
        timestamp = int(datetime.now().timestamp())
        safe_num = str(invoice_num).replace('/', '_').replace('\\', '_').strip()
        mahnung_filename = f"Mahnung_{level}_{safe_num}_{timestamp}.pdf"
        mahnung_path = mahnungen_dir / mahnung_filename
        
        success = dunning_generator.create_dunning_pdf(
            str(mandant_dir), 
            mandant_config, 
            invoice_data, 
            str(mahnung_path), 
            dunning_level=level
        )
        if success:
            attachments.append(str(mahnung_path))
            
        # B) Original Invoice PDF
        rechnungen_dir = mandant_dir / 'Rechnungen'
        for f in rechnungen_dir.rglob('*.pdf'):
            if invoice_num in f.name:
                attachments.append(str(f))
                break

        # 3. Send Email
        subject = f"Zahlungserinnerung: Rechnung {invoice_num}"
        betrag_fmt = f"{invoice_data.get('betrag', 0):.2f}".replace('.', ',')
        
        body = f"""Sehr geehrte Damen und Herren,

anbei erhalten Sie unsere Zahlungserinnerung zur Rechnung {invoice_num} über {betrag_fmt} €.
Eine Kopie der ursprünglichen Rechnung liegt ebenfalls bei.

Wir bitten um zeitnahe Überweisung.

Mit freundlichen Grüßen,
{mandant_config.get('firma', 'Buchhaltung')}
"""
        send_email_with_attachments(kunde_email, subject, body, attachments, mandant_config)
        
        return jsonify({'success': True, 'message': f'Mahnung per E-Mail an {kunde_email} versendet!'})

    except Exception as e:
        logger.error(f"Send Reminder Error: {e}")
        return jsonify({'error': str(e)}), 500

import bank_parser

@app.route('/api/mandanten/<mandant_id>/op-check/scan', methods=['POST'])
def scan_bank_statement(mandant_id):
    """Scans uploaded bank statement and finds matching invoices"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        mandant_dir = MANDANTEN_DIR / mandant_id
        if not mandant_dir.exists():
            return jsonify({'error': 'Mandant nicht gefunden'}), 404
            
        # 1. Save File temporarily
        temp_dir = mandant_dir / 'Temp'
        temp_dir.mkdir(parents=True, exist_ok=True)
        filename = f"bank_scan_{int(datetime.now().timestamp())}_{file.filename}"
        filepath = temp_dir / filename
        file.save(filepath)
        
        # 2. Parse File
        transactions = bank_parser.parse_bank_statement(str(filepath))
        
        # 3. Load Open Invoices
        import excel_utils
        einnahmen_path = mandant_dir / 'Einnahmen' / 'einnahmen.xlsx'
        open_invoices = []
        if einnahmen_path.exists():
            invoices = excel_utils.read_data(str(einnahmen_path), 'Einnahmen')
            # Filter Open
            open_invoices = [inv for inv in invoices if str(inv.get('Status','')).lower() != 'bezahlt']
            
        # 4. Find Matches
        matches = bank_parser.find_matches(transactions, open_invoices)
        
        # Cleanup? Keep for debug?
        # filepath.unlink() 
        
        return jsonify({
            'success': True, 
            'matches': matches,
            'count': len(matches),
            'transactions_found': len(transactions)
        })

    except Exception as e:
        logger.error(f"Scan Error: {e}")
        return jsonify({'error': str(e)}), 500

# ===== DELETE DOCUMENT ENDPOINTS =====

def reset_counter_after_delete(mandant_dir, prefix, folder, counter_file_name):
    try:
        counter_file = mandant_dir / counter_file_name
        today = datetime.now()
        current_year = str(today.year)
        current_month = f"{today.month:02d}"
        
        docs_dir = mandant_dir / folder
        max_counter = 0
        
        if docs_dir.exists():
            for f in docs_dir.glob(f"{prefix}-*-{current_year}-{current_month}-*.pdf"):
                parts = f.stem.split('-')
                if len(parts) >= 5:
                    try:
                        c = int(parts[-1])
                        if c > max_counter:
                            max_counter = c
                    except:
                        pass
                        
        data = {
            'year': current_year,
            'month': current_month,
            'counter': max_counter
        }
        with open(counter_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
    except Exception as e:
        logger.error(f"Error resetting counter for {folder}: {e}")

@app.route('/api/mandanten/<mandant_id>/angebote/<path:filename>', methods=['DELETE'])
def delete_angebot(mandant_id, filename):
    try:
        mandant_dir = MANDANTEN_DIR / mandant_id
        angebote_dir = mandant_dir / 'Angebote'
        
        pdf_file = angebote_dir / filename
        json_file = angebote_dir / filename.replace('.pdf', '.json')
        
        if pdf_file.exists():
            pdf_file.unlink()
        if json_file.exists():
            json_file.unlink()
            
        reset_counter_after_delete(mandant_dir, 'ANG', 'Angebote', 'offer_counter.json')
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Angebots: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mandanten/<mandant_id>/lieferscheine/<path:filename>', methods=['DELETE'])
def delete_lieferschein(mandant_id, filename):
    try:
        mandant_dir = MANDANTEN_DIR / mandant_id
        lieferscheine_dir = mandant_dir / 'Lieferscheine'
        
        pdf_file = lieferscheine_dir / filename
        json_file = lieferscheine_dir / filename.replace('.pdf', '.json')
        
        if pdf_file.exists():
            pdf_file.unlink()
        if json_file.exists():
            json_file.unlink()
            
        reset_counter_after_delete(mandant_dir, 'LS', 'Lieferscheine', 'delivery_counter.json')
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Lieferscheins: {e}")
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
