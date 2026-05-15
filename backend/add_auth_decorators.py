"""
Script zum automatischen Hinzufügen von @require_auth zu allen API Routes
"""
import re

# Lies die Datei
with open('api_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Routes die NICHT geschützt werden sollen (public routes)
SKIP_ROUTES = [
    '/api/health',  # Health check
    '/',  # Frontend serving
    '/<path:path>',  # Static files
]

# Finde alle @app.route Definitionen
route_pattern = r"(@app\.route\('(/api/[^']+)'[^\)]*\))\n(def [a-z_]+)"

matches = list(re.finditer(route_pattern, content))

print(f"Gefunden: {len(matches)} Routes")

# Zähler
added_count = 0
skipped_count = 0

# Iteriere rückwärts (damit Positionen stabil bleiben)
for match in reversed(matches):
    route_decorator = match.group(1)
    route_path = match.group(2)
    func_def = match.group(3)
    
    # Prüfe ob Skip
    if any(skip in route_path for skip in SKIP_ROUTES):
        print(f"  SKIP: {route_path}")
        skipped_count += 1
        continue
    
    # Prüfe ob bereits @require_auth vorhanden
    # Schaue im Text VOR der Route
    before_route = content[:match.start()]
    last_100_chars = before_route[-100:]
    
    if '@require_auth' in last_100_chars:
        print(f"  EXISTS: {route_path}")
        skipped_count += 1
        continue
    
    # Füge @require_auth hinzu
    old_text = match.group(0)
    new_text = f"{route_decorator}\n@require_auth\n{func_def}"
    
    content = content[:match.start()] + new_text + content[match.end():]
    
    print(f"  ADDED: {route_path}")
    added_count += 1

# Speichere
with open('api_server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✅ Fertig!")
print(f"   {added_count} Routes geschützt")
print(f"   {skipped_count} Routes übersprungen")
