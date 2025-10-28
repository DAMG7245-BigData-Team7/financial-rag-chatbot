#!/bin/bash

# ============================================
# AURELIA - Database Backup Script
# ============================================

# Create backups directory if it doesn't exist
mkdir -p ./backups

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="./backups/aurelia_backup_${TIMESTAMP}.sql"

echo "🗄️  AURELIA Database Backup"
echo "============================================"
echo ""
echo "Creating backup: ${BACKUP_FILE}"

# Export database
docker compose exec -T postgres pg_dump -U aurelia_user aurelia > "${BACKUP_FILE}"

if [ $? -eq 0 ]; then
    echo "✅ Backup created successfully!"
    echo ""
    echo "Backup file: ${BACKUP_FILE}"
    echo "Size: $(du -h ${BACKUP_FILE} | cut -f1)"
    echo ""

    # Show record count
    RECORD_COUNT=$(docker compose exec -T postgres psql -U aurelia_user -d aurelia -t -c "SELECT COUNT(*) FROM concept_notes;" | tr -d ' ')
    echo "📊 Total cached concepts: ${RECORD_COUNT}"
else
    echo "❌ Backup failed!"
    exit 1
fi

echo ""
echo "To restore this backup, run:"
echo "  docker compose exec -T postgres psql -U aurelia_user aurelia < ${BACKUP_FILE}"
