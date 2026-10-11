"""Génère les données 100 % fictives de la démo : un CRM commercial (aucune vraie entreprise ni personne)."""
import json, random, datetime as dt
random.seed(7)
T = dt.date(2026, 10, 11)
PRE = ["Nova", "Datalis", "Orbis", "Kelia", "Vertigo", "Altea", "Lumen", "Strata", "Ondine", "Pyxis", "Corvus", "Helio", "Mistral", "Sirius", "Tessera", "Arcadia", "Boreal", "Quanta", "Zephyr", "Ilios"]
SUF = ["Conseil", "Analytics", "Retail", "Assurances", "Énergie", "Santé", "Logistique", "Digital", "Finance", "Mobilité"]
VILLES = [("Paris", 48.8566, 2.3522), ("Boulogne-Billancourt", 48.8397, 2.2399), ("Levallois-Perret", 48.8946, 2.2874), ("Issy-les-Moulineaux", 48.8245, 2.27), ("Courbevoie", 48.8973, 2.2565), ("Saint-Denis", 48.9362, 2.3574), ("Montreuil", 48.8638, 2.4485), ("Créteil", 48.7904, 2.4556), ("Nanterre", 48.8924, 2.2071), ("Massy", 48.7309, 2.2713)]
PRENOMS = ["Camille", "Julien", "Sarah", "Karim", "Léa", "Thomas", "Inès", "Hugo", "Nadia", "Paul"]
POSTES_C = ["Directrice commerciale", "Responsable achats", "Directeur financier", "Responsable data", "Directrice marketing"]
STATUTS = ["À contacter"] * 14 + ["Contacté"] * 24 + ["À relancer"] * 5 + ["Intéressé"] * 4 + ["Rendez-vous"] * 3 + ["Gagné"] * 2 + ["Perdu"] * 6 + ["Abandonné"] * 2
TYPES = ["📥 Entrant", "🏢 Prospection directe", "✉️ Recommandation", "🤝 Partenaire"]
rows = []
for i, st in enumerate(STATUTS):
    ent = f"{random.choice(PRE)} {random.choice(SUF)}"
    v = random.choice(VILLES)
    env = (T - dt.timedelta(days=random.randint(1, 24))).isoformat() if st != "À contacter" else None
    rel = None if st in ("Perdu", "Abandonné") else (T + dt.timedelta(days=random.randint(-5, 9))).isoformat()
    pr = random.choice(PRENOMS)
    rows.append(dict(id=i + 1, notion_page_id=None, entreprise=ent, poste=random.choice(["Refonte du reporting commercial", "Tableau de bord de direction", "Audit qualité des données clients", "Automatisation du reporting mensuel", "Prévision des ventes"]),
                     statut=st, type=random.choice(TYPES), piste=random.choice(["💼 Grands comptes", "🏪 PME"]), canal="LinkedIn", chances=None, envoi=env, relance=rel,
                     action=f"Premier appel avec {pr} : présenter l'offre et proposer un rendez-vous de 30 minutes" if st == "À contacter" else "",
                     contacts=f"{pr} {chr(65 + i % 26)}. ({random.choice(POSTES_C)})", linkedin=None, email=None, telephone=None,
                     notes="[Relance 1 le 07/10]" if st == "À relancer" else "", preuve=None, msg=None, agent=None,
                     ville=v[0], lat=v[1] + random.uniform(-.015, .015), lon=v[2] + random.uniform(-.02, .02), notion_sync=True))
TITRES = ["Appel d'offres : reporting Power BI", "Demande de devis : tableau de bord ventes", "Projet : qualité des données clients", "Appel d'offres : migration cloud des rapports", "Projet : prévision de la demande", "Demande de devis : automatisation Excel"]
offres = []
for i in range(36):
    v = random.choice(VILLES)
    f = {k: True for k in random.sample(["pbi", "sql", "dbt"], random.randint(1, 3))}
    offres.append(dict(cle=f"demo|{i}", titre=random.choice(TITRES), entreprise=f"{random.choice(PRE)} {random.choice(SUF)}", lieu=v[0],
                       source=random.choice(["Site web", "Salon", "Recommandation"]), publiee=(T - dt.timedelta(days=random.randint(0, 9))).isoformat(),
                       url="https://example.com/opportunite", statut="Nouvelle", trouvee=T.isoformat(), extrait="", lat=v[1] + random.uniform(-.01, .01), lon=v[2] + random.uniform(-.015, .015), flags=f))
json.dump({"fiches": rows, "offres": offres}, open("demo/donnees_demo.json", "w"), ensure_ascii=False, indent=0)
print(len(rows), "fiches et", len(offres), "opportunités fictives")
