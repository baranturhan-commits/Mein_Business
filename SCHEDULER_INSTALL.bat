@echo off
REM ======================================
REM Windows Task Scheduler Setup
REM Richtet automatische Tasks ein
REM ======================================

echo ========================================
echo   Mein Business - Scheduler Setup
echo ========================================
echo.
echo Dieser Script richtet folgende Tasks ein:
echo   [1] Tägliches Backup um 23:00 Uhr
echo   [2] Wöchentliche Mahnprüfung (Freitag 10:00)
echo   [3] Monatlicher Report (1. des Monats 09:00)
echo.
pause

REM Pfade
set BACKEND_PATH=%~dp0backend
set PYTHON_EXE=python

echo.
echo [1/3] Erstelle täglichen Backup-Task...
schtasks /create /tn "Mein_Business_Backup" /tr "%PYTHON_EXE% %BACKEND_PATH%\backup.py" /sc daily /st 23:00 /f
if %errorlevel% equ 0 (
    echo    ✅ Backup-Task erstellt
) else (
    echo    ❌ Fehler beim Erstellen
)

echo.
echo [2/3] Erstelle wöchentlichen Mahnung-Check...
schtasks /create /tn "Mein_Business_Mahnungen" /tr "%PYTHON_EXE% %BACKEND_PATH%\tasks\auto_mahnung.py" /sc weekly /d FRI /st 10:00 /f
if %errorlevel% equ 0 (
    echo    ✅ Mahnung-Task erstellt
) else (
    echo    ❌ Fehler beim Erstellen
)

echo.
echo [3/3] Erstelle monatlichen Report...
schtasks /create /tn "Mein_Business_Report" /tr "%PYTHON_EXE% %BACKEND_PATH%\tasks\monthly_report.py" /sc monthly /d 1 /st 09:00 /f
if %errorlevel% equ 0 (
    echo    ✅ Report-Task erstellt
) else (
    echo    ❌ Fehler beim Erstellen
)

echo.
echo ========================================
echo   Setup abgeschlossen!
echo ========================================
echo.
echo Prüfe Tasks mit: schtasks /query /tn "Mein_Business_*"
echo.
pause
