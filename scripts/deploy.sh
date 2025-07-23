#!/bin/bash
set -e

echo "🚀 Starting podcast generation system deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

print_status "Docker is running"

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install Docker Compose."
    exit 1
fi

print_status "Docker Compose is available"

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning "No .env file found. Creating from template..."
    if [ -f .env.template ]; then
        cp .env.template .env
        print_info "Please edit .env with your actual configuration values"
        print_info "Required: OPENAI_API_KEY, AWS credentials, Google Cloud credentials"
        echo -e "${YELLOW}Do you want to continue with default values? (y/N)${NC}"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_info "Please edit .env file and run deploy script again"
            exit 0
        fi
    else
        print_error ".env.template not found. Please create .env file manually."
        exit 1
    fi
fi

print_status ".env file exists"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p data/postgres
mkdir -p data/kafka
mkdir -p backups

print_status "Directories created"

# Stop any existing services
echo "🛑 Stopping existing services..."
docker-compose down --remove-orphans || true

print_status "Existing services stopped"

# Pull latest images
echo "📥 Pulling latest Docker images..."
docker-compose pull

print_status "Images pulled"

# Build custom images
echo "🔨 Building custom Docker images..."
docker-compose build --no-cache

print_status "Images built"

# Start core infrastructure first
echo "🏗️ Starting core infrastructure..."
docker-compose up -d postgres zookeeper kafka redis

print_info "Waiting for core services to be healthy..."
sleep 30

# Check if Kafka is ready
echo "🔍 Checking Kafka readiness..."
for i in {1..30}; do
    if docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list &> /dev/null; then
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "Kafka failed to start properly"
        docker-compose logs kafka
        exit 1
    fi
    sleep 2
done

print_status "Kafka is ready"

# Check if PostgreSQL is ready
echo "🔍 Checking PostgreSQL readiness..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U podcast_user -d podcast_db &> /dev/null; then
        break
    fi
    if [ $i -eq 30 ]; then
        print_error "PostgreSQL failed to start properly"
        docker-compose logs postgres
        exit 1
    fi
    sleep 2
done

print_status "PostgreSQL is ready"

# Start API service
echo "🌐 Starting API service..."
docker-compose up -d api

print_info "Waiting for API service to be ready..."
sleep 15

# Check API health
for i in {1..20}; do
    if curl -f http://localhost:5050/health &> /dev/null; then
        break
    fi
    if [ $i -eq 20 ]; then
        print_error "API service failed to start properly"
        docker-compose logs api
        exit 1
    fi
    sleep 3
done

print_status "API service is healthy"

# Start worker services
echo "👷 Starting worker services..."
docker-compose up -d \
    outline-worker \
    outline-evaluation-worker \
    outline-guardrails-worker \
    outline-approval-worker \
    script-worker \
    script-evaluation-worker \
    script-guardrails-worker \
    script-approval-worker \
    tts-worker \
    tts-evaluation-worker \
    audio-approval-worker \
    publishing-worker

print_info "Waiting for workers to start..."
sleep 10

print_status "Worker services started"

# Start Airflow if enabled
if grep -q "AIRFLOW_ENABLED=true" .env 2>/dev/null; then
    echo "🌊 Starting Airflow services..."
    docker-compose up -d airflow-webserver airflow-scheduler
    
    print_info "Waiting for Airflow to be ready..."
    sleep 20
    
    for i in {1..20}; do
        if curl -f http://localhost:8080/health &> /dev/null; then
            break
        fi
        if [ $i -eq 20 ]; then
            print_warning "Airflow may not be ready yet, but continuing..."
            break
        fi
        sleep 3
    done
    
    print_status "Airflow services started"
fi

# Run system validation
echo "🔍 Running system validation..."
if command -v python3 &> /dev/null; then
    if [ -f scripts/validate-system.py ]; then
        python3 scripts/validate-system.py
        if [ $? -eq 0 ]; then
            print_status "System validation passed"
        else
            print_warning "System validation had issues, but deployment continued"
        fi
    else
        print_warning "Validation script not found, skipping validation"
    fi
else
    print_warning "Python3 not found, skipping validation"
fi

# Show service status
echo "📊 Service Status:"
docker-compose ps

# Final status check
echo ""
echo "🎉 Deployment Summary:"
print_status "API available at: http://localhost:5050"
print_status "Health check: http://localhost:5050/health"
print_status "API docs: http://localhost:5050/api/docs"

if grep -q "AIRFLOW_ENABLED=true" .env 2>/dev/null; then
    print_status "Airflow UI: http://localhost:8080"
fi

echo ""
echo "📝 Quick Test:"
echo "curl -X POST http://localhost:5050/api/v1/podcast/create \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"topic\": \"Test Podcast\","
echo "    \"tone\": \"professional\","
echo "    \"length_minutes\": 10"
echo "  }'"

echo ""
echo "📋 Management Commands:"
echo "  Stop:    docker-compose down"
echo "  Logs:    docker-compose logs [service]"
echo "  Restart: docker-compose restart [service]"

echo ""
print_status "Podcast Generation System deployed successfully! 🎙️"