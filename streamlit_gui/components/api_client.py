"""
API client for Event Planning Agent v2 integration
"""
import asyncio
import time
import hashlib
import json
from typing import Dict, List, Optional, Any
import requests
import aiohttp
from asyncio_throttle import Throttler
import streamlit as st
from utils.config import config
from utils.caching import cache_with_ttl, monitor_performance, CacheConfig

class APIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)

class APIClient:
    """
    API client for Event Planning Agent v2 backend
    Handles all communication with the FastAPI backend with caching support
    """
    
    def __init__(self):
        self.base_url = config.API_BASE_URL
        self.timeout = config.API_TIMEOUT
        self.retry_attempts = config.API_RETRY_ATTEMPTS
        self.retry_delay = config.API_RETRY_DELAY
        self.throttler = Throttler(rate_limit=10, period=1)  # 10 requests per second
        self.cache_ttl = config.get("CACHE_TTL", 300)  # 5 minutes default
        
    def _get_cache_key(self, method: str, endpoint: str, **kwargs) -> str:
        """Generate a cache key for the request"""
        cache_data = {
            "method": method,
            "endpoint": endpoint,
            "params": kwargs.get("params", {}),
            "json": kwargs.get("json", {})
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _is_cacheable(self, method: str, endpoint: str) -> bool:
        """Determine if a request should be cached"""
        # Only cache GET requests and specific endpoints
        if method != "GET":
            return False
        
        cacheable_endpoints = [
            "/health",
            "/v1/plans",  # List plans
        ]
        
        # Cache plan details and status for a short time
        if "/v1/plans/" in endpoint and any(suffix in endpoint for suffix in ["/status", "/results", "/blueprint"]):
            return True
            
        return any(endpoint.startswith(cacheable) for cacheable in cacheable_endpoints)
    
    def _cached_request(self, cache_key: str, method: str, endpoint: str, data_type: str = 'default', **kwargs) -> Dict:
        """Cached version of _make_request with configurable TTL"""
        ttl = CacheConfig.get_ttl(data_type)
        
        @st.cache_data(ttl=ttl, show_spinner=False)
        def _execute_cached(_cache_key: str, _method: str, _endpoint: str, **_kwargs) -> Dict:
            return self._make_request_uncached(_method, _endpoint, **_kwargs)
        
        return _execute_cached(cache_key, method, endpoint, **kwargs)
    
    @monitor_performance('api_request')
    def _make_request_uncached(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make request without caching (original implementation)"""
        url = config.get_api_url(endpoint)
        
        for attempt in range(self.retry_attempts):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    **kwargs
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    raise APIError(f"Endpoint not found: {endpoint}", response.status_code)
                elif response.status_code >= 500:
                    # Server error - retry
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                    raise APIError(f"Server error: {response.status_code}", response.status_code)
                else:
                    # Client error - don't retry
                    error_data = None
                    try:
                        error_data = response.json()
                    except:
                        pass
                    raise APIError(f"Request failed: {response.status_code}", response.status_code, error_data)
                    
            except requests.exceptions.ConnectionError:
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise APIError("Cannot connect to API server")
            except requests.exceptions.Timeout:
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise APIError("Request timeout")
            except requests.exceptions.RequestException as e:
                raise APIError(f"Request error: {str(e)}")
        
        raise APIError("Max retry attempts exceeded")
        
    def _make_request(self, method: str, endpoint: str, data_type: str = 'default', **kwargs) -> Dict:
        """
        Make a synchronous HTTP request with caching and retry logic
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data_type: Data type for cache TTL configuration
            **kwargs: Additional request parameters
        """
        # Check if request should be cached
        if self._is_cacheable(method, endpoint):
            cache_key = self._get_cache_key(method, endpoint, **kwargs)
            return self._cached_request(cache_key, method, endpoint, data_type, **kwargs)
        else:
            return self._make_request_uncached(method, endpoint, **kwargs)
    
    async def _make_async_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        Make an asynchronous HTTP request with retry logic
        """
        url = config.get_api_url(endpoint)
        
        async with self.throttler:
            for attempt in range(self.retry_attempts):
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                        async with session.request(method, url, **kwargs) as response:
                            if response.status == 200:
                                return await response.json()
                            elif response.status == 404:
                                raise APIError(f"Endpoint not found: {endpoint}", response.status)
                            elif response.status >= 500:
                                # Server error - retry
                                if attempt < self.retry_attempts - 1:
                                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                                    continue
                                raise APIError(f"Server error: {response.status}", response.status)
                            else:
                                # Client error - don't retry
                                error_data = None
                                try:
                                    error_data = await response.json()
                                except:
                                    pass
                                raise APIError(f"Request failed: {response.status}", response.status, error_data)
                                
                except aiohttp.ClientConnectorError:
                    if attempt < self.retry_attempts - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                    raise APIError("Cannot connect to API server")
                except asyncio.TimeoutError:
                    if attempt < self.retry_attempts - 1:
                        await asyncio.sleep(self.retry_delay * (attempt + 1))
                        continue
                    raise APIError("Request timeout")
                except Exception as e:
                    raise APIError(f"Request error: {str(e)}")
        
        raise APIError("Max retry attempts exceeded")
    
    def health_check(self) -> Dict:
        """
        Check API server health
        """
        try:
            return self._make_request("GET", "/health", data_type='health_check')
        except APIError:
            return {"status": "unhealthy", "error": "Cannot connect to server"}
    
    def create_plan(self, request_data: Dict) -> Dict:
        """
        Create a new event plan (synchronous)
        """
        return self._make_request("POST", "/v1/plans", json=request_data)
    
    async def create_plan_async(self, request_data: Dict) -> Dict:
        """
        Create a new event plan (asynchronous)
        """
        return await self._make_async_request("POST", "/v1/plans", json=request_data)
    
    def get_plan_status(self, plan_id: str) -> Dict:
        """
        Get the status of an event plan
        """
        return self._make_request("GET", f"/v1/plans/{plan_id}/status", data_type='plan_status')
    
    def get_plan_results(self, plan_id: str) -> Dict:
        """
        Get the results/combinations for an event plan
        """
        return self._make_request("GET", f"/v1/plans/{plan_id}/results", data_type='plan_results')
    
    def select_combination(self, plan_id: str, combination_id: str) -> Dict:
        """
        Select a vendor combination for an event plan
        """
        return self._make_request("POST", f"/v1/plans/{plan_id}/select", json={"combination_id": combination_id})
    
    def get_blueprint(self, plan_id: str) -> Dict:
        """
        Get the final blueprint for an event plan
        """
        return self._make_request("GET", f"/v1/plans/{plan_id}/blueprint", data_type='plan_blueprint')
    
    def list_plans(self, limit: int = 50, offset: int = 0) -> Dict:
        """
        List all event plans
        """
        params = {"limit": limit, "offset": offset}
        return self._make_request("GET", "/v1/plans", params=params, data_type='plan_list')
    
    def get_plan_details(self, plan_id: str) -> Dict:
        """
        Get detailed information about a specific plan
        """
        return self._make_request("GET", f"/v1/plans/{plan_id}")
    
    def delete_plan(self, plan_id: str) -> Dict:
        """
        Delete an event plan
        """
        return self._make_request("DELETE", f"/v1/plans/{plan_id}")
    
    async def stream_plan_status(self, plan_id: str, callback):
        """
        Stream real-time status updates for a plan
        """
        while True:
            try:
                status = await self._make_async_request("GET", f"/v1/plans/{plan_id}/status")
                callback(status)
                
                # Check if plan is complete
                if status.get("status") in ["completed", "failed", "cancelled"]:
                    break
                    
                await asyncio.sleep(2)  # Poll every 2 seconds
                
            except APIError as e:
                callback({"status": "error", "error": str(e)})
                break
    
    # ========== CRM API Methods ==========
    
    def get_preferences(self, client_id: str) -> Dict:
        """
        Get client communication preferences
        
        Args:
            client_id: Client identifier
            
        Returns:
            Preferences dictionary
        """
        return self._make_request("GET", f"/api/crm/preferences/{client_id}", data_type='crm_preferences')
    
    def update_preferences(self, preferences_data: Dict) -> Dict:
        """
        Update client communication preferences
        
        Args:
            preferences_data: Preferences data including client_id
            
        Returns:
            Updated preferences
        """
        return self._make_request("POST", "/api/crm/preferences", json=preferences_data)
    
    def get_communications(self, plan_id: Optional[str] = None, client_id: Optional[str] = None, 
                          channel: Optional[str] = None, status: Optional[str] = None,
                          limit: int = 100, offset: int = 0) -> Dict:
        """
        Get communication history with optional filters
        
        Args:
            plan_id: Optional plan ID filter
            client_id: Optional client ID filter
            channel: Optional channel filter (email, sms, whatsapp)
            status: Optional status filter (sent, delivered, opened, failed)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            Communications list and metadata
        """
        params = {"limit": limit, "offset": offset}
        
        if plan_id:
            params["plan_id"] = plan_id
        if client_id:
            params["client_id"] = client_id
        if channel:
            params["channel"] = channel
        if status:
            params["status"] = status
        
        return self._make_request("GET", "/api/crm/communications", params=params, data_type='communications')
    
    def get_analytics(self, plan_id: Optional[str] = None, client_id: Optional[str] = None,
                     start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """
        Get CRM analytics data
        
        Args:
            plan_id: Optional plan ID filter
            client_id: Optional client ID filter
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)
            
        Returns:
            Analytics data with metrics and charts
        """
        params = {}
        
        if plan_id:
            params["plan_id"] = plan_id
        if client_id:
            params["client_id"] = client_id
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        return self._make_request("GET", "/api/crm/analytics", params=params, data_type='analytics')
    
    # ========== Task Management API Methods ==========
    
    def get_extended_task_list(self, plan_id: str) -> Dict:
        """
        Get extended task list for a plan
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Extended task list with priorities, dependencies, vendors, and logistics
        """
        return self._make_request("GET", f"/api/task-management/plans/{plan_id}/extended-task-list", data_type='task_list')
    
    def get_timeline_data(self, plan_id: str) -> Dict:
        """
        Get timeline data for Gantt chart visualization
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Timeline data with task schedules and dependencies
        """
        return self._make_request("GET", f"/api/task-management/plans/{plan_id}/timeline", data_type='timeline_data')
    
    def get_conflicts(self, plan_id: str) -> Dict:
        """
        Get conflicts for a plan
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            List of conflicts with severity and resolution suggestions
        """
        return self._make_request("GET", f"/api/task-management/plans/{plan_id}/conflicts", data_type='conflicts')
    
    def update_task_status(self, plan_id: str, task_id: str, status: str) -> Dict:
        """
        Update task status
        
        Args:
            plan_id: Plan identifier
            task_id: Task identifier
            status: New status (pending, in_progress, completed, blocked)
            
        Returns:
            Updated task data
        """
        return self._make_request(
            "POST", 
            f"/api/task-management/plans/{plan_id}/tasks/{task_id}/status",
            json={"status": status}
        )
    
    def resolve_conflict(self, plan_id: str, conflict_id: str, resolution: Dict) -> Dict:
        """
        Apply a resolution to a conflict
        
        Args:
            plan_id: Plan identifier
            conflict_id: Conflict identifier
            resolution: Resolution data
            
        Returns:
            Updated conflict status
        """
        return self._make_request(
            "POST",
            f"/api/task-management/plans/{plan_id}/conflicts/{conflict_id}/resolve",
            json=resolution
        )

# Global API client instance
api_client = APIClient()