@echo off
title Buffett-Aktienfinder
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python ist nicht installiert.
  echo Bitte von https://www.python.org/downloads/ installieren
  echo und dabei "Add python.exe to PATH" anhaken. Danach erneut starten.
  start https://www.python.org/downloads/
  pause
  exit /b
)
if not exist ".venv\Scripts\python.exe" (
  echo Erster Start: richte die App ein, das dauert 1-2 Minuten ...
  python -m venv .venv
  ".venv\Scripts\python.exe" -m pip install --upgrade pip -q
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt -q
  if errorlevel 1 ( echo Installation fehlgeschlagen. & pause & exit /b )
)
echo Starte Buffett-Aktienfinder ... (dieses Fenster offen lassen, zum Beenden schliessen)
".venv\Scripts\python.exe" -m streamlit run app.py --server.headless false --browser.gatherUsageStats false
pause
