# Institutional Security & Maintenance Guidelines

## 1. API Security
- Never store Hyperliquid raw keys in Git or PostgreSQL. Rely on `.env` injected at runtime only.
- Frontend Gateway communicates securely with external services.
- Always regenerate JWT Secret Tokens. Run `openssl rand -hex 32` and place it in `.env`.

## 2. Risk Protocol
- The Risk Officer role should verify `MAX_PORTFOLIO_EXPOSURE_PCT` is never manually modified outside database migrations.
- Emergency Liquidate button on UI triggers a global bypass flag to close open positions across all algorithms instantly without requiring API overrides.

## 3. Database Maintenance (PostgreSQL)
Vacuum analyze periodically to maintain low-latency fetches on high volume trade ticks.
```bash
docker exec -it qb-postgres psql -U quantbot_user quantbot -c "VACUUM ANALYZE;"
```

## 4. Logs
Nginx and Docker compose have built-in log rotations to prevent disk space exhausting:
```yml
# Standard implementation handled implicitly by Docker log limits
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "5"
```
