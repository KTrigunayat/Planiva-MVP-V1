"""
Optimized LLM Manager with caching, batch processing, and performance enhancements.
Provides efficient model loading, response caching, and connection pooling for LLM operations.
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from functools import lru_cache
from dataclasses import dataclass
from contextlib import asynccontextmanager
import aiohttp
from cachetools import TTLCache
import httpx

from ..config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class LLMRequest:
    """Structured LLM request for batch processing"""
    prompt: str
    model: str
    request_id: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None


@dataclass
class LLMResponse:
    """Structured LLM response"""
    request_id: str
    content: str
    model: str
    execution_time: float
    cached: bool = False
    error: Optional[str] = None


class OptimizedLLMManager:
    """
    Optimized LLM Manager with performance enhancements:
    - Response caching with TTL
    - Connection pooling
    - Batch processing
    - Model warmup and keep-alive
    - GPU optimization
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.llm_settings = self.settings.llm
        
        # Response cache
        self._response_cache = None
        if self.llm_settings.enable_response_cache:
            self._response_cache = TTLCache(
                maxsize=self.llm_settings.response_cache_size,
                ttl=self.llm_settings.response_cache_ttl
            )
        
        # Connection pool
        self._http_client = None
        self._connection_semaphore = asyncio.Semaphore(self.llm_settings.max_connections)
        
        # Batch processing
        self._batch_queue = asyncio.Queue()
        self._batch_processor_task = None
        self._batch_results = {}
        
        # Model status tracking
        self._model_status = {}
        self._warmup_completed = False
        
        # Performance metrics
        self._request_count = 0
        self._cache_hits = 0
        self._total_execution_time = 0.0
    
    async def initialize(self):
        """Initialize the LLM manager with optimizations"""
        logger.info("Initializing optimized LLM manager...")
        
        # Create optimized HTTP client
        timeout = httpx.Timeout(
            connect=self.llm_settings.connection_timeout,
            read=self.llm_settings.read_timeout,
            write=30.0,
            pool=5.0
        )
        
        limits = httpx.Limits(
            max_keepalive_connections=self.llm_settings.max_connections,
            max_connections=self.llm_settings.max_connections * 2,
            keepalive_expiry=self.llm_settings.model_keep_alive
        )
        
        self._http_client = httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            http2=True  # Enable HTTP/2 for better performance
        )
        
        # Start batch processor if enabled
        if self.llm_settings.enable_batch_processing:
            self._batch_processor_task = asyncio.create_task(self._batch_processor())
        
        # Warm up models if enabled
        if self.llm_settings.model_warmup_enabled:
            await self._warmup_models()
        
        logger.info("LLM manager initialization completed")
    
    async def shutdown(self):
        """Shutdown the LLM manager and cleanup resources"""
        logger.info("Shutting down LLM manager...")
        
        # Stop batch processor
        if self._batch_processor_task:
            self._batch_processor_task.cancel()
            try:
                await self._batch_processor_task
            except asyncio.CancelledError:
                pass
        
        # Close HTTP client
        if self._http_client:
            await self._http_client.aclose()
        
        # Log performance metrics
        self._log_performance_metrics()
        
        logger.info("LLM manager shutdown completed")
    
    def _generate_cache_key(self, prompt: str, model: str, **kwargs) -> str:
        """Generate cache key for request"""
        cache_data = {
            'prompt': prompt,
            'model': model,
            **kwargs
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Get cached response if available"""
        if not self._response_cache:
            return None
        
        cached_response = self._response_cache.get(cache_key)
        if cached_response:
            self._cache_hits += 1
            logger.debug(f"Cache hit for key: {cache_key[:8]}...")
            return cached_response
        
        return None
    
    def _cache_response(self, cache_key: str, response: str):
        """Cache response with TTL"""
        if self._response_cache:
            self._response_cache[cache_key] = response
            logger.debug(f"Cached response for key: {cache_key[:8]}...")
    
    async def _warmup_models(self):
        """Warm up models to improve first-request performance"""
        logger.info("Starting model warmup...")
        
        models_to_warmup = [
            self.llm_settings.gemma_model,
            self.llm_settings.tinyllama_model
        ]
        
        warmup_tasks = []
        for model in models_to_warmup:
            task = asyncio.create_task(self._warmup_single_model(model))
            warmup_tasks.append(task)
        
        try:
            await asyncio.gather(*warmup_tasks, return_exceptions=True)
            self._warmup_completed = True
            logger.info("Model warmup completed successfully")
        except Exception as e:
            logger.warning(f"Model warmup failed: {e}")
    
    async def _warmup_single_model(self, model: str):
        """Warm up a single model"""
        try:
            warmup_prompt = "Hello, this is a warmup request."
            
            async with self._connection_semaphore:
                response = await self._http_client.post(
                    f"{self.llm_settings.ollama_base_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": warmup_prompt,
                        "stream": False,
                        "keep_alive": f"{self.llm_settings.model_keep_alive}s"
                    }
                )
                
                if response.status_code == 200:
                    self._model_status[model] = "ready"
                    logger.info(f"Model {model} warmed up successfully")
                else:
                    logger.warning(f"Failed to warm up model {model}: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error warming up model {model}: {e}")
    
    async def _batch_processor(self):
        """Process LLM requests in batches for improved efficiency"""
        logger.info("Starting batch processor...")
        
        while True:
            try:
                batch = []
                
                # Collect requests for batch processing
                try:
                    # Wait for first request
                    first_request = await asyncio.wait_for(
                        self._batch_queue.get(),
                        timeout=self.llm_settings.batch_timeout
                    )
                    batch.append(first_request)
                    
                    # Collect additional requests up to batch size
                    for _ in range(self.llm_settings.batch_size - 1):
                        try:
                            request = await asyncio.wait_for(
                                self._batch_queue.get(),
                                timeout=0.1  # Short timeout for additional requests
                            )
                            batch.append(request)
                        except asyncio.TimeoutError:
                            break
                            
                except asyncio.TimeoutError:
                    continue  # No requests to process
                
                # Process batch
                if batch:
                    await self._process_batch(batch)
                    
            except asyncio.CancelledError:
                logger.info("Batch processor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in batch processor: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
    
    async def _process_batch(self, batch: List[LLMRequest]):
        """Process a batch of LLM requests"""
        logger.debug(f"Processing batch of {len(batch)} requests")
        
        # Group requests by model for efficiency
        model_groups = {}
        for request in batch:
            if request.model not in model_groups:
                model_groups[request.model] = []
            model_groups[request.model].append(request)
        
        # Process each model group
        tasks = []
        for model, requests in model_groups.items():
            task = asyncio.create_task(self._process_model_batch(model, requests))
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_model_batch(self, model: str, requests: List[LLMRequest]):
        """Process requests for a specific model"""
        for request in requests:
            try:
                response = await self._execute_single_request(request)
                self._batch_results[request.request_id] = response
            except Exception as e:
                error_response = LLMResponse(
                    request_id=request.request_id,
                    content="",
                    model=model,
                    execution_time=0.0,
                    error=str(e)
                )
                self._batch_results[request.request_id] = error_response
    
    async def _execute_single_request(self, request: LLMRequest) -> LLMResponse:
        """Execute a single LLM request"""
        start_time = time.time()
        
        # Check cache first
        cache_key = self._generate_cache_key(
            request.prompt, 
            request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            system_prompt=request.system_prompt
        )
        
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            return LLMResponse(
                request_id=request.request_id,
                content=cached_response,
                model=request.model,
                execution_time=time.time() - start_time,
                cached=True
            )
        
        # Execute request
        try:
            async with self._connection_semaphore:
                payload = {
                    "model": request.model,
                    "prompt": request.prompt,
                    "stream": False,
                    "keep_alive": f"{self.llm_settings.model_keep_alive}s",
                    "options": {
                        "temperature": request.temperature
                    }
                }
                
                if request.max_tokens:
                    payload["options"]["num_predict"] = request.max_tokens
                
                if request.system_prompt:
                    payload["system"] = request.system_prompt
                
                response = await self._http_client.post(
                    f"{self.llm_settings.ollama_base_url}/api/generate",
                    json=payload,
                    timeout=self.llm_settings.model_timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("response", "")
                    
                    # Cache successful response
                    self._cache_response(cache_key, content)
                    
                    execution_time = time.time() - start_time
                    self._total_execution_time += execution_time
                    
                    return LLMResponse(
                        request_id=request.request_id,
                        content=content,
                        model=request.model,
                        execution_time=execution_time
                    )
                else:
                    raise Exception(f"LLM request failed with status {response.status_code}: {response.text}")
                    
        except Exception as e:
            logger.error(f"LLM request execution failed: {e}")
            raise
    
    async def generate_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        use_batch: bool = True
    ) -> str:
        """
        Generate LLM response with optimizations
        
        Args:
            prompt: Input prompt
            model: Model name (defaults to gemma:2b)
            temperature: Response randomness
            max_tokens: Maximum tokens to generate
            system_prompt: System prompt for context
            use_batch: Whether to use batch processing
            
        Returns:
            Generated response content
        """
        self._request_count += 1
        
        if not model:
            model = self.llm_settings.gemma_model
        
        request_id = f"req_{int(time.time() * 1000)}_{self._request_count}"
        
        llm_request = LLMRequest(
            prompt=prompt,
            model=model,
            request_id=request_id,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt
        )
        
        if use_batch and self.llm_settings.enable_batch_processing:
            # Add to batch queue
            await self._batch_queue.put(llm_request)
            
            # Wait for result
            max_wait_time = self.llm_settings.batch_timeout + self.llm_settings.model_timeout
            for _ in range(int(max_wait_time * 10)):  # Check every 100ms
                if request_id in self._batch_results:
                    response = self._batch_results.pop(request_id)
                    if response.error:
                        raise Exception(response.error)
                    return response.content
                await asyncio.sleep(0.1)
            
            raise Exception("Batch processing timeout")
        else:
            # Execute immediately
            response = await self._execute_single_request(llm_request)
            if response.error:
                raise Exception(response.error)
            return response.content
    
    async def generate_batch_responses(
        self,
        requests: List[Dict[str, Any]]
    ) -> List[LLMResponse]:
        """
        Generate multiple responses efficiently
        
        Args:
            requests: List of request dictionaries with prompt, model, etc.
            
        Returns:
            List of LLM responses
        """
        llm_requests = []
        for i, req in enumerate(requests):
            request_id = f"batch_{int(time.time() * 1000)}_{i}"
            llm_request = LLMRequest(
                prompt=req["prompt"],
                model=req.get("model", self.llm_settings.gemma_model),
                request_id=request_id,
                temperature=req.get("temperature", 0.7),
                max_tokens=req.get("max_tokens"),
                system_prompt=req.get("system_prompt")
            )
            llm_requests.append(llm_request)
        
        # Process batch directly
        await self._process_batch(llm_requests)
        
        # Collect results
        responses = []
        for request in llm_requests:
            if request.request_id in self._batch_results:
                response = self._batch_results.pop(request.request_id)
                responses.append(response)
            else:
                # Create error response for missing results
                error_response = LLMResponse(
                    request_id=request.request_id,
                    content="",
                    model=request.model,
                    execution_time=0.0,
                    error="Request not processed"
                )
                responses.append(error_response)
        
        return responses
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring"""
        cache_hit_rate = (self._cache_hits / self._request_count) if self._request_count > 0 else 0
        avg_execution_time = (self._total_execution_time / self._request_count) if self._request_count > 0 else 0
        
        return {
            "total_requests": self._request_count,
            "cache_hits": self._cache_hits,
            "cache_hit_rate": cache_hit_rate,
            "avg_execution_time": avg_execution_time,
            "total_execution_time": self._total_execution_time,
            "warmup_completed": self._warmup_completed,
            "model_status": self._model_status.copy(),
            "cache_size": len(self._response_cache) if self._response_cache else 0,
            "batch_queue_size": self._batch_queue.qsize() if self._batch_queue else 0
        }
    
    def _log_performance_metrics(self):
        """Log performance metrics"""
        metrics = self.get_performance_metrics()
        logger.info(f"LLM Manager Performance Metrics: {json.dumps(metrics, indent=2)}")


# Global LLM manager instance
_llm_manager: Optional[OptimizedLLMManager] = None


async def get_llm_manager() -> OptimizedLLMManager:
    """Get global LLM manager instance"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = OptimizedLLMManager()
        await _llm_manager.initialize()
    return _llm_manager


async def shutdown_llm_manager():
    """Shutdown global LLM manager"""
    global _llm_manager
    if _llm_manager:
        await _llm_manager.shutdown()
        _llm_manager = None


@asynccontextmanager
async def llm_manager_context():
    """Context manager for LLM manager lifecycle"""
    manager = await get_llm_manager()
    try:
        yield manager
    finally:
        # Manager will be shutdown when application shuts down
        pass