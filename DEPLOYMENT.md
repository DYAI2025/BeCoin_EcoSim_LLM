# BeCoin EcoSim - Fly.io Deployment Guide

This guide walks you through deploying the BeCoin EcoSim dashboard to Fly.io with password protection.

## Prerequisites

1. **Install Fly CLI**:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Sign up / Log in to Fly.io**:
   ```bash
   fly auth signup  # or fly auth login
   ```

## Deployment Steps

### 1. Configure Your Application

The project is already configured with:
- `Dockerfile` - Multi-stage build optimized for Python 3.11
- `fly.toml` - Fly.io configuration with health checks and volume mounts
- `.dockerignore` - Optimized build context
- `.env.example` - Environment variable template

### 2. Create the Fly.io App

Initialize your app (replace `becoin-ecosystem` with your preferred name):

```bash
fly launch --no-deploy
```

This will:
- Create a new app on Fly.io
- Generate a unique URL for your app
- Configure the app based on `fly.toml`

**Note**: The app name in `fly.toml` can be customized. Update the `app` field if you want a different name.

### 3. Set Authentication Credentials (IMPORTANT!)

Set secure credentials to protect your dashboard:

```bash
fly secrets set AUTH_USERNAME="your_admin_username"
fly secrets set AUTH_PASSWORD="your_secure_password_here"
```

⚠️ **Security Best Practices**:
- Use a strong, unique password (16+ characters)
- Include uppercase, lowercase, numbers, and symbols
- Don't commit credentials to git
- Store credentials securely (use a password manager)

### 4. Create a Persistent Volume (Optional)

If you want to persist discovery session data across deployments:

```bash
fly volumes create becoin_data --size 1 --region iad
```

**Note**: The region (`iad` = US East) should match `primary_region` in `fly.toml`.

### 5. Deploy Your Application

```bash
fly deploy
```

This will:
- Build the Docker image
- Push to Fly.io registry
- Deploy to your configured region
- Run health checks
- Make your app available

### 6. Verify Deployment

Check your app status:

```bash
fly status
```

View logs:

```bash
fly logs
```

Open your app in browser:

```bash
fly open
```

### 7. Test Authentication

Visit your app URL and verify that:
1. The browser prompts for username/password
2. Correct credentials grant access to the dashboard
3. Incorrect credentials are rejected with 401 Unauthorized

Test the API endpoints:

```bash
# Replace with your app URL and credentials
curl -u username:password https://your-app.fly.dev/api/status
```

## Configuration

### Environment Variables

Set additional environment variables as secrets:

```bash
fly secrets set VARIABLE_NAME="value"
```

Available variables (see `.env.example`):
- `AUTH_USERNAME` - Username for HTTP Basic Auth (REQUIRED)
- `AUTH_PASSWORD` - Password for HTTP Basic Auth (REQUIRED)
- `ANTHROPIC_API_KEY` - API key for Claude integration (optional, for future use)

### Scaling

Scale your app:

```bash
# Scale to 2 instances
fly scale count 2

# Change VM size
fly scale vm shared-cpu-2x
```

### Resource Configuration

Current defaults (in `fly.toml`):
- **VM Size**: `shared-cpu-1x`
- **Memory**: 256MB
- **Region**: `iad` (US East - Virginia)
- **Min Machines**: 1

Adjust these in `fly.toml` before deployment or via CLI:

```bash
fly scale memory 512  # Increase to 512MB
```

## API Endpoints

Once deployed, your dashboard exposes:

### Public Endpoints (No Auth Required)
- `GET /` - Service information
- `GET /api/status` - Health check

### Protected Endpoints (Auth Required)
- `GET /api/ceo/status` - Current discovery session
- `GET /api/ceo/proposals?min_roi=0&limit=10` - Filtered proposals
- `GET /api/ceo/patterns?type=<type>` - Operational patterns
- `GET /api/ceo/pain-points` - Identified issues
- `GET /api/ceo/history?limit=10` - Historical sessions
- `WS /ws/ceo` - WebSocket for real-time updates

## Monitoring

### View Logs

```bash
# Real-time logs
fly logs

# Follow logs
fly logs -f
```

### Health Checks

The app includes a health check at `/api/status` that runs every 30 seconds.

View health check status:

```bash
fly checks list
```

### Monitoring Dashboard

Access Fly.io's monitoring dashboard:

```bash
fly dashboard
```

## Troubleshooting

### App Won't Start

1. Check logs: `fly logs`
2. Verify secrets are set: `fly secrets list`
3. Check build logs: `fly logs --deploy`

### Authentication Issues

If auth is not working:

```bash
# Verify secrets are set
fly secrets list

# Should show: AUTH_USERNAME, AUTH_PASSWORD

# Restart app to reload secrets
fly apps restart becoin-ecosystem
```

### Connection Issues

```bash
# Check app status
fly status

# Verify health checks
fly checks list

# SSH into the container for debugging
fly ssh console
```

### Out of Memory

If the app crashes due to memory:

```bash
# Increase memory allocation
fly scale memory 512
```

## Updating Your Deployment

After making code changes:

1. **Commit your changes** (optional but recommended):
   ```bash
   git add .
   git commit -m "Update dashboard"
   ```

2. **Deploy updated version**:
   ```bash
   fly deploy
   ```

3. **Monitor deployment**:
   ```bash
   fly logs -f
   ```

## Security Considerations

### Authentication

- ✅ HTTP Basic Auth is enabled on all CEO endpoints
- ✅ Credentials are stored as encrypted secrets
- ✅ Constant-time comparison prevents timing attacks
- ⚠️ WebSocket endpoint currently doesn't require auth (consider adding token-based auth)

### HTTPS

- ✅ Fly.io provides automatic HTTPS with TLS certificates
- ✅ `force_https = true` in `fly.toml` ensures all traffic is encrypted

### CORS

Current configuration allows all origins (`allow_origins=["*"]`). For production:

1. Edit `dashboard/server.py`
2. Replace `allow_origins=["*"]` with specific domains:
   ```python
   allow_origins=[
       "https://your-frontend.com",
       "https://dashboard.your-company.com"
   ]
   ```

3. Redeploy: `fly deploy`

### Recommendations

- [ ] Use strong, unique passwords
- [ ] Enable MFA on your Fly.io account
- [ ] Regularly rotate credentials
- [ ] Monitor logs for suspicious activity
- [ ] Keep dependencies updated
- [ ] Consider adding rate limiting for production use
- [ ] Add WebSocket authentication for production

## Cost Estimation

Fly.io pricing (as of 2024):

- **Free tier**: Includes resources for hobby projects
- **Shared CPU**: ~$3-5/month per instance
- **Volumes**: $0.15/GB per month

For this app:
- 1x shared-cpu-1x instance: ~$3/month
- 1GB volume: ~$0.15/month
- **Total**: ~$3-5/month

Check current pricing: https://fly.io/docs/about/pricing/

## Support

- **Fly.io Docs**: https://fly.io/docs/
- **Community Forum**: https://community.fly.io/
- **BeCoin EcoSim Issues**: [GitHub Issues](https://github.com/DYAI2025/BeCoin_EcoSim_LLM/issues)

## Quick Reference

```bash
# Common commands
fly launch              # Initialize app
fly deploy              # Deploy changes
fly open                # Open app in browser
fly logs                # View logs
fly ssh console         # SSH into container
fly secrets set KEY=VAL # Set environment variable
fly status              # Check app status
fly apps restart <app>  # Restart app
```

---

**Ready to deploy?** Follow steps 1-7 above to get your BeCoin EcoSim dashboard running on Fly.io!
