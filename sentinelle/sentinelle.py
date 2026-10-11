#!/usr/bin/env python3
"""Sentinelle LinkedIn : lit l'activité LinkedIn du propriétaire du compte (API Member Data Portability)
et met à jour sa base Supabase. Tourne dans GitHub Actions, Mac éteint.

Ce qu'elle fait à chaque passage :
  1. nouvelles relations  -> la fiche passe « message 1 à envoyer aujourd'hui » (ou une fiche est créée)
  2. messages reçus       -> la fiche passe en « Réponse positive », relance annulée, alerte Telegram
  3. chiffres de la semaine (invitations, acceptations, réponses) -> table semaines
Elle n'envoie jamais rien sur LinkedIn. Les jetons ne sont jamais affichés.

Variables : LINKEDIN_DMA_TOKEN, SUPABASE_URL, SUPABASE_SECRET_KEY, TELEGRAM_TOKEN, TELEGRAM_CHAT.
DRY=1 : n'écrit rien, affiche ce qui serait fait (lit les fiches dans DRY_FICHES, un fichier JSON).
"""
import datetime as dt, json, os, re, sys, unicodedata, urllib.parse, urllib.request, urllib.error
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
NOW = dt.datetime.now(PARIS)
TODAY = NOW.date()
DRY = os.environ.get("DRY") == "1"
LI_H = {"Authorization": "Bearer " + os.environ["LINKEDIN_DMA_TOKEN"].strip(), "Linkedin-Version": "202312", "X-Restli-Protocol-Version": "2.0.0"}
SB_URL = os.environ.get("SUPABASE_URL", "").rstrip("/") + "/rest/v1/"
SB_KEY = os.environ.get("SUPABASE_SECRET_KEY", "")
AGENT = f"Sentinelle LinkedIn, {TODAY:%d/%m}"
ACTIFS = ("À contacter", "Contacté", "À relancer", "Suivi flag")
RECRUTEURS = re.compile(r"recrut|talent|business manager|business developer|ing[ée]nieur d.affaires|account manager|charg[ée] d.affaires|rh\b|human resources|staffing|sourcing", re.I)
DATA = re.compile(r"data|bi\b|analytics|power bi|analyste|analyst", re.I)
REFUS = re.compile(r"pas de besoin|pas de poste|ne recrut|malheureusement|pas pour le moment|pas d.opportunit|aucun poste", re.I)


def log(*a):
    print(*a, flush=True)


def li_get(path):
    req = urllib.request.Request("https://api.linkedin.com/rest/" + path, headers=LI_H)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"{}")


def snapshot(domain):
    rows, start = [], 0
    while True:
        j = li_get(f"memberSnapshotData?q=criteria&domain={domain}&start={start}")
        for e in j.get("elements", []):
            rows += e.get("snapshotData", [])
        if not any(l.get("rel") == "next" for l in j.get("paging", {}).get("links", [])):
            return rows
        start += 1


def changelog():
    """La fin du journal seulement : l'API a un plafond d'appels par jour.
    On demande le total, puis les ~200 dernières entrées (4 à 5 appels au lieu d'une dizaine)."""
    tot = li_get("memberChangeLogs?q=memberAndApplication&count=1&start=0").get("paging", {}).get("total")
    start = max(0, tot - 200) if isinstance(tot, int) else 0
    out = []
    while start < 5000:
        e = li_get(f"memberChangeLogs?q=memberAndApplication&count=50&start={start}").get("elements", [])
        out += e
        if len(e) < 50:
            return out
        start += 50
    return out


def sb(method, table, params="", body=None, prefer=None):
    if DRY and method != "GET":
        log("  [DRY]", method, table, params, (json.dumps(body, ensure_ascii=False)[:160] if body else ""))
        return []
    h = {"apikey": SB_KEY, "Authorization": "Bearer " + SB_KEY, "Content-Type": "application/json"}
    if prefer:
        h["Prefer"] = prefer
    req = urllib.request.Request(SB_URL + table + ("?" + params if params else ""), method=method, headers=h,
                                 data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            txt = r.read()
            return json.loads(txt) if txt else []
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Supabase {method} {table} : {e.code} {e.read().decode()[:300]}")


def norm_url(u):
    u = urllib.parse.unquote((u or "").strip().lower()).split("?")[0].rstrip("/")
    m = re.search(r"linkedin\.com/in/([^/]+)", u)
    return "linkedin.com/in/" + m.group(1) if m else ""


def nrm(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c)).lower()


def prenom_fiche(f):
    m = re.match(r"MESSAGE 1 : Bonjour ([^,]+),", f.get("prochaine_action") or "")
    if m:
        return nrm(m.group(1))
    return nrm(re.split(r"[ (·]", (f.get("contacts") or "").strip())[0])


def telegram(texte):
    tok, chat = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT")
    if DRY or not tok or not chat:
        log("[Telegram]", texte)
        return
    req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendMessage", headers={"Content-Type": "application/json"},
                                 data=json.dumps({"chat_id": chat, "text": texte[:3900], "disable_web_page_preview": True}).encode())
    urllib.request.urlopen(req, timeout=30)


def geo_entreprise(nom):
    try:
        q = urllib.parse.quote(nom)
        with urllib.request.urlopen(f"https://recherche-entreprises.api.gouv.fr/search?q={q}&per_page=1", timeout=15) as r:
            s = (json.loads(r.read()).get("results") or [{}])[0].get("siege") or {}
        if s.get("latitude"):
            return s.get("libelle_commune"), float(s["latitude"]), float(s["longitude"])
    except Exception:
        pass
    return None, None, None


def main():
    if not DRY and not SB_KEY:
        sys.exit("SUPABASE_SECRET_KEY manquante")
    alertes, resume = [], []

    # ---------- état actuel ----------
    if DRY:
        fiches = json.load(open(os.environ["DRY_FICHES"]))
        connues, vus = None, set()
    else:
        fiches = sb("GET", "fiches", "select=id,entreprise,poste,statut,type,contacts,linkedin,prochaine_action,notes,date_envoi,relance")
        connues = {r["url"] for r in sb("GET", "li_relations", "select=url")}
        vus = {r["id"] for r in sb("GET", "li_events", "select=id")}
    par_url = {}
    for f in fiches:
        k = norm_url(f.get("linkedin"))
        if k:
            par_url.setdefault(k, []).append(f)
    rel = snapshot("CONNECTIONS")
    if connues is None:  # test à blanc : les relations depuis DRY_SINCE sont traitées comme nouvelles
        since = os.environ.get("DRY_SINCE", "2026-10-08")
        connues = set()
        for r in rel:
            try:
                if dt.datetime.strptime(r.get("Connected On", ""), "%d %b %Y").date().isoformat() < since:
                    connues.add(norm_url(r.get("URL")))
            except ValueError:
                connues.add(norm_url(r.get("URL")))
    premier_passage = not connues
    log(f"{len(fiches)} fiches · {len(connues)} relations connues · premier passage : {premier_passage}")

    def maj(f, champs, raison):
        champs = {**champs, "agent": AGENT, "notion_sync": False, "updated_at": NOW.isoformat()}
        sb("PATCH", "fiches", f"id=eq.{f['id']}", champs, "return=minimal")
        f.update(champs)
        log("  fiche", f["id"], f["entreprise"], "→", raison)

    # ---------- 1. relations ----------
    nouvelles = []
    lignes = []
    for r in rel:
        k = norm_url(r.get("URL"))
        if not k:
            continue
        try:
            co = dt.datetime.strptime(r.get("Connected On", ""), "%d %b %Y").date()
        except ValueError:
            co = None
        lignes.append({"url": k, "prenom": r.get("First Name"), "nom": r.get("Last Name"), "entreprise": r.get("Company"), "poste": r.get("Position"), "connected_on": co and co.isoformat()})
        if k not in connues and (not premier_passage or (co and co.isoformat() >= os.environ.get("PREMIER_DEPUIS", ""))):
            nouvelles.append((k, r, co))
    for i in range(0, len(lignes), 500):
        sb("POST", "li_relations", "on_conflict=url", lignes[i:i + 500], "resolution=ignore-duplicates,return=minimal")
    crees = 0
    for k, r, co in nouvelles:
        nom = f"{r.get('First Name', '')} {r.get('Last Name', '')}".strip()
        fs = par_url.get(k, [])
        if fs:
            for f in fs:
                if f["statut"] == "À contacter":
                    maj(f, {"relance": TODAY.isoformat(), "notes": ((f.get("notes") or "") + f" [Invitation acceptée {TODAY:%d/%m}]").strip()}, "invitation acceptée")
                    alertes.append(f"✅ {nom} ({f['entreprise']}) a accepté : envoie le message 1 aujourd'hui")
                else:
                    maj(f, {"notes": ((f.get("notes") or "") + f" [Connecté {TODAY:%d/%m}]").strip()}, "connecté")
        elif crees < 15 and (RECRUTEURS.search(r.get("Position") or "") or DATA.search(r.get("Position") or "")):
            ent = r.get("Company") or "?"
            recr = bool(RECRUTEURS.search(r.get("Position") or ""))
            ville, lat, lon = geo_entreprise(ent) if ent != "?" else (None, None, None)
            body = {"entreprise": ent, "poste": "Prospection directe" if recr else "Partenaire",
                    "type": "🏢 Prospection directe" if recr else "🤝 Partenaire", "piste": "💼 Grands comptes", "canal": "LinkedIn",
                    "statut": "À contacter", "relance": TODAY.isoformat(), "contacts": f"{nom} ({r.get('Position') or '?'})", "linkedin": r.get("URL"),
                    "prochaine_action": "Nouvelle relation LinkedIn : choisis le message 1 dans le playbook (catégorie " + ("A ou B" if recr else "D, pair data") + ")",
                    "notes": f"Fiche créée par la Sentinelle : relation acceptée le {co:%d/%m}." if co else "Fiche créée par la Sentinelle.",
                    "agent": AGENT, "notion_sync": False, "ville": ville, "lat": lat, "lon": lon}
            sb("POST", "fiches", "", body, "return=minimal")
            crees += 1
            alertes.append(f"🆕 Nouvelle relation : {nom}, {r.get('Position')} chez {ent} (fiche créée)")
    resume.append(f"{len(rel)} relations, {len(nouvelles)} nouvelles, {crees} fiches créées")

    # ---------- 2. messages ----------
    ev = changelog()
    if not ev:
        resume.append("journal LinkedIn vide")
    moi = ev[0]["owner"] if ev else None
    msgs = [e for e in ev if e.get("resourceName") == "messages" and e.get("method") == "CREATE"]
    # prénom du destinataire d'après les messages du propriétaire dans chaque conversation
    prenoms, url_fil = {}, {}
    for e in msgs:
        a = e["activity"]
        if a.get("author") == moi:
            m = re.match(r"\s*(?:Bonjour|Hello|Salut|Re-?bonjour)\s+([A-Za-zÀ-ÿ\-]+)", (a.get("content") or {}).get("fallback") or "")
            if m:
                prenoms[a.get("thread")] = nrm(m.group(1))
    try:  # ancienne copie de la boîte : conversation -> profil de l'interlocuteur
        for x in snapshot("INBOX"):
            cid, s = x.get("CONVERSATION ID") or "", x.get("SENDER PROFILE URL") or ""
            if cid and s and os.environ.get("MON_PROFIL", "mon-profil") not in s.lower():
                url_fil[cid] = norm_url(s)
    except Exception as e:
        log("boîte de réception indisponible :", e)
    nouveaux = []
    for e in msgs:
        if str(e["id"]) in vus:
            continue
        a = e["activity"]
        thread = a.get("thread") or ""
        at = dt.datetime.fromtimestamp((a.get("createdAt") or e["capturedAt"]) / 1000, dt.timezone.utc)
        txt = ((a.get("content") or {}).get("fallback") or "").strip()
        row = {"id": str(e["id"]), "type": "message", "at": at.isoformat(), "thread": thread, "de_moi": a.get("author") == moi, "auteur": a.get("author"), "extrait": txt[:240]}
        nouveaux.append(row)
    if nouveaux:
        sb("POST", "li_events", "on_conflict=id", nouveaux, "resolution=ignore-duplicates,return=minimal")
    recus = [n for n in nouveaux if not n["de_moi"]]
    deja = set()
    for n in sorted(recus, key=lambda x: x["at"]):
        if n["thread"] in deja:
            continue
        deja.add(n["thread"])
        cid = n["thread"].split(":")[-1]
        cand = []
        u = url_fil.get(cid)
        if u:
            cand = [f for f in par_url.get(u, []) if f["statut"] in ACTIFS]
        if not cand and prenoms.get(n["thread"]):
            p = prenoms[n["thread"]]
            cand = [f for f in fiches if f["statut"] in ACTIFS and prenom_fiche(f) == p]
        quand = dt.datetime.fromisoformat(n["at"]).astimezone(PARIS)
        extrait = n["extrait"][:140].replace("\n", " ")
        if len(cand) == 1:
            f = cand[0]
            neg = bool(REFUS.search(n["extrait"]))
            maj(f, {"statut": "Intéressé", "relance": TODAY.isoformat(),
                    "prochaine_action": f"💬 Réponse LinkedIn du {quand:%d/%m} : " + ("à lire, elle semble négative : remercie et demande si tu peux revenir dans un mois" if neg else "propose un appel de 10 minutes"),
                    "notes": ((f.get("notes") or "") + f" [Réponse LinkedIn {quand:%d/%m} : « {extrait[:90]} »]").strip()}, "réponse reçue")
            sb("PATCH", "li_events", f"id=eq.{urllib.parse.quote(n['id'], safe='')}", {"fiche_id": f["id"], "traite": True}, "return=minimal")
            alertes.append(f"🔥 {f['entreprise']} ({f.get('contacts') or '?'}) t'a répondu sur LinkedIn : « {extrait} »")
        else:
            qui = f"« {prenoms.get(n['thread'], '').title()} »" if prenoms.get(n["thread"]) else "un contact"
            alertes.append(f"💬 Message LinkedIn de {qui} ({quand:%d/%m %H:%M}), fiche non trouvée{' (plusieurs possibles)' if len(cand) > 1 else ''} : « {extrait} »")
    resume.append(f"{len(nouveaux)} messages nouveaux dont {len(recus)} reçus")

    # ---------- 3. chiffres de la semaine ----------
    lundi = TODAY - dt.timedelta(days=TODAY.weekday())
    def cette_semaine(ms):
        return dt.datetime.fromtimestamp(ms / 1000, PARIS).date() >= lundi
    invit = sum(1 for e in ev if e.get("resourceName") == "invitations" and (e["activity"].get("invitationV2") or {}).get("inviter") == moi and cette_semaine(e["capturedAt"]))
    acc = sum(1 for l in lignes if l["connected_on"] and l["connected_on"] >= lundi.isoformat())
    rep = len({e["activity"].get("thread") for e in msgs if e["activity"].get("author") != moi and cette_semaine(e["activity"].get("createdAt") or e["capturedAt"])})
    sb("POST", "semaines", "on_conflict=debut", {"debut": lundi.isoformat(), "invitations": invit, "acceptees": acc, "reponses": rep},
       "resolution=merge-duplicates,return=minimal")
    resume.append(f"semaine du {lundi:%d/%m} : {invit} invitations, {acc} acceptées, {rep} réponses")

    # ---------- journal + alerte ----------
    sb("POST", "journal_agents", "", {"agent": "Sentinelle LinkedIn", "execution": f"Sentinelle {NOW:%d/%m %H:%M}", "statut": "OK",
                                      "resume": " · ".join(resume), "marque_page": NOW.isoformat()}, "return=minimal")
    log(" · ".join(resume))
    alertes.sort(key=lambda a: 0 if a.startswith("🔥") else 1 if a.startswith("💬") else 2 if a.startswith("✅") else 3)
    if alertes:
        telegram("🔭 Sentinelle LinkedIn\n\n" + "\n\n".join(alertes[:25]) + ("\n\n…" if len(alertes) > 25 else "") + "\n\nTout est dans ton cockpit (onglet À faire).")



if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        msg = str(e)
        for k in ("LINKEDIN_DMA_TOKEN", "SUPABASE_SECRET_KEY", "TELEGRAM_TOKEN"):
            v = os.environ.get(k)
            if v:
                msg = msg.replace(v, "***")
        print("ERREUR :", msg)
        try:
            if not DRY and SB_KEY:
                sb("POST", "journal_agents", "", {"agent": "Sentinelle LinkedIn", "execution": f"Sentinelle {NOW:%d/%m %H:%M}", "statut": "Échec", "resume": msg[:400]}, "return=minimal")
        except Exception:
            pass
        sys.exit(1)
