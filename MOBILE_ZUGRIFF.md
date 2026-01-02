# Mobile Zugriff - Anleitung

## 📱 Dashboard vom Handy nutzen

### Option 1: Im gleichen Netzwerk (Empfohlen)

1. **IP-Adresse des PCs herausfinden:**
   ```powershell
   ipconfig
   ```
   Suche nach "IPv4-Adresse" (z.B. `192.168.1.100`)

2. **API Server starten:**
   - Doppelklick auf `START_DASHBOARD.bat`
   - Server läuft auf `http://0.0.0.0:5000` (= alle Netzwerk-Interfaces)

3. **Vom Handy zugreifen:**
   - Öffne Browser auf dem Handy
   - Gehe zu: `http://[DEINE-PC-IP]:5000`
   - Beispiel: `http://192.168.1.100:5000`
   - Dann öffne: `index.html` manuell im Handy-Browser
   
   **Oder direkt:**
   - Platziere `frontend/index.html` und alle Assets auf einem Webserver
   - Ändere in `app.js` die `API_BASE_URL` zu deiner PC-IP

### Option 2: QR-Code

Erstelle einen QR-Code mit dieser URL:
```
http://[DEINE-PC-IP]:5000
```

**Online QR-Generator:**
- https://www.qr-code-generator.com/
- URL eingeben → QR-Code erstellen → als Bild speichern

**QR-Code auf Handy scannen = Sofort im Dashboard!**

---

## 🔧 Einrichtung

### Firewall-Regel (Windows)

Damit dein Handy zugreifen kann, muss die Windows-Firewall den Port freigeben:

```powershell
# Als Administrator ausführen:
netsh advfirewall firewall add rule name="Mein Business API" dir=in action=allow protocol=TCP localport=5000
```

### Permanenter Zugriff

Für dauerhaften Zugriff ohne lokalen Webserver:

1. **Statische IP für PC einrichten:**
   - Router-Einstellungen → DHCP-Reservierung
   - Oder manuel in Windows-Netzwerkeinstellungen

2. **Bookmark auf Handy:**
   - Öffne Dashboard einmal
   - "Zum Startbildschirm hinzufügen"
   - = App-Icon auf dem Handy!

---

## ✅ Vorteile

- ✅ **Überall im Haus Zugriff** (gleicher WLAN)
- ✅ **Touch-optimiert** (größere Buttons, einfache Navigation)
- ✅ **Schnelle Checks** unterwegs im Büro
- ✅ **Belege hochladen** direkt vom Handy-Kamera

---

## 🔒 Sicherheit

**Wichtig:**
- Dashboard ist aktuell **OHNE LOGIN**
- Nur im **lokalen Netzwerk** verwenden
- **NICHT** im Internet veröffentlichen ohne Authentifizierung!

Für Internet-Zugriff später:
- VPN einrichten (z.B. WireGuard)
- Oder Login-System implementieren

---

## 🧪 Test

1. Starte Dashboard: `START_DASHBOARD.bat`
2. Öffne auf PC: `http://localhost:5000`
3. Öffne auf Handy: `http://[PC-IP]:5000`
4. **Beide sollten funktionieren!**

Fertig! 🎉
