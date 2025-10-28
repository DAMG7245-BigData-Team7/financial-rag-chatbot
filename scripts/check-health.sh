#!/bin/bash

# ============================================
# AURELIA - Health Check Script
# ============================================

echo "🏥 AURELIA Health Check"
echo "============================================"
echo ""

# Check Docker containers
echo "📦 Container Status:"
docker compose ps
echo ""

# Check Backend API
echo "🔧 Backend API Health:"
if curl -f http://localhost:8080/health 2>/dev/null; then
    echo ""
    echo "✅ Backend is healthy"
else
    echo "❌ Backend is not responding"
fi
echo ""

# Check Frontend
echo "📱 Frontend Status:"
if curl -f http://localhost:8501/_stcore/health 2>/dev/null > /dev/null; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend is not responding"
fi
echo ""

# Get API stats
echo "📊 API Statistics:"
curl -s http://localhost:8080/stats | python3 -m json.tool 2>/dev/null || echo "Unable to fetch stats"
echo ""

# Resource usage
echo "💻 Resource Usage:"
docker stats --no-stream aurelia-backend aurelia-frontend aurelia-postgres
echo ""

echo "============================================"
echo "Access URLs:"
echo "  Frontend: http://tail8ccfe9.ts.net:8501"
echo "  Backend:  http://tail8ccfe9.ts.net:8080"
echo "  API Docs: http://tail8ccfe9.ts.net:8080/docs"
echo "============================================"
