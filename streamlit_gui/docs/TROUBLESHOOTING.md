# Troubleshooting Guide

This guide helps you resolve common issues with the Event Planning Agent v2 Streamlit GUI.

## Table of Contents
1. [Connection Issues](#connection-issues)
2. [Performance Issues](#performance-issues)
3. [Data Loading Issues](#data-loading-issues)
4. [Form and Validation Issues](#form-and-validation-issues)
5. [Task Management Issues](#task-management-issues)
6. [CRM and Communication Issues](#crm-and-communication-issues)
7. [Export and Download Issues](#export-and-download-issues)
8. [Display and UI Issues](#display-and-ui-issues)

## Connection Issues

### API Server Not Responding

**Symptoms:**
- "API server error" message
- "Connection failed" errors
- Health indicator shows red/offline

**Solutions:**

1. **Check if backend is running:**
   ```bash
   curl http://localhost:8000/health
   ```
   Expected response: `{"status": "healthy"}`

2. **Verify API_BASE_URL in .env:**
   ```
   API_BASE_URL=http://localhost:8000
   ```

3. **Check network connectivity:**
   - Ensure no firewall blocking the connection
   - Verify the backend port is accessible
   - Try accessing the API URL in a browser

4. **Review backend logs:**
   - Check for errors in the backend service
   - Look for port conflicts
   - Verify all backend services are running

5. **Restart services:**
   ```bash
   # Restart backend
   # Restart Streamlit GUI
   streamlit run app.py
   ```

### Intermittent Connection Drops

**Symptoms:**
- Connection works sometimes but fails randomly
- Timeout errors
- Slow response times

**Solutions:**

1. **Increase timeout in .env:**
   ```
   API_TIMEOUT=60
   ```

2. **Check network stability:**
   - Test with ping to backend server
   - Check for network congestion
   - Verify DNS resolution

3. **Enable retry mechanism:**
   ```
   API_RETRY_ATTEMPTS=5
   ```

4. **Monitor backend performance:**
   - Check CPU and memory usage
   - Look for slow database queries
   - Review API response times

### CORS Errors

**Symptoms:**
- Browser console shows CORS errors
- API calls fail with CORS policy messages

**Solutions:**

1. **Configure backend CORS settings:**
   - Add Streamlit URL to allowed origins
   - Enable credentials if needed
   - Check CORS middleware configuration

2. **Use proxy if needed:**
   - Configure reverse proxy
   - Update API_BASE_URL to use proxy

## Performance Issues

### Slow Page Loading

**Symptoms:**
- Pages take long time to load
- Spinner shows for extended periods
- UI feels sluggish

**Solutions:**

1. **Check caching configuration:**
   - Verify @st.cache_data decorators are in place
   - Clear cache if stale: `streamlit cache clear`

2. **Optimize data loading:**
   - Use pagination for large lists
   - Implement lazy loading
   - Reduce polling frequency

3. **Monitor API performance:**
   - Check backend response times
   - Optimize database queries
   - Add indexes if needed

4. **Browser optimization:**
   - Clear browser cache
   - Disable unnecessary browser extensions
   - Use modern browser version

### High Memory Usage

**Symptoms:**
- Browser becomes slow
- System memory usage high
- Page crashes or freezes

**Solutions:**

1. **Limit data in session state:**
   - Clear old data regularly
   - Use pagination instead of loading all data
   - Implement data cleanup

2. **Optimize caching:**
   - Set appropriate TTL for cached data
   - Clear unused cache entries
   - Reduce cache size limits

3. **Restart application:**
   - Close and reopen browser tab
   - Restart Streamlit server
   - Clear all caches

### Charts Not Rendering Smoothly

**Symptoms:**
- Plotly charts lag or stutter
- Timeline visualization is slow
- Charts don't update properly

**Solutions:**

1. **Reduce data points:**
   - Sample large datasets
   - Aggregate data for overview charts
   - Use data decimation

2. **Optimize chart configuration:**
   - Disable animations for large datasets
   - Reduce chart complexity
   - Use simpler chart types

3. **Update Plotly:**
   ```bash
   pip install --upgrade plotly
   ```

## Data Loading Issues

### Tasks Not Loading

**Symptoms:**
- Task list shows empty
- "No tasks found" message
- Loading spinner never completes

**Solutions:**

1. **Verify plan exists:**
   - Check that event plan was created
   - Confirm plan ID is correct
   - Verify plan status is complete

2. **Check API endpoint:**
   - Test endpoint directly: `GET /api/task-management/extended-task-list`
   - Verify authentication if required
   - Check for API errors in network tab

3. **Review backend logs:**
   - Look for task generation errors
   - Check database connectivity
   - Verify task data exists

4. **Refresh the page:**
   - Use browser refresh (F5)
   - Clear session state
   - Try different browser

### Communication History Empty

**Symptoms:**
- No communications shown
- History page is blank
- "No communications found" message

**Solutions:**

1. **Verify client ID:**
   - Ensure correct client ID is entered
   - Check for typos
   - Try different client ID

2. **Check date range:**
   - Expand date range filter
   - Remove date filters
   - Verify communications exist in period

3. **Test API endpoint:**
   - `GET /api/crm/communications?client_id=xxx`
   - Check response data
   - Verify authentication

4. **Check backend:**
   - Verify CRM service is running
   - Check database for communication records
   - Review backend logs

### Analytics Not Displaying

**Symptoms:**
- Analytics page shows no data
- Charts are empty
- Metrics show zero

**Solutions:**

1. **Verify data exists:**
   - Check communication history has data
   - Ensure date range includes communications
   - Verify analytics calculation is working

2. **Check date range:**
   - Select wider date range
   - Remove date filters
   - Try "All Time" option

3. **Test API:**
   - `GET /api/crm/analytics`
   - Verify response structure
   - Check for calculation errors

## Form and Validation Issues

### Form Won't Submit

**Symptoms:**
- Submit button doesn't work
- Form shows validation errors
- No response after clicking submit

**Solutions:**

1. **Check required fields:**
   - Ensure all required fields are filled
   - Look for red error messages
   - Verify field formats

2. **Validate input formats:**
   - Email: valid email format
   - Phone: correct phone format
   - Date: future date for events
   - Budget: positive number

3. **Check browser console:**
   - Look for JavaScript errors
   - Check network tab for failed requests
   - Verify form data is being sent

4. **Try different browser:**
   - Test in Chrome, Firefox, or Edge
   - Disable browser extensions
   - Clear browser cache

### Validation Errors Persist

**Symptoms:**
- Error messages don't clear
- Valid input still shows errors
- Can't proceed despite correct data

**Solutions:**

1. **Refresh the page:**
   - Clear form and start over
   - Use browser refresh
   - Clear session state

2. **Check input format:**
   - Review format requirements
   - Copy-paste might add hidden characters
   - Type input manually

3. **Update validation rules:**
   - Check if validation is too strict
   - Review backend validation
   - Verify field requirements

## Task Management Issues

### Timeline Not Displaying

**Symptoms:**
- Gantt chart is blank
- Timeline shows error
- No tasks visible on timeline

**Solutions:**

1. **Verify task data:**
   - Ensure tasks have start and end times
   - Check that timeline data is available
   - Verify date formats are correct

2. **Adjust zoom level:**
   - Try different zoom settings
   - Change time scale (day/week/month)
   - Reset zoom to default

3. **Check date range:**
   - Ensure date range includes tasks
   - Expand date range
   - Remove date filters

4. **Clear cache:**
   ```bash
   streamlit cache clear
   ```

### Conflicts Not Resolving

**Symptoms:**
- Applied resolution doesn't work
- Conflicts reappear
- Resolution fails with error

**Solutions:**

1. **Verify resolution was applied:**
   - Check API response
   - Refresh conflicts page
   - Verify task updates

2. **Check for new conflicts:**
   - Resolution might create new conflicts
   - Review all affected tasks
   - Check dependency chain

3. **Manual resolution:**
   - Update tasks directly in task list
   - Adjust timelines manually
   - Contact vendors for schedule changes

4. **Backend issues:**
   - Check backend logs
   - Verify conflict resolution logic
   - Test API endpoint directly

### Task Status Not Updating

**Symptoms:**
- Checkbox doesn't update status
- Status changes don't save
- Tasks revert to previous status

**Solutions:**

1. **Check API call:**
   - Verify update endpoint is working
   - Check network tab for errors
   - Review API response

2. **Refresh page:**
   - Reload to get latest data
   - Clear cache
   - Check if update persisted

3. **Check permissions:**
   - Verify user has update permissions
   - Check authentication
   - Review access controls

## CRM and Communication Issues

### Preferences Not Saving

**Symptoms:**
- Save button doesn't work
- Preferences revert after save
- Error message on save

**Solutions:**

1. **Verify all fields:**
   - Check required fields are filled
   - Ensure valid timezone selected
   - Verify quiet hours format

2. **Check API:**
   - Test POST /api/crm/preferences
   - Verify request payload
   - Check response for errors

3. **Review validation:**
   - Ensure quiet hours are valid
   - Check channel selections
   - Verify client ID format

### Real-Time Updates Not Working

**Symptoms:**
- Communication status doesn't update
- Must manually refresh
- Polling not working

**Solutions:**

1. **Check polling configuration:**
   - Verify polling is enabled
   - Check polling interval
   - Review browser console for errors

2. **Network issues:**
   - Check connection stability
   - Verify API is responding
   - Test manual refresh

3. **Disable ad blockers:**
   - Some ad blockers interfere with polling
   - Whitelist the application
   - Try different browser

### Email Tracking Not Working

**Symptoms:**
- Opens not recorded
- Clicks not tracked
- Engagement metrics missing

**Solutions:**

1. **Check tracking configuration:**
   - Verify tracking is enabled in backend
   - Ensure tracking pixels are included
   - Check link tracking setup

2. **Email client limitations:**
   - Some clients block tracking pixels
   - Privacy settings may prevent tracking
   - Not all clients support tracking

3. **Review backend logs:**
   - Check for tracking webhook errors
   - Verify tracking service is running
   - Test tracking endpoints

## Export and Download Issues

### CSV Export Fails

**Symptoms:**
- Export button doesn't work
- Download doesn't start
- Empty or corrupt CSV file

**Solutions:**

1. **Check data availability:**
   - Ensure data exists to export
   - Verify filters aren't excluding all data
   - Check data format

2. **Browser settings:**
   - Check download permissions
   - Verify download location
   - Disable popup blockers

3. **Try different format:**
   - Use JSON export instead
   - Export smaller date range
   - Export in batches

### PDF Generation Fails

**Symptoms:**
- PDF download doesn't work
- PDF is blank or corrupt
- Error during generation

**Solutions:**

1. **Check dependencies:**
   ```bash
   pip install --upgrade reportlab weasyprint
   ```

2. **Verify data:**
   - Ensure all required data is available
   - Check for special characters
   - Verify chart rendering

3. **Backend issues:**
   - Check backend PDF generation
   - Review error logs
   - Test PDF endpoint directly

## Display and UI Issues

### Mobile Display Problems

**Symptoms:**
- Layout broken on mobile
- Buttons not clickable
- Text overlapping

**Solutions:**

1. **Use supported browser:**
   - Chrome or Safari on mobile
   - Update to latest version
   - Clear browser cache

2. **Rotate device:**
   - Try landscape orientation
   - Some features work better in landscape
   - Adjust zoom level

3. **Use desktop version:**
   - Request desktop site in browser
   - Some features optimized for desktop
   - Consider using tablet or computer

### Charts Not Visible

**Symptoms:**
- Charts show blank space
- Plotly charts don't render
- Chart area is empty

**Solutions:**

1. **Check browser compatibility:**
   - Use modern browser
   - Enable JavaScript
   - Update browser version

2. **Clear cache:**
   - Clear browser cache
   - Reload page
   - Try incognito mode

3. **Check data:**
   - Verify chart has data
   - Check for data format errors
   - Review console for errors

### Styling Issues

**Symptoms:**
- Colors wrong
- Layout broken
- CSS not loading

**Solutions:**

1. **Clear cache:**
   - Hard refresh (Ctrl+F5)
   - Clear browser cache
   - Restart browser

2. **Check custom CSS:**
   - Verify CSS in app.py
   - Check for CSS conflicts
   - Review browser console

3. **Update Streamlit:**
   ```bash
   pip install --upgrade streamlit
   ```

## Getting Additional Help

If issues persist after trying these solutions:

1. **Check logs:**
   - Streamlit logs: Terminal where app is running
   - Backend logs: Backend service logs
   - Browser console: F12 → Console tab

2. **Gather information:**
   - Error messages
   - Steps to reproduce
   - Browser and OS version
   - Screenshots if applicable

3. **Contact support:**
   - System administrator
   - Development team
   - Technical support channel

4. **Report bugs:**
   - Include error details
   - Provide reproduction steps
   - Attach relevant logs
   - Describe expected vs actual behavior

## Preventive Measures

To avoid common issues:

1. **Keep software updated:**
   - Update Streamlit regularly
   - Update Python packages
   - Update browser

2. **Monitor system health:**
   - Check API health indicator
   - Monitor backend performance
   - Review logs periodically

3. **Regular maintenance:**
   - Clear caches periodically
   - Restart services regularly
   - Update configurations as needed

4. **Follow best practices:**
   - Use supported browsers
   - Maintain stable network connection
   - Keep data organized
   - Regular backups
