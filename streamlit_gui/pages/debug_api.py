"""
Debug page to check API configuration and connectivity
"""
import streamlit as st
import requests
from utils.config import config
from components.api_client import api_client, APIError

def render_debug_api_page():
    """Render API debug page"""
    st.title("🔧 API Debug Information")
    
    st.markdown("---")
    
    # Configuration
    st.subheader("📋 Configuration")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("API Base URL", config.API_BASE_URL)
        st.metric("API Timeout", f"{config.API_TIMEOUT}s")
        st.metric("Retry Attempts", config.API_RETRY_ATTEMPTS)
    
    with col2:
        st.metric("Environment", "Development" if config.is_development() else "Production")
        st.metric("Cache TTL", f"{config.CACHE_TTL}s")
    
    st.markdown("---")
    
    # Health Check
    st.subheader("🏥 Health Check")
    
    if st.button("Test API Connection", type="primary"):
        with st.spinner("Testing connection..."):
            try:
                # Direct request to health endpoint
                health_url = f"{config.API_BASE_URL}/health"
                st.info(f"Testing: {health_url}")
                
                response = requests.get(health_url, timeout=10)
                
                if response.status_code == 200:
                    st.success("✅ API is reachable!")
                    st.json(response.json())
                else:
                    st.error(f"❌ API returned status code: {response.status_code}")
                    st.code(response.text)
                    
            except requests.exceptions.ConnectionError as e:
                st.error("❌ Connection Error: Cannot reach the API server")
                st.code(str(e))
                st.warning("""
                **Possible causes:**
                - API server is not running
                - Wrong API_BASE_URL configured
                - Network/firewall blocking the connection
                - CORS issues
                """)
                
            except requests.exceptions.Timeout:
                st.error("❌ Timeout: API server took too long to respond")
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)
    
    st.markdown("---")
    
    # Test Endpoints
    st.subheader("🧪 Test Endpoints")
    
    endpoints = [
        ("/health", "GET", "Health Check"),
        ("/docs", "GET", "API Documentation"),
        ("/v1/plans", "GET", "List Plans"),
    ]
    
    for endpoint, method, description in endpoints:
        with st.expander(f"{method} {endpoint} - {description}"):
            if st.button(f"Test {endpoint}", key=f"test_{endpoint}"):
                try:
                    url = f"{config.API_BASE_URL}{endpoint}"
                    st.info(f"Testing: {url}")
                    
                    if method == "GET":
                        response = requests.get(url, timeout=10)
                    else:
                        response = requests.request(method, url, timeout=10)
                    
                    st.success(f"Status Code: {response.status_code}")
                    
                    try:
                        st.json(response.json())
                    except:
                        st.code(response.text)
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    st.markdown("---")
    
    # Environment Variables
    st.subheader("🔐 Environment Variables")
    
    with st.expander("Show Environment Configuration"):
        env_vars = {
            "API_BASE_URL": config.API_BASE_URL,
            "API_TIMEOUT": config.API_TIMEOUT,
            "API_RETRY_ATTEMPTS": config.API_RETRY_ATTEMPTS,
            "APP_TITLE": config.APP_TITLE,
            "ENVIRONMENT": "development" if config.is_development() else "production",
            "CACHE_TTL": config.CACHE_TTL,
        }
        
        for key, value in env_vars.items():
            st.code(f"{key} = {value}")
    
    st.markdown("---")
    
    # Instructions
    st.subheader("📖 How to Fix Connection Issues")
    
    st.markdown("""
    ### If API connection fails:
    
    1. **Check API_BASE_URL in Streamlit Secrets**
       - Go to Streamlit Cloud dashboard
       - Click on your app → Settings → Secrets
       - Verify `API_BASE_URL` is set correctly
       - Example: `API_BASE_URL = "https://your-app.onrender.com"`
    
    2. **Verify Backend is Running**
       - Visit your backend URL in browser
       - Should see: `{"status": "healthy", "version": "2.0.0"}`
    
    3. **Check CORS Configuration**
       - Backend must allow requests from Streamlit domain
       - In Render, set: `CORS_ORIGINS=*` (or specific Streamlit URL)
    
    4. **Test Backend Directly**
       ```bash
       curl https://your-backend-url.onrender.com/health
       ```
    
    5. **Common Issues:**
       - Backend URL missing `/health` endpoint
       - HTTPS vs HTTP mismatch
       - Backend service sleeping (Render free tier)
       - Firewall/network blocking requests
    """)

if __name__ == "__main__":
    render_debug_api_page()
