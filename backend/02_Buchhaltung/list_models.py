from google import genai
import sys
import io
import os
from dotenv import load_dotenv

# Windows Console Fix für Sonderzeichen
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Lade Umgebungsvariablen aus .env Datei
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Konfiguriere API Key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("❌ GOOGLE_API_KEY nicht gefunden!")
    print("👉 Bitte erstelle eine .env Datei im backend/ Ordner mit:")
    print("   GOOGLE_API_KEY=dein_api_key_hier")
    sys.exit(1)

# Erstelle Client mit API Key
client = genai.Client(api_key=GOOGLE_API_KEY)

# Liste alle verfügbaren Modelle auf
print("Verfügbare Gemini-Modelle:\n")
for model in client.models.list():
    # Prüfe ob das Modell generateContent unterstützt
    if hasattr(model, 'supported_actions') and 'generateContent' in (model.supported_actions or []):
        print(f"✅ {model.name}")
        if hasattr(model, 'description') and model.description:
            print(f"   Beschreibung: {model.description}")
        print()
    elif model.name and 'gemini' in model.name.lower():
        # Zeige Gemini-Modelle auch ohne Filter
        print(f"✅ {model.name}")
        if hasattr(model, 'description') and model.description:
            print(f"   Beschreibung: {model.description}")
        print()
