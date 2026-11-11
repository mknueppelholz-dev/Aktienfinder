import unittest

from daten import lade_demo
from finder import main
from kriterien import Grenzwerte, bewerte, innerer_wert_dcf, wachstumsrate


class TestKriterien(unittest.TestCase):
    def setUp(self):
        self.demo = {d["ticker"]: d for d in lade_demo()}

    def test_solide_aktie_besteht_alles(self):
        e = bewerte(self.demo["DEMO1"])
        self.assertTrue(e.pflicht_erfuellt)
        self.assertEqual(e.punkte, e.max_punkte, [p for p in e.pruefungen if not p.bestanden])

    def test_verschuldete_aktie_faellt_durch(self):
        e = bewerte(self.demo["DEMO2"])
        self.assertFalse(e.pflicht_erfuellt)  # FCF war negativ
        self.assertLess(e.punkte, 4)

    def test_teure_aktie_scheitert_am_kgv(self):
        e = bewerte(self.demo["DEMO3"])
        self.assertFalse(e.pflicht_erfuellt)
        self.assertTrue(bewerte(self.demo["DEMO3"], Grenzwerte(kgv_max=40)).pflicht_erfuellt)

    def test_fehlende_daten_sind_kein_bestanden(self):
        e = bewerte({"ticker": "X"})
        self.assertEqual(e.punkte, 0)
        self.assertEqual(e.datenluecken, e.max_punkte)
        self.assertFalse(e.pflicht_erfuellt)

    def test_negatives_kgv_faellt_durch(self):
        self.assertFalse(bewerte({"ticker": "X", "kgv": -3}).pruefungen[0].bestanden)

    def test_wachstumsrate(self):
        self.assertAlmostEqual(wachstumsrate([121, 110, 100]), 0.10)
        self.assertIsNone(wachstumsrate([100, -5]))

    def test_dcf_plausibel(self):
        iw = innerer_wert_dcf(self.demo["DEMO1"], Grenzwerte())
        self.assertGreater(iw, 40)    # günstig bewertet
        self.assertLess(iw, 200)

    def test_cli_demo(self):
        self.assertEqual(main(["--demo"]), 0)


if __name__ == "__main__":
    unittest.main()
