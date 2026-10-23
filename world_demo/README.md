# WELISPEAK Monde — maquette locale FR/EN

## Lancer (Python 3, bibliothèque standard uniquement)

```sh
cd /Users/romaric/news_brief/world_demo
python3 server.py --port 8011 --demo-activation
```

Ouvrir `http://127.0.0.1:8011/`. Le bind est fixé à **127.0.0.1 uniquement** ; aucun argument ne permet une écoute publique. Sans `--demo-activation`, l'activation simulée retourne 403. Le serveur n'est pas un produit prêt pour production.

Base SQLite par défaut jetable sous `.runtime/`, supprimée à l'arrêt normal ; ne contient ni nom ni adresse email. Option explicite pour conserver uniquement l'état des sessions :

```sh
python3 server.py --port 8012 --db .runtime/demo.sqlite --demo-activation
```

Cookie de session aléatoire 256 bits, HttpOnly, SameSite=Strict, durée 24 h. HTTP loopback uniquement (pas de cookie Secure sur ce HTTP local). État gratuit initial et droits conservés côté SQLite, non dans le navigateur. Token CSRF pour mutations, contrôle Host/Origin, CSP et liste fermée de fichiers servis. Une autre session reste gratuite. L'interface webhook future **rejette tous les événements** et ne peut accorder de droits ; une vraie intégration demanderait authentification/signature, protection anti-rejeu, idempotence et validation des transactions. Aucun SDK paiement, SMTP, appel réseau sortant, publication, contact réel ni tâche planifiée.

## Les 7 écrans

Navigation visible et routes SPA : `/#welcome`, `/#signup`, `/#offers`, `/#preview`, `/#activation`, `/#preferences`, `/#catalogue`. Bascule Français / English visible sur tous les écrans ; langue UI indépendante de la langue du mail.

- Inscription gratuite simulée avec adresse fixe désactivée `example.invalid` (jamais transmise). La case facultative Découvrir l'Édition Monde ne donne **aucun droit**.
- Comparaison base CI gratuite FR/EN et Monde payant CI + 30, tarif à définir.
- Aperçu public : archive Côte d'Ivoire **22 octobre 2026**, avec sources, dates et réserves d'origine. Explicitement ancien, pas actualité du 1er novembre ; aucune nouvelle vérification en direct.
- Simulation explicite d'activation après paiement, **sans aucun paiement réel**, possible uniquement avec flag serveur.
- Préférences réservées au statut Monde simulé : destinations et langue fr/en/both ; elles personnalisent le mail, jamais le droit de lecture.
- Catalogue protégé contenant les **31 éditions**, même si une seule destination est choisie pour le mail. Les 30 destinations internationales ne contiennent que des structures de démonstration, sans fait récent ni source fictive.

## Endpoints

| Méthode | Chemin | Accès / rôle |
|---|---|---|
| GET | `/api/session` | Créer/lire la session et token CSRF |
| GET | `/api/overview` | Référentiel public ; CI séparée et 30 destinations |
| GET | `/api/ci` | Archive CI publique du 22 octobre 2026 |
| GET | `/api/catalogue` | **403 si gratuit**, 31 entrées avec droit Monde |
| POST | `/api/register` | `{"discover_world":true}` ; aucune adresse acceptée, aucun droit accordé |
| POST | `/api/demo/activate` | `{"confirm":true}` ; flag serveur + CSRF requis |
| POST | `/api/preferences` | `{"destinations":["US"],"language":"en"}` ; droit Monde + CSRF ; liste unique, non vide |
| POST | `/api/webhook` | **501 systématique**, authentification future non configurée |
| GET | `/mailMonde.eml` | Modèle MIME non envoyé, sans destinataire |

Tous les POST de session demandent `X-CSRF-Token` issu de `/api/session`. Les fichiers source, le registre brut, la base et les tests ne sont pas servis comme fichiers statiques.

## Données et modèles

- `registry.py` parse le **tableau exact §18** de `AGENT_SPEC_CI_PRESS_BRIEF_v2.md`, contrôle nombres, ordre et unicité. `destinations.json` contient les 30 destinations séparément de `base` CI. Les libellés du tableau sont conservés, sans déductions depuis une chaîne de codes. Le registre exprime des périmètres éditoriaux, pas des statuts politiques.
- Pour régénérer : `python3 registry.py /Users/romaric/Downloads/AGENT_SPEC_CI_PRESS_BRIEF_v2.md`.
- `archive_20261022.json` : copie de l'archive fournie, non modifiée.
- `assets/` : copie intacte du logo original et des six scènes validées depuis `portable_welispeak/assets`. Logo non recoloré, non recadré, ratio intrinsèque 4:1. Illustrations génériques, pas photographies d'événements ; aucune nouvelle licence inventée.
- `index.html`, `style.css`, `app.js` : interface locale sans dépendance distante ; conteneur 720 px, bleu `#0F2A60`, or `#F0B100`, corps ≥16 px sur téléphone, cibles principales ≥44 px.
- `mailMonde.eml` : multipart texte/HTML FR/EN court, sans To/Cc/Bcc ni expéditeur inventé, marqué non envoyé ; sélection illustrative CI/US/GH, **pas 31 revues**. URL de lecture complète non configurée donc non cliquable ; préférences/désinscription explicitement non configurées. Aucun href local ou URL publique inventée.
- `build_mail.py` régénère le MIME et `mailMonde_preview.html` pour inspection hors envoi. L'aperçu web des préférences reflète quant à lui le vrai sous-ensemble de la session.

## Tests et vérification

```sh
python3 -m unittest -v
node --check app.js   # optionnel, si Node est installé ; pas une dépendance du serveur
```

TDD par tranches : référentiel RED→GREEN, droits HTTP RED→GREEN, interface RED→GREEN, MIME RED→GREEN. Suite standard : **4 tests** dont un parcours HTTP complet (serveur réel sur port aléatoire, DB isolée supprimée). Contrôles : case sans droits, catalogue gratuit 403, préférence gratuite 403, CSRF, faux webhook rejeté, activation désactivée, session indépendante gratuite, sélection unique valide, 31 entrées après sous-sélection, refus de champs email et absence de stockage.

Vérification navigateur réelle : inscription avec case → toujours gratuit/403 ; activation explicite → préférences US/EN → catalogue de 31 ; clic EN puis FR réussi. `browser_checks.json` : **56 combinaisons** (7 écrans × 2 langues × 360/390/768/1440 px), zéro débordement horizontal, toutes images chargées, zéro cible principale <44 px. Captures `qa-390.png`, `qa-1440.png` (article) et `qa-header-390.png`. Captures inspectées : pas de chevauchement/clipping, logo intact. Ces résultats ne constituent **pas** un test de rendu Gmail ni un envoi.

Le serveur temporaire de QA est arrêté après vérification. Aucun changement à la numérotation, SMTP, cron ni fichiers hors `world_demo`.
