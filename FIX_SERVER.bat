@echo off
echo ========================================
echo   REPARATUR: Mein Business Server
echo ========================================
echo.
echo 1. Stoppe ALLE laufenden Python-Prozesse...
taskkill /F /IM python.exe >nul 2>&1
echo    Erledigt.
echo.
echo 2. Starte Server neu...
cd backend
start "Mein Business API" py api_server.py
echo.
echo ========================================
echo   FERTIG!
echo ========================================
echo.
echo Bitte jetzt Browser neu laden (F5) und nochmal testen!
echo.
pause
