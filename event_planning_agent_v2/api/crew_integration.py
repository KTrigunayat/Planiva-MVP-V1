"""
CrewAI and LangGraph integration for API endpoints.
Provides seamless integration between REST API and agent workflows.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import uuid4

from crewai import Crew, Task
from crewai.agent import Agent

from ..workflows.execution_engine import (
    get_execution_engine, ExecutionConfig, ExecutionMode, ExecutionResult
)
from ..workflows.state_models import EventPlanningState, create_initial_state
from ..agents.orchestrator import create_orchestrator_agent
from ..agents.budgeting import create_budgeting_agent
from ..agents.sourcing import create_sourcing_agent
from ..agents.timeline import create_timeline_agent
from ..agents.blueprint import create_blueprint_agent
from ..tools.budget_tools import BudgetAllocationTool, FitnessCalculationTool
from ..tools.vendor_tools import HybridFilterTool, VendorDatabaseTool
from ..tools.timeline_tools import ConflictDetectionTool, TimelineGenerationTool
from ..tools.blueprint_tools import BlueprintGenerationTool
from ..database.state_manager import get_state_manager

logger = logging.getLogger(__name__)


class EventPlanningCrew:
    """
    CrewAI crew for event planning with integrated LangGraph workflow.
    Manages agent coordination and task execution for event planning workflows.
    """
    
    def __init__(self):
        self.state_manager = get_state_manager()
        self.execution_engine = get_execution_engine()
        
        # Initialize agents
        self.orchestrator_agent = create_orchestrator_agent()
        self.budgeting_agent = create_budgeting_agent()
        self.sourcing_agent = create_sourcing_agent()
        self.timeline_agent = create_timeline_agent()
        self.blueprint_agent = create_blueprint_agent()
        
        # Initialize tools
        self.budget_allocation_tool = BudgetAllocationTool()
        self.fitness_calculation_tool = FitnessCalculationTool()
        self.hybrid_filter_tool = HybridFilterTool()
        self.vendor_database_tool = VendorDatabaseTool()
        self.conflict_detection_tool = ConflictDetectionTool()
        self.timeline_generation_tool = TimelineGenerationTool()
        self.blueprint_generation_tool = BlueprintGenerationTool()
        
        # Create crew
        self.crew = self._create_crew()
    
    def _create_crew(self) -> Crew:
        """Create and configure CrewAI crew"""
        
        # Define tasks for the crew
        budget_task = Task(
            description="""
            Generate budget allocations for the event planning request.
            
            Analyze the client's total budget and requirements to create 3 different
            budget allocation strategies that distribute funds across:
            - Venue rental
            - Catering services
            - Photography services
            - Makeup artist services
            - Miscellaneous expenses
            
            Each allocation should consider the client's priorities and guest count.
            """,
            expected_output="JSON array with 3 budget allocation options, each containing service categories and amounts",
            agent=self.budgeting_agent,
            tools=[self.budget_allocation_tool]
        )
        
        sourcing_task = Task(
            description="""
            Source and rank vendors for each service category based on the budget allocations.
            
            For each service type (venue, caterer, photographer, makeup_artist):
            1. Parse client requirements and preferences
            2. Apply hard filters (budget, location, capacity)
            3. Rank vendors using weighted scoring
            4. Return top 5 vendors per category
            
            Consider client vision, location preferences, and quality requirements.
            """,
            expected_output="JSON object with ranked vendor lists for each service category",
            agent=self.sourcing_agent,
            tools=[self.hybrid_filter_tool, self.vendor_database_tool],
            context=[budget_task]
        )
        
        combination_task = Task(
            description="""
            Generate and evaluate vendor combinations using beam search optimization.
            
            Create vendor combinations from the sourced vendors and:
            1. Calculate fitness scores for each combination
            2. Check vendor compatibility and availability
            3. Estimate total costs and feasibility
            4. Apply beam search to find top 3 combinations
            
            Optimize for client satisfaction, budget compliance, and logistical feasibility.
            """,
            expected_output="JSON array with top 3 vendor combinations, each with scores and cost estimates",
            agent=self.budgeting_agent,
            tools=[self.fitness_calculation_tool],
            context=[sourcing_task]
        )
        
        timeline_task = Task(
            description="""
            Validate vendor combinations for timeline conflicts and logistical feasibility.
            
            For each vendor combination:
            1. Check for scheduling conflicts
            2. Validate vendor availability on event date
            3. Assess logistical compatibility
            4. Generate preliminary timeline
            
            Flag any combinations with conflicts or feasibility issues.
            """,
            expected_output="JSON object with feasibility analysis and conflict reports for each combination",
            agent=self.timeline_agent,
            tools=[self.conflict_detection_tool, self.timeline_generation_tool],
            context=[combination_task]
        )
        
        # Create crew
        crew = Crew(
            agents=[
                self.orchestrator_agent,
                self.budgeting_agent,
                self.sourcing_agent,
                self.timeline_agent
            ],
            tasks=[budget_task, sourcing_task, combination_task, timeline_task],
            verbose=True,
            process_type="sequential"  # Use sequential process for now
        )
        
        return crew
    
    def execute_planning_workflow(
        self,
        client_request: Dict[str, Any],
        plan_id: Optional[str] = None,
        execution_config: Optional[ExecutionConfig] = None
    ) -> ExecutionResult:
        """
        Execute complete event planning workflow using CrewAI and LangGraph.
        
        Args:
            client_request: Client's event planning request
            plan_id: Optional existing plan ID
            execution_config: Optional execution configuration
            
        Returns:
            ExecutionResult with workflow outcome
        """
        try:
            # Generate plan ID if not provided
            if plan_id is None:
                plan_id = str(uuid4())
            
            logger.info(f"Starting event planning workflow for plan {plan_id}")
            
            # Create initial workflow state
            initial_state = create_initial_state(
                client_request=client_request,
                plan_id=plan_id
            )
            
            # Save initial state
            self.state_manager.save_workflow_state(initial_state)
            
            # Execute workflow using LangGraph execution engine
            if execution_config:
                result = self.execution_engine.execute_workflow(
                    client_request=client_request,
                    plan_id=plan_id,
                    execution_config=execution_config
                )
            else:
                # Use default synchronous execution
                default_config = ExecutionConfig(
                    mode=ExecutionMode.SYNCHRONOUS,
                    timeout=300.0,
                    enable_monitoring=True,
                    enable_checkpointing=True
                )
                result = self.execution_engine.execute_workflow(
                    client_request=client_request,
                    plan_id=plan_id,
                    execution_config=default_config
                )
            
            logger.info(f"Workflow execution completed for plan {plan_id} (success: {result.success})")
            return result
            
        except Exception as e:
            logger.error(f"Workflow execution failed for plan {plan_id}: {e}")
            return ExecutionResult(
                plan_id=plan_id,
                success=False,
                error=str(e),
                execution_time=0.0
            )
    
    def execute_crew_workflow(
        self,
        client_request: Dict[str, Any],
        plan_id: str
    ) -> Dict[str, Any]:
        """
        Execute CrewAI workflow directly (alternative to LangGraph).
        
        Args:
            client_request: Client's event planning request
            plan_id: Plan identifier
            
        Returns:
            Crew execution result
        """
        try:
            logger.info(f"Starting CrewAI workflow for plan {plan_id}")
            
            # Prepare inputs for crew
            crew_inputs = {
                "client_request": client_request,
                "plan_id": plan_id,
                "client_name": client_request.get("clientName", "Unknown"),
                "guest_count": client_request.get("guestCount", {}),
                "budget": client_request.get("budget", 1000000),
                "client_vision": client_request.get("clientVision", ""),
                "venue_preferences": client_request.get("venuePreferences", []),
                "food_preferences": client_request.get("foodAndCatering", {}),
                "additional_requirements": client_request.get("additionalRequirements", {})
            }
            
            # Execute crew
            result = self.crew.kickoff(inputs=crew_inputs)
            
            # Process crew result
            if result and hasattr(result, 'raw'):
                crew_output = result.raw
            else:
                crew_output = str(result) if result else "No output from crew"
            
            logger.info(f"CrewAI workflow completed for plan {plan_id}")
            
            return {
                "success": True,
                "output": crew_output,
                "plan_id": plan_id,
                "execution_time": 0.0  # Would need to measure actual time
            }
            
        except Exception as e:
            logger.error(f"CrewAI workflow failed for plan {plan_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "plan_id": plan_id,
                "execution_time": 0.0
            }
    
    def generate_blueprint(
        self,
        plan_id: str,
        selected_combination: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate final event blueprint using Blueprint Agent.
        
        Args:
            plan_id: Plan identifier
            selected_combination: Selected vendor combination
            
        Returns:
            Generated blueprint text or None if failed
        """
        try:
            logger.info(f"Generating blueprint for plan {plan_id}")
            
            # Create blueprint generation task
            blueprint_task = Task(
                description=f"""
                Generate a comprehensive event blueprint for plan {plan_id}.
                
                Create a detailed event blueprint document that includes:
                1. Event overview and client information
                2. Selected vendor details and contact information
                3. Timeline and schedule
                4. Budget breakdown and cost summary
                5. Logistics and coordination notes
                6. Emergency contacts and contingency plans
                
                Use the selected vendor combination to create a professional,
                actionable blueprint document.
                """,
                expected_output="Comprehensive event blueprint document in markdown format",
                agent=self.blueprint_agent,
                tools=[self.blueprint_generation_tool]
            )
            
            # Create temporary crew for blueprint generation
            blueprint_crew = Crew(
                agents=[self.blueprint_agent],
                tasks=[blueprint_task],
                verbose=True
            )
            
            # Execute blueprint generation
            inputs = {
                "plan_id": plan_id,
                "selected_combination": selected_combination
            }
            
            result = blueprint_crew.kickoff(inputs=inputs)
            
            if result and hasattr(result, 'raw'):
                blueprint = result.raw
            else:
                blueprint = str(result) if result else None
            
            logger.info(f"Blueprint generation completed for plan {plan_id}")
            return blueprint
            
        except Exception as e:
            logger.error(f"Blueprint generation failed for plan {plan_id}: {e}")
            return None
    
    def get_workflow_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current workflow status from execution engine.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Workflow status information
        """
        return self.execution_engine.get_execution_status(plan_id)
    
    def cancel_workflow(self, plan_id: str) -> bool:
        """
        Cancel active workflow execution.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            True if cancelled successfully
        """
        return self.execution_engine.cancel_execution(plan_id)
    
    def resume_workflow(
        self,
        plan_id: str,
        execution_config: Optional[ExecutionConfig] = None
    ) -> ExecutionResult:
        """
        Resume paused or failed workflow.
        
        Args:
            plan_id: Plan identifier
            execution_config: Optional execution configuration
            
        Returns:
            ExecutionResult with resume outcome
        """
        return self.execution_engine.resume_workflow(plan_id, execution_config)


# Global crew instance
_event_planning_crew: Optional[EventPlanningCrew] = None


def get_event_planning_crew() -> EventPlanningCrew:
    """Get global event planning crew instance"""
    global _event_planning_crew
    if _event_planning_crew is None:
        _event_planning_crew = EventPlanningCrew()
    return _event_planning_crew


# Convenience functions for API integration
def execute_event_planning(
    client_request: Dict[str, Any],
    plan_id: Optional[str] = None,
    async_execution: bool = False
) -> ExecutionResult:
    """Execute event planning workflow"""
    crew = get_event_planning_crew()
    
    execution_config = ExecutionConfig(
        mode=ExecutionMode.ASYNCHRONOUS if async_execution else ExecutionMode.SYNCHRONOUS,
        timeout=300.0 if not async_execution else None,
        enable_monitoring=True,
        enable_checkpointing=True
    )
    
    return crew.execute_planning_workflow(client_request, plan_id, execution_config)


def generate_event_blueprint(plan_id: str, selected_combination: Dict[str, Any]) -> Optional[str]:
    """Generate event blueprint"""
    crew = get_event_planning_crew()
    return crew.generate_blueprint(plan_id, selected_combination)


def get_planning_workflow_status(plan_id: str) -> Optional[Dict[str, Any]]:
    """Get workflow status"""
    crew = get_event_planning_crew()
    return crew.get_workflow_status(plan_id)


def cancel_planning_workflow(plan_id: str) -> bool:
    """Cancel workflow"""
    crew = get_event_planning_crew()
    return crew.cancel_workflow(plan_id)


def resume_planning_workflow(plan_id: str, async_execution: bool = False) -> ExecutionResult:
    """Resume workflow"""
    crew = get_event_planning_crew()
    
    execution_config = ExecutionConfig(
        mode=ExecutionMode.ASYNCHRONOUS if async_execution else ExecutionMode.SYNCHRONOUS,
        timeout=300.0 if not async_execution else None,
        enable_monitoring=True,
        enable_checkpointing=True
    )
    
    return crew.resume_workflow(plan_id, execution_config)