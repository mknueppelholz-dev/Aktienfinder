"""Datenbeschaffung über Yahoo Finance (yfinance) und Aktienlisten."""
from __future__ import annotations

import json
import math
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

INDIZES: dict[str, list[str]] = {
    # Zusammensetzung ändert sich gelegentlich – fehlende Ticker werden übersprungen.
    "dax": [
        "ADS.DE", "AIR.DE", "ALV.DE", "BAS.DE", "BAYN.DE", "BEI.DE", "BMW.DE",
        "BNR.DE", "CBK.DE", "CON.DE", "DB1.DE", "DBK.DE", "DHL.DE", "DTE.DE",
        "DTG.DE", "ENR.DE", "EOAN.DE", "FRE.DE", "G1A.DE", "HEI.DE", "HEN3.DE",
        "HNR1.DE", "IFX.DE", "MBG.DE", "MRK.DE", "MTX.DE", "MUV2.DE", "P911.DE",
        "PAH3.DE", "QIA.DE", "RHM.DE", "RWE.DE", "SAP.DE", "SHL.DE", "SIE.DE",
        "SRT3.DE", "SY1.DE", "VNA.DE", "VOW3.DE", "ZAL.DE",
    ],
    "dow": [
        "AAPL", "AMGN", "AMZN", "AXP", "BA", "CAT", "CRM", "CSCO", "CVX", "DIS",
        "GS", "HD", "HON", "IBM", "JNJ", "JPM", "KO", "MCD", "MMM", "MRK",
        "MSFT", "NKE", "NVDA", "PG", "SHW", "TRV", "UNH", "V", "VZ", "WMT",
    ],
    "value": [  # bekannte Value-/Buffett-nahe Titel zum Ausprobieren
        "BRK-B", "KO", "AXP", "BAC", "CVX", "OXY", "KHC", "AAPL", "MCO", "CB",
        "ALV.DE", "MUV2.DE", "BMW.DE", "MBG.DE", "VOW3.DE", "DHL.DE",
    ],
}


def lade_tickerliste(quelle: str) -> list[str]:
    """Index-Name (dax, dow, value), Datei mit einem Ticker pro Zeile
    oder kommagetrennte Liste."""
    if quelle.lower() in INDIZES:
        return INDIZES[quelle.lower()]
    pfad = Path(quelle)
    if pfad.is_file():
        return [z.strip() for z in pfad.read_text().splitlines()
                if z.strip() and not z.startswith("#")]
    return [t.strip().upper() for t in quelle.split(",") if t.strip()]


def _f(x) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) or math.isinf(v) else v


def _zeile(df, *namen) -> list[float] | None:
    """Zeitreihe (neueste zuerst) aus einem yfinance-Abschluss-DataFrame."""
    if df is None or getattr(df, "empty", True):
        return None
    for n in namen:
        if n in df.index:
            werte = [_f(v) for v in df.loc[n].tolist()]
            werte = [v for v in werte if v is not None]
            return werte or None
    return None


def _jahre(df) -> list[str] | None:
    if df is None or getattr(df, "empty", True):
        return None
    return [str(getattr(c, "year", c)) for c in df.columns]


def hole_kursverlauf(ticker: str, zeitraum: str = "5y"):
    """Schlusskurse als pandas-Series (Index = Datum). None bei Fehler."""
    import yfinance as yf
    try:
        h = yf.Ticker(ticker).history(period=zeitraum)
        return None if h.empty else h["Close"]
    except Exception:
        return None


def hole_kennzahlen(ticker: str) -> dict | None:
    """Holt alle benötigten Kennzahlen für einen Ticker. None bei Fehler."""
    import yfinance as yf

    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        if not info.get("regularMarketPrice") and not info.get("currentPrice"):
            return None
        cashflow = t.cashflow
        gewinn = t.income_stmt
    except Exception:
        return None

    fcf_hist = _zeile(cashflow, "Free Cash Flow")
    if fcf_hist is None:
        ocf = _zeile(cashflow, "Operating Cash Flow")
        capex = _zeile(cashflow, "Capital Expenditure")
        if ocf and capex:
            fcf_hist = [o + c for o, c in zip(ocf, capex)]  # Capex ist negativ

    d2e = _f(info.get("debtToEquity"))
    return {
        "ticker": ticker,
        "name": info.get("longName") or info.get("shortName"),
        "waehrung": info.get("currency"),
        "sektor": info.get("sector"),
        "kurs": _f(info.get("currentPrice") or info.get("regularMarketPrice")),
        "kgv": _f(info.get("trailingPE")),
        "kbv": _f(info.get("priceToBook")),
        "eigenkapitalrendite": _f(info.get("returnOnEquity")),
        "verschuldung": d2e / 100 if d2e is not None else None,  # Yahoo liefert %
        "nettomarge": _f(info.get("profitMargins")),
        "liquiditaet": _f(info.get("currentRatio")),
        "fcf": _f(info.get("freeCashflow")) or (fcf_hist[0] if fcf_hist else None),
        "marktkapitalisierung": _f(info.get("marketCap")),
        "aktien_anzahl": _f(info.get("sharesOutstanding")),
        "cash": _f(info.get("totalCash")),
        "schulden": _f(info.get("totalDebt")),
        "fcf_historie": fcf_hist,
        "gewinn_historie": _zeile(gewinn, "Net Income", "Net Income Common Stockholders"),
        "jahre": _jahre(cashflow),
    }


def hole_viele(ticker: list[str], parallel: int = 8, fortschritt=None) -> list[dict]:
    ergebnisse = []
    with ThreadPoolExecutor(max_workers=parallel) as pool:
        for i, k in enumerate(pool.map(hole_kennzahlen, ticker), 1):
            if fortschritt:
                fortschritt(i, len(ticker))
            if k:
                ergebnisse.append(k)
    return ergebnisse


def lade_demo() -> list[dict]:
    return json.loads((Path(__file__).parent / "demo_daten.json").read_text())
