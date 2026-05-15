
import csv
import re
import os
from datetime import datetime

# Optional: Try importing pytesseract for OCR
try:
    import pytesseract
    from PIL import Image
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

def parse_bank_statement(file_path):
    """
    Parses a bank statement file (CSV or Image).
    Returns a list of dicts: {'amount': float, 'usage': str, 'date': str}
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.csv':
        return parse_csv(file_path)
    elif ext in ['.jpg', '.jpeg', '.png']:
        return parse_image(file_path)
    else:
        return []

def parse_csv(file_path):
    transactions = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            # Detect delimiter
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            try:
                dialect = sniffer.sniff(sample)
                delimiter = dialect.delimiter
            except:
                delimiter = ';' # Default fallback for German CSVs

            reader = csv.reader(f, delimiter=delimiter)
            
            # Simple heuristic to find columns
            # We look for "Betrag" (Amount) and "Verwendungszweck" (Usage)
            header_idx = -1
            col_map = {'amount': -1, 'usage': -1, 'date': -1}
            
            rows = list(reader)
            for i, row in enumerate(rows):
                lower_row = [c.lower() for c in row]
                if 'betrag' in lower_row or 'amount' in lower_row:
                    header_idx = i
                    # Map columns
                    for j, col in enumerate(lower_row):
                        if 'betrag' in col or 'amount' in col: col_map['amount'] = j
                        if 'verwendungszweck' in col or 'usage' in col or 'text' in col: col_map['usage'] = j
                        if 'datum' in col or 'date' in col: col_map['date'] = j
                    break
            
            if header_idx != -1 and col_map['amount'] != -1:
                for i in range(header_idx + 1, len(rows)):
                    row = rows[i]
                    if len(row) <= max(col_map.values()): continue
                    
                    try:
                        amount_str = row[col_map['amount']].replace('.', '').replace(',', '.') # German format
                        amount = float(amount_str)
                        
                        usage = ""
                        if col_map['usage'] != -1: usage = row[col_map['usage']]
                        
                        date_str = ""
                        if col_map['date'] != -1: date_str = row[col_map['date']]
                        
                        transactions.append({
                            'amount': amount,
                            'usage': usage,
                            'date': date_str
                        })
                    except:
                        continue
    except Exception as e:
        print(f"CSV Parse Error: {e}")
        
    return transactions

def parse_image(file_path):
    if not HAS_OCR:
        print("OCR not available (pytesseract/PIL missing)")
        return []
        
    transactions = []
    try:
        # Simple OCR
        # We assume Tesseract is installed on system PATH
        # text = pytesseract.image_to_string(Image.open(file_path))
        
        # NOTE: This implementation requires Tesseract binary installed
        # and pytesseract + Pillow packages.
        # We will stub this for now or implement if dependencies exist.
        pass
    except Exception as e:
        print(f"OCR Error: {e}")
        
    return transactions

def find_matches(transactions, open_invoices):
    """
    Matches parsed transactions against open invoices.
    open_invoices: list of dicts (from einnahmen.xlsx)
    Returns: list of matches [{'invoice_id': ..., 'transaction': ...}]
    """
    matches = []
    
    for inv in open_invoices:
        inv_id = str(inv.get('Rechnungsnummer', ''))
        inv_amount = float(inv.get('Betrag_Brutto', 0) or 0)
        
        if not inv_id: continue
        
        # Search in transactions
        for trans in transactions:
            # Match Logic:
            # 1. Invoice ID in Usage Text (High Confidence)
            # 2. Exact Amount Match (Medium/High Confidence depending on uniqueness)
            
            # Normalize usage text
            usage_norm = str(trans.get('usage', '')).replace(' ', '').lower()
            inv_id_norm = inv_id.lower().replace(' ', '')
            
            # Check ID Match
            id_match = False
            if len(inv_id_norm) > 3: # Avoid matching short numbers accidentally
                if inv_id_norm in usage_norm:
                    id_match = True
                elif inv_id_norm.replace('re-', '') in usage_norm: # e.g. "2026-005" in text
                    id_match = True
                    
            # Check Amount Match (Tolerance 0.05 for rounding diffs)
            amount_diff = abs(trans['amount'] - inv_amount)
            amount_match = amount_diff < 0.05
            
            if id_match:
                matches.append({
                    'invoice_id': inv_id,
                    'matched_via': 'Invoice ID',
                    'confidence': 'High'
                })
            elif amount_match:
                # If amount matches but ID doesn't
                # This is what the user requested: "The amount fits... that could be the invoice"
                matches.append({
                    'invoice_id': inv_id,
                    'matched_via': 'Amount',
                    'confidence': 'Medium'
                })
    
    return matches
