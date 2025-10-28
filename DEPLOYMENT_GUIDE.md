# AURELIA - Server Deployment Guide

Deploy AURELIA (Frontend + Backend) on your private server using Docker Compose.

## 📋 Server Requirements

- **CPU:** 8 vCPU ✅
- **RAM:** 16GB ✅
- **Storage:** 50GB ✅
- **OS:** Linux (Ubuntu 20.04+ recommended)
- **Network:** Accessible via Tailscale

## 🚀 Quick Start (5 Minutes)

### 1. Prerequisites

Install Docker and Docker Compose on your server:

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Add your user to docker group (optional, to run without sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

### 2. Clone Repository

```bash
# Clone the repository to your server
git clone https://github.com/DAMG7245-BigData-Team7/financial-rag-chatbot.git
cd financial-rag-chatbot

# Or if already cloned, pull latest changes
git pull origin main
```

### 3. Configure Environment

```bash
# Copy the server environment template
cp .env.server .env

# Edit the .env file with your API keys
nano .env
```

**Required Configuration:**

```bash
# OpenAI API Key (REQUIRED)
OPENAI_API_KEY=sk-your-actual-openai-key

# Pinecone API Key (REQUIRED)
PINECONE_API_KEY=your-actual-pinecone-key

# Pinecone Index Name (must match your index)
PINECONE_INDEX_NAME=fintbx-hybrid-3072

# PostgreSQL Password (change in production!)
POSTGRES_PASSWORD=your-secure-password-here
```

### 4. Start Services

```bash
# Build and start all services
docker compose up -d

# View logs
docker compose logs -f

# Check service status
docker compose ps
```

### 5. Access Your Application

Once services are running:

- **Frontend (Streamlit):** `http://your-server-ip:8501`
- **Backend API (FastAPI):** `http://your-server-ip:8080`
- **API Documentation:** `http://your-server-ip:8080/docs`
- **Health Check:** `http://your-server-ip:8080/health`

**Via Tailscale:**
- Use your Tailscale hostname: `http://your-tailscale-hostname:8501`

## 📊 Service Architecture

```
┌─────────────────────────────────────────────┐
│         Your Server (Tailscale)             │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────┐         ┌──────────────┐  │
│  │  Frontend   │  ────>  │   Backend    │  │
│  │ (Streamlit) │         │  (FastAPI)   │  │
│  │  Port 8501  │         │  Port 8080   │  │
│  └─────────────┘         └──────┬───────┘  │
│                                  │          │
│                          ┌───────▼───────┐  │
│                          │  PostgreSQL   │  │
│                          │   Port 5432   │  │
│                          └───────────────┘  │
│                                             │
└─────────────────────────────────────────────┘
            │                    │
            ▼                    ▼
      OpenAI API          Pinecone API
```

## 🔧 Management Commands

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f postgres
```

### Restart Services

```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart backend
docker compose restart frontend
```

### Stop Services

```bash
# Stop all services (keeps data)
docker compose stop

# Stop and remove containers (keeps data in volumes)
docker compose down

# Stop and remove everything including volumes (⚠️ deletes database)
docker compose down -v
```

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker compose down
docker compose up -d --build
```

### Check Resource Usage

```bash
# View container resource usage
docker stats

# View disk usage
docker system df

# View logs size
du -sh $(docker inspect --format='{{.LogPath}}' aurelia-backend)
```

## 🔍 Troubleshooting

### Check Service Health

```bash
# Check if all containers are running
docker compose ps

# Check health status
curl http://localhost:8080/health

# View backend logs
docker compose logs backend

# View frontend logs
docker compose logs frontend
```

### Common Issues

#### 1. Backend fails to start

**Symptom:** Backend container keeps restarting

**Solution:**
```bash
# Check logs
docker compose logs backend

# Common causes:
# - Missing OPENAI_API_KEY or PINECONE_API_KEY
# - Invalid API keys
# - Pinecone index doesn't exist
# - PostgreSQL not ready (wait 30 seconds and check again)
```

#### 2. Frontend can't connect to backend

**Symptom:** Frontend shows "API Disconnected"

**Solution:**
```bash
# Verify backend is running
curl http://localhost:8080/health

# Check if backend container is healthy
docker compose ps

# Restart frontend
docker compose restart frontend
```

#### 3. Database connection errors

**Symptom:** Backend logs show PostgreSQL connection errors

**Solution:**
```bash
# Check PostgreSQL logs
docker compose logs postgres

# Verify PostgreSQL is healthy
docker compose ps postgres

# Reset database (⚠️ this will delete all cached data)
docker compose down
docker volume rm aurelia_postgres_data
docker compose up -d
```

#### 4. Port already in use

**Symptom:** "bind: address already in use"

**Solution:**
```bash
# Check what's using the port
sudo lsof -i :8080
sudo lsof -i :8501

# Stop the conflicting service or change ports in docker-compose.yml
```

### Port Configuration

To change ports, edit `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8080:8080"  # Change left side: "YOUR_PORT:8080"

  frontend:
    ports:
      - "8501:8080"  # Change left side: "YOUR_PORT:8080"
```

## 💾 Data Persistence

All data is stored in Docker volumes:

- **postgres_data:** PostgreSQL database (cached concept notes)

### Backup Database

```bash
# Export database
docker compose exec postgres pg_dump -U aurelia_user aurelia > backup.sql

# Restore database
docker compose exec -T postgres psql -U aurelia_user aurelia < backup.sql
```

### View Cached Concepts

```bash
# Via API
curl http://localhost:8080/cache

# Via Database
docker compose exec postgres psql -U aurelia_user -d aurelia -c "SELECT concept, source, created_at FROM concept_notes;"
```

## 🔒 Security Recommendations

### For Production Deployment:

1. **Change Default Password**
   ```bash
   # In .env file
   POSTGRES_PASSWORD=use-a-strong-password-here
   ```

2. **Restrict CORS Origins**
   Edit `app/main.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-domain.com"],  # Restrict origins
       ...
   )
   ```

3. **Use HTTPS**
   - Set up a reverse proxy (nginx/Caddy) with SSL certificates
   - Use Let's Encrypt for free SSL certificates

4. **Firewall Rules**
   ```bash
   # Only allow Tailscale network
   sudo ufw allow from 100.64.0.0/10 to any port 8501
   sudo ufw allow from 100.64.0.0/10 to any port 8080
   sudo ufw enable
   ```

5. **Environment Variables**
   - Never commit `.env` file to git
   - Use secrets management for API keys in production

## 📊 Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8080/health

# Frontend health (returns HTML)
curl http://localhost:8501/_stcore/health

# Database stats
curl http://localhost:8080/stats
```

### Resource Monitoring

```bash
# Real-time container stats
docker stats aurelia-backend aurelia-frontend aurelia-postgres

# Disk usage
docker system df
```

## 🎯 Performance Tuning

For your 8vCPU/16GB RAM server:

### PostgreSQL Tuning

Edit `docker-compose.yml` to add PostgreSQL configuration:

```yaml
postgres:
  command:
    - "postgres"
    - "-c"
    - "max_connections=200"
    - "-c"
    - "shared_buffers=4GB"
    - "-c"
    - "effective_cache_size=12GB"
    - "-c"
    - "work_mem=20MB"
```

### Backend Scaling

To run multiple backend workers:

```yaml
backend:
  command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
```

## 📞 Support

If you encounter issues:

1. Check logs: `docker compose logs -f`
2. Verify configuration: `cat .env`
3. Test API directly: `curl http://localhost:8080/health`
4. Check GitHub issues: https://github.com/DAMG7245-BigData-Team7/financial-rag-chatbot/issues

## 🎉 Success!

Once everything is running:

1. Open frontend: `http://your-server-ip:8501`
2. Try example concepts: "Duration", "Sharpe Ratio", "Black-Scholes Model"
3. Check the API docs: `http://your-server-ip:8080/docs`

Your AURELIA instance is now running on your private server! 🚀
