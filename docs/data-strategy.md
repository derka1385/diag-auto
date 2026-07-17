# Stratégie de données

La valeur et la sécurité du produit reposent d’abord sur une base de connaissances fiable, versionnée et révisée, pas sur le modèle de langage.

1. **Phase 1 — démonstration** : corpus fictif, scénarios contrôlés, règles manuelles, validation logicielle. Chaque item porte `demo_only: true`.
2. **Phase 2 — sources publiques ou autorisées** : codes OBD génériques, licences compatibles, manuels appartenant à l’entreprise et contenu produit par des garages partenaires. Aucun scraping protégé ni contournement d’accès.
3. **Phase 3 — licences professionnelles** : fournisseurs techniques, pièces, temps de main-d’œuvre, schémas, bulletins, procédures et VIN, avec provenance et droits documentés.
4. **Phase 4 — retours terrain** : DTC, symptômes, mesures, réparation, confirmation, variante, temps, pièces et retour mécanicien. Ces données restent candidates jusqu’à revue humaine.

Les imports sont validés, hachés, versionnés, dédupliqués puis appliqués dans une transaction. Une source peut devenir `outdated` ou `rejected` sans supprimer l’historique. La promotion vers les règles actives exige une revue humaine et une licence compatible.

## Catalogue générique initial

La liste fournie contenait 1 236 occurrences, soit 1 230 codes uniques après suppression de six doublons. Les 1 230 intitulés anglais ont été trouvés dans Wal33D DTC Database (MIT), au commit inscrit dans `data/fixtures/dtc_catalog.json`. La source se présente comme couvrant les codes génériques SAE J2012, mais cette correspondance n’a pas été auditée contre le Digital Annex SAE J2012DA actuel, qui est licencié. Les entrées sont donc `unreviewed`, sans traduction française inventée, sans sévérité déduite et sans procédure de diagnostic automatique.
