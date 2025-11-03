"""
LangGraph workflow implementation for event planning orchestration.
Implements beam search algorithm with k=3 optimization and workflow nodes.
"""

import logging
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
from uuid import uuid4

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from crewai import Crew, Task

from .state_models import (
    EventPlanningState, 
    WorkflowStatus, 
    transition_logger,
    state_validator,
    validate_state_transition
)
from ..agents.orchestrator import create_orchestrator_agent
from ..agents.budgeting import create_budgeting_agent
from ..agents.sourcing import create_sourcing_agent
from ..agents.timeline import create_timeline_agent
from ..agents.blueprint import create_blueprint_agent
from ..database.state_manager import get_state_manager
from .task_management_node import task_management_node, should_run_task_management
from .crm_integration import (
    trigger_welcome_communication_sync,
    trigger_budget_summary_communication_sync,
    trigger_vendor_options_communication_sync,
    trigger_selection_confirmation_communication_sync,
    trigger_blueprint_delivery_communication_sync,
    trigger_error_notification_communication_sync,
)

logger = logging.getLogger(__name__)


class EventPlanningWorkflowNodes:
    """
    LangGraph workflow nodes for event planning process.
    Implements beam search algorithm with k=3 optimization preserved.
    """
    
    def __init__(self):
        self.state_manager = get_state_manager()
        self.beam_width = 3  # Preserved k=3 optimization
        
        # Initialize agents (lazy loading)
        self._orchestrator_agent = None
        self._budgeting_agent = None
        self._sourcing_agent = None
        self._timeline_agent = None
        self._blueprint_agent = None
    
    @property
    def orchestrator_agent(self):
        if self._orchestrator_agent is None:
            self._orchestrator_agent = create_orchestrator_agent()
        return self._orchestrator_agent
    
    @property
    def budgeting_agent(self):
        if self._budgeting_agent is None:
            self._budgeting_agent = create_budgeting_agent()
        return self._budgeting_agent
    
    @property
    def sourcing_agent(self):
        if self._sourcing_agent is None:
            self._sourcing_agent = create_sourcing_agent()
        return self._sourcing_agent
    
    @property
    def timeline_agent(self):
        if self._timeline_agent is None:
            self._timeline_agent = create_timeline_agent()
        return self._timeline_agent
    
    @property
    def blueprint_agent(self):
        if self._blueprint_agent is None:
            self._blueprint_agent = create_blueprint_agent()
        return self._blueprint_agent
    
    def initialize_planning(self, state: EventPlanningState) -> EventPlanningState:
        """
        Initialize planning workflow and validate client request.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with initialization complete
        """
        logger.info(f"Initializing planning workflow for plan {state.get('plan_id')}")
        
        # Log node entry
        state = transition_logger.log_node_entry(
            state=state,
            node_name="initialize",
            input_data={"client_request": state.get('client_request', {})}
        )
        
        try:
            # Validate client request
            client_request = state.get('client_request', {})
            required_fields = ['client_id', 'event_type', 'guest_count', 'budget', 'date', 'location']
            
            missing_fields = [field for field in required_fields if field not in client_request]
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            # Initialize workflow metadata
            state['workflow_status'] = WorkflowStatus.RUNNING.value
            state['iteration_count'] = 0
            state['beam_candidates'] = []
            state['next_node'] = 'budget_allocation'
            
            # Save initial state
            self.state_manager.save_workflow_state(state)
            
            # Trigger welcome communication
            try:
                state = trigger_welcome_communication_sync(state)
                logger.info(f"Welcome communication triggered for plan {state.get('plan_id')}")
            except Exception as comm_error:
                logger.warning(f"Failed to send welcome communication: {comm_error}")
                # Don't fail workflow on communication error
            
            # Log successful initialization
            state = transition_logger.log_node_exit(
                state=state,
                node_name="initialize",
                output_data={"status": "initialized", "next_node": "budget_allocation"},
                success=True
            )
            
            logger.info(f"Successfully initialized planning for plan {state.get('plan_id')}")
            return state
            
        except Exception as e:
            logger.error(f"Failed to initialize planning: {e}")
            
            # Log failed initialization
            state = transition_logger.log_node_exit(
                state=state,
                node_name="initialize",
                output_data={"error": str(e)},
                success=False
            )
            
            state['workflow_status'] = WorkflowStatus.FAILED.value
            state['last_error'] = str(e)
            state['error_count'] = state.get('error_count', 0) + 1
            
            # Trigger error notification
            try:
                state = trigger_error_notification_communication_sync(state, str(e))
                logger.info(f"Error notification sent for plan {state.get('plan_id')}")
            except Exception as comm_error:
                logger.warning(f"Failed to send error notification: {comm_error}")
            
            return state
    
    def budget_allocation_node(self, state: EventPlanningState) -> EventPlanningState:
        """
        Generate budget allocations using the Budgeting Agent.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with budget allocations
        """
        logger.info(f"Starting budget allocation for plan {state.get('plan_id')}")
        
        # Log node entry
        state = transition_logger.log_node_entry(
            state=state,
            node_name="budget_allocation",
            input_data={"client_request": state.get('client_request', {})}
        )
        
        try:
            client_request = state.get('client_request', {})
            
            # Create budget allocation task
            budget_task = Task(
                description=f"""Generate 3 budget allocation strategies for an {client_request.get('event_type', 'event')} 
                with {client_request.get('guest_count', 0)} guests and a total budget of ${client_request.get('budget', 0)}.
                
                Consider the client preferences: {client_request.get('preferences', {})}
                
                Return a JSON list of 3 budget allocation options with the following structure:
                [
                    {{
                        "allocation_id": "unique_id",
                        "strategy": "strategy_name",
                        "venue_budget": amount,
                        "catering_budget": amount,
                        "photography_budget": amount,
                        "makeup_budget": amount,
                        "total_allocated": total_amount
                    }}
                ]""",
                expected_output="JSON list of 3 budget allocation strategies",
                agent=self.budgeting_agent
            )
            
            # Execute budget allocation
            crew = Crew(
                agents=[self.budgeting_agent],
                tasks=[budget_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Parse budget allocations from result
            try:
                import json
                if hasattr(result, 'raw'):
                    budget_data = json.loads(result.raw)
                else:
                    budget_data = json.loads(str(result))
                
                # Ensure we have a list of allocations
                if not isinstance(budget_data, list):
                    budget_data = [budget_data]
                
                # Limit to 3 allocations as per beam width
                budget_allocations = budget_data[:3]
                
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"Failed to parse budget allocation result, using fallback: {e}")
                # Fallback budget allocation
                total_budget = client_request.get('budget', 10000)
                budget_allocations = [
                    {
                        "allocation_id": str(uuid4()),
                        "strategy": "balanced",
                        "venue_budget": total_budget * 0.40,
                        "catering_budget": total_budget * 0.40,
                        "photography_budget": total_budget * 0.15,
                        "makeup_budget": total_budget * 0.05,
                        "total_allocated": total_budget
                    }
                ]
            
            # Update state
            state['budget_allocations'] = budget_allocations
            state['workflow_status'] = WorkflowStatus.VENDOR_SOURCING.value
            state['next_node'] = 'vendor_sourcing'
            
            # Save state
            self.state_manager.save_workflow_state(state)
            
            # Trigger budget summary communication
            try:
                state = trigger_budget_summary_communication_sync(state)
                logger.info(f"Budget summary communication triggered for plan {state.get('plan_id')}")
            except Exception as comm_error:
                logger.warning(f"Failed to send budget summary communication: {comm_error}")
                # Don't fail workflow on communication error
            
            # Log successful budget allocation
            state = transition_logger.log_node_exit(
                state=state,
                node_name="budget_allocation",
                output_data={"allocations_count": len(budget_allocations)},
                success=True
            )
            
            logger.info(f"Generated {len(budget_allocations)} budget allocations for plan {state.get('plan_id')}")
            return state
            
        except Exception as e:
            logger.error(f"Failed budget allocation: {e}")
            
            # Log failed budget allocation
            state = transition_logger.log_node_exit(
                state=state,
                node_name="budget_allocation",
                output_data={"error": str(e)},
                success=False
            )
            
            state['workflow_status'] = WorkflowStatus.FAILED.value
            state['last_error'] = str(e)
            state['error_count'] = state.get('error_count', 0) + 1
            
            # Trigger error notification
            try:
                state = trigger_error_notification_communication_sync(state, str(e))
                logger.info(f"Error notification sent for plan {state.get('plan_id')}")
            except Exception as comm_error:
                logger.warning(f"Failed to send error notification: {comm_error}")
            
            return state
    
    def vendor_sourcing_node(self, state: EventPlanningState) -> EventPlanningState:
        """
        Source vendors using the Sourcing Agent.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with vendor combinations
        """
        logger.info(f"Starting vendor sourcing for plan {state.get('plan_id')}")
        
        # Log node entry
        state = transition_logger.log_node_entry(
            state=state,
            node_name="vendor_sourcing",
            input_data={
                "budget_allocations": len(state.get('budget_allocations', [])),
                "client_request": state.get('client_request', {})
            }
        )
        
        try:
            client_request = state.get('client_request', {})
            budget_allocations = state.get('budget_allocations', [])
            
            if not budget_allocations:
                raise ValueError("No budget allocations available for vendor sourcing")
            
            vendor_combinations = []
            
            # Generate vendor combinations for each budget allocation
            for allocation in budget_allocations:
                # Create vendor sourcing task
                sourcing_task = Task(
                    description=f"""Find and rank optimal vendors for an {client_request.get('event_type', 'event')} 
                    with {client_request.get('guest_count', 0)} guests in {client_request.get('location', 'unknown location')}.
                    
                    Budget allocation:
                    - Venue: ${allocation.get('venue_budget', 0)}
                    - Catering: ${allocation.get('catering_budget', 0)}
                    - Photography: ${allocation.get('photography_budget', 0)}
                    - Makeup: ${allocation.get('makeup_budget', 0)}
                    
                    Client preferences: {client_request.get('preferences', {})}
                    Event date: {client_request.get('date', 'TBD')}
                    
                    Return a JSON object with vendor combinations:
                    {{
                        "combination_id": "unique_id",
                        "venue": {{"id": "venue_id", "name": "venue_name", "cost": amount}},
                        "caterer": {{"id": "caterer_id", "name": "caterer_name", "cost": amount}},
                        "photographer": {{"id": "photographer_id", "name": "photographer_name", "cost": amount}},
                        "makeup_artist": {{"id": "makeup_id", "name": "makeup_name", "cost": amount}},
                        "total_cost": total_amount,
                        "budget_allocation_id": "{allocation.get('allocation_id', '')}"
                    }}""",
                    expected_output="JSON object with vendor combination",
                    agent=self.sourcing_agent
                )
                
                # Execute vendor sourcing
                crew = Crew(
                    agents=[self.sourcing_agent],
                    tasks=[sourcing_task],
                    verbose=True
                )
                
                result = crew.kickoff()
                
                # Parse vendor combination from result
                try:
                    import json
                    if hasattr(result, 'raw'):
                        combination_data = json.loads(result.raw)
                    else:
                        combination_data = json.loads(str(result))
                    
                    # Ensure combination has required fields
                    if not combination_data.get('combination_id'):
                        combination_data['combination_id'] = str(uuid4())
                    
                    combination_data['budget_allocation_id'] = allocation.get('allocation_id', '')
                    vendor_combinations.append(combination_data)
                    
                except (json.JSONDecodeError, AttributeError) as e:
                    logger.warning(f"Failed to parse vendor combination result: {e}")
                    # Create fallback combination
                    fallback_combination = {
                        "combination_id": str(uuid4()),
                        "venue": {"id": "fallback_venue", "name": "Default Venue", "cost": allocation.get('venue_budget', 0)},
                        "caterer": {"id": "fallback_caterer", "name": "Default Caterer", "cost": allocation.get('catering_budget', 0)},
                        "photographer": {"id": "fallback_photographer", "name": "Default Photographer", "cost": allocation.get('photography_budget', 0)},
                        "makeup_artist": {"id": "fallback_makeup", "name": "Default Makeup Artist", "cost": allocation.get('makeup_budget', 0)},
                        "total_cost": allocation.get('total_allocated', 0),
                        "budget_allocation_id": allocation.get('allocation_id', '')
                    }
                    vendor_combinations.append(fallback_combination)
            
            # Update state
            state['vendor_combinations'] = vendor_combinations
            state['workflow_status'] = WorkflowStatus.BEAM_SEARCH.value
            state['next_node'] = 'beam_search'
            
            # Save state
            self.state_manager.save_workflow_state(state)
            
            # Log successful vendor sourcing
            state = transition_logger.log_node_exit(
                state=state,
                node_name="vendor_sourcing",
                output_data={"combinations_count": len(vendor_combinations)},
                success=True
            )
            
            logger.info(f"Generated {len(vendor_combinations)} vendor combinations for plan {state.get('plan_id')}")
            return state
            
        except Exception as e:
            logger.error(f"Failed vendor sourcing: {e}")
            
            # Log failed vendor sourcing
            state = transition_logger.log_node_exit(
                state=state,
                node_name="vendor_sourcing",
                output_data={"error": str(e)},
                success=False
            )
            
            state['workflow_status'] = WorkflowStatus.FAILED.value
            state['last_error'] = str(e)
            state['error_count'] = state.get('error_count', 0) + 1
            
            # Trigger error notification
            try:
                state = trigger_error_notification_communication_sync(state, str(e))
                logger.info(f"Error notification sent for plan {state.get('plan_id')}")
            except Exception as comm_error:
                logger.warning(f"Failed to send error notification: {comm_error}")
            
            return state
    
    def beam_search_node(self, state: EventPlanningState) -> EventPlanningState:
        """
        Optimized beam search algorithm with k=3 optimization preserved and performance enhancements.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with beam candidates
        """
        logger.info(f"Starting optimized beam search for plan {state.get('plan_id')}")
        
        # Log node entry
        state = transition_logger.log_node_entry(
            state=state,
            node_name="beam_search",
            input_data={
                "vendor_combinations": len(state.get('vendor_combinations', [])),
                "iteration": state.get('iteration_count', 0)
            }
        )
        
        try:
            from ..config.settings import get_settings
            settings = get_settings()
            workflow_settings = settings.workflow
            
            client_request = state.get('client_request', {})
            vendor_combinations = state.get('vendor_combinations', [])
            current_beam = state.get('beam_candidates', [])
            current_iteration = state.get('iteration_count', 0)
            
            if not vendor_combinations:
                raise ValueError("No vendor combinations available for beam search")
            
            # Early termination check for high-quality solutions
            if (workflow_settings.enable_early_termination and 
                current_iteration >= workflow_settings.min_iterations_before_termination and
                current_beam):
                
                best_current_score = max(combo.get('fitness_score', 0) for combo in current_beam)
                if best_current_score >= workflow_settings.early_termination_threshold:
                    logger.info(f"Early termination triggered with score {best_current_score}")
                    state['workflow_status'] = WorkflowStatus.CLIENT_SELECTION.value
                    state['next_node'] = 'client_selection'
                    state['early_termination'] = True
                    return state
            
            # Combine current beam with new combinations (optimized)
            all_combinations = []
            
            # Add current beam candidates (already scored)
            all_combinations.extend(current_beam)
            
            # Add new combinations
            all_combinations.extend(vendor_combinations)
            
            # Optimized fitness score calculation with caching
            scored_combinations = []
            score_cache = {}
            
            for combination in all_combinations:
                # Create cache key for combination
                combo_key = self._create_combination_cache_key(combination)
                
                if combo_key in score_cache:
                    score = score_cache[combo_key]
                else:
                    score = self._calculate_fitness_score(combination, client_request)
                    score_cache[combo_key] = score
                
                scored_combinations.append({
                    **combination,
                    'fitness_score': score,
                    'iteration_created': current_iteration,
                    'cache_key': combo_key
                })
            
            # Optimized sorting and selection (preserve k=3)
            scored_combinations.sort(key=lambda x: x.get('fitness_score', 0), reverse=True)
            top_combinations = scored_combinations[:self.beam_width]
            
            # Convergence detection
            converged = False
            if (workflow_settings.enable_convergence_detection and 
                len(current_beam) == self.beam_width and 
                current_iteration >= workflow_settings.convergence_window):
                
                converged = self._check_convergence_optimized(
                    current_beam, 
                    top_combinations, 
                    workflow_settings.convergence_threshold
                )
            
            # Update beam candidates with memory optimization
            if workflow_settings.enable_memory_optimization:
                # Remove unnecessary fields to reduce memory usage
                optimized_combinations = []
                for combo in top_combinations:
                    optimized_combo = {
                        key: value for key, value in combo.items()
                        if key not in ['cache_key', 'detailed_breakdown']  # Remove heavy fields
                    }
                    optimized_combinations.append(optimized_combo)
                state['beam_candidates'] = optimized_combinations
            else:
                state['beam_candidates'] = top_combinations
            
            state['iteration_count'] = current_iteration + 1
            
            # Enhanced termination logic
            max_iterations = workflow_settings.max_workflow_iterations
            new_iteration = state['iteration_count']
            
            should_terminate = (
                new_iteration >= max_iterations or
                converged or
                (workflow_settings.enable_early_termination and 
                 top_combinations and 
                 top_combinations[0].get('fitness_score', 0) >= workflow_settings.early_termination_threshold)
            )
            
            if should_terminate:
                # Present options to client
                state['workflow_status'] = WorkflowStatus.CLIENT_SELECTION.value
                state['next_node'] = 'client_selection'
                if converged:
                    state['convergence_achieved'] = True
                    logger.info(f"Beam search converged at iteration {new_iteration}")
            else:
                # Continue with more iterations
                state['workflow_status'] = WorkflowStatus.VENDOR_SOURCING.value
                state['next_node'] = 'vendor_sourcing'
                # Clear vendor combinations for next iteration
                state['vendor_combinations'] = []
            
            # Optimized state persistence (compress if enabled)
            if workflow_settings.enable_state_compression:
                state = self._compress_state_for_storage(state)
            
            # Save state with checkpoint interval
            if new_iteration % workflow_settings.state_checkpoint_interval == 0:
                self.state_manager.save_workflow_state(state)
            
            # Log successful beam search with performance metrics
            state = transition_logger.log_node_exit(
                state=state,
                node_name="beam_search",
                output_data={
                    "beam_candidates": len(top_combinations),
                    "iteration": new_iteration,
                    "next_node": state['next_node'],
                    "best_score": top_combinations[0].get('fitness_score', 0) if top_combinations else 0,
                    "converged": converged,
                    "combinations_evaluated": len(scored_combinations)
                },
                success=True
            )
            
            logger.info(f"Optimized beam search iteration {new_iteration} complete for plan {state.get('plan_id')} "
                       f"(best score: {top_combinations[0].get('fitness_score', 0):.3f})")
            return state
            
        except Exception as e:
            logger.error(f"Failed optimized beam search: {e}")
            
            # Log failed beam search
            state = transition_logger.log_node_exit(
                state=state,
                node_name="beam_search",
                output_data={"error": str(e)},
                success=False
            )
            
            state['workflow_status'] = WorkflowStatus.FAILED.value
            state['last_error'] = str(e)
            state['error_count'] = state.get('error_count', 0) + 1
            
            # Trigger error notification
            try:
                state = trigger_error_notification_communication_sync(state, str(e))
                logger.info(f"Error notification sent for plan {state.get('plan_id')}")
            except Exception as comm_error:
                logger.warning(f"Failed to send error notification: {comm_error}")
            
            return state
    
    def _create_combination_cache_key(self, combination: Dict[str, Any]) -> str:
        """Create cache key for combination to avoid redundant calculations"""
        import hashlib
        import json
        
        # Extract key fields for caching
        cache_data = {
            'venue_id': combination.get('venue', {}).get('id'),
            'caterer_id': combination.get('caterer', {}).get('id'),
            'photographer_id': combination.get('photographer', {}).get('id'),
            'makeup_artist_id': combination.get('makeup_artist', {}).get('id'),
            'total_cost': combination.get('total_cost')
        }
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()[:16]
    
    def _check_convergence_optimized(
        self, 
        previous_beam: List[Dict[str, Any]], 
        current_beam: List[Dict[str, Any]], 
        threshold: float
    ) -> bool:
        """
        Optimized convergence detection for beam search.
        
        Args:
            previous_beam: Previous iteration's beam candidates
            current_beam: Current iteration's beam candidates
            threshold: Convergence threshold for score differences
            
        Returns:
            True if beam search has converged
        """
        if not previous_beam or not current_beam:
            return False
        
        # Check if top candidates are similar
        prev_scores = [combo.get('fitness_score', 0) for combo in previous_beam]
        curr_scores = [combo.get('fitness_score', 0) for combo in current_beam]
        
        # Calculate score differences
        score_diffs = []
        for i in range(min(len(prev_scores), len(curr_scores))):
            diff = abs(curr_scores[i] - prev_scores[i])
            score_diffs.append(diff)
        
        # Check if all differences are below threshold
        max_diff = max(score_diffs) if score_diffs else float('inf')
        converged = max_diff < threshold
        
        if converged:
            logger.debug(f"Convergence detected: max score difference {max_diff:.4f} < threshold {threshold}")
        
        return converged
    
    def _compress_state_for_storage(self, state: EventPlanningState) -> EventPlanningState:
        """
        Compress workflow state to reduce memory usage.
        
        Args:
            state: Current workflow state
            
        Returns:
            Compressed state
        """
        import gzip
        import json
        import base64
        
        # Identify large fields to compress
        large_fields = ['beam_history', 'agent_logs', 'detailed_combinations']
        
        compressed_state = state.copy()
        
        for field in large_fields:
            if field in state and state[field]:
                try:
                    # Serialize and compress
                    json_data = json.dumps(state[field])
                    compressed_data = gzip.compress(json_data.encode('utf-8'))
                    encoded_data = base64.b64encode(compressed_data).decode('utf-8')
                    
                    # Store compressed data with marker
                    compressed_state[f"{field}_compressed"] = encoded_data
                    compressed_state.pop(field, None)
                    
                except Exception as e:
                    logger.warning(f"Failed to compress field {field}: {e}")
        
        return compressed_state
    
    def client_selection_node(self, state: EventPlanningState) -> EventPlanningState:
        """
        Present options to client and wait for selection.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state ready for client selection
        """
        logger.info(f"Preparing client selection for plan {state.get('plan_id')}")
        
        # Log node entry
        state = transition_logger.log_node_entry(
            state=state,
            node_name="client_selection",
            input_data={"beam_candidates": len(state.get('beam_candidates', []))}
        )
        
        try:
            beam_candidates = state.get('beam_candidates', [])
            
            if not beam_candidates:
                raise ValueError("No beam candidates available for client selection")
            
            # Prepare candidates for client presentation
            presentation_candidates = []
            for i, candidate in enumerate(beam_candidates):
                presentation_candidate = {
                    "rank": i + 1,
                    "combination_id": candidate.get('combination_id', str(uuid4())),
                    "fitness_score": candidate.get('fitness_score', 0),
                    "total_cost": candidate.get('total_cost', 0),
                    "vendors": {
                        "venue": candidate.get('venue', {}),
                        "caterer": candidate.get('caterer', {}),
                        "photographer": candidate.get('photographer', {}),
                        "makeup_artist": candidate.get('makeup_artist', {})
                    },
                    "summary": self._generate_combination_summary(candidate)
                }
                presentation_candidates.append(presentation_candidate)
            
            # Update state for client selection
            state['beam_candidates'] = presentation_candidates
            state['workflow_status'] = WorkflowStatus.CLIENT_SELECTION.value
            state['next_node'] = 'blueprint_generation'  # Will be triggered after client selects
            
            # Save state
            self.state_manager.save_workflow_state(state)
            
            # Trigger vendor options communication
            try:
                state = trigger_vendor_options_communication_sync(state)
                logger.info(f"Vendor options communication triggered for plan {state.get('plan_id')}")
            except Exception as comm_error:
                logger.warning(f"Failed to send vendor options communication: {comm_error}")
                # Don't fail workflow on communication error
            
            # Log successful client selection preparation
            state = transition_logger.log_node_exit(
                state=state,
                node_name="client_selection",
                output_data={"presentation_candidates": len(presentation_candidates)},
                success=True
            )
            
            logger.info(f"Prepared {len(presentation_candidates)} candidates for client selection (plan {state.get('plan_id')})")
            return state
            
        except Exception as e:
            logger.error(f"Failed client selection preparation: {e}")
            
            # Log failed client selection
            state = transition_logger.log_node_exit(
                state=state,
                node_name="client_selection",
                output_data={"error": str(e)},
                success=False
            )
            
            state['workflow_status'] = WorkflowStatus.FAILED.value
            state['last_error'] = str(e)
            state['error_count'] = state.get('error_count', 0) + 1
            
            # Trigger error notification
            try:
                state = trigger_error_notification_communication_sync(state, str(e))
                logger.info(f"Error notification sent for plan {state.get('plan_id')}")
            except Exception as comm_error:
                logger.warning(f"Failed to send error notification: {comm_error}")
            
            return state
    
    def blueprint_generation_node(self, state: EventPlanningState) -> EventPlanningState:
        """
        Generate final event blueprint using the Blueprint Agent.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with final blueprint
        """
        logger.info(f"Starting blueprint generation for plan {state.get('plan_id')}")
        
        # Log node entry
        state = transition_logger.log_node_entry(
            state=state,
            node_name="blueprint_generation",
            input_data={"selected_combination": bool(state.get('selected_combination'))}
        )
        
        try:
            selected_combination = state.get('selected_combination')
            client_request = state.get('client_request', {})
            
            if not selected_combination:
                raise ValueError("No combination selected for blueprint generation")
            
            # Create blueprint generation task
            blueprint_task = Task(
                description=f"""Generate a comprehensive event blueprint for an {client_request.get('event_type', 'event')} 
                with {client_request.get('guest_count', 0)} guests on {client_request.get('date', 'TBD')} 
                at {client_request.get('location', 'unknown location')}.
                
                Selected vendor combination:
                - Venue: {selected_combination.get('venue', {}).get('name', 'Unknown')} (${selected_combination.get('venue', {}).get('cost', 0)})
                - Caterer: {selected_combination.get('caterer', {}).get('name', 'Unknown')} (${selected_combination.get('caterer', {}).get('cost', 0)})
                - Photographer: {selected_combination.get('photographer', {}).get('name', 'Unknown')} (${selected_combination.get('photographer', {}).get('cost', 0)})
                - Makeup Artist: {selected_combination.get('makeup_artist', {}).get('name', 'Unknown')} (${selected_combination.get('makeup_artist', {}).get('cost', 0)})
                
                Total Cost: ${selected_combination.get('total_cost', 0)}
                Client Budget: ${client_request.get('budget', 0)}
                
                Create a detailed event blueprint including:
                1. Executive Summary
                2. Vendor Details and Contact Information
                3. Timeline and Schedule
                4. Budget Breakdown
                5. Logistics and Coordination Plan
                6. Contingency Plans
                
                Format as a professional document suitable for client presentation.""",
                expected_output="Comprehensive event blueprint document",
                agent=self.blueprint_agent
            )
            
            # Execute blueprint generation
            crew = Crew(
                agents=[self.blueprint_agent],
                tasks=[blueprint_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Extract blueprint content
            if hasattr(result, 'raw'):
                final_blueprint = result.raw
            else:
                final_blueprint = str(result)
            
            # Update state
            state['final_blueprint'] = final_blueprint
            state['workflow_status'] = WorkflowStatus.COMPLETED.value
            state['next_node'] = None  # Terminal state
            
            # Save final state
            self.state_manager.save_workflow_state(state)
            
            # Trigger blueprint delivery communication
            try:
                state = trigger_blueprint_delivery_communication_sync(state)
                logger.info(f"Blueprint delivery communication triggered for plan {state.get('plan_id')}")
            except Exception as comm_error:
                logger.warning(f"Failed to send blueprint delivery communication: {comm_error}")
                # Don't fail workflow on communication error
            
            # Log successful blueprint generation
            state = transition_logger.log_node_exit(
                state=state,
                node_name="blueprint_generation",
                output_data={"blueprint_length": len(final_blueprint)},
                success=True
            )
            
            logger.info(f"Successfully generated blueprint for plan {state.get('plan_id')}")
            return state
            
        except Exception as e:
            logger.error(f"Failed blueprint generation: {e}")
            
            # Log failed blueprint generation
            state = transition_logger.log_node_exit(
                state=state,
                node_name="blueprint_generation",
                output_data={"error": str(e)},
                success=False
            )
            
            state['workflow_status'] = WorkflowStatus.FAILED.value
            state['last_error'] = str(e)
            state['error_count'] = state.get('error_count', 0) + 1
            
            # Trigger error notification
            try:
                state = trigger_error_notification_communication_sync(state, str(e))
                logger.info(f"Error notification sent for plan {state.get('plan_id')}")
            except Exception as comm_error:
                logger.warning(f"Failed to send error notification: {comm_error}")
            
            return state
    
    def _calculate_fitness_score(self, combination: Dict[str, Any], client_request: Dict[str, Any]) -> float:
        """
        Calculate fitness score for a vendor combination.
        Preserves existing calculateFitnessScore algorithm logic.
        
        Args:
            combination: Vendor combination to score
            client_request: Client requirements
            
        Returns:
            Fitness score between 0 and 1
        """
        try:
            score = 0.0
            total_weight = 0.0
            
            # Budget compliance (40% weight)
            budget_weight = 0.4
            client_budget = client_request.get('budget', 0)
            combination_cost = combination.get('total_cost', 0)
            
            if client_budget > 0:
                if combination_cost <= client_budget:
                    # Reward staying under budget
                    budget_score = 1.0 - (combination_cost / client_budget) * 0.2
                else:
                    # Penalize going over budget
                    budget_score = max(0.0, 1.0 - ((combination_cost - client_budget) / client_budget))
                
                score += budget_score * budget_weight
                total_weight += budget_weight
            
            # Vendor quality scores (30% weight)
            quality_weight = 0.3
            vendors = ['venue', 'caterer', 'photographer', 'makeup_artist']
            vendor_scores = []
            
            for vendor_type in vendors:
                vendor = combination.get(vendor_type, {})
                vendor_score = vendor.get('rating', 0.5)  # Default to 0.5 if no rating
                vendor_scores.append(vendor_score)
            
            if vendor_scores:
                avg_quality = sum(vendor_scores) / len(vendor_scores)
                score += avg_quality * quality_weight
                total_weight += quality_weight
            
            # Preference matching (20% weight)
            preference_weight = 0.2
            preferences = client_request.get('preferences', {})
            preference_score = self._calculate_preference_match(combination, preferences)
            score += preference_score * preference_weight
            total_weight += preference_weight
            
            # Availability and logistics (10% weight)
            logistics_weight = 0.1
            logistics_score = self._calculate_logistics_score(combination, client_request)
            score += logistics_score * logistics_weight
            total_weight += logistics_weight
            
            # Normalize score
            if total_weight > 0:
                final_score = score / total_weight
            else:
                final_score = 0.0
            
            return min(1.0, max(0.0, final_score))
            
        except Exception as e:
            logger.error(f"Error calculating fitness score: {e}")
            return 0.0
    
    def _calculate_preference_match(self, combination: Dict[str, Any], preferences: Dict[str, Any]) -> float:
        """Calculate how well the combination matches client preferences"""
        if not preferences:
            return 0.5  # Neutral score if no preferences
        
        match_score = 0.0
        total_preferences = 0
        
        # Check style preferences
        if 'style' in preferences:
            preferred_style = preferences['style'].lower()
            style_matches = 0
            
            for vendor_type in ['venue', 'caterer', 'photographer', 'makeup_artist']:
                vendor = combination.get(vendor_type, {})
                vendor_style = vendor.get('style', '').lower()
                if preferred_style in vendor_style or vendor_style in preferred_style:
                    style_matches += 1
            
            match_score += style_matches / 4.0  # Normalize by number of vendors
            total_preferences += 1
        
        # Check location preferences
        if 'location_preference' in preferences:
            venue = combination.get('venue', {})
            venue_location = venue.get('location', '').lower()
            preferred_location = preferences['location_preference'].lower()
            
            if preferred_location in venue_location:
                match_score += 1.0
            total_preferences += 1
        
        # Normalize final preference score
        if total_preferences > 0:
            return match_score / total_preferences
        else:
            return 0.5
    
    def _calculate_logistics_score(self, combination: Dict[str, Any], client_request: Dict[str, Any]) -> float:
        """Calculate logistics feasibility score"""
        logistics_score = 0.5  # Base score
        
        # Check date availability (simplified)
        event_date = client_request.get('date')
        if event_date:
            # In a real implementation, this would check actual vendor availability
            logistics_score += 0.3
        
        # Check location compatibility
        venue = combination.get('venue', {})
        venue_location = venue.get('location', '')
        client_location = client_request.get('location', '')
        
        if venue_location and client_location:
            # Simplified location compatibility check
            if venue_location.lower() in client_location.lower() or client_location.lower() in venue_location.lower():
                logistics_score += 0.2
        
        return min(1.0, logistics_score)
    
    def _check_convergence(self, beam_candidates: List[Dict[str, Any]]) -> bool:
        """
        Check if beam search has converged (scores are very similar)
        
        Args:
            beam_candidates: Current beam candidates
            
        Returns:
            True if converged, False otherwise
        """
        if len(beam_candidates) < 2:
            return True
        
        scores = [candidate.get('fitness_score', 0) for candidate in beam_candidates]
        max_score = max(scores)
        min_score = min(scores)
        
        # Consider converged if score difference is less than 5%
        convergence_threshold = 0.05
        return (max_score - min_score) < convergence_threshold
    
    def _generate_combination_summary(self, combination: Dict[str, Any]) -> str:
        """Generate a human-readable summary of a vendor combination"""
        venue_name = combination.get('venue', {}).get('name', 'Unknown Venue')
        caterer_name = combination.get('caterer', {}).get('name', 'Unknown Caterer')
        photographer_name = combination.get('photographer', {}).get('name', 'Unknown Photographer')
        makeup_name = combination.get('makeup_artist', {}).get('name', 'Unknown Makeup Artist')
        total_cost = combination.get('total_cost', 0)
        fitness_score = combination.get('fitness_score', 0)
        
        return (f"Venue: {venue_name}, Catering: {caterer_name}, "
                f"Photography: {photographer_name}, Makeup: {makeup_name} "
                f"(Total: ${total_cost:,.2f}, Score: {fitness_score:.2f})")


# Conditional routing functions
def should_continue_search(state: EventPlanningState) -> Literal["continue", "present_options"]:
    """
    Determine whether to continue beam search or present options to client.
    
    Args:
        state: Current workflow state
        
    Returns:
        "continue" to continue search, "present_options" to present to client
    """
    current_iteration = state.get('iteration_count', 0)
    max_iterations = state.get('max_iterations', 20)
    
    # Check if we've reached max iterations
    if current_iteration >= max_iterations:
        return "present_options"
    
    # Check for convergence
    beam_candidates = state.get('beam_candidates', [])
    if len(beam_candidates) >= 2:
        scores = [candidate.get('fitness_score', 0) for candidate in beam_candidates]
        max_score = max(scores)
        min_score = min(scores)
        
        # If scores are very close, we've converged
        if (max_score - min_score) < 0.05:
            return "present_options"
    
    # Continue searching
    return "continue"


def should_generate_blueprint(state: EventPlanningState) -> Literal["task_management", "wait_selection"]:
    """
    Determine whether to proceed to task management or wait for client selection.
    
    Args:
        state: Current workflow state
        
    Returns:
        "task_management" if selection made, "wait_selection" otherwise
    """
    selected_combination = state.get('selected_combination')
    
    if selected_combination:
        return "task_management"
    else:
        return "wait_selection"


def should_skip_task_management(state: EventPlanningState) -> Literal["blueprint_generation", "skip_to_blueprint"]:
    """
    Determine whether to run task management or skip to blueprint generation.
    
    Task management is skipped if:
    - Timeline data is missing
    - Workflow is in failed state
    - Task management is explicitly disabled
    
    Args:
        state: Current workflow state
        
    Returns:
        "blueprint_generation" to run task management, "skip_to_blueprint" to skip
    """
    # Check if we should run task management
    if should_run_task_management(state):
        return "blueprint_generation"
    else:
        return "skip_to_blueprint"


# Workflow graph creation
def create_event_planning_workflow() -> StateGraph:
    """
    Create and configure the LangGraph workflow for event planning.
    
    Returns:
        Configured StateGraph workflow
    """
    # Initialize workflow nodes
    nodes = EventPlanningWorkflowNodes()
    
    # Create state graph
    workflow = StateGraph(EventPlanningState)
    
    # Add nodes
    workflow.add_node("initialize", nodes.initialize_planning)
    workflow.add_node("budget_allocation", nodes.budget_allocation_node)
    workflow.add_node("vendor_sourcing", nodes.vendor_sourcing_node)
    workflow.add_node("beam_search", nodes.beam_search_node)
    workflow.add_node("client_selection", nodes.client_selection_node)
    workflow.add_node("task_management", task_management_node)
    workflow.add_node("blueprint_generation", nodes.blueprint_generation_node)
    
    # Add edges
    workflow.add_edge(START, "initialize")
    workflow.add_edge("initialize", "budget_allocation")
    workflow.add_edge("budget_allocation", "vendor_sourcing")
    workflow.add_edge("vendor_sourcing", "beam_search")
    
    # Conditional routing from beam search
    workflow.add_conditional_edges(
        "beam_search",
        should_continue_search,
        {
            "continue": "vendor_sourcing",
            "present_options": "client_selection"
        }
    )
    
    # Conditional routing from client selection
    workflow.add_conditional_edges(
        "client_selection",
        should_generate_blueprint,
        {
            "task_management": "task_management",
            "wait_selection": END  # Wait for external selection
        }
    )
    
    # Add edge from task management to blueprint generation
    # Task management node handles its own conditional logic internally
    workflow.add_edge("task_management", "blueprint_generation")
    
    workflow.add_edge("blueprint_generation", END)
    
    return workflow


# Workflow execution class
class EventPlanningWorkflow:
    """
    Main workflow execution class for event planning.
    Provides high-level interface for workflow management.
    """
    
    def __init__(self, checkpointer=None):
        self.workflow_graph = create_event_planning_workflow()
        self.checkpointer = checkpointer or MemorySaver()
        self.compiled_workflow = None
        self.state_manager = get_state_manager()
    
    def compile_workflow(self):
        """Compile the workflow graph for execution"""
        if self.compiled_workflow is None:
            self.compiled_workflow = self.workflow_graph.compile(
                checkpointer=self.checkpointer
            )
        return self.compiled_workflow
    
    def execute_workflow(
        self,
        client_request: Dict[str, Any],
        plan_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> EventPlanningState:
        """
        Execute the complete event planning workflow.
        
        Args:
            client_request: Client's event planning request
            plan_id: Optional existing plan ID
            config: Optional workflow configuration
            
        Returns:
            Final workflow state
        """
        # Create initial state
        from .state_models import create_initial_state
        
        initial_state = create_initial_state(
            client_request=client_request,
            plan_id=plan_id
        )
        
        # Compile workflow
        app = self.compile_workflow()
        
        # Execute workflow
        try:
            final_state = app.invoke(
                initial_state,
                config=config or {"configurable": {"thread_id": initial_state['plan_id']}}
            )
            
            logger.info(f"Workflow completed for plan {initial_state['plan_id']}")
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            
            # Update state with error
            error_state = initial_state.copy()
            error_state['workflow_status'] = WorkflowStatus.FAILED.value
            error_state['last_error'] = str(e)
            error_state['error_count'] = error_state.get('error_count', 0) + 1
            
            # Save error state
            self.state_manager.save_workflow_state(error_state)
            
            return error_state
    
    def resume_workflow(
        self,
        plan_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> EventPlanningState:
        """
        Resume a paused or failed workflow.
        
        Args:
            plan_id: Plan identifier to resume
            config: Optional workflow configuration
            
        Returns:
            Resumed workflow state
        """
        # Load existing state
        existing_state = self.state_manager.load_workflow_state(plan_id)
        
        if not existing_state:
            raise ValueError(f"No workflow state found for plan {plan_id}")
        
        # Compile workflow
        app = self.compile_workflow()
        
        # Resume execution
        try:
            final_state = app.invoke(
                existing_state,
                config=config or {"configurable": {"thread_id": plan_id}}
            )
            
            logger.info(f"Workflow resumed and completed for plan {plan_id}")
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow resume failed: {e}")
            
            # Update state with error
            existing_state['workflow_status'] = WorkflowStatus.FAILED.value
            existing_state['last_error'] = str(e)
            existing_state['error_count'] = existing_state.get('error_count', 0) + 1
            
            # Save error state
            self.state_manager.save_workflow_state(existing_state)
            
            return existing_state
    
    def select_combination(
        self,
        plan_id: str,
        combination_id: str
    ) -> EventPlanningState:
        """
        Handle client selection of a vendor combination.
        
        Args:
            plan_id: Plan identifier
            combination_id: Selected combination identifier
            
        Returns:
            Updated workflow state
        """
        # Load current state
        current_state = self.state_manager.load_workflow_state(plan_id)
        
        if not current_state:
            raise ValueError(f"No workflow state found for plan {plan_id}")
        
        # Find selected combination
        beam_candidates = current_state.get('beam_candidates', [])
        selected_combination = None
        
        for candidate in beam_candidates:
            if candidate.get('combination_id') == combination_id:
                selected_combination = candidate
                break
        
        if not selected_combination:
            raise ValueError(f"Combination {combination_id} not found in beam candidates")
        
        # Update state with selection
        current_state['selected_combination'] = selected_combination
        current_state['workflow_status'] = WorkflowStatus.BLUEPRINT_GENERATION.value
        current_state['next_node'] = 'blueprint_generation'
        
        # Trigger selection confirmation communication
        try:
            current_state = trigger_selection_confirmation_communication_sync(current_state)
            logger.info(f"Selection confirmation communication sent for plan {plan_id}")
        except Exception as comm_error:
            logger.warning(f"Failed to send selection confirmation: {comm_error}")
        
        # Save updated state
        self.state_manager.save_workflow_state(current_state)
        
        # Continue workflow from blueprint generation
        return self.resume_workflow(plan_id)