"""
Agent performance tracking utilities for monitoring and optimization.
Provides comprehensive tracking of agent execution metrics and system performance.
"""

import time
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from uuid import UUID
from contextlib import contextmanager
from dataclasses import dataclass
from sqlalchemy import select, func, and_, desc
from sqlalchemy.exc import SQLAlchemyError

from .connection import get_sync_session, get_async_session
from .models import AgentPerformance, WorkflowMetrics, EventPlan, SystemHealth
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class AgentExecutionMetrics:
    """Data class for agent execution metrics"""
    agent_name: str
    task_name: str
    execution_time_ms: int
    success: bool
    error_message: Optional[str] = None
    input_size: Optional[int] = None
    output_size: Optional[int] = None
    memory_usage_mb: Optional[float] = None


@dataclass
class WorkflowExecutionMetrics:
    """Data class for workflow execution metrics"""
    total_iterations: int
    total_execution_time_ms: int
    combinations_evaluated: int
    final_score: Optional[float] = None
    beam_width_used: int = 3
    convergence_iteration: Optional[int] = None
    error_count: int = 0
    retry_count: int = 0


class AgentPerformanceTracker:
    """
    Tracks and analyzes agent performance metrics.
    Provides detailed monitoring of individual agent tasks and overall workflow performance.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.enable_detailed_tracking = getattr(self.settings, 'enable_detailed_performance_tracking', True)
        self.max_metrics_age_days = getattr(self.settings, 'max_performance_metrics_age_days', 30)
    
    @contextmanager
    def track_agent_execution(
        self,
        plan_id: str,
        agent_name: str,
        task_name: str,
        input_data: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for tracking agent execution time and performance
        
        Usage:
            with tracker.track_agent_execution(plan_id, "BudgetingAgent", "calculate_fitness"):
                # Agent execution code here
                result = agent.execute_task()
        """
        start_time = time.time()
        start_memory = self._get_memory_usage() if self.enable_detailed_tracking else None
        
        success = False
        error_message = None
        output_data = None
        
        try:
            yield
            success = True
        except Exception as e:
            error_message = str(e)
            logger.error(f"Agent {agent_name} task {task_name} failed: {e}")
            raise
        finally:
            end_time = time.time()
            execution_time_ms = int((end_time - start_time) * 1000)
            end_memory = self._get_memory_usage() if self.enable_detailed_tracking else None
            
            # Calculate memory usage delta
            memory_usage_mb = None
            if start_memory is not None and end_memory is not None:
                memory_usage_mb = end_memory - start_memory
            
            # Record performance metrics
            self.record_agent_performance(
                plan_id=plan_id,
                agent_name=agent_name,
                task_name=task_name,
                execution_time_ms=execution_time_ms,
                success=success,
                error_message=error_message,
                input_data=input_data,
                output_data=output_data,
                memory_usage_mb=memory_usage_mb
            )
    
    def record_agent_performance(
        self,
        plan_id: str,
        agent_name: str,
        task_name: str,
        execution_time_ms: int,
        success: bool,
        error_message: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        memory_usage_mb: Optional[float] = None
    ) -> bool:
        """
        Record agent performance metrics to database
        
        Args:
            plan_id: Plan identifier
            agent_name: Name of the agent
            task_name: Name of the task executed
            execution_time_ms: Execution time in milliseconds
            success: Whether the task succeeded
            error_message: Error message if task failed
            input_data: Task input data (for analysis)
            output_data: Task output data (for analysis)
            memory_usage_mb: Memory usage in MB
        
        Returns:
            True if recording successful, False otherwise
        """
        try:
            plan_uuid = UUID(plan_id)
            
            # Limit input/output data size to prevent database bloat
            if input_data and len(str(input_data)) > 10000:
                input_data = {"_truncated": True, "size": len(str(input_data))}
            
            if output_data and len(str(output_data)) > 10000:
                output_data = {"_truncated": True, "size": len(str(output_data))}
            
            with get_sync_session() as session:
                performance_record = AgentPerformance(
                    plan_id=plan_uuid,
                    agent_name=agent_name,
                    task_name=task_name,
                    execution_time_ms=execution_time_ms,
                    success=success,
                    error_message=error_message,
                    input_data=input_data,
                    output_data=output_data
                )
                
                # Add memory usage to input_data if available
                if memory_usage_mb is not None:
                    if not performance_record.input_data:
                        performance_record.input_data = {}
                    performance_record.input_data['memory_usage_mb'] = memory_usage_mb
                
                session.add(performance_record)
                session.commit()
                
                logger.debug(f"Recorded performance for {agent_name}.{task_name}: {execution_time_ms}ms, success={success}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to record agent performance: {e}")
            return False
    
    def record_workflow_metrics(
        self,
        plan_id: str,
        metrics: WorkflowExecutionMetrics
    ) -> bool:
        """
        Record workflow-level performance metrics
        
        Args:
            plan_id: Plan identifier
            metrics: Workflow execution metrics
        
        Returns:
            True if recording successful, False otherwise
        """
        try:
            plan_uuid = UUID(plan_id)
            
            with get_sync_session() as session:
                workflow_metrics = WorkflowMetrics(
                    plan_id=plan_uuid,
                    total_iterations=metrics.total_iterations,
                    total_execution_time_ms=metrics.total_execution_time_ms,
                    combinations_evaluated=metrics.combinations_evaluated,
                    final_score=metrics.final_score,
                    beam_width_used=metrics.beam_width_used,
                    convergence_iteration=metrics.convergence_iteration,
                    error_count=metrics.error_count,
                    retry_count=metrics.retry_count
                )
                
                session.add(workflow_metrics)
                session.commit()
                
                logger.info(f"Recorded workflow metrics for plan {plan_id}: {metrics.total_execution_time_ms}ms, score={metrics.final_score}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to record workflow metrics: {e}")
            return False
    
    def get_agent_performance_stats(
        self,
        agent_name: Optional[str] = None,
        task_name: Optional[str] = None,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Get agent performance statistics
        
        Args:
            agent_name: Filter by agent name (optional)
            task_name: Filter by task name (optional)
            days_back: Number of days to look back
        
        Returns:
            Dictionary with performance statistics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            with get_sync_session() as session:
                query = select(AgentPerformance).where(AgentPerformance.created_at >= cutoff_date)
                
                if agent_name:
                    query = query.where(AgentPerformance.agent_name == agent_name)
                
                if task_name:
                    query = query.where(AgentPerformance.task_name == task_name)
                
                results = session.execute(query).scalars().all()
                
                if not results:
                    return {"message": "No performance data found"}
                
                # Calculate statistics
                total_executions = len(results)
                successful_executions = sum(1 for r in results if r.success)
                failed_executions = total_executions - successful_executions
                
                execution_times = [r.execution_time_ms for r in results if r.execution_time_ms]
                
                stats = {
                    "total_executions": total_executions,
                    "successful_executions": successful_executions,
                    "failed_executions": failed_executions,
                    "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
                    "execution_time_stats": {
                        "min_ms": min(execution_times) if execution_times else 0,
                        "max_ms": max(execution_times) if execution_times else 0,
                        "avg_ms": sum(execution_times) / len(execution_times) if execution_times else 0,
                        "total_ms": sum(execution_times) if execution_times else 0
                    },
                    "period_days": days_back
                }
                
                # Add agent-specific breakdown if not filtered by agent
                if not agent_name:
                    agent_breakdown = {}
                    for result in results:
                        agent = result.agent_name
                        if agent not in agent_breakdown:
                            agent_breakdown[agent] = {"executions": 0, "successes": 0, "total_time_ms": 0}
                        
                        agent_breakdown[agent]["executions"] += 1
                        if result.success:
                            agent_breakdown[agent]["successes"] += 1
                        if result.execution_time_ms:
                            agent_breakdown[agent]["total_time_ms"] += result.execution_time_ms
                    
                    stats["agent_breakdown"] = agent_breakdown
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get agent performance stats: {e}")
            return {"error": str(e)}
    
    def get_workflow_performance_stats(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Get workflow performance statistics
        
        Args:
            days_back: Number of days to look back
        
        Returns:
            Dictionary with workflow performance statistics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            with get_sync_session() as session:
                results = session.execute(
                    select(WorkflowMetrics).where(WorkflowMetrics.created_at >= cutoff_date)
                ).scalars().all()
                
                if not results:
                    return {"message": "No workflow performance data found"}
                
                # Calculate statistics
                total_workflows = len(results)
                execution_times = [r.total_execution_time_ms for r in results if r.total_execution_time_ms]
                iterations = [r.total_iterations for r in results if r.total_iterations]
                scores = [r.final_score for r in results if r.final_score is not None]
                
                stats = {
                    "total_workflows": total_workflows,
                    "execution_time_stats": {
                        "min_ms": min(execution_times) if execution_times else 0,
                        "max_ms": max(execution_times) if execution_times else 0,
                        "avg_ms": sum(execution_times) / len(execution_times) if execution_times else 0
                    },
                    "iteration_stats": {
                        "min": min(iterations) if iterations else 0,
                        "max": max(iterations) if iterations else 0,
                        "avg": sum(iterations) / len(iterations) if iterations else 0
                    },
                    "score_stats": {
                        "min": min(scores) if scores else 0,
                        "max": max(scores) if scores else 0,
                        "avg": sum(scores) / len(scores) if scores else 0
                    },
                    "period_days": days_back
                }
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get workflow performance stats: {e}")
            return {"error": str(e)}
    
    def get_system_health_status(self) -> Dict[str, Any]:
        """
        Get current system health status
        
        Returns:
            Dictionary with system health information
        """
        try:
            with get_sync_session() as session:
                # Get latest health check for each component
                latest_checks = session.execute(
                    select(SystemHealth)
                    .order_by(SystemHealth.component_name, desc(SystemHealth.checked_at))
                ).scalars().all()
                
                # Group by component and get latest
                component_health = {}
                for check in latest_checks:
                    if check.component_name not in component_health:
                        component_health[check.component_name] = {
                            "status": check.status,
                            "response_time_ms": check.response_time_ms,
                            "error_message": check.error_message,
                            "last_checked": check.checked_at.isoformat() if check.checked_at else None,
                            "metadata": check.metadata
                        }
                
                # Determine overall system status
                overall_status = "healthy"
                if any(comp["status"] == "unhealthy" for comp in component_health.values()):
                    overall_status = "unhealthy"
                elif any(comp["status"] == "degraded" for comp in component_health.values()):
                    overall_status = "degraded"
                
                return {
                    "overall_status": overall_status,
                    "components": component_health,
                    "checked_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get system health status: {e}")
            return {
                "overall_status": "unknown",
                "error": str(e),
                "checked_at": datetime.utcnow().isoformat()
            }
    
    def record_system_health(
        self,
        component_name: str,
        status: str,
        response_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Record system health check result
        
        Args:
            component_name: Name of the component (e.g., 'database', 'ollama', 'mcp_server')
            status: Health status ('healthy', 'degraded', 'unhealthy')
            response_time_ms: Response time in milliseconds
            error_message: Error message if unhealthy
            metadata: Additional health check metadata
        
        Returns:
            True if recording successful, False otherwise
        """
        try:
            with get_sync_session() as session:
                health_record = SystemHealth(
                    component_name=component_name,
                    status=status,
                    response_time_ms=response_time_ms,
                    error_message=error_message,
                    metadata=metadata
                )
                
                session.add(health_record)
                session.commit()
                
                logger.debug(f"Recorded health check for {component_name}: {status}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to record system health: {e}")
            return False
    
    def cleanup_old_metrics(self) -> int:
        """
        Clean up old performance metrics to prevent database bloat
        
        Returns:
            Number of records cleaned up
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.max_metrics_age_days)
            
            with get_sync_session() as session:
                # Count records to be deleted
                old_performance_count = session.execute(
                    select(func.count(AgentPerformance.id))
                    .where(AgentPerformance.created_at < cutoff_date)
                ).scalar()
                
                old_health_count = session.execute(
                    select(func.count(SystemHealth.id))
                    .where(SystemHealth.checked_at < cutoff_date)
                ).scalar()
                
                # Delete old records
                session.execute(
                    select(AgentPerformance).where(AgentPerformance.created_at < cutoff_date)
                )
                
                session.execute(
                    select(SystemHealth).where(SystemHealth.checked_at < cutoff_date)
                )
                
                session.commit()
                
                total_cleaned = old_performance_count + old_health_count
                logger.info(f"Cleaned up {total_cleaned} old performance records")
                return total_cleaned
                
        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")
            return 0
    
    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return None
        except Exception:
            return None


# Global performance tracker instance
_performance_tracker: Optional[AgentPerformanceTracker] = None


def get_performance_tracker() -> AgentPerformanceTracker:
    """Get global agent performance tracker instance"""
    global _performance_tracker
    if _performance_tracker is None:
        _performance_tracker = AgentPerformanceTracker()
    return _performance_tracker


# Convenience functions
def track_agent_execution(plan_id: str, agent_name: str, task_name: str, input_data: Optional[Dict[str, Any]] = None):
    """Context manager for tracking agent execution"""
    return get_performance_tracker().track_agent_execution(plan_id, agent_name, task_name, input_data)


def record_agent_performance(
    plan_id: str,
    agent_name: str,
    task_name: str,
    execution_time_ms: int,
    success: bool,
    error_message: Optional[str] = None,
    input_data: Optional[Dict[str, Any]] = None,
    output_data: Optional[Dict[str, Any]] = None
) -> bool:
    """Record agent performance metrics"""
    return get_performance_tracker().record_agent_performance(
        plan_id, agent_name, task_name, execution_time_ms, success, error_message, input_data, output_data
    )


def record_workflow_metrics(plan_id: str, metrics: WorkflowExecutionMetrics) -> bool:
    """Record workflow performance metrics"""
    return get_performance_tracker().record_workflow_metrics(plan_id, metrics)


def get_system_health_status() -> Dict[str, Any]:
    """Get current system health status"""
    return get_performance_tracker().get_system_health_status()


def record_system_health(
    component_name: str,
    status: str,
    response_time_ms: Optional[int] = None,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """Record system health check result"""
    return get_performance_tracker().record_system_health(
        component_name, status, response_time_ms, error_message, metadata
    )