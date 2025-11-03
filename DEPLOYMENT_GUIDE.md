# Free Deployment Guide for Event Planning Agent

## Option 1: Streamlit Community Cloud (Recommended - 100% Free)

### Prerequisites
- GitHub account
- Your code pushed to a GitHub repository

### Step-by-Step Deployment

1. **Prepare Your Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

2. **Deploy to Streamlit Cloud**
   - Go to https://share.streamlit.io
   - Click "Sign in with GitHub"
   - Click "New app"
   - Select your repository
   - Set main file path: `streamlit_gui/app.py`
   - Click "Deploy"

3. **Configure Secrets**
   In Streamlit Cloud dashboard, add these secrets:
   ```toml
   # .streamlit/secrets.toml format
   API_BASE_URL = "YOUR_BACKEND_API_URL"
   API_TIMEOUT = "30"
   APP_TITLE = "Event Planning Agent"
   APP_ICON = "🎉"
   ENVIRONMENT = "production"
   CACHE_TTL = "300"
   ENABLE_DEBUG = "false"
   ```

4. **Your app will be live at:**
   `https://YOUR_USERNAME-YOUR_REPO-streamlit-gui-app.streamlit.app`

### Limitations
- 1GB RAM
- Backend API needs separate hosting
- App sleeps after inactivity (wakes on visit)

---

## Option 2: Render (Free Tier - Full Stack)

### Deploy Backend + Frontend + Database

1. **Sign up at https://render.com**

2. **Deploy PostgreSQL Database**
   - Click "New +" → "PostgreSQL"
   - Name: `event-planning-db`
   - Free tier selected
   - Click "Create Database"
   - Save connection string

3. **Deploy Backend API**
   - Click "New +" → "Web Service"
   - Connect your GitHub repo
   - Name: `event-planning-api`
   - Root Directory: `event_planning_agent_v2`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py` (or your API start command)
   - Add environment variables (database connection, API keys)
   - Click "Create Web Service"

4. **Deploy Streamlit Frontend**
   - Click "New +" → "Web Service"
   - Connect your GitHub repo
   - Name: `event-planning-frontend`
   - Root Directory: `streamlit_gui`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run app.py --server.port=$PORT`
   - Add environment variable: `API_BASE_URL` = your backend URL
   - Click "Create Web Service"

### Limitations
- Services spin down after 15 min inactivity (cold start ~30s)
- 750 hours/month free (enough for 1 service 24/7)

---

## Option 3: Hugging Face Spaces (AI-Focused)

### Best for AI/ML Applications

1. **Create Account**
   - Go to https://huggingface.co
   - Sign up (free)

2. **Create New Space**
   - Click your profile → "New Space"
   - Name: `event-planning-agent`
   - License: Choose appropriate
   - Select SDK: **Streamlit**
   - Click "Create Space"

3. **Upload Your Code**
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/event-planning-agent
   cd event-planning-agent
   
   # Copy your streamlit_gui files here
   cp -r ../streamlit_gui/* .
   
   git add .
   git commit -m "Add event planning app"
   git push
   ```

4. **Configure Secrets**
   - Go to Space Settings → "Repository secrets"
   - Add your environment variables

5. **Your app will be live at:**
   `https://huggingface.co/spaces/YOUR_USERNAME/event-planning-agent`

### Limitations
- Backend needs separate hosting
- Limited compute on free tier

---

## Option 4: Railway (Developer-Friendly)

### $5 Free Credit Monthly

1. **Sign up at https://railway.app**

2. **Deploy from GitHub**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway auto-detects and deploys

3. **Configure Services**
   - Add PostgreSQL database (click "+ New")
   - Configure environment variables
   - Set start command for Streamlit: `streamlit run streamlit_gui/app.py`

4. **Your app gets a URL:**
   `https://YOUR_APP.up.railway.app`

### Limitations
- $5 credit = ~500 hours of usage
- Need to add credit card (not charged unless you exceed free tier)

---

## Option 5: PythonAnywhere (Python-Specific)

### Free Tier Available

1. **Sign up at https://www.pythonanywhere.com**

2. **Upload Code**
   - Use their web interface or Git
   - Install dependencies in virtual environment

3. **Configure Web App**
   - Go to "Web" tab
   - Add new web app
   - Choose manual configuration
   - Set up WSGI file for your app

### Limitations
- More manual setup required
- Limited CPU time on free tier
- Not ideal for Streamlit (better for Flask/Django)

---

## Recommended Setup for Complete Free Deployment

### Best Combination:

1. **Frontend (Streamlit)**: Streamlit Community Cloud
   - Free, unlimited, perfect for Streamlit
   - URL: `https://your-app.streamlit.app`

2. **Backend API**: Render Free Tier
   - Includes PostgreSQL database
   - Auto-deploy from GitHub
   - URL: `https://your-api.onrender.com`

3. **Database**: Render PostgreSQL (Free)
   - Included with Render
   - 1GB storage

### Total Cost: $0/month

---

## Environment Variables Needed

### For Streamlit Frontend:
```
API_BASE_URL=https://your-backend-api-url.onrender.com
API_TIMEOUT=30
APP_TITLE=Event Planning Agent
ENVIRONMENT=production
CACHE_TTL=300
```

### For Backend API:
```
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=your_database_host
DB_PORT=5432
OPENAI_API_KEY=your_api_key (if using OpenAI)
```

---

## Quick Start Commands

### Push to GitHub:
```bash
git init
git add .
git commit -m "Ready for deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### Test Locally Before Deploying:
```bash
cd streamlit_gui
pip install -r requirements.txt
streamlit run app.py
```

---

## Troubleshooting

### App Won't Start
- Check logs in deployment platform
- Verify all dependencies in requirements.txt
- Ensure environment variables are set

### Database Connection Issues
- Verify database URL format
- Check firewall/security settings
- Ensure database is running

### API Connection Failed
- Verify API_BASE_URL is correct
- Check CORS settings on backend
- Ensure backend is deployed and running

### Out of Memory
- Reduce cache size
- Optimize data loading
- Consider upgrading to paid tier

---

## Next Steps

1. Choose your deployment platform
2. Push code to GitHub
3. Follow platform-specific steps above
4. Configure environment variables
5. Test your deployed app
6. Share your URL!

## Support

For issues:
- Streamlit Cloud: https://discuss.streamlit.io
- Render: https://render.com/docs
- Hugging Face: https://discuss.huggingface.co
- Railway: https://railway.app/help
