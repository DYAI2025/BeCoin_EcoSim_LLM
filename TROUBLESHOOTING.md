# Fly.io Deployment Troubleshooting Guide

## Issues Found and Fixed

### Issue 1: Missing PYTHONPATH ❌ → ✅ FIXED
**Problem**: The Dockerfile didn't set PYTHONPATH, causing Python to not find the `dashboard` and `becoin_economy` modules.

**Symptom**: `ModuleNotFoundError: No module named 'dashboard'` or similar import errors.

**Fix Applied**:
```dockerfile
# Added PYTHONPATH to Dockerfile
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    ...
```

Also added to `fly.toml`:
```toml
[env]
  PYTHONPATH = "/app"
```

---

### Issue 2: Insufficient Memory ❌ → ✅ FIXED
**Problem**: 256MB RAM is too low for Python + FastAPI + all dependencies. The app would crash or fail to start.

**Symptom**: Container crashes, OOM (out of memory) errors in logs.

**Fix Applied**:
```toml
# Increased from 256mb to 512mb in fly.toml
[[vm]]
  size = "shared-cpu-1x"
  memory = "512mb"
```

---

### Issue 3: Volume Mount Blocking Deployment ❌ → ✅ FIXED
**Problem**: The `[mounts]` section referenced a volume `becoin_data` that doesn't exist, causing deployment to fail.

**Symptom**: Deployment fails with volume not found error.

**Fix Applied**:
```toml
# Commented out volume mount (made optional)
# Optional: Uncomment to use persistent volume for discovery sessions
# You must create the volume first: fly volumes create becoin_data --size 1 --region iad
# [mounts]
#   source = "becoin_data"
#   destination = "/app/.claude-flow"
```

The directory is created in the Docker image, so the app works without a volume. If you need persistence, create the volume first and then uncomment.

---

### Issue 4: Wrong Health Check Command ❌ → ✅ FIXED
**Problem**: Health check used Python urllib which requires Python to be invoked as a module, but `curl` is simpler and more reliable.

**Symptom**: Health checks fail even when app is running.

**Fix Applied**:
```dockerfile
# Changed from Python urllib to curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/api/status || exit 1

# Also added curl to system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*
```

---

### Issue 5: CMD Using `python -m` Unnecessarily ❌ → ✅ FIXED
**Problem**: Using `python -m uvicorn` adds unnecessary complexity. Direct `uvicorn` command is cleaner with PYTHONPATH set.

**Fix Applied**:
```dockerfile
# Changed from:
CMD ["python", "-m", "uvicorn", "dashboard.server:app", "--host", "0.0.0.0", "--port", "3000"]

# To:
CMD ["uvicorn", "dashboard.server:app", "--host", "0.0.0.0", "--port", "3000"]
```

---

### Issue 6: Short Health Check Grace Period ❌ → ✅ FIXED
**Problem**: The health check started too early (5s) before the app was fully initialized.

**Fix Applied**:
```toml
# Increased grace_period and timeout in fly.toml
[[http_service.checks]]
  grace_period = "20s"  # Was 10s
  interval = "30s"
  method = "GET"
  timeout = "10s"       # Was 5s
  path = "/api/status"
```

```dockerfile
# Increased start_period in Dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3
```

---

## How to Deploy with Fixed Configuration

### Step 1: Ensure You're Using Latest Code

```bash
git pull origin claude/test-services-deploy-flyio-011CUqedCSXXrpbjCz7Ke7ax
```

### Step 2: Deploy to Fly.io

```bash
# If this is your first deployment
fly launch --no-deploy

# Set credentials (IMPORTANT!)
fly secrets set AUTH_USERNAME="your_admin_username"
fly secrets set AUTH_PASSWORD="your_secure_password"

# Deploy
fly deploy

# Monitor logs
fly logs -f
```

### Step 3: If Deployment Still Fails

Check logs for specific errors:
```bash
fly logs
```

Common issues and solutions:

#### Error: "App name already taken"
```bash
# Update app name in fly.toml, then redeploy
fly apps destroy becoin-ecosystem  # If you want to start fresh
# OR change the app name in fly.toml
```

#### Error: "Secrets not set"
```bash
# Verify secrets are set
fly secrets list

# Should show:
# NAME            DIGEST  CREATED AT
# AUTH_USERNAME   xxxxxx  1m ago
# AUTH_PASSWORD   xxxxxx  1m ago

# If missing, set them:
fly secrets set AUTH_USERNAME="admin" AUTH_PASSWORD="secure_password"
```

#### Error: "Health checks failing"
```bash
# SSH into the container to debug
fly ssh console

# Inside container, check if app is running
ps aux | grep uvicorn

# Test health endpoint manually
curl http://localhost:3000/api/status

# Check Python path
python -c "import sys; print(sys.path)"

# Test imports
python -c "from dashboard.server import app; print('OK')"

# Exit SSH
exit
```

#### Error: "Out of memory"
```bash
# Increase memory (already set to 512mb, but can go higher if needed)
fly scale memory 1024
```

---

## Verification Steps After Deployment

### 1. Check App Status
```bash
fly status
```

Expected output:
```
...
Machines
ID        STATE   HEALTH  ...
12345678  started passing ...
```

### 2. Check Health Checks
```bash
fly checks list
```

Expected output:
```
Health Checks
  NAME    STATUS  ...
  http    passing ...
```

### 3. Test API Endpoints
```bash
# Get your app URL
fly open

# Or test with curl (replace with your URL and credentials)
curl -u username:password https://becoin-ecosystem.fly.dev/api/status
```

Expected response:
```json
{
  "status": "operational",
  "service": "ceo-discovery-dashboard",
  "version": "1.0.0"
}
```

### 4. Test Authentication
```bash
# Without credentials (should fail with 401)
curl https://becoin-ecosystem.fly.dev/api/ceo/status

# With correct credentials (should succeed)
curl -u username:password https://becoin-ecosystem.fly.dev/api/ceo/status

# With wrong credentials (should fail with 401)
curl -u wrong:credentials https://becoin-ecosystem.fly.dev/api/ceo/status
```

---

## Optional: Enable Persistent Volume

If you want discovery session data to persist across deployments:

```bash
# 1. Create volume
fly volumes create becoin_data --size 1 --region iad

# 2. Uncomment mounts section in fly.toml
# [mounts]
#   source = "becoin_data"
#   destination = "/app/.claude-flow"

# 3. Redeploy
fly deploy
```

---

## Performance Tuning

### Scaling Instances
```bash
# Scale to 2 instances for redundancy
fly scale count 2

# Scale back to 1
fly scale count 1
```

### Scaling Memory
```bash
# If you see memory issues, increase to 1GB
fly scale memory 1024

# Or 2GB
fly scale memory 2048
```

### Scaling CPU
```bash
# Upgrade to 2x CPU
fly scale vm shared-cpu-2x

# Or dedicated CPU
fly scale vm dedicated-cpu-1x
```

---

## Monitoring and Debugging

### Real-time Logs
```bash
# Follow logs in real-time
fly logs -f

# Filter for errors
fly logs -f | grep ERROR

# Filter for authentication attempts
fly logs -f | grep "401\|Unauthorized"
```

### SSH Access
```bash
# SSH into running container
fly ssh console

# Run commands inside container
python -c "from dashboard.server import app; print('OK')"
uvicorn --help
env | grep AUTH
```

### Metrics Dashboard
```bash
# Open Fly.io dashboard in browser
fly dashboard
```

---

## Summary of Changes

| File | Change | Reason |
|------|--------|--------|
| `Dockerfile` | Added `PYTHONPATH=/app` | Fix module imports |
| `Dockerfile` | Removed `AS base` | Simplified build |
| `Dockerfile` | Added `curl` install | Health checks |
| `Dockerfile` | Changed CMD to direct `uvicorn` | Simplified command |
| `Dockerfile` | Increased health check start period to 40s | More time to start |
| `fly.toml` | Increased memory to 512mb | Prevent OOM |
| `fly.toml` | Added `PYTHONPATH=/app` | Fix module imports |
| `fly.toml` | Commented out `[mounts]` | Make volume optional |
| `fly.toml` | Increased grace_period to 20s | More time to start |
| `fly.toml` | Increased timeout to 10s | More reliable checks |

---

## Next Steps

1. ✅ Pull latest code
2. ✅ Verify fixes in files
3. ✅ Deploy: `fly deploy`
4. ✅ Monitor: `fly logs -f`
5. ✅ Test: Visit your app URL
6. ✅ Verify auth works

---

**All issues have been identified and fixed. The deployment should now work correctly!**
