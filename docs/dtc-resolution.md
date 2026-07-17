# Résolution compatible des DTC

La compatibilité part d’une `VehicleConfiguration` confirmée. Les connaissances explicitement incompatibles sont rejetées; les correspondances exposent source et champs utilisés.

L’ordre cible est ECU exact, famille ECU, code moteur, variante, modèle/année/marché, constructeur, puis définition OBD générique. Le moteur classe les scopes ECU/configuration/véhicule. P0301 retombe sur le catalogue générique ; P1351 reste accepté mais explicitement non résolu tant qu’aucune documentation constructeur compatible n’est disponible.

```bash
curl -X POST http://localhost:8000/api/vehicles/VEHICLE_ID/diagnostic-compatibility -H 'Content-Type: application/json' -d '{"dtcs":["P0301"],"system":"engine_ignition"}'
```
