
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import excel_utils

file_path = r"C:\Users\Admin\Desktop\Mein_Business\backend\Mandanten\Elektroniker_Testbetrieb\Einnahmen\einnahmen.xlsx"

print(f"Reading: {file_path}")
try:
    data = excel_utils.read_data(file_path, 'Einnahmen')
    print(f"Rows found: {len(data)}")
    for row in data:
        print(row)
except Exception as e:
    print(f"Error: {e}")
