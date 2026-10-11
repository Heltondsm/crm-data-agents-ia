"""Génère des données 100 % fictives pour la démo (aucune vraie entreprise ni personne)."""
import json, random, datetime as dt
random.seed(7)
T = dt.date(2026, 10, 11)
PRE = ["Nova", "Datalis", "Orbis", "Kelia", "Vertigo", "Altea", "Lumen", "Strata", "Ondine", "Pyxis", "Corvus", "Helio", "Mistral", "Sirius", "Tessera", "Arcadia", "Boreal", "Quanta", "Zephyr", "Ilios"]
SUF = ["Conseil", "Analytics", "Retail", "Assurances", "Énergie", "Santé", "Logistique", "Digital", "Finance", "Mobilité"]
VILLES = [("Paris", 48.8566, 2.3522), ("Boulogne-Billancourt", 48.8397, 2.2399), ("Levallois-Perret", 48.8946, 2.2874), ("Issy-les-Moulineaux", 48.8245, 2.27), ("Courbevoie", 48.8973, 2.2565), ("Saint-Denis", 48.9362, 2.3574), ("Montreuil", 48.8638, 2.4485), ("Créteil", 48.7904, 2.4556), ("Nanterre", 48.8924, 2.2071), ("Massy", 48.7309, 2.2713)]
PRENOMS = ["Camille", "Julien", "Sarah", "Karim", "Léa", "Thomas", "Inès", "Hugo", "Nadia", "Paul"]
POSTES_C = ["Talent Acquisition", "Ingénieur d'affaires", "Business Manager", "Responsable data", "Chargée de recrutement"]
STATUTS = ["À préparer"] * 14 + ["Envoyé"] * 26 + ["Relancer"] * 4 + ["Réponse positive"] * 3 + ["Entretien"] * 2 + ["Refus"] * 9 + ["Abandon"] * 2
TYPES = ["📨 Candidature", "🏢 Démarchage ESN", "✉️ Spontanée", "🤝 Réseau"]
rows = []
for i, st in enumerate(STATUTS):
    ent = f"{random.choice(PRE)} {random.choice(SUF)}"
    v = random.choice(VILLES)
    env = (T - dt.timedelta(days=random.randint(1, 24))).isoformat() if st != "À préparer" else None
    rel = None if st in ("Refus", "Abandon") else (T + dt.timedelta(days=random.randint(-5, 9))).isoformat()
    pr = random.choice(PRENOMS)
    rows.append(dict(id=i + 1, notion_page_id=None, entreprise=ent, poste=random.choice(["Data Analyst H/F", "Analyste BI Power BI", "Consultant Data Analyst", "Prospection LinkedIn · CDI Data Analyst"]),
                     statut=st, type=random.choice(TYPES), piste="💼 CDI / CDD Data Analyst", canal="LinkedIn", chances=None, envoi=env, relance=rel,
                     action=f"MESSAGE 1 : Bonjour {pr}, merci pour l'ajout. Je suis Data Analyst (SQL, Power BI, Python). Vos équipes ont des besoins data en ce moment ?" if st == "À préparer" else "",
                     contacts=f"{pr} {chr(65 + i % 26)}. ({random.choice(POSTES_C)})", linkedin=None, email=None, telephone=None,
                     notes="[R1 07/10]" if st == "Relancer" else "", preuve=None, msg=None, agent=None,
                     ville=v[0], lat=v[1] + random.uniform(-.015, .015), lon=v[2] + random.uniform(-.02, .02), notion_sync=True))
TITRES = ["Data Analyst Junior", "Analyste BI", "Data Analyst Power BI", "Chargé d'études statistiques", "Business Analyst data", "Data Analyst CRM"]
offres = []
for i in range(36):
    v = random.choice(VILLES)
    f = {k: True for k in random.sample(["junior", "pbi", "sql", "dbt", "bac5"], random.randint(1, 3))}
    if random.random() < .3: f["exp"] = random.choice([1, 2, 3, 5])
    offres.append(dict(cle=f"demo|{i}", titre=random.choice(TITRES) + " H/F", entreprise=f"{random.choice(PRE)} {random.choice(SUF)}", lieu=v[0],
                       source=random.choice(["LinkedIn", "WTTJ", "Indeed"]), publiee=(T - dt.timedelta(days=random.randint(0, 9))).isoformat(),
                       url="https://example.com/offre", statut="Nouvelle", trouvee=T.isoformat(), extrait="", lat=v[1] + random.uniform(-.01, .01), lon=v[2] + random.uniform(-.015, .015), flags=f))
json.dump({"fiches": rows, "offres": offres}, open("demo/donnees_demo.json", "w"), ensure_ascii=False, indent=0)
print(len(rows), "fiches et", len(offres), "offres fictives")
