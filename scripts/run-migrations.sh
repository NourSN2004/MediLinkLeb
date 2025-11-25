#!/bin/bash
# Run Django migrations for all microservices

set -e

echo "====================================="
echo "Running Django Migrations"
echo "====================================="
echo ""

NAMESPACE="medilink"

# Services that need migrations (exclude api-gateway)
SERVICES=(
    "auth-service"
    "doctor-service"
    "patient-service"
    "pharmacy-service"
    "scheduling-service"
    "inventory-service"
    "notification-service"
)

for service in "${SERVICES[@]}"; do
    echo "--------------------------------------"
    echo "Running migrations for $service..."
    echo "--------------------------------------"

    # Get the first pod for this service
    POD=$(kubectl get pods -n $NAMESPACE -l app=$service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

    if [ -z "$POD" ]; then
        echo "⚠ No pods found for $service, skipping..."
        echo ""
        continue
    fi

    # Run migrations
    kubectl exec -n $NAMESPACE $POD -- python manage.py migrate --no-input

    echo "✓ Migrations completed for $service"
    echo ""
done

echo "====================================="
echo "All migrations completed!"
echo "====================================="
echo ""
echo "Optional: Create a superuser for auth-service:"
echo "  POD=\$(kubectl get pods -n medilink -l app=auth-service -o jsonpath='{.items[0].metadata.name}')"
echo "  kubectl exec -it -n medilink \$POD -- python manage.py createsuperuser"
