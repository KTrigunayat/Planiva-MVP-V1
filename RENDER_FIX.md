# Fix for Render Deployment Error

## The Problem
Error: `ModuleNotFoundError: No module named 'event_planning_agent_v2'`

This happens because when you set Root Directory to `event_planning_agent_v2` in Render, it's already inside that folder, so it can't import `event_planning_agent_v2.main`.

## The Solution

I've fixed the code. Now update your Render configuration:

### In Render Dashboard:

1. **Go to your service settings**
2. **Change these settings:**
   - **Root Directory**: `event_planning_agent_v2`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Save and redeploy**

### Alternative: Deploy from Root

If that doesn't work, try this:

1. **Root Directory**: Leave EMPTY (deploy from repo root)
2. **Build Command**: `cd event_planning_agent_v2 && pip install -r requirements.txt`
3. **Start Command**: `cd event_planning_agent_v2 && uvicorn main:app --host 0.0.0.0 --port $PORT`

## Push the Fixed Code

```bash
git add .
git commit -m "Fix module import for Render deployment"
git push origin master
```

Then in Render, click "Manual Deploy" → "Clear build cache & deploy"

## What I Changed

1. **main.py**: Added fallback imports to handle both scenarios
2. **render_start.sh**: Created startup script with proper paths
3. **Procfile**: Updated command to work from correct directory
4. **render.yaml**: Updated configuration

The app should now deploy successfully!
