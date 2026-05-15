@echo off
cd /d "%~dp0"
echo ==========================================
echo   Einrichtung Autostart fuer Mein Business
echo ==========================================
echo.

set "TARGET=%~dp0START_DASHBOARD.bat"
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT=%STARTUP_DIR%\MeinBusinessServer.lnk"

echo Erstelle Verknuepfung im Autostart-Ordner:
echo "%SHORTCUT%"
echo.

:: PowerShell Script zum Erstellen der Verknüpfung
powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT%');$s.TargetPath='%TARGET%';$s.WorkingDirectory='%~dp0';$s.Description='Mein Business Server & Dashboard';$s.Save()"

if exist "%SHORTCUT%" (
    echo.
    echo [OK] Verknuepfung erfolgreich erstellt!
    echo.
    echo ========================================================
    echo  FERTIG!
    echo  Der Server startet ab jetzt automatisch mit Windows.
    echo  (Das schwarze Fenster bitte minimieren, nicht schliessen)
    echo ========================================================
) else (
    echo.
    echo [FEHLER] Konnte Verknuepfung nicht erstellen.
)

echo.
pause
