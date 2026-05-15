
import bank_parser
import os

# Create dummy CSV
csv_content = """Datum;Verwendungszweck;Betrag;Währung
01.02.2026;Miete Büro Februar; 800,00;EUR
02.02.2026;Zahlung Rechnung RE-2026-005 Kunde X; 1500,00;EUR
03.02.2026;Tankstelle Aral; -65,50;EUR
04.02.2026;Gutschrift 2026-001; 250,00;EUR
"""

filename = "test_bank_stmt.csv"
with open(filename, 'w', encoding='utf-8') as f:
    f.write(csv_content)

print(f"--- Parsing {filename} ---")
transactions = bank_parser.parse_bank_statement(filename)
for t in transactions:
    print(t)

print("\n--- Testing Matching ---")
open_invoices = [
    {'Rechnungsnummer': 'RE-2026-005', 'Betrag_Brutto': 1500.00},
    {'Rechnungsnummer': '2026-001', 'Betrag_Brutto': 250.00},
    {'Rechnungsnummer': 'RE-2026-999', 'Betrag_Brutto': 100.00}, # Not in CSV
    {'Rechnungsnummer': 'RE-AMOUNT-ONLY', 'Betrag_Brutto': 800.00} # Miete 800
]

matches = bank_parser.find_matches(transactions, open_invoices)
print(f"Matches Found: {len(matches)}")
for m in matches:
    print(m)

# Cleanup
if os.path.exists(filename): os.remove(filename)
