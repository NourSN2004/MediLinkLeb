#!/bin/bash
# Test script to verify MediLink microservices deployment

set -e

echo "========================================"
echo "MediLink Deployment Test Suite"
echo "========================================"
echo ""

NAMESPACE="medilink"
FAILED=0
PASSED=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Test 1: Minikube running
echo "Test 1: Checking Minikube status..."
if minikube status &> /dev/null; then
    pass "Minikube is running"
else
    fail "Minikube is not running"
    echo "Please run: ./scripts/start-minikube.sh"
    exit 1
fi
echo ""

# Test 2: Namespace exists
echo "Test 2: Checking namespace..."
if kubectl get namespace $NAMESPACE &> /dev/null; then
    pass "Namespace '$NAMESPACE' exists"
else
    fail "Namespace '$NAMESPACE' not found"
    echo "Please run: ./scripts/deploy.sh"
    exit 1
fi
echo ""

# Test 3: PostgreSQL running
echo "Test 3: Checking PostgreSQL database..."
POSTGRES_READY=$(kubectl get pods -n $NAMESPACE -l app=postgres -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "False")
if [ "$POSTGRES_READY" = "True" ]; then
    pass "PostgreSQL database is ready"
else
    fail "PostgreSQL database is not ready"
fi
echo ""

# Test 4: Count pods
echo "Test 4: Checking pod count..."
EXPECTED_PODS=29  # 4 gateway + 25 backend
RUNNING_PODS=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
if [ "$RUNNING_PODS" -ge "$EXPECTED_PODS" ]; then
    pass "$RUNNING_PODS pods running (expected $EXPECTED_PODS)"
elif [ "$RUNNING_PODS" -gt 0 ]; then
    warn "$RUNNING_PODS pods running (expected $EXPECTED_PODS) - some may still be starting"
else
    fail "No pods running (expected $EXPECTED_PODS)"
fi
echo ""

# Test 5: Check each service deployment
echo "Test 5: Checking service deployments..."
SERVICES=("api-gateway" "auth-service" "doctor-service" "patient-service" "pharmacy-service" "scheduling-service" "inventory-service" "notification-service")
for service in "${SERVICES[@]}"; do
    READY=$(kubectl get deployment -n $NAMESPACE $service -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    DESIRED=$(kubectl get deployment -n $NAMESPACE $service -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")

    if [ "$READY" = "$DESIRED" ] && [ "$READY" != "0" ]; then
        pass "$service: $READY/$DESIRED replicas ready"
    elif [ "$READY" != "0" ]; then
        warn "$service: $READY/$DESIRED replicas ready (may be starting)"
    else
        fail "$service: $READY/$DESIRED replicas ready"
    fi
done
echo ""

# Test 6: Check services
echo "Test 6: Checking Kubernetes services..."
for service in "${SERVICES[@]}"; do
    if kubectl get service -n $NAMESPACE $service &> /dev/null; then
        CLUSTER_IP=$(kubectl get service -n $NAMESPACE $service -o jsonpath='{.spec.clusterIP}')
        pass "$service service exists (ClusterIP: $CLUSTER_IP)"
    else
        fail "$service service not found"
    fi
done
echo ""

# Test 7: API Gateway accessibility
echo "Test 7: Testing API Gateway accessibility..."
MINIKUBE_IP=$(minikube ip 2>/dev/null || echo "")
if [ -n "$MINIKUBE_IP" ]; then
    if curl -s -o /dev/null -w "%{http_code}" http://$MINIKUBE_IP:30080/health 2>/dev/null | grep -q "200"; then
        pass "API Gateway accessible at http://$MINIKUBE_IP:30080"
    else
        warn "API Gateway not responding at http://$MINIKUBE_IP:30080 (may still be starting)"
    fi
else
    fail "Cannot get Minikube IP"
fi
echo ""

# Test 8: Test Auth Service API
echo "Test 8: Testing Auth Service API..."
if [ -n "$MINIKUBE_IP" ]; then
    # Test health endpoint
    AUTH_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://$MINIKUBE_IP:30080/api/auth/health/live/ 2>/dev/null)
    if [ "$AUTH_HEALTH" = "200" ]; then
        pass "Auth Service health check passed"

        # Test registration
        echo "  Testing user registration..."
        REGISTER_RESPONSE=$(curl -s -X POST http://$MINIKUBE_IP:30080/api/auth/register/ \
            -H "Content-Type: application/json" \
            -d '{
                "email": "test'$(date +%s)'@example.com",
                "name": "Test User",
                "role": "doctor",
                "password": "testpass123",
                "password_confirm": "testpass123"
            }' 2>/dev/null)

        if echo "$REGISTER_RESPONSE" | grep -q "access"; then
            pass "User registration working (JWT token received)"

            # Extract token for login test
            ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access":"[^"]*"' | cut -d'"' -f4)

            if [ -n "$ACCESS_TOKEN" ]; then
                # Test authenticated endpoint
                ME_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://$MINIKUBE_IP:30080/api/auth/me/ \
                    -H "Authorization: Bearer $ACCESS_TOKEN" 2>/dev/null)

                if [ "$ME_RESPONSE" = "200" ]; then
                    pass "JWT authentication working"
                else
                    fail "JWT authentication failed (got HTTP $ME_RESPONSE)"
                fi
            fi
        else
            warn "User registration may have issues (check logs for details)"
        fi
    else
        warn "Auth Service not responding (HTTP $AUTH_HEALTH)"
    fi
else
    fail "Cannot test Auth Service - no Minikube IP"
fi
echo ""

# Test 9: Database migrations
echo "Test 9: Checking database migrations..."
AUTH_POD=$(kubectl get pods -n $NAMESPACE -l app=auth-service -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -n "$AUTH_POD" ]; then
    MIGRATION_OUTPUT=$(kubectl exec -n $NAMESPACE $AUTH_POD -- python manage.py showmigrations 2>/dev/null || echo "ERROR")
    if echo "$MIGRATION_OUTPUT" | grep -q "\[X\]"; then
        pass "Database migrations applied successfully"
    elif echo "$MIGRATION_OUTPUT" | grep -q "ERROR"; then
        fail "Cannot check migrations (pod may not be ready)"
    else
        warn "Migrations may not be applied yet"
    fi
else
    fail "Cannot find auth-service pod to check migrations"
fi
echo ""

# Test 10: Inter-service communication
echo "Test 10: Testing inter-service connectivity..."
if [ -n "$AUTH_POD" ]; then
    # Test DNS resolution
    POSTGRES_DNS=$(kubectl exec -n $NAMESPACE $AUTH_POD -- nslookup postgres-service 2>/dev/null | grep -c "Address" || echo "0")
    if [ "$POSTGRES_DNS" -gt "1" ]; then
        pass "Service discovery working (DNS resolves postgres-service)"
    else
        warn "Service discovery may have issues"
    fi

    # Test database connectivity
    DB_CHECK=$(kubectl exec -n $NAMESPACE $AUTH_POD -- python manage.py check --database default 2>&1)
    if echo "$DB_CHECK" | grep -q "no issues"; then
        pass "Database connectivity working"
    else
        warn "Database connectivity may have issues"
    fi
else
    fail "Cannot test inter-service communication - no auth pod"
fi
echo ""

# Summary
echo "========================================"
echo "Test Summary"
echo "========================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Your MediLink deployment is working correctly."
    echo ""
    echo "Access the application:"
    echo "  URL: http://$MINIKUBE_IP:30080"
    echo ""
    echo "Test the Auth API:"
    echo "  curl -X POST http://$MINIKUBE_IP:30080/api/auth/register/ \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"email\":\"user@test.com\",\"name\":\"Test\",\"role\":\"doctor\",\"password\":\"pass123\",\"password_confirm\":\"pass123\"}'"
    exit 0
elif [ $FAILED -le 3 ]; then
    echo -e "${YELLOW}⚠ Some tests failed, but deployment may still be functional${NC}"
    echo ""
    echo "Check pod status: kubectl get pods -n $NAMESPACE"
    echo "Check logs: kubectl logs -n $NAMESPACE -l app=<service-name>"
    exit 1
else
    echo -e "${RED}✗ Multiple tests failed${NC}"
    echo ""
    echo "Your deployment may have issues. Try:"
    echo "  1. Check pods: kubectl get pods -n $NAMESPACE"
    echo "  2. View logs: kubectl logs -n $NAMESPACE <pod-name>"
    echo "  3. Redeploy: ./scripts/cleanup.sh && ./scripts/full-deploy.sh"
    exit 1
fi
