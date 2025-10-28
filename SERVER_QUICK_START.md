# AURELIA - Quick Start Guide for Your Server

## Your Server Details
- **Tailscale Domain:** `tail8ccfe9.ts.net`
- **Resources:** 8 vCPU, 16GB RAM, 50GB Storage
- **Network:** Tailscale

## 🚀 Deploy in 3 Steps

### Step 1: Install Docker (one-time setup)
```bash
# SSH into your server
ssh user@tail8ccfe9.ts.net

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com | sh
sudo apt install docker-compose-plugin -y
sudo usermod -aG docker $USER
newgrp docker
```

### Step 2: Clone and Configure
```bash
# Clone repository
git clone https://github.com/DAMG7245-BigData-Team7/financial-rag-chatbot.git
cd financial-rag-chatbot

# Configure environment
cp .env.server .env
nano .env  # Add your API keys
```

**Required in .env:**
```bash
OPENAI_API_KEY=sk-your-actual-key
PINECONE_API_KEY=your-actual-key
PINECONE_INDEX_NAME=fintbx-hybrid-3072
POSTGRES_PASSWORD=your-secure-password
```

### Step 3: Deploy
```bash
# Run deployment script
./deploy.sh
```

That's it! 🎉

## Access Your Application

**From anywhere on your Tailscale network:**
- Frontend: http://tail8ccfe9.ts.net:8501
- Backend API: http://tail8ccfe9.ts.net:8080
- API Docs: http://tail8ccfe9.ts.net:8080/docs

**On the server locally:**
- Frontend: http://localhost:8501
- Backend: http://localhost:8080

## 📋 Daily Commands

```bash
# Check status
docker compose ps

# View logs
./scripts/view-logs.sh

# Check health
./scripts/check-health.sh

# Backup database
./scripts/backup-db.sh

# Restart services
docker compose restart

# Stop services
docker compose stop

# Start services
docker compose up -d

# Update to latest code
git pull origin main
docker compose down
docker compose up -d --build
```

## 🔍 Quick Health Check

```bash
# Check if everything is running
curl http://localhost:8080/health

# View statistics
curl http://localhost:8080/stats

# List cached concepts
curl http://localhost:8080/cache
```

## 📊 Resource Monitoring

```bash
# Real-time stats
docker stats

# Disk usage
docker system df

# View container logs
docker compose logs -f backend
```

## 🛠️ Troubleshooting

### Backend not starting?
```bash
# Check logs
docker compose logs backend

# Verify environment variables
cat .env

# Restart
docker compose restart backend
```

### Frontend can't connect?
```bash
# Check backend is running
curl http://localhost:8080/health

# Restart frontend
docker compose restart frontend
```

### Database issues?
```bash
# Check PostgreSQL logs
docker compose logs postgres

# Restart database
docker compose restart postgres
```

## 🔥 Emergency Commands

```bash
# Full restart (keeps data)
docker compose down
docker compose up -d

# Full reset (⚠️ DELETES ALL DATA)
docker compose down -v
docker compose up -d
```

## 📞 Need Help?

1. Check logs: `docker compose logs -f`
2. Read full guide: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
3. Check service health: `./scripts/check-health.sh`

## 🎯 Test Your Deployment

1. Open: http://tail8ccfe9.ts.net:8501
2. Try a concept: "Duration" or "Sharpe Ratio"
3. Check the result appears correctly
4. View API docs: http://tail8ccfe9.ts.net:8080/docs

## 🔒 Security Checklist

- [ ] Changed `POSTGRES_PASSWORD` in .env
- [ ] Never commit .env to git
- [ ] Keep API keys secure
- [ ] Regular backups: `./scripts/backup-db.sh`
- [ ] Monitor resource usage: `docker stats`

---

**That's all you need!** Your AURELIA instance should now be running on your private server accessible via Tailscale. 🚀
