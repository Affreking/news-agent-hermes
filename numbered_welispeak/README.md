# WELISPEAK — numérotation officielle isolée

Python 3.10+ (stdlib uniquement). Aucun SMTP, aucune tâche, aucun réseau. L’ensemble des nouveaux fichiers est limité à `numbered_welispeak/`. Les modules et assets de `../portable_welispeak/` sont lus sans modification ni écriture de bytecode.

## Artefacts livrés

- `preview/launch_fr.html`, `preview/launch_en.html` : Nº001, **1er novembre 2026 / 1 November 2026**, APERÇU DU LANCEMENT / LAUNCH PREVIEW. Zéro article, logo original embarqué, palette/style portable conservés.
- `preview/manifest.json` : `published=false`, `approved_for_send=false`, `official_number_reserved=false`, SHA-256 des HTML. Aucun registre de production créé.
- `registry.py`, `coordinator.py`, `renderer.py`, `tests/`.

```sh
cd /Users/romaric/news_brief/numbered_welispeak
python3 -B -m unittest discover -s tests -v
python3 -B renderer.py  # régénère uniquement les deux aperçus et leur manifeste
```

## Interfaces de registre

```python
from registry import Registry
from coordinator import PublicationCoordinator

# Exemple d’interface seulement. Ne pas exécuter pour une prévisualisation.
# Choisir UN chemin persistant dédié, commun à tous les processus de publication.
r = Registry('/chemin/dedie/official.sqlite3', environment='production')
c = PublicationCoordinator(r)
# Après le 1er novembre, validation éditoriale et autorisation humaines explicites :
a = c.prepare('2026-11-01', approved_for_send=True)
identity = c.identity(a['token'], language='fr', destination='web')
# Le futur transport appelle une seule branche avec sa preuve réelle :
c.smtp_result(a['token'], outcome='accepted', evidence='réponse positive finale à DATA')
# failure : échec certain AVANT publication, libère le numéro.
# ambiguous : réponse DATA perdue / déconnexion pendant DATA, gèle le registre.
```

La date doit être littéralement `YYYY-MM-DD`, >= 2026-11-01 et non future selon Africa/Abidjan. La première confirmation doit concerner le 2026-11-01 : aucune renumérotation silencieuse d’un autre jour en Nº001. Le compteur n’est jamais calculé à partir de l’écoulement des jours.

`Registry(path, environment='test', now=...)` : horloge injectée réservée aux tests ; production refuse `now`. Chaque base porte son environnement, une réouverture avec l’autre mode échoue. Aucun chemin par défaut, aucune variable globale de registre et aucune migration du registre existant. Les tests utilisent exclusivement `TemporaryDirectory`.

Toutes les mutations sont des transactions SQLite `BEGIN IMMEDIATE` / `synchronous=FULL`. Unicité `(bulletin,date)` et `(bulletin,number)`. Une ligne `reserved` ou `ambiguous` constitue le verrou durable global de WELISPEAK, sans TTL et sans vol automatique : elle survit à la fermeture/au crash du processus. Un seul numéro peut être en attente ; FR/EN/web/destinations/recipients ne créent pas d’identités différentes.

- `reserve(date, approved_for_send=True)` / `prepare(...)` réserve `last+1`, journalise l’identité, sans avancer le compteur.
- `confirm(token, evidence=...)` publie et avance atomiquement, une seule fois. Une répétition pour un numéro déjà publié est idempotente, même après publication d’un numéro ultérieur.
- `fail(token, evidence=...)` supprime uniquement une réservation dont l’échec avant publication est certain ; conserve l’identité dans le journal et permet de réutiliser le numéro avec un nouveau jeton.
- `ambiguous(token, evidence=...)` gèle ; ni confirmation automatique, ni libération, ni nouvelle tentative.
- `reconcile(token, published=True|False, operator='...', evidence='...')` : décision manuelle documentée pour une ambiguïté ou réservation orpheline. Aucun retry automatique. Une décision publiée avance le compteur, une décision non publiée libère le numéro.
- `edition(date)`, `last_number()`, `journal()` lisent l’état.
- `metadata(date, mode='resend', language=..., destination=...)` réutilise une édition publiée, sans incrément.
- `metadata(date, mode='correction', correction_reason='...')` conserve le numéro et journalise la correction. Le renderer affiche **ÉDITION CORRIGÉE / CORRECTED EDITION**. Appeler une fois, réutiliser l’objet pour chaque langue/destination.
- Format `f'Nº{number:03d}'` : 001 … 999, 1000, sans troncature.

## Contrat SMTP du coordinateur (pas de transport fourni)

Le futur transport doit enregistrer `accepted` **immédiatement après la réponse positive finale à DATA, avant QUIT et avant toute sortie de context manager SMTP**. Un échec QUIT ultérieur peut être journalisé par `quit_failed(...)` et ne dépublie pas l’édition. Une déconnexion pendant DATA ou avant lecture de la réponse finale est `ambiguous`, jamais `failure`. Une partie des destinataires acceptée représente déjà une publication : ne jamais libérer le numéro parce qu’une autre destination a échoué.

Si DATA est accepté mais que l’écriture SQLite échoue, arrêter immédiatement le transport : la réservation durable bloque la suite ; rapprocher manuellement la preuve d’acceptation et le registre. Aucune transaction SQLite ne peut rendre atomiques une livraison distante et un disque local.

**`../portable_welispeak/sender.py` n’est PAS câblé à ce registre. Ne pas l’utiliser pour publier officiellement ces artefacts ; son activation doit rester interdite tant qu’un futur raccordement explicitement autorisé et testé n’existe pas. Aucun paramètre de désactivation ni planification existante n’a été modifié ici.**

## Renderer et archives

- `launch_preview(output, portable_root=...)` : sans accès SQLite ; maquette vide uniquement.
- `build_numbered(data, config, metadata, portable_root=..., context_preview=False)` : wrapper du vrai `welispeak.build` et du template portable. Ajoute Nº à l’objet MIME, texte et bannières FR/EN, deux pièces HTML numérotées, et `manifest`. Ne réserve ni ne confirme jamais.
- `write_archive(artifact, target)` : nouveau dossier exclusivement, refuse tout écrasement ; HTML bilingue, FR, EN, texte, `.eml` **non envoyé**, manifeste numéroté et empreintes.
- L’exemple portable est une archive du 22 octobre, pas une édition future. Utilisation autorisée uniquement avec `context_preview=True`, bannière CONTEXTE HISTORIQUE DU 2026-10-22 / HISTORICAL CONTEXT FROM 2026-10-22 ; jamais transformé en actualités du 1er novembre.
- Date du contenu différente de celle du numéro : refus sauf contexte historique explicite.
- Tous les rendus restent `approved_for_send=false`, `published=false`, `sent=false`, même si une identité déjà publiée est réutilisée. L’approbation éditoriale/d’envoi appartient exclusivement à un humain, pas au renderer.

## Tests et limites

Cycles RED→GREEN exécutés avant chaque tranche de fonctionnalité. Tests réels : 8 processus simultanés (un gagnant), verrou durable après réouverture, crash en transaction et rollback, abort SQLite sur réservation/confirmation, 1000 publications temporaires, idempotence, corrections et multi-langues/destinations, libération, gel/réconciliation, DATA accepté avant erreur QUIT, archive et MIME réels. Aucun test n’appelle un serveur SMTP.

Ce module est spécialisé WELISPEAK, registre unique sur **disque local**. Pas d’atomicité SMTP/SQLite, de haute disponibilité multi-hôtes, d’audit inviolable ou d’automatisation de réconciliation. Un utilisateur pouvant modifier le fichier SQLite peut modifier son contenu. Les marqueurs d’environnement préviennent les confusions de chemin, pas un administrateur malveillant. Les HTML ont été ouverts localement ; pas de test Gmail ni de livraison réelle. La validation structurelle et les tests logiciels ne certifient pas la véracité éditoriale.
