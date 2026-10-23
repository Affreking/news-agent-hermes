# Procédure réutilisable — maquette d'accès local

- Parser le tableau source exact puis vérifier l'égalité du JSON avec ce parseur ; séparer la base CI des 30 destinations pour éviter un compte de 30 incluant CI.
- Tester d'abord le refus du catalogue gratuit et l'absence de droits après la case marketing, puis simuler explicitement l'activation via un flag serveur fermé par défaut.
- Garder l'état du droit côté serveur SQLite ; ne jamais employer une préférence de mail comme filtre de droits de lecture.
- Servir les fichiers avec une liste fermée, pas via un répertoire statique générique qui pourrait exposer SQLite ou les sources.
- Refuser les clés d'email avant stockage ; ne pas journaliser corps de requêtes ou identifiants de session.
- Pour toute archive, afficher date, avertissement ancien/pas actualité de lancement, source et réserves dans chaque langue.
- Garder les éditions internationales en contenu structurel de démonstration tant qu'aucune collecte n'est préparée ; ne pas remplir avec de faux faits ou sources.
- Tester le mail multipart parsé, sans destinataire ni href de lecture lorsque l'URL officielle n'est pas configurée.
- Mesurer dans le navigateur chaque écran et chaque langue aux quatre largeurs ; inspecter une capture d'article, pas seulement l'en-tête.
- Arrêter le serveur de QA ; laisser l'utilisateur démarrer son serveur avec son port et sa base.
