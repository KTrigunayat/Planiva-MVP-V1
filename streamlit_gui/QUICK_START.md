# Quick Start Guide - Streamlit GUI

## Getting Started in 5 Minutes

### 1. Installation (1 minute)

```bash
cd streamlit_gui
pip install -r requirements.txt
```

### 2. Configuration (1 minute)

Create `.env` file:
```bash
cp .env.template .env
```

Edit `.env`:
```
API_BASE_URL=http://localhost:8000
API_TIMEOUT=30
API_RETRY_ATTEMPTS=3
ENVIRONMENT=development
```

### 3. Start Application (1 minute)

```bash
streamlit run app.py
```

Access at: http://localhost:8501

### 4. Quick Tour (2 minutes)

#### Create an Event Plan
1. Click **"➕ Create Plan"**
2. Fill in event details
3. Submit to start planning

#### View Tasks
1. Navigate to **"📋 Tasks"** → **"Task List"**
2. See all tasks with dependencies
3. Mark tasks complete with checkboxes
4. View **"Timeline"** for Gantt chart
5. Check **"Conflicts"** for issues

#### Manage Communications
1. Go to **"💬 Communications"** → **"Preferences"**
2. Set client communication preferences
3. View **"History"** for all messages
4. Check **"Analytics"** for performance metrics

---

## Key Features at a Glance

### Task Management
- **Task List**: View and manage all tasks
- **Timeline**: Visual Gantt chart
- **Conflicts**: Resolve scheduling issues
- **Vendors**: Track vendor assignments

### CRM & Communications
- **Preferences**: Set communication channels
- **History**: Track all messages
- **Analytics**: View performance metrics

---

## Common Tasks

### Mark a Task Complete
1. Go to Task List
2. Click checkbox next to task
3. Status updates automatically

### Export Communication History
1. Go to Communication History
2. Apply filters if needed
3. Click "Export to CSV"

### Resolve a Conflict
1. Go to Conflicts page
2. Review conflict details
3. Click "Apply Resolution"

### View Analytics
1. Go to Analytics dashboard
2. Select date range
3. View metrics and charts

---

## Troubleshooting

### Can't Connect to API
- Check backend is running: `curl http://localhost:8000/health`
- Verify `API_BASE_URL` in `.env`
- Check network connectivity

### Page Not Loading
- Refresh browser (F5)
- Clear cache: `streamlit cache clear`
- Check browser console for errors

### Tests Failing
```bash
# Run tests
pytest streamlit_gui/tests/ -v

# Run specific test
pytest streamlit_gui/tests/test_crm_pages.py -v
```

---

## Next Steps

1. **Read Full Documentation**
   - `README.md` - Complete feature overview
   - `docs/TASK_MANAGEMENT_GUIDE.md` - Task features
   - `docs/CRM_GUIDE.md` - CRM features

2. **Explore Features**
   - Try all navigation options
   - Test filtering and sorting
   - Export data to CSV

3. **Deploy to Production**
   - Follow `docs/DEPLOYMENT_CHECKLIST.md`
   - Configure production environment
   - Monitor logs and performance

---

## Support

- **Documentation**: Check `docs/` folder
- **Troubleshooting**: See `docs/TROUBLESHOOTING.md`
- **Issues**: Contact development team

---

**Ready to go!** 🚀
