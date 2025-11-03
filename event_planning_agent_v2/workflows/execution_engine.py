"""
Workflow execution engine with error handling and recovery mechanisms.
Provides comprehensive workflow management, monitoring, and recovery capabilities.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime, timedelta
from uuid import uuid4
from enum import Enum
from dataclasses import dataclass, field

from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
try:
    from langgraph.checkpoint.postgres import PostgresSaver
except ImportError:
    PostgresSaver = None
from langgraph.errors import GraphRecursionError, GraphInterrupt

from .state_models import (
    EventPlanningState, 
    WorkflowStatus, 
    transition_logger,
    state_validator,
    validate_state_transition
)
from .planning_workflow import EventPlanningWorkflow, create_event_planning_workflow
from ..database.state_manager import get_state_manager
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class ExecutionMode(str, Enum):
    """Workflow execution modes"""
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    BATCH = "batch"
    STREAMING = "streaming"


class RecoveryStrategy(str, Enum):
    """Recovery strategies for workflow failures"""
    RETRY = "retry"
    ROLLBACK = "rollback"
    SKIP_NODE = "skip_node"
    MANUAL_INTERVENTION = "manual_intervention"
    RESTART = "restart"


@dataclass
class ExecutionConfig:
    """Configuration for workflow execution"""
    mode: ExecutionMode = ExecutionMode.SYNCHRONOUS
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    timeout: Optional[float] = 300.0  # 5 minutes
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY
    enable_checkpointing: bool = True
    checkpoint_interval: int = 1  # checkpoint every N nodes
    enable_monitoring: bool = True
    debug_mode: bool = False


@dataclass
class ExecutionResult:
    """Result of workflow execution"""
    plan_id: str
    success: bool
    final_state: Optional[EventPlanningState] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    nodes_executed: List[str] = field(default_factory=list)
    retries_used: int = 0
    checkpoints_created: int = 0
    recovery_actions: List[str] = field(default_factory=list)


class WorkflowExecutionEngine:
    """
    Advanced workflow execution engine with comprehensive error handling and recovery.
    
    Provides robust workflow execution with monitoring, checkpointing, and recovery
    mechanisms for the event planning workflow.
    """
    
    def __init__(self, config: Optional[ExecutionConfig] = None):
        self.config = config or ExecutionConfig()
        self.state_manager = get_state_manager()
        self.settings = get_settings()
        
        # Initialize checkpointer based on configuration
        self.checkpointer = self._initialize_checkpointer()
        
        # Workflow instances
        self._workflow_graph = None
        self._compiled_workflow = None
        
        # Execution tracking
        self.active_executions: Dict[str, ExecutionResult] = {}
        self.execution_history: List[ExecutionResult] = []
        
        # Error handling
        self.error_handlers: Dict[type, Callable] = {}
        self.recovery_handlers: Dict[RecoveryStrategy, Callable] = {}
        
        # Initialize default handlers
        self._setup_default_handlers()
    
    def _initialize_checkpointer(self):
        """Initialize appropriate checkpointer based on configuration"""
        if self.config.enable_checkpointing:
            try:
                # Try to use PostgreSQL checkpointer if available
                if PostgresSaver is not None:
                    database_url = getattr(self.settings, 'database_url', None)
                    if database_url:
                        return PostgresSaver.from_conn_string(database_url)
            except Exception as e:
                logger.warning(f"Failed to initialize PostgreSQL checkpointer: {e}")
            
            # Fallback to memory checkpointer
            return MemorySaver()
        else:
            return None
    
    def _setup_default_handlers(self):
        """Setup default error and recovery handlers"""
        # Error handlers
        self.error_handlers.update({
            GraphRecursionError: self._handle_recursion_error,
            GraphInterrupt: self._handle_graph_interrupt,
            TimeoutError: self._handle_timeout_error,
            Exception: self._handle_generic_error
        })
        
        # Recovery handlers
        self.recovery_handlers.update({
            RecoveryStrategy.RETRY: self._retry_recovery,
            RecoveryStrategy.ROLLBACK: self._rollback_recovery,
            RecoveryStrategy.SKIP_NODE: self._skip_node_recovery,
            RecoveryStrategy.MANUAL_INTERVENTION: self._manual_intervention_recovery,
            RecoveryStrategy.RESTART: self._restart_recovery
        })
    
    @property
    def workflow_graph(self) -> StateGraph:
        """Get or create workflow graph"""
        if self._workflow_graph is None:
            self._workflow_graph = create_event_planning_workflow()
        return self._workflow_graph
    
    @property
    def compiled_workflow(self):
        """Get or create compiled workflow"""
        if self._compiled_workflow is None:
            self._compiled_workflow = self.workflow_graph.compile(
                checkpointer=self.checkpointer,
                debug=self.config.debug_mode
            )
        return self._compiled_workflow
    
    def execute_workflow(
        self,
        client_request: Dict[str, Any],
        plan_id: Optional[str] = None,
        execution_config: Optional[ExecutionConfig] = None
    ) -> ExecutionResult:
        """
        Execute workflow with comprehensive error handling and recovery.
        
        Args:
            client_request: Client's event planning request
            plan_id: Optional existing plan ID
            execution_config: Optional execution configuration override
            
        Returns:
            ExecutionResult with execution details and final state
        """
        # Use provided config or default
        config = execution_config or self.config
        
        # Generate plan ID if not provided
        if plan_id is None:
            plan_id = str(uuid4())
        
        # Create execution result tracker
        result = ExecutionResult(plan_id=plan_id, success=False)
        self.active_executions[plan_id] = result
        
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting workflow execution for plan {plan_id}")
            
            # Create initial state
            from .state_models import create_initial_state
            initial_state = create_initial_state(
                client_request=client_request,
                plan_id=plan_id
            )
            
            # Execute based on mode
            if config.mode == ExecutionMode.SYNCHRONOUS:
                final_state = self._execute_synchronous(initial_state, config, result)
            elif config.mode == ExecutionMode.ASYNCHRONOUS:
                final_state = asyncio.run(self._execute_asynchronous(initial_state, config, result))
            elif config.mode == ExecutionMode.STREAMING:
                final_state = self._execute_streaming(initial_state, config, result)
            else:
                raise ValueError(f"Unsupported execution mode: {config.mode}")
            
            # Update result
            result.final_state = final_state
            result.success = final_state.get('workflow_status') == WorkflowStatus.COMPLETED.value
            result.execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Workflow execution completed for plan {plan_id} (success: {result.success})")
            
        except Exception as e:
            logger.error(f"Workflow execution failed for plan {plan_id}: {e}")
            result.error = str(e)
            result.execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Attempt recovery if configured
            if config.recovery_strategy != RecoveryStrategy.MANUAL_INTERVENTION:
                recovery_result = self._attempt_recovery(plan_id, e, config)
                if recovery_result:
                    result = recovery_result
        
        finally:
            # Move to execution history
            self.execution_history.append(result)
            if plan_id in self.active_executions:
                del self.active_executions[plan_id]
        
        return result
    
    def _execute_synchronous(
        self,
        initial_state: EventPlanningState,
        config: ExecutionConfig,
        result: ExecutionResult
    ) -> EventPlanningState:
        """Execute workflow synchronously"""
        app = self.compiled_workflow
        
        # Configure execution
        execution_config = {
            "configurable": {"thread_id": initial_state['plan_id']},
            "recursion_limit": 50
        }
        
        if config.timeout:
            # Implement timeout using threading
            import threading
            import time
            
            final_state = None
            exception = None
            
            def execute_with_timeout():
                nonlocal final_state, exception
                try:
                    final_state = app.invoke(initial_state, config=execution_config)
                except Exception as e:
                    exception = e
            
            thread = threading.Thread(target=execute_with_timeout)
            thread.start()
            thread.join(timeout=config.timeout)
            
            if thread.is_alive():
                # Timeout occurred
                raise TimeoutError(f"Workflow execution timed out after {config.timeout} seconds")
            
            if exception:
                raise exception
            
            return final_state
        else:
            # Execute without timeout
            return app.invoke(initial_state, config=execution_config)
    
    async def _execute_asynchronous(
        self,
        initial_state: EventPlanningState,
        config: ExecutionConfig,
        result: ExecutionResult
    ) -> EventPlanningState:
        """Execute workflow asynchronously"""
        app = self.compiled_workflow
        
        execution_config = {
            "configurable": {"thread_id": initial_state['plan_id']},
            "recursion_limit": 50
        }
        
        if config.timeout:
            # Use asyncio timeout
            try:
                final_state = await asyncio.wait_for(
                    asyncio.to_thread(app.invoke, initial_state, execution_config),
                    timeout=config.timeout
                )
                return final_state
            except asyncio.TimeoutError:
                raise TimeoutError(f"Workflow execution timed out after {config.timeout} seconds")
        else:
            # Execute without timeout
            return await asyncio.to_thread(app.invoke, initial_state, execution_config)
    
    def _execute_streaming(
        self,
        initial_state: EventPlanningState,
        config: ExecutionConfig,
        result: ExecutionResult
    ) -> EventPlanningState:
        """Execute workflow with streaming updates"""
        app = self.compiled_workflow
        
        execution_config = {
            "configurable": {"thread_id": initial_state['plan_id']},
            "recursion_limit": 50
        }
        
        final_state = None
        
        # Stream execution updates
        for chunk in app.stream(initial_state, config=execution_config):
            # Process streaming chunk
            if isinstance(chunk, dict):
                for node_name, node_state in chunk.items():
                    result.nodes_executed.append(node_name)
                    
                    # Create checkpoint if configured
                    if (config.enable_checkpointing and 
                        len(result.nodes_executed) % config.checkpoint_interval == 0):
                        self._create_checkpoint(node_state, result)
                    
                    # Update monitoring
                    if config.enable_monitoring:
                        self._update_monitoring(node_name, node_state, result)
                    
                    final_state = node_state
        
        return final_state or initial_state
    
    def _create_checkpoint(self, state: EventPlanningState, result: ExecutionResult):
        """Create workflow checkpoint"""
        try:
            self.state_manager.checkpoint_workflow(state)
            result.checkpoints_created += 1
            logger.debug(f"Created checkpoint for plan {state.get('plan_id')}")
        except Exception as e:
            logger.warning(f"Failed to create checkpoint: {e}")
    
    def _update_monitoring(self, node_name: str, state: EventPlanningState, result: ExecutionResult):
        """Update monitoring metrics"""
        try:
            # Log node execution
            transition_logger.log_node_entry(state, node_name)
            
            # Update performance metrics (would integrate with monitoring MCP server)
            logger.debug(f"Node {node_name} executed for plan {state.get('plan_id')}")
        except Exception as e:
            logger.warning(f"Failed to update monitoring: {e}")
    
    def _attempt_recovery(
        self,
        plan_id: str,
        error: Exception,
        config: ExecutionConfig
    ) -> Optional[ExecutionResult]:
        """Attempt workflow recovery based on strategy"""
        logger.info(f"Attempting recovery for plan {plan_id} using strategy {config.recovery_strategy}")
        
        try:
            recovery_handler = self.recovery_handlers.get(config.recovery_strategy)
            if recovery_handler:
                return recovery_handler(plan_id, error, config)
            else:
                logger.error(f"No recovery handler for strategy {config.recovery_strategy}")
                return None
        except Exception as recovery_error:
            logger.error(f"Recovery attempt failed: {recovery_error}")
            return None
    
    def _retry_recovery(
        self,
        plan_id: str,
        error: Exception,
        config: ExecutionConfig
    ) -> Optional[ExecutionResult]:
        """Retry recovery strategy"""
        result = self.active_executions.get(plan_id)
        if not result:
            return None
        
        if result.retries_used >= config.max_retries:
            logger.error(f"Max retries ({config.max_retries}) exceeded for plan {plan_id}")
            return None
        
        # Wait before retry
        import time
        time.sleep(config.retry_delay * (result.retries_used + 1))  # Exponential backoff
        
        # Load last known state
        last_state = self.state_manager.load_workflow_state(plan_id)
        if not last_state:
            logger.error(f"Cannot retry - no saved state for plan {plan_id}")
            return None
        
        # Increment retry count
        result.retries_used += 1
        result.recovery_actions.append(f"retry_{result.retries_used}")
        
        # Attempt execution again
        try:
            final_state = self._execute_synchronous(last_state, config, result)
            result.final_state = final_state
            result.success = final_state.get('workflow_status') == WorkflowStatus.COMPLETED.value
            return result
        except Exception as retry_error:
            logger.error(f"Retry {result.retries_used} failed: {retry_error}")
            return self._attempt_recovery(plan_id, retry_error, config)
    
    def _rollback_recovery(
        self,
        plan_id: str,
        error: Exception,
        config: ExecutionConfig
    ) -> Optional[ExecutionResult]:
        """Rollback recovery strategy"""
        logger.info(f"Attempting rollback recovery for plan {plan_id}")
        
        # Load previous checkpoint
        state = self.state_manager.load_workflow_state(plan_id)
        if not state:
            return None
        
        # Rollback to previous stable state
        state['workflow_status'] = WorkflowStatus.RECOVERING.value
        state['last_error'] = str(error)
        state['retry_count'] = state.get('retry_count', 0) + 1
        
        # Save recovery state
        self.state_manager.save_workflow_state(state)
        
        result = self.active_executions.get(plan_id)
        if result:
            result.recovery_actions.append("rollback_to_checkpoint")
            result.final_state = state
        
        return result
    
    def _skip_node_recovery(
        self,
        plan_id: str,
        error: Exception,
        config: ExecutionConfig
    ) -> Optional[ExecutionResult]:
        """Skip node recovery strategy"""
        logger.info(f"Attempting skip node recovery for plan {plan_id}")
        
        # This would require more sophisticated graph manipulation
        # For now, we'll treat it as a rollback
        return self._rollback_recovery(plan_id, error, config)
    
    def _manual_intervention_recovery(
        self,
        plan_id: str,
        error: Exception,
        config: ExecutionConfig
    ) -> Optional[ExecutionResult]:
        """Manual intervention recovery strategy"""
        logger.info(f"Manual intervention required for plan {plan_id}")
        
        # Update state to indicate manual intervention needed
        state = self.state_manager.load_workflow_state(plan_id)
        if state:
            state['workflow_status'] = WorkflowStatus.FAILED.value
            state['last_error'] = f"Manual intervention required: {str(error)}"
            self.state_manager.save_workflow_state(state)
        
        result = self.active_executions.get(plan_id)
        if result:
            result.recovery_actions.append("manual_intervention_required")
            result.error = f"Manual intervention required: {str(error)}"
        
        return result
    
    def _restart_recovery(
        self,
        plan_id: str,
        error: Exception,
        config: ExecutionConfig
    ) -> Optional[ExecutionResult]:
        """Restart recovery strategy"""
        logger.info(f"Attempting restart recovery for plan {plan_id}")
        
        # Load original client request
        state = self.state_manager.load_workflow_state(plan_id)
        if not state:
            return None
        
        client_request = state.get('client_request', {})
        
        # Create new execution with fresh state
        return self.execute_workflow(
            client_request=client_request,
            plan_id=plan_id,
            execution_config=config
        )
    
    def _handle_recursion_error(self, error: GraphRecursionError, plan_id: str) -> str:
        """Handle graph recursion errors"""
        logger.error(f"Graph recursion limit exceeded for plan {plan_id}")
        return "Graph recursion limit exceeded - possible infinite loop detected"
    
    def _handle_graph_interrupt(self, error: GraphInterrupt, plan_id: str) -> str:
        """Handle graph interrupts"""
        logger.info(f"Graph execution interrupted for plan {plan_id}")
        return "Graph execution interrupted - may require user input"
    
    def _handle_timeout_error(self, error: TimeoutError, plan_id: str) -> str:
        """Handle timeout errors"""
        logger.error(f"Workflow execution timed out for plan {plan_id}")
        return "Workflow execution timed out"
    
    def _handle_generic_error(self, error: Exception, plan_id: str) -> str:
        """Handle generic errors"""
        logger.error(f"Generic error in workflow for plan {plan_id}: {error}")
        return f"Workflow error: {str(error)}"
    
    def resume_workflow(
        self,
        plan_id: str,
        execution_config: Optional[ExecutionConfig] = None
    ) -> ExecutionResult:
        """
        Resume a paused or failed workflow.
        
        Args:
            plan_id: Plan identifier to resume
            execution_config: Optional execution configuration
            
        Returns:
            ExecutionResult with resume details
        """
        config = execution_config or self.config
        
        # Load existing state
        existing_state = self.state_manager.load_workflow_state(plan_id)
        if not existing_state:
            raise ValueError(f"No workflow state found for plan {plan_id}")
        
        logger.info(f"Resuming workflow for plan {plan_id}")
        
        # Create execution result
        result = ExecutionResult(plan_id=plan_id, success=False)
        self.active_executions[plan_id] = result
        
        start_time = datetime.utcnow()
        
        try:
            # Resume execution
            final_state = self._execute_synchronous(existing_state, config, result)
            
            result.final_state = final_state
            result.success = final_state.get('workflow_status') == WorkflowStatus.COMPLETED.value
            result.execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"Workflow resume completed for plan {plan_id}")
            
        except Exception as e:
            logger.error(f"Workflow resume failed for plan {plan_id}: {e}")
            result.error = str(e)
            result.execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        finally:
            self.execution_history.append(result)
            if plan_id in self.active_executions:
                del self.active_executions[plan_id]
        
        return result
    
    def get_execution_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current execution status for a plan.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Execution status information
        """
        # Check active executions
        if plan_id in self.active_executions:
            result = self.active_executions[plan_id]
            return {
                "plan_id": plan_id,
                "status": "running",
                "nodes_executed": result.nodes_executed,
                "retries_used": result.retries_used,
                "checkpoints_created": result.checkpoints_created,
                "recovery_actions": result.recovery_actions
            }
        
        # Check execution history
        for result in reversed(self.execution_history):
            if result.plan_id == plan_id:
                return {
                    "plan_id": plan_id,
                    "status": "completed" if result.success else "failed",
                    "execution_time": result.execution_time,
                    "nodes_executed": result.nodes_executed,
                    "retries_used": result.retries_used,
                    "error": result.error,
                    "recovery_actions": result.recovery_actions
                }
        
        # Check database
        state = self.state_manager.load_workflow_state(plan_id)
        if state:
            return {
                "plan_id": plan_id,
                "status": state.get('workflow_status', 'unknown'),
                "last_updated": state.get('last_updated'),
                "iteration_count": state.get('iteration_count', 0),
                "error_count": state.get('error_count', 0)
            }
        
        return None
    
    def cancel_execution(self, plan_id: str) -> bool:
        """
        Cancel an active workflow execution.
        
        Args:
            plan_id: Plan identifier to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        if plan_id in self.active_executions:
            result = self.active_executions[plan_id]
            result.error = "Execution cancelled by user"
            
            # Update state
            state = self.state_manager.load_workflow_state(plan_id)
            if state:
                state['workflow_status'] = WorkflowStatus.FAILED.value
                state['last_error'] = "Execution cancelled"
                self.state_manager.save_workflow_state(state)
            
            # Move to history
            self.execution_history.append(result)
            del self.active_executions[plan_id]
            
            logger.info(f"Cancelled execution for plan {plan_id}")
            return True
        
        return False
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get execution engine performance metrics.
        
        Returns:
            Performance metrics and statistics
        """
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for r in self.execution_history if r.success)
        
        if total_executions > 0:
            success_rate = successful_executions / total_executions
            avg_execution_time = sum(r.execution_time for r in self.execution_history) / total_executions
            total_retries = sum(r.retries_used for r in self.execution_history)
        else:
            success_rate = 0.0
            avg_execution_time = 0.0
            total_retries = 0
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": total_executions - successful_executions,
            "success_rate": success_rate,
            "average_execution_time": avg_execution_time,
            "total_retries": total_retries,
            "active_executions": len(self.active_executions),
            "recovery_strategies_used": {
                strategy.value: sum(1 for r in self.execution_history 
                                  if strategy.value in r.recovery_actions)
                for strategy in RecoveryStrategy
            }
        }


# Global execution engine instance
_execution_engine: Optional[WorkflowExecutionEngine] = None


def get_execution_engine(config: Optional[ExecutionConfig] = None) -> WorkflowExecutionEngine:
    """Get global workflow execution engine instance"""
    global _execution_engine
    if _execution_engine is None:
        _execution_engine = WorkflowExecutionEngine(config)
    return _execution_engine


# Convenience functions
def execute_event_planning_workflow(
    client_request: Dict[str, Any],
    plan_id: Optional[str] = None,
    config: Optional[ExecutionConfig] = None
) -> ExecutionResult:
    """Execute event planning workflow with error handling"""
    engine = get_execution_engine()
    return engine.execute_workflow(client_request, plan_id, config)


def resume_event_planning_workflow(
    plan_id: str,
    config: Optional[ExecutionConfig] = None
) -> ExecutionResult:
    """Resume event planning workflow"""
    engine = get_execution_engine()
    return engine.resume_workflow(plan_id, config)


def get_workflow_status(plan_id: str) -> Optional[Dict[str, Any]]:
    """Get workflow execution status"""
    engine = get_execution_engine()
    return engine.get_execution_status(plan_id)


def cancel_workflow(plan_id: str) -> bool:
    """Cancel workflow execution"""
    engine = get_execution_engine()
    return engine.cancel_execution(plan_id)