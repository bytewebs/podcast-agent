#!/bin/bash

echo "🧹 Cleaning up podcast generation system..."

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Confirm destructive action
echo -e "${YELLOW}This will remove all containers, volumes, and data. Are you sure? (y/N)${NC}"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

print_warning "Starting cleanup process..."

# Stop and remove all containers
echo "🛑 Stopping and removing containers..."
docker-compose down -v --remove-orphans

# Remove custom images
echo "🗑️ Removing custom images..."
docker rmi $(docker images | grep podcast-system | awk '{print $3}') 2>/dev/null || true

# Clean up Docker system
echo "🧽 Cleaning Docker system..."
docker system prune -f

# Remove log files
if [ -d "logs" ]; then
    echo "📝 Cleaning log files..."
    rm -rf logs/*
fi

# Remove data directories
if [ -d "data" ]; then
    echo "💾 Removing data directories..."
    rm -rf data/
fi

# Remove backup files
if [ -d "backups" ]; then
    echo "💾 Cleaning backup files..."
    rm -rf backups/*
fi

print_status "Cleanup completed!"
print_warning "Note: .env file and source code preserved"
