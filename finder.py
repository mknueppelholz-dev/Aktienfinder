"""Aktienfinder nach Warren-Buffett-Regeln – Kommandozeile.

Beispiele:
    python finder.py dax
    python finder.py dow --kgv 15 --min-punkte 6
    python finder.py AAPL,KO,ALV.DE --details
    python finder.py meine_liste.txt --csv ergebnis.csv
    python finder.py --demo
"""
from __future__ import annotations

import argparse
import csv
import sys

from daten import hole_viele, lade_demo, lade_tickerliste
from kriterien import Ergebnis, Grenzwerte, bewerte


def sortiere(ergebnisse: list[Ergebnis]) -> list[Ergebnis]:
    return sorted(ergebnisse, key=lambda e: (e.pflicht_erfuellt, e.punkte,
                                             e.sicherheitsmarge or -9), reverse=True)


def zeige_tabelle(ergebnisse: list[Ergebnis]) -> None:
    kopf = f"{'Ticker':<9} {'Name':<28} {'Kurs':>10} {'Inn. Wert':>10} {'Marge':>7} {'Punkte':>7}  Pflicht"
    print(kopf)
    print("-" * len(kopf))
    for e in ergebnisse:
        kurs = f"{e.kurs:.2f}" if e.kurs else "–"
        iw = f"{e.innerer_wert:.2f}" if e.innerer_wert else "–"
        marge = f"{e.sicherheitsmarge * 100:.0f}%" if e.sicherheitsmarge is not None else "–"
        print(f"{e.ticker:<9} {e.name[:28]:<28} {kurs:>10} {iw:>10} {marge:>7} "
              f"{e.punkte:>3}/{e.max_punkte:<3}  {'✔' if e.pflicht_erfuellt else '✘'}")


def zeige_details(e: Ergebnis) -> None:
    print(f"\n{e.name} ({e.ticker})  {e.kurs or '–'} {e.waehrung}")
    for p in e.pruefungen:
        symbol = {True: "✔", False: "✘", None: "?"}[p.bestanden]
        stern = "*" if p.pflicht else " "
        print(f"  {symbol}{stern} {p.name:<28} {p.wert:>16}   ({p.regel})")


def schreibe_csv(pfad: str, ergebnisse: list[Ergebnis]) -> None:
    with open(pfad, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        namen = [p.name for p in ergebnisse[0].pruefungen] if ergebnisse else []
        w.writerow(["Ticker", "Name", "Kurs", "Währung", "Innerer Wert",
                    "Sicherheitsmarge", "Punkte", "Pflicht erfüllt", *namen])
        for e in ergebnisse:
            w.writerow([e.ticker, e.name, e.kurs, e.waehrung,
                        round(e.innerer_wert, 2) if e.innerer_wert else "",
                        round(e.sicherheitsmarge, 3) if e.sicherheitsmarge is not None else "",
                        e.punkte, e.pflicht_erfuellt,
                        *[p.wert for p in e.pruefungen]])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Aktienfinder nach Buffett-Regeln")
    ap.add_argument("quelle", nargs="?", default="value",
                    help="dax | dow | value | Datei | Ticker,kommagetrennt")
    ap.add_argument("--demo", action="store_true", help="Beispieldaten ohne Internet")
    ap.add_argument("--kgv", type=float, help="max. KGV (Standard 10)")
    ap.add_argument("--roe", type=float, help="min. Eigenkapitalrendite in %% (Standard 15)")
    ap.add_argument("--marge", type=float, help="min. Sicherheitsmarge in %% (Standard 25)")
    ap.add_argument("--min-punkte", type=int, default=0, help="nur Aktien ab n Punkten")
    ap.add_argument("--alle", action="store_true", help="auch Aktien ohne erfüllte Pflichtkriterien")
    ap.add_argument("--details", action="store_true", help="Einzelprüfungen anzeigen")
    ap.add_argument("--csv", help="Ergebnis als CSV speichern")
    a = ap.parse_args(argv)

    g = Grenzwerte()
    if a.kgv is not None:
        g.kgv_max = a.kgv
    if a.roe is not None:
        g.eigenkapitalrendite_min = a.roe / 100
    if a.marge is not None:
        g.sicherheitsmarge_min = a.marge / 100

    if a.demo:
        daten = lade_demo()
    else:
        ticker = lade_tickerliste(a.quelle)
        print(f"Lade Daten für {len(ticker)} Aktien …", file=sys.stderr)
        daten = hole_viele(ticker, fortschritt=lambda i, n: print(
            f"\r  {i}/{n}", end="", file=sys.stderr))
        print(file=sys.stderr)
        if not daten:
            print("Keine Daten erhalten – Internetverbindung / Ticker prüfen.", file=sys.stderr)
            return 1

    ergebnisse = sortiere([bewerte(k, g) for k in daten])
    treffer = [e for e in ergebnisse if e.punkte >= a.min_punkte
               and (a.alle or e.pflicht_erfuellt)]

    erfuellt = sum(1 for e in ergebnisse if e.pflicht_erfuellt)
    print(f"\n{erfuellt} von {len(ergebnisse)} Aktien erfüllen die Pflichtkriterien "
          f"(KGV < {g.kgv_max:g}, FCF stets positiv)"
          + (f" – {len(treffer)} angezeigt" if a.alle or a.min_punkte else "") + "\n")
    if treffer:
        zeige_tabelle(treffer)
        if a.details:
            for e in treffer:
                zeige_details(e)
    if a.csv:
        schreibe_csv(a.csv, treffer)
        print(f"\nGespeichert: {a.csv}")
    print("\nHinweis: Keine Anlageberatung. Kennzahlen von Yahoo Finance, ohne Gewähr.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
