#!/bin/bash
# Start Minikube with appropriate resources for MediLink

set -e

echo "====================================="
echo "Starting Minikube for MediLink"
echo "====================================="
echo ""

# Check if minikube is already running
if minikube status &> /dev/null; then
    echo "Minikube is already running!"
    minikube status
    exit 0
fi

echo "Starting Minikube with:"
echo "  - Memory: 8GB"
echo "  - CPUs: 4"
echo "  - Driver: docker"
echo ""

minikube start \
    --memory=8192 \
    --cpus=4 \
    --driver=docker \
    --disk-size=20g

echo ""
echo "✓ Minikube started successfully!"
echo ""

minikube status

echo ""
echo "====================================="
echo "Minikube Ready!"
echo "====================================="
echo ""
echo "Next steps:"
echo "  1. Build images: ./scripts/build-all.sh"
echo "  2. Deploy services: ./scripts/deploy.sh"
echo "  3. Run migrations: ./scripts/run-migrations.sh"
echo ""
echo "Minikube dashboard: minikube dashboard"
