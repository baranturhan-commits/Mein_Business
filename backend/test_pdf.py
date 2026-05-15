import json
import os
from invoice_generator import create_pdf
from offer_generator import create_offer_pdf

mandant_dir = "Mandanten/Max_Kleingewerbe_Test_2"

# Ensure Mandant exists
if not os.path.exists(mandant_dir):
    print("Mandant directory not found.")
    exit(1)

with open(f"{mandant_dir}/mandant_config.json", "r", encoding="utf-8") as f:
    mandant_config = json.load(f)

# 1. Test Invoice
invoice_data = {
    "nummer": "RE-123",
    "datum": "01.01.2024",
    "faellig_am": "15.01.2024",
    "items": [
        {"menge": 10, "beschreibung": "Test Item", "preis": 50.0}
    ]
}

kunde_data = {
    "firma": "Test Kunde GmbH",
    "adresse": {"strasse": "Teststr. 1", "ort": "12345 Teststadt"}
}

try:
    pdf_path = create_pdf(invoice_data, mandant_config, kunde_data, mandant_dir)
    print(f"Invoice generated correctly at {pdf_path}")
except Exception as e:
    print(f"Invoice generation failed: {e}")

# 2. Test Offer
offer_data = {
    "counter": 1,
    "datum": "01.01.2024",
    "kunde": {
        "firma": "Test Kunde GmbH",
        "adresse": "Teststr. 1",
        "ort": "12345 Teststadt"
    },
    "betreff": "Test Angebot",
    "items": [
        {"menge": 10, "beschreibung": "Test Item", "preis": 50.0}
    ]
}

try:
    offer_path, offer_filename = create_offer_pdf(offer_data, mandant_config, mandant_dir)
    print(f"Offer generated correctly at {offer_path}")
except Exception as e:
     print(f"Offer generation failed: {e}")
