# Backend API Deployment Guide

Your Streamlit frontend needs a backend API to work. Here's how to deploy it for free.

## Problem
Your app is too heavy to run locally, so you need to deploy the backend API to the cloud first.

## Solution: Deploy Backend to Render (Free)

### Step 1: Prepare for Deployment

Your backend API is in the `event_planning_agent_v2/` folder and runs on FastAPI.

### Step 2: Deploy to Render

1. **Go to Render**: https://render.com
2. **Sign up** with GitHub
3. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repo: `KTrigunayat/Planiva-MVP-V1`
   - Name: `planiva-api`
   - Root Directory: `event_planning_agent_v2`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn event_planning_agent_v2.main:app --host 0.0.0.0 --port $PORT`
   - Plan: **Free**

4. **Add Environment Variables** (in Render dashboard):
   ```
   API_HOST=0.0.0.0
   API_PORT=8000
   LOG_LEVEL=INFO
   ENVIRONMENT=production
   CORS_ORIGINS=["*"]
   DATABASE_URL=<your-database-url>
   OLLAMA_BASE_URL=<ollama-service-url-or-skip>
   SECRET_KEY=<generate-random-secret>
   ```

5. **Click "Create Web Service"**

6. **Wait for deployment** (~5-10 minutes)

7. **Your API will be live at**: `https://planiva-api.onrender.com`

### Step 3: Test Your Backend

Once deployed, test it:
```bash
curl https://planiva-api.onrender.com/health
```

Should return:
```json
{"status": "healthy", "version": "2.0.0"}
```

### Step 4: Use Backend URL in Streamlit

Now deploy your Streamlit frontend with this backend URL:

**In Streamlit Cloud secrets:**
```toml
API_BASE_URL = "https://planiva-api.onrender.com"
API_TIMEOUT = "30"
APP_TITLE = "Planiva - Event Planning Agent"
APP_ICON = "🎉"
ENVIRONMENT = "production"
```

---

## Alternative: Railway (Better Resources)

If Render's free tier is too limited, try Railway:

1. **Go to Railway**: https://railway.app
2. **Sign up** with GitHub
3. **New Project** → "Deploy from GitHub repo"
4. Select `KTrigunayat/Planiva-MVP-V1`
5. Railway auto-detects Python and deploys
6. Add environment variables
7. Get URL: `https://planiva-api.up.railway.app`

**Pros**: $5 free credit monthly, better resources
**Cons**: Need credit card (won't charge unless you exceed free tier)

---

## Alternative: Google Cloud Run (Best for Heavy Apps)

For heavy AI/ML applications:

1. **Install Google Cloud CLI**
2. **Build Docker image**:
   ```bash
   cd event_planning_agent_v2
   docker build -t planiva-api .
   ```
3. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy planiva-api --source .
   ```
4. Free tier: 2M requests/month, 360,000 GB-seconds

---

## Handling Heavy Dependencies

Your app has heavy dependencies (torch, transformers, crewai). Here's how to optimize:

### Option 1: Use Lighter Models
Edit `requirements.txt` to use CPU-only versions:
```
torch>=2.1.0  # Remove this or use torch-cpu
transformers>=4.35.0  # Keep but use smaller models
```

### Option 2: Use External AI Services
Instead of running models locally, use APIs:
- OpenAI API (paid but cheap)
- Hugging Face Inference API (free tier)
- Replicate (pay-per-use)

Update your `.env`:
```
OPENAI_API_KEY=your-key
USE_EXTERNAL_LLM=true
```

### Option 3: Deploy with Docker on Better Platform
Use platforms with more resources:
- **Fly.io**: Free tier with 256MB RAM
- **Google Cloud Run**: Up to 4GB RAM on free tier
- **AWS Lambda**: 10GB RAM (pay-per-use)

---

## Quick Start Commands

### Push changes to GitHub:
```bash
git add .
git commit -m "Add backend deployment config"
git push origin master
```

### Test locally (if you can):
```bash
cd event_planning_agent_v2
pip install -r requirements.txt
uvicorn event_planning_agent_v2.main:app --reload
```

Then visit: http://localhost:8000/docs

---

## Troubleshooting

### Build Fails on Render
**Issue**: Out of memory during build
**Solution**: 
- Remove heavy dependencies (torch, transformers)
- Use external AI APIs instead
- Try Railway or Google Cloud Run

### App Crashes After Deploy
**Issue**: Not enough RAM
**Solution**:
- Upgrade to paid tier ($7/month on Render)
- Use Railway ($5 credit = ~100 hours)
- Optimize code to use less memory

### Database Connection Fails
**Issue**: No database configured
**Solution**:
- Add PostgreSQL on Render (free tier)
- Or use Supabase (free PostgreSQL)
- Update DATABASE_URL in environment variables

### CORS Errors
**Issue**: Frontend can't connect to backend
**Solution**:
Add to environment variables:
```
CORS_ORIGINS=["*"]
```

Or specific domains:
```
CORS_ORIGINS=["https://your-streamlit-app.streamlit.app"]
```

---

## Summary

1. **Deploy Backend First**: Render or Railway
2. **Get Backend URL**: `https://planiva-api.onrender.com`
3. **Deploy Frontend**: Streamlit Cloud with backend URL
4. **Test**: Visit your Streamlit app and verify it connects

Your backend URL will be something like:
- Render: `https://planiva-api.onrender.com`
- Railway: `https://planiva-api.up.railway.app`
- Cloud Run: `https://planiva-api-xxx.run.app`

Use this URL as `API_BASE_URL` in your Streamlit deployment!
