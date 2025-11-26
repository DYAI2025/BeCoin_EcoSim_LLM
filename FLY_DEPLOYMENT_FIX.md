# Fly.io Deployment - Quick Path (Skip `fly launch`)

If `fly launch` crashes or you already trust the existing `fly.toml`, deploy
straight from the current configuration.

## Direct Deploy

1. **Create the app (optional if it already exists)**
   ```bash
   fly apps create becoin-ecosim-llm-dqfelw --region fra
   ```

2. **Set authentication secrets**
   ```bash
   fly secrets set AUTH_USERNAME="admin" AUTH_PASSWORD="strong_password"
   ```

3. **Deploy using the existing config**
   ```bash
   fly deploy
   fly logs -f
   ```

## What `fly.toml` Provides Today
- `[http_service]` on port 3000 with auto start/stop (`min_machines_running = 0`).
- Shared CPU with 4 vCPUs and 2048MB RAM.
- Health check served by `/api/status` from the Dockerfile.

## Verify After Deployment
```bash
fly status
fly checks list
FLY_URL=$(fly info --json | jq -r .hostname)
curl -u "$AUTH_USERNAME:$AUTH_PASSWORD" https://$FLY_URL/api/status
```

If a custom app name is required, update the `app` field in `fly.toml` before
running `fly deploy`.
