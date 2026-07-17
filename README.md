# DiagPilot — MVP de diagnostic automobile assisté

DiagPilot aide un mécanicien à transformer un DTC en parcours de contrôle guidé, sourcé et traçable. Ce dépôt est une fondation fonctionnelle, **entièrement fictive et interdite d’usage sur un véhicule réel**. Un DTC n’est jamais présenté comme la preuve d’une pièce défectueuse.

## Ce qui fonctionne

- véhicule, garage et technicien de démonstration ;
- quatre DTC fictifs, connaissances atomiques et règles sourcées ;
- catalogue de 1 230 définitions DTC génériques en anglais, provenant d’une source ouverte MIT et conservant sa provenance ;
- import OBD canonique JSON/CSV sans connexion physique ;
- scénario P0301 interactif avec branches « le défaut suit la bobine » / « reste sur le cylindre 1 » ;
- parcours générique sûr pour tout code DTC syntaxiquement valide, y compris les codes constructeur non définis comme P1351 ;
- hypothèses classées, preuves/contradictions, étape courante, événements immuables et rapport ;
- mock LLM strictement validé et désactivable sans casser le moteur ;
- dashboard, création, console tablette et rapport Next.js ;
- isolation de base par garage et tests d’intégration.
- résolution VIN avec mock hors ligne, adaptateur NHTSA vPIC optionnel, cache HMAC, confirmation technicien et rapprochement ECU/DTC.
- diagnostic multimodal avec codes multiples, mesures, photos privées, sortie JSON stricte et provider Gemini interchangeable ;
- mode `mock` déterministe utilisable sans clé pour tester intégralement P1351 et le parcours de réévaluation.

## Stack et structure

FastAPI, Pydantic, SQLAlchemy, Alembic, pytest ; Next.js 16, React 19, TypeScript strict et Tailwind ; PostgreSQL avec Docker Compose, SQLite en local. Le backend est un monolithe modulaire (`vehicles`, `obd`, `knowledge`, `diagnostics`, `vehicle_resolution`, `ai`, `garages`, `reports`, `imports`). Les décisions sont détaillées dans [docs/architecture.md](docs/architecture.md).

## Démarrage recommandé avec Docker

```bash
cp .env.example .env
docker compose up --build
```

Les migrations et fixtures sont appliquées au démarrage du backend. Arrêt : `docker compose down`. Réinitialisation volontaire : `docker compose down -v`.

## Démarrage local

Prérequis : Python 3.11+ et Node 22+.

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

Dans un second terminal :

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000/api npm run dev
```

## Tests et contrôles

```bash
cd backend
DATABASE_URL=sqlite:///./test.db pytest

# ou, sans Python local :
docker build -f backend/Dockerfile.test -t diagpilot-backend-test backend
docker run --rm diagpilot-backend-test

cd ../frontend
npm run typecheck
npm run build
```

## URLs locales

- application : http://localhost:3000
- santé API : http://localhost:8000/api/health
- Swagger : http://localhost:8000/docs
- OpenAPI : http://localhost:8000/openapi.json

## Démonstration IA P1351

Le mode par défaut est `LLM_PROVIDER=mock` : aucune clé ni donnée externe n’est nécessaire.

1. Ouvrir `http://localhost:3000/diagnostics/new`.
2. Garder le véhicule de démonstration, ou saisir la plaque fictive `DEMO123`.
3. Conserver `P1351` (ajouter éventuellement `P0301` pour tester les corrélations).
4. Ajouter une mesure ou une photo, vérifier la synthèse, puis lancer l’analyse.
5. Dans la console IA, renseigner le résultat du contrôle et demander la réévaluation.

Pour activer Gemini, renseigner `GEMINI_API_KEY` dans `.env` et passer `LLM_PROVIDER=gemini`, puis reconstruire le backend. La clé reste exclusivement côté serveur. Voir [docs/vehicle-diagnostic-ai.md](docs/vehicle-diagnostic-ai.md).

## Identification obligatoire par plaque

L’interface principale n’affiche plus l’historique : `/` redirige vers « Diagnostiquer » et une plaque confirmée est obligatoire. `DEMO123` reste disponible pour les tests hors ligne. Pour une plaque réelle, utilisez un fournisseur professionnel autorisé qui retourne au minimum un VIN :

```env
REGISTRATION_PROVIDER=http
REGISTRATION_API_URL=https://endpoint-fourni-par-votre-prestataire
REGISTRATION_API_KEY=votre_cle_serveur
```

Le connecteur envoie côté serveur `{"registration":"AB123CD","countryCode":"FR"}` avec un jeton Bearer. Il reconnaît les champs usuels `vin`, `make`/`brand`, `model`, `engineCode`, `transmissionType`, etc. Si le contrat du prestataire diffère, adaptez uniquement `vehicle_data/providers.py`; aucune plaque ni clé ne transite dans le frontend.

## Démonstration historique P0301

1. Ouvrir « Nouveau diagnostic » et garder le véhicule Demo Motors DM-1.
2. Saisir P0301, vérifier la plainte et lancer l’analyse.
3. Dans la console, confirmer l’un des résultats de permutation.
4. Observer le nouveau classement et l’étape suivante.
5. Clôturer puis consulter le rapport sourcé.

Pour vérifier spécifiquement le parcours constructeur prudent :

```bash
python3 scripts/smoke_p1351.py
```

## Démonstration VIN

Ouvrir `/vehicle-resolution` et conserver `ZZZTESTA0DEMA0001`. Le mock retourne une DM-1 fictive, puis demande une confirmation avant de créer le véhicule. Les scénarios B à E couvrent moteur manquant, candidats multiples, conflit ECU et fournisseur indisponible. Voir [docs/vin-resolution.md](docs/vin-resolution.md).

Import alternatif : envoyer `data/fixtures/demo_obd_report.json` à `POST /api/imports/obd-report`, ou utiliser Swagger. Aucun effacement de code ni commande ECU n’a lieu.

Le catalogue sous `data/fixtures/dtc_catalog.json` est chargé de façon idempotente par `python -m app.seed`. Ses intitulés anglais sont conservés tels quels. Ils proviennent de Wal33D DTC Database au commit documenté dans le fichier ; ils n’ont pas été vérifiés indépendamment contre l’annexe SAE J2012DA sous licence.

## Limites actuelles

Authentification réelle, fournisseur de plaques officiel, PDF, rate limiting distribué, OCR dédié, ingestion documentaire/RAG, documentation constructeur licenciée et connexion OBD sont hors MVP. `X-Garage-ID` est un mécanisme de développement, pas une authentification. Les photos sont privées côté backend mais l’accès doit être raccordé à une authentification réelle avant production. Le corpus et toutes les valeurs de démonstration sont fictifs. Voir [docs/security.md](docs/security.md) et [docs/roadmap.md](docs/roadmap.md).
