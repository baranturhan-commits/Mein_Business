
import pandas as pd
import os

path = r'C:\Users\Admin\Desktop\Mein_Business\backend\Mandanten\Elektroniker_Testbetrieb\Angebote\angebote.xlsx'

if os.path.exists(path):
    try:
        df = pd.read_excel(path, sheet_name='Angebote')
        print(df.tail().to_string())
    except Exception as e:
        print(f"Error: {e}")
else:
    print("File not found")
