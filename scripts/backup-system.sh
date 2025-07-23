#!/bin/bash
set -e

echo "💾 Creating system backup..."

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup database
echo "📊 Backing up database..."
docker-compose exec -T postgres pg_dump -U podcast_user podcast_db > $BACKUP_DIR/database.sql

# Backup configuration
echo "⚙️ Backing up configuration..."
cp .env $BACKUP_DIR/
cp docker-compose.yml $BACKUP_DIR/

# Create backup manifest
echo "📝 Creating backup manifest..."
cat > $BACKUP_DIR/manifest.json << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "version": "1.0.0",
  "contents": [
    "database.sql",
    ".env",
    "docker-compose.yml"
  ]
}
EOF

echo "✅ Backup created at $BACKUP_DIR"
