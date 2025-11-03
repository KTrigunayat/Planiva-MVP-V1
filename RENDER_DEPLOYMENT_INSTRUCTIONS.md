# Render Deployment Instructions - UPDATED

## The Problem
Your app has complex relative imports that break when deployed from a subdirectory.

## The Solution
Deploy from the **repository root** (not from `event_planning_agent_v2` subdirectory).

## Update Your Render Configuration

### Go to your Render service dashboard and update these settings:

1. **Root Directory**: Leave **EMPTY** (or set to `.`)
   - This deploys from the repo root

2. **Build Command**:
   ```
   pip install -r event_planning_agent_v2/requirements.txt
   ```

3. **Start Command**:
   ```
   uvicorn event_planning_agent_v2.wsgi:app --host 0.0.0.0 --port $PORT
   ```

4. **Environment Variables** (Add these in Render dashboard):
   ```
   ENVIRONMENT=production
   API_HOST=0.0.0.0
   API_PORT=8000
   LOG_LEVEL=INFO
   CORS_ORIGINS=*
   DATABASE_URL=postgresql://user:pass@host:5432/db
   OLLAMA_BASE_URL=http://localhost:11434
   SECRET_KEY=your-secret-key-change-this
   ```

5. Click **"Save Changes"**

6. Click **"Manual Deploy"** → **"Clear build cache & deploy"**

## What I Changed

Created `event_planning_agent_v2/wsgi.py` that:
- Adds the parent directory to Python path
- Imports the app correctly
- Works with Render's deployment structure

## Alternative: Simplify for Free Tier

Your app is very heavy (torch, transformers, crewai). If deployment keeps failing due to resource limits, you have two options:

### Option A: Remove Heavy Dependencies (Recommended for Free Tier)

Create a lightweight version:

1. Remove from `requirements.txt`:
   - `torch>=2.1.0`
   - `transformers>=4.35.0`
   - Heavy AI libraries

2. Use external APIs instead:
   - OpenAI API
   - Hugging Face Inference API
   - Replicate

### Option B: Upgrade to Paid Tier

- **Render**: $7/month for 512MB RAM
- **Railway**: $5 credit/month (better resources)
- **Google Cloud Run**: Pay-per-use (generous free tier)

## Testing Locally

Before deploying, test the wsgi entry point:

```bash
# From repo root
uvicorn event_planning_agent_v2.wsgi:app --reload
```

Visit: http://localhost:8000/health

Should return: `{"status": "healthy", "version": "2.0.0"}`

## If It Still Fails

The free tier might not have enough resources for your heavy app. Consider:

1. **Deploy just the Streamlit frontend** to Streamlit Cloud (free)
2. **Run backend locally** or on a more powerful platform
3. **Simplify the app** by removing AI models and using APIs

Let me know what happens!
