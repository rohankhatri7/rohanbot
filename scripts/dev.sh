#!/bin/bash
# Development helper scripts for RohanAI

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper function for colored output
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Development setup
dev_setup() {
    log "Setting up development environment..."
    
    # Create .env if it doesn't exist
    if [ ! -f .env ]; then
        cp .env.example .env
        warn "Created .env file from template. Please edit it with your tokens."
    fi
    
    # Create necessary directories
    mkdir -p logs data/processed models
    
    log "Development environment ready!"
}

# Start development services
dev_start() {
    log "Starting development services..."
    check_docker
    
    docker-compose up --build -d
    
    # Wait for services to start
    sleep 5
    
    # Check health
    if curl -f http://localhost:8000/ >/dev/null 2>&1; then
        log "API is healthy"
    else
        warn "API health check failed"
    fi
    
    log "Development services started!"
    log "API: http://localhost:8000"
    log "API Docs: http://localhost:8000/docs"
}

# Stop development services
dev_stop() {
    log "Stopping development services..."
    docker-compose down
    log "Development services stopped!"
}

# View logs
dev_logs() {
    service=${1:-""}
    if [ -z "$service" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$service"
    fi
}

# Clean up Docker resources
dev_clean() {
    log "Cleaning up Docker resources..."
    docker-compose down -v
    docker system prune -f
    log "Cleanup complete!"
}

# Health check
dev_health() {
    log "Checking service health..."
    
    echo "=== Docker Containers ==="
    docker-compose ps
    
    echo -e "\n=== API Health ==="
    if curl -f http://localhost:8000/ 2>/dev/null; then
        echo "API is healthy"
    else
        echo "API is not responding"
    fi
    
    echo -e "\n=== System Resources ==="
    echo "Memory:"
    free -h 2>/dev/null || echo "Memory info not available"
    echo "Disk:"
    df -h . 2>/dev/null || echo "Disk info not available"
}

# Test API
dev_test() {
    log "Testing API endpoints..."
    
    echo "=== Health Check ==="
    curl -s http://localhost:8000/ | jq . 2>/dev/null || curl -s http://localhost:8000/
    
    echo -e "\n=== Chat Test ==="
    curl -s -X POST http://localhost:8000/api/chat \
        -H "Content-Type: application/json" \
        -d '{"message": "Hello, this is a test!"}' | jq . 2>/dev/null || \
    curl -s -X POST http://localhost:8000/api/chat \
        -H "Content-Type: application/json" \
        -d '{"message": "Hello, this is a test!"}'
}

# Show usage
usage() {
    echo "RohanAI Development Helper"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  setup     - Initialize development environment"
    echo "  start     - Start all services"
    echo "  stop      - Stop all services"
    echo "  logs      - View logs (optional: specify service name)"
    echo "  health    - Check service health"
    echo "  test      - Test API endpoints"
    echo "  clean     - Clean up Docker resources"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs api"
    echo "  $0 health"
}

# Main command handler
case "${1:-}" in
    setup)
        dev_setup
        ;;
    start)
        dev_start
        ;;
    stop)
        dev_stop
        ;;
    logs)
        dev_logs "$2"
        ;;
    health)
        dev_health
        ;;
    test)
        dev_test
        ;;
    clean)
        dev_clean
        ;;
    *)
        usage
        exit 1
        ;;
esac
