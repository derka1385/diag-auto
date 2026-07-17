# Sécurité et sûreté

- **Hallucination IA** : contexte limité, schéma strict, sources obligatoires, moteur de règles souverain et journal des échecs.
- **Mauvaises données** : provenance, checksum, revue humaine, statut de source et indicateur de démonstration.
- **Procédures dangereuses** : avertissements visibles, confirmation humaine à chaque test, aucune écriture ECU ni action distante.
- **Fichiers** : limite 1 Mio, MIME/extension contrôlés, contenu jamais exécuté, validation avant transaction.
- **Multi-tenant** : toutes les sessions sont filtrées par garage. L’en-tête de développement devra être remplacé par un jeton signé et des politiques d’accès testées avant production.
- **Données client** : minimisation, absence de secrets dans les logs, chiffrement et politique de rétention à définir.
- **Prise en main distante** : hors périmètre ; aucune commande véhicule, suppression de DTC ou codage ECU.

Le rate limiting possède un point d’extension middleware mais nécessite un stockage partagé avant déploiement. CORS est limité par configuration. Une revue OWASP, sauvegardes, rotation des secrets, audit des dépendances et tests d’intrusion restent requis avant usage réel.

