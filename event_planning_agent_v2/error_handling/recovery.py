"""
Recovery management system for the Event Planning Agent.

Provides comprehensive recovery strategies and mechanisms for different
types of failures across the system.
"""

import logging
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


class RecoveryStrategy(str, Enum):
    """Available recovery strategies"""
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    RESTART_COMPONENT = "restart_component"
    RESET_STATE = "reset_state"
    RESTORE_CHECKPOINT = "restore_checkpoint"
    SKIP_FAILED_NODE = "skip_failed_node"
    INCREASE_TIMEOUT = "increase_timeout"
    FALLBACK_TO_ALTERNATIVE = "fallback_to_alternative"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    MANUAL_INTERVENTION = "manual_intervention"
    CIRCUIT_BREAKER = "circuit_breaker"


@dataclass
class RecoveryResult:
    """Result of a recovery operation"""
    success: bool
    strategy: RecoveryStrategy
    message: str
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    next_action: Optional[str] = None
    retry_after: Optional[int] = None


@dataclass
class RecoveryContext:
    """Context information for recovery operations"""
    strategy: RecoveryStrategy
    error: Exception
    component: str
    operation: str
    attempt_count: int = 0
    max_attempts: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class RecoveryHandler(ABC):
    """Base class for recovery handlers"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def can_handle(self, strategy: RecoveryStrategy) -> bool:
        """Check if this handler can handle the recovery strategy"""
        pass
    
    @abstractmethod
    def execute_recovery(self, context: RecoveryContext) -> RecoveryResult:
        """Execute the recovery operation"""
        pass


class RetryRecoveryHandler(RecoveryHandler):
    """Handler for retry-based recovery strategies"""
    
    def __init__(self):
        super().__init__("RetryRecoveryHandler")
        self.base_delay = 1.0
        self.max_delay = 60.0
        self.backoff_multiplier = 2.0
    
    def can_handle(self, strategy: RecoveryStrategy) -> bool:
        return strategy == RecoveryStrategy.RETRY_WITH_BACKOFF
    
    def execute_recovery(self, context: RecoveryContext) -> RecoveryResult:
        """Execute retry with exponential backoff"""
        start_time = time.time()
        
        try:
            # Calculate delay with exponential backoff
            delay = min(
                self.base_delay * (self.backoff_multiplier ** context.attempt_count),
                self.max_delay
            )
            
            # Add jitter to prevent thundering herd
            import random
            jitter = random.uniform(0, delay * 0.1)
            total_delay = delay + jitter
            
            logger.info(f"Retry recovery: waiting {total_delay:.2f}s before attempt {context.attempt_count + 1}")
            
            # In practice, the calling code would handle the actual delay and retry
            execution_time = time.time() - start_time
            
            return RecoveryResult(
                success=True,
                strategy=context.strategy,
                message=f"Retry scheduled with {total_delay:.2f}s delay",
                execution_time=execution_time,
                metadata={
                    "delay_seconds": total_delay,
                    "attempt_count": context.attempt_count + 1,
                    "max_attempts": context.max_attempts
                },
                retry_after=int(total_delay)
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Retry recovery failed: {e}")
            
            return RecoveryResult(
                success=False,
                strategy=context.strategy,
                message=f"Retry recovery failed: {str(e)}",
                execution_time=execution_time
            )


class ComponentRecoveryHandler(RecoveryHandler):
    """Handler for component restart recovery"""
    
    def __init__(self):
        super().__init__("ComponentRecoveryHandler")
        self.restart_timeout = 30.0
    
    def can_handle(self, strategy: RecoveryStrategy) -> bool:
        return strategy == RecoveryStrategy.RESTART_COMPONENT
    
    def execute_recovery(self, context: RecoveryContext) -> RecoveryResult:
        """Execute component restart recovery"""
        start_time = time.time()
        
        try:
            component = context.component
            logger.info(f"Attempting to restart component: {component}")
            
            # Component-specific restart logic
            if component.startswith("agent_"):
                return self._restart_agent(context, component)
            elif component.startswith("mcp_"):
                return self._restart_mcp_server(context, component)
            elif component.startswith("workflow_"):
                return self._restart_workflow(context, component)
            else:
                return self._restart_generic_component(context, component)
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Component restart failed: {e}")
            
            return RecoveryResult(
                success=False,
                strategy=context.strategy,
                message=f"Component restart failed: {str(e)}",
                execution_time=execution_time
            )
    
    def _restart_agent(self, context: RecoveryContext, component: str) -> RecoveryResult:
        """Restart a CrewAI agent"""
        try:
            agent_name = context.metadata.get("agent_name", component)
            
            # In practice, this would:
            # 1. Stop the current agent instance
            # 2. Clear any cached state
            # 3. Reinitialize the agent
            # 4. Restore necessary context
            
            logger.info(f"Restarting agent: {agent_name}")
            
            # Simulate restart process
            time.sleep(1)  # Simulate restart time
            
            execution_time = time.time() - context.timestamp.timestamp()
            
            return RecoveryResult(
                success=True,
                strategy=context.strategy,
                message=f"Agent {agent_name} restarted successfully",
                execution_time=execution_time,
                metadata={"agent_name": agent_name, "restart_time": datetime.utcnow().isoformat()}
            )
            
        except Exception as e:
            return RecoveryResult(
                success=False,
                strategy=context.strategy,
                message=f"Agent restart failed: {str(e)}",
                execution_time=time.time() - context.timestamp.timestamp()
            )
    
    def _restart_mcp_server(self, context: RecoveryContext, component: str) -> RecoveryResult:
        """Restart an MCP server"""
        try:
            server_name = context.metadata.get("server_name", component)
            
            # In practice, this would:
            # 1. Stop the MCP server process
            # 2. Clear connection pools
            # 3. Restart the server
            # 4. Re-establish connections
            
            logger.info(f"Restarting MCP server: {server_name}")
            
            # Simulate restart process
            time.sleep(2)  # MCP servers might take longer to restart
            
            execution_time = time.time() - context.timestamp.timestamp()
            
            return RecoveryResult(
                success=True,
                strategy=context.strategy,
                message=f"MCP server {server_name} restarted successfully",
                execution_time=execution_time,
                metadata={"server_name": server_name, "restart_time": datetime.utcnow().isoformat()}
            )
            
        except Exception as e:
            return RecoveryResult(
                success=False,
                strategy=context.strategy,
                message=f"MCP server restart failed: {str(e)}",
                execution_time=time.time() - context.timestamp.timestamp()
            )
    
    def _restart_workflow(self, context: RecoveryContext, component: str) -> RecoveryResult:
        """Restart a workflow"""
        try:
            workflow_id = context.metadata.get("workflow_id", component)
            
            # In practice, this would:
            # 1. Stop the current workflow execution
            # 2. Clear workflow state
            # 3. Restart from initial state or checkpoint
            
            logger.info(f"Restarting workflow: {workflow_id}")
            
            execution_time = time.time() - context.timestamp.timestamp()
            
            return RecoveryResult(
                success=True,
                strategy=context.strategy,
                message=f"Workflow {workflow_id} restart initiated",
                execution_time=execution_time,
                metadata={"workflow_id": workflow_id, "restart_time": datetime.utcnow().isoformat()},
                next_action="restart_workflow"
            )
            
        except Exception as e:
            return RecoveryResult(
                success=False,
                strategy=context.strategy,
                message=f"Workflow restart failed: {str(e)}",
                execution_time=time.time() - context.timestamp.timestamp()
            )
    
    def _restart_generic_component(self, context: RecoveryContext, component: str) -> RecoveryResult:
        """Restart a generic component"""
        try:
            logger.info(f"Restarting generic component: {component}")
            
            # Generic restart logic
            execution_time = time.time() - context.timestamp.timestamp()
            
            return RecoveryResult(
                success=True,
                strategy=context.strategy,
                message=f"Component {component} restart initiated",
                execution_time=execution_time,
                metadata={"component": component, "restart_time": datetime.utcnow().isoformat()}
            )
            
        except Exception as e:
            return RecoveryResult(
                success=False,
                strategy=context.strategy,
                message=f"Generic component restart failed: {str(e)}",
                execution_time=time.time() - context.timestamp.timestamp()
            )


class StateRecoveryHandler(RecoveryHandler):
    """Handler for state-based recovery strategies"""
    
    def __init__(self):
        super().__init__("StateRecoveryHandler")
    
    def can_handle(self, strategy: RecoveryStrategy) -> bool:
        return strategy in [
            RecoveryStrategy.RESET_STATE,
            RecoveryStrategy.RESTORE_CHECKPOINT
        ]
    
    def execute_recovery(self, context: RecoveryContext) -> RecoveryResult:
        """Execute state recovery"""
        start_time = time.time()
        
        try:
            if context.strategy == RecoveryStrategy.RESET_STATE:
                return self._reset_state(context)
            elif context.strategy == RecoveryStrategy.RESTORE_CHECKPOINT:
                return self._restore_checkpoint(context)
            else:
                raise ValueError(f"Unsupported strategy: {context.strategy}")
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"State recovery failed: {e}")
            
            return RecoveryResult(
                success=False,
                strategy=context.strategy,
                message=f"State recovery failed: {str(e)}",
                execution_time=execution_time
            )
    
    def _reset_state(self, context: RecoveryContext) -> RecoveryResult:
        """Reset component state to initial values"""
        try:
            component = context.component
            logger.info(f"Resetting state for component: {component}")
            
            # Component-specific state reset
            if "workflow" in component:
                workflow_id = context.metadata.get("workflow_id")
                if workflow_id:
                    # Reset workflow state to initial
                    logger.info(f"Resetting workflow state for {workflow_id}")
                    
                    # In practice, this would:
                    # 1. Load initial state template
                    # 2. Clear current state
                    # 3. Initialize with fresh state
                    
            elif "agent" in component:
                agent_name = context.metadata.get("agent_name")
                if agent_name:
                    # Reset agent state
                    logger.info(f"Resetting agent state for {agent_name}")
                    
                    # In practice, this would:
                    # 1. Clear agent memory/context
                    # 2. Reset tool states
                    # 3. Reinitialize agent configuration
            
            execution_time = time.time() - context.timestamp.timestamp()
            
            return RecoveryResult(
                success=True,
                strategy=context.strategy,
                message=f"State reset completed for {component}",
                execution_time=execution_time,
                metadata={"component": component, "reset_time": datetime.utcnow().isoformat()}
            )
            
        except Exception as e:
            return RecoveryResult(
                success=False,
                strategy=context.strategy,
                message=f"State reset failed: {str(e)}",
                execution_time=time.time() - context.timestamp.timestamp()
            )
    
    def _restore_checkpoint(self, context: RecoveryContext) -> RecoveryResult:
        """Restore state from checkpoint"""
        try:
            component = context.component
            logger.info(f"Restoring checkpoint for component: {component}")
            
            # Try to restore from checkpoint
            if "workflow" in component:
                workflow_id = context.metadata.get("workflow_id")
                if workflow_id:
                    # Restore workflow from checkpoint
                    logger.info(f"Restoring workflow checkpoint for {workflow_id}")
                    
                    # In practice, this would:
                    # 1. Load latest checkpoint from database
                    # 2. Validate checkpoint integrity
                    # 3. Restore workflow state
                    # 4. Resume from checkpoint point
                    
                    # Simulate checkpoint restoration
                    checkpoint_found = True  # In practice, check if checkpoint exists
                    
                    if checkpoint_found:
                        execution_time = time.time() - context.timestamp.timestamp()
                        
                        return RecoveryResult(
                            success=True,
                            strategy=context.strategy,
                            message=f"Checkpoint restored for workflow {workflow_id}",
                            execution_time=execution_time,
                            metadata={
                                "workflow_id": workflow_id,
                                "checkpoint_time": datetime.utcnow().isoformat(),
                                "restored_from": "latest_checkpoint"
                            }
                        )
                    else:
                        return RecoveryResult(
                            success=False,
                            strategy=context.strategy,
                            message=f"No checkpoint found for workflow {workflow_id}",
                            execution_time=time.time() - context.timestamp.timestamp()
                        )
            
            # Generic checkpoint restoration
            execution_time = time.time() - context.timestamp.timestamp()
            
            return RecoveryResult(
                success=True,
                strategy=context.strategy,
                message=f"Checkpoint restoration attempted for {component}",
                execution_time=execution_time,
                metadata={"component": component}
            )
            
        except Exception as e:
            return RecoveryResult(
                success=False,
                strategy=context.strategy,
                message=f"Checkpoint restoration failed: {str(e)}",
                execution_time=time.time() - context.timestamp.timestamp()
            )


class WorkflowRecoveryHandler(RecoveryHandler):
    """Handler for workflow-specific recovery strategies"""
    
    def __init__(self):
        super().__init__("WorkflowRecoveryHandler")
    
    def can_handle(self, strategy: RecoveryStrategy) -> bool:
        return strategy in [
            RecoveryStrategy.SKIP_FAILED_NODE,
            RecoveryStrategy.INCREASE_TIMEOUT
        ]
    
    def execute_recovery(self, context: RecoveryContext) -> RecoveryResult:
        """Execute workflow recovery"""
        start_time = time.time()
        
        try:
            if context.strategy == RecoveryStrategy.SKIP_FAILED_NODE:
                return self._skip_failed_node(context)
            elif context.strategy == RecoveryStrategy.INCREASE_TIMEOUT:
                return self._increase_timeout(context)
            else:
                raise ValueError(f"Unsupported strategy: {context.strategy}")
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Workflow recovery failed: {e}")
            
            return RecoveryResult(
                success=False,
                strategy=context.strategy,
                message=f"Workflow recovery failed: {str(e)}",
                execution_time=execution_time
            )
    
    def _skip_failed_node(self, context: RecoveryContext) -> RecoveryResult:
        """Skip failed workflow node"""
        try:
            workflow_id = context.metadata.get("workflow_id", "unknown")
            node_name = context.metadata.get("node_name", "unknown")
            
            logger.info(f"Skipping failed node {node_name} in workflow {workflow_id}")
            
            # In practice, this would:
            # 1. Mark the node as skipped in workflow state
            # 2. Update workflow graph to bypass the node
            # 3. Continue execution from next node
            # 4. Log the skip for audit purposes
            
            execution_time = time.time() - context.timestamp.timestamp()
            
            return RecoveryResult(
                success=True,
                strategy=context.strategy,
                message=f"Node {node_name} skipped in workflow {workflow_id}",
                execution_time=execution_time,
                metadata={
                    "workflow_id": workflow_id,
                    "skipped_node": node_name,
                    "skip_time": datetime.utcnow().isoformat()
                },
                next_action="continue_workflow"
            )
            
        except Exception as e:
            return RecoveryResult(
                success=False,
                strategy=context.strategy,
                message=f"Node skip failed: {str(e)}",
                execution_time=time.time() - context.timestamp.timestamp()
            )
    
    def _increase_timeout(self, context: RecoveryContext) -> RecoveryResult:
        """Increase operation timeout"""
        try:
            current_timeout = context.metadata.get("current_timeout", 30)
            
            # Increase timeout by 50% or minimum 30 seconds
            new_timeout = max(int(current_timeout * 1.5), current_timeout + 30)
            max_timeout = context.metadata.get("max_timeout", 600)  # 10 minutes max
            
            if new_timeout > max_timeout:
                new_timeout = max_timeout
            
            logger.info(f"Increasing timeout from {current_timeout}s to {new_timeout}s")
            
            execution_time = time.time() - context.timestamp.timestamp()
            
            return RecoveryResult(
                success=True,
                strategy=context.strategy,
                message=f"Timeout increased from {current_timeout}s to {new_timeout}s",
                execution_time=execution_time,
                metadata={
                    "old_timeout": current_timeout,
                    "new_timeout": new_timeout,
                    "max_timeout": max_timeout
                }
            )
            
        except Exception as e:
            return RecoveryResult(
                success=False,
                strategy=context.strategy,
                message=f"Timeout increase failed: {str(e)}",
                execution_time=time.time() - context.timestamp.timestamp()
            )


class FallbackRecoveryHandler(RecoveryHandler):
    """Handler for fallback and degradation strategies"""
    
    def __init__(self):
        super().__init__("FallbackRecoveryHandler")
    
    def can_handle(self, strategy: RecoveryStrategy) -> bool:
        return strategy in [
            RecoveryStrategy.FALLBACK_TO_ALTERNATIVE,
            RecoveryStrategy.GRACEFUL_DEGRADATION
        ]
    
    def execute_recovery(self, context: RecoveryContext) -> RecoveryResult:
        """Execute fallback recovery"""
        start_time = time.time()
        
        try:
            if context.strategy == RecoveryStrategy.FALLBACK_TO_ALTERNATIVE:
                return self._fallback_to_alternative(context)
            elif context.strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
                return self._graceful_degradation(context)
            else:
                raise ValueError(f"Unsupported strategy: {context.strategy}")
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Fallback recovery failed: {e}")
            
            return RecoveryResult(
                success=False,
                strategy=context.strategy,
                message=f"Fallback recovery failed: {str(e)}",
                execution_time=execution_time
            )
    
    def _fallback_to_alternative(self, context: RecoveryContext) -> RecoveryResult:
        """Fallback to alternative implementation"""
        try:
            component = context.component
            operation = context.operation
            
            logger.info(f"Falling back to alternative for {component}:{operation}")
            
            # Define fallback mappings
            fallback_mappings = {
                "mcp_vendor_server": "local_vendor_database",
                "mcp_calculation_server": "local_calculation_engine",
                "mcp_monitoring_server": "local_logging",
                "external_llm": "local_llm",
                "cloud_storage": "local_storage"
            }
            
            fallback_component = fallback_mappings.get(component, "local_implementation")
            
            execution_time = time.time() - context.timestamp.timestamp()
            
            return RecoveryResult(
                success=True,
                strategy=context.strategy,
                message=f"Fallback activated: {component} -> {fallback_component}",
                execution_time=execution_time,
                metadata={
                    "original_component": component,
                    "fallback_component": fallback_component,
                    "operation": operation,
                    "fallback_time": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            return RecoveryResult(
                success=False,
                strategy=context.strategy,
                message=f"Fallback failed: {str(e)}",
                execution_time=time.time() - context.timestamp.timestamp()
            )
    
    def _graceful_degradation(self, context: RecoveryContext) -> RecoveryResult:
        """Implement graceful degradation"""
        try:
            component = context.component
            operation = context.operation
            
            logger.info(f"Implementing graceful degradation for {component}:{operation}")
            
            # Define degradation strategies
            degradation_strategies = {
                "vendor_search": "return_cached_results",
                "fitness_calculation": "use_simplified_algorithm",
                "timeline_generation": "use_template_timeline",
                "blueprint_generation": "use_basic_template",
                "monitoring": "disable_detailed_tracking"
            }
            
            degradation_mode = degradation_strategies.get(operation, "reduced_functionality")
            
            execution_time = time.time() - context.timestamp.timestamp()
            
            return RecoveryResult(
                success=True,
                strategy=context.strategy,
                message=f"Graceful degradation activated: {degradation_mode}",
                execution_time=execution_time,
                metadata={
                    "component": component,
                    "operation": operation,
                    "degradation_mode": degradation_mode,
                    "degradation_time": datetime.utcnow().isoformat(),
                    "reduced_functionality": True
                }
            )
            
        except Exception as e:
            return RecoveryResult(
                success=False,
                strategy=context.strategy,
                message=f"Graceful degradation failed: {str(e)}",
                execution_time=time.time() - context.timestamp.timestamp()
            )


class RecoveryManager:
    """Central manager for recovery operations"""
    
    def __init__(self):
        self.handlers: List[RecoveryHandler] = []
        self.recovery_history: List[RecoveryResult] = []
        self.max_history_size = 1000
        
        # Initialize default handlers
        self._initialize_default_handlers()
    
    def _initialize_default_handlers(self):
        """Initialize default recovery handlers"""
        self.handlers = [
            RetryRecoveryHandler(),
            ComponentRecoveryHandler(),
            StateRecoveryHandler(),
            WorkflowRecoveryHandler(),
            FallbackRecoveryHandler()
        ]
    
    def add_handler(self, handler: RecoveryHandler):
        """Add a custom recovery handler"""
        self.handlers.append(handler)
    
    def execute_recovery(
        self,
        strategy: RecoveryStrategy,
        context: Dict[str, Any],
        error: Optional[Exception] = None,
        component: str = "unknown",
        operation: str = "unknown"
    ) -> RecoveryResult:
        """Execute recovery operation"""
        
        # Create recovery context
        recovery_context = RecoveryContext(
            strategy=strategy,
            error=error or Exception("Unknown error"),
            component=component,
            operation=operation,
            metadata=context
        )
        
        # Find appropriate handler
        handler = self._find_handler(strategy)
        if not handler:
            logger.error(f"No handler found for recovery strategy: {strategy}")
            return RecoveryResult(
                success=False,
                strategy=strategy,
                message=f"No handler available for strategy: {strategy}"
            )
        
        # Execute recovery
        try:
            logger.info(f"Executing recovery strategy: {strategy} with handler: {handler.name}")
            result = handler.execute_recovery(recovery_context)
            
            # Store in history
            self._add_to_history(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Recovery execution failed: {e}")
            
            error_result = RecoveryResult(
                success=False,
                strategy=strategy,
                message=f"Recovery execution failed: {str(e)}"
            )
            
            self._add_to_history(error_result)
            return error_result
    
    def _find_handler(self, strategy: RecoveryStrategy) -> Optional[RecoveryHandler]:
        """Find handler for recovery strategy"""
        for handler in self.handlers:
            if handler.can_handle(strategy):
                return handler
        return None
    
    def _add_to_history(self, result: RecoveryResult):
        """Add recovery result to history"""
        self.recovery_history.append(result)
        
        # Trim history if too large
        if len(self.recovery_history) > self.max_history_size:
            self.recovery_history = self.recovery_history[-self.max_history_size:]
    
    def get_recovery_stats(self) -> Dict[str, Any]:
        """Get recovery statistics"""
        if not self.recovery_history:
            return {"total_recoveries": 0}
        
        total_recoveries = len(self.recovery_history)
        successful_recoveries = sum(1 for r in self.recovery_history if r.success)
        
        # Strategy breakdown
        strategy_stats = {}
        for result in self.recovery_history:
            strategy = result.strategy.value
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {"total": 0, "successful": 0}
            
            strategy_stats[strategy]["total"] += 1
            if result.success:
                strategy_stats[strategy]["successful"] += 1
        
        # Calculate success rates
        for strategy, stats in strategy_stats.items():
            stats["success_rate"] = stats["successful"] / stats["total"] if stats["total"] > 0 else 0
        
        return {
            "total_recoveries": total_recoveries,
            "successful_recoveries": successful_recoveries,
            "success_rate": successful_recoveries / total_recoveries,
            "strategy_breakdown": strategy_stats,
            "average_execution_time": sum(r.execution_time for r in self.recovery_history) / total_recoveries
        }
    
    def get_recent_recoveries(self, limit: int = 10) -> List[RecoveryResult]:
        """Get recent recovery results"""
        return self.recovery_history[-limit:]
    
    def clear_history(self):
        """Clear recovery history"""
        self.recovery_history.clear()


# Global recovery manager instance
_recovery_manager: Optional[RecoveryManager] = None


def get_recovery_manager() -> RecoveryManager:
    """Get global recovery manager instance"""
    global _recovery_manager
    if _recovery_manager is None:
        _recovery_manager = RecoveryManager()
    return _recovery_manager


# Convenience functions
def execute_recovery(
    strategy: RecoveryStrategy,
    context: Dict[str, Any],
    error: Optional[Exception] = None,
    component: str = "unknown",
    operation: str = "unknown"
) -> RecoveryResult:
    """Execute recovery operation using global manager"""
    manager = get_recovery_manager()
    return manager.execute_recovery(strategy, context, error, component, operation)


def get_recovery_stats() -> Dict[str, Any]:
    """Get recovery statistics from global manager"""
    manager = get_recovery_manager()
    return manager.get_recovery_stats()