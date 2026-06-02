# Setup Guide

## Schnellstart via Docker
1. `.env.example` nach `.env` kopieren.
2. `SECRET_KEY` und DB-Credentials anpassen.
3. `docker compose up --build -d`.
4. `http://localhost:8000/` öffnen.

## Manuelles Setup
1. Python Dependencies installieren.
2. Postgres DB bereitstellen.
3. `alembic upgrade head`.
4. `python scripts/seed_db.py`.
5. API und Worker starten.

## Produktion
- Reverse Proxy (Nginx/Traefik) vorschalten.
- TLS aktivieren.
- Container-Restart-Policy `unless-stopped` beibehalten.
- Regelmäßige Backups per `pg_dump`.
- Monitoring auf `/api/v1/system/*`.
