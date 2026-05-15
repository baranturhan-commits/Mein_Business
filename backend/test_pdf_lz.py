import json
import os
from pathlib import Path
from invoice_generator import create_pdf
from offer_generator import create_offer_pdf

mandant_dir = Path("C:/Users/Admin/Desktop/Mein_Business/backend/Mandanten/Max_Kleingewerbe_Test")

if not mandant_dir.exists():
    mandant_dir.mkdir(parents=True, exist_ok=True)
    (mandant_dir / "Angebote").mkdir(exist_ok=True)
    (mandant_dir / "Rechnungen").mkdir(exist_ok=True)

mandant_config = {
    "firma": "Max Kleingewerbe Test",
    "adresse": {"strasse": "Musterstr. 1", "ort": "12345 Musterstadt"},
    "geschaeftsfuehrer": "Max Mustermann"
}

print("Starting Offer Generation...")

try:
    positionen = [{"bezeichnung": "Test Offer Pos", "menge": 1, "einzelpreis": 250.0}]
    brutto, netto = create_offer_pdf(
        str(mandant_dir),
        mandant_config,
        "Test Kunde",
        positionen,
        str(mandant_dir / "Angebote" / "ANG-TEST.pdf"),
        "ANG-TEST",
        leistungs_von="01.03.2026",
        leistungs_bis="31.03.2026"
    )
    print("Offer generated correctly.")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Offer generation failed: {e}")

print("Starting Invoice Generation...")

invoice_data = {
    "nummer": "RE-TEST",
    "datum": "20.04.2026",
    "leistungs_von": "01.04.2026",
    "leistungs_bis": "15.04.2026",
    "items": [
        {"beschreibung": "Test Invoice Pos", "menge": 10, "einzelpreis": 50.0, "einheit": "h"}
    ]
}

kunde_data = {
    "firma": "Test Kunde GmbH",
    "adresse": "Teststr. 1, 12345 Teststadt",
    "anrede": "Herr Test"
}

try:
    pdf_path = create_pdf(invoice_data, str(mandant_dir), mandant_config, kunde_data)
    print(f"Invoice generated correctly at {pdf_path}")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Invoice generation failed: {e}")
