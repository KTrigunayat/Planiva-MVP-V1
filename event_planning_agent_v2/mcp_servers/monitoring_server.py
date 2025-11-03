"""
Monitoring MCP Server for Event Planning Agent

This MCP server provides monitoring and observability capabilities including:
- Agent interaction logging system
- Workflow performance tracking tools
- System health monitoring and reporting capabilities
"""

import json
import logging
import asyncio
import time
import psutil
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
from dataclasses import dataclass, asdict

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.types as types

from ..database.setup import DatabaseSetup
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class AgentInteraction:
    """Data class for agent interaction logging"""
    interaction_id: str
    agent_name: str
    action: str
    timestamp: datetime
    duration_ms: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class WorkflowMetrics:
    """Data class for workflow performance metrics"""
    workflow_id: str
    workflow_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration_ms: Optional[int] = None
    agent_interactions: List[str] = None
    success: bool = True
    error_message: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None


@dataclass
class SystemHealthMetrics:
    """Data class for system health metrics"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_workflows: int
    database_connections: int
    response_time_ms: float
    error_rate: float


class MonitoringServer:
    """MCP server for system monitoring and observability"""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_setup = DatabaseSetup()
        self.server = Server("monitoring-server")
        
        # In-memory storage for real-time metrics
        self.agent_interactions: deque = deque(maxlen=1000)
        self.workflow_metrics: Dict[str, WorkflowMetrics] = {}
        self.system_metrics: deque = deque(maxlen=100)
        
        # Performance tracking
        self.performance_counters = defaultdict(list)
        self.error_counters = defaultdict(int)
        
        # Background monitoring
        self.monitoring_active = False
        self.monitoring_thread = None
        
        self._setup_tools()
        self._start_background_monitoring()
    
    def _setup_tools(self):
        """Setup MCP tools for monitoring operations"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available monitoring tools"""
            return [
                Tool(
                    name="log_agent_interaction",
                    description="Log agent interactions for monitoring and analysis",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_name": {"type": "string", "description": "Name of the agent"},
                            "action": {"type": "string", "description": "Action performed by the agent"},
                            "duration_ms": {"type": "integer", "description": "Duration in milliseconds"},
                            "success": {"type": "boolean", "default": True},
                            "error_message": {"type": "string"},
                            "input_data": {"type": "object", "description": "Input data for the action"},
                            "output_data": {"type": "object", "description": "Output data from the action"},
                            "metadata": {"type": "object", "description": "Additional metadata"}
                        },
                        "required": ["agent_name", "action"]
                    }
                ),
                Tool(
                    name="track_workflow_performance",
                    description="Track workflow performance metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {"type": "string"},
                            "workflow_type": {"type": "string"},
                            "action": {
                                "type": "string", 
                                "enum": ["start", "update", "complete", "error"],
                                "description": "Workflow tracking action"
                            },
                            "agent_interactions": {
                                "type": "array", 
                                "items": {"type": "string"},
                                "description": "List of agent interaction IDs"
                            },
                            "performance_metrics": {"type": "object"},
                            "error_message": {"type": "string"}
                        },
                        "required": ["workflow_id", "workflow_type", "action"]
                    }
                ),
                Tool(
                    name="generate_health_report",
                    description="Generate comprehensive system health report",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "report_type": {
                                "type": "string",
                                "enum": ["summary", "detailed", "performance", "errors"],
                                "default": "summary"
                            },
                            "time_range_hours": {"type": "integer", "default": 24},
                            "include_predictions": {"type": "boolean", "default": False}
                        }
                    }
                ),
                Tool(
                    name="get_agent_performance_stats",
                    description="Get performance statistics for specific agents",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "agent_names": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of agent names to analyze"
                            },
                            "time_range_hours": {"type": "integer", "default": 24},
                            "metrics": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["response_time", "success_rate", "error_rate", "throughput"]
                                },
                                "default": ["response_time", "success_rate"]
                            }
                        }
                    }
                ),
                Tool(
                    name="get_workflow_analytics",
                    description="Get analytics for workflow performance",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_types": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Types of workflows to analyze"
                            },
                            "time_range_hours": {"type": "integer", "default": 24},
                            "analysis_type": {
                                "type": "string",
                                "enum": ["performance", "bottlenecks", "trends"],
                                "default": "performance"
                            }
                        }
                    }
                ),
                Tool(
                    name="set_alert_thresholds",
                    description="Set monitoring alert thresholds",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "thresholds": {
                                "type": "object",
                                "properties": {
                                    "cpu_usage_percent": {"type": "number", "default": 80},
                                    "memory_usage_percent": {"type": "number", "default": 85},
                                    "response_time_ms": {"type": "number", "default": 5000},
                                    "error_rate_percent": {"type": "number", "default": 5}
                                }
                            },
                            "notification_channels": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Channels for alert notifications"
                            }
                        },
                        "required": ["thresholds"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Handle tool calls"""
            try:
                if name == "log_agent_interaction":
                    result = await self.log_agent_interaction(**arguments)
                elif name == "track_workflow_performance":
                    result = await self.track_workflow_performance(**arguments)
                elif name == "generate_health_report":
                    result = await self.generate_health_report(**arguments)
                elif name == "get_agent_performance_stats":
                    result = await self.get_agent_performance_stats(**arguments)
                elif name == "get_workflow_analytics":
                    result = await self.get_workflow_analytics(**arguments)
                elif name == "set_alert_thresholds":
                    result = await self.set_alert_thresholds(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
                
            except Exception as e:
                logger.error(f"Tool call failed for {name}: {e}")
                return [types.TextContent(
                    type="text", 
                    text=json.dumps({"error": str(e), "tool": name})
                )]
    
    def _start_background_monitoring(self):
        """Start background system monitoring"""
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._background_monitor, daemon=True)
        self.monitoring_thread.start()
        logger.info("Background system monitoring started")
    
    def _background_monitor(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                metrics = self._collect_system_metrics()
                self.system_metrics.append(metrics)
                
                # Check for alerts
                self._check_alert_conditions(metrics)
                
                # Cleanup old data
                self._cleanup_old_data()
                
                # Sleep for monitoring interval
                time.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logger.error(f"Background monitoring error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _collect_system_metrics(self) -> SystemHealthMetrics:
        """Collect current system health metrics"""
        
        # CPU and memory usage
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Application-specific metrics
        active_workflows = len(self.workflow_metrics)
        
        # Database connections (simulated)
        db_connections = 5  # In practice, get from connection pool
        
        # Response time (average from recent interactions)
        recent_interactions = list(self.agent_interactions)[-10:]
        if recent_interactions:
            response_times = [i.duration_ms for i in recent_interactions if i.duration_ms]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        else:
            avg_response_time = 0
        
        # Error rate (from recent interactions)
        if recent_interactions:
            error_count = sum(1 for i in recent_interactions if not i.success)
            error_rate = (error_count / len(recent_interactions)) * 100
        else:
            error_rate = 0
        
        return SystemHealthMetrics(
            timestamp=datetime.now(),
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            disk_usage=disk.percent,
            active_workflows=active_workflows,
            database_connections=db_connections,
            response_time_ms=avg_response_time,
            error_rate=error_rate
        )
    
    def _check_alert_conditions(self, metrics: SystemHealthMetrics):
        """Check if any alert conditions are met"""
        
        # Default thresholds (can be configured via set_alert_thresholds)
        thresholds = {
            "cpu_usage_percent": 80,
            "memory_usage_percent": 85,
            "response_time_ms": 5000,
            "error_rate_percent": 5
        }
        
        alerts = []
        
        if metrics.cpu_usage > thresholds["cpu_usage_percent"]:
            alerts.append(f"High CPU usage: {metrics.cpu_usage:.1f}%")
        
        if metrics.memory_usage > thresholds["memory_usage_percent"]:
            alerts.append(f"High memory usage: {metrics.memory_usage:.1f}%")
        
        if metrics.response_time_ms > thresholds["response_time_ms"]:
            alerts.append(f"High response time: {metrics.response_time_ms:.0f}ms")
        
        if metrics.error_rate > thresholds["error_rate_percent"]:
            alerts.append(f"High error rate: {metrics.error_rate:.1f}%")
        
        if alerts:
            logger.warning(f"System alerts: {'; '.join(alerts)}")
            # In practice, send to notification channels
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        
        # Remove old workflow metrics (older than 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        workflows_to_remove = []
        for workflow_id, metrics in self.workflow_metrics.items():
            if metrics.start_time < cutoff_time:
                workflows_to_remove.append(workflow_id)
        
        for workflow_id in workflows_to_remove:
            del self.workflow_metrics[workflow_id]
        
        # Performance counters cleanup is handled by deque maxlen
    
    async def log_agent_interaction(
        self,
        agent_name: str,
        action: str,
        duration_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log agent interactions for monitoring and analysis"""
        
        try:
            # Generate unique interaction ID
            interaction_id = f"{agent_name}_{action}_{int(time.time() * 1000)}"
            
            # Create interaction record
            interaction = AgentInteraction(
                interaction_id=interaction_id,
                agent_name=agent_name,
                action=action,
                timestamp=datetime.now(),
                duration_ms=duration_ms,
                success=success,
                error_message=error_message,
                input_data=input_data,
                output_data=output_data,
                metadata=metadata
            )
            
            # Store in memory for real-time access
            self.agent_interactions.append(interaction)
            
            # Update performance counters
            self.performance_counters[agent_name].append({
                "action": action,
                "duration_ms": duration_ms,
                "success": success,
                "timestamp": interaction.timestamp
            })
            
            if not success:
                self.error_counters[agent_name] += 1
            
            # Persist to database
            await self._persist_agent_interaction(interaction)
            
            return {
                "interaction_id": interaction_id,
                "logged_at": interaction.timestamp.isoformat(),
                "status": "success",
                "message": f"Logged {action} for {agent_name}"
            }
            
        except Exception as e:
            logger.error(f"Failed to log agent interaction: {e}")
            raise
    
    async def _persist_agent_interaction(self, interaction: AgentInteraction):
        """Persist agent interaction to database"""
        
        try:
            with self.db_setup.get_session() as session:
                # Insert into agent_performance table
                insert_query = """
                INSERT INTO agent_performance 
                (plan_id, agent_name, task_name, execution_time_ms, success, error_message, created_at)
                VALUES (NULL, %s, %s, %s, %s, %s, %s)
                """
                
                session.execute(insert_query, (
                    interaction.agent_name,
                    interaction.action,
                    interaction.duration_ms,
                    interaction.success,
                    interaction.error_message,
                    interaction.timestamp
                ))
                
        except Exception as e:
            logger.warning(f"Failed to persist agent interaction to database: {e}")
    
    async def track_workflow_performance(
        self,
        workflow_id: str,
        workflow_type: str,
        action: str,
        agent_interactions: Optional[List[str]] = None,
        performance_metrics: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Track workflow performance metrics"""
        
        try:
            current_time = datetime.now()
            
            if action == "start":
                # Start new workflow tracking
                workflow_metrics = WorkflowMetrics(
                    workflow_id=workflow_id,
                    workflow_type=workflow_type,
                    start_time=current_time,
                    agent_interactions=agent_interactions or []
                )
                self.workflow_metrics[workflow_id] = workflow_metrics
                
                result = {
                    "workflow_id": workflow_id,
                    "action": "started",
                    "start_time": current_time.isoformat()
                }
                
            elif action in ["update", "complete", "error"]:
                # Update existing workflow
                if workflow_id not in self.workflow_metrics:
                    raise ValueError(f"Workflow {workflow_id} not found")
                
                workflow_metrics = self.workflow_metrics[workflow_id]
                
                if action == "update":
                    if agent_interactions:
                        workflow_metrics.agent_interactions.extend(agent_interactions)
                    if performance_metrics:
                        if not workflow_metrics.performance_metrics:
                            workflow_metrics.performance_metrics = {}
                        workflow_metrics.performance_metrics.update(performance_metrics)
                
                elif action in ["complete", "error"]:
                    workflow_metrics.end_time = current_time
                    workflow_metrics.total_duration_ms = int(
                        (current_time - workflow_metrics.start_time).total_seconds() * 1000
                    )
                    workflow_metrics.success = (action == "complete")
                    if error_message:
                        workflow_metrics.error_message = error_message
                    
                    # Persist to database
                    await self._persist_workflow_metrics(workflow_metrics)
                
                result = {
                    "workflow_id": workflow_id,
                    "action": action,
                    "updated_at": current_time.isoformat()
                }
                
                if action in ["complete", "error"]:
                    result["total_duration_ms"] = workflow_metrics.total_duration_ms
                    result["success"] = workflow_metrics.success
            
            else:
                raise ValueError(f"Unknown workflow action: {action}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to track workflow performance: {e}")
            raise
    
    async def _persist_workflow_metrics(self, workflow_metrics: WorkflowMetrics):
        """Persist workflow metrics to database"""
        
        try:
            with self.db_setup.get_session() as session:
                # Insert into workflow_metrics table
                insert_query = """
                INSERT INTO workflow_metrics 
                (plan_id, total_iterations, total_execution_time_ms, combinations_evaluated, final_score, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                # Extract metrics from performance_metrics
                performance = workflow_metrics.performance_metrics or {}
                iterations = performance.get("iterations", 1)
                combinations = performance.get("combinations_evaluated", 0)
                final_score = performance.get("final_score", 0.0)
                
                session.execute(insert_query, (
                    workflow_metrics.workflow_id,
                    iterations,
                    workflow_metrics.total_duration_ms,
                    combinations,
                    final_score,
                    workflow_metrics.end_time
                ))
                
        except Exception as e:
            logger.warning(f"Failed to persist workflow metrics to database: {e}")
    
    async def generate_health_report(
        self,
        report_type: str = "summary",
        time_range_hours: int = 24,
        include_predictions: bool = False
    ) -> Dict[str, Any]:
        """Generate comprehensive system health report"""
        
        try:
            current_time = datetime.now()
            cutoff_time = current_time - timedelta(hours=time_range_hours)
            
            # Get recent system metrics
            recent_metrics = [m for m in self.system_metrics if m.timestamp >= cutoff_time]
            
            # Get recent agent interactions
            recent_interactions = [i for i in self.agent_interactions if i.timestamp >= cutoff_time]
            
            # Get recent workflow metrics
            recent_workflows = [w for w in self.workflow_metrics.values() if w.start_time >= cutoff_time]
            
            # Generate report based on type
            if report_type == "summary":
                report = await self._generate_summary_report(recent_metrics, recent_interactions, recent_workflows)
            elif report_type == "detailed":
                report = await self._generate_detailed_report(recent_metrics, recent_interactions, recent_workflows)
            elif report_type == "performance":
                report = await self._generate_performance_report(recent_interactions, recent_workflows)
            elif report_type == "errors":
                report = await self._generate_error_report(recent_interactions, recent_workflows)
            else:
                raise ValueError(f"Unknown report type: {report_type}")
            
            # Add predictions if requested
            if include_predictions:
                report["predictions"] = await self._generate_predictions(recent_metrics, recent_interactions)
            
            # Add metadata
            report["report_metadata"] = {
                "report_type": report_type,
                "time_range_hours": time_range_hours,
                "generated_at": current_time.isoformat(),
                "data_points": {
                    "system_metrics": len(recent_metrics),
                    "agent_interactions": len(recent_interactions),
                    "workflows": len(recent_workflows)
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate health report: {e}")
            raise
    
    async def _generate_summary_report(
        self, 
        metrics: List[SystemHealthMetrics], 
        interactions: List[AgentInteraction], 
        workflows: List[WorkflowMetrics]
    ) -> Dict[str, Any]:
        """Generate summary health report"""
        
        # System health summary
        if metrics:
            latest_metrics = metrics[-1]
            avg_cpu = sum(m.cpu_usage for m in metrics) / len(metrics)
            avg_memory = sum(m.memory_usage for m in metrics) / len(metrics)
            avg_response_time = sum(m.response_time_ms for m in metrics) / len(metrics)
        else:
            latest_metrics = None
            avg_cpu = avg_memory = avg_response_time = 0
        
        # Agent activity summary
        agent_stats = defaultdict(lambda: {"interactions": 0, "errors": 0, "avg_duration": 0})
        
        for interaction in interactions:
            agent_stats[interaction.agent_name]["interactions"] += 1
            if not interaction.success:
                agent_stats[interaction.agent_name]["errors"] += 1
            if interaction.duration_ms:
                current_avg = agent_stats[interaction.agent_name]["avg_duration"]
                count = agent_stats[interaction.agent_name]["interactions"]
                agent_stats[interaction.agent_name]["avg_duration"] = (
                    (current_avg * (count - 1) + interaction.duration_ms) / count
                )
        
        # Workflow summary
        completed_workflows = [w for w in workflows if w.end_time]
        successful_workflows = [w for w in completed_workflows if w.success]
        
        return {
            "system_health": {
                "status": "healthy" if latest_metrics and latest_metrics.cpu_usage < 80 else "warning",
                "current_cpu_usage": latest_metrics.cpu_usage if latest_metrics else 0,
                "current_memory_usage": latest_metrics.memory_usage if latest_metrics else 0,
                "average_cpu_usage": avg_cpu,
                "average_memory_usage": avg_memory,
                "average_response_time_ms": avg_response_time,
                "active_workflows": len([w for w in workflows if not w.end_time])
            },
            "agent_activity": {
                "total_interactions": len(interactions),
                "unique_agents": len(agent_stats),
                "total_errors": sum(stats["errors"] for stats in agent_stats.values()),
                "agent_breakdown": dict(agent_stats)
            },
            "workflow_performance": {
                "total_workflows": len(workflows),
                "completed_workflows": len(completed_workflows),
                "successful_workflows": len(successful_workflows),
                "success_rate": (len(successful_workflows) / len(completed_workflows) * 100) if completed_workflows else 0,
                "average_duration_ms": (
                    sum(w.total_duration_ms for w in completed_workflows if w.total_duration_ms) / 
                    len(completed_workflows)
                ) if completed_workflows else 0
            }
        }
    
    async def _generate_detailed_report(
        self, 
        metrics: List[SystemHealthMetrics], 
        interactions: List[AgentInteraction], 
        workflows: List[WorkflowMetrics]
    ) -> Dict[str, Any]:
        """Generate detailed health report"""
        
        # Start with summary
        summary = await self._generate_summary_report(metrics, interactions, workflows)
        
        # Add detailed breakdowns
        detailed = {
            **summary,
            "detailed_metrics": {
                "system_trends": self._analyze_system_trends(metrics),
                "agent_performance_details": self._analyze_agent_performance(interactions),
                "workflow_analysis": self._analyze_workflow_performance(workflows),
                "error_analysis": self._analyze_errors(interactions, workflows)
            }
        }
        
        return detailed
    
    async def _generate_performance_report(
        self, 
        interactions: List[AgentInteraction], 
        workflows: List[WorkflowMetrics]
    ) -> Dict[str, Any]:
        """Generate performance-focused report"""
        
        return {
            "performance_summary": {
                "total_interactions": len(interactions),
                "average_response_time": (
                    sum(i.duration_ms for i in interactions if i.duration_ms) / 
                    len([i for i in interactions if i.duration_ms])
                ) if interactions else 0,
                "throughput_per_hour": len(interactions),
                "success_rate": (
                    sum(1 for i in interactions if i.success) / len(interactions) * 100
                ) if interactions else 0
            },
            "agent_performance": self._analyze_agent_performance(interactions),
            "workflow_performance": self._analyze_workflow_performance(workflows),
            "bottleneck_analysis": self._identify_bottlenecks(interactions, workflows)
        }
    
    async def _generate_error_report(
        self, 
        interactions: List[AgentInteraction], 
        workflows: List[WorkflowMetrics]
    ) -> Dict[str, Any]:
        """Generate error-focused report"""
        
        failed_interactions = [i for i in interactions if not i.success]
        failed_workflows = [w for w in workflows if w.end_time and not w.success]
        
        return {
            "error_summary": {
                "total_errors": len(failed_interactions) + len(failed_workflows),
                "interaction_errors": len(failed_interactions),
                "workflow_errors": len(failed_workflows),
                "error_rate": (
                    (len(failed_interactions) + len(failed_workflows)) / 
                    (len(interactions) + len(workflows)) * 100
                ) if (interactions or workflows) else 0
            },
            "error_breakdown": self._analyze_errors(interactions, workflows),
            "error_trends": self._analyze_error_trends(failed_interactions, failed_workflows),
            "recommendations": self._generate_error_recommendations(failed_interactions, failed_workflows)
        }
    
    def _analyze_system_trends(self, metrics: List[SystemHealthMetrics]) -> Dict[str, Any]:
        """Analyze system performance trends"""
        
        if len(metrics) < 2:
            return {"trend": "insufficient_data"}
        
        # Calculate trends
        cpu_trend = "stable"
        memory_trend = "stable"
        
        if len(metrics) >= 5:
            recent_cpu = [m.cpu_usage for m in metrics[-5:]]
            earlier_cpu = [m.cpu_usage for m in metrics[-10:-5]] if len(metrics) >= 10 else recent_cpu
            
            if sum(recent_cpu) / len(recent_cpu) > sum(earlier_cpu) / len(earlier_cpu) + 5:
                cpu_trend = "increasing"
            elif sum(recent_cpu) / len(recent_cpu) < sum(earlier_cpu) / len(earlier_cpu) - 5:
                cpu_trend = "decreasing"
        
        return {
            "cpu_trend": cpu_trend,
            "memory_trend": memory_trend,
            "peak_cpu": max(m.cpu_usage for m in metrics),
            "peak_memory": max(m.memory_usage for m in metrics),
            "avg_response_time": sum(m.response_time_ms for m in metrics) / len(metrics)
        }
    
    def _analyze_agent_performance(self, interactions: List[AgentInteraction]) -> Dict[str, Any]:
        """Analyze individual agent performance"""
        
        agent_analysis = {}
        
        for agent_name in set(i.agent_name for i in interactions):
            agent_interactions = [i for i in interactions if i.agent_name == agent_name]
            
            durations = [i.duration_ms for i in agent_interactions if i.duration_ms]
            successes = [i for i in agent_interactions if i.success]
            
            agent_analysis[agent_name] = {
                "total_interactions": len(agent_interactions),
                "success_rate": len(successes) / len(agent_interactions) * 100 if agent_interactions else 0,
                "average_duration_ms": sum(durations) / len(durations) if durations else 0,
                "min_duration_ms": min(durations) if durations else 0,
                "max_duration_ms": max(durations) if durations else 0,
                "error_count": len(agent_interactions) - len(successes)
            }
        
        return agent_analysis
    
    def _analyze_workflow_performance(self, workflows: List[WorkflowMetrics]) -> Dict[str, Any]:
        """Analyze workflow performance patterns"""
        
        completed = [w for w in workflows if w.end_time]
        successful = [w for w in completed if w.success]
        
        if not completed:
            return {"status": "no_completed_workflows"}
        
        durations = [w.total_duration_ms for w in completed if w.total_duration_ms]
        
        return {
            "total_workflows": len(workflows),
            "completed_workflows": len(completed),
            "success_rate": len(successful) / len(completed) * 100,
            "average_duration_ms": sum(durations) / len(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "workflow_types": list(set(w.workflow_type for w in workflows))
        }
    
    def _analyze_errors(self, interactions: List[AgentInteraction], workflows: List[WorkflowMetrics]) -> Dict[str, Any]:
        """Analyze error patterns"""
        
        failed_interactions = [i for i in interactions if not i.success]
        failed_workflows = [w for w in workflows if w.end_time and not w.success]
        
        # Group errors by type
        interaction_errors = defaultdict(int)
        workflow_errors = defaultdict(int)
        
        for interaction in failed_interactions:
            error_type = interaction.error_message or "unknown_error"
            interaction_errors[error_type] += 1
        
        for workflow in failed_workflows:
            error_type = workflow.error_message or "unknown_error"
            workflow_errors[error_type] += 1
        
        return {
            "interaction_errors": dict(interaction_errors),
            "workflow_errors": dict(workflow_errors),
            "most_common_interaction_error": max(interaction_errors.items(), key=lambda x: x[1])[0] if interaction_errors else None,
            "most_common_workflow_error": max(workflow_errors.items(), key=lambda x: x[1])[0] if workflow_errors else None
        }
    
    def _analyze_error_trends(self, failed_interactions: List[AgentInteraction], failed_workflows: List[WorkflowMetrics]) -> Dict[str, Any]:
        """Analyze error trends over time"""
        
        # Simple trend analysis
        if len(failed_interactions) < 2:
            return {"trend": "insufficient_data"}
        
        # Group by hour
        hourly_errors = defaultdict(int)
        
        for interaction in failed_interactions:
            hour = interaction.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_errors[hour] += 1
        
        for workflow in failed_workflows:
            if workflow.end_time:
                hour = workflow.end_time.replace(minute=0, second=0, microsecond=0)
                hourly_errors[hour] += 1
        
        return {
            "hourly_error_distribution": {k.isoformat(): v for k, v in hourly_errors.items()},
            "peak_error_hour": max(hourly_errors.items(), key=lambda x: x[1])[0].isoformat() if hourly_errors else None
        }
    
    def _generate_error_recommendations(self, failed_interactions: List[AgentInteraction], failed_workflows: List[WorkflowMetrics]) -> List[str]:
        """Generate recommendations based on error analysis"""
        
        recommendations = []
        
        # Analyze error patterns
        if len(failed_interactions) > len(failed_workflows) * 2:
            recommendations.append("High agent interaction failure rate - review agent error handling")
        
        if len(failed_workflows) > 0:
            recommendations.append("Workflow failures detected - implement better workflow recovery mechanisms")
        
        # Check for specific error patterns
        error_messages = [i.error_message for i in failed_interactions if i.error_message]
        
        if any("timeout" in msg.lower() for msg in error_messages):
            recommendations.append("Timeout errors detected - consider increasing timeout thresholds or optimizing performance")
        
        if any("database" in msg.lower() for msg in error_messages):
            recommendations.append("Database errors detected - check database connectivity and performance")
        
        return recommendations
    
    def _identify_bottlenecks(self, interactions: List[AgentInteraction], workflows: List[WorkflowMetrics]) -> Dict[str, Any]:
        """Identify performance bottlenecks"""
        
        bottlenecks = []
        
        # Analyze agent response times
        agent_times = defaultdict(list)
        for interaction in interactions:
            if interaction.duration_ms:
                agent_times[interaction.agent_name].append(interaction.duration_ms)
        
        for agent, times in agent_times.items():
            avg_time = sum(times) / len(times)
            if avg_time > 3000:  # 3 seconds threshold
                bottlenecks.append({
                    "type": "slow_agent",
                    "agent": agent,
                    "average_duration_ms": avg_time,
                    "severity": "high" if avg_time > 5000 else "medium"
                })
        
        # Analyze workflow durations
        completed_workflows = [w for w in workflows if w.end_time and w.total_duration_ms]
        if completed_workflows:
            avg_workflow_time = sum(w.total_duration_ms for w in completed_workflows) / len(completed_workflows)
            if avg_workflow_time > 30000:  # 30 seconds threshold
                bottlenecks.append({
                    "type": "slow_workflow",
                    "average_duration_ms": avg_workflow_time,
                    "severity": "high" if avg_workflow_time > 60000 else "medium"
                })
        
        return {
            "bottlenecks_found": len(bottlenecks),
            "bottlenecks": bottlenecks,
            "recommendations": self._generate_bottleneck_recommendations(bottlenecks)
        }
    
    def _generate_bottleneck_recommendations(self, bottlenecks: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for addressing bottlenecks"""
        
        recommendations = []
        
        for bottleneck in bottlenecks:
            if bottleneck["type"] == "slow_agent":
                recommendations.append(f"Optimize {bottleneck['agent']} agent performance - current avg: {bottleneck['average_duration_ms']:.0f}ms")
            elif bottleneck["type"] == "slow_workflow":
                recommendations.append(f"Optimize workflow execution - current avg: {bottleneck['average_duration_ms']:.0f}ms")
        
        return recommendations
    
    async def _generate_predictions(self, metrics: List[SystemHealthMetrics], interactions: List[AgentInteraction]) -> Dict[str, Any]:
        """Generate predictive insights"""
        
        # Simple trend-based predictions
        predictions = {}
        
        if len(metrics) >= 5:
            recent_cpu = [m.cpu_usage for m in metrics[-5:]]
            cpu_trend = (recent_cpu[-1] - recent_cpu[0]) / len(recent_cpu)
            
            predictions["cpu_usage_prediction"] = {
                "next_hour_estimate": min(100, max(0, recent_cpu[-1] + cpu_trend * 12)),  # 12 * 5min intervals
                "trend": "increasing" if cpu_trend > 1 else "decreasing" if cpu_trend < -1 else "stable"
            }
        
        if interactions:
            recent_errors = len([i for i in interactions[-10:] if not i.success])
            predictions["error_rate_prediction"] = {
                "risk_level": "high" if recent_errors > 3 else "medium" if recent_errors > 1 else "low",
                "recent_error_count": recent_errors
            }
        
        return predictions
    
    async def get_agent_performance_stats(
        self,
        agent_names: Optional[List[str]] = None,
        time_range_hours: int = 24,
        metrics: List[str] = None
    ) -> Dict[str, Any]:
        """Get performance statistics for specific agents"""
        
        if not metrics:
            metrics = ["response_time", "success_rate"]
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
            recent_interactions = [i for i in self.agent_interactions if i.timestamp >= cutoff_time]
            
            # Filter by agent names if specified
            if agent_names:
                recent_interactions = [i for i in recent_interactions if i.agent_name in agent_names]
            
            stats = {}
            
            for agent_name in set(i.agent_name for i in recent_interactions):
                agent_interactions = [i for i in recent_interactions if i.agent_name == agent_name]
                agent_stats = {}
                
                if "response_time" in metrics:
                    durations = [i.duration_ms for i in agent_interactions if i.duration_ms]
                    agent_stats["response_time"] = {
                        "average_ms": sum(durations) / len(durations) if durations else 0,
                        "min_ms": min(durations) if durations else 0,
                        "max_ms": max(durations) if durations else 0,
                        "p95_ms": sorted(durations)[int(len(durations) * 0.95)] if durations else 0
                    }
                
                if "success_rate" in metrics:
                    successful = sum(1 for i in agent_interactions if i.success)
                    agent_stats["success_rate"] = {
                        "percentage": (successful / len(agent_interactions) * 100) if agent_interactions else 0,
                        "successful_interactions": successful,
                        "total_interactions": len(agent_interactions)
                    }
                
                if "error_rate" in metrics:
                    errors = len(agent_interactions) - sum(1 for i in agent_interactions if i.success)
                    agent_stats["error_rate"] = {
                        "percentage": (errors / len(agent_interactions) * 100) if agent_interactions else 0,
                        "error_count": errors
                    }
                
                if "throughput" in metrics:
                    agent_stats["throughput"] = {
                        "interactions_per_hour": len(agent_interactions) / time_range_hours,
                        "total_interactions": len(agent_interactions)
                    }
                
                stats[agent_name] = agent_stats
            
            return {
                "agent_statistics": stats,
                "query_metadata": {
                    "time_range_hours": time_range_hours,
                    "metrics_requested": metrics,
                    "agents_analyzed": list(stats.keys()),
                    "total_interactions": len(recent_interactions)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get agent performance stats: {e}")
            raise
    
    async def get_workflow_analytics(
        self,
        workflow_types: Optional[List[str]] = None,
        time_range_hours: int = 24,
        analysis_type: str = "performance"
    ) -> Dict[str, Any]:
        """Get analytics for workflow performance"""
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
            recent_workflows = [w for w in self.workflow_metrics.values() if w.start_time >= cutoff_time]
            
            # Filter by workflow types if specified
            if workflow_types:
                recent_workflows = [w for w in recent_workflows if w.workflow_type in workflow_types]
            
            if analysis_type == "performance":
                analytics = self._analyze_workflow_performance(recent_workflows)
            elif analysis_type == "bottlenecks":
                analytics = self._identify_bottlenecks([], recent_workflows)
            elif analysis_type == "trends":
                analytics = self._analyze_workflow_trends(recent_workflows)
            else:
                raise ValueError(f"Unknown analysis type: {analysis_type}")
            
            analytics["query_metadata"] = {
                "analysis_type": analysis_type,
                "time_range_hours": time_range_hours,
                "workflow_types_analyzed": workflow_types or "all",
                "workflows_found": len(recent_workflows)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get workflow analytics: {e}")
            raise
    
    def _analyze_workflow_trends(self, workflows: List[WorkflowMetrics]) -> Dict[str, Any]:
        """Analyze workflow trends over time"""
        
        if len(workflows) < 2:
            return {"trend": "insufficient_data"}
        
        # Group by workflow type
        type_analysis = defaultdict(list)
        
        for workflow in workflows:
            type_analysis[workflow.workflow_type].append(workflow)
        
        trends = {}
        
        for workflow_type, type_workflows in type_analysis.items():
            completed = [w for w in type_workflows if w.end_time and w.total_duration_ms]
            
            if len(completed) >= 2:
                durations = [w.total_duration_ms for w in completed]
                success_rate = sum(1 for w in completed if w.success) / len(completed) * 100
                
                trends[workflow_type] = {
                    "average_duration_ms": sum(durations) / len(durations),
                    "success_rate": success_rate,
                    "total_workflows": len(type_workflows),
                    "completed_workflows": len(completed)
                }
        
        return {
            "workflow_type_trends": trends,
            "overall_trend": "stable"  # Simplified trend analysis
        }
    
    async def set_alert_thresholds(
        self,
        thresholds: Dict[str, float],
        notification_channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Set monitoring alert thresholds"""
        
        try:
            # Store thresholds (in practice, persist to configuration)
            self.alert_thresholds = thresholds
            self.notification_channels = notification_channels or []
            
            logger.info(f"Alert thresholds updated: {thresholds}")
            
            return {
                "status": "success",
                "thresholds_set": thresholds,
                "notification_channels": self.notification_channels,
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to set alert thresholds: {e}")
            raise
    
    async def run_server(self, host: str = "localhost", port: int = 8003):
        """Run the MCP server"""
        logger.info(f"Starting Monitoring MCP Server on {host}:{port}")
        
        try:
            # Initialize server
            async with self.server.run_server() as server:
                await server.serve_forever()
        finally:
            # Cleanup
            self.monitoring_active = False
            if self.monitoring_thread:
                self.monitoring_thread.join(timeout=5)


# Server instance for external usage
monitoring_server = MonitoringServer()


if __name__ == "__main__":
    import asyncio
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run server
    asyncio.run(monitoring_server.run_server())