
import sys
import os
import json
from pathlib import Path

# Setup
sys.path.append(os.path.abspath("backend"))
import delivery_generator

MANDANT_ID = "Elektroniker_Testbetrieb"
MANDANTEN_DIR = Path(r"c:\Users\Admin\Desktop\Mein_Business\backend\Mandanten")
MANDANT_PATH = MANDANTEN_DIR / MANDANT_ID
LIEFERSCHEINE_DIR = MANDANT_PATH / 'Lieferscheine'

# Target
nummer = "PROT-2026-001"
# Match the latest timestamp file
pdf_filename = "Lieferschein_PROT-2026-001_1767560752.pdf"
output_path = LIEFERSCHEINE_DIR / pdf_filename

print(f"🔄 Regenerating {output_path}...")

# Load Offer items if possible
items = []
target_offer = "Angebot_ANG-2026-001.json" # Guessing filename format
offer_path = MANDANT_PATH / 'Angebote' / target_offer

if not offer_path.exists():
    # Try just ID
    offer_path = MANDANT_PATH / 'Angebote' / "ANG-2026-001.json"

if offer_path.exists():
    print(f"📄 Loading offer from {offer_path}")
    with open(offer_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        items = data.get('positionen', [])
else:
    print("⚠️ Offer not found, using dummy items.")
    items = [{'text': 'Regenerated Item 1', 'menge': 1}]

# Config
config = {'firma': 'Elektroniker Testbetrieb', 'logo': ''}
# Load real config if exists
config_path = MANDANT_PATH / 'mandant_config.json'
if config_path.exists():
     with open(config_path, 'r', encoding='utf-8') as f:
         config = json.load(f)

# Generate
success = delivery_generator.create_delivery_pdf(
    mandant_path=str(MANDANT_PATH),
    mandant_config=config,
    kunde_name="Oma_Erna",
    positionen=items,
    output_path=str(output_path),
    nummer=nummer,
    angebot_nr="ANG-2026-001"
)

if success:
    print("✅ Regeneration successful.")
else:
    print("❌ Regeneration failed.")
