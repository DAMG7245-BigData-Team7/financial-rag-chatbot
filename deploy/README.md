# Deploying to a VPS

Backend and Postgres run in Docker Compose. The frontend is a static export
served by Caddy, which also terminates HTTPS for every project on the box.

```
https://<host>/       → Caddy → /srv/aurelia (static files)
https://<host>/api/*  → Caddy → 127.0.0.1:8080 (FastAPI container, /api stripped)
```

Currently `<host>` is `sachin.40.160.143.143.sslip.io` (free [sslip.io](https://sslip.io) name that resolves to the VPS IP).

## One-time server setup (Ubuntu)

```bash
# Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER            # log out and back in

# Caddy
sudo apt install -y caddy
sudo mkdir -p /srv/aurelia && sudo chown $USER /srv/aurelia

# 2 GB swap
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Firewall: SSH + HTTP(S) only
sudo ufw allow OpenSSH && sudo ufw allow 80 && sudo ufw allow 443 && sudo ufw enable
```

To use your own domain, point its A record at the VPS IP and swap it into
`deploy/Caddyfile` and the frontend build command below.

## Backend

```bash
git clone https://github.com/DAMG7245-BigData-Team7/financial-rag-chatbot.git
cd financial-rag-chatbot/deploy
cp .env.example .env                     # fill in keys and a strong DB_PASSWORD
docker compose up -d --build
curl localhost:8080/health
```

To carry over cached concept notes from an existing database:

```bash
pg_dump -d <old_db> -t concept_notes --data-only > notes.sql      # on the old machine
docker compose exec -T db psql -U aurelia -d aurelia < notes.sql  # on the VPS
```

## Frontend

Build on your machine (the API URL is baked in at build time) and copy it up:

```bash
cd web
NEXT_PUBLIC_API_URL=https://sachin.40.160.143.143.sslip.io/api npm run build
rsync -av --delete out/ user@vps:/srv/aurelia/
```

## Caddy

Copy `deploy/Caddyfile` to `/etc/caddy/Caddyfile` (or merge its blocks in if
other projects already live there), then `sudo systemctl reload caddy`.
Certificates are automatic.

## Updating

```bash
git pull && cd deploy && docker compose up -d --build && docker image prune -f
```
