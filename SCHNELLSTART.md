# Launcher für Mein Business Dashboard

## 🚀 Schnellstart

### Schritt 1: API Server starten
```powershell
cd backend
python api_server.py
```

### Schritt 2: Frontend öffnen
Öffne in deinem Browser:
```
file:///c:/Users/Admin/Desktop/Mein_Business/frontend/index.html
```

Oder doppelklicke auf `frontend/index.html`

---

## 📝 Was ist neu?

### ✅ Sicherheit (Phase 1)
- **`.env` System**: Passwörter sind jetzt sicher in `.env` gespeichert
- **Automatisches Backup**: `python backend/backup.py` erstellt ZIP-Backups
- **Logging**: Alle Aktionen werden in `backend/logs/` protokolliert

### ✅ Admin Dashboard (Phase 2)
- **Moderne Web-UI**: Übersicht aller Mandanten
- **Echtzeit-Statistiken**: Einnahmen, offene Rechnungen, etc.
- **Schnellaktionen**: Direktzugriff auf häufige Funktionen
- **REST API**: Backend auf http://localhost:5000

---

## 🔧 Fehlerbehebung

### API Server startet nicht?
```powershell
# Dependencies installieren
cd backend
python -m pip install -r requirements.txt

# Dann nochmal starten
python api_server.py
```

### Frontend zeigt Fehler?
- Stelle sicher, dass der API Server läuft (siehe Schritt 1)
- Browser neu laden (F5)

---

## 💡 Tipps

### Backup erstellen
```powershell
cd backend
python backup.py
```

### Logs ansehen
```powershell
cd backend/logs
type 2026-01-01.log
```

### Test-Logging
```powershell
cd backend
python logger.py
```

---

Viel Erfolg! 🚀
