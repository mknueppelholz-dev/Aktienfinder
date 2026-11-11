"""Farben, CSS und kleine HTML-Bausteine für die App."""
import html
import random

ZITATE = [
    "Preis ist, was du zahlst. Wert ist, was du bekommst.",
    "Regel Nr. 1: Verliere niemals Geld. Regel Nr. 2: Vergiss niemals Regel Nr. 1.",
    "Sei ängstlich, wenn andere gierig sind, und gierig, wenn andere ängstlich sind.",
    "Kaufe lieber ein wunderbares Unternehmen zu einem fairen Preis als ein faires "
    "Unternehmen zu einem wunderbaren Preis.",
    "Wenn du eine Aktie nicht zehn Jahre halten willst, denk nicht einmal daran, "
    "sie zehn Minuten zu besitzen.",
    "Die Börse ist ein Instrument, um Geld von den Ungeduldigen zu den Geduldigen zu transferieren.",
    "Risiko entsteht, wenn man nicht weiß, was man tut.",
]

GRUEN, GELB, ROT, GRAU = "#10b981", "#f59e0b", "#ef4444", "#94a3b8"

CSS = """
<style>
/* ---------- Grundlayout ---------- */
.block-container {padding-top: 1.2rem; max-width: 1250px;}
[data-testid="stSidebar"] {background: linear-gradient(180deg,#f5f3ff 0%,#fdf2f8 100%);}

/* ---------- Kopfbanner ---------- */
.hero {background: linear-gradient(120deg,#7c3aed 0%,#db2777 55%,#f59e0b 100%);
  border-radius: 26px; padding: 26px 32px; color: #fff; margin-bottom: 14px;
  box-shadow: 0 12px 30px -12px rgba(124,58,237,.55); position: relative; overflow: hidden;}
.hero:after {content: "📈"; position: absolute; right: 24px; top: -6px; font-size: 120px; opacity: .18;}
.hero h1 {color: #fff; margin: 0; font-size: 2.3rem; font-weight: 800; letter-spacing: -.5px;}
.hero p {margin: 6px 0 0 0; font-size: 1.02rem; opacity: .95; max-width: 760px;}
.hero .zitat {font-style: italic; opacity: .85; font-size: .92rem; margin-top: 10px;}

/* ---------- Knöpfe ---------- */
[data-testid="stBaseButton-primary"] {background: linear-gradient(90deg,#7c3aed,#db2777) !important;
  border: none !important; font-weight: 700 !important; box-shadow: 0 6px 16px -6px #db2777;
  transition: transform .12s ease, box-shadow .12s ease;}
[data-testid="stBaseButton-primary"]:hover {transform: translateY(-2px) scale(1.02);
  box-shadow: 0 10px 22px -8px #7c3aed;}
[data-testid="stBaseButton-secondary"] {transition: transform .12s ease;}
[data-testid="stBaseButton-secondary"]:hover {transform: translateY(-1px);}

/* ---------- Kennzahl-Kacheln ---------- */
[data-testid="stMetric"] {background: #fff; border-radius: 20px; padding: 14px 18px;
  box-shadow: 0 4px 14px -6px rgba(15,23,42,.18); border-top: 5px solid #a78bfa;}
[data-testid="stColumn"]:nth-child(2) [data-testid="stMetric"] {border-top-color: #f472b6;}
[data-testid="stColumn"]:nth-child(3) [data-testid="stMetric"] {border-top-color: #fbbf24;}
[data-testid="stColumn"]:nth-child(4) [data-testid="stMetric"] {border-top-color: #34d399;}

/* ---------- Ergebnis-Karten ---------- */
[class*="st-key-karte_"] {background: #fff; border-radius: 22px; padding: 16px 16px 10px 16px;
  box-shadow: 0 6px 18px -8px rgba(15,23,42,.25); border: 2px solid transparent;
  transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;}
[class*="st-key-karte_"]:hover {transform: translateY(-4px); border-color: #c4b5fd;
  box-shadow: 0 14px 28px -10px rgba(124,58,237,.45);}
.k-kopf {display: flex; align-items: center; gap: 8px;}
.k-flagge {font-size: 1.6rem;}
.k-ticker {font-weight: 800; font-size: 1.05rem; color: #4c1d95;}
.k-name {color: #475569; font-size: .88rem; margin: 2px 0 10px 0; height: 2.5em; overflow: hidden;}
.k-werte {display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px;}
.chip {background: #f1f5f9; border-radius: 999px; padding: 3px 10px; font-size: .8rem; color: #334155;}
.chip b {color: #0f172a;}
.chip.gut {background: #d1fae5; color: #065f46;} .chip.schlecht {background: #fee2e2; color: #991b1b;}
.score {margin-left: auto; color: #fff; font-weight: 800; border-radius: 999px; padding: 3px 12px;
  font-size: .9rem;}

/* ---------- Score-Ring & Abzeichen ---------- */
.ring {width: 170px; height: 170px; border-radius: 50%; margin: 6px auto;
  background: conic-gradient(var(--c) calc(var(--p) * 1%), #e2e8f0 0);
  display: flex; align-items: center; justify-content: center;}
.ring > div {width: 128px; height: 128px; border-radius: 50%; background: #fff;
  display: flex; flex-direction: column; align-items: center; justify-content: center;}
.ring b {font-size: 2.6rem; line-height: 1; color: var(--c);}
.ring small {color: #64748b; font-size: .78rem;}
.abzeichen {display: flex; flex-wrap: wrap; gap: 8px; margin: 6px 0 14px 0;}
.abz {border-radius: 16px; padding: 8px 14px; font-weight: 700; font-size: .9rem;}
.abz.an {background: linear-gradient(90deg,#fef3c7,#fde68a); color: #78350f;
  box-shadow: 0 4px 10px -5px #f59e0b;}
.abz.aus {background: #f1f5f9; color: #94a3b8; filter: grayscale(1);}
.pruef {background: #fff; border-radius: 14px; padding: 9px 14px; margin-bottom: 7px;
  border-left: 6px solid var(--c); box-shadow: 0 2px 8px -4px rgba(15,23,42,.18);}
.pruef small {color: #64748b;}
.urteil {border-radius: 18px; padding: 14px 18px; color: #fff; font-weight: 700; font-size: 1.05rem;}
</style>
"""


def hero(untertitel: str) -> str:
    return (f'<div class="hero"><h1>Buffett-Finder</h1><p>{untertitel}</p>'
            f'<div class="zitat">„{random.choice(ZITATE)}“ – Warren Buffett</div></div>')


def farbe(score: float | None) -> str:
    if score is None:
        return GRAU
    return GRUEN if score >= 70 else GELB if score >= 40 else ROT


def karte_html(flagge: str, ticker: str, name: str, chips: list[tuple[str, str, bool | None]],
               score: float | None = None) -> str:
    badge = (f'<span class="score" style="background:{farbe(score)}">{score:.0f}</span>'
             if score is not None else "")
    chip_html = "".join(
        f'<span class="chip {"gut" if ok else "schlecht" if ok is False else ""}">'
        f'{html.escape(label)} <b>{html.escape(wert)}</b></span>' for label, wert, ok in chips)
    return (f'<div class="k-kopf"><span class="k-flagge">{flagge}</span>'
            f'<span class="k-ticker">{html.escape(ticker)}</span>{badge}</div>'
            f'<div class="k-name">{html.escape(name)}</div><div class="k-werte">{chip_html}</div>')


def ring_html(score: float) -> str:
    return (f'<div class="ring" style="--p:{score:.0f};--c:{farbe(score)}"><div>'
            f'<b>{score:.0f}</b><small>Buffett-Score</small></div></div>')


def abzeichen_html(liste: list[tuple[str, bool]]) -> str:
    return '<div class="abzeichen">' + "".join(
        f'<span class="abz {"an" if an else "aus"}">{html.escape(t)}</span>' for t, an in liste) + "</div>"


def pruef_html(symbol: str, name: str, wert: str, regel: str, ok: bool | None, pflicht: bool) -> str:
    c = GRUEN if ok else ROT if ok is False else GRAU
    p = " · <small>Pflicht</small>" if pflicht else ""
    return (f'<div class="pruef" style="--c:{c}">{symbol} <b>{html.escape(name)}</b>{p}'
            f' — {html.escape(wert)}<br><small>Regel: {html.escape(regel)}</small></div>')
