# Périmètre Git et sécurité

## Principe

Le dépôt contient uniquement le projet News Agent/WELISPEAK, pas son environnement Hermes partagé. Un dépôt GitHub privé n’est pas un coffre-fort : les secrets et données d’exploitation en sont exclus avant le premier commit.

## Inclus après examen

- Code Python, JavaScript, CSS et modèles HTML des modules racine, portable, numérotation et démonstration Monde.
- Tests automatisés, instructions éditoriales, documentation, exemples de configuration fermés par défaut.
- Logo, illustrations et sources SVG nécessaires à la reproduction de la présentation.
- Quelques exemples rédactionnels datés et explicitement archivés ; référentiel des destinations.
- Aperçus de lancement sans actualités futures inventées.
- Fixtures de sortie du package portable requises par ses tests de distribution.

## Exclus

- `mail_settings.json`, `.env*` sauf exemples explicites, configurations locales et credentials.
- Bases SQLite, compteurs de production, sessions, registres d’envoi et données d’abonnés.
- Journaux, caches Python, environnements virtuels, dépendances installées, ZIP et rendus courants générés.
- Copies brutes de collecte, pages externes téléchargées, captures QA et historiques d’exécution.
- L’intégralité de `~/.hermes`, des clés SSH, du Trousseau et des profils d’autres agents.

Les fichiers exclus restent sur la machine ; `.gitignore` ne les supprime pas. Le compteur officiel et l’historique d’envoi doivent être sauvegardés séparément de Git, avec chiffrement et procédure de restauration contrôlée.

## Points à faire approuver avant push

Le code historique et certains exemples contiennent des adresses e-mail de destination et des chemins propres au Mac d’origine. Ils ne sont pas des mots de passe, mais demeurent des données à examiner. Ils sont conservés dans les sources pour ne pas changer le comportement de l’agent ; un dépôt public n’est pas approprié sans revue supplémentaire.

Une exception précise à l’exclusion des `.eml` concerne `portable_welispeak/example_output/newsletter_unsent.eml`. C’est une fixture requise par le packaging : X-Unsent=1, seul destinataire le propriétaire, sans expéditeur, Cc/Bcc ni credential. Elle n’est pas un message reçu, ni un journal de livraison, ni une autorisation d’envoi. Si le propriétaire préfère exclure toute adresse du dépôt, il faut préparer une autre fixture et adapter les tests dans un changement distinct, sans modifier la configuration opérationnelle.

Les archives rédactionnelles peuvent contenir des références à des articles de presse ; les droits de ces éditeurs ne sont pas transférés avec le dépôt. Les preuves brutes téléchargées sont exclues. Le logo reste une marque, distincte de la licence CC0 des scènes originales.

## Contrôles

```sh
python3 tools/audit_repository.py
git status --short --untracked-files=all
git diff --cached --stat
```

Le scanner compare en mémoire les valeurs sensibles de l’environnement et recherche des formats connus de tokens, clés privées et secrets littéraux. Il n’affiche ni n’enregistre les valeurs. Il vérifie aussi les chemins privés de runtime, les liens symboliques et les métadonnées PNG suspectes. Les résultats détaillés et listes exactes restent dans `.repo-audit/`, ignoré par Git.

L’absence de détection n’est pas une preuve absolue de confidentialité. La revue des fichiers sélectionnés et le contrôle d’un éventuel historique Git restent indispensables. Aucun `git add -f`, aucune publication automatique, aucun workflow d’envoi GitHub Actions ne sont mis en place par cette préparation.

## Authentification recommandée

GitHub CLI avec authentification HTTPS dans le navigateur et conservation dans le Trousseau macOS. Ne transmettre aucun mot de passe, token ou code de double authentification dans la conversation. Ne pas utiliser de remote contenant un token, de helper Git en clair ou `--insecure-storage`.

La création du dépôt distant et le premier push nécessitent une autorisation explicite séparée. Vérifier ensuite la visibilité PRIVATE et l’égalité des commits local/distant.
