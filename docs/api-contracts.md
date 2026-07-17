# Contrats API

La documentation interactive est disponible sur `/docs` et le schéma OpenAPI sur `/openapi.json`. Toutes les routes métier sont préfixées par `/api`.

Le contexte locataire accepte `X-Garage-ID`. Sans en-tête, le garage de démonstration est utilisé uniquement dans ce MVP. Les erreurs utilisent le format FastAPI `{"detail": ...}` avec un message exploitable.

Le rapport OBD canonique utilise `schema_version: "1.0"`, un objet véhicule et un scan contenant horodatage, outil, DTC, freeze frame et données live. Les modèles Pydantic refusent les champs inconnus. Les fichiers sont limités à 1 Mio et aux formats JSON/CSV.

`POST /api/imports/knowledge` accepte le corpus JSON strict décrit dans `data/fixtures/demo_knowledge.json`. Le checksum SHA-256 détecte un contenu déjà importé ; l’écriture de la source et de tous ses items utilise une seule transaction. Ce MVP refuse tout corpus qui ne porte pas `demo_only: true` à tous les niveaux.

Voir les routes et exemples directement dans Swagger, les contrats restant générés depuis les schémas exécutables.
