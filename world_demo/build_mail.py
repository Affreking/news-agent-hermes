"""Generate an unsent, recipient-free preview. Never imports SMTP or sends."""
from email.message import EmailMessage
from email.policy import SMTP
from pathlib import Path

plain = '''WELISPEAK — Monde / World
DÉMONSTRATION · NON ENVOYÉ / DEMONSTRATION · UNSENT

FRANÇAIS
Vos destinations (exemple de préférences) : Côte d’Ivoire, États-Unis, Ghana.
Langue choisie : français + anglais.
Un mail court pour les destinations sélectionnées ; votre accès Monde couvre
les 31 éditions, même si votre mail n’en sélectionne que quelques-unes.
Aucun article international réel : démonstration de format sans fausse actualité.
Lire l’édition complète : URL non configurée — bouton désactivé.
Préférences et désinscription : service non configuré dans ce modèle non envoyé.

ENGLISH
Your destinations (example preferences): Côte d’Ivoire, United States, Ghana.
Selected language: French + English.
A short email for selected destinations; World access covers all 31 editions,
even when you choose only a few for your email.
No real international articles: format demonstration without invented reporting.
Read the full edition: URL not configured — button disabled.
Preferences and unsubscribe: service not configured in this unsent template.

Aucun paiement, aucun abonnement réel, aucun envoi.
No payment, no real subscription, no sending.
'''
html = '''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body style="margin:0;background:#f3f4f6;font:16px/1.6 Arial,Helvetica,sans-serif;color:#0F2A60"><table role="presentation" style="width:100%;max-width:640px;margin:auto;background:white;border-collapse:collapse"><tr><td style="padding:24px"><h1 style="font-size:26px">WELISPEAK — Monde / World</h1><p style="background:#fff6d9;padding:12px">DÉMONSTRATION · NON ENVOYÉ<br>DEMONSTRATION · UNSENT</p><h2 style="font-size:22px">Français</h2><p>Vos destinations (exemple de préférences) : Côte d’Ivoire, États-Unis, Ghana.<br>Langue : français + anglais.</p><p>Un mail court, pas 31 revues : vos choix mail ne limitent pas l’accès aux 31 éditions du catalogue Monde.</p><p>Aucun article international réel : démonstration de format sans fausse actualité.</p><p aria-disabled="true" style="padding:14px;background:#e8ebef;color:#535c69">Lire l’édition complète — URL non configurée</p><p>Préférences et désinscription : service non configuré dans ce modèle non envoyé.</p><h2 lang="en" style="font-size:22px">English</h2><div lang="en"><p>Your destinations (example preferences): Côte d’Ivoire, United States, Ghana.<br>Language: French + English.</p><p>A short email, not 31 reviews: email preferences do not restrict access to all 31 World catalogue editions.</p><p>No real international articles: format demonstration without invented reporting.</p><p aria-disabled="true" style="padding:14px;background:#e8ebef;color:#535c69">Read full edition — URL not configured</p><p>Preferences and unsubscribe: service not configured in this unsent template.</p></div><p style="font-size:13px">Aucun paiement, aucun abonnement réel, aucun envoi.<br>No payment, no real subscription, no sending.</p></td></tr></table></body></html>'''

if __name__ == '__main__':
    message = EmailMessage(policy=SMTP)
    message['Subject'] = '[DÉMONSTRATION / DEMO] WELISPEAK — Monde / World'
    message['X-Unsent'] = '1'
    message.set_content(plain)
    message.add_alternative(html, subtype='html')
    root = Path(__file__).resolve().parent
    (root / 'mailMonde.eml').write_bytes(message.as_bytes())
    (root / 'mailMonde_preview.html').write_text(html)
