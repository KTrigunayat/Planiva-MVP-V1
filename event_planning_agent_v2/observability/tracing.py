"""
Distributed tracing system for Event Planning Agent v2.

Provides request tracing, span management, and distributed context
propagation across agents, workflows, and MCP servers.
"""

import time
import uuid
import threading
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from contextvars import ContextVar
import json

from .logging import get_logger, CorrelationContext

logger = get_logger(__name__, component="tracing")


class SpanKind(str, Enum):
    """Types of spans"""
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"
    INTERNAL = "internal"


class SpanStatus(str, Enum):
    """Span status"""
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


# Context variables for tracing
trace_context: ContextVar[Optional['TraceContext']] = ContextVar('trace_context', default=None)
current_span: ContextVar[Optional['Span']] = ContextVar('current_span', default=None)


@dataclass
class TraceContext:
    """Trace context for distributed tracing"""
    trace_id: str
    parent_span_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "baggage": self.baggage
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TraceContext':
        """Create from dictionary"""
        return cls(
            trace_id=data["trace_id"],
            parent_span_id=data.get("parent_span_id"),
            baggage=data.get("baggage", {})
        )
    
    def add_baggage(self, key: str, value: str):
        """Add baggage item"""
        self.baggage[key] = value
    
    def get_baggage(self, key: str) -> Optional[str]:
        """Get baggage item"""
        return self.baggage.get(key)


@dataclass
class Span:
    """Individual span in a trace"""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: SpanStatus = SpanStatus.OK
    kind: SpanKind = SpanKind.INTERNAL
    component: Optional[str] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    def finish(self, status: SpanStatus = SpanStatus.OK):
        """Finish the span"""
        self.end_time = datetime.utcnow()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = status
    
    def set_tag(self, key: str, value: Any):
        """Set span tag"""
        self.tags[key] = value
    
    def log(self, message: str, level: str = "info", **kwargs):
        """Add log entry to span"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }
        self.logs.append(log_entry)
    
    def set_error(self, error: Exception):
        """Mark span as error"""
        self.status = SpanStatus.ERROR
        self.set_tag("error", True)
        self.set_tag("error.type", type(error).__name__)
        self.set_tag("error.message", str(error))
        self.log(f"Error: {error}", level="error")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "operation_name": self.operation_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "kind": self.kind.value,
            "component": self.component,
            "tags": self.tags,
            "logs": self.logs
        }


class TracingManager:
    """Central tracing management system"""
    
    def __init__(self):
        self.spans: Dict[str, Span] = {}
        self.traces: Dict[str, List[str]] = {}  # trace_id -> list of span_ids
        self.span_processors: List[Callable[[Span], None]] = []
        
        # Configuration
        self.enabled = True
        self.max_spans_per_trace = 1000
        self.max_traces = 10000
        self.span_retention_hours = 24
        
        # Background cleanup
        self.cleanup_enabled = True
        self.cleanup_interval = 300  # 5 minutes
        self.cleanup_thread: Optional[threading.Thread] = None
        self.stop_cleanup = threading.Event()
        
        # Thread safety
        self._lock = threading.Lock()
    
    def start_tracing(self):
        """Start tracing system"""
        if not self.enabled:
            return
        
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            logger.warning("Tracing already started")
            return
        
        self.stop_cleanup.clear()
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        logger.info("Tracing system started")
    
    def stop_tracing(self):
        """Stop tracing system"""
        self.stop_cleanup.set()
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        
        logger.info("Tracing system stopped")
    
    def add_span_processor(self, processor: Callable[[Span], None]):
        """Add span processor"""
        self.span_processors.append(processor)
    
    def create_trace(self, trace_id: Optional[str] = None) -> TraceContext:
        """Create new trace context"""
        if not trace_id:
            trace_id = self._generate_trace_id()
        
        trace_context_obj = TraceContext(trace_id=trace_id)
        
        with self._lock:
            if trace_id not in self.traces:
                self.traces[trace_id] = []
        
        return trace_context_obj
    
    def start_span(
        self,
        operation_name: str,
        parent_span: Optional[Span] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        component: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ) -> Span:
        """Start new span"""
        if not self.enabled:
            # Return dummy span if tracing is disabled
            return self._create_dummy_span(operation_name)
        
        # Get trace context
        context = trace_context.get()
        if not context:
            # Create new trace if none exists
            context = self.create_trace()
            trace_context.set(context)
        
        # Determine parent
        parent_span_id = None
        if parent_span:
            parent_span_id = parent_span.span_id
        else:
            current = current_span.get()
            if current:
                parent_span_id = current.span_id
        
        # Create span
        span = Span(
            span_id=self._generate_span_id(),
            trace_id=context.trace_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=datetime.utcnow(),
            kind=kind,
            component=component,
            tags=tags or {}
        )
        
        # Store span
        with self._lock:
            self.spans[span.span_id] = span
            self.traces[context.trace_id].append(span.span_id)
        
        # Set as current span
        current_span.set(span)
        
        logger.debug(f"Started span: {operation_name} (trace: {context.trace_id}, span: {span.span_id})")
        return span
    
    def finish_span(self, span: Span, status: SpanStatus = SpanStatus.OK):
        """Finish span"""
        if not self.enabled or not span:
            return
        
        span.finish(status)
        
        # Process span
        for processor in self.span_processors:
            try:
                processor(span)
            except Exception as e:
                logger.error(f"Span processor failed: {e}")
        
        logger.debug(f"Finished span: {span.operation_name} ({span.duration_ms:.2f}ms)")
    
    def get_current_span(self) -> Optional[Span]:
        """Get current active span"""
        return current_span.get()
    
    def get_trace_context(self) -> Optional[TraceContext]:
        """Get current trace context"""
        return trace_context.get()
    
    def set_trace_context(self, context: TraceContext):
        """Set trace context"""
        trace_context.set(context)
    
    def get_trace(self, trace_id: str) -> List[Span]:
        """Get all spans for a trace"""
        with self._lock:
            span_ids = self.traces.get(trace_id, [])
            return [self.spans[span_id] for span_id in span_ids if span_id in self.spans]
    
    def get_span(self, span_id: str) -> Optional[Span]:
        """Get specific span"""
        with self._lock:
            return self.spans.get(span_id)
    
    def export_trace(self, trace_id: str, format_type: str = "json") -> str:
        """Export trace in specified format"""
        spans = self.get_trace(trace_id)
        
        if format_type == "json":
            trace_data = {
                "trace_id": trace_id,
                "spans": [span.to_dict() for span in spans],
                "span_count": len(spans),
                "total_duration_ms": self._calculate_trace_duration(spans)
            }
            return json.dumps(trace_data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def get_trace_summary(self, trace_id: str) -> Dict[str, Any]:
        """Get trace summary"""
        spans = self.get_trace(trace_id)
        
        if not spans:
            return {"trace_id": trace_id, "spans": 0}
        
        # Calculate statistics
        total_duration = self._calculate_trace_duration(spans)
        error_count = sum(1 for span in spans if span.status == SpanStatus.ERROR)
        components = set(span.component for span in spans if span.component)
        operations = set(span.operation_name for span in spans)
        
        return {
            "trace_id": trace_id,
            "span_count": len(spans),
            "total_duration_ms": total_duration,
            "error_count": error_count,
            "success_rate": (len(spans) - error_count) / len(spans) if spans else 0,
            "components": list(components),
            "operations": list(operations),
            "start_time": min(span.start_time for span in spans).isoformat(),
            "end_time": max(span.end_time for span in spans if span.end_time).isoformat() if any(span.end_time for span in spans) else None
        }
    
    def _generate_trace_id(self) -> str:
        """Generate unique trace ID"""
        return str(uuid.uuid4())
    
    def _generate_span_id(self) -> str:
        """Generate unique span ID"""
        return str(uuid.uuid4())
    
    def _create_dummy_span(self, operation_name: str) -> Span:
        """Create dummy span when tracing is disabled"""
        return Span(
            span_id="dummy",
            trace_id="dummy",
            parent_span_id=None,
            operation_name=operation_name,
            start_time=datetime.utcnow()
        )
    
    def _calculate_trace_duration(self, spans: List[Span]) -> Optional[float]:
        """Calculate total trace duration"""
        if not spans:
            return None
        
        start_times = [span.start_time for span in spans]
        end_times = [span.end_time for span in spans if span.end_time]
        
        if not end_times:
            return None
        
        earliest_start = min(start_times)
        latest_end = max(end_times)
        
        return (latest_end - earliest_start).total_seconds() * 1000
    
    def _cleanup_loop(self):
        """Background cleanup loop"""
        while not self.stop_cleanup.wait(self.cleanup_interval):
            try:
                self._cleanup_old_traces()
            except Exception as e:
                logger.error(f"Error in tracing cleanup loop: {e}")
    
    def _cleanup_old_traces(self):
        """Clean up old traces and spans"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.span_retention_hours)
        
        with self._lock:
            # Find old spans
            old_span_ids = []
            for span_id, span in self.spans.items():
                if span.start_time < cutoff_time:
                    old_span_ids.append(span_id)
            
            # Remove old spans
            for span_id in old_span_ids:
                del self.spans[span_id]
            
            # Clean up traces
            traces_to_remove = []
            for trace_id, span_ids in self.traces.items():
                # Remove old span IDs from trace
                self.traces[trace_id] = [sid for sid in span_ids if sid not in old_span_ids]
                
                # Remove empty traces
                if not self.traces[trace_id]:
                    traces_to_remove.append(trace_id)
            
            for trace_id in traces_to_remove:
                del self.traces[trace_id]
            
            if old_span_ids:
                logger.debug(f"Cleaned up {len(old_span_ids)} old spans and {len(traces_to_remove)} empty traces")


class SpanContext:
    """Context manager for spans"""
    
    def __init__(
        self,
        operation_name: str,
        tracer: Optional[TracingManager] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        component: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None
    ):
        self.operation_name = operation_name
        self.tracer = tracer or get_tracer()
        self.kind = kind
        self.component = component
        self.tags = tags
        self.span: Optional[Span] = None
        self.previous_span: Optional[Span] = None
    
    def __enter__(self) -> Span:
        # Save previous span
        self.previous_span = current_span.get()
        
        # Start new span
        self.span = self.tracer.start_span(
            operation_name=self.operation_name,
            kind=self.kind,
            component=self.component,
            tags=self.tags
        )
        
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            # Set error status if exception occurred
            if exc_type is not None:
                self.span.set_error(exc_val)
                status = SpanStatus.ERROR
            else:
                status = SpanStatus.OK
            
            # Finish span
            self.tracer.finish_span(self.span, status)
        
        # Restore previous span
        current_span.set(self.previous_span)


# Global tracer instance
_tracer: Optional[TracingManager] = None


def get_tracer() -> TracingManager:
    """Get global tracer instance"""
    global _tracer
    if _tracer is None:
        _tracer = TracingManager()
    return _tracer


# Convenience functions
def start_span(
    operation_name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    component: Optional[str] = None,
    tags: Optional[Dict[str, Any]] = None
) -> Span:
    """Start new span"""
    tracer = get_tracer()
    return tracer.start_span(operation_name, kind=kind, component=component, tags=tags)


def finish_span(span: Span, status: SpanStatus = SpanStatus.OK):
    """Finish span"""
    tracer = get_tracer()
    tracer.finish_span(span, status)


def get_current_span() -> Optional[Span]:
    """Get current span"""
    return current_span.get()


def trace_operation(
    operation_name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    component: Optional[str] = None,
    tags: Optional[Dict[str, Any]] = None
) -> SpanContext:
    """Create span context manager"""
    return SpanContext(
        operation_name=operation_name,
        kind=kind,
        component=component,
        tags=tags
    )


# Decorators
def trace_function(
    operation_name: Optional[str] = None,
    kind: SpanKind = SpanKind.INTERNAL,
    component: Optional[str] = None,
    include_args: bool = False
):
    """Decorator to trace function execution"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            tags = {}
            if include_args:
                tags["args_count"] = len(args)
                tags["kwargs_count"] = len(kwargs)
            
            with trace_operation(op_name, kind=kind, component=component, tags=tags) as span:
                # Add function metadata
                span.set_tag("function.name", func.__name__)
                span.set_tag("function.module", func.__module__)
                
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def trace_agent_operation(agent_name: str, operation: Optional[str] = None):
    """Decorator to trace agent operations"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_name = operation or func.__name__
            
            with trace_operation(
                f"agent.{agent_name}.{op_name}",
                kind=SpanKind.INTERNAL,
                component="agent",
                tags={"agent.name": agent_name, "agent.operation": op_name}
            ) as span:
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def trace_workflow_operation(workflow_type: str, operation: Optional[str] = None):
    """Decorator to trace workflow operations"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_name = operation or func.__name__
            
            with trace_operation(
                f"workflow.{workflow_type}.{op_name}",
                kind=SpanKind.INTERNAL,
                component="workflow",
                tags={"workflow.type": workflow_type, "workflow.operation": op_name}
            ) as span:
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def trace_mcp_operation(server_name: str, tool_name: Optional[str] = None):
    """Decorator to trace MCP operations"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            tool = tool_name or func.__name__
            
            with trace_operation(
                f"mcp.{server_name}.{tool}",
                kind=SpanKind.CLIENT,
                component="mcp_server",
                tags={"mcp.server": server_name, "mcp.tool": tool}
            ) as span:
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Context propagation utilities
def inject_trace_context(headers: Dict[str, str]) -> Dict[str, str]:
    """Inject trace context into headers"""
    context = trace_context.get()
    if context:
        headers["X-Trace-Id"] = context.trace_id
        if context.parent_span_id:
            headers["X-Parent-Span-Id"] = context.parent_span_id
        
        # Inject baggage
        for key, value in context.baggage.items():
            headers[f"X-Baggage-{key}"] = value
    
    # Also inject correlation ID
    correlation_id = CorrelationContext.get_correlation_id()
    if correlation_id:
        headers["X-Correlation-Id"] = correlation_id
    
    return headers


def extract_trace_context(headers: Dict[str, str]) -> Optional[TraceContext]:
    """Extract trace context from headers"""
    trace_id = headers.get("X-Trace-Id")
    if not trace_id:
        return None
    
    parent_span_id = headers.get("X-Parent-Span-Id")
    
    # Extract baggage
    baggage = {}
    for key, value in headers.items():
        if key.startswith("X-Baggage-"):
            baggage_key = key[10:]  # Remove "X-Baggage-" prefix
            baggage[baggage_key] = value
    
    context = TraceContext(
        trace_id=trace_id,
        parent_span_id=parent_span_id,
        baggage=baggage
    )
    
    # Also extract correlation ID
    correlation_id = headers.get("X-Correlation-Id")
    if correlation_id:
        CorrelationContext.set_correlation_id(correlation_id)
    
    return context


# Span processors
def logging_span_processor(span: Span):
    """Span processor that logs span completion"""
    logger.debug(
        f"Span completed: {span.operation_name}",
        operation="span_completed",
        metadata={
            "span_id": span.span_id,
            "trace_id": span.trace_id,
            "duration_ms": span.duration_ms,
            "status": span.status.value,
            "component": span.component
        }
    )


def metrics_span_processor(span: Span):
    """Span processor that records metrics"""
    from .metrics import get_metrics_collector
    
    collector = get_metrics_collector()
    
    # Record span duration
    if span.duration_ms is not None:
        collector.record_timer(
            f"span_duration",
            span.duration_ms,
            labels={
                "operation": span.operation_name,
                "component": span.component or "unknown",
                "status": span.status.value
            }
        )
    
    # Record span count
    collector.record_counter(
        "span_count",
        1.0,
        labels={
            "operation": span.operation_name,
            "component": span.component or "unknown",
            "status": span.status.value
        }
    )


# Initialize default tracing
def setup_default_tracing():
    """Setup default tracing configuration"""
    tracer = get_tracer()
    
    # Add default span processors
    tracer.add_span_processor(logging_span_processor)
    tracer.add_span_processor(metrics_span_processor)
    
    # Start tracing
    tracer.start_tracing()
    
    logger.info("Default tracing setup completed")