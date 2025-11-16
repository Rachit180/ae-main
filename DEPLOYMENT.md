# Render Deployment Guide - Web Service

## Prerequisites
- GitHub account
- Render account (sign up at https://render.com)
- Mailgun account with verified domain

## Step-by-Step Deployment Instructions

### Step 1: Prepare Your Repository
1. Initialize git (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Email sender web service"
   ```

2. Create a GitHub repository and push:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Render

#### Option A: Using render.yaml (Recommended)
1. Go to https://dashboard.render.com
2. Click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml`
5. Click "Apply" to create the web service

#### Option B: Manual Setup
1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `email-sender-api` (or any name you prefer)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free tier works fine

### Step 3: Set Environment Variables
In your Render service dashboard, go to "Environment" tab and add:

**Required:**
- `MAILGUN_SMTP_LOGIN` = `postmaster@your-domain.mailgun.org`
- `MAILGUN_SMTP_PASSWORD` = `your-mailgun-smtp-password`

**Optional (but recommended for security):**
- `API_KEY` = `your-secret-api-key` (protects your endpoints)
- `SENDER_ADDRESS` = `your-email@example.com` (defaults to MAILGUN_SMTP_LOGIN)
- `RESUME_FILE` = `AKASHSINGH_RESUME_V9.pdf` (default)
- `MAILGUN_SMTP_HOST` = `smtp.mailgun.org` (default)
- `MAILGUN_SMTP_PORT` = `587` (default)

### Step 4: Deploy
1. Click "Save Changes"
2. Render will automatically deploy
3. Your service will be available at: `https://your-service-name.onrender.com`

### Step 5: Use the API

#### Endpoints:
- **GET /** - Service information
- **GET /health** - Health check
- **POST /send** - Trigger email sending
- **GET /status** - Check sending status

#### Example Usage:

**Trigger email sending:**
```bash
# Without API key (if not set)
curl -X POST https://your-service-name.onrender.com/send

# With API key (if configured)
curl -X POST https://your-service-name.onrender.com/send \
  -H "X-API-Key: your-api-key"
```

**Check status:**
```bash
curl https://your-service-name.onrender.com/status?api_key=your-api-key
```

**Health check:**
```bash
curl https://your-service-name.onrender.com/health
```

## Important Notes

1. **Web Service**: The service runs continuously and can be triggered via HTTP requests

2. **API Security**: Set `API_KEY` environment variable to protect your endpoints. Use it in requests:
   - Header: `X-API-Key: your-key`
   - Query param: `?api_key=your-key`

3. **Resume File**: Make sure `AKASHSINGH_RESUME_V9.pdf` is committed to your repository

4. **Recipients**: Update the `recipients` dictionary in `app.py` before deploying

5. **Email Delays**: The script waits 10-12 minutes between emails (runs in background)

6. **Free Tier**: Render free tier spins down after 15 minutes of inactivity. First request may be slow.

7. **Background Processing**: Email sending runs in a background thread, so the API responds immediately

## Troubleshooting

- **Service not starting**: Check build logs for pip install errors
- **Connection failed**: Verify Mailgun credentials in environment variables
- **Domain not verified**: Complete DNS verification in Mailgun dashboard
- **Resume not found**: Ensure PDF file is committed to git
- **401 Unauthorized**: Set and use API_KEY if configured

