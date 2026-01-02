
import os
import json
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def analyze_protocol(file_path, mandant_path=None):
    """
    Uses Gemini to extract handwritten table data from Abnahmeprotokoll.
    Returns: List of dicts [{'bezeichnung': '...', 'menge': 1, 'einzelpreis': 0}]
    """
    if not api_key:
        raise Exception("Google API Key missing in .env")

    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    # Upload file
    sample_file = genai.upload_file(path=file_path, display_name="Protocol")
    
    prompt = """
    Analyze this handwritten Acceptance Protocol (Abnahmeprotokoll).
    Extract the table rows containing "Gewerk", "Beschreibung", "ok", "nok", "Bemerkung".
    
    Ignore rows that are completely empty.
    For each row found, create a billable item.
    Since prices are not on the protocol, set them to 0.00 for now.
    
    Return ONLY a valid JSON array like this:
    [
        {
            "bezeichnung": "Gewerk X: Beschreibung text...",
            "menge": 1,
            "einheit": "Psch",
            "einzelpreis": 0.00
        }
    ]
    Include the status (ok/nok) in the description if relevant.
    """
    
    response = model.generate_content([sample_file, prompt])
    
    # Parse JSON from response
    try:
        text = response.text
        # Cleanup markdown code blocks if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
            
        data = json.loads(text)
        
        # --- Price Matching Logic ---
        if mandant_path:
            try:
                import excel_utils
                from difflib import get_close_matches
                
                pl_path = Path(mandant_path) / 'Preislisten' / 'preisliste.xlsx'
                if pl_path.exists():
                    # Read Price List: [{'Pos': '1', 'Bezeichnung': '...', 'Einzelpreis': 100, ...}]
                    pl_data = excel_utils.read_data(str(pl_path), "Preisliste")
                    
                    # Create lookup helper
                    # Normalize keys to lower case for easier matching
                    price_map = {} # 'bezeichnung_lower' -> {'price': float, 'unit': str}
                    for row in pl_data:
                        bez = row.get('Bezeichnung', '').lower().strip()
                        if bez:
                            try:
                                p = float(str(row.get('Einzelpreis', 0)).replace(',', '.'))
                            except: p = 0.0
                            u = row.get('Einheit', 'Stk')
                            price_map[bez] = {'price': p, 'unit': u}
                            
                    # Match extracted items
                    known_names = list(price_map.keys())
                    
                    for item in data:
                        # Item from AI: {'bezeichnung': '...', ...}
                        scanned_name = item.get('bezeichnung', '').lower().strip()
                        
                        # 1. Exact match (substring check often useful for "Montage X")
                        match = None
                        
                        # Check if any known price list item is contained in scanned text
                        # e.g. Scanned: "Montage von Steckdose" -> Known: "Steckdose" ? Maybe risky.
                        # Better: Check if Scanned text is close to a Known Item.
                        
                        matches = get_close_matches(scanned_name, known_names, n=1, cutoff=0.6)
                        if matches:
                            match = matches[0]
                        else:
                            # Try reverse: is a known item contained in the scanned text?
                            # e.g. Scanned: "1x Anfahrt 50km" -> Known: "Anfahrt"
                            for key in known_names:
                                if key in scanned_name:
                                    match = key
                                    break
                                    
                        if match:
                            info = price_map[match]
                            item['einzelpreis'] = info['price']
                            if not item.get('einheit') or item.get('einheit') == 'Psch':
                                item['einheit'] = info['unit']
                                
            except Exception as e:
                print(f"Price Matching Error: {e}")
                
        return data
    except Exception as e:
        print(f"Gemini Parse Error: {e}")
        print(f"Raw Response: {response.text}")
        return []
