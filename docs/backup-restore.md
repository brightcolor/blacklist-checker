# Backup / Restore

## PostgreSQL Backup
```bash
docker compose exec db pg_dump -U rblguard -d rblguard > backup.sql
```

## Restore
```bash
cat backup.sql | docker compose exec -T db psql -U rblguard -d rblguard
```

Hinweis: Für große Instanzen `pg_dump -Fc` + `pg_restore` verwenden.
