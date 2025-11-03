"""
Performance metrics collection system for agents and workflows.

Provides comprehensive metrics collection, aggregation, and reporting
for monitoring system performance and identifying bottlenecks.
"""

import time
import threading
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
import json

from .logging import get_logger

logger = get_logger(__name__, component="metrics")


class MetricType(str, Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"


class AggregationType(str, Enum):
    """Metric aggregation types"""
    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE_50 = "p50"
    PERCENTILE_95 = "p95"
    PERCENTILE_99 = "p99"


@dataclass
class MetricValue:
    """Individual metric value"""
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricSeries:
    """Time series of metric values"""
    name: str
    metric_type: MetricType
    values: deque = field(default_factory=lambda: deque(maxlen=1000))
    labels: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    
    def add_value(self, value: float, labels: Optional[Dict[str, str]] = None, metadata: Optional[Dict[str, Any]] = None):
        """Add value to metric series"""
        metric_value = MetricValue(
            value=value,
            timestamp=datetime.utcnow(),
            labels=labels or {},
            metadata=metadata or {}
        )
        self.values.append(metric_value)
    
    def get_latest_value(self) -> Optional[float]:
        """Get latest metric value"""
        return self.values[-1].value if self.values else None
    
    def get_values_in_window(self, window_minutes: int) -> List[MetricValue]:
        """Get values within time window"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        return [v for v in self.values if v.timestamp >= cutoff_time]
    
    def aggregate(self, aggregation: AggregationType, window_minutes: Optional[int] = None) -> Optional[float]:
        """Aggregate metric values"""
        values = self.get_values_in_window(window_minutes) if window_minutes else list(self.values)
        
        if not values:
            return None
        
        numeric_values = [v.value for v in values]
        
        if aggregation == AggregationType.SUM:
            return sum(numeric_values)
        elif aggregation == AggregationType.AVERAGE:
            return statistics.mean(numeric_values)
        elif aggregation == AggregationType.MIN:
            return min(numeric_values)
        elif aggregation == AggregationType.MAX:
            return max(numeric_values)
        elif aggregation == AggregationType.COUNT:
            return len(numeric_values)
        elif aggregation == AggregationType.PERCENTILE_50:
            return statistics.median(numeric_values)
        elif aggregation == AggregationType.PERCENTILE_95:
            return statistics.quantiles(numeric_values, n=20)[18] if len(numeric_values) >= 20 else max(numeric_values)
        elif aggregation == AggregationType.PERCENTILE_99:
            return statistics.quantiles(numeric_values, n=100)[98] if len(numeric_values) >= 100 else max(numeric_values)
        else:
            return None


@dataclass
class AgentMetrics:
    """Metrics specific to agent performance"""
    agent_name: str
    task_execution_times: deque = field(default_factory=lambda: deque(maxlen=100))
    task_success_count: int = 0
    task_failure_count: int = 0
    total_tasks: int = 0
    communication_count: int = 0
    tool_usage_count: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    last_activity: Optional[datetime] = None
    
    def record_task_execution(self, duration_ms: float, success: bool, tool_name: Optional[str] = None):
        """Record task execution metrics"""
        self.task_execution_times.append(duration_ms)
        self.total_tasks += 1
        self.last_activity = datetime.utcnow()
        
        if success:
            self.task_success_count += 1
        else:
            self.task_failure_count += 1
        
        if tool_name:
            self.tool_usage_count[tool_name] += 1
    
    def record_communication(self):
        """Record agent communication"""
        self.communication_count += 1
        self.last_activity = datetime.utcnow()
    
    def get_success_rate(self) -> float:
        """Calculate task success rate"""
        if self.total_tasks == 0:
            return 0.0
        return self.task_success_count / self.total_tasks
    
    def get_average_execution_time(self) -> float:
        """Calculate average task execution time"""
        if not self.task_execution_times:
            return 0.0
        return statistics.mean(self.task_execution_times)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get agent metrics summary"""
        return {
            "agent_name": self.agent_name,
            "total_tasks": self.total_tasks,
            "success_rate": self.get_success_rate(),
            "failure_rate": 1.0 - self.get_success_rate(),
            "average_execution_time_ms": self.get_average_execution_time(),
            "communication_count": self.communication_count,
            "tool_usage": dict(self.tool_usage_count),
            "last_activity": self.last_activity.isoformat() if self.last_activity else None
        }


@dataclass
class WorkflowMetrics:
    """Metrics specific to workflow performance"""
    workflow_id: str
    workflow_type: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    node_execution_times: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    node_success_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    node_failure_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    iterations: int = 0
    beam_search_evaluations: int = 0
    state_transitions: int = 0
    checkpoints_created: int = 0
    recovery_attempts: int = 0
    
    def start_workflow(self):
        """Mark workflow start"""
        self.start_time = datetime.utcnow()
    
    def end_workflow(self):
        """Mark workflow end"""
        self.end_time = datetime.utcnow()
    
    def record_node_execution(self, node_name: str, duration_ms: float, success: bool):
        """Record node execution metrics"""
        self.node_execution_times[node_name].append(duration_ms)
        
        if success:
            self.node_success_counts[node_name] += 1
        else:
            self.node_failure_counts[node_name] += 1
    
    def record_iteration(self):
        """Record workflow iteration"""
        self.iterations += 1
    
    def record_beam_search_evaluation(self, count: int = 1):
        """Record beam search evaluations"""
        self.beam_search_evaluations += count
    
    def record_state_transition(self):
        """Record state transition"""
        self.state_transitions += 1
    
    def record_checkpoint(self):
        """Record checkpoint creation"""
        self.checkpoints_created += 1
    
    def record_recovery_attempt(self):
        """Record recovery attempt"""
        self.recovery_attempts += 1
    
    def get_total_duration(self) -> Optional[float]:
        """Get total workflow duration in milliseconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return None
    
    def get_node_performance(self, node_name: str) -> Dict[str, Any]:
        """Get performance metrics for specific node"""
        execution_times = self.node_execution_times.get(node_name, [])
        success_count = self.node_success_counts.get(node_name, 0)
        failure_count = self.node_failure_counts.get(node_name, 0)
        total_executions = success_count + failure_count
        
        return {
            "node_name": node_name,
            "total_executions": total_executions,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": success_count / total_executions if total_executions > 0 else 0.0,
            "average_execution_time_ms": statistics.mean(execution_times) if execution_times else 0.0,
            "min_execution_time_ms": min(execution_times) if execution_times else 0.0,
            "max_execution_time_ms": max(execution_times) if execution_times else 0.0
        }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get workflow metrics summary"""
        total_duration = self.get_total_duration()
        
        # Calculate overall node performance
        all_nodes = set(self.node_execution_times.keys()) | set(self.node_success_counts.keys()) | set(self.node_failure_counts.keys())
        node_performance = {node: self.get_node_performance(node) for node in all_nodes}
        
        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_ms": total_duration,
            "iterations": self.iterations,
            "beam_search_evaluations": self.beam_search_evaluations,
            "state_transitions": self.state_transitions,
            "checkpoints_created": self.checkpoints_created,
            "recovery_attempts": self.recovery_attempts,
            "node_performance": node_performance,
            "total_nodes": len(all_nodes)
        }


class PerformanceTracker:
    """Tracks performance of operations with timing"""
    
    def __init__(self, name: str, metrics_collector: Optional['MetricsCollector'] = None):
        self.name = name
        self.metrics_collector = metrics_collector
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.metadata: Dict[str, Any] = {}
        self.success: bool = True
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        
        if exc_type is not None:
            self.success = False
        
        duration_ms = (self.end_time - self.start_time) * 1000
        
        # Record metrics if collector is available
        if self.metrics_collector:
            self.metrics_collector.record_timer(
                name=f"{self.name}_duration",
                duration_ms=duration_ms,
                labels={"operation": self.name, "success": str(self.success)},
                metadata=self.metadata
            )
        
        # Log performance
        logger.log_performance(
            operation=self.name,
            duration_ms=duration_ms,
            success=self.success,
            metadata=self.metadata
        )
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to performance tracking"""
        self.metadata[key] = value
    
    def mark_failure(self):
        """Mark operation as failed"""
        self.success = False


class MetricsCollector:
    """Central metrics collection and management system"""
    
    def __init__(self):
        self.metrics: Dict[str, MetricSeries] = {}
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.workflow_metrics: Dict[str, WorkflowMetrics] = {}
        
        # System metrics
        self.system_metrics: Dict[str, float] = {}
        
        # Metric callbacks
        self.metric_callbacks: List[Callable[[str, float, Dict[str, str]], None]] = []
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Background collection
        self.collection_enabled = True
        self.collection_interval = 30  # seconds
        self.collection_thread: Optional[threading.Thread] = None
        self.stop_collection = threading.Event()
    
    def start_collection(self):
        """Start background metrics collection"""
        if self.collection_thread and self.collection_thread.is_alive():
            logger.warning("Metrics collection already started")
            return
        
        self.stop_collection.clear()
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
        
        logger.info("Metrics collection started")
    
    def stop_collection(self):
        """Stop background metrics collection"""
        self.stop_collection.set()
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        
        logger.info("Metrics collection stopped")
    
    def add_metric_callback(self, callback: Callable[[str, float, Dict[str, str]], None]):
        """Add callback for metric updates"""
        self.metric_callbacks.append(callback)
    
    def record_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record counter metric"""
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = MetricSeries(name=name, metric_type=MetricType.COUNTER)
            
            self.metrics[name].add_value(value, labels, metadata)
            
            # Notify callbacks
            for callback in self.metric_callbacks:
                try:
                    callback(name, value, labels or {})
                except Exception as e:
                    logger.error(f"Metric callback failed: {e}")
    
    def record_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record gauge metric"""
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = MetricSeries(name=name, metric_type=MetricType.GAUGE)
            
            self.metrics[name].add_value(value, labels, metadata)
            
            # Notify callbacks
            for callback in self.metric_callbacks:
                try:
                    callback(name, value, labels or {})
                except Exception as e:
                    logger.error(f"Metric callback failed: {e}")
    
    def record_timer(
        self,
        name: str,
        duration_ms: float,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record timer metric"""
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = MetricSeries(name=name, metric_type=MetricType.TIMER)
            
            self.metrics[name].add_value(duration_ms, labels, metadata)
            
            # Notify callbacks
            for callback in self.metric_callbacks:
                try:
                    callback(name, duration_ms, labels or {})
                except Exception as e:
                    logger.error(f"Metric callback failed: {e}")
    
    def record_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record histogram metric"""
        with self._lock:
            if name not in self.metrics:
                self.metrics[name] = MetricSeries(name=name, metric_type=MetricType.HISTOGRAM)
            
            self.metrics[name].add_value(value, labels, metadata)
            
            # Notify callbacks
            for callback in self.metric_callbacks:
                try:
                    callback(name, value, labels or {})
                except Exception as e:
                    logger.error(f"Metric callback failed: {e}")
    
    def get_agent_metrics(self, agent_name: str) -> AgentMetrics:
        """Get or create agent metrics"""
        with self._lock:
            if agent_name not in self.agent_metrics:
                self.agent_metrics[agent_name] = AgentMetrics(agent_name=agent_name)
            return self.agent_metrics[agent_name]
    
    def get_workflow_metrics(self, workflow_id: str, workflow_type: str = "unknown") -> WorkflowMetrics:
        """Get or create workflow metrics"""
        with self._lock:
            if workflow_id not in self.workflow_metrics:
                self.workflow_metrics[workflow_id] = WorkflowMetrics(
                    workflow_id=workflow_id,
                    workflow_type=workflow_type
                )
            return self.workflow_metrics[workflow_id]
    
    def create_performance_tracker(self, name: str) -> PerformanceTracker:
        """Create performance tracker"""
        return PerformanceTracker(name=name, metrics_collector=self)
    
    def get_metric_value(
        self,
        name: str,
        aggregation: AggregationType = AggregationType.AVERAGE,
        window_minutes: Optional[int] = None
    ) -> Optional[float]:
        """Get aggregated metric value"""
        with self._lock:
            if name not in self.metrics:
                return None
            
            return self.metrics[name].aggregate(aggregation, window_minutes)
    
    def get_metrics_summary(self, window_minutes: int = 60) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        with self._lock:
            # System metrics
            system_summary = {}
            for name, series in self.metrics.items():
                latest_value = series.get_latest_value()
                avg_value = series.aggregate(AggregationType.AVERAGE, window_minutes)
                
                system_summary[name] = {
                    "latest": latest_value,
                    "average": avg_value,
                    "type": series.metric_type.value
                }
            
            # Agent metrics
            agent_summary = {}
            for agent_name, metrics in self.agent_metrics.items():
                agent_summary[agent_name] = metrics.get_metrics_summary()
            
            # Workflow metrics
            workflow_summary = {}
            for workflow_id, metrics in self.workflow_metrics.items():
                workflow_summary[workflow_id] = metrics.get_metrics_summary()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "window_minutes": window_minutes,
                "system_metrics": system_summary,
                "agent_metrics": agent_summary,
                "workflow_metrics": workflow_summary,
                "total_agents": len(self.agent_metrics),
                "total_workflows": len(self.workflow_metrics),
                "total_metrics": len(self.metrics)
            }
    
    def export_metrics(self, format_type: str = "json") -> str:
        """Export metrics in specified format"""
        summary = self.get_metrics_summary()
        
        if format_type == "json":
            return json.dumps(summary, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _collection_loop(self):
        """Background metrics collection loop"""
        while not self.stop_collection.wait(self.collection_interval):
            try:
                # Collect system metrics
                self._collect_system_metrics()
                
                # Clean up old metrics
                self._cleanup_old_metrics()
                
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
    
    def _collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            import psutil
            
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            self.record_gauge("system_cpu_percent", cpu_percent)
            self.record_gauge("system_memory_percent", memory.percent)
            self.record_gauge("system_memory_available_gb", memory.available / (1024**3))
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.record_gauge("system_disk_percent", disk.percent)
            self.record_gauge("system_disk_free_gb", disk.free / (1024**3))
            
            # Process metrics
            process = psutil.Process()
            self.record_gauge("process_cpu_percent", process.cpu_percent())
            self.record_gauge("process_memory_mb", process.memory_info().rss / (1024**2))
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
    
    def _cleanup_old_metrics(self):
        """Clean up old metric data"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        with self._lock:
            # Clean up old workflow metrics
            workflows_to_remove = []
            for workflow_id, metrics in self.workflow_metrics.items():
                if (metrics.end_time and metrics.end_time < cutoff_time) or \
                   (metrics.start_time and metrics.start_time < cutoff_time and not metrics.end_time):
                    workflows_to_remove.append(workflow_id)
            
            for workflow_id in workflows_to_remove:
                del self.workflow_metrics[workflow_id]
            
            logger.debug(f"Cleaned up {len(workflows_to_remove)} old workflow metrics")


# Global metrics collector
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


# Convenience functions
def record_counter(name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
    """Record counter metric"""
    collector = get_metrics_collector()
    collector.record_counter(name, value, labels)


def record_gauge(name: str, value: float, labels: Optional[Dict[str, str]] = None):
    """Record gauge metric"""
    collector = get_metrics_collector()
    collector.record_gauge(name, value, labels)


def record_timer(name: str, duration_ms: float, labels: Optional[Dict[str, str]] = None):
    """Record timer metric"""
    collector = get_metrics_collector()
    collector.record_timer(name, duration_ms, labels)


def track_performance(name: str) -> PerformanceTracker:
    """Create performance tracker"""
    collector = get_metrics_collector()
    return collector.create_performance_tracker(name)


def get_agent_metrics(agent_name: str) -> AgentMetrics:
    """Get agent metrics"""
    collector = get_metrics_collector()
    return collector.get_agent_metrics(agent_name)


def get_workflow_metrics(workflow_id: str, workflow_type: str = "unknown") -> WorkflowMetrics:
    """Get workflow metrics"""
    collector = get_metrics_collector()
    return collector.get_workflow_metrics(workflow_id, workflow_type)


# Decorator for automatic performance tracking
def track_performance_decorator(
    metric_name: Optional[str] = None,
    labels: Optional[Dict[str, str]] = None
):
    """Decorator for automatic performance tracking"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            name = metric_name or f"{func.__module__}.{func.__name__}"
            
            with track_performance(name) as tracker:
                if labels:
                    for key, value in labels.items():
                        tracker.add_metadata(key, value)
                
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Initialize default metrics collection
def setup_default_metrics():
    """Setup default metrics collection"""
    collector = get_metrics_collector()
    collector.start_collection()
    
    logger.info("Default metrics collection setup completed")