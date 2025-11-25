# MediLink Microservices Architecture Design

## Overview
This document outlines the design for migrating MediLink from a Django monolith to a microservices architecture running on Kubernetes (Minikube).

## Technology Stack

### Backend Services
- **Framework**: Django 4.2 + Django REST Framework
- **Language**: Python 3.12
- **API Style**: RESTful HTTP/JSON
- **Authentication**: JWT tokens (shared across services)
- **Database**: PostgreSQL 15 (shared database)

### Frontend
- **API Gateway**: NGINX
- **Frontend**: Static SPA (HTML/CSS/JavaScript with modern frameworks)
- **Communication**: REST API calls to backend services via API Gateway

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Kubernetes (Minikube for local dev)
- **Database**: PostgreSQL StatefulSet in Kubernetes

## Microservices Architecture

### Service Boundaries

#### 1. API Gateway & Frontend Service (4 replicas)
**Responsibility**:
- Route incoming HTTP requests to appropriate backend services
- Serve static frontend assets
- Rate limiting and basic WAF
- CORS policy enforcement

**Technology**: NGINX + Static HTML/CSS/JS
**Port**: 80/443
**Routes to**: All backend services

---

#### 2. Auth & Access Service (3 replicas)
**Responsibility**: User authentication, registration, password reset, JWT token issuance

**Models**:
- User (email, name, role, phone_number, password, reset tokens)

**Endpoints**:
- POST /api/auth/signup
- POST /api/auth/login
- POST /api/auth/logout
- POST /api/auth/forgot-password
- POST /api/auth/reset-password
- GET /api/auth/verify-email/:token
- GET /api/auth/me (current user info)
- GET /api/auth/users/:id (for inter-service calls)

**Dependencies**: None (foundational service)
**Port**: 8001

---

#### 3. Doctor Service (3 replicas)
**Responsibility**: Doctor profiles, working hours, time-off management

**Models**:
- Doctor (specialty, license_number)
- DoctorWorkingHours (day_of_week, start_time, end_time)
- DoctorTimeOff (date, start_time, end_time, reason)

**Endpoints**:
- GET /api/doctors (list all doctors)
- GET /api/doctors/:id (doctor profile)
- PUT /api/doctors/:id (update profile)
- GET /api/doctors/:id/working-hours
- POST /api/doctors/:id/working-hours
- PUT /api/doctors/:id/working-hours/:id
- DELETE /api/doctors/:id/working-hours/:id
- GET /api/doctors/:id/time-off
- POST /api/doctors/:id/time-off
- DELETE /api/doctors/:id/time-off/:id
- GET /api/doctors/:id/availability (calculate available slots)
- GET /api/doctors/:id/dashboard (aggregated dashboard data)

**Dependencies**:
- Auth Service (user info)
- Scheduling Service (appointments for dashboard)
- Notification Service (missed appointment alerts)

**Port**: 8002

---

#### 4. Patient Service (4 replicas)
**Responsibility**: Patient profiles, medical history, test results

**Models**:
- Patient (national_id, dob, gender, blood_type, history_summary)
- PatientTestResult (patient, test_result file)

**Endpoints**:
- GET /api/patients (search patients by name)
- GET /api/patients/:id (patient profile)
- PUT /api/patients/:id (update profile)
- PUT /api/patients/:id/medical-history
- GET /api/patients/:id/test-results
- POST /api/patients/:id/test-results
- GET /api/patients/:id/dashboard (aggregated dashboard data)
- GET /api/patients/:id/prescriptions (calls Inventory Service internally)

**Dependencies**:
- Auth Service (user info)
- Scheduling Service (appointments)
- Inventory Service (medicine prescriptions)

**Port**: 8003

---

#### 5. Pharmacy Service (2 replicas)
**Responsibility**: Pharmacy profiles, branch data, pharmacist staff management

**Models**:
- Pharmacy (address, license_number)
- PharmacistStaff (name, email, phone)

**Endpoints**:
- GET /api/pharmacies (list pharmacies)
- GET /api/pharmacies/:id (pharmacy profile)
- PUT /api/pharmacies/:id (update pharmacy name/address)
- GET /api/pharmacies/:id/staff
- POST /api/pharmacies/:id/staff
- PUT /api/pharmacies/:id/staff/:id
- DELETE /api/pharmacies/:id/staff/:id
- GET /api/pharmacies/:id/dashboard (aggregated data)

**Dependencies**:
- Auth Service (user info)
- Inventory Service (stock counts, low/expiring/expired stats)

**Port**: 8004

---

#### 6. Scheduling Service (4 replicas)
**Responsibility**: Appointments, conflict checking, availability calculation

**Models**:
- Appointment (doctor, patient, date_time, status, notes, doctor_notes)

**Endpoints**:
- GET /api/appointments (filter by doctor/patient/date/status)
- POST /api/appointments (create new appointment)
- GET /api/appointments/:id
- PUT /api/appointments/:id
- DELETE /api/appointments/:id (cancel)
- PATCH /api/appointments/:id/complete
- PATCH /api/appointments/:id/cancel
- GET /api/appointments/doctor/:id/today
- GET /api/appointments/doctor/:id/upcoming
- GET /api/appointments/doctor/:id/past
- GET /api/appointments/patient/:id/upcoming
- GET /api/appointments/calendar/:doctor_id/:year/:month

**Dependencies**:
- Auth Service (validate users)
- Doctor Service (validate availability)
- Patient Service (patient info)

**Port**: 8005

---

#### 7. Inventory Service (3 replicas)
**Responsibility**: Medicine catalog, pharmacy stock, expiry tracking, prescriptions

**Models**:
- Medicine (name, dosage_form, strength, description)
- Stock (pharmacy, medicine, quantity, price, expiry_date)
- Prescribes (doctor, patient, medicine, date_prescribed, dosage, duration, extra_notes)

**Endpoints**:
- GET /api/medicines (search/browse catalog)
- GET /api/medicines/:id
- POST /api/medicines (create new medicine)
- GET /api/stock (filter by pharmacy)
- POST /api/stock (add stock entry)
- PUT /api/stock/:id (update quantity/price/expiry)
- DELETE /api/stock/:id
- GET /api/stock/pharmacy/:id/summary (total, low, expiring, expired counts)
- GET /api/stock/pharmacy/:id/inventory (full inventory with filters)
- GET /api/prescriptions (filter by patient/doctor)
- POST /api/prescriptions
- GET /api/prescriptions/patient/:id

**Dependencies**:
- Auth Service (user validation)
- Pharmacy Service (pharmacy info)

**Port**: 8006

---

#### 8. Notification Service (2 replicas)
**Responsibility**: Missed appointment notifications, critical inventory alerts

**Models**:
- Notification (user, type, message, read, created_at)

**Endpoints**:
- GET /api/notifications/user/:id
- POST /api/notifications (create notification)
- PATCH /api/notifications/:id/read
- DELETE /api/notifications/:id
- GET /api/notifications/doctor/:id/missed-appointments

**Dependencies**:
- Scheduling Service (listen for missed appointments)
- Inventory Service (listen for low/expired stock)

**Port**: 8007

---

## Database Strategy

### Shared PostgreSQL Database
Per architecture requirements, all services connect to a **single PostgreSQL instance** but maintain logical separation:

```
medilink_db (PostgreSQL database)
├── auth_users                    (Auth Service)
├── doctor_profiles               (Doctor Service)
├── doctor_working_hours          (Doctor Service)
├── doctor_time_off               (Doctor Service)
├── patient_profiles              (Patient Service)
├── patient_test_results          (Patient Service)
├── pharmacy_profiles             (Pharmacy Service)
├── pharmacy_staff                (Pharmacy Service)
├── appointments                  (Scheduling Service)
├── medicines                     (Inventory Service)
├── stock                         (Inventory Service)
├── prescriptions                 (Inventory Service)
└── notifications                 (Notification Service)
```

**Database Connection**:
- All services connect to: `postgresql://medilink:password@postgres-service:5432/medilink_db`
- Managed via Kubernetes Secret

**Migrations**:
- Each service manages its own Django migrations
- Database initialization runs migrations for all services in order

---

## Inter-Service Communication

### Authentication Flow
1. User logs in via Frontend → API Gateway → Auth Service
2. Auth Service returns JWT token
3. Frontend includes JWT in all subsequent requests
4. Each service validates JWT (shared secret key)
5. Services extract user_id and role from JWT

### Service-to-Service Calls
Services communicate via HTTP REST APIs using internal Kubernetes service DNS:

Example: Doctor Service needs to fetch appointments
```python
response = requests.get(
    'http://scheduling-service:8005/api/appointments',
    params={'doctor_id': doctor_id},
    headers={'X-Service-Auth': SERVICE_SECRET}
)
```

### Service Discovery
- Kubernetes DNS: `<service-name>.<namespace>.svc.cluster.local`
- Simplified: `<service-name>:port` (same namespace)

---

## Project Structure

```
MediLinkLeb-Copy/
├── microservices/
│   ├── api-gateway/
│   │   ├── nginx.conf
│   │   ├── Dockerfile
│   │   └── frontend/
│   │       ├── index.html
│   │       ├── css/
│   │       ├── js/
│   │       └── assets/
│   │
│   ├── auth-service/
│   │   ├── manage.py
│   │   ├── auth_service/
│   │   │   ├── settings.py
│   │   │   ├── urls.py
│   │   │   └── wsgi.py
│   │   ├── accounts/
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   └── migrations/
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── doctor-service/
│   │   ├── manage.py
│   │   ├── doctor_service/
│   │   ├── doctors/
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   └── urls.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── patient-service/
│   │   └── [similar structure]
│   │
│   ├── pharmacy-service/
│   │   └── [similar structure]
│   │
│   ├── scheduling-service/
│   │   └── [similar structure]
│   │
│   ├── inventory-service/
│   │   └── [similar structure]
│   │
│   └── notification-service/
│       └── [similar structure]
│
├── k8s/
│   ├── namespace.yaml
│   ├── database/
│   │   ├── postgres-pv.yaml
│   │   ├── postgres-pvc.yaml
│   │   ├── postgres-deployment.yaml
│   │   └── postgres-service.yaml
│   ├── configmaps/
│   │   └── app-config.yaml
│   ├── secrets/
│   │   └── db-secrets.yaml
│   ├── deployments/
│   │   ├── api-gateway-deployment.yaml
│   │   ├── auth-deployment.yaml
│   │   ├── doctor-deployment.yaml
│   │   ├── patient-deployment.yaml
│   │   ├── pharmacy-deployment.yaml
│   │   ├── scheduling-deployment.yaml
│   │   ├── inventory-deployment.yaml
│   │   └── notification-deployment.yaml
│   └── services/
│       ├── api-gateway-service.yaml
│       ├── auth-service.yaml
│       ├── doctor-service.yaml
│       ├── patient-service.yaml
│       ├── pharmacy-service.yaml
│       ├── scheduling-service.yaml
│       ├── inventory-service.yaml
│       └── notification-service.yaml
│
└── scripts/
    ├── build-all.sh
    ├── deploy-db.sh
    ├── deploy-services.sh
    ├── run-migrations.sh
    └── cleanup.sh
```

---

## Deployment Strategy

### Phase 1: Setup Minikube & Database
1. Start minikube with sufficient resources
2. Create namespace: `medilink`
3. Deploy PostgreSQL StatefulSet
4. Create database and apply initial schema

### Phase 2: Build Service Images
1. Build Docker images for all 8 services
2. Load images into minikube (or push to local registry)

### Phase 3: Deploy Backend Services
1. Apply ConfigMaps and Secrets
2. Deploy services in dependency order:
   - Auth Service (no dependencies)
   - Doctor, Patient, Pharmacy Services
   - Scheduling Service
   - Inventory Service
   - Notification Service

### Phase 4: Deploy API Gateway
1. Deploy NGINX with frontend assets
2. Configure routing to backend services
3. Expose via NodePort or LoadBalancer

### Phase 5: Run Migrations
1. Run Django migrations for each service
2. Populate demo data if needed

### Phase 6: Testing
1. Test individual service endpoints
2. Test end-to-end user flows
3. Verify inter-service communication

---

## Kubernetes Resources

### Replica Counts (as per architecture document)
- API Gateway: 4 replicas
- Auth Service: 3 replicas
- Doctor Service: 3 replicas
- Patient Service: 4 replicas
- Pharmacy Service: 2 replicas
- Scheduling Service: 4 replicas
- Inventory Service: 3 replicas
- Notification Service: 2 replicas

**Total Pods**: 25 backend pods + 1 database pod = 26 pods

### Resource Limits (per pod)
```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Health Checks
All services implement:
- **Liveness Probe**: `GET /health/live`
- **Readiness Probe**: `GET /health/ready`

---

## Security Considerations

### Authentication
- JWT tokens with 24-hour expiration
- Shared JWT secret across services (via Kubernetes Secret)
- Refresh token mechanism

### Service-to-Service Auth
- Internal API calls use `X-Service-Auth` header
- Service secret key shared via ConfigMap/Secret

### Database Security
- Database credentials stored in Kubernetes Secret
- No external database access (ClusterIP only)

### Network Policies
- Services only accessible via API Gateway (except internal calls)
- Database only accessible from backend services

---

## Monitoring & Logging

### Health Endpoints
Each service exposes:
- `/health/live` - Liveness check
- `/health/ready` - Readiness check (includes DB connection)

### Logging
- All services log to stdout/stderr
- Kubernetes aggregates logs
- Structured JSON logging for parsing

---

## Migration Path from Monolith

### Code Migration
1. **Models**: Copy to respective service, adjust foreign keys
2. **Views**: Convert to DRF ViewSets/APIViews
3. **Forms**: Convert to DRF Serializers
4. **Templates**: Convert to SPA components or keep for API Gateway
5. **Business Logic**: Refactor into service layers

### Data Migration
1. Export data from SQLite
2. Transform to match new schema (if needed)
3. Import into PostgreSQL
4. Run migrations for each service

### Gradual Migration (if needed)
1. Start with Auth Service (foundational)
2. Migrate one domain at a time
3. Use API Gateway to route to monolith for unmigrated features
4. Complete when all domains are migrated

---

## Next Steps

1. Create base Django project structure for each service
2. Define models and serializers
3. Implement REST API endpoints
4. Create Dockerfiles
5. Write Kubernetes manifests
6. Build and deploy to minikube
7. Test and validate

