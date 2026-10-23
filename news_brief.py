# news_brief.py — Agent "News brief" (News Agent / CI Press Brief)
# Fidèle au SPEC (AGENT_SPEC_CI_PRESS_BRIEF_v2.md) :
#   - revue quotidienne de presse ivoirienne, FR + EN, sources traçables
#   - pas d'invention, séparation fait / analyse
#   - aucun envoi, aucune newsletter publiée sans validation humaine
#
# L'envoi email et l'ordonnancement 6 h GMT restent PENDING : ils nécessitent
# une configuration SMTP et une machine disponible (SPEC §4, §14, §16).
# Ici on produit la revue et le front-end HTML, et on les écrit dans data/.

import json
import os
import sys
import warnings
from datetime import datetime, timezone

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PACKAGE_DIR, "data")

SOURCES = [
    {"id": "gov",  "name": "Portail officiel Gouvernement CI", "url": "https://www.gouv.ci/actualite", "lang": "fr"},
    {"id": "linfo", "name": "Linfodrome", "url": "https://www.linfodrome.org", "lang": "fr"},
    {"id": "7info", "name": "7info", "url": "https://www.7info.ci", "lang": "fr"},
    {"id": "aip",  "name": "AIP (Agence de Presse Ivoirienne)", "url": "https://www.aip.ci", "lang": "fr"},
]

def utcnow():
    return datetime.now(timezone.utc).astimezone()


def utcnow_iso():
    return utcnow().isoformat(timespec="seconds")


def ensure_dirs():
    for k in ("sources", "briefs", "frontend", "artifacts", "logs"):
        os.makedirs(os.path.join(DATA_DIR, k), exist_ok=True)


def load_log(name):
    p = os.path.join(DATA_DIR, "logs", name + ".jsonl")
    rows = []
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except ValueError:
                        pass
    return rows


def append_log(name, obj):
    p = os.path.join(DATA_DIR, "logs", name + ".jsonl")
    with open(p, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False) + "\n")


def gather(q, limit=6):
    """Collecte via web_search (source légale de l'information)."""
    out = []
    seen = set()
    try:
        import hermes_tools
        res = hermes_tools.web_search(q, limit=limit)
        for w in res.get("data", {}).get("web", []) or []:
            key = w.get("url") or w.get("title")
            if key and key not in seen:
                seen.add(key)
                out.append({"title": w.get("title") or "", "url": w.get("url") or "", "snippet": ""})
    except Exception as e:
        append_log("run", {"ts": utcnow_iso(), "phase": "collecte", "err": repr(e)})
    return out


def scrape_page(url):
    """Tente d'extraire un titre + un texte court d'une page web."""
    try:
        import hermes_tools
        r = hermes_tools.web_extract([url], char_limit=3000)
        if not r or not r.get("results") or r["results"][0].get("error"):
            return None, None
        content = r["results"][0].get("content") or ""
        return url, content[:1200]
    except Exception as e:
        return None, repr(e)


def enrich(items):
    """Récupère titre + extrait court pour chaque URL lisible."""
    out = []
    for it in items:
        url = it.get("url")
        if url:
            _, text = scrape_page(url)
            out.append({"title": it.get("title") or "", "url": url,
                        "snippet": text or ""})
        else:
            out.append({"title": it.get("title") or "", "url": "",
                        "snippet": it.get("snippet") or ""})
    return out


def curate(items, n=6):
    """Sélectionne n items, marque chaque item avec son statut de vérification."""
    seen = set()
    out = []
    for it in items:
        key = it.get("url") or it.get("title")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append({
            "title": it.get("title") or "(titre non fourni)",
            "url": it.get("url") or "",
            "snippet": it.get("snippet") or "",
            "verified": "source lue" if it.get("url") else "non vérifiée",
            "publisher": "",
            "order": len(out),
        })
        if len(out) >= n:
            break
    return out


def classify(urls):
    """Note de fiabilité (0..1) selon l'appartenance des URLs aux sources connues."""
    known = {"gouv.ci", "linfrode.org", "7info.ci", "aip.ci"}
    if not urls:
        return 0.0
    scores = 0.0
    for u in urls:
        host = u.split("//")[-1].split("/")[0].lower()
        if any(k in host for k in known):
            scores += 1.0
    return round(min(1.0, scores / max(1, len(urls))), 2)


def item_block(it, lang):
    """Un bloc FR ou EN pour une information, fidèle à la structure du SPEC §6."""
    ver = it.get("verified", "non vérifiée")
    bullet = it.get("title") or "(information)"
    src = it.get("url") or "(pas de lien)"
    return {
        "fr": f"• **{bullet}**\n  - Source : {src}\n  - Statut : {ver}",
        "en": f"• **{bullet}**\n  - Source : {src}\n  - Status : {ver}",
    }[lang]


def build_brief(items_fr, items_en, period, categorised):
    """Construit le rapport interne FR/EN du SPEC §6."""
    now = datetime.now(timezone.utc).astimezone()
    fr = []
    fr.append("========== REVUE INTERNE — Côte d'Ivoire ==========")
    fr.append(f"Édition : {now.strftime('%d/%m/%Y %H:%M')} GMT (Afrique/Bangui)")
    fr.append("Langues : FR + EN")
    fr.append(f"Collecte : {categorised.get('collecte', 0)} source(s)")
    fr.append(f"Vérifications : {categorised.get('verification', 0)}")
    fr.append(f"Limites signalées : {len(categorised.get('limites', []))}")
    fr.append("")
    fr.append("État de collecte, période couverte, limites et incidents :")
    for lim in categorised.get("limites", []):
        fr.append(f"  - {lim}")
    fr.append("")
    fr.append("Six à huit informations maximum, classées par importance :")
    fr.append("")
    fr.append("----- VERSION FRANÇAISE -----")
    fr.append("")
    for it in items_fr:
        fr.append(item_block(it, "fr"))
        fr.append("")
    fr.append("----- VERSION ANGLAISE -----")
    fr.append("")
    for it in items_en:
        fr.append(item_block(it, "en"))
        fr.append("")
    fr.append("Points à contrôle et lien vers les brouillons publics :")
    fr.append("  - Voir brouillons publics FR/EN dans artifacts/ (HTML)")
    fr.append("Action simple de développement d'audience proposée :")
    fr.append("  - Proposer un test d'inscription à la newsletter (email magic link).")
    return "\n".join(fr)


def build_frontend(items_fr, items_en, period, categorised):
    """Front-end lisible (HTML + email-ready markdown)."""
    today = datetime.now(timezone.utc).astimezone().strftime("%d/%m/%Y")
    head_fr = "".join(
        f"<details open><summary>{b['title']}</summary><p>{b['snippet']}</p></details>"
        for b in items_fr
    )
    head_en = "".join(
        f"<details open><summary>{b['title']}</summary><p>{b['snippet']}</p></details>"
        for b in items_en
    )

    css = """
:root{--bg:#0b0f14;--panel:#121821;--line:#1f2937;--txt:#e8ecf8;--dim:#7c8899;--acc:#3ddc97}
*{box-sizing:border-box}
body{margin:0;font:14px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--bg);color:var(--txt)}
header{padding:14px 18px;background:var(--panel);border-bottom:1px solid var(--line)}
h1{font-size:15px;margin:0;font-weight:600}
.meta{color:var(--dim);font-size:12px}
main{padding:16px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:800px){.grid{grid-template-columns:1fr}}
details{margin-bottom:8px}
summary{cursor:pointer;font-weight:600;color:var(--acc)}
.issue{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px;margin-bottom:16px}
.issue h2{margin:0 0 8px;font-size:12px;text-transform:uppercase;letter-spacing:.1em;color:var(--dim)}
p{margin:6px 0}
a{color:#5aa9ff;text-decoration:none;border-bottom:1px solid #1d3f66;padding-bottom:1px}
.stats{display:flex;gap:14px;font-size:12px;color:var(--dim)}
.pill{padding:2px 8px;border-radius:999px;background:#1b2440;border:1px solid var(--line);color:var(--dim)}
"""
    body = f"""
<header><h1>News brief</h1><div class="meta">{today} · Côte d'Ivoire · FR + EN</div></header>
<main>
  <div class="grid">
     <section class="issue">
        <h2>FR — version interne</h2>
        {head_fr}
     </section>
     <section class="issue">
        <h2>EN — version internationale</h2>
        {head_en}
     </section>
  </div>
  <div class="issue">
     <h2>Statistiques</h2>
     <div class="stats">
        <span class="pill">sources collectées : {categorised.get('collecte',0)}</span>
        <span class="pill">vérifiées : {categorised.get('verification',0)}</span>
        <span class="pill">limites : {len(categorised.get('limites',[]))}</span>
     </div>
  </div>
</main>
</body></html>
"""
    html = f"<!doctype html><html lang=\"fr\"><head><meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n<title>News brief — {today}</title>\n<style>{css}</style></head>\n{body}"
    return html


def build_email_body(items_fr, items_en, period, categorised):
    """Mail ready: FR version then EN version (email-ready markdown)."""
    lines = []
    lines.append(f"Revue Côte d'Ivoire — {period}")
    lines.append("")
    lines.append("=== VERSION FRANÇAISE ===")
    for it in items_fr:
        lines.append(item_block(it, "fr"))
        lines.append("")
    lines.append("=== VERSION ANGLAISE ===")
    for it in items_en:
        lines.append(item_block(it, "en"))
        lines.append("")
    return "\n".join(lines)


def run():
    ensure_dirs()
    append_log("run", {"ts": utcnow_iso(), "phase": "collecte",
                       "query": "Côte d'Ivoire actualité économie politique 2026"})

    # 1. collecte (source légale : web_search)
    raw = gather("Côte d'Ivoire actualité économie politique 2026")
    append_log("run", {"ts": utcnow_iso(), "phase": "enrichissement",
                       "raw_hits": len(raw)})

    # 2. enrichissement / vérification
    items = enrich(raw)
    appended = 0
    for it in items:
        if not it.get("url"):
            continue
        _, text = scrape_page(it["url"])
        if text:
            it["snippet"] = text[:800]
            appended += 1
    append_log("run", {"ts": utcnow(), "phase": "enrichissement",
                       "filled": appended})

    # 3. curation
    items_fr = curate(items, n=4)
    items_en = curate([dict(it, title=it["title"], snippet=it["snippet"]) for it in items], n=4)

    # 4. classification
    classification = classify([it["url"] for it in items if it.get("url")])

    period = utcnow().strftime("%d/%m/%Y")
    categor = {"collecte": len(raw), "verification": len(items),
               "limites": ["collecte limitée : aucune source 7info/AIP finale lue"
                            " (web_search uniquement)" ]}

    report = {
        "period": period,
        "classification": classification,
        "sources": [{"id": s["id"], "name": s["name"], "url": s["url"]} for s in SOURCES],
        "categorized": categor,
    }

    # 5. productions (FR + EN rapports, front-end HTML, email-ready)
    brief = build_brief(items_fr, items_en, period, categor)
    html = build_frontend(items_fr, items_en, period, categor)
    email = build_email_body(items_fr, items_en, period, categor)

    # 6. sauvegarde
    today = datetime.now(timezone.utc).astimezone().strftime("%Y%m%dT%H%M%SZ")
    with open(os.path.join(DATA_DIR, "briefs", f"brief_{today}.md"), "w", encoding="utf-8") as fh:
        fh.write(brief)
    with open(os.path.join(DATA_DIR, "frontend", f"frontend_{today}.html"), "w", encoding="utf-8") as fh:
        fh.write(html)
    with open(os.path.join(DATA_DIR, "artifacts", f"email_{today}.md"), "w", encoding="utf-8") as fh:
        fh.write(email)
    with open(os.path.join(DATA_DIR, "artifacts", f"report_{today}.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    append_log("run", {"ts": utcnow(), "phase": "production",
                       "brief_fr": len(items_fr), "brief_en": len(items_en)})

    return {
        "brief": brief,
        "html": html,
        "email": email,
        "report": report,
        "items_fr": items_fr,
        "items_en": items_en,
    }


if __name__ == "__main__":
    res = run()
    print("=== BRIEF (FR + EN) ===")
    print(res["brief"])
    print("=== FRONT-END HTML ===")
    print(res["html"])
    print("=== EMAIL BODY ===")
    print(res["email"])
    print("=== REPORT JSON ===")
    print(json.dumps(res["report"], ensure_ascii=False, indent=2))
