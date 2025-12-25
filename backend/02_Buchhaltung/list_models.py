import google.generativeai as genai
import sys
import io

# Windows Console Fix für Sonderzeichen
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Konfiguriere API Key
GOOGLE_API_KEY = "AIzaSyA0XsNdUbfw6Pm0dl6TkmMCMfbYUh_8-aE"
genai.configure(api_key=GOOGLE_API_KEY)

# Liste alle verfügbaren Modelle auf
print("Verfügbare Gemini-Modelle:\n")
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✅ {model.name}")
        print(f"   Beschreibung: {model.description}")
        print(f"   Unterstützte Methoden: {model.supported_generation_methods}")
        print()
