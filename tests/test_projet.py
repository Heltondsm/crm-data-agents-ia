"""Tests lancés automatiquement à chaque push (GitHub Actions)."""
import json, pathlib, py_compile, re, subprocess, sys, unittest

RACINE = pathlib.Path(__file__).resolve().parent.parent


class TestCode(unittest.TestCase):
    def test_scripts_python_compilent(self):
        for f in RACINE.rglob("*.py"):
            py_compile.compile(str(f), doraise=True)

    def test_schema_cree_les_7_tables_avec_securite(self):
        sql = (RACINE / "sql/schema.sql").read_text()
        tables = re.findall(r"create table (\w+)", sql)
        self.assertEqual(len(tables), 7)
        for t in tables:
            self.assertIn(f"alter table {t} enable row level security", sql)


class TestDemo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for script in ("generer_donnees.py", "construire_demo.py"):
            subprocess.run([sys.executable, str(RACINE / "app/demo" / script)], check=True, cwd=RACINE / "app")
        cls.donnees = json.loads((RACINE / "app/demo/donnees_demo.json").read_text())
        cls.html = (RACINE / "app/demo.html").read_text()

    def test_volumes_de_la_demo(self):
        self.assertEqual(len(self.donnees["fiches"]), 60)
        self.assertEqual(len(self.donnees["offres"]), 36)

    def test_chaque_fiche_est_placee_en_ile_de_france(self):
        for f in self.donnees["fiches"]:
            self.assertTrue(48.1 < f["lat"] < 49.3 and 1.4 < f["lon"] < 3.6, f["entreprise"])

    def test_aucune_donnee_personnelle_publiee(self):
        interdit = re.compile(r"@gmail\.com|\b0[67](?:[ .]?\d{2}){4}\b|supabase\.co|sb_secret_", re.I)
        for f in list(RACINE.rglob("*.html")) + list(RACINE.rglob("*.py")) + list(RACINE.rglob("*.json")):
            if "tests" in f.parts:
                continue
            self.assertIsNone(interdit.search(f.read_text(errors="ignore")), f.name)


if __name__ == "__main__":
    unittest.main()
