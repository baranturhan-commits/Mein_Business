@echo off
echo ========================================
echo    Stoppe Mein Business Dashboard
echo ========================================
echo.

echo Beende alle Python-Prozesse...
taskkill /F /IM python.exe >nul 2>&1

if %errorlevel% equ 0 (
    echo ✓ Alle Server wurden gestoppt!
) else (
    echo Kein laufender Server gefunden.
)

echo.
pause
