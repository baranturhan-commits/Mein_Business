
import pandas as pd
import json
import os

base_dir = r'C:\Users\Admin\Desktop\Mein_Business\backend\Mandanten\Elektroniker_Testbetrieb\Angebote'
counter_path = r'C:\Users\Admin\Desktop\Mein_Business\backend\Mandanten\Elektroniker_Testbetrieb\offer_counter.json'
excel_path = os.path.join(base_dir, 'angebote.xlsx')

# Files to move
current_pdf = 'ANG-001-2026-001.pdf'
current_json = 'Angebot_ANG-001-2026-001.json'

new_pdf = 'ANG-001-2026-005.pdf'
new_json = 'Angebot_ANG-001-2026-005.json'
new_id = 'ANG-001-2026-005'

# 1. Rename PDF
if os.path.exists(os.path.join(base_dir, current_pdf)):
    os.rename(os.path.join(base_dir, current_pdf), os.path.join(base_dir, new_pdf))
    print(f"Renamed PDF to {new_pdf}")

# 2. Rename JSON and Update Content
if os.path.exists(os.path.join(base_dir, current_json)):
    # Read
    with open(os.path.join(base_dir, current_json), 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Update
    data['nummer'] = new_id
    
    # Write to new name
    with open(os.path.join(base_dir, new_json), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    
    # Remove old
    os.remove(os.path.join(base_dir, current_json))
    print(f"Renamed JSON to {new_json} and updated ID")

# 3. Update Excel
try:
    df = pd.read_excel(excel_path, sheet_name='Angebote')
    
    # Find the row with the OLD ID 'ANG-001-2026-001' (which I know is the new offer because of previous check)
    # Actually, verify by checking if PDF_Path was the one I just set 'ANG-001-2026-001.pdf'
    mask = df['PDF_Path'] == 'ANG-001-2026-001.pdf'
    
    if mask.any():
        df.loc[mask, 'Nummer'] = new_id
        df.loc[mask, 'PDF_Path'] = new_pdf
        df.to_excel(excel_path, sheet_name='Angebote', index=False)
        print("Updated Excel.")
    else:
        print("Warning: Could not find Excel row to update.")

except Exception as e:
    print(f"Excel Error: {e}")

# 4. Update Counter
try:
    with open(counter_path, 'r') as f:
        cdata = json.load(f)
    cdata['counter'] = 5
    with open(counter_path, 'w') as f:
        json.dump(cdata, f, indent=4)
    print("Updated Counter to 5.")
except Exception as e:
    print(f"Counter Error: {e}")
