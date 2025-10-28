#!/bin/bash

# ============================================
# AURELIA - Server Deployment Script
# ============================================

set -e  # Exit on error

echo "============================================"
echo "🎯 AURELIA Deployment Script"
echo "============================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed!"
    echo "Install Docker with: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

# Check if Docker Compose is installed
if ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed!"
    echo "Install with: sudo apt install docker-compose-plugin -y"
    exit 1
fi

print_success "Docker and Docker Compose are installed"

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found!"
    echo ""
    echo "Creating .env from template..."
    cp .env.server .env
    print_info "Please edit .env file with your API keys:"
    echo "  - OPENAI_API_KEY"
    echo "  - PINECONE_API_KEY"
    echo "  - PINECONE_INDEX_NAME"
    echo "  - POSTGRES_PASSWORD"
    echo ""
    read -p "Press Enter after you've configured .env file..."
fi

# Validate required environment variables
source .env

if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-your-openai-api-key-here" ]; then
    print_error "OPENAI_API_KEY is not configured in .env"
    exit 1
fi

if [ -z "$PINECONE_API_KEY" ] || [ "$PINECONE_API_KEY" = "your-pinecone-api-key-here" ]; then
    print_error "PINECONE_API_KEY is not configured in .env"
    exit 1
fi

print_success "Environment variables are configured"

# Stop existing containers if running
if docker compose ps | grep -q "Up"; then
    print_info "Stopping existing containers..."
    docker compose down
fi

# Build and start services
print_info "Building Docker images (this may take a few minutes)..."
docker compose build

print_info "Starting services..."
docker compose up -d

# Wait for services to be healthy
print_info "Waiting for services to start..."
sleep 10

# Check service health
print_info "Checking service health..."

# Check PostgreSQL
if docker compose ps postgres | grep -q "healthy"; then
    print_success "PostgreSQL is healthy"
else
    print_warning "PostgreSQL is starting..."
fi

# Wait for backend to be ready
print_info "Waiting for backend to be ready (this may take 30-60 seconds)..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -f http://localhost:8080/health > /dev/null 2>&1; then
        print_success "Backend is healthy"
        break
    fi
    attempt=$((attempt + 1))
    echo -n "."
    sleep 2
done

echo ""

if [ $attempt -eq $max_attempts ]; then
    print_error "Backend failed to start. Check logs with: docker compose logs backend"
    exit 1
fi

# Check frontend
if docker compose ps frontend | grep -q "Up"; then
    print_success "Frontend is running"
else
    print_warning "Frontend is starting..."
fi

echo ""
echo "============================================"
echo "🎉 DEPLOYMENT COMPLETE!"
echo "============================================"
echo ""
echo "Access your application:"
echo ""
echo "📱 Frontend:      http://tail8ccfe9.ts.net:8501"
echo "🔧 Backend API:   http://tail8ccfe9.ts.net:8080"
echo "📚 API Docs:      http://tail8ccfe9.ts.net:8080/docs"
echo "💚 Health Check:  http://tail8ccfe9.ts.net:8080/health"
echo ""
echo "Local access:"
echo "📱 Frontend:      http://localhost:8501"
echo "🔧 Backend API:   http://localhost:8080"
echo ""
echo "Useful commands:"
echo "  - View logs:           docker compose logs -f"
echo "  - Check status:        docker compose ps"
echo "  - Stop services:       docker compose stop"
echo "  - Restart services:    docker compose restart"
echo "  - View stats:          curl http://localhost:8080/stats"
echo ""
