"""Welt-Scanner: durchsucht ALLE börsennotierten Aktien weltweit über den
Yahoo-Finance-Screener. Die Filter laufen auf Yahoos Server, deshalb ist das
auch bei zehntausenden Aktien in Sekunden erledigt."""
from __future__ import annotations

from kriterien import Grenzwerte

# Kürzel → (Flagge, Name). Reihenfolge = Anzeige in der App.
REGIONEN: dict[str, tuple[str, str]] = {
    "de": ("🇩🇪", "Deutschland"), "us": ("🇺🇸", "USA"), "at": ("🇦🇹", "Österreich"),
    "ch": ("🇨🇭", "Schweiz"), "gb": ("🇬🇧", "Großbritannien"), "fr": ("🇫🇷", "Frankreich"),
    "nl": ("🇳🇱", "Niederlande"), "it": ("🇮🇹", "Italien"), "es": ("🇪🇸", "Spanien"),
    "se": ("🇸🇪", "Schweden"), "no": ("🇳🇴", "Norwegen"), "dk": ("🇩🇰", "Dänemark"),
    "fi": ("🇫🇮", "Finnland"), "be": ("🇧🇪", "Belgien"), "pl": ("🇵🇱", "Polen"),
    "jp": ("🇯🇵", "Japan"), "kr": ("🇰🇷", "Südkorea"), "cn": ("🇨🇳", "China"),
    "hk": ("🇭🇰", "Hongkong"), "tw": ("🇹🇼", "Taiwan"), "in": ("🇮🇳", "Indien"),
    "sg": ("🇸🇬", "Singapur"), "au": ("🇦🇺", "Australien"), "ca": ("🇨🇦", "Kanada"),
    "br": ("🇧🇷", "Brasilien"), "mx": ("🇲🇽", "Mexiko"), "za": ("🇿🇦", "Südafrika"),
}

# Ticker-Endung → Flagge (für die Ergebnis-Karten)
_ENDUNG_FLAGGE = {
    "DE": "🇩🇪", "F": "🇩🇪", "MU": "🇩🇪", "SG": "🇩🇪", "BE": "🇩🇪", "DU": "🇩🇪", "HM": "🇩🇪",
    "VI": "🇦🇹", "SW": "🇨🇭", "L": "🇬🇧", "PA": "🇫🇷", "AS": "🇳🇱", "MI": "🇮🇹",
    "MC": "🇪🇸", "ST": "🇸🇪", "OL": "🇳🇴", "CO": "🇩🇰", "HE": "🇫🇮", "BR": "🇧🇪",
    "WA": "🇵🇱", "T": "🇯🇵", "KS": "🇰🇷", "KQ": "🇰🇷", "SS": "🇨🇳", "SZ": "🇨🇳",
    "HK": "🇭🇰", "TW": "🇹🇼", "TWO": "🇹🇼", "NS": "🇮🇳", "BO": "🇮🇳", "SI": "🇸🇬",
    "AX": "🇦🇺", "TO": "🇨🇦", "V": "🇨🇦", "SA": "🇧🇷", "MX": "🇲🇽", "JO": "🇿🇦",
    "IR": "🇮🇪", "LS": "🇵🇹", "AT": "🇬🇷", "IS": "🇹🇷", "TA": "🇮🇱", "NZ": "🇳🇿",
}


def flagge(ticker: str) -> str:
    if "." not in ticker:
        return "🇺🇸"
    return _ENDUNG_FLAGGE.get(ticker.rsplit(".", 1)[1].upper(), "🌐")


# Kriterien, die sich im Welt-Scanner an-/ausschalten lassen
KRITERIEN = {
    "kgv": "🏷️ KGV",
    "kbv": "📘 KBV",
    "roe": "🏰 Eigenkapitalrendite",
    "schulden": "🛡️ Wenig Schulden",
    "marge": "💎 Nettomarge",
    "liquiditaet": "💧 Liquidität",
    "fcf": "💰 Free Cashflow > 0",
    "dividende": "📈 5 J. Dividende erhöht",
}
STANDARD_AKTIV = ["kgv", "roe", "schulden", "marge", "fcf"]


def baue_query(g: Grenzwerte, aktiv: list[str], regionen: list[str], min_mcap: float):
    """Baut die Yahoo-Screener-Abfrage. Prozentwerte erwartet Yahoo als 15 statt 0.15."""
    from yfinance import EquityQuery as Q

    teile = []
    if "kgv" in aktiv:
        teile.append(Q("btwn", ["peratio.lasttwelvemonths", 0, g.kgv_max]))
    if "kbv" in aktiv:
        teile.append(Q("btwn", ["pricebookratio.quarterly", 0, g.kbv_max]))
    if "roe" in aktiv:
        teile.append(Q("gte", ["returnonequity.lasttwelvemonths", g.eigenkapitalrendite_min * 100]))
    if "schulden" in aktiv:
        teile.append(Q("lte", ["totaldebtequity.lasttwelvemonths", g.verschuldung_max * 100]))
    if "marge" in aktiv:
        teile.append(Q("gte", ["netincomemargin.lasttwelvemonths", g.nettomarge_min * 100]))
    if "liquiditaet" in aktiv:
        teile.append(Q("gte", ["currentratio.lasttwelvemonths", g.liquiditaet_min]))
    if "fcf" in aktiv:
        teile.append(Q("gt", ["leveredfreecashflow.lasttwelvemonths", 0]))
    if "dividende" in aktiv:
        teile.append(Q("gte", ["consecutive_years_of_dividend_growth_count", 5]))
    if regionen:
        teile.append(Q("eq", ["region", regionen[0]]) if len(regionen) == 1
                     else Q("is-in", ["region", *regionen]))
    if min_mcap > 0:
        teile.append(Q("gte", ["intradaymarketcap", min_mcap]))
    if not teile:  # Yahoo braucht mindestens einen Filter
        teile.append(Q("gt", ["intradaymarketcap", 0]))
    return teile[0] if len(teile) == 1 else Q("and", teile)


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def wandle(q: dict) -> dict:
    """Ein Yahoo-Screener-Ergebnis in ein schlankes Dict übersetzen."""
    t = q.get("symbol", "?")
    return {
        "ticker": t,
        "name": q.get("longName") or q.get("shortName") or t,
        "flagge": flagge(t),
        "boerse": q.get("fullExchangeName") or q.get("exchange") or "",
        "waehrung": q.get("currency") or "",
        "kurs": _f(q.get("regularMarketPrice")),
        "kgv": _f(q.get("trailingPE")),
        "kbv": _f(q.get("priceToBook")),
        "marktkapitalisierung": _f(q.get("marketCap")),
        "jahrestief": _f(q.get("fiftyTwoWeekLow")),
        "jahreshoch": _f(q.get("fiftyTwoWeekHigh")),
    }


def scanne(query, max_treffer: int = 500, fortschritt=None) -> tuple[list[dict], int]:
    """Holt bis zu max_treffer Ergebnisse (größte Firmen zuerst).
    Gibt (Treffer, Gesamtzahl weltweit) zurück."""
    import yfinance as yf

    treffer, gesamt, offset = [], 0, 0
    while offset < max_treffer:
        groesse = min(250, max_treffer - offset)
        antwort = yf.screen(query, offset=offset, size=groesse,
                            sortField="intradaymarketcap", sortAsc=False)
        quotes = antwort.get("quotes") or []
        gesamt = antwort.get("total") or len(quotes)
        treffer += [wandle(q) for q in quotes]
        offset += groesse
        if fortschritt:
            fortschritt(min(len(treffer), gesamt), min(gesamt, max_treffer))
        if len(quotes) < groesse or offset >= gesamt:
            break
    return treffer, gesamt
