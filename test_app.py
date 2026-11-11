"""App-Tests ohne Internet: Yahoo wird durch Beispieldaten ersetzt."""
import unittest
from unittest import mock

import yfinance as yf
from streamlit.testing.v1 import AppTest

from kriterien import Grenzwerte
from welt import baue_query, scanne

FAKE = [{"symbol": s, "longName": n, "regularMarketPrice": p, "currency": c, "trailingPE": pe,
         "priceToBook": pb, "marketCap": mc, "fullExchangeName": ex}
        for s, n, p, c, pe, pb, mc, ex in [
            ("ALV.DE", "Allianz SE", 350, "EUR", 9.5, 1.4, 1.3e11, "XETRA"),
            ("7203.T", "Toyota Motor", 2800, "JPY", 8.1, 1.0, 4.4e13, "Tokyo"),
            ("KO", "Coca-Cola", 70, "USD", 9.9, 1.2, 3e11, "NYSE"),
        ] * 100]


def fake_screen(query, offset=0, size=100, **kw):
    return {"quotes": FAKE[offset:offset + size], "total": len(FAKE)}


class TestWelt(unittest.TestCase):
    def test_query_struktur(self):
        q = baue_query(Grenzwerte(), ["kgv", "roe", "fcf"], ["de", "us"], 1e9).to_dict()
        self.assertEqual(q["operator"], "AND")
        felder = [o["operands"][0] for o in q["operands"] if o["operator"] != "OR"]
        self.assertIn("peratio.lasttwelvemonths", felder)
        self.assertIn(["returnonequity.lasttwelvemonths", 15.0],
                      [o["operands"] for o in q["operands"]])

    def test_query_minimal(self):
        self.assertEqual(baue_query(Grenzwerte(), [], [], 0).to_dict()["operator"], "GT")
        self.assertEqual(baue_query(Grenzwerte(), [], ["de"], 0).to_dict()["operator"], "EQ")

    def test_scanne_blaettert(self):
        with mock.patch.object(yf, "screen", side_effect=fake_screen) as m:
            treffer, gesamt = scanne(baue_query(Grenzwerte(), ["kgv"], [], 0), 260)
        self.assertEqual((len(treffer), gesamt, m.call_count), (260, 300, 2))
        self.assertEqual(treffer[1]["flagge"], "🇯🇵")


class TestApp(unittest.TestCase):
    def setUp(self):
        self.at = AppTest.from_file("app.py", default_timeout=30)
        self.at.run()
        self.assertFalse(self.at.exception)

    def test_welt_scanner(self):
        at = self.at
        with mock.patch.object(yf, "screen", side_effect=fake_screen):
            at.button(key="welt_start").click().run()
        self.assertFalse(at.exception, at.exception)
        self.assertEqual(at.metric[0].value, "300")
        at.button(key="an_welt_1").click().run()  # Karte "Analysieren" → Einzelanalyse
        self.assertEqual(at.session_state.seite, "🔬 Einzelanalyse")
        self.assertEqual(at.text_input(key="einzel_ticker").value, "7203.T")
        at.session_state.seite = "🌍 Welt-Scanner"
        at.run()
        at.segmented_control(key="welt_ansicht").set_value("📋 Tabelle").run()
        self.assertFalse(at.exception, at.exception)

    def test_einzel_und_strategien(self):
        at = self.at
        at.segmented_control(key="seite").set_value("🔬 Einzelanalyse").run()
        at.text_input(key="einzel_ticker").set_value("DEMO1").run()
        self.assertFalse(at.exception, at.exception)
        self.assertIn("Starker Buffett-Kandidat", "".join(m.value for m in at.markdown))
        for s in ["💎 Buffett Qualität", "🔎 Graham Deep Value", "🎈 Locker"]:
            at.pills(key="strategie").set_value(s).run()
            self.assertFalse(at.exception, at.exception)

    def test_index_demo_und_lexikon(self):
        at = self.at
        at.segmented_control(key="seite").set_value("🏆 Index-Check").run()
        at.pills(key="liste").set_value("🧪 Demo").run()
        at.button(key="suchen").click().run()
        self.assertFalse(at.exception, at.exception)
        self.assertEqual(at.metric[1].value, "2")
        at.segmented_control(key="idx_ansicht").set_value("📋 Tabelle").run()
        self.assertFalse(at.exception, at.exception)
        at.segmented_control(key="seite").set_value("📚 Lexikon").run()
        self.assertFalse(at.exception, at.exception)


if __name__ == "__main__":
    unittest.main()
