# Fly.io Deployment Troubleshooting Guide

Use this checklist to debug deployments of the BeCoin EcoSim dashboard on Fly.io.

## Common Issues

### 1) Authentication not enforced
- **Symptom**: Dashboard loads without asking for credentials.
- **Fix**: Set secrets and redeploy:
  ```bash
  fly secrets set AUTH_USERNAME="admin" AUTH_PASSWORD="strong_password"
  fly deploy
  ```

### 2) Health check failing
- **Symptom**: Fly reports failing checks or restarts the machine.
- **Fixes**:
  - Confirm the app is listening on port 3000: `fly ssh console` then
    `curl http://localhost:3000/api/status`.
  - Ensure dependencies are installed in the image (Dockerfile already installs
    `dashboard/requirements.txt`).
  - Wait for the container health check (30s interval, 40s start period) to pass.

### 3) Discovery data missing
- **Symptom**: CEO endpoints return empty data.
- **Fix**: Populate JSON files under `.claude-flow/discovery-sessions` or mount a
  Fly volume to `/app/.claude-flow` for persistence.

### 4) Chat history not persisted
- **Symptom**: Chat resets after restart.
- **Fix**: Mount a volume so `dashboard/chat_history.json` survives restarts or
  manage history externally.

### 5) Memory or CPU pressure
- **Symptom**: Slow responses or OOM kills.
- **Fix**: Increase resources (defaults are 4 shared vCPUs and 2048MB):
  ```bash
  fly scale vm shared-cpu-4x
  fly scale memory 4096
  ```

## Verification Steps

1. **Status**
   ```bash
   fly status
   fly checks list
   ```

2. **Logs**
   ```bash
   fly logs -f
   ```

3. **API smoke test**
   ```bash
   FLY_URL=$(fly info --json | jq -r .hostname)
   curl -u "$AUTH_USERNAME:$AUTH_PASSWORD" https://$FLY_URL/api/status
   curl -u "$AUTH_USERNAME:$AUTH_PASSWORD" https://$FLY_URL/api/chat/history
   ```

## When in Doubt
- Rebuild and redeploy: `fly deploy --remote-only`.
- SSH into the machine and verify imports: `python -c "from dashboard.server import app; print('ok')"`.
- Confirm `PYTHONPATH=/app` is set (defined in Dockerfile and `fly.toml`).
