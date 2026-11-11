"""Buffett-Kriterien und Bewertungslogik.

Reine Logik ohne Netzwerkzugriff: bekommt ein Kennzahlen-Dict und liefert
Prüfergebnisse, Punktzahl und inneren Wert (DCF) zurück.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Grenzwerte:
    """Alle Schwellen an einem Ort, damit man sie leicht anpassen kann."""
    kgv_max: float = 10.0               # Kurs-Gewinn-Verhältnis
    kbv_max: float = 1.5                # Kurs-Buchwert-Verhältnis
    eigenkapitalrendite_min: float = 0.15   # ROE 15 %
    verschuldung_max: float = 0.5       # Fremdkapital / Eigenkapital
    nettomarge_min: float = 0.10        # 10 %
    liquiditaet_min: float = 1.5        # Current Ratio
    fcf_rendite_min: float = 0.05       # Free Cashflow / Marktkapitalisierung
    fcf_positive_jahre: int = 3         # FCF in allen letzten n Jahren > 0
    gewinn_stabil_jahre: int = 3        # Gewinn in allen letzten n Jahren > 0
    sicherheitsmarge_min: float = 0.25  # Kurs mind. 25 % unter innerem Wert
    # DCF-Annahmen
    abzinsung: float = 0.10
    ewiges_wachstum: float = 0.025
    wachstum_max: float = 0.12
    dcf_jahre: int = 10


@dataclass
class Pruefung:
    name: str
    bestanden: bool | None   # None = keine Daten
    wert: str
    regel: str
    pflicht: bool = False


@dataclass
class Ergebnis:
    ticker: str
    name: str
    kurs: float | None
    waehrung: str
    pruefungen: list[Pruefung] = field(default_factory=list)
    innerer_wert: float | None = None
    sicherheitsmarge: float | None = None

    @property
    def punkte(self) -> int:
        return sum(1 for p in self.pruefungen if p.bestanden)

    @property
    def max_punkte(self) -> int:
        return len(self.pruefungen)

    @property
    def pflicht_erfuellt(self) -> bool:
        return all(p.bestanden for p in self.pruefungen if p.pflicht)

    @property
    def datenluecken(self) -> int:
        return sum(1 for p in self.pruefungen if p.bestanden is None)


def _pct(x: float | None) -> str:
    return "–" if x is None else f"{x * 100:.1f} %"


def _num(x: float | None, nachkomma: int = 2) -> str:
    return "–" if x is None else f"{x:.{nachkomma}f}"


def _check(wert, bedingung) -> bool | None:
    return None if wert is None else bool(bedingung(wert))


def _alle_positiv(reihe: list[float] | None, n: int) -> bool | None:
    if not reihe:
        return None
    letzte = reihe[:n]  # neueste zuerst
    return all(v is not None and v > 0 for v in letzte)


def wachstumsrate(reihe: list[float] | None) -> float | None:
    """Jährliche Wachstumsrate (CAGR) aus einer Reihe, neueste zuerst."""
    if not reihe or len(reihe) < 2:
        return None
    neu, alt = reihe[0], reihe[-1]
    jahre = len(reihe) - 1
    if neu is None or alt is None or alt <= 0 or neu <= 0:
        return None
    return (neu / alt) ** (1 / jahre) - 1


def innerer_wert_dcf(k: dict, g: Grenzwerte) -> float | None:
    """Innerer Wert je Aktie per Discounted-Cashflow auf Basis des Free Cashflows
    (Buffetts "Owner Earnings" näherungsweise)."""
    fcf_reihe = k.get("fcf_historie") or []
    aktien = k.get("aktien_anzahl")
    if not fcf_reihe or not aktien:
        return None
    # Durchschnitt der letzten Jahre glättet Ausreißer
    werte = [v for v in fcf_reihe[:3] if v is not None]
    if not werte:
        return None
    fcf = sum(werte) / len(werte)
    if fcf <= 0:
        return None
    wachstum = wachstumsrate(fcf_reihe) or 0.0
    wachstum = max(0.0, min(wachstum, g.wachstum_max))  # konservativ deckeln

    barwert = 0.0
    cf = fcf
    for jahr in range(1, g.dcf_jahre + 1):
        # Wachstum läuft linear auf das ewige Wachstum aus
        anteil = (jahr - 1) / max(g.dcf_jahre - 1, 1)
        rate = wachstum + (g.ewiges_wachstum - wachstum) * anteil
        cf *= 1 + rate
        barwert += cf / (1 + g.abzinsung) ** jahr
    endwert = cf * (1 + g.ewiges_wachstum) / (g.abzinsung - g.ewiges_wachstum)
    barwert += endwert / (1 + g.abzinsung) ** g.dcf_jahre

    netto_cash = (k.get("cash") or 0) - (k.get("schulden") or 0)
    return (barwert + netto_cash) / aktien


def bewerte(k: dict, g: Grenzwerte | None = None) -> Ergebnis:
    g = g or Grenzwerte()
    e = Ergebnis(
        ticker=k["ticker"],
        name=k.get("name") or k["ticker"],
        kurs=k.get("kurs"),
        waehrung=k.get("waehrung") or "",
    )

    kgv = k.get("kgv")
    e.pruefungen.append(Pruefung(
        "KGV", _check(kgv, lambda v: 0 < v < g.kgv_max), _num(kgv),
        f"0 < KGV < {g.kgv_max:g}", pflicht=True))

    kbv = k.get("kbv")
    e.pruefungen.append(Pruefung(
        "KBV", _check(kbv, lambda v: 0 < v < g.kbv_max), _num(kbv),
        f"KBV < {g.kbv_max:g}"))

    roe = k.get("eigenkapitalrendite")
    e.pruefungen.append(Pruefung(
        "Eigenkapitalrendite", _check(roe, lambda v: v >= g.eigenkapitalrendite_min),
        _pct(roe), f"≥ {_pct(g.eigenkapitalrendite_min)}"))

    vs = k.get("verschuldung")
    e.pruefungen.append(Pruefung(
        "Verschuldungsgrad", _check(vs, lambda v: 0 <= v <= g.verschuldung_max),
        _num(vs), f"FK/EK ≤ {g.verschuldung_max:g}"))

    marge = k.get("nettomarge")
    e.pruefungen.append(Pruefung(
        "Nettomarge", _check(marge, lambda v: v >= g.nettomarge_min),
        _pct(marge), f"≥ {_pct(g.nettomarge_min)}"))

    cr = k.get("liquiditaet")
    e.pruefungen.append(Pruefung(
        "Liquidität (Current Ratio)", _check(cr, lambda v: v >= g.liquiditaet_min),
        _num(cr), f"≥ {g.liquiditaet_min:g}"))

    fcf_hist = k.get("fcf_historie")
    e.pruefungen.append(Pruefung(
        "Free Cashflow stets positiv", _alle_positiv(fcf_hist, g.fcf_positive_jahre),
        f"{len(fcf_hist or [])} Jahre Daten", f"letzte {g.fcf_positive_jahre} Jahre > 0",
        pflicht=True))

    fcf, mcap = k.get("fcf"), k.get("marktkapitalisierung")
    fcf_rendite = fcf / mcap if fcf is not None and mcap else None
    e.pruefungen.append(Pruefung(
        "FCF-Rendite", _check(fcf_rendite, lambda v: v >= g.fcf_rendite_min),
        _pct(fcf_rendite), f"≥ {_pct(g.fcf_rendite_min)}"))

    gewinne = k.get("gewinn_historie")
    e.pruefungen.append(Pruefung(
        "Gewinn stabil", _alle_positiv(gewinne, g.gewinn_stabil_jahre),
        f"Wachstum p.a. {_pct(wachstumsrate(gewinne))}",
        f"letzte {g.gewinn_stabil_jahre} Jahre Gewinn > 0"))

    e.innerer_wert = innerer_wert_dcf(k, g)
    if e.innerer_wert and e.kurs and e.innerer_wert > 0:
        e.sicherheitsmarge = 1 - e.kurs / e.innerer_wert
    e.pruefungen.append(Pruefung(
        "Sicherheitsmarge (DCF)",
        _check(e.sicherheitsmarge, lambda v: v >= g.sicherheitsmarge_min),
        _pct(e.sicherheitsmarge), f"≥ {_pct(g.sicherheitsmarge_min)}"))
    return e
