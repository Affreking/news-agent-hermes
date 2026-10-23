# mailer.py — Moteur d'envoi email pour l'agent "News brief".
# Fidèle au SPEC §14 : secrets dans des variables d'environnement (jamais dans le
# dépôt), adresse d'expédition autorisée, séparation tests/production.
# Au lancement, si les paramètres SMTP ne sont pas renseignés, l'agent reste en
# MODE DRY : le brief est produit, mais aucun courrier n'est détruit.

import os, smtplib, logging
from email.message import EmailMessage

LOG = logging.getLogger("news_brief.mailer")

def _env(name, default=""):
    return os.environ.get(name, default)

# --- Configuration par variable d'environnement (SPEC §14) ---------------------
SMTP_HOST   = _env("MAIL_HOST")
SMTP_PORT   = int(os.environ.get("MAIL_PORT", "587"))
USER        = _env("MAIL_USER")
PASSWORD    = _env("MAIL_PASSWORD")
FROM_ADDR   = _env("MAIL_FROM")
REPLY_TO    = _env("MAIL_REPLY_TO")
RECIPIENTS  = [r.strip() for r in _env("MAIL_RECIPIENTS", "ndri@gmail.com,affredatascientist@gmail.com").split(",") if r.strip()]

# Si aucun SMTP réel n'est configuré, on reste en DRY (pas d'envoi).
IN_TEST_MODE = not all([SMTP_HOST, USER, PASSWORD, FROM_ADDR, RECIPIENTS])

def build_message(fr, en, subject):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = FROM_ADDR
    msg["To"] = ", ".join(RECIPIENTS) if RECIPIENTS else FROM_ADDR
    msg["Reply-To"] = REPLY_TO or FROM_ADDR
    msg.set_content("\n".join([fr, "", "--- VERSION ANGLAISE ---", en]))
    return msg

def send(fr, en, subject="News brief — Côte d'Ivoire (FR/EN)"):
    if IN_TEST_MODE:
        LOG.info("[DRY] SMTP non configuré — le brief est produit, aucun courrier n'est envoyé.")
        LOG.info("[DRY] destinataires : %s", RECIPIENTS or "(aucun)")
        return False
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
            s.ehlo()
            if SMTP_PORT == 587:
                s.starttls()
                s.ehlo()
            s.login(USER, PASSWORD)
            msg = build_message(fr, en, subject)
            s.send_message(msg)
        LOG.info("[OK] courrier envoyé à %s", RECIPIENTS)
        return True
    except Exception as e:
        LOG.error("[ERREUR] envoi échoué : %s", e)
        return False
