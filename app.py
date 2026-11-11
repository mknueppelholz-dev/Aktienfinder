"""Buffett-Aktienfinder – Web-App.  Start: Doppelklick auf start_windows.bat /
start_mac.command  oder  `streamlit run app.py`."""
from dataclasses import replace

import pandas as pd
import streamlit as st

from daten import INDIZES, hole_kennzahlen, hole_kursverlauf, hole_viele, lade_demo
from finder import sortiere
from kriterien import Grenzwerte, bewerte

st.set_page_config(page_title="Buffett-Aktienfinder", page_icon="📈", layout="wide")

LISTEN = {
    "🇩🇪 DAX 40": "dax",
    "🇺🇸 Dow Jones 30": "dow",
    "💎 Value-Klassiker": "value",
    "✏️ Eigene Ticker": "eigene",
    "🧪 Demo (ohne Internet)": "demo",
}

VORLAGEN = {
    "Buffett streng (KGV < 10)": Grenzwerte(),
    "Buffett Qualität (KGV < 20)": Grenzwerte(kgv_max=20, kbv_max=5, sicherheitsmarge_min=0.15,
                                               fcf_rendite_min=0.04),
    "Graham Deep Value": Grenzwerte(kgv_max=12, kbv_max=1.0, eigenkapitalrendite_min=0.08,
                                    nettomarge_min=0.05, liquiditaet_min=2.0,
                                    sicherheitsmarge_min=0.33),
    "Locker (alles anzeigen)": Grenzwerte(kgv_max=40, kbv_max=10, eigenkapitalrendite_min=0,
                                          verschuldung_max=3, nettomarge_min=0,
                                          liquiditaet_min=0.5, fcf_rendite_min=0,
                                          sicherheitsmarge_min=0),
}

SYMBOL = {True: "✅", False: "❌", None: "❔"}


@st.cache_data(ttl=3600, show_spinner=False)
def lade_liste(ticker: tuple[str, ...]):
    return hole_viele(list(ticker))


@st.cache_data(ttl=3600, show_spinner=False)
def lade_einzeln(ticker: str):
    if ticker.startswith("DEMO"):
        return next((d for d in lade_demo() if d["ticker"] == ticker), None), None
    return hole_kennzahlen(ticker), hole_kursverlauf(ticker)


def geld(x, w=""):
    if x is None:
        return "–"
    de = lambda z, n: f"{z:,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    for grenze, endung in ((1e12, "Bio."), (1e9, "Mrd."), (1e6, "Mio.")):
        if abs(x) >= grenze:
            return f"{de(x / grenze, 1)} {endung} {w}".strip()
    return f"{de(x, 2)} {w}".strip()


# ---------------------------------------------------------------- Seitenleiste
with st.sidebar:
    st.title("📈 Buffett-Finder")
    vorlage = st.selectbox("Strategie", list(VORLAGEN), key="strategie", help="Voreinstellung für alle Regler")
    v = VORLAGEN[vorlage]
    k = f"_{vorlage}"  # Regler springen beim Wechsel der Strategie auf deren Werte
    g = replace(v)
    with st.expander("⚙️ Kriterien anpassen"):
        g.kgv_max = st.slider("max. KGV", 3.0, 40.0, float(v.kgv_max), 0.5, key="kgv" + k)
        g.kbv_max = st.slider("max. KBV", 0.5, 10.0, float(v.kbv_max), 0.1, key="kbv" + k)
        g.eigenkapitalrendite_min = st.slider(
            "min. Eigenkapitalrendite %", 0, 40, round(v.eigenkapitalrendite_min * 100), key="roe" + k) / 100
        g.verschuldung_max = st.slider("max. Verschuldung FK/EK", 0.0, 3.0, float(v.verschuldung_max), 0.1, key="vs" + k)
        g.nettomarge_min = st.slider("min. Nettomarge %", 0, 40, round(v.nettomarge_min * 100), key="nm" + k) / 100
        g.liquiditaet_min = st.slider("min. Current Ratio", 0.5, 3.0, float(v.liquiditaet_min), 0.1, key="cr" + k)
        g.fcf_rendite_min = st.slider("min. FCF-Rendite %", 0, 20, round(v.fcf_rendite_min * 100), key="fcf" + k) / 100
        g.sicherheitsmarge_min = st.slider(
            "min. Sicherheitsmarge %", 0, 60, round(v.sicherheitsmarge_min * 100), key="sm" + k) / 100
        st.caption("DCF-Annahmen")
        g.abzinsung = st.slider("Abzinsung %", 6, 15, 10, key="dz" + k) / 100
        g.wachstum_max = st.slider("max. Wachstum %", 0, 25, 12, key="wm" + k) / 100
    st.caption("Keine Anlageberatung · Daten: Yahoo Finance")

tab_suche, tab_einzel, tab_info = st.tabs(["🔍 Aktien finden", "📊 Einzelanalyse", "ℹ️ So funktioniert's"])

# ---------------------------------------------------------------- Suche
with tab_suche:
    c1, c2, c3 = st.columns([2, 3, 1])
    liste = c1.selectbox("Welche Aktien durchsuchen?", list(LISTEN), key="liste")
    eigene = ""
    if LISTEN[liste] == "eigene":
        eigene = c2.text_input("Ticker, durch Komma getrennt", "AAPL, KO, ALV.DE, BMW.DE, MUV2.DE",
                               help="Deutsche Aktien mit .DE, z. B. SAP.DE")
    c3.write("")
    c3.write("")
    if c3.button("🔍 Suchen", type="primary", width="stretch", key="suchen"):
        quelle = LISTEN[liste]
        if quelle == "demo":
            st.session_state.daten = lade_demo()
        else:
            ticker = ([t.strip().upper() for t in eigene.split(",") if t.strip()]
                      if quelle == "eigene" else INDIZES[quelle])
            with st.spinner(f"Lade {len(ticker)} Aktien … (dauert beim ersten Mal ca. 30 Sek.)"):
                st.session_state.daten = lade_liste(tuple(ticker))
            if not st.session_state.daten:
                st.error("Keine Daten erhalten. Bitte Internetverbindung und Ticker prüfen.")

    daten = st.session_state.get("daten")
    if not daten:
        st.info("👆 Liste wählen und **Suchen** klicken. Die Kriterien stellst du links ein.")
    else:
        ergebnisse = sortiere([bewerte(d, g) for d in daten])
        treffer = [e for e in ergebnisse if e.pflicht_erfuellt]
        m1, m2, m3 = st.columns(3)
        m1.metric("Geprüfte Aktien", len(ergebnisse))
        m2.metric("Erfüllen Pflichtkriterien", len(treffer), help=f"KGV < {g.kgv_max:g} und FCF stets positiv")
        m3.metric("Mit Sicherheitsmarge", sum(1 for e in treffer if e.sicherheitsmarge is not None
                                             and e.sicherheitsmarge >= g.sicherheitsmarge_min))
        alle = st.toggle("Auch Aktien zeigen, die durchfallen", value=not treffer)
        zeigen = ergebnisse if alle else treffer
        if not zeigen:
            st.warning("Keine Aktie erfüllt die Kriterien. Tipp: Strategie "
                       "**Buffett Qualität** wählen oder KGV-Grenze lockern.")
        else:
            zeilen = []
            for e in zeigen:
                z = {"Ticker": e.ticker, "Name": e.name,
                     "Punkte": e.punkte / e.max_punkte * 100,
                     "Kurs": e.kurs, "Innerer Wert": e.innerer_wert,
                     "Sicherheitsmarge": e.sicherheitsmarge * 100 if e.sicherheitsmarge is not None else None,
                     "Währung": e.waehrung, "Pflicht": "✅" if e.pflicht_erfuellt else "❌"}
                for p in e.pruefungen:
                    z[p.name] = f"{SYMBOL[p.bestanden]} {p.wert}"
                zeilen.append(z)
            df = pd.DataFrame(zeilen)
            st.dataframe(
                df, hide_index=True, width="stretch",
                column_config={
                    "Punkte": st.column_config.ProgressColumn(
                        "Punkte", format="%.0f %%", min_value=0, max_value=100,
                        help="Anteil erfüllter Kriterien"),
                    "Kurs": st.column_config.NumberColumn(format="%.2f"),
                    "Innerer Wert": st.column_config.NumberColumn(format="%.2f"),
                    "Sicherheitsmarge": st.column_config.NumberColumn(format="%.0f %%"),
                })
            st.download_button("⬇️ Als CSV (Excel) speichern",
                               df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                               "buffett_treffer.csv", "text/csv")
            st.caption("Tipp: Ticker kopieren und im Tab **Einzelanalyse** genauer ansehen.")

# ---------------------------------------------------------------- Einzelanalyse
with tab_einzel:
    vorschlaege = [d["ticker"] for d in st.session_state.get("daten") or []]
    c1, c2 = st.columns([3, 1])
    eingabe = c1.text_input("Ticker eingeben", key="einzel_ticker",
                            placeholder=", ".join(vorschlaege[:4]) or "z. B. ALV.DE",
                            help="z. B. AAPL, KO, SAP.DE, ALV.DE – oder DEMO1 ohne Internet")
    c2.write("")
    c2.write("")
    c2.button("Analysieren", type="primary", width="stretch")
    ticker = eingabe.strip().upper()
    if not ticker:
        st.info("Ticker eingeben, z. B. **ALV.DE** (Allianz), **KO** (Coca-Cola) oder **SAP.DE**.")
    else:
        with st.spinner("Lade Daten …"):
            kz, verlauf = lade_einzeln(ticker)
        if not kz:
            st.error(f"Keine Daten für **{ticker}** gefunden. Schreibweise prüfen "
                     "(deutsche Aktien mit .DE).")
        else:
            e = bewerte(kz, g)
            w = e.waehrung
            st.subheader(f"{e.name} ({e.ticker})")
            if kz.get("sektor"):
                st.caption(kz["sektor"])

            if e.pflicht_erfuellt and e.punkte >= 8:
                st.success(f"🟢 Starker Buffett-Kandidat: {e.punkte} von {e.max_punkte} Kriterien erfüllt.")
            elif e.pflicht_erfuellt:
                st.warning(f"🟡 Interessant, aber mit Schwächen: {e.punkte} von {e.max_punkte} Kriterien erfüllt.")
            else:
                st.error(f"🔴 Erfüllt die Pflichtkriterien nicht ({e.punkte} von {e.max_punkte} Kriterien).")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Kurs", geld(e.kurs, w))
            m2.metric("Innerer Wert (DCF)", geld(e.innerer_wert, w))
            m3.metric("Sicherheitsmarge", "–" if e.sicherheitsmarge is None else f"{e.sicherheitsmarge * 100:.0f} %",
                      help="Wie weit der Kurs unter dem inneren Wert liegt")
            m4.metric("Börsenwert", geld(kz.get("marktkapitalisierung"), w))

            links, rechts = st.columns([1, 1])
            with links:
                st.markdown("**Checkliste**")
                for p in e.pruefungen:
                    st.markdown(f"{SYMBOL[p.bestanden]} **{p.name}**{' *(Pflicht)*' if p.pflicht else ''} "
                                f"– {p.wert}  \n<small>Regel: {p.regel}</small>",
                                unsafe_allow_html=True)
            with rechts:
                if verlauf is not None:
                    st.markdown("**Kursverlauf 5 Jahre**")
                    st.line_chart(verlauf, height=220)
                fcf, gew = kz.get("fcf_historie") or [], kz.get("gewinn_historie") or []
                n = max(len(fcf), len(gew))
                if n:
                    jahre = kz.get("jahre") or [f"vor {i} J." if i else "letztes J." for i in range(n)]
                    jahre = list(jahre)[:n] + [f"#{i}" for i in range(len(jahre), n)]
                    pad = lambda r: [x / 1e6 for x in r] + [None] * (n - len(r))
                    hist = pd.DataFrame({"Free Cashflow": pad(fcf), "Gewinn": pad(gew)},
                                        index=jahre)[::-1]
                    st.markdown(f"**Free Cashflow & Gewinn (Mio. {w})**")
                    st.bar_chart(hist, height=220, stack=False)

# ---------------------------------------------------------------- Info
with tab_info:
    st.markdown(f"""
### Die Idee
Warren Buffett kauft **gute Unternehmen zu vernünftigen Preisen** und hält sie lange.
Der Finder prüft jede Aktie mit 10 Regeln. Für jede erfüllte Regel gibt es einen Punkt.

| Kriterium | aktuell | Bedeutung |
|---|---|---|
| **KGV** *(Pflicht)* | < {g.kgv_max:g} | Wie viele Jahresgewinne kostet die Aktie? Niedrig = günstig |
| **Free Cashflow** *(Pflicht)* | 3 Jahre > 0 | Bleibt nach allen Investitionen echtes Geld übrig? |
| KBV | < {g.kbv_max:g} | Kurs im Verhältnis zum Buchwert (Eigenkapital) |
| Eigenkapitalrendite | ≥ {g.eigenkapitalrendite_min * 100:.0f} % | Wie gut verzinst die Firma das Geld der Aktionäre? Hoch = Burggraben |
| Verschuldung | ≤ {g.verschuldung_max:g} | Fremdkapital / Eigenkapital. Buffett mag wenig Schulden |
| Nettomarge | ≥ {g.nettomarge_min * 100:.0f} % | Wie viel vom Umsatz bleibt als Gewinn? Hoch = Preissetzungsmacht |
| Current Ratio | ≥ {g.liquiditaet_min:g} | Kann die Firma kurzfristige Schulden bezahlen? |
| FCF-Rendite | ≥ {g.fcf_rendite_min * 100:.0f} % | Free Cashflow im Verhältnis zum Börsenwert |
| Gewinn stabil | 3 Jahre > 0 | Verlässliches Geschäft ohne Verlustjahre |
| Sicherheitsmarge | ≥ {g.sicherheitsmarge_min * 100:.0f} % | Kurs liegt deutlich unter dem inneren Wert |

### Innerer Wert
Geschätzt per **Discounted Cashflow**: der durchschnittliche Free Cashflow der letzten Jahre
wird 10 Jahre in die Zukunft fortgeschrieben (Wachstum gedeckelt bei {g.wachstum_max * 100:.0f} %)
und mit {g.abzinsung * 100:.0f} % auf heute abgezinst.

### Wichtig zu wissen
- **KGV < 10 ist strenger als Buffett selbst.** Er zahlt für Qualität auch mehr.
  Probier die Strategie *Buffett Qualität*.
- **Banken & Versicherungen:** Current Ratio und Verschuldung passen nicht zu ihrem
  Geschäftsmodell. Sie fallen dort oft zu Unrecht durch.
- Yahoo liefert meist nur ~4 Jahre Bilanzdaten. Buffett schaut auf 10 Jahre.
- **Keine Anlageberatung.** Der Finder ersetzt nicht das Lesen der Geschäftsberichte.
""")
