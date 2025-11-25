#!/usr/bin/env python3
"""
Script to generate Kubernetes deployment and service manifests for all microservices
"""
from pathlib import Path

K8S_DIR = Path(__file__).parent.parent / "k8s"

# Service configurations with replica counts as per architecture document
SERVICES = [
    {"name": "api-gateway", "port": 80, "replicas": 4, "image": "api-gateway"},
    {"name": "auth-service", "port": 8001, "replicas": 3, "image": "auth-service"},
    {"name": "doctor-service", "port": 8002, "replicas": 3, "image": "doctor-service"},
    {"name": "patient-service", "port": 8003, "replicas": 4, "image": "patient-service"},
    {"name": "pharmacy-service", "port": 8004, "replicas": 2, "image": "pharmacy-service"},
    {"name": "scheduling-service", "port": 8005, "replicas": 4, "image": "scheduling-service"},
    {"name": "inventory-service", "port": 8006, "replicas": 3, "image": "inventory-service"},
    {"name": "notification-service", "port": 8007, "replicas": 2, "image": "notification-service"},
]

DEPLOYMENT_TEMPLATE = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: medilink
  labels:
    app: {name}
    tier: {tier}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {name}
  template:
    metadata:
      labels:
        app: {name}
        tier: {tier}
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - {name}
              topologyKey: kubernetes.io/hostname
      containers:
      - name: {name}
        image: {image}:latest
        imagePullPolicy: Never
        ports:
        - containerPort: {port}
          name: http
        envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: db-secrets
        - secretRef:
            name: app-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/live/
            port: {port}
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health/ready/
            port: {port}
          initialDelaySeconds: 20
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
"""

SERVICE_TEMPLATE = """apiVersion: v1
kind: Service
metadata:
  name: {name}
  namespace: medilink
  labels:
    app: {name}
    tier: {tier}
spec:
  type: {service_type}
  ports:
  - port: {port}
    targetPort: {port}
    protocol: TCP
    name: http
{node_port}
  selector:
    app: {name}
"""

def create_file(path, content):
    """Create a file with content"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"Created: {path}")

def generate_deployment(service):
    """Generate deployment manifest for a service"""
    name = service['name']
    tier = 'frontend' if name == 'api-gateway' else 'backend'

    deployment_content = DEPLOYMENT_TEMPLATE.format(
        name=name,
        image=service['image'],
        port=service['port'],
        replicas=service['replicas'],
        tier=tier
    )

    deployment_file = K8S_DIR / "deployments" / f"{name}-deployment.yaml"
    create_file(deployment_file, deployment_content)

def generate_service(service):
    """Generate service manifest for a service"""
    name = service['name']
    tier = 'frontend' if name == 'api-gateway' else 'backend'

    # API Gateway should be NodePort for external access, others ClusterIP
    if name == 'api-gateway':
        service_type = 'NodePort'
        node_port = '    nodePort: 30080'
    else:
        service_type = 'ClusterIP'
        node_port = ''

    service_content = SERVICE_TEMPLATE.format(
        name=name,
        port=service['port'],
        tier=tier,
        service_type=service_type,
        node_port=node_port
    )

    service_file = K8S_DIR / "services" / f"{name}-service.yaml"
    create_file(service_file, service_content)

def main():
    """Generate all Kubernetes manifests"""
    print("Generating Kubernetes manifests...\n")

    for service in SERVICES:
        print(f"=== {service['name']} ({service['replicas']} replicas) ===")
        generate_deployment(service)
        generate_service(service)
        print()

    print("="*50)
    print("All Kubernetes manifests generated successfully!")
    print("="*50)

if __name__ == "__main__":
    main()
