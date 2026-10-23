from datetime import datetime, timezone
C = {'fr': {'mast': 'REVUE DE PRESSE — CÔTE D’IVOIRE', 'date': '', 'lang': 'FRANÇAIS', 'draft': 'Brouillon — à valider', 'toc': 'L’essentiel en 30 secondes', 'read': 'Lire la source', 'stakes': 'Les enjeux', 'caveat': 'À retenir avec réserve', 'method': 'Sources, crédits et méthode', 'period': 'Publications du 21 au 22 octobre 2026 · heure d’Abidjan', 'published': 'Publié le', 'event': 'Événement', 'lead': 'À LA UNE', 'credit': 'Pictogrammes génériques originaux : Hermes Agent pour CI Press Brief, licence CC0 1.0. Ils illustrent les thèmes, pas les événements. Aucune photo de presse réutilisée. Les grandes images sont réservées aux photographies pertinentes dont les droits de réutilisation sont établis.', 'warning': 'Sélection révisée, non envoyée. Les sources et leurs réserves restent indiquées dans chaque article ; la mise en page ne vaut pas certification des faits.', 'methodtext': '', 'end': 'Document de relecture · Non envoyé'}, 'en': {'mast': 'PRESS BRIEF — CÔTE D’IVOIRE', 'date': '', 'lang': 'ENGLISH', 'draft': 'Draft — pending review', 'toc': 'The essentials in 30 seconds', 'read': 'Read the source', 'stakes': 'Why it matters', 'caveat': 'Essential caveat', 'method': 'Sources, credits and methodology', 'period': 'Publications from 21–22 October 2026 · Abidjan time', 'published': 'Published', 'event': 'Event', 'lead': 'LEAD STORY', 'credit': 'Original generic pictograms: Hermes Agent for CI Press Brief, CC0 1.0 licence. They illustrate subjects, not reported events. No press photographs reused. Large images are reserved for relevant photographs with established reuse rights.', 'warning': 'Revised selection, not sent. Sources and caveats remain visible in each story; visual presentation does not certify the facts.', 'methodtext': '', 'end': 'Review document · Unsent'}}

def date_label(stamp,lang):
 d=datetime.fromisoformat(stamp)
 if d.utcoffset() is None: raise ValueError("Timezone required")
 d=d.astimezone(timezone.utc)
 return d.strftime("%Y-%m-%d %H:%M UTC")

def event_label(value,lang):
 return str(value)
