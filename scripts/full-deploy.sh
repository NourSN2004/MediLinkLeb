#!/bin/bash
# Complete deployment script - builds and deploys everything

set -e

echo "========================================"
echo "MediLink Full Deployment"
echo "========================================"
echo ""

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Step 1: Start Minikube (if not running)
echo "Step 1/5: Checking Minikube..."
if ! minikube status &> /dev/null; then
    echo "Starting Minikube..."
    bash "$BASE_DIR/start-minikube.sh"
else
    echo "✓ Minikube is already running"
fi
echo ""

# Step 2: Build all images
echo "Step 2/5: Building Docker images..."
bash "$BASE_DIR/build-all.sh"
echo ""

# Step 3: Deploy to Kubernetes
echo "Step 3/5: Deploying to Kubernetes..."
bash "$BASE_DIR/deploy.sh"
echo ""

# Step 4: Run migrations
echo "Step 4/5: Running database migrations..."
sleep 10  # Wait a bit for pods to stabilize
bash "$BASE_DIR/run-migrations.sh"
echo ""

# Step 5: Show access information
echo "Step 5/5: Getting access information..."
echo ""

MINIKUBE_IP=$(minikube ip)

echo "========================================"
echo "Deployment Complete!"
echo "========================================"
echo ""
echo "🎉 MediLink is now running on Minikube!"
echo ""
echo "Access the application at:"
echo "  http://$MINIKUBE_IP:30080"
echo ""
echo "Or use port forwarding:"
echo "  kubectl port-forward -n medilink service/api-gateway 8080:80"
echo "  Then visit: http://localhost:8080"
echo ""
echo "Useful commands:"
echo "  - View pods: kubectl get pods -n medilink"
echo "  - View logs: kubectl logs -f -n medilink -l app=auth-service"
echo "  - Dashboard: minikube dashboard"
echo "  - Clean up: ./scripts/cleanup.sh"
echo ""
