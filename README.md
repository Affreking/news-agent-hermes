# News Agent — WELISPEAK

Projet de revue de presse Côte d’Ivoire en français et en anglais, préparé avec Hermes Agent. Il regroupe la validation éditoriale, les modèles de newsletter WELISPEAK, le rendu HTML/texte/MIME, un prototype d’offre internationale et un registre de numérotation officielle.

Ce dépôt est destiné à une sauvegarde privée du code et à sa maintenance. Ce n’est ni un service Cloud déployé, ni un collecteur autonome prêt à publier sans supervision. Les configurations locales, secrets, contacts, sessions, journaux et registres d’envoi ne doivent pas être versionnés, même dans un dépôt privé.

## État et limites

- Présentation bilingue WELISPEAK : logo original, palette de marque, illustrations génériques originales, variantes web et e-mail, images CID et texte de secours.
- Contrôles éditoriaux : fenêtre de publication de 24 heures en `Africa/Abidjan`, dates d’événement distinctes, résumés FR/EN, sources et réserves.
- La validation structurelle ne certifie pas la véracité des faits, les droits de reproduction, l’indépendance des sources ou la qualité de traduction : revue humaine nécessaire.
- Première identité officielle prévue : Nº 001, 1er novembre 2026. Les aperçus de lancement n’inventent aucune actualité future et ne consomment aucun numéro.
- Le registre officiel n’est PAS encore raccordé au transport SMTP portable. Ne pas utiliser ce dernier pour une publication officielle avant intégration et validation.
- La maquette Édition Monde est locale, sans paiement réel ; le choix de destinations reçues par e-mail est distinct du droit d’accès au catalogue.
- Les exemples datés du 22 octobre 2026 sont des archives de démonstration, jamais des éditions actuelles.
- Aucun horaire ni aucune autorisation d’envoi ne sont accordés par l’installation ou le clonage du dépôt.

## Architecture

| Élément | Rôle |
| --- | --- |
| `editorial.py`, `test_editorial.py` | Validation des dossiers éditoriaux, preuves déclarées, doublons et brouillons |
| `news_brief.py` | Entrée locale nécessitant un fichier éditorial explicite ; ancienne collecte conservée pour historique |
| `newsletter_design.py`, `newsletter_v3.py`, `newsletter_v4.py` | Historique des rendus ; dépendances encore utilisées par les versions suivantes |
| `welispeak_v4.py`, `welispeak_v5.py` | Modèles de marque, images et gabarits distincts web/e-mail |
| `portable_welispeak/` | Chemin portable recommandé : rendu, configuration exemple, envoi fermé par défaut, modèles et tests |
| `numbered_welispeak/` | Registre SQLite transactionnel, coordination des états de publication et rendu numéroté |
| `world_demo/` | Démonstration locale d’inscription, découverte de l’offre Monde, simulation d’activation et préférences |
| `data/artifacts/` | Seulement les quelques jeux rédactionnels publics explicitement autorisés par `.gitignore` |
| `data/frontend/` | Logo et scènes sources requis ; les aperçus générés ordinaires ne sont pas sauvegardés |
| `secure_smtp.py` | Adaptateur local au Trousseau macOS, sans mot de passe dans le code |
| `mailer.py`, `send_approved_test.py`, `scheduler.py` | Interfaces historiques/opérationnelles : ne pas lancer comme exemples d’installation |
| `docs/` | Dépendances, sécurité et périmètre de sauvegarde |

Les scripts historiques comportent des chemins propres au Mac d’origine et des dates figées. Ils sont conservés pour maintenance sans modification de leur comportement. Pour un autre ordinateur, commencer par `portable_welispeak/` et consulter ses instructions ; ne pas exécuter les anciens scripts d’envoi ou de programmation pour tester le clonage.

## Prérequis

- Python 3.10+ pour le package portable, la numérotation et la maquette locale.
- Git pour le versionnement ; GitHub CLI est utile pour authentifier le propriétaire et maintenir le dépôt, sans être une dépendance du runtime.
- Bibliothèque standard Python pour les modules portables : aucune installation `pip` obligatoire.
- Des tests des outils racine requièrent les jeux d’archives et ressources graphiques inclus.
- `sips` sur macOS uniquement si les illustrations PNG doivent être régénérées depuis les SVG des anciens générateurs. Les PNG du package portable sont déjà inclus.
- Hermes, un modèle fonctionnel et des outils web sont nécessaires à la recherche/rédaction assistée. `hermes_tools` n’est pas une dépendance standard installable par ce projet : les anciens collecteurs ne doivent pas être supposés opérationnels hors de leur runtime Hermes.
- Les exécutions quotidiennes exigent un hôte disponible, un ordonnanceur actif et des autorisations explicites. Le clonage ne configure aucun de ces services.

## Installation et essais sans réseau SMTP

Depuis la racine du projet :

```sh
python3 --version
python3 -m unittest test_editorial -v
(cd portable_welispeak && python3 -m unittest discover -s tests -v)
(cd numbered_welispeak && python3 -B -m unittest discover -s tests -v)
(cd world_demo && python3 -m unittest test_demo -v)
```

Créer un aperçu d’archive, sans envoi :

```sh
cd portable_welispeak
python3 welispeak.py examples/archive_20261022.json --output preview
```

Ouvrir `preview/newsletter.html` dans son navigateur. `newsletter.txt` fournit le texte complet ; `newsletter_unsent.eml` est un brouillon MIME. Le nom `unsent` ne constitue pas une autorisation d’envoi.

Le projet possède plusieurs dossiers `tests` : les exécuter séparément, comme ci-dessus, pour éviter les collisions de modules.

## Configuration et secrets

Copier `portable_welispeak/config.example.json` vers un fichier local ignoré, puis renseigner les paramètres non secrets après revue. L’expéditeur futur de domaine reste désactivé. Les URL WhatsApp, LinkedIn, préférences et désinscription restent nulles tant que les destinations et services réels ne sont pas configurés.

Les secrets ne doivent jamais être saisis dans le dépôt, l’historique shell, un fichier README ou une URL de remote Git. Utiliser le Trousseau macOS sur la machine d’origine, ou un gestionnaire de secrets adapté sur un autre hôte. Ne pas transférer automatiquement le Trousseau, `mail_settings.json`, `.env`, `~/.hermes`, des tokens ou une base d’abonnés.

L’envoi portable est bloqué par défaut et exige plusieurs validations. Les essais de maintenance se limitent aux rendus et tests hors envoi. Consulter `portable_welispeak/README_V6.md` avant toute future activation.

## Numérotation officielle

`numbered_welispeak/` utilise un registre SQLite dédié et des transactions pour sérialiser l’allocation. Les mêmes numéros s’appliquent aux variantes linguistiques et géographiques d’un bulletin. Une publication confirmée fait avancer le compteur une seule fois ; tests, aperçus et renvois n’incrémentent pas la production. Une correction garde son numéro. Une ambiguïté SMTP bloque les reprises jusqu’à rapprochement manuel.

Les bases SQLite ne sont pas versionnées. Leur sauvegarde chiffrée et leur restauration relèvent d’une procédure d’exploitation distincte : cloner Git ne restaure ni les envois passés ni le compteur réel. Ne pas réinitialiser ces bases pour contourner un blocage.

## Maquette internationale

```sh
cd world_demo
python3 server.py --port 8011 --demo-activation
```

Accès uniquement sur `http://127.0.0.1:8011/`. Le flag autorise une simulation locale clairement identifiée, jamais un paiement. Les 30 destinations supplémentaires proviennent du référentiel confirmé du projet ; Côte d’Ivoire reste séparée. Les contenus internationaux non préparés sont marqués comme démonstration, sans actualités ni sources inventées.

## Maintenance et sauvegarde Git

Avant chaque commit : examiner les fichiers sélectionnés, vérifier `.gitignore`, analyser les secrets et lancer les tests concernés. Ajouter explicitement les fichiers approuvés plutôt que tout l’environnement Hermes. Ne pas committer des fichiers de configuration locale pour résoudre une dépendance manquante.

Le dépôt GitHub doit être créé PRIVÉ, uniquement après accord du propriétaire. Le premier push exige aussi son autorisation explicite. La préparation locale n’autorise ni création distante, ni push, ni GitHub Actions, ni hébergement, ni e-mail.

Le code contient encore des adresses de contact et des chemins locaux historiques : ce ne sont pas des secrets d’authentification, mais ils doivent être relus avant sauvegarde distante. Voir le rapport local d’audit, exclu du dépôt.

## Droits et ressources

Les illustrations génériques originales sont documentées CC0 dans les modèles. Le logo WELISPEAK reste une marque et n’est pas couvert par cette licence. Les articles et preuves consultés restent soumis aux droits de leurs éditeurs ; leurs copies de collecte brutes sont exclues de Git. Aucune licence générale du code n’est accordée automatiquement par ce README.
