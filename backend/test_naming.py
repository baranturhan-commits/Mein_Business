
import os
import json
import offer_generator
import delivery_generator
import invoice_generator

# Dummy config
mandant_config = {'mandantennummer': '999', 'firma': 'Test'}
mandant_path = '.'

# Offer
print("Testing Offer Generator:")
try:
    path = os.path.join(mandant_path, "offer_counter.json")
    if os.path.exists(path): os.remove(path)
    
    id1 = offer_generator.get_and_increment_offer_counter(mandant_path, mandant_config)
    print(f"ID 1: {id1}")
    if "-02-001" not in id1:
        print("❌ Month missing or wrong")
    else:
        print("✅ Correct Month Format")

    id2 = offer_generator.get_and_increment_offer_counter(mandant_path, mandant_config)
    print(f"ID 2: {id2}")
    
    # Simulate Month Change
    with open(path, 'r') as f:
        data = json.load(f)
    print(f"Current Date stored: {data}")
    data['month'] = '01' # Previous month
    with open(path, 'w') as f:
        json.dump(data, f)
        
    id3 = offer_generator.get_and_increment_offer_counter(mandant_path, mandant_config)
    print(f"ID 3 (New Month): {id3}")
    if id3.endswith("-001"):
        print("✅ Reset Successful")
    else:
        print("❌ Counter did not reset")

except Exception as e:
    print(f"❌ Error: {e}")

# Cleanup
if os.path.exists(path): os.remove(path)
