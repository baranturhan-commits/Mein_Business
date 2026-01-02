
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

def analyze_protocol(file_path, mandant_path=None, offer_items=None):
    """
    Uses Gemini to extract handwritten table data from Abnahmeprotokoll.
    Returns: List of dicts [{'bezeichnung': '...', 'menge': 1, 'einzelpreis': 0}]
    """
    if not api_key:
        raise Exception("Google API Key missing in .env")

    model = genai.GenerativeModel('gemini-2.0-flash-exp')

    # Upload file
    sample_file = genai.upload_file(path=file_path, display_name="Protocol")
    
    prompt = """
    Analyze this handwritten Acceptance Protocol (Abnahmeprotokoll).
    Extract the table rows containing "Gewerk", "Beschreibung", "ok", "nok", "Bemerkung".
    
    CRITICAL INSTRUCTION:
    - IGNORE rows that are empty or only contain a line number (like "1", "2", etc.).
    - IGNORE the pre-printed template lines 1-15 unless they have actual handwritten or typed content in the "Beschreibung" column.
    - If a row has no description, skip it.
    
    Return ONLY a valid JSON array like this:
    [
        {
            "bezeichnung": "Gewerk X: Beschreibung text...",
            "menge": 1, 
            "einheit": "Stk",
            "einzelpreis": 0.00
        }
    ]
    Include the status (ok/nok) in the description if relevant.
    If a quantity is visible, use it. If not, default to 1.
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
                
                # 1. Build Lookup Map from Offer (High Priority)
                offer_map = {}
                if offer_items:
                    for item in offer_items:
                        name = item.get('bezeichnung', '').lower().strip()
                        if name:
                            try: p = float(item.get('einzelpreis', 0))
                            except: p = 0.0
                            offer_map[name] = {'price': p, 'unit': item.get('einheit', 'Stk')}

                # 2. Build Lookup Map from Price List (Fallback)
                plist_map = {}
                pl_path = Path(mandant_path) / 'preisliste.xlsx'
                if pl_path.exists():
                    pl_data = excel_utils.read_data(str(pl_path), "Preisliste")
                    for row in pl_data:
                        bez = row.get('Bezeichnung', '').lower().strip()
                        if bez:
                            try: p = float(str(row.get('Einzelpreis', 0)).replace(',', '.'))
                            except: p = 0.0
                            plist_map[bez] = {'price': p, 'unit': row.get('Einheit', 'Stk')}
                            
                # Helper to match
                def find_match(query, source_map):
                    # Direct match
                    if query in source_map:
                        return source_map[query]
                    # Fuzzy match keys
                    keys = list(source_map.keys())
                    matches = get_close_matches(query, keys, n=1, cutoff=0.6)
                    if matches:
                        return source_map[matches[0]]
                    # Substring match (source in query) - e.g. "Steckdose" in "Montage Steckdose"
                    for k in keys:
                        if k in query:
                            return source_map[k]
                    return None

                # 3. Apply Matching
                for item in data:
                    scanned_name = item.get('bezeichnung', '').lower().strip()
                    matched_info = None
                    
                    # Try Offer First
                    if offer_map:
                        matched_info = find_match(scanned_name, offer_map)
                    
                    # Try Price List Second
                    if not matched_info and plist_map:
                        matched_info = find_match(scanned_name, plist_map)
                        
                    if matched_info:
                        item['einzelpreis'] = matched_info['price']
                        # Only overwrite unit if generic
                        if not item.get('einheit') or item.get('einheit') in ['Psch', 'Pauschale', 'Stk']:
                            item['einheit'] = matched_info['unit']
                                
            except Exception as e:
                print(f"Price Matching Error: {e}")
                
        # Fallback: If scan is empty but we have offer items, return offer items
        if not data and offer_items:
            combined = []
            for oi in offer_items:
                # Map offer item structure to invoice item structure
                combined.append({
                    'bezeichnung': oi.get('titel', oi.get('bezeichnung', '')),
                    'menge': oi.get('menge', 1),
                    'einheit': oi.get('einheit', 'Stk'),
                    'einzelpreis': oi.get('preis', oi.get('einzelpreis', 0))
                })
            return combined

        return data
    except Exception as e:
        print(f"Gemini Parse Error: {e}")
        try:
             print(f"Raw Response: {response.text}")
        except: pass
        return []
