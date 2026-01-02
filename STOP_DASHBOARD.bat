@echo off
echo ========================================
echo    Stoppe Mein Business Dashboard
echo ========================================
echo.

taskkill /FI "WINDOWTITLE eq Mein Business API*" /F >nul 2>&1

if %errorlevel% equ 0 (
    echo API Server wurde gestoppt!
) else (
    echo Kein laufender API Server gefunden.
)

echo.
pause
