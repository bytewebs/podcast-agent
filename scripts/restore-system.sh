#!/bin/bash
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <backup_directory>"
  exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
  echo "❌ Backup directory not found: $BACKUP_DIR"
  exit 1
fi

echo "📥 Restoring system from $BACKUP_DIR..."

# Stop services
echo "🛑 Stopping services..."
docker-compose down

# Restore database
if [ -f "$BACKUP_DIR/database.sql" ]; then
  echo "📊 Restoring database..."
  docker-compose up -d postgres
  sleep 10
  cat "$BACKUP_DIR/database.sql" | docker-compose exec -T postgres psql -U podcast_user -d podcast_db
fi

# Restore configuration
if [ -f "$BACKUP_DIR/.env" ]; then
  echo "⚙️ Restoring configuration..."
  cp "$BACKUP_DIR/.env" .env
fi

# Start services
echo "🚀 Starting services..."
docker-compose up -d

echo "✅ System restored successfully!"
