# Architecture

DiagPilot est un monolithe modulaire : un déploiement backend, une base relationnelle et un frontend Next.js. Les modules `vehicles`, `obd`, `knowledge`, `diagnostics`, `ai`, `garages`, `reports` et `imports` partagent une transaction SQLAlchemy mais gardent leurs contrats et services.

Le flux est : entrée validée → normalisation → recherche des connaissances fictives sourcées → règles déterministes → sortie IA strictement validée (mock par défaut) → persistance du raisonnement et événement immuable. Une réponse IA invalide est journalisée mais ne devient jamais un diagnostic.

SQLite facilite le développement local ; PostgreSQL est utilisé dans Compose. L’en-tête `X-Garage-ID` prépare l’isolation locataire. Pour le MVP, sa valeur par défaut pointe vers le garage de démonstration ; une authentification réelle devra produire ce contexte côté serveur.

## Décisions

- UUID partout pour éviter les identifiants séquentiels exposés.
- JSON uniquement pour les structures variables (mesures, preuves et règles), relationnel pour les entités et appartenances.
- Corpus versionné dans `data/fixtures`, importé explicitement et idempotent.
- Aucun LLM n’est requis pour choisir une procédure ou une branche.
- Journal append-only `diagnostic_events` et journal séparé `ai_calls`.

