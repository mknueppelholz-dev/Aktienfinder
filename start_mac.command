#!/bin/bash
# Buffett-Aktienfinder starten (Mac/Linux): Doppelklick bzw. ./start_mac.command
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 ist nicht installiert. Bitte von https://www.python.org/downloads/ installieren."
  open https://www.python.org/downloads/ 2>/dev/null || xdg-open https://www.python.org/downloads/ 2>/dev/null
  read -p "Enter zum Schließen"; exit 1
fi
if [ ! -x .venv/bin/python ]; then
  echo "Erster Start: richte die App ein, das dauert 1-2 Minuten ..."
  python3 -m venv .venv && .venv/bin/python -m pip install --upgrade pip -q \
    && .venv/bin/python -m pip install -r requirements.txt -q \
    || { echo "Installation fehlgeschlagen."; rm -rf .venv; read -p "Enter zum Schließen"; exit 1; }
fi
echo "Starte Buffett-Aktienfinder ... (Fenster offen lassen, zum Beenden Ctrl+C)"
.venv/bin/python -m streamlit run app.py --server.headless false --browser.gatherUsageStats false
