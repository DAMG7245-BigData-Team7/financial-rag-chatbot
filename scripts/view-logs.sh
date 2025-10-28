#!/bin/bash

# ============================================
# AURELIA - Log Viewer Script
# ============================================

echo "📋 AURELIA Log Viewer"
echo "============================================"
echo ""
echo "Select which logs to view:"
echo ""
echo "  1) All services"
echo "  2) Backend only"
echo "  3) Frontend only"
echo "  4) PostgreSQL only"
echo "  5) Last 100 lines (all services)"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        echo "Viewing all service logs (Ctrl+C to exit)..."
        docker compose logs -f
        ;;
    2)
        echo "Viewing backend logs (Ctrl+C to exit)..."
        docker compose logs -f backend
        ;;
    3)
        echo "Viewing frontend logs (Ctrl+C to exit)..."
        docker compose logs -f frontend
        ;;
    4)
        echo "Viewing PostgreSQL logs (Ctrl+C to exit)..."
        docker compose logs -f postgres
        ;;
    5)
        echo "Last 100 lines:"
        docker compose logs --tail=100
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
