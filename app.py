"""Buffett-Finder – Web-App.  Start: streamlit run app.py"""
from dataclasses import replace

import pandas as pd
import streamlit as st

import stil
from daten import INDIZES, hole_kennzahlen, hole_kursverlauf, hole_viele, lade_demo
from finder import sortiere
from kriterien import Ergebnis, Grenzwerte, bewerte
from welt import KRITERIEN, REGIONEN, STANDARD_AKTIV, baue_query, scanne

st.set_page_config(page_title="Buffett-Finder", page_icon="📈", layout="wide")
st.markdown(stil.CSS, unsafe_allow_html=True)

SEITEN = ["🌍 Welt-Scanner", "🏆 Index-Check", "🔬 Einzelanalyse", "📚 Lexikon"]

VORLAGEN = {
    "🎩 Buffett streng": Grenzwerte(),
    "💎 Buffett Qualität": Grenzwerte(kgv_max=20, kbv_max=5, sicherheitsmarge_min=0.15,
                                      fcf_rendite_min=0.04),
    "🔎 Graham Deep Value": Grenzwerte(kgv_max=12, kbv_max=1.0, eigenkapitalrendite_min=0.08,
                                       nettomarge_min=0.05, liquiditaet_min=2.0,
                                       sicherheitsmarge_min=0.33),
    "🎈 Locker": Grenzwerte(kgv_max=40, kbv_max=10, eigenkapitalrendite_min=0,
                           verschuldung_max=3, nettomarge_min=0, liquiditaet_min=0.5,
                           fcf_rendite_min=0, sicherheitsmarge_min=0),
}

SCHNELLWAHL = {
    "🇩🇪 Allianz": "ALV.DE", "🇩🇪 Münchener Rück": "MUV2.DE", "🇩🇪 Mercedes": "MBG.DE",
    "🇺🇸 Coca-Cola": "KO", "🇺🇸 Apple": "AAPL", "🇺🇸 Berkshire": "BRK-B",
    "🧪 Demo": "DEMO1",
}

INDEX_LISTEN = {"🇩🇪 DAX 40": "dax", "🇺🇸 Dow Jones 30": "dow", "💎 Value-Klassiker": "value",
                "✏️ Eigene Ticker": "eigene", "🧪 Demo": "demo"}

st.session_state.setdefault("seite", SEITEN[0])
st.session_state.setdefault("gefeiert", set())


# ---------------------------------------------------------------- Hilfen
def de(z: float | None, n: int = 2) -> str:
    if z is None:
        return "–"
    return f"{z:,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def geld(x: float | None, w: str = "") -> str:
    if x is None:
        return "–"
    for grenze, endung in ((1e12, "Bio."), (1e9, "Mrd."), (1e6, "Mio.")):
        if abs(x) >= grenze:
            return f"{de(x / grenze, 1)} {endung} {w}".strip()
    return f"{de(x)} {w}".strip()


def score(e: Ergebnis) -> float:
    return e.punkte / e.max_punkte * 100


def analysiere(ticker: str):
    """Callback der 'Analysieren'-Knöpfe: springt zur Einzelanalyse."""
    st.session_state.einzel_ticker = ticker
    st.session_state.seite = SEITEN[2]


def schnellwahl():
    wahl = st.session_state.get("schnellwahl")
    if wahl:
        st.session_state.einzel_ticker = SCHNELLWAHL[wahl]


@st.cache_data(ttl=3600, show_spinner=False)
def lade_liste(ticker: tuple[str, ...]):
    return hole_viele(list(ticker))


@st.cache_data(ttl=3600, show_spinner=False)
def lade_einzeln(ticker: str):
    if ticker.startswith("DEMO"):
        return next((d for d in lade_demo() if d["ticker"] == ticker), None), None
    return hole_kennzahlen(ticker), hole_kursverlauf(ticker)


@st.cache_data(ttl=1800, show_spinner=False)
def welt_scan(g_tuple, aktiv, regionen, min_mcap, anzahl):
    g = Grenzwerte(*g_tuple)
    return scanne(baue_query(g, list(aktiv), list(regionen), min_mcap), anzahl)


def karten_raster(eintraege: list[dict], praefix: str, spalten: int = 3):
    """eintraege: dicts mit flagge, ticker, name, chips, score."""
    for start in range(0, len(eintraege), spalten):
        cols = st.columns(spalten)
        for col, (i, e) in zip(cols, enumerate(eintraege[start:start + spalten], start)):
            with col, st.container(key=f"karte_{praefix}_{i}"):
                st.markdown(stil.karte_html(e["flagge"], e["ticker"], e["name"], e["chips"],
                                            e.get("score")), unsafe_allow_html=True)
                st.button("🔬 Analysieren", key=f"an_{praefix}_{i}", on_click=analysiere,
                          args=(e["ticker"],), width="stretch")


# ---------------------------------------------------------------- Seitenleiste
with st.sidebar:
    st.markdown("### 🎯 Deine Strategie")
    vorlage = st.pills("Strategie", list(VORLAGEN), default=list(VORLAGEN)[0],
                       key="strategie", label_visibility="collapsed") or list(VORLAGEN)[0]
    v = VORLAGEN[vorlage]
    k = f"_{vorlage}"  # Regler springen bei Strategiewechsel auf deren Werte
    g = replace(v)
    with st.expander("🎚️ Feinjustieren"):
        g.kgv_max = st.slider("max. KGV", 3.0, 40.0, float(v.kgv_max), 0.5, key="kgv" + k)
        g.kbv_max = st.slider("max. KBV", 0.5, 10.0, float(v.kbv_max), 0.1, key="kbv" + k)
        g.eigenkapitalrendite_min = st.slider(
            "min. Eigenkapitalrendite %", 0, 40, round(v.eigenkapitalrendite_min * 100), key="roe" + k) / 100
        g.verschuldung_max = st.slider("max. Verschuldung FK/EK", 0.0, 3.0,
                                       float(v.verschuldung_max), 0.1, key="vs" + k)
        g.nettomarge_min = st.slider("min. Nettomarge %", 0, 40, round(v.nettomarge_min * 100), key="nm" + k) / 100
        g.liquiditaet_min = st.slider("min. Current Ratio", 0.5, 3.0, float(v.liquiditaet_min), 0.1, key="cr" + k)
        g.fcf_rendite_min = st.slider("min. FCF-Rendite %", 0, 20, round(v.fcf_rendite_min * 100), key="fcf" + k) / 100
        g.sicherheitsmarge_min = st.slider(
            "min. Sicherheitsmarge %", 0, 60, round(v.sicherheitsmarge_min * 100), key="sm" + k) / 100
        st.caption("DCF-Annahmen")
        g.abzinsung = st.slider("Abzinsung %", 6, 15, 10, key="dz" + k) / 100
        g.wachstum_max = st.slider("max. Wachstum %", 0, 25, 12, key="wm" + k) / 100
    st.markdown(
        f"<small>🏷️ KGV &lt; {de(g.kgv_max, 1)} · 🏰 EK-Rendite ≥ {g.eigenkapitalrendite_min:.0%} · "
        f"🛡️ FK/EK ≤ {de(g.verschuldung_max, 1)} · 💎 Marge ≥ {g.nettomarge_min:.0%}</small>",
        unsafe_allow_html=True)
    st.divider()
    st.caption("Keine Anlageberatung · Daten: Yahoo Finance")

# ---------------------------------------------------------------- Kopf + Navigation
st.markdown(stil.hero("Finde unterbewertete Qualitätsaktien – weltweit, nach den Regeln "
                      "des erfolgreichsten Investors der Welt."), unsafe_allow_html=True)
seite = st.segmented_control("Navigation", SEITEN, key="seite", label_visibility="collapsed",
                             width="stretch") or SEITEN[0]
st.write("")

# ================================================================ Welt-Scanner
if seite == SEITEN[0]:
    st.markdown("#### 1️⃣ Wo suchen?")
    ganze_welt = st.toggle("🌍 Ganze Welt (alle Börsen)", value=True, key="ganze_welt")
    regionen = []
    if not ganze_welt:
        regionen = st.pills("Länder", list(REGIONEN), selection_mode="multi", default=["de", "us"],
                            format_func=lambda r: f"{REGIONEN[r][0]} {REGIONEN[r][1]}",
                            key="regionen", label_visibility="collapsed") or []

    st.markdown("#### 2️⃣ Welche Buffett-Regeln?")
    aktiv = st.pills("Regeln", list(KRITERIEN), selection_mode="multi", default=STANDARD_AKTIV,
                     format_func=KRITERIEN.get, key="regeln", label_visibility="collapsed") or []
    st.caption("Grenzwerte kommen aus deiner Strategie links. Jede eingeschaltete Regel muss erfüllt sein.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 3️⃣ Firmengröße")
        groessen = {"🐜 Alle": 0, "🐇 > 100 Mio.": 1e8, "🐎 > 1 Mrd.": 1e9, "🐘 > 10 Mrd.": 1e10}
        groesse = st.segmented_control("Größe", list(groessen), default="🐎 > 1 Mrd.",
                                       key="groesse", label_visibility="collapsed") or "🐜 Alle"
    with c2:
        st.markdown("#### 4️⃣ Wie viele Treffer laden?")
        anzahl = st.segmented_control("Anzahl", [100, 250, 500, 1000], default=250,
                                      key="anzahl", label_visibility="collapsed") or 250

    if st.button("🚀 Welt scannen!", type="primary", width="stretch", key="welt_start"):
        if not ganze_welt and not regionen:
            st.warning("Bitte mindestens ein Land auswählen oder „Ganze Welt“ einschalten.")
        else:
            with st.spinner("🌍 Durchsuche alle Börsen der Welt …"):
                try:
                    st.session_state.welt = welt_scan(
                        tuple(vars(g).values()), tuple(aktiv), tuple(regionen),
                        groessen[groesse], anzahl)
                    st.session_state.pop("welt_scores", None)
                except Exception as fehler:
                    st.session_state.pop("welt", None)
                    st.error(f"Yahoo hat nicht geantwortet ({type(fehler).__name__}). "
                             "Bitte in einer Minute noch einmal versuchen.")

    if "welt" in st.session_state:
        treffer, gesamt = st.session_state.welt
        st.divider()
        if not treffer:
            st.warning("😕 Keine Aktie erfüllt alle Regeln. Schalte eine Regel aus "
                       "oder wähle links die Strategie **🎈 Locker**.")
        else:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🎯 Treffer weltweit", f"{gesamt:,}".replace(",", "."))
            m2.metric("📥 Geladen", len(treffer))
            laender = pd.Series([t["flagge"] for t in treffer]).value_counts()
            m3.metric("🌍 Länder", len(laender), help=" ".join(f"{f}×{n}" for f, n in laender.items()))
            kgvs = [t["kgv"] for t in treffer if t["kgv"]]
            m4.metric("🏷️ Ø KGV", de(sum(kgvs) / len(kgvs), 1) if kgvs else "–")

            scores: dict = st.session_state.get("welt_scores", {})
            b1, b2 = st.columns([2, 3])
            if b1.button("⚡ Buffett-Score für die Top 21 berechnen", key="welt_score",
                         help="Lädt Bilanzdaten und berechnet DCF & Sicherheitsmarge"):
                with st.spinner("Rechne Buffett-Scores …"):
                    daten = lade_liste(tuple(t["ticker"] for t in treffer[:21]))
                st.session_state.welt_scores = scores = {
                    d["ticker"]: bewerte(d, g) for d in daten}
                st.toast(f"⚡ {len(scores)} Scores berechnet!")
            ansicht = b2.segmented_control("Ansicht", ["🃏 Karten", "📋 Tabelle"], default="🃏 Karten",
                                           key="welt_ansicht", label_visibility="collapsed")

            if ansicht == "📋 Tabelle":
                df = pd.DataFrame([{
                    "": t["flagge"], "Ticker": t["ticker"], "Name": t["name"], "Börse": t["boerse"],
                    "Kurs": t["kurs"], "Währung": t["waehrung"], "KGV": t["kgv"], "KBV": t["kbv"],
                    "Börsenwert (Mrd.)": t["marktkapitalisierung"] / 1e9 if t["marktkapitalisierung"] else None,
                    "Score": score(scores[t["ticker"]]) if t["ticker"] in scores else None,
                } for t in treffer])
                st.dataframe(df, hide_index=True, width="stretch", height=560, column_config={
                    "Kurs": st.column_config.NumberColumn(format="%.2f"),
                    "KGV": st.column_config.NumberColumn(format="%.1f"),
                    "KBV": st.column_config.NumberColumn(format="%.2f"),
                    "Börsenwert (Mrd.)": st.column_config.NumberColumn(format="%.1f"),
                    "Score": st.column_config.ProgressColumn(format="%.0f", min_value=0, max_value=100),
                })
                st.download_button("⬇️ Als CSV (Excel) speichern",
                                   df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                                   "buffett_welt.csv", "text/csv")
            else:
                n = st.session_state.get("welt_n", 21)
                eintraege = []
                for t in treffer[:n]:
                    e = scores.get(t["ticker"])
                    chips = [("KGV", de(t["kgv"], 1), None), ("KBV", de(t["kbv"], 1), None),
                             ("💰", geld(t["marktkapitalisierung"], t["waehrung"]), None)]
                    if e and e.sicherheitsmarge is not None:
                        chips.append(("Marge", f"{e.sicherheitsmarge:.0%}",
                                      e.sicherheitsmarge >= g.sicherheitsmarge_min))
                    eintraege.append({**t, "chips": chips, "score": score(e) if e else None})
                karten_raster(eintraege, "welt")
                if n < len(treffer):
                    if st.button(f"➕ Mehr zeigen ({len(treffer) - n} weitere)", key="welt_mehr"):
                        st.session_state.welt_n = n + 21
                        st.rerun()

# ================================================================ Index-Check
elif seite == SEITEN[1]:
    c1, c2 = st.columns([1, 2])
    liste = c1.pills("Liste", list(INDEX_LISTEN), default="🇩🇪 DAX 40", key="liste",
                     label_visibility="collapsed") or "🇩🇪 DAX 40"
    eigene = ""
    if INDEX_LISTEN[liste] == "eigene":
        eigene = c2.text_input("Ticker, durch Komma getrennt", "AAPL, KO, ALV.DE, BMW.DE, MUV2.DE",
                               help="Deutsche Aktien mit .DE, z. B. SAP.DE")
    if st.button("🏁 Komplett-Check starten", type="primary", width="stretch", key="suchen"):
        quelle = INDEX_LISTEN[liste]
        if quelle == "demo":
            st.session_state.daten = lade_demo()
        else:
            ticker = ([t.strip().upper() for t in eigene.split(",") if t.strip()]
                      if quelle == "eigene" else INDIZES[quelle])
            with st.spinner(f"Prüfe {len(ticker)} Aktien auf alle 10 Regeln …"):
                st.session_state.daten = lade_liste(tuple(ticker))
            if not st.session_state.daten:
                st.error("Keine Daten erhalten. Bitte Internetverbindung und Ticker prüfen.")

    daten = st.session_state.get("daten")
    if daten:
        ergebnisse = sortiere([bewerte(d, g) for d in daten])
        treffer = [e for e in ergebnisse if e.pflicht_erfuellt]
        m1, m2, m3 = st.columns(3)
        m1.metric("🔍 Geprüft", len(ergebnisse))
        m2.metric("✅ Pflicht erfüllt", len(treffer), help=f"KGV < {g.kgv_max:g} und FCF stets positiv")
        m3.metric("🛡️ Mit Sicherheitsmarge", sum(1 for e in treffer if e.sicherheitsmarge is not None
                                                 and e.sicherheitsmarge >= g.sicherheitsmarge_min))
        alle = st.toggle("Auch Aktien zeigen, die durchfallen", value=not treffer, key="idx_alle")
        zeigen = ergebnisse if alle else treffer
        if not zeigen:
            st.warning("😕 Keine Aktie erfüllt die Kriterien. Tipp: Strategie **💎 Buffett Qualität** wählen.")
        else:
            ansicht = st.segmented_control("Ansicht", ["🃏 Karten", "📋 Tabelle"], default="🃏 Karten",
                                           key="idx_ansicht", label_visibility="collapsed")
            if ansicht == "📋 Tabelle":
                zeilen = []
                for e in zeigen:
                    z = {"Ticker": e.ticker, "Name": e.name, "Score": score(e), "Kurs": e.kurs,
                         "Innerer Wert": e.innerer_wert,
                         "Sicherheitsmarge": e.sicherheitsmarge * 100 if e.sicherheitsmarge is not None else None,
                         "Währung": e.waehrung}
                    for p in e.pruefungen:
                        z[p.name] = {True: "✅", False: "❌", None: "❔"}[p.bestanden] + " " + p.wert
                    zeilen.append(z)
                df = pd.DataFrame(zeilen)
                st.dataframe(df, hide_index=True, width="stretch", column_config={
                    "Score": st.column_config.ProgressColumn(format="%.0f", min_value=0, max_value=100),
                    "Kurs": st.column_config.NumberColumn(format="%.2f"),
                    "Innerer Wert": st.column_config.NumberColumn(format="%.2f"),
                    "Sicherheitsmarge": st.column_config.NumberColumn(format="%.0f %%"),
                })
                st.download_button("⬇️ Als CSV (Excel) speichern",
                                   df.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                                   "buffett_index.csv", "text/csv")
            else:
                from welt import flagge
                eintraege = [{
                    "flagge": flagge(e.ticker), "ticker": e.ticker, "name": e.name,
                    "score": score(e),
                    "chips": [(p.name.split(" (")[0], p.wert, p.bestanden) for p in e.pruefungen
                              if p.name in ("KGV", "Eigenkapitalrendite", "Verschuldungsgrad",
                                            "Sicherheitsmarge (DCF)")],
                } for e in zeigen]
                karten_raster(eintraege, "idx")
    else:
        st.info("👆 Liste wählen und **Komplett-Check** starten. Hier wird jede Aktie mit allen "
                "10 Regeln inklusive innerem Wert geprüft.")

# ================================================================ Einzelanalyse
elif seite == SEITEN[2]:
    st.pills("Schnellwahl", list(SCHNELLWAHL), key="schnellwahl", on_change=schnellwahl,
             label_visibility="collapsed")
    eingabe = st.text_input("Ticker eingeben", key="einzel_ticker", placeholder="z. B. ALV.DE, KO, 7203.T",
                            help="Deutsche Aktien mit .DE, Japan mit .T, London mit .L …")
    ticker = (eingabe or "").strip().upper()
    if not ticker:
        st.info("👆 Wähle oben eine Aktie oder gib einen Ticker ein. Im **🌍 Welt-Scanner** "
                "kannst du bei jeder Karte auf **Analysieren** klicken.")
    else:
        with st.spinner("Lade Daten …"):
            kz, verlauf = lade_einzeln(ticker)
        if not kz:
            st.error(f"🤷 Keine Daten für **{ticker}** gefunden. Schreibweise prüfen.")
        else:
            e = bewerte(kz, g)
            s = score(e)
            ok = {p.name: p.bestanden for p in e.pruefungen}
            w = e.waehrung

            links, rechts = st.columns([1, 2.4])
            with links:
                st.markdown(stil.ring_html(s), unsafe_allow_html=True)
            with rechts:
                st.markdown(f"## {e.name}")
                st.caption(f"{e.ticker}" + (f" · {kz['sektor']}" if kz.get("sektor") else ""))
                if e.pflicht_erfuellt and s >= 80:
                    urteil, farbe = "🟢 Starker Buffett-Kandidat!", stil.GRUEN
                elif e.pflicht_erfuellt:
                    urteil, farbe = "🟡 Interessant, aber mit Schwächen", stil.GELB
                else:
                    urteil, farbe = "🔴 Erfüllt die Pflichtregeln nicht", stil.ROT
                st.markdown(f'<div class="urteil" style="background:{farbe}">{urteil} · '
                            f'{e.punkte} von {e.max_punkte} Regeln erfüllt</div>', unsafe_allow_html=True)
                st.markdown(stil.abzeichen_html([
                    ("🏷️ Schnäppchen", bool(ok["KGV"])),
                    ("🏰 Burggraben", bool(ok["Eigenkapitalrendite"] and ok["Nettomarge"])),
                    ("🛡️ Festung", bool(ok["Verschuldungsgrad"] and ok["Liquidität (Current Ratio)"])),
                    ("💰 Cash-Maschine", bool(ok["Free Cashflow stets positiv"] and ok["FCF-Rendite"])),
                    ("📈 Verlässlich", bool(ok["Gewinn stabil"])),
                    ("🎯 Sicherheitsmarge", bool(ok["Sicherheitsmarge (DCF)"])),
                ]), unsafe_allow_html=True)

            if e.pflicht_erfuellt and s >= 80 and ticker not in st.session_state.gefeiert:
                st.session_state.gefeiert.add(ticker)
                st.balloons()

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("💶 Kurs", geld(e.kurs, w))
            m2.metric("💎 Innerer Wert", geld(e.innerer_wert, w))
            m3.metric("🛡️ Sicherheitsmarge",
                      "–" if e.sicherheitsmarge is None else f"{e.sicherheitsmarge * 100:.0f} %",
                      help="Wie weit der Kurs unter dem inneren Wert liegt")
            m4.metric("🏢 Börsenwert", geld(kz.get("marktkapitalisierung"), w))

            st.write("")
            links, rechts = st.columns([1, 1])
            with links:
                st.markdown("#### ✅ Checkliste")
                symbole = {True: "✅", False: "❌", None: "❔"}
                st.markdown("".join(stil.pruef_html(symbole[p.bestanden], p.name, p.wert, p.regel,
                                                    p.bestanden, p.pflicht) for p in e.pruefungen),
                            unsafe_allow_html=True)
            with rechts:
                if verlauf is not None:
                    st.markdown("#### 📉 Kursverlauf 5 Jahre")
                    st.area_chart(verlauf, height=230, color="#7c3aed")
                fcf, gew = kz.get("fcf_historie") or [], kz.get("gewinn_historie") or []
                n = max(len(fcf), len(gew))
                if n:
                    jahre = kz.get("jahre") or [f"vor {i} J." if i else "letztes J." for i in range(n)]
                    jahre = list(jahre)[:n] + [f"#{i}" for i in range(len(jahre), n)]
                    pad = lambda r: [x / 1e6 for x in r] + [None] * (n - len(r))
                    hist = pd.DataFrame({"Free Cashflow": pad(fcf), "Gewinn": pad(gew)}, index=jahre)[::-1]
                    st.markdown(f"#### 💰 Free Cashflow & Gewinn (Mio. {w})")
                    st.bar_chart(hist, height=230, stack=False, color=["#10b981", "#f59e0b"])

# ================================================================ Lexikon
else:
    karten = [
        ("🏷️", "KGV", f"Kurs ÷ Gewinn je Aktie. Wie viele Jahresgewinne kostet die Aktie? "
                     f"Deine Grenze: unter {de(g.kgv_max, 1)}. **Pflichtregel.**"),
        ("💰", "Free Cashflow", "Geld, das nach allen Investitionen übrig bleibt. Muss 3 Jahre "
                               "in Folge positiv sein. **Pflichtregel.**"),
        ("📘", "KBV", f"Kurs ÷ Buchwert. Unter {de(g.kbv_max, 1)} heißt: man zahlt kaum mehr als "
                     "das Eigenkapital wert ist."),
        ("🏰", "Eigenkapitalrendite", f"Wie gut verzinst die Firma das Geld der Aktionäre? "
                                     f"Ab {g.eigenkapitalrendite_min:.0%} ein Hinweis auf einen Burggraben."),
        ("🛡️", "Verschuldung", f"Fremdkapital ÷ Eigenkapital. Buffett mag wenig Schulden: "
                              f"höchstens {de(g.verschuldung_max, 1)}."),
        ("💎", "Nettomarge", f"Wie viel vom Umsatz bleibt als Gewinn? Ab {g.nettomarge_min:.0%} "
                            "spricht das für Preissetzungsmacht."),
        ("💧", "Current Ratio", f"Kurzfristiges Vermögen ÷ kurzfristige Schulden. "
                               f"Ab {de(g.liquiditaet_min, 1)} ist die Firma gut zahlungsfähig."),
        ("📊", "FCF-Rendite", f"Free Cashflow ÷ Börsenwert. Ab {g.fcf_rendite_min:.0%} "
                             "bekommst du viel Cash für dein Geld."),
        ("📈", "Gewinnstabilität", "Keine Verlustjahre in den letzten 3 Jahren."),
        ("🎯", "Sicherheitsmarge", f"Der Kurs liegt mind. {g.sicherheitsmarge_min:.0%} unter dem "
                                  "inneren Wert (DCF). Puffer gegen Fehleinschätzungen."),
    ]
    for start in range(0, len(karten), 2):
        cols = st.columns(2)
        for col, (i, (emoji, titel, text)) in zip(cols, enumerate(karten[start:start + 2], start)):
            with col, st.container(key=f"karte_lex_{i}"):
                st.markdown(f"### {emoji} {titel}\n{text}")
    st.info("**Wichtig:** KGV < 10 ist strenger als Buffett selbst. Er zahlt für Qualität auch mehr. "
            "Banken & Versicherungen fallen bei Verschuldung/Liquidität oft zu Unrecht durch. "
            "**Keine Anlageberatung.**")
