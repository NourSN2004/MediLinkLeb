#!/bin/bash
# Build all Docker images for MediLink microservices

set -e  # Exit on error

echo "====================================="
echo "Building MediLink Microservices"
echo "====================================="
echo ""

# Set minikube docker environment
eval $(minikube -p minikube docker-env)

# Base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MICROSERVICES_DIR="$BASE_DIR/microservices"

# Services to build
SERVICES=(
    "api-gateway"
    "auth-service"
    "doctor-service"
    "patient-service"
    "pharmacy-service"
    "scheduling-service"
    "inventory-service"
    "notification-service"
)

# Build each service
for service in "${SERVICES[@]}"; do
    echo "--------------------------------------"
    echo "Building $service..."
    echo "--------------------------------------"

    cd "$MICROSERVICES_DIR/$service"

    if [ -f "Dockerfile" ]; then
        docker build -t "$service:latest" .
        echo "✓ $service built successfully"
    else
        echo "✗ Dockerfile not found for $service"
        exit 1
    fi

    echo ""
done

echo "====================================="
echo "All images built successfully!"
echo "====================================="
echo ""
echo "List of built images:"
docker images | grep -E "(api-gateway|auth-service|doctor-service|patient-service|pharmacy-service|scheduling-service|inventory-service|notification-service)"
