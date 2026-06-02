# Architektur

## Überblick
RBL Guard ist ein API-first DNSBL/RBL Monitoring-Dienst mit drei Laufzeitkomponenten:

1. `api` (FastAPI): REST-API, Auth, Admin-Funktionen, Web-UI.
2. `worker` (APScheduler): periodische Monitor-Ausführung, Diff-Erkennung, Alerting.
3. `db` (PostgreSQL): Zustands-, Historie- und Konfigurationsspeicher.

## Schichten
- `app/services/dns_engine.py`: DNS-Lookups (A/TXT/PTR), Retry-/Timeout-respektierend.
- `app/services/check_service.py`: Orchestrierung, Parallelisierung mit Semaphore, Health-Scoring.
- `app/services/alerts.py`: E-Mail/Webhook + Cooldown-Entprellung.
- `app/api/routes/*`: klar getrennte API-Endpunkte.

## Datenmodell
- `users`, `alert_channels`, `alert_events`
- `rbl_lists`, `rbl_list_groups`
- `monitors`, `check_runs`, `check_run_results`
- `global_settings`

## Listen-Health-Scoring
Jeder Listenlauf aktualisiert `health_score`:
- Erfolg: +2 (max. 100)
- Fehler/Timeout: -8 (min. 0)
- `is_degraded=true`, wenn `health_score < LIST_HEALTH_DEGRADE_THRESHOLD`.

Degradierte Listen werden als unklar/fehlerhaft behandelt und nicht als sauber gewertet.

## Mandantenfähigkeit
Alle benutzerspezifischen Objekte (`monitors`, `alert_channels`, `alert_events`) sind per `user_id` getrennt. Admins verwalten globale Listen und User.
