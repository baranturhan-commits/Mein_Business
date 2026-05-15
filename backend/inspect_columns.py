
import pandas as pd
import os

path = r'C:\Users\Admin\Desktop\Mein_Business\backend\Mandanten\Elektroniker_Testbetrieb\Lieferscheine\lieferscheine.xlsx'

if os.path.exists(path):
    try:
        df = pd.read_excel(path, sheet_name='Lieferscheine')
        print(f"Columns: {list(df.columns)}")
        print(df.head().to_string())
    except Exception as e:
        print(f"Error: {e}")
else:
    print("File not found")
