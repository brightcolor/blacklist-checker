# RBL Guard

Self-hostbarer DNSBL/RBL/URIBL-Monitoring-Service mit Webinterface, REST-API, Scheduler und Alerting.

## Projektbeschreibung
RBL Guard überwacht IPv4/IPv6, Domains und Hostnamen gegen konfigurierbare DNS-basierte Block- und Whitelists. Der Dienst führt periodische Checks aus, erkennt Statusänderungen und versendet Alerts nur bei relevanten Änderungen.

## Funktionsumfang
- API-first FastAPI Backend mit OpenAPI/Swagger
- Responsive UI mit Light/Dark Theme
- PostgreSQL Persistenz + Historie
- APScheduler Worker für Monitoring-Jobs
- DNSBL/RBL/URIBL + Whitelist Checks
- FCrDNS/iprev-fähige DNS-Engine (PTR/Forward Logik vorbereitet)
- Alerting via E-Mail/Webhook (+ Slack/Discord/Matrix/Telegram über Webhook-Modus)
- Cooldown/Dedupe gegen Alert-Spam
- Rollenbasiertes Login (Admin/User), Argon2 Passwort-Hashing
- Rate-Limiting für öffentliche Sofortprüfungen
- List-Health-Scoring für tote/instabile Listen

## Screenshots
Platzhalter:
- `docs/screenshots/dashboard.png`
- `docs/screenshots/monitor-detail.png`
- `docs/screenshots/list-health.png`

## Architekturüberblick
Siehe [docs/architecture.md](/C:/Users/brigh/Documents/blacklist-checker/docs/architecture.md).

## Verzeichnisstruktur
```text
app/
  api/
  core/
  db/
  models/
  schemas/
  services/
  static/
  templates/
worker/
alembic/
scripts/
tests/
docs/
```

## Lokale Entwicklung
### Voraussetzungen
- Python 3.11+
- PostgreSQL 16+

### Schritte
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

DB starten und migrieren:
```bash
alembic upgrade head
python scripts/seed_db.py
```

API starten:
```bash
uvicorn app.main:app --reload --port 8000
```

Worker starten:
```bash
python -m worker.main
```

## Docker Deployment
```bash
docker compose up --build -d
```

Danach:
- UI: `http://localhost:8000/`
- API Docs: `http://localhost:8000/docs`

## Container Images
GitHub Actions baut bei jedem Push auf `master`/`main` und bei Tags `v*` automatisch ein Image:

```text
ghcr.io/brightcolor/blacklist-checker:latest
ghcr.io/brightcolor/blacklist-checker:master
ghcr.io/brightcolor/blacklist-checker:sha-<commit>
```

Das gleiche Image wird fuer API und Worker genutzt; der jeweilige Container unterscheidet sich nur durch das `command` in `docker-compose.yml`.

## Standard-Login (nur Seed)
- E-Mail: `admin@example.com`
- Passwort: `ChangeMeNow123!`

Bitte nach dem ersten Login sofort ändern.

## Konfiguration
Siehe [.env.example](/C:/Users/brigh/Documents/blacklist-checker/.env.example).

Wichtige Variablen:
- `DATABASE_URL`
- `SECRET_KEY`
- `DNS_DEFAULT_TIMEOUT`, `DNS_MAX_CONCURRENCY`
- `LIST_HEALTH_DEGRADE_THRESHOLD`
- `SMTP_*`
- `PUBLIC_LOOKUP_RATE_PER_MINUTE`

## SMTP/Webhook Setup
- SMTP aktivieren: `SMTP_ENABLED=true` + Host/Credentials setzen.
- Webhook-Alerts über `/api/v1/channels` mit `channel_type=webhook` konfigurieren.

## Scheduler-Erklärung
- Worker pollt alle 30 Sekunden fällige Monitore.
- Fälligkeit über `next_run_at` + `interval_minutes`.
- Alerts werden nur bei Statusänderung erzeugt.
- Cooldown je Alert-Kanal verhindert Spam.

## Backup/Restore
Siehe [docs/backup-restore.md](/C:/Users/brigh/Documents/blacklist-checker/docs/backup-restore.md).

## Update-Anleitung
1. Neues Release deployen.
2. `alembic upgrade head` ausführen.
3. Container/API/Worker neu starten.
4. Health prüfen: `/api/v1/system/ready`.

## Sicherheitshinweise
- `SECRET_KEY` immer produktiv setzen.
- API hinter TLS-Termination betreiben.
- Admin-Seed-User und Passwort direkt ändern.
- Optional 2FA-Felder sind im Datenmodell vorbereitet (`otp_enabled`, `otp_secret`).

## Qualität / Tests
```bash
pytest
ruff check .
```

## Roadmap
- Vollständige FCrDNS/iprev Detailansicht im UI
- Eskalationsprofile pro Monitor
- Daily Summary Scheduling je Tenant
- Optional Redis/Celery für größere Last
- Multi-Org/Tenant-Scopes über eigene Tabellen
- Exporte (CSV/JSON) für Audit und Compliance

## Lizenz
MIT, siehe [LICENSE](/C:/Users/brigh/Documents/blacklist-checker/LICENSE).
