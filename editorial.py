"""Offline editorial validation. Evidence is reviewer-supplied, never fetched or certified.

Input: {"articles": [article, ...], "limitations": [str, ...]}.
Publication evidence must repeat the timezone-aware published_at timestamp and
record its source URL and the exact supporting excerpt. Event dates are metadata.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from html import escape
from email.message import EmailMessage
from email.policy import SMTP


_LOCAL = re.compile(r"file:|\b[A-Za-z]:[\\\\/]|(?:^|\s)(?:/|~/)|(?:\b(?:data|artifacts|frontend)/)", re.I)


def _text(value):
    if not isinstance(value, str) or not value.strip() or _LOCAL.search(value):
        raise ValueError("required text missing or contains local path")
    return value.strip()


def _url(value):
    value = _text(value)
    parts = urlsplit(value)
    if parts.scheme not in ("https", "http") or not parts.hostname or parts.username or parts.password:
        raise ValueError("public HTTP(S) source URL required")
    query = [(k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith("utm_") and k.lower() not in ("fbclid", "gclid")]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), urlencode(sorted(query)), ""))


def _timestamp(value):
    if not isinstance(value, str):
        raise ValueError("timezone-aware timestamp required")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timezone-aware timestamp required")
    return result


def validate_edition(data, *, now=None):
    if not isinstance(data, dict) or not isinstance(data.get("articles"), list):
        raise ValueError("edition must contain an articles list")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    end = now.astimezone(ZoneInfo("Africa/Abidjan"))
    start = end - timedelta(hours=24)
    accepted, excluded = [], []
    seen_urls, seen_stories = set(), set()
    for index, item in enumerate(data["articles"]):
        try:
            if not isinstance(item, dict):
                raise ValueError("article must be an object")
            story = _text(item.get("story_id"))
            url = _url(item.get("url"))
            _text(item.get("source"))
            if item.get("event_date"):
                _text(item["event_date"])
            for lang in ("fr", "en"):
                block = item.get(lang) or {}
                if not isinstance(block, dict):
                    raise ValueError("language block must be an object")
                for field in ("title", "interest", "summary"):
                    _text(block.get(field))
                if not 60 <= len(re.findall(r"\b[\w]+(?:[’'-][\w]+)*\b", block["summary"])) <= 90:
                    raise ValueError(f"{lang} summary must contain 60–90 words")
            if item["fr"]["summary"].strip().casefold() == item["en"]["summary"].strip().casefold():
                raise ValueError("FR and EN summaries must be independently written")
            if url in seen_urls or story in seen_stories:
                raise ValueError("duplicate URL or story_id")
            published = _timestamp(item.get("published_at"))
            if not start <= published <= end:
                raise ValueError("publication outside the rolling 24-hour window")
            evidence = item.get("published_evidence") or {}
            if not isinstance(evidence, dict):
                raise ValueError("publication evidence must be an object")
            if not evidence.get("url") or not evidence.get("excerpt"):
                raise ValueError("publication evidence missing")
            if _timestamp(evidence.get("published_at")) != published:
                raise ValueError("publication evidence timestamp mismatch")
            _text(evidence["excerpt"])
            evidence_url = _url(evidence["url"])
            verification = item.get("verification") or {}
            if not isinstance(verification, dict):
                raise ValueError("verification must be an object")
            status = verification.get("status")
            if status not in ("source_consulted", "primary", "corroborated"):
                raise ValueError("explicit verification status required")
            sources = verification.get("sources") or []
            if not isinstance(sources, list) or not sources:
                raise ValueError("recorded source consultation required")
            urls, origins, hosts = set(), set(), set()
            primary = False
            for source in sources:
                if not isinstance(source, dict):
                    raise ValueError("consulted source must be an object")
                source_url = _url(source.get("url"))
                urls.add(source_url)
                origins.add(_text(source.get("origin")).casefold())
                hosts.add(urlsplit(source_url).hostname.removeprefix("www."))
                _text(source.get("excerpt"))
                consulted = _timestamp(source.get("consulted_at"))
                if consulted < published:
                    raise ValueError("source consultation time invalid")
                if source.get("is_primary") is True:
                    _text(source.get("primary_evidence"))
                    primary = True
                if status == "corroborated":
                    _text(source.get("independence_evidence"))
            if url not in urls or evidence_url not in urls:
                raise ValueError("article and publication evidence must come from consulted sources")
            if status == "primary" and not primary:
                raise ValueError("primary source evidence required")
            if status == "corroborated" and min(len(urls), len(origins), len(hosts)) < 2:
                raise ValueError("two independent consulted origins required")
        except (ValueError, TypeError) as exc:
            excluded.append({"index": index, "reason": str(exc)})
        else:
            accepted.append(item)
            seen_urls.add(url)
            seen_stories.add(story)
    return {"articles": accepted, "excluded": excluded, "timezone": "Africa/Abidjan",
            "window_start": start.isoformat(), "window_end": end.isoformat()}


def prepare_draft(data, *, now=None):
    """Return html_fr, html_en, mime_bytes and a separate technical report.

    No files, network, environment or SMTP access. This validates recorded
    evidence, not the truth of claims or the quality of a translation.
    """
    edition = validate_edition(data, now=now)
    limitations = [_text(value) for value in data.get("limitations", [])]
    for item in edition["articles"]:
        if item["published_evidence"].get("timezone_basis"):
            limitations.append(_text(item["published_evidence"]["timezone_basis"]))
    limitations.append("Offline checks validate reviewer-supplied evidence only; no independent fact certification or translation-quality assessment. Human review required.")
    if not edition["articles"]:
        limitations.append("No eligible article: none supplied or publication window, evidence or editorial requirements could not be established.")
    labels = {
        "fr": {"heading": "Revue de presse — brouillon", "empty": "Aucun article admissible : critères éditoriaux ou fenêtre de publication non établis.", "interest": "Pourquoi c’est important", "publication": "Publication", "event": "Date de l’événement (distincte)", "review": "Brouillon — revue humaine requise. Aucun envoi.", "status": {"source_consulted": "Source consultée (preuve déclarée)", "primary": "Source primaire (preuve déclarée)", "corroborated": "Corroboration indépendante (preuves déclarées)"}},
        "en": {"heading": "News brief — draft", "empty": "No eligible article: editorial criteria or publication window could not be established.", "interest": "Why it matters", "publication": "Published", "event": "Event date (separate)", "review": "Draft — human review required. Not sent.", "status": {"source_consulted": "Source consulted (recorded evidence)", "primary": "Primary source (recorded evidence)", "corroborated": "Independent corroboration (recorded evidence)"}},
    }
    html = {}
    plain = []
    for lang, label in labels.items():
        blocks = []
        for item in edition["articles"]:
            block = item[lang]
            event = f'<p>{label["event"]}: {escape(str(item["event_date"]))}</p>' if item.get("event_date") else ""
            if item["published_evidence"].get("timezone_basis"):
                event += f'<p>{escape(_text(item["published_evidence"]["timezone_basis"]))}</p>'
            blocks.append(f'<article><h2>{escape(block["title"])}</h2><p>{escape(block["summary"])}</p><p><strong>{label["interest"]}:</strong> {escape(block["interest"])}</p><p>Source: <a href="{escape(item["url"], quote=True)}">{escape(item["source"])}</a></p><p>{label["publication"]}: <time>{escape(item["published_at"])}</time></p>{event}<p>{label["status"][item["verification"]["status"]]}</p></article>')
        for index, item in enumerate(edition["articles"]):
            note = item[lang].get("verification_note")
            if note:
                blocks[index] += f'<p>{escape(_text(note))}</p>'
            for extra_url in item.get("additional_source_urls", []):
                safe_url = escape(_url(extra_url), quote=True)
                blocks[index] += f'<p><a href="{safe_url}">{safe_url}</a></p>'
        lang_limits = [_text(v) for v in data.get("limitations_" + lang, limitations)]
        limit_html = "".join(f"<p>{escape(value)}</p>" for value in lang_limits)
        content = limit_html + ("".join(blocks) or f'<p>{label["empty"]}</p>')
        plain_parts = [label["heading"], label["review"], edition["window_start"] + " — " + edition["window_end"] + " · Africa/Abidjan"] + lang_limits
        for item in edition["articles"]:
            block = item[lang]
            plain_parts.extend([block["title"], block["summary"], label["interest"] + ": " + block["interest"], item["source"], item["url"], label["publication"] + ": " + item["published_at"], label["event"] + ": " + item.get("event_date", "—"), block.get("verification_note", label["status"][item["verification"]["status"]])])
            plain_parts.extend(item.get("additional_source_urls", []))
        plain.append("\n\n".join(plain_parts))
        html[lang] = f'<!doctype html>\n<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{label["heading"]}</title><style>body{{max-width:760px;margin:2rem auto;padding:0 1rem;font:18px/1.65 Georgia,serif;color:#17212b;background:#fff}}article{{border-top:1px solid #ccd4dc;padding:1rem 0}}a{{color:#174b87}}h1,h2{{line-height:1.25}}</style></head><body><h1>{label["heading"]}</h1><p>{label["review"]}</p><p>{escape(edition["window_start"])} — {escape(edition["window_end"])} · Africa/Abidjan</p>{content}</body></html>'
    message = EmailMessage(policy=SMTP)
    message["Subject"] = "News brief FR/EN — DRAFT — human review required"
    message["X-Unsent"] = "1"
    message.set_content("\n\n".join(plain))
    message.add_alternative(html["fr"] + "\n" + html["en"], subtype="html")
    for lang in ("fr", "en"):
        message.add_attachment(html[lang].encode("utf-8"), maintype="text", subtype="html", filename=f"draft_{lang}.html", params={"charset": "utf-8"})
    report = {k: v for k, v in edition.items() if k != "articles"}
    report.update(accepted_count=len(edition["articles"]), excluded_count=len(edition["excluded"]), limitations=limitations, sent=False, human_review_required=True)
    return {"html_fr": html["fr"], "html_en": html["en"], "mime_bytes": message.as_bytes(), "report": report}
