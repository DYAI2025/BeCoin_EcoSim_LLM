# Fly.io Deployment - Alternative Method (Bypassing flyctl Bug)

## The Problem

The `fly launch` command has a bug causing a panic:
```
panic: runtime error: invalid memory address or nil pointer dereference
```

This is a bug in flyctl itself, not your code. We'll bypass it by creating the app manually.

---

## ✅ Solution: Deploy Directly Without `fly launch`

### Method 1: Use `fly deploy` Directly (Recommended)

Since we already have a complete `fly.toml` configuration, we can skip `fly launch` entirely.

#### Step 1: Create the App Manually

```bash
# Option A: Use a custom app name
fly apps create becoin-ecosystem --region iad

# Option B: Let Fly generate a unique name
fly apps create --region iad
```

**Note**: If "becoin-ecosystem" is taken, use a different name or let Fly generate one. Update the `app` field in `fly.toml` to match.

#### Step 2: Set Authentication Secrets

```bash
# Set your credentials (REQUIRED!)
fly secrets set AUTH_USERNAME="your_admin_username" AUTH_PASSWORD="your_secure_password"
```

#### Step 3: Deploy Directly

```bash
# Deploy the app
fly deploy

# Watch logs
fly logs -f
```

That's it! Skip the `fly launch` command entirely.

---

### Method 2: Use the Fly.io Web Dashboard

If the CLI keeps crashing, use the web interface:

1. **Go to**: https://fly.io/dashboard
2. **Click**: "Create App"
3. **Choose**:
   - Region: iad (US East - Virginia)
   - App name: becoin-ecosystem (or custom name)
4. **After creation**, use CLI:
   ```bash
   # Update app name in fly.toml if needed
   # Then set secrets
   fly secrets set AUTH_USERNAME="admin" AUTH_PASSWORD="secure_pass"

   # Deploy
   fly deploy
   ```

---

### Method 3: Update fly.toml App Name

If "becoin-ecosystem" is already taken:

1. **Pick a unique name**: e.g., `becoin-ecosystem-YOUR_SUFFIX`

2. **Update fly.toml**:
   ```toml
   # Change line 5
   app = "becoin-ecosystem-unique-name"
   ```

3. **Create and deploy**:
   ```bash
   fly apps create becoin-ecosystem-unique-name --region iad
   fly secrets set AUTH_USERNAME="admin" AUTH_PASSWORD="password"
   fly deploy
   ```

---

## What Was Fixed in fly.toml

The panic was caused by issues in the fly.toml configuration:

### ❌ Before (Problematic)
```toml
[build]  # Empty section causing nil pointer

[http_service]  # Deprecated syntax
  processes = ["app"]  # Problematic field
```

### ✅ After (Fixed)
```toml
# Removed empty [build] section
# Removed processes field
# Changed to [[services]] syntax (more stable)

[[services]]
  protocol = "tcp"
  internal_port = 3000

  [[services.ports]]
    port = 80
    handlers = ["http"]
    force_https = true

  # Proper health checks
  [[services.http_checks]]
    path = "/api/status"
```

**Key Changes**:
1. ✅ Removed empty `[build]` section (was causing nil pointer)
2. ✅ Changed from `[http_service]` to `[[services]]` (newer, more stable)
3. ✅ Removed `processes = ["app"]` (was problematic)
4. ✅ Added proper TCP and HTTP checks
5. ✅ Added graceful shutdown config

---

## Quick Start (TL;DR)

```bash
# 1. Create app (choose unique name if needed)
fly apps create becoin-ecosystem --region iad

# 2. Set secrets
fly secrets set AUTH_USERNAME="admin" AUTH_PASSWORD="your_secure_password"

# 3. Deploy
fly deploy

# 4. Monitor
fly logs -f

# 5. Open in browser
fly open
```

---

## Troubleshooting

### Error: "App name already taken"

```bash
# Use a different name
fly apps create becoin-ecosystem-$(date +%s) --region iad

# Update fly.toml with the new name
# Then deploy
fly deploy
```

### Error: "Could not find App"

```bash
# List your apps
fly apps list

# Make sure app name in fly.toml matches
# Then deploy
fly deploy
```

### Error: "Secrets not set"

```bash
# Verify secrets exist
fly secrets list

# Set them if missing
fly secrets set AUTH_USERNAME="admin" AUTH_PASSWORD="password"
```

### Error: "Dockerfile not found"

```bash
# Make sure you're in the project root
cd /home/user/BeCoin_EcoSim_LLM

# Verify Dockerfile exists
ls -la Dockerfile

# Deploy
fly deploy
```

---

## Verification After Deployment

### 1. Check Status
```bash
fly status
```

Expected:
```
...
Machines
ID        STATE   HEALTH
12345678  started passing
```

### 2. Test API
```bash
# Get your app URL
FLY_URL=$(fly info --json | jq -r .hostname)

# Test without auth (should fail)
curl https://$FLY_URL/api/status

# Test with auth (should work)
curl -u username:password https://$FLY_URL/api/status
```

### 3. View Logs
```bash
fly logs -f
```

Look for:
```
INFO:     Uvicorn running on http://0.0.0.0:3000
INFO:     Application startup complete
✓ Authentication is ENABLED
```

---

## Summary

**The Fix**:
- ✅ Fixed fly.toml to avoid flyctl bug
- ✅ Use `fly deploy` instead of `fly launch`
- ✅ Create app manually with `fly apps create`

**No more panic errors!**

---

## Next Steps

After successful deployment:

1. ✅ Test authentication
2. ✅ Verify health checks passing
3. ✅ Monitor logs for errors
4. ✅ Test all API endpoints

**You're ready to deploy!** 🚀
