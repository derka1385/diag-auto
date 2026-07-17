# VehicleResolver

## Objectif

`VehicleResolver` transforme une plaque, un VIN ou une saisie technicien en identité technique stable utilisable par le diagnostic. La plaque et le VIN ne sont que des clés : Gemini reçoit la génération, la motorisation, le code moteur, la puissance, la boîte, la norme antipollution, les identifiants techniques et, lorsqu’ils sont connus, les calculateurs.

Le resolver se trouve dans `backend/app/modules/vehicle_resolution`. Il complète les routes et tables historiques sans les remplacer.

## Parcours

1. Recherche par plaque et pays.
2. Appel du fournisseur principal, puis des fallbacks si les champs critiques manquent.
3. Normalisation et fusion des résultats compatibles.
4. Retour d’un résultat résolu, ambigu ou insuffisant.
5. Si nécessaire, recherche VIN puis sélection d’une variante ou saisie manuelle.
6. Confirmation obligatoire par le garagiste avant diagnostic.

Une contradiction moteur/puissance/boîte crée une confirmation requise. Aucune variante incertaine n’est choisie silencieusement.

## Fournisseurs

| Adaptateur | État | Champs attendus |
| --- | --- | --- |
| AAA Data / SIvin | préparé, non connecté sans contrat | plaque, VIN, marque, modèle, année, CNIT, variante, puissance |
| TecAlliance / TecDoc | préparé, non connecté sans contrat | K-Type, génération, moteur, code moteur, boîte, période |
| Auto Ways | préparé, non connecté sans contrat | plaque/VIN et identité technique selon contrat |
| NHTSA vPIC | existant, optionnel | VIN, identité générale, surtout marché nord-américain |
| Mock | développement/test uniquement | scénarios fictifs explicitement marqués |
| Utilisateur | fallback | identité vérifiée par le garagiste |

Les adaptateurs professionnels utilisent un contrat HTTP JSON minimal : `POST {API_URL}/registration` ou `POST {API_URL}/vin`, authentification Bearer, puis `vehicle`, `vehicles` ou `candidates`. Le mapping exact doit être adapté à la documentation contractuelle du fournisseur avant activation. Aucun scraping n’est utilisé.

## Configuration

```env
VEHICLE_PROVIDER_PRIMARY=aaa_data
VEHICLE_PROVIDER_FALLBACKS=tecalliance,auto_ways
AAA_DATA_API_URL=
AAA_DATA_API_KEY=
TECALLIANCE_API_URL=
TECALLIANCE_API_KEY=
AUTO_WAYS_API_URL=
AUTO_WAYS_API_KEY=
VEHICLE_LOOKUP_TIMEOUT_MS=8000
VEHICLE_LOOKUP_CACHE_TTL_SECONDS=86400
VEHICLE_LOOKUP_ENABLE_MOCK=false
VEHICLE_CONFIDENCE_RELIABLE=0.90
VEHICLE_CONFIDENCE_RECOMMENDED=0.70
VEHICLE_CONFIDENCE_AMBIGUOUS=0.40
```

Les clés restent exclusivement dans le backend. En production, ne laissez ni `VEHICLE_PROVIDER_PRIMARY=mock` ni `VEHICLE_LOOKUP_ENABLE_MOCK=true`.

## Normalisation et fusion

`VehicleNormalizer` harmonise plaques, VIN, marques, carburants, transmissions et puissances kW/ch. Il conserve la réponse source dans le résultat de travail, mais celle-ci n’est pas automatiquement persistée. Un champ absent reste absent.

`VehicleMerger` conserve une provenance par champ. Les champs non contradictoires sont rapprochés. Une contradiction critique (`engine_code`, `engine_power_hp`, `transmission_code`, `transmission_type`) est laissée vide dans le résultat fusionné et force une confirmation.

Le score sert uniquement au routage : fiable à partir de 0,90, confirmation recommandée à partir de 0,70, ambigu à partir de 0,40, insuffisant en dessous. Ces seuils sont configurables.

Les champs critiques sont marque, modèle, génération, motorisation, code/famille moteur, puissance, carburant, type de boîte et année/période.

## Routes

- `POST /api/vehicles/resolve-registration`
- `POST /api/vehicles/resolve-vin`
- `POST /api/vehicles/resolve` (parcours persistant historique compatible)
- `POST /api/vehicle-resolution/{id}/confirm`
- `GET /api/vehicles/{id}`
- `POST /api/vehicle-resolution/{id}/invalidate-cache`
- `POST /api/vehicle-resolution/{id}/anonymize`

La confirmation accepte un candidat ou des `corrections`. Une correction manuelle du moteur est enregistrée séparément comme `engine_code_from_provider` et `engine_code_confirmed_by_user`; cette dernière est prioritaire pour le diagnostic.

## Cache et sécurité

Le cache persistant utilise une empreinte HMAC du VIN, est isolé par garage et expire. Le VIN et la plaque sont chiffrés, masqués dans les réponses et absents des journaux. Les événements ne conservent que le fournisseur, les champs retournés et les décisions. Les noms, adresses et coordonnées de propriétaires ne sont ni demandés ni stockés.

Les routes appliquent l’isolation garage, le rate limiting existant et permettent anonymisation/invalidation. L’authentification actuelle repose encore sur les identifiants de garage/utilisateur de démonstration : une authentification externe réelle reste nécessaire avant production.

## Diagnostic Gemini

`DiagnosticContextBuilder` transmet l’identité confirmée complète. Le prompt interdit à Gemini de modifier ou redéduire un véhicule confirmé. La création d’un diagnostic est refusée si le code moteur est inconnu ou si une configuration présente n’est pas confirmée.

Les codes défaut incluent leur valeur brute/normalisée, leur catégorie générique/constructeur/calculateur, le calculateur, le sous-code et le statut.

## Démonstration et tests

- `DEMO123` : Peugeot 308 II, DV6FC, 120 ch, BVM6, données fictives.
- `DEMOAMB` via la route normalisée : deux variantes fictives, confirmation requise.
- plaque inconnue en mode mock : demande du VIN.
- moteur remplacé : ouvrir la saisie manuelle et confirmer le nouveau code moteur.

```bash
docker build -f backend/Dockerfile.test -t automotive-diagnostic-ai-backend-test backend
docker run --rm -e PYTHONPATH=/app automotive-diagnostic-ai-backend-test
docker compose run --rm frontend npm run typecheck
docker compose build
```

Les tests n’appellent aucun fournisseur payant.

## Ajouter un fournisseur

1. Implémenter `lookup_by_registration` et `lookup_by_vin` dans `providers/`.
2. Déclarer URL/clé dans `Settings`, `.env.example` et Docker Compose.
3. Mapper uniquement les champs techniques autorisés.
4. Ajouter le fournisseur au registre et fixer sa priorité.
5. Tester succès, données incomplètes, timeout, quota, format invalide et fallback avec un faux client.

## Limites actuelles

Les contrats réels AAA Data, TecAlliance et Auto Ways ne peuvent pas être finalisés sans documentation et identifiants sous licence. Le cache normalisé multi-fournisseurs utilise encore les tables de résolution existantes pour la persistance VIN; une couche Redis peut être ajoutée à grande échelle. L’interface propose France, Belgique, Suisse et Luxembourg, mais la disponibilité réelle dépend du contrat fournisseur.

## Déploiement Vercel et Railway

- Vercel : connecter le dépôt avec `frontend` comme Root Directory.
- Railway backend : connecter le même dépôt avec `/backend` comme Root Directory et `/backend/railway.toml` comme fichier de configuration.
- Railway PostgreSQL : ajouter un service PostgreSQL et fournir sa `DATABASE_URL` au backend.
- Vercel : définir `NEXT_PUBLIC_API_URL=https://<backend-railway>/api`.
- Railway : définir `CORS_ORIGINS=https://<frontend-vercel>`, `LLM_PROVIDER=gemini` et `GEMINI_API_KEY`.

La clé Gemini reste exclusivement dans les variables Railway.
