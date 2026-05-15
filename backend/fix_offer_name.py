
import pandas as pd
import os
import shutil

base_dir = r'C:\Users\Admin\Desktop\Mein_Business\backend\Mandanten\Elektroniker_Testbetrieb\Angebote'
excel_path = os.path.join(base_dir, 'angebote.xlsx')

# Target
old_pdf_name = 'Angebot_ANG-001-2026-001_1769951938.pdf'
new_pdf_name = 'ANG-001-2026-001.pdf'

old_path = os.path.join(base_dir, old_pdf_name)
new_path = os.path.join(base_dir, new_pdf_name)

print(f"Renaming {old_pdf_name} -> {new_pdf_name}")

# 1. Rename File
if os.path.exists(old_path):
    # If new path exists (the small dummy), remove it first
    if os.path.exists(new_path):
        print("Target exists, overwriting...")
        os.remove(new_path)
    
    os.rename(old_path, new_path)
    print("File renamed successfully.")
else:
    print("Old file not found! Checking if already renamed...")
    if os.path.exists(new_path):
        print("File already seems to be named correctly.")
    else:
        print("Error: Neither old nor new file found.")
        exit(1)

# 2. Update Excel
try:
    df = pd.read_excel(excel_path, sheet_name='Angebote')
    
    # Update matching rows
    mask = df['PDF_Path'] == old_pdf_name
    if mask.any():
        df.loc[mask, 'PDF_Path'] = new_pdf_name
        df.to_excel(excel_path, sheet_name='Angebote', index=False)
        print("Excel updated successfully.")
    else:
        print("Warning: No matching entry in Excel found to update.")
        # Check if already updated
        if (df['PDF_Path'] == new_pdf_name).any():
            print("Excel entry already has new name.")
        
except Exception as e:
    print(f"Error updating Excel: {e}")
