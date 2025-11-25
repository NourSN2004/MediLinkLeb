# MediLink Testing - Command Cheatsheet

Copy and paste these commands to test your microservices.

---

## 🚀 STEP 1: Deploy (One-Time Setup)

```bash
# Start Minikube
minikube start --cpus=4 --memory=8192 --disk-size=20g

# Configure Docker
eval $(minikube docker-env)

# Deploy everything
./scripts/full-deploy.sh
```

**Wait 10-15 minutes for deployment to complete.**

---

## 🧪 STEP 2: Run Automated Tests

```bash
# Run automated test suite
./scripts/quick-test.sh
```

**This will test everything and give you a token to use below.**

---

## 📝 STEP 3: Set Variables from Test Output

After the automated test, you'll see output like this - **copy and run it:**

```bash
export TOKEN="eyJ0eXAiOiJKV1Qi..."
export API_URL="http://192.168.49.2:31234"
export USER_ID="1"
```

---

## 🔍 Manual Testing Commands

### Register New Users

**Register a doctor:**
```bash
curl -X POST "$API_URL/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "dr_smith",
    "email": "drsmith@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "John",
    "last_name": "Smith",
    "role": "doctor"
  }'
```

**Register a patient:**
```bash
curl -X POST "$API_URL/api/auth/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "patient_jane",
    "email": "jane@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "Jane",
    "last_name": "Doe",
    "role": "patient"
  }'
```

### Login

```bash
curl -X POST "$API_URL/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "dr_smith",
    "password": "SecurePass123!"
  }'
```

**Copy the "access" token from the response and set it:**
```bash
export TOKEN="<paste-token-here>"
```

### Get User Profile

```bash
curl -X GET "$API_URL/api/auth/profile/" \
  -H "Authorization: Bearer $TOKEN"
```

### Create Doctor Profile

```bash
curl -X POST "$API_URL/api/doctors/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "user_id": 1,
    "specialty": "Cardiology",
    "license_number": "MD12345"
  }'
```

### Add Working Hours

**Monday 9 AM - 5 PM:**
```bash
curl -X POST "$API_URL/api/doctors/1/working-hours/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "day_of_week": 1,
    "start_time": "09:00:00",
    "end_time": "17:00:00"
  }'
```

**Add full week (Mon-Fri):**
```bash
for day in 1 2 3 4 5; do
  curl -X POST "$API_URL/api/doctors/1/working-hours/" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d "{
      \"day_of_week\": $day,
      \"start_time\": \"09:00:00\",
      \"end_time\": \"17:00:00\"
    }"
done
```

### Add Time-Off (Lunch Break)

```bash
TOMORROW=$(date -d "+1 day" +%Y-%m-%d)

curl -X POST "$API_URL/api/doctors/1/time-off/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"date\": \"$TOMORROW\",
    \"start_time\": \"12:00:00\",
    \"end_time\": \"13:00:00\",
    \"reason\": \"Lunch break\"
  }"
```

### Calculate Available Slots ⭐ (MOST IMPORTANT)

**30-minute appointments:**
```bash
TOMORROW=$(date -d "+1 day" +%Y-%m-%d)

curl -X GET "$API_URL/api/doctors/1/availability/?date=$TOMORROW&duration=30" \
  -H "Authorization: Bearer $TOKEN"
```

**15-minute appointments:**
```bash
curl -X GET "$API_URL/api/doctors/1/availability/?date=$TOMORROW&duration=15" \
  -H "Authorization: Bearer $TOKEN"
```

**60-minute appointments:**
```bash
curl -X GET "$API_URL/api/doctors/1/availability/?date=$TOMORROW&duration=60" \
  -H "Authorization: Bearer $TOKEN"
```

### List All Doctors

```bash
curl -X GET "$API_URL/api/doctors/" \
  -H "Authorization: Bearer $TOKEN"
```

### Search Doctors by Specialty

```bash
curl -X GET "$API_URL/api/doctors/search/?specialty=Cardiology" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Specific Doctor

```bash
curl -X GET "$API_URL/api/doctors/1/" \
  -H "Authorization: Bearer $TOKEN"
```

### Update Doctor Profile

```bash
curl -X PATCH "$API_URL/api/doctors/1/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "specialty": "Interventional Cardiology"
  }'
```

### List Doctor's Working Hours

```bash
curl -X GET "$API_URL/api/doctors/1/working-hours/" \
  -H "Authorization: Bearer $TOKEN"
```

### List Doctor's Time-Off

```bash
curl -X GET "$API_URL/api/doctors/1/time-off/" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔧 Infrastructure Commands

### Check All Pods

```bash
kubectl get pods -n medilink
```

**Expected: 29 pods (22 Running, 7 Completed)**

### Check Services

```bash
kubectl get services -n medilink
```

**Expected: 9 services**

### Get API Gateway URL

```bash
minikube service api-gateway-service -n medilink --url
```

### Check Logs

**Auth service:**
```bash
kubectl logs -l app=auth-service -n medilink --tail=50
```

**Doctor service:**
```bash
kubectl logs -l app=doctor-service -n medilink --tail=50
```

**Specific pod:**
```bash
kubectl logs <pod-name> -n medilink
```

### Access Database

```bash
kubectl exec -it postgres-0 -n medilink -- psql -U medilink -d medilink_db
```

**Inside PostgreSQL:**
```sql
\dt                              -- List tables
SELECT * FROM auth_user;         -- List users
SELECT * FROM doctors;           -- List doctors
SELECT * FROM doctor_working_hours;  -- List working hours
SELECT * FROM doctor_time_off;   -- List time-off
\q                               -- Quit
```

### Restart Services

```bash
kubectl rollout restart deployment auth-service -n medilink
kubectl rollout restart deployment doctor-service -n medilink
```

### Check Pod Health

```bash
kubectl describe pod <pod-name> -n medilink
```

### Port Forward (Alternative to Minikube Service)

```bash
kubectl port-forward -n medilink service/api-gateway-service 8080:8000
```

**Then use: `http://localhost:8080` as API_URL**

---

## 🐛 Debugging Commands

### Check Pod Events

```bash
kubectl get events -n medilink --sort-by='.lastTimestamp'
```

### Get Pod Details

```bash
kubectl describe pod <pod-name> -n medilink
```

### Interactive Shell in Pod

```bash
kubectl exec -it <pod-name> -n medilink -- /bin/sh
```

**Inside pod:**
```bash
curl http://auth-service:8000/health/
curl http://doctor-service:8000/health/
env | grep DB
```

### Check Resource Usage

```bash
kubectl top nodes
kubectl top pods -n medilink
```

### Check ConfigMaps and Secrets

```bash
kubectl get configmaps -n medilink
kubectl get secrets -n medilink
kubectl describe configmap shared-config -n medilink
```

---

## 🧹 Cleanup Commands

### Delete Everything

```bash
kubectl delete namespace medilink
```

### Delete and Redeploy

```bash
kubectl delete namespace medilink
./scripts/full-deploy.sh
```

### Stop Minikube

```bash
minikube stop
```

### Delete Minikube (Fresh Start)

```bash
minikube delete
minikube start --cpus=4 --memory=8192 --disk-size=20g
```

---

## 📊 Quick Verification

### Are pods running?

```bash
kubectl get pods -n medilink | grep Running | wc -l
```

**Expected: 22**

### Is database accessible?

```bash
kubectl exec -it postgres-0 -n medilink -- psql -U medilink -d medilink_db -c "SELECT 1;"
```

**Expected: "1"**

### Can I access API Gateway?

```bash
curl -s $(minikube service api-gateway-service -n medilink --url)/health/
```

**Expected: `{"status": "healthy"}`**

### Are services healthy?

```bash
kubectl run curl-test --image=curlimages/curl -i --rm --restart=Never -n medilink -- \
  curl -s http://auth-service:8000/health/

kubectl run curl-test --image=curlimages/curl -i --rm --restart=Never -n medilink -- \
  curl -s http://doctor-service:8000/health/
```

**Expected: `{"status": "healthy"}` for both**

---

## 💡 Pro Tips

### Save Token for Session

```bash
# After login, save token
export TOKEN="your-token-here"

# Verify it's set
echo $TOKEN

# Use in all subsequent requests
curl -H "Authorization: Bearer $TOKEN" ...
```

### Format JSON Output (if jq installed)

```bash
curl ... | jq '.'

# Install jq:
sudo apt-get install jq
```

### Watch Pods in Real-Time

```bash
watch kubectl get pods -n medilink
```

### Follow Logs in Real-Time

```bash
kubectl logs -f -l app=doctor-service -n medilink
```

### Quick Health Check All Services

```bash
for service in auth-service doctor-service patient-service pharmacy-service scheduling-service inventory-service notification-service; do
  echo "Testing $service..."
  kubectl run curl-test --image=curlimages/curl -i --rm --restart=Never -n medilink -- \
    curl -s http://$service:8000/health/
done
```

---

## 📚 More Information

- **Complete testing guide:** `TESTING_GUIDE.md`
- **Quick start:** `QUICK_START.md`
- **Deployment guide:** `DEPLOYMENT_GUIDE.md`
- **Architecture:** `MICROSERVICES_DESIGN.md`
- **Implementation details:** `IMPLEMENTATION_COMPLETE_DETAILED.md`
- **Academic report:** `OVERLEAF_IMPLEMENTATION_REPORT.tex`

---

## ⚡ Copy-Paste Quick Test

**Complete test in 30 seconds:**

```bash
# Set variables (from automated test output)
export TOKEN="<your-token>"
export API_URL="<your-api-url>"

# Test availability
TOMORROW=$(date -d "+1 day" +%Y-%m-%d)
curl -X GET "$API_URL/api/doctors/1/availability/?date=$TOMORROW&duration=30" \
  -H "Authorization: Bearer $TOKEN" | jq '.'

# If you see available_slots with 15-minute increments, IT WORKS! ✅
```

---

**Questions? Check logs:**
```bash
kubectl logs -l app=doctor-service -n medilink --tail=100
```
