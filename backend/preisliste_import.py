"""
Intelligenter Preislisten-Import
Unterstützt: Excel, CSV, PDF, Bilder (mit AI-OCR)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

def parse_excel(file_path):
    """Liest Excel-Datei"""
    import openpyxl
    
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active
    
    positionen = []
    
    # Skip header row
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0]:  # Skip empty rows
            continue
        
        positionen.append({
            'bezeichnung': str(row[0]) if row[0] else '',
            'einheit': str(row[1]) if len(row) > 1 and row[1] else 'Stk',
            'einzelpreis': float(row[2]) if len(row) > 2 and row[2] else 0,
            'kategorie': str(row[3]) if len(row) > 3 and row[3] else 'Sonstiges'
        })
    
    return positionen

def parse_csv(file_path):
    """Liest CSV-Datei"""
    import csv
    
    positionen = []
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')  # Try semicolon first
        
        # If no proper headers, try comma
        if not reader.fieldnames or len(reader.fieldnames) < 2:
            f.seek(0)
            reader = csv.DictReader(f, delimiter=',')
        
        for row in reader:
            # Try to find columns (flexible)
            bezeichnung = (row.get('Bezeichnung') or row.get('Name') or 
                          row.get('Artikel') or row.get('bezeichnung') or 
                          list(row.values())[0])
            
            einheit = (row.get('Einheit') or row.get('einheit') or 
                      row.get('Unit') or 'Stk')
            
            preis_str = (row.get('Preis') or row.get('preis') or 
                        row.get('Einzelpreis') or row.get('Price') or '0')
            
            try:
                einzelpreis = float(str(preis_str).replace(',', '.').replace('€', '').strip())
            except:
                einzelpreis = 0
            
            kategorie = (row.get('Kategorie') or row.get('kategorie') or 
                        row.get('Category') or 'Sonstiges')
            
            if bezeichnung:
                positionen.append({
                    'bezeichnung': str(bezeichnung).strip(),
                    'einheit': str(einheit).strip(),
                    'einzelpreis': einzelpreis,
                    'kategorie': str(kategorie).strip()
                })
    
    return positionen

def parse_with_ai(file_path):
    """Verwendet Gemini AI für OCR auf Bildern/PDFs"""
    print(f"🤖 Starte AI-Analyse für: {file_path}")
    try:
        # Verwende ein Modell das sicher verfügbar ist (gemini-flash-latest)
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # Upload file to Gemini
        print("📤 Lade Datei zu Gemini hoch...")
        uploaded_file = genai.upload_file(file_path)
        print(f"✅ Upload fertig: {uploaded_file.name}")
        
        prompt = """
Analysiere diese Preisliste und extrahiere ALLE Positionen.

Für jede Position brauche ich:
- Bezeichnung (Produktname)
- Einheit (z.B. Stk, Std, m, kg)
- Einzelpreis (nur Zahl, in Euro)
- Kategorie (z.B. Material, Dienstleistung)

Gib das Ergebnis als JSON zurück, Format:
[
  {
    "bezeichnung": "Produktname",
    "einheit": "Stk",
    "einzelpreis": 12.50,
    "kategorie": "Material"
  }
]

WICHTIG: 
- Nur JSON zurückgeben, keinen anderen Text
- Preise als Zahlen (float), nicht als String
- Falls Einheit nicht klar ist, nutze "Stk"
- Falls Kategorie nicht erkennbar, nutze "Sonstiges"
"""
        
        print("🤔 Generiere Antwort...")
        response = model.generate_content([uploaded_file, prompt])
        print("✅ Antwort erhalten")
        
        # Parse JSON from response
        import json
        import re
        
        # Extract JSON from response (might have markdown fences)
        text = response.text
        print(f"📄 Raw Response: {text[:100]}...") # Log first 100 chars
        
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(0)
            positionen = json.loads(json_str)
            print(f"✅ {len(positionen)} Positionen extrahiert")
            return positionen
        else:
            print("❌ Kein JSON in Antwort gefunden")
            raise ValueError("Konnte keine Daten aus dem Bild extrahieren. Antwort war kein JSON.")

    except Exception as e:
        print(f"❌ AI Error: {str(e)}")
        raise e

def import_preisliste(file_path):
    """
    Hauptfunktion: Automatische Format-Erkennung
    """
    file_ext = Path(file_path).suffix.lower()
    
    print(f"📄 Importiere: {Path(file_path).name}")
    print(f"Format: {file_ext}")
    
    try:
        if file_ext in ['.xlsx', '.xls']:
            print("→ Excel-Modus")
            return parse_excel(file_path)
        
        elif file_ext == '.csv':
            print("→ CSV-Modus")
            return parse_csv(file_path)
        
        elif file_ext in ['.pdf', '.jpg', '.jpeg', '.png', '.webp']:
            print("→ AI-OCR-Modus (Gemini)")
            return parse_with_ai(file_path)
        
        else:
            # Fallback: Try AI for unknown types if it might be an image
            print(f"⚠️ Unbekanntes Format '{file_ext}', versuche AI-Mode...")
            return parse_with_ai(file_path)
    
    except Exception as e:
        print(f"❌ Fehler beim Import: {e}")
        raise

if __name__ == '__main__':
    # Test
    if len(sys.argv) < 2:
        print("Usage: python preisliste_import.py <file>")
        sys.exit(1)
    
    file = sys.argv[1]
    positionen = import_preisliste(file)
    
    print(f"\n✅ {len(positionen)} Positionen gefunden:")
    for p in positionen[:5]:  # Show first 5
        print(f"  - {p['bezeichnung']}: {p['einzelpreis']}€/{p['einheit']}")
