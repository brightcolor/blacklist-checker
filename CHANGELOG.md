# Changelog

## [0.1.0] - 2026-04-20
### Added
- Initial produktionsnahes Grundsystem `RBL Guard`
- FastAPI API + Web-UI (Light/Dark)
- PostgreSQL Datenmodell und Alembic Initialmigration
- Monitoring-Worker mit APScheduler
- DNSBL/RBL/URIBL/Whitelist Lookup-Engine mit TXT-Auflösung
- List-Health-Scoring und Degradierungslogik
- Alerting via E-Mail und Webhook inkl. Cooldown
- Rollenbasiertes Auth-System mit Argon2 + JWT
- Dockerfile und Docker Compose Setup
- Seed-Daten (Admin + Initiallisten)
- Kern-Tests und Dokumentation
