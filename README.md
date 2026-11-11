# Buffett-Aktienfinder

Durchsucht Aktienlisten (DAX, Dow Jones, eigene Listen) nach Warren-Buffett-/Value-Kriterien.
Die Daten kommen kostenlos von Yahoo Finance (über `yfinance`).

## App starten (ohne Vorkenntnisse)
1. **Python installieren** (einmalig): https://www.python.org/downloads/
   Unter Windows dabei **„Add python.exe to PATH“** anhaken.
2. Ordner `aktienfinder` entpacken.
3. Doppelklick auf
   - **Windows:** `start_windows.bat`
   - **Mac:** `start_mac.command` (beim ersten Mal: Rechtsklick → Öffnen)
4. Der Browser öffnet die App. Der erste Start dauert 1–2 Minuten (Einrichtung).
   Das schwarze Fenster offen lassen, zum Beenden schließen.

### Was die App kann
- **🌍 Welt-Scanner:** durchsucht *alle* börsennotierten Aktien weltweit (oder ausgewählte
  Länder) direkt über den Yahoo-Screener. Regeln als An/Aus-Knöpfe, Ergebnis als Karten
  oder Tabelle, „⚡ Buffett-Score“ für die Top-Treffer.
- **🏆 Index-Check:** DAX, Dow Jones, Value-Klassiker oder eigene Ticker mit allen
  10 Regeln inkl. innerem Wert (DCF) prüfen.
- **🔬 Einzelanalyse:** Buffett-Score-Ring, Abzeichen (🏷️ Schnäppchen, 🏰 Burggraben,
  🛡️ Festung, 💰 Cash-Maschine …), Checkliste, Kursverlauf, Cashflow-Diagramm.
- **📚 Lexikon:** jede Kennzahl einfach erklärt.
- **Strategien:** 🎩 Buffett streng (KGV < 10), 💎 Buffett Qualität, 🔎 Graham Deep Value,
  🎈 Locker. Alle Grenzwerte lassen sich zusätzlich per Regler anpassen.

**Welt-Scanner vs. Index-Check:** Der Welt-Scanner filtert auf Yahoos Servern und ist
deshalb blitzschnell, kennt aber nur die aktuellen Kennzahlen (letzte 12 Monate).
Mehrjahres-Prüfungen und den inneren Wert gibt es per „⚡ Buffett-Score“ bzw. in der
Einzelanalyse.

## Für Fortgeschrittene
```bash
pip install -r requirements.txt
```
```bash
streamlit run app.py
```
Kommandozeile:
```bash
python finder.py dax                      # DAX-40 durchsuchen
python finder.py dow --kgv 15 --details   # Dow Jones, KGV-Grenze 15, Einzelprüfungen
python finder.py AAPL,KO,ALV.DE --alle    # eigene Ticker, auch Aktien, die durchfallen
python finder.py liste.txt --csv out.csv  # Datei mit einem Ticker pro Zeile
python finder.py --demo                   # Beispieldaten ohne Internet
```
Deutsche Aktien bekommen die Endung `.DE` (Xetra), z. B. `ALV.DE`.

## Kriterien (änderbar in `kriterien.py` → `Grenzwerte`)
| Kriterium | Standard | Warum |
|---|---|---|
| **KGV** (Pflicht) | 0 < KGV < 10 | günstige Bewertung |
| **Free Cashflow** (Pflicht) | letzte 3 Jahre > 0 | das Geschäft erwirtschaftet echtes Geld |
| KBV | < 1,5 | Graham-Regel, Buchwert als Untergrenze |
| Eigenkapitalrendite | ≥ 15 % | Hinweis auf einen Burggraben (Moat) |
| Verschuldungsgrad FK/EK | ≤ 0,5 | Buffett meidet hohe Schulden |
| Nettomarge | ≥ 10 % | Preissetzungsmacht |
| Current Ratio | ≥ 1,5 | kurzfristige Zahlungsfähigkeit |
| FCF-Rendite | ≥ 5 % | Free Cashflow im Verhältnis zum Börsenwert |
| Gewinnstabilität | letzte 3 Jahre Gewinn > 0 | verlässliches Geschäft |
| Sicherheitsmarge | Kurs ≥ 25 % unter innerem Wert | „Margin of Safety“ |

Für jede Aktie gibt es 0–10 Punkte. Treffer müssen beide Pflichtkriterien erfüllen.

**Innerer Wert:** Der Free Cashflow (Durchschnitt der letzten 3 Jahre, als Näherung für
Buffetts „Owner Earnings“) wird über 10 Jahre abgezinst (10 %). Das Wachstum wird bei 12 %
gedeckelt und läuft auf 2,5 % ewiges Wachstum aus. Dazu kommt die Netto-Liquidität.

## Gut zu wissen
- Buffett selbst kauft lieber „ein wunderbares Unternehmen zu einem fairen Preis“ als ein
  mittelmäßiges zu einem Schnäppchenpreis. KGV < 10 schließt viele Qualitätsaktien aus
  (Apple, Coca-Cola). Probier also auch `--kgv 15` oder `--kgv 20`.
- **Banken und Versicherungen:** Kennzahlen wie Current Ratio oder Verschuldungsgrad sagen
  bei ihnen wenig aus. Sie fallen dort oft zu Unrecht durch.
- Yahoo liefert meist nur 4 Jahre Bilanzhistorie. Buffett schaut auf 10 Jahre.
- Keine Anlageberatung.

## Tests
```bash
python -m unittest
```
