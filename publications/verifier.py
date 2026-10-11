#!/usr/bin/env python3
"""Les jours de post : attend que le post soit publié, puis ajoute le lien en 1er commentaire s'il manque.
Ne fait rien si l'auteur a déjà commenté avec le lien. Prévient sur Telegram dans tous les cas.

Variables : LINKEDIN_POST_TOKEN (publication), LINKEDIN_DMA_TOKEN (lecture du journal), TELEGRAM_TOKEN, TELEGRAM_CHAT.
Usage : python3 commentaires/verifier.py [--essai]   (--essai : ne commente pas, ne réessaie pas)
"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ICI = Path(__file__).resolve().parent
ESSAI = "--essai" in sys.argv
PARIS = ZoneInfo("Europe/Paris")
VERSION = "202609"


def appel(url, jeton, methode="GET", donnees=None, version=True):
    h = {"Authorization": f"Bearer {jeton}", "X-Restli-Protocol-Version": "2.0.0", "Content-Type": "application/json"}
    h["Linkedin-Version"] = VERSION if version else "202312"
    req = urllib.request.Request(url, data=json.dumps(donnees).encode() if donnees else None, method=methode, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            txt = r.read().decode() or "{}"
            return r.status, json.loads(txt)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


def telegram(texte):
    t, c = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT")
    if not t or not c:
        print(texte); return
    data = json.dumps({"chat_id": c, "text": texte, "disable_web_page_preview": True}).encode()
    urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{t}/sendMessage", data=data,
                                                  headers={"Content-Type": "application/json"}), timeout=30)


def journal():
    """La fin du journal LinkedIn seulement (il est rangé du plus ancien au plus récent).
    L'API a un plafond d'appels PAR JOUR : on demande le total, puis les ~150 dernières entrées (3 à 4 appels)."""
    tok = os.environ["LINKEDIN_DMA_TOKEN"]
    s, d = appel("https://api.linkedin.com/rest/memberChangeLogs?q=memberAndApplication&count=1&start=0", tok, version=False)
    if s != 200 or not isinstance(d, dict):
        raise RuntimeError(f"journal LinkedIn indisponible ({s}) : {str(d)[:160]}")
    total = (d.get("paging") or {}).get("total")
    start = max(0, total - 150) if isinstance(total, int) else 0
    out = []
    while start < 5000:
        s, d = appel(f"https://api.linkedin.com/rest/memberChangeLogs?q=memberAndApplication&count=50&start={start}", tok, version=False)
        if s != 200 or not isinstance(d, dict):
            raise RuntimeError(f"journal LinkedIn indisponible ({s}) : {str(d)[:160]}")
        e = d.get("elements", [])
        out += e
        if len(e) < 50:
            return out
        start += 50
    return out


def posts_supabase(jour):
    """Posts préparés par l'agent Plume (table li_posts), en plus de posts.json."""
    cle = os.environ.get("SUPABASE_SECRET_KEY")
    if not cle:
        return []
    url = os.environ.get("SUPABASE_URL", "") + "/rest/v1/li_posts?select=id,date,debut,lien,commentaire,statut&date=eq." + jour
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"apikey": cle, "Authorization": "Bearer " + cle}), timeout=30) as r:
            return [p for p in json.loads(r.read()) if p.get("lien") and p.get("statut") != "commenté"]
    except Exception as e:
        print("Supabase indisponible :", e); return []


def marquer(post, statut):
    cle = os.environ.get("SUPABASE_SECRET_KEY")
    if not cle or not post.get("id"):
        return
    req = urllib.request.Request(os.environ.get("SUPABASE_URL", "") + "/rest/v1/li_posts?id=eq." + str(post["id"]), method="PATCH",
                                 data=json.dumps({"statut": statut}).encode(),
                                 headers={"apikey": cle, "Authorization": "Bearer " + cle, "Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=30)
    except Exception:
        pass


def chercher(post, aujourdhui, ev):
    """Renvoie (urn du post publié ou None, lien déjà commenté ?)."""
    cible, deja = None, False
    for e in ev:
        if datetime.fromtimestamp(e["capturedAt"] / 1000, PARIS).date() != aujourdhui:
            continue
        a = json.dumps(e.get("activity", {}), ensure_ascii=False)
        if e.get("resourceName") in ("ugcPosts", "posts", "shares") and e.get("method") in ("CREATE", "UPDATE") \
                and post["debut"] in a and '"PUBLISHED"' in a:
            cible = e.get("resourceId")
        if e.get("resourceName") == "socialActions/comments" and e.get("method") == "CREATE" \
                and (post["lien"].rstrip("/") in a or (os.environ.get("PORTFOLIO_URL") or "§") in a):  # le lien du projet OU celui du portfolio suffit
            deja = True
    return cible, deja


def main():
    """Passe chaque heure l'après-midi (GitHub a souvent des heures de retard : pas de créneau strict).
    Silencieux tant qu'il n'y a rien à faire ; prévient une seule fois : lien ajouté, échec, ou post jamais sorti (dernier passage du soir)."""
    maintenant = datetime.now(PARIS)
    jour = maintenant.date().isoformat()
    posts = [p for p in json.loads((ICI / "posts.json").read_text()) if p["date"] == jour] + posts_supabase(jour)
    if not posts:
        print("aucun post aujourd'hui"); return
    if not ESSAI and maintenant.hour * 60 + maintenant.minute < 12 * 60 + 40:
        print("trop tôt", maintenant.strftime("%H:%M")); return
    dernier_passage = maintenant.hour >= 20
    ev = journal()
    for post in posts:
        cible, deja = chercher(post, maintenant.date(), ev)
        titre = f"« {post['debut']}… »"
        if deja:
            print("lien déjà en commentaire :", titre); marquer(post, "commenté"); continue
        if not cible:
            print("post pas encore vu :", titre)
            if dernier_passage and not ESSAI:
                telegram(f"⚠️ Post {titre} : je ne le vois toujours pas publié ce soir. Vérifie qu'il est bien sorti, et mets le lien toi-même si besoin :\n{post['lien']}")
            continue
        if ESSAI:
            print("essai : post trouvé", cible); continue
        jeton = os.environ["LINKEDIN_POST_TOKEN"]
        s, moi = appel("https://api.linkedin.com/v2/userinfo", jeton, version=False)
        acteur = "urn:li:person:" + moi["sub"]
        s, d = appel(f"https://api.linkedin.com/rest/socialActions/{urllib.parse.quote(cible, safe='')}/comments", jeton,
                     "POST", {"actor": acteur, "object": cible, "message": {"text": post["commentaire"]}})
        if s < 300:
            marquer(post, "commenté"); telegram(f"✅ Post {titre} : j'ai ajouté le lien en 1er commentaire.")
        else:
            telegram(f"❌ Post {titre} : échec du commentaire ({s}). Mets le lien toi-même :\n{post['lien']}")


if __name__ == "__main__":
    main()
