#!/bin/bash
# Clean up MediLink deployment from Kubernetes

set -e

echo "====================================="
echo "Cleaning up MediLink Deployment"
echo "====================================="
echo ""

read -p "Are you sure you want to delete all MediLink resources? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

NAMESPACE="medilink"

echo "Deleting all resources in namespace $NAMESPACE..."

# Delete deployments
kubectl delete deployments --all -n $NAMESPACE 2>/dev/null || true

# Delete services
kubectl delete services --all -n $NAMESPACE 2>/dev/null || true

# Delete configmaps
kubectl delete configmaps --all -n $NAMESPACE 2>/dev/null || true

# Delete secrets
kubectl delete secrets --all -n $NAMESPACE 2>/dev/null || true

# Delete PVCs
kubectl delete pvc --all -n $NAMESPACE 2>/dev/null || true

# Delete PVs (labeled for postgres)
kubectl delete pv postgres-pv 2>/dev/null || true

# Delete namespace
kubectl delete namespace $NAMESPACE 2>/dev/null || true

echo ""
echo "====================================="
echo "Cleanup Complete!"
echo "====================================="
echo ""
echo "All MediLink resources have been removed."
echo "To redeploy, run: ./scripts/deploy.sh"
