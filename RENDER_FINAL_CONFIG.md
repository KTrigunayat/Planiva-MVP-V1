# Final Render Configuration - COPY THESE EXACT SETTINGS

## In Your Render Dashboard

### Service Settings:

1. **Root Directory**: Leave **EMPTY** (or just put `.`)

2. **Build Command**:
   ```
   pip install -r event_planning_agent_v2/requirements.txt
   ```

3. **Start Command**:
   ```
   uvicorn event_planning_agent_v2.wsgi:app --host 0.0.0.0 --port $PORT
   ```

### Environment Variables:

Add these in the "Environment" tab:

```
ENVIRONMENT=production
API_HOST=0.0.0.0
LOG_LEVEL=INFO
CORS_ORIGINS=*
SECRET_KEY=EPXzZG-CkaqttfBwPEOX4TmiP3nxDo6VZ3A_l8TZASI
JWT_SECRET=EPXzZG-CkaqttfBwPEOX4TmiP3nxDo6VZ3A_l8TZASI
DATABASE_URL=postgresql://user:pass@host:5432/db
OLLAMA_BASE_URL=http://localhost:11434
```

### Important Notes:

- **Root Directory must be EMPTY** - This is critical!
- The build command installs from the subdirectory
- The start command runs from repo root but imports the package correctly
- All imports in the code now use `event_planning_agent_v2.` prefix

## After Updating Settings:

1. Click "Save Changes"
2. Click "Manual Deploy" → "Clear build cache & deploy"
3. Wait for deployment (5-10 minutes)

## What Should Happen:

✅ Build successful
✅ Dependencies installed
✅ App starts without import errors
✅ Health check at: `https://your-app.onrender.com/health`

## If It Still Fails:

Your app is very heavy (torch, transformers, crewai). The free tier might not have enough:
- Memory (512MB free tier)
- Build time (limited)
- CPU resources

### Options:
1. **Upgrade to paid tier**: $7/month for more resources
2. **Remove heavy dependencies**: Use external AI APIs instead
3. **Try Railway**: Better free tier ($5 credit)
4. **Deploy frontend only**: Use Streamlit Cloud for frontend, skip backend for now

Let me know what happens!
