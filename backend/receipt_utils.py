import os
import google.generativeai as genai
from pathlib import Path
import json
from datetime import datetime
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API Key
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def analyze_receipt(image_path):
    """
    Analyzes a receipt image using Gemini Flash to extract:
    - Date, Total Amount, Tax, Shop Name, Category
    """
    if not api_key:
        logger.error("No Google API Key found")
        return None

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        myfile = genai.upload_file(image_path)
        
        prompt = """
        Extrahiere Daten aus diesem Beleg für die Buchhaltung.
        Antworte NUR mit reinem JSON (kein Markdown).
        
        Format:
        {
            "datum": "DD.MM.YYYY",
            "betrag": 0.00,  // Gesamtbetrag (float)
            "mwst": 0.00,    // Enthaltene MwSt (float)
            "firma": "Name des Ladens",
            "kategorie": "Tanken | Material | Essen | Sonstiges",
            "beschreibung": "Kurze Beschreibung des Inhalts"
        }
        
        Falls das Datum fehlt, nimm das heutige Datum.
        Falls Kategorie unklar, wähle die passendste aus der Liste.
        """
        
        result = model.generate_content([prompt, myfile])
        text = result.text.strip()
        
        # Cleanup Markdown
        if text.startswith('```json'):
            text = text.replace('```json', '').replace('```', '')
        
        data = json.loads(text)
        return data

    except Exception as e:
        logger.error(f"Receipt Analysis Error: {e}")
        return None
