# JobTest Azure VM deployment

This is a Docker Compose deployment for the supported Next.js UI (`web/`),
FastAPI, PostgreSQL, local Ollama, and Nginx. It deliberately does not run the
deprecated Streamlit UI in `frontend/`.

## Public architecture

Only Nginx publishes TCP port 80. Nginx sends `/api/v1/*` to FastAPI and all
other traffic to Next.js. PostgreSQL (5432), Ollama (11434), FastAPI (8000), and
Next.js (3000) have no host port mappings and remain Docker-network internal.

The browser build uses `NEXT_PUBLIC_API_BASE=/api/v1`, so API requests use the
same public origin rather than a localhost URL. FastAPI documentation remains at
`/api/v1/docs`. HTTP is intentional until a domain and TLS certificate exist.

## First deployment on Ubuntu

```bash
sudo install -d -m 0755 -o "$USER" -g "$USER" /opt/jobtest
cd /opt/jobtest
cp .env.example .env
chmod 600 .env
# Set POSTGRES_PASSWORD and JWT_SECRET_KEY to distinct `openssl rand -hex 32`
# values; DATABASE_URL must use the same PostgreSQL password.
docker compose --env-file .env.example config --quiet
docker compose build
docker compose up -d db ollama api web nginx
docker compose exec ollama ollama pull qwen2.5:1.5b
```

The application creates its SQLAlchemy schema and performs its existing
additive-only `ensure_schema` check during API startup. It does not fabricate or
run destructive migrations. Model/download cache, Ollama models, and PostgreSQL
data use named volumes.

## Operations

```bash
cd /opt/jobtest
docker compose ps
docker compose logs -f --tail=200 nginx api web ollama db
docker compose restart
docker compose up -d --build
docker compose down                 # stops containers; keeps all named volumes
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' | gzip > jobtest-$(date +%F).sql.gz
```

For an update, create a database backup and retain the VM-local `.env`. This VM
was seeded from Git and overlaid with the current workstation source, so it may be
dirty relative to the upstream remote; do not use `git pull` over uncommitted
deployment files. First commit/review the desired source on the workstation, use
`git archive` (which excludes ignored `.env` files) to transfer that revision,
then validate with `docker compose --env-file .env.example config --quiet` and run
`docker compose up -d --build`. Do not use `down -v` unless you explicitly intend
to erase the database, Ollama model cache, and embedding cache.

## Cost control

`docker compose down` stops the stack but the Azure VM continues to accrue VM
charges while allocated. After a demo, use Azure Portal: **Virtual machines →
your VM → Stop**, then choose **Stop (deallocate)** and confirm the VM shows
**Deallocated**. Keep port 22 available for SSH; allow only TCP 80 for public
HTTP. Do not claim HTTPS until a domain and certificate are configured.

## Deployment files

- `Dockerfile.api` — multi-stage FastAPI/ML image.
- `web/Dockerfile` — multi-stage production Next.js image.
- `docker-compose.yml` — five-service topology, health checks, volumes, and
  internal-only service ports.
- `deploy/nginx/default.conf` — public routing and proxy configuration.
- `.env.example` — safe template; real values belong only in host `.env`.
- `.dockerignore` / `web/.dockerignore` — protect local secrets and avoid
  copying development artifacts while retaining quality-center assets.
