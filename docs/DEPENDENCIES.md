# Dépendances et chemins de maintenance

## Exécution portable

Les modules `portable_welispeak`, `numbered_welispeak` et `world_demo` utilisent la bibliothèque standard Python : `sqlite3`, `ssl`, `email`, `http.server`, `unittest`, `zoneinfo`, etc. Le minimum documenté est Python 3.10 ; sur certaines distributions Linux, installer aussi le paquet système de fuseaux `tzdata` si `Africa/Abidjan` n’est pas disponible.

`portable_welispeak/requirements.txt` reste la référence du package portable : il n’impose aucune dépendance pip. Aucun environnement virtuel ni paquet installé sur le Mac n’est copié dans Git.

## Dépendances internes à préserver

- `welispeak_v5.py` importe `newsletter_v3`, lequel importe les illustrations de `newsletter_design`.
- `welispeak_v4.py`, `newsletter_v4.py` et les tests historiques utilisent aussi ces modules. Ne pas supprimer une ancienne version au motif qu’elle semble obsolète sans analyse d’imports.
- `numbered_welispeak/renderer.py` lit le package frère `portable_welispeak` et son logo. Garder ces répertoires voisins dans le dépôt.
- Les modèles racine utilisent les jeux d’archives rédactionnels et le logo sous `data/`; ces quelques fichiers sont explicitement autorisés par `.gitignore`.
- Les tests de distribution portable lisent les fixtures `example_output/` et `VERIFICATION_V6.json`. Ces exceptions sont examinées, datées et non opérationnelles.
- `world_demo/test_demo.py` attend le modèle MIME non adressé `mailMonde.eml`. Il est conservé comme fixture et non comme e-mail d’exploitation.

## Dépendances spécifiques à la machine

- `secure_smtp.py` utilise les frameworks Security/CoreFoundation de macOS via `ctypes`. Il n’est pas portable sur Linux ; le package portable utilise une injection de secret distincte.
- Certains générateurs racine utilisent `/usr/bin/sips` pour convertir les SVG en PNG. Les assets portables sont pré-rendus, sans cette exigence.
- Les anciens collecteurs de `news_brief.py` tentent d’importer `hermes_tools`. L’accès aux outils et au modèle est fourni par Hermes, pas par un package déclaré ici. Ces fonctions historiques ne remplacent pas une nouvelle collecte validée.
- Git et `gh` servent à la sauvegarde et à la maintenance, pas à la génération de newsletters.

## Tests sans envoi

```sh
python3 -B -m unittest test_editorial test_newsletter_design test_newsletter_v3 test_newsletter_v4 test_welispeak test_welispeak_v5 -q
(cd portable_welispeak && python3 -B -m unittest discover -s tests -q)
(cd numbered_welispeak && python3 -B -m unittest discover -s tests -q)
(cd world_demo && python3 -B -m unittest test_demo -q)
```

Les suites sont lancées séparément pour éviter les collisions entre modules `registry`, `tests`, etc. Certains tests créent des états temporaires, des rendus et un serveur HTTP local de test ; ils ne doivent jamais utiliser de registre de production ni le SMTP réel.

Une copie isolée des candidats Git est utilisée pendant la préparation pour vérifier que les exclusions n’enlèvent pas un fichier nécessaire. Réussir les tests sur le seul dossier opérationnel ne prouve pas qu’un clonage sera complet.
