
import os
import json
import datetime
from dateutil.relativedelta import relativedelta
from pathlib import Path
from logger import get_logger

logger = get_logger(__name__)

def get_recurring_file(mandant_dir):
    return Path(mandant_dir) / 'recurring.json'

def load_recurring(mandant_dir):
    """Lädt alle Abo-Einträge"""
    file_path = get_recurring_file(mandant_dir)
    if not file_path.exists():
        return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Fehler beim Laden der Abos: {e}")
        return []

def save_recurring(mandant_dir, data):
    """Speichert Abo-Einträge"""
    file_path = get_recurring_file(mandant_dir)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def add_recurring(mandant_dir, data):
    """Fügt ein neues Abo hinzu"""
    entries = load_recurring(mandant_dir)
    
    # ID generieren
    import uuid
    new_entry = {
        'id': str(uuid.uuid4())[:8],
        'kunde': data.get('kunde'),
        'beschreibung': data.get('beschreibung'),
        'betrag': float(data.get('betrag', 0)),
        'intervall': data.get('intervall', 'monatlich'), # monatlich, quartalsweise, jaehrlich
        'start_datum': data.get('start_datum'),
        'naechste_faelligkeit': data.get('start_datum'), # Erstes Mal am Startdatum
        'aktiv': True,
        'created_at': datetime.datetime.now().isoformat()
    }
    
    entries.append(new_entry)
    save_recurring(mandant_dir, entries)
    return new_entry

def delete_recurring(mandant_dir, entry_id):
    """Löscht ein Abo"""
    entries = load_recurring(mandant_dir)
    entries = [e for e in entries if e['id'] != entry_id]
    save_recurring(mandant_dir, entries)

def process_due_invoices(mandant_dir, mandant_config):
    """
    Prüft fällige Abos und erstellt Rechnungen.
    Gibt Liste der erstellten Rechnungen zurück.
    """
    entries = load_recurring(mandant_dir)
    today = datetime.date.today()
    created_invoices = []
    
    updated = False
    
    # Import hier um zirkuläre Imports zu vermeiden
    import invoice_generator
    import excel_utils
    
    # Counter laden
    counter_func = getattr(invoice_generator, 'get_and_increment_counter')
    create_pdf_func = getattr(invoice_generator, 'create_pdf')
    load_kunden_func = getattr(invoice_generator, 'load_kunden')
    
    # Kunden laden für Address-Daten
    kunden_liste = load_kunden_func(str(mandant_dir))
    
    for entry in entries:
        if not entry.get('aktiv', True):
            continue
            
        due_date_str = entry.get('naechste_faelligkeit')
        if not due_date_str: continue
        
        try:
            due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
        except:
            continue
            
        if due_date <= today:
            # FÄLLIG! Rechnung erstellen
            logger.info(f"Abo fällig: {entry['kunde']} - {entry['beschreibung']}")
            
            # Kunde finden
            kunde_data = next((k for k in kunden_liste if k['firma'] == entry['kunde']), None)
            if not kunde_data:
                logger.error(f"Kunde nicht gefunden für Abo: {entry['kunde']}")
                continue
                
            # Rechnungsdaten
            inv_nr = counter_func(str(mandant_dir))
            
            # Items vorbereiten
            items = [{
                'beschreibung': f"{entry['beschreibung']} (Zeitraum: {due_date.strftime('%m/%Y')})",
                'betrag': float(entry['betrag'])
            }]
            
            invoice_data = {
                'nummer': inv_nr,
                'datum': today.strftime("%d.%m.%Y"),
                'items': items
            }
            
            # PDF Erstellen
            pdf = create_pdf_func(invoice_data, str(mandant_dir), mandant_config, kunde_data)
            
            if pdf:
                created_invoices.append(pdf)
                
                # Nächstes Datum berechnen
                intervall = entry.get('intervall', 'monatlich')
                if intervall == 'monatlich':
                    next_date = due_date + relativedelta(months=1)
                elif intervall == 'quartalsweise':
                    next_date = due_date + relativedelta(months=3)
                elif intervall == 'jaehrlich':
                    next_date = due_date + relativedelta(years=1)
                else:
                    next_date = due_date + relativedelta(months=1)
                
                entry['naechste_faelligkeit'] = next_date.strftime("%Y-%m-%d")
                entry['letzte_ausfuehrung'] = today.strftime("%Y-%m-%d")
                updated = True
                
    if updated:
        save_recurring(mandant_dir, entries)
        
    return created_invoices
