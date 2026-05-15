
import delivery_generator
import os

# Dummy config
config = {'firma': 'Test Firma GmbH', 'logo': None}

# Test Positions
positions = [
    {'menge': 5, 'einheit': 'Stk', 'bezeichnung': 'Fensterreinigung'},
    {'menge': 10, 'einheit': 'm²', 'bezeichnung': 'Bodenbelag entfernen'}
]

# Output file
output_file = 'test_protocol_filled.pdf'

print("Generating Test Protocol...")
try:
    delivery_generator.create_delivery_pdf(
        mandant_path='.', 
        mandant_config=config, 
        kunde_name='Test Kunde', 
        positionen=positions, 
        output_path=output_file, 
        nummer='LS-TEST-001'
    )
    print(f"✅ Success! Generated {output_file}")
    
    # Check if we can verify the file exists
    if os.path.exists(output_file):
        print("File exists on disk.")
    else:
        print("❌ File not found on disk.")
        
except Exception as e:
    print(f"❌ Error: {e}")
