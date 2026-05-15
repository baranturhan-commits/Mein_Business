@echo off
cd /d "%~dp0"

echo ========================================
echo    Mein Business Dashboard Starter (v2)
echo ========================================
echo.

echo Oeffne Browser in 2 Sekunden...
start "" "http://localhost:5000"
echo.

:loop
echo Starte API Server... (Druecke Strg+C zum Beenden)
cd backend
py api_server.py
cd ..

echo.
echo ⚠️ Server wurde beendet oder ist abgestuerzt!
echo 🔄 Neustart in 5 Sekunden...
timeout /t 5 /nobreak >nul
goto loop
