#!/bin/bash
# Deploy MediLink microservices to Kubernetes (Minikube)

set -e

echo "====================================="
echo "Deploying MediLink to Kubernetes"
echo "====================================="
echo ""

# Base directory
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
K8S_DIR="$BASE_DIR/k8s"

# Check if minikube is running
if ! minikube status &> /dev/null; then
    echo "Error: Minikube is not running. Please start minikube first:"
    echo "  minikube start --memory=8192 --cpus=4"
    exit 1
fi

echo "Step 1: Create namespace"
kubectl apply -f "$K8S_DIR/namespace.yaml"
echo "✓ Namespace created"
echo ""

echo "Step 2: Create secrets and configmaps"
kubectl apply -f "$K8S_DIR/secrets/"
kubectl apply -f "$K8S_DIR/configmaps/"
echo "✓ Secrets and ConfigMaps created"
echo ""

echo "Step 3: Deploy PostgreSQL database"
kubectl apply -f "$K8S_DIR/database/postgres-pv.yaml"
kubectl apply -f "$K8S_DIR/database/postgres-pvc.yaml"
kubectl apply -f "$K8S_DIR/database/postgres-deployment.yaml"
kubectl apply -f "$K8S_DIR/database/postgres-service.yaml"
echo "✓ PostgreSQL deployed"
echo ""

echo "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n medilink --timeout=300s
echo "✓ PostgreSQL is ready"
echo ""

echo "Step 4: Deploy backend microservices"
kubectl apply -f "$K8S_DIR/deployments/"
kubectl apply -f "$K8S_DIR/services/"
echo "✓ Microservices deployed"
echo ""

echo "Step 5: Waiting for all pods to be ready..."
echo "This may take a few minutes..."
kubectl wait --for=condition=ready pod --all -n medilink --timeout=600s || true
echo ""

echo "====================================="
echo "Deployment Status"
echo "====================================="
kubectl get pods -n medilink
echo ""
kubectl get services -n medilink
echo ""

echo "====================================="
echo "Deployment Complete!"
echo "====================================="
echo ""
echo "To access the application:"
echo "  1. Get the Minikube IP: minikube ip"
echo "  2. Access the app at: http://\$(minikube ip):30080"
echo ""
echo "Or use port forwarding:"
echo "  kubectl port-forward -n medilink service/api-gateway 8080:80"
echo "  Then access: http://localhost:8080"
echo ""
echo "To view logs:"
echo "  kubectl logs -f -n medilink -l app=<service-name>"
echo ""
echo "To run migrations:"
echo "  ./scripts/run-migrations.sh"
