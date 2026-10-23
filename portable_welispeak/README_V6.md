# WELISPEAK V6 — package portable, non déployé

Python 3.10+ sur Linux/macOS. Bibliothèque standard seulement, aucune installation pip nécessaire. Sources originales et configuration SMTP existantes inchangées. Aucun ordonnanceur ni collecte automatique dans ce package.

## Démarrage hors ligne

Depuis le dossier extrait :

```sh
python3 -m unittest discover -s tests -v
python3 welispeak.py examples/archive_20261022.json --output preview
python3 sender.py examples/archive_20261022.json
```

La dernière commande est un **dry-run**, sans réseau SMTP, sans lecture du secret et sans écriture du registre. Ouvrir `preview/newsletter.html` dans un navigateur. `newsletter.txt` est le texte intégral ; `newsletter_unsent.eml` est un brouillon MIME non envoyé. L'exemple du 22 octobre 2026 est marqué ARCHIVE EXEMPLE et techniquement interdit d'envoi, quelle que soit sa fraîcheur apparente. Ne jamais modifier ses dates pour le rendre envoyable.

Un message unique : FR complet, puis EN complet ; liens internes Français/English ; lecture séquentielle si le client mail ne suit pas les ancres. Une image logo visible, sept pièces CID (logo original + six scènes). Le fichier HTML navigateur embarque les PNG. Les scènes sont génériques et non des photos de l'événement. Choisir `scene_index` 0–5 par article selon le sujet ; ne pas représenter un événement avec une scène sans rapport. Par défaut, scènes 0 poisson, 1 studio, 2 forêt, 3 investissement, 4 mobilité, 5 agriculture ; pour 7–8 sujets, réutiliser seulement une scène pertinente et contrôler le choix.

## Configuration sans secrets

Copier `config.example.json` vers `config.local.json` **hors archive**. Conserver l'adresse expéditeur actuelle en renseignant `sender_email` ; elle n'a pas été lue ni copiée depuis l'installation existante. Le nom d'affichage est imposé : `WELISPEAK — L’essentiel`. `newsletter@welispeak.com` est une identité future désactivée et explicitement refusée en V6. Renseigner `smtp_host`, facultativement `smtp_username`, et conserver le port 587. Aucun mot de passe dans JSON.

Les cinq destinations `whatsapp_channel_url`, `linkedin_url`, `linkedin_kind`, `preference_url`, `unsubscribe_url` sont configurables. Les URL sont `null` par défaut (pas de faux lien) ; `linkedin_kind` vaut `null` par défaut et accepte `newsletter`, `page` ou `profile` (libellé générique LinkedIn si null). Utiliser uniquement des URL HTTPS réelles. Invitation WhatsApp après chaque sommaire ; Restons connectés après les derniers articles de chaque langue. Sans URL : bouton non cliquable, lien à configurer. Sans gestion effective des préférences/désabonnements, ne pas élargir la diffusion.

## Édition fraîche et contrôle rédactionnel

La génération IA avec accès web est **nécessaire** : voir `PROMPT_EDITION_V6.md` et `sources.json`. Aucun collecteur autonome n'est implémenté. Le JSON de l'exemple expose le schéma : `cutoff` ISO avec fuseau explicite, 6–8 `articles` (story_id, source, url, published_at avec fuseau, event_date, scene_index facultatif ; fr/en avec category/title/summary/relevance/caveat/takeaway), `limits_fr`, `limits_en`. Ajouter `method_fr`/`method_en` pour conserver les preuves et limites de la méthode éditoriale. `extra_sources` facultatif : liste d'URL réelles. Pour une édition neuve seulement, ajouter `approved_for_send: true` après validation humaine. Ne pas copier `archive_example`.

Le validateur vérifie structure, fenêtre de publication 24h, fuseaux, doublons et deux résumés distincts ; il ne prouve ni la véracité des articles, ni le fuseau réel du média, ni la qualité de la traduction, ni l'indépendance des sources. Les preuves doivent être établies par la rédaction. Ne pas antidater ni remettre à l'heure une ancienne édition.

## Envoi futur, bloqué par défaut

Aucun envoi n'est requis pour tester ce package. Après accord explicite seulement : config `send_authorized: true`, édition `approved_for_send: true`, secret fourni via l'environnement sécurisé `WELISPEAK_SMTP_PASSWORD`, puis :

```sh
python3 sender.py fresh.json --config config.local.json --state runtime/delivery.sqlite3 --send
```

Ne pas saisir le secret dans un argument de commande, un fichier du package, un historique shell ou une conversation. Injection via gestionnaire de secrets de l'hébergeur à mettre en place séparément. **Ne pas exécuter cette commande pendant la migration préparatoire.**

Destinataire et enveloppe uniques : `ndriaffre@gmail.com`, aucun Cc/Bcc. Fraîcheur maximale : 2 heures depuis `cutoff`, jamais dans le futur, contrôlée avant réservation, connexion et émission. SMTP 587 + STARTTLS avec vérification certificat/nom par le magasin CA système. Les tests transport sont simulés, pas une validation du serveur réel.

Registre SQLite durable : clé jour UTC/Abidjan + destinataire, état `attempting` validé avant toute connexion SMTP ; puis `accepted` ou `ambiguous`. Les détails d'erreur SMTP sont masqués. Tout état existant bloque la réémission, y compris une correction le même jour. Conserver ce registre sur stockage persistant, sauvegardé, instance unique, permissions privées ; ne jamais le supprimer pour tenter à nouveau. Après interruption, `attempting` est aussi ambigu. Vérifier la livraison côté fournisseur avant toute décision humaine ; pas de reprise automatique. L'acceptation SMTP ne prouve pas la réception en boîte.

## Test distant sans déploiement

1. Transférer uniquement l'archive vérifiée sur un Linux de test avec Python 3.10+.
2. Extraire dans un dossier isolé ; aucun fichier de secrets ni registre historique à transférer.
3. Exécuter les trois commandes de démarrage, sans `--send`, dans un environnement sans accès SMTP.
4. Vérifier les 7 tests et ouvrir le rendu. Contrôler visuellement FR/EN à 360/390/768/1440 px ; tester les ancres et l'absence de liens sociaux inventés.
5. Ne pas créer de cron, service, récurrence ou déploiement. La cible prévue de 06h00 GMT/Africa/Abidjan reste une intention, pas une activation.

L'autonomie Mac éteint nécessite séparément un hôte permanent, Hermes et son accès IA/recherche autorisés, secrets sécurisés, stockage SQLite persistant et accord de récurrence. Rien de cela n'est provisionné ici. Linux réel, SMTP réel et rendu Gmail ne sont pas attestés par les tests locaux.

## Distribution

`python3 package_release.py` reconstruit uniquement une liste blanche de fichiers. Exclut config locale, registre, caches et historiques. Scanner binaire des chemins personnels et marqueurs interdits ; ne lit jamais l'ancien fichier de paramètres ni les secrets. Un scan de marqueurs n'est pas une preuve mathématique d'absence de toute donnée sensible : la garantie principale est la copie strictement limitée aux modèles, sept PNG et un JSON rédactionnel public. Voir `VERIFICATION_V6.json` pour les résultats locaux et limites.
