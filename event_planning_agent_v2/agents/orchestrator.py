"""
Orchestrator Agent for Event Planning System

This agent serves as the master coordinator and workflow manager,
implementing beam search coordination capabilities and workflow state management.
"""

import json
from typing import Dict, List, Any, Optional
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
try:
    from langchain_ollama import OllamaLLM
except ImportError:
    from langchain_community.llms import Ollama as OllamaLLM


class BeamSearchToolInput(BaseModel):
    """Input schema for BeamSearchTool"""
    current_combinations: List[dict] = Field(..., description="Current vendor combinations to evaluate")
    client_requirements: dict = Field(..., description="Client requirements for scoring")
    beam_width: int = Field(default=3, description="Number of top combinations to keep")


class BeamSearchTool(BaseTool):
    """
    Implements beam search algorithm with k=3 optimization for vendor combinations.
    Maintains existing beam search functionality while integrating with CrewAI.
    """
    name: str = "Beam Search Optimization Tool"
    description: str = "Implements beam search algorithm to find optimal vendor combinations"
    args_schema: type[BaseModel] = BeamSearchToolInput

    def _calculate_combination_score(self, combination: dict, client_requirements: dict) -> float:
        """
        Calculate fitness score for a vendor combination.
        Preserves existing beam search scoring logic.
        """
        score = 0.0
        total_services = len(combination.get('vendors', {}))
        
        if total_services == 0:
            return 0.0
        
        vendors = combination.get('vendors', {})
        budget_allocation = combination.get('budget_allocation', {})
        
        # Budget compliance scoring
        budget_score = 0.0
        for service_type, vendor in vendors.items():
            allocated_budget = budget_allocation.get(service_type, 0)
            
            # Get vendor price based on service type
            vendor_price = 0
            if service_type == 'venue':
                vendor_price = vendor.get('rental_cost', 0)
            elif service_type == 'caterer':
                price_per_plate = vendor.get('min_veg_price', 0)
                guest_count = max(client_requirements.get('guestCount', {}).values() or [200])
                vendor_price = price_per_plate * guest_count
            elif service_type == 'photographer':
                vendor_price = vendor.get('photo_package_price', 0)
            elif service_type == 'makeup_artist':
                vendor_price = vendor.get('bridal_makeup_price', 0)
            
            if allocated_budget > 0 and vendor_price <= allocated_budget:
                budget_score += 1.0 / total_services
            elif allocated_budget > 0:
                # Penalty for exceeding budget
                overage = (vendor_price - allocated_budget) / allocated_budget
                budget_score += max(0, (1.0 - overage * 0.5)) / total_services
        
        score += budget_score * 0.4  # 40% weight on budget
        
        # Preference matching scoring
        preference_score = 0.0
        client_vision = client_requirements.get('clientVision', '').lower()
        
        for service_type, vendor in vendors.items():
            service_score = 0.0
            
            # Location preference
            vendor_location = vendor.get('location_city', '')
            if vendor_location and vendor_location.lower() in client_vision:
                service_score += 0.2
            
            # Service-specific preferences
            if service_type == 'venue':
                venue_prefs = client_requirements.get('venuePreferences', [])
                venue_type = vendor.get('venue_type', '')
                if venue_type in venue_prefs:
                    service_score += 0.3
                
                # Capacity matching
                guest_count = max(client_requirements.get('guestCount', {}).values() or [0])
                capacity = vendor.get('max_seating_capacity', 0)
                if capacity >= guest_count:
                    utilization = guest_count / capacity if capacity > 0 else 0
                    if 0.7 <= utilization <= 0.95:  # Optimal utilization
                        service_score += 0.3
                    else:
                        service_score += 0.15
            
            elif service_type == 'caterer':
                cuisine_prefs = client_requirements.get('foodAndCatering', {}).get('cuisinePreferences', [])
                vendor_cuisines = vendor.get('attributes', {}).get('cuisines', [])
                if cuisine_prefs and vendor_cuisines:
                    matches = sum(1 for pref in cuisine_prefs 
                                if any(pref.lower() in vc.lower() for vc in vendor_cuisines))
                    service_score += (matches / len(cuisine_prefs)) * 0.4
            
            preference_score += service_score / total_services
        
        score += preference_score * 0.45  # 45% weight on preferences
        
        # Vendor compatibility scoring
        locations = [v.get('location_city') for v in vendors.values() if v.get('location_city')]
        unique_locations = set(locations)
        
        if len(unique_locations) <= 1:
            compatibility_score = 1.0
        elif len(unique_locations) <= 2:
            compatibility_score = 0.8
        else:
            compatibility_score = 0.6
        
        score += compatibility_score * 0.15  # 15% weight on compatibility
        
        return min(1.0, score)

    def _run(self, current_combinations: List[dict], client_requirements: dict, 
             beam_width: int = 3) -> str:
        """
        Execute beam search algorithm to find top vendor combinations.
        """
        if not current_combinations:
            return json.dumps({
                "top_combinations": [],
                "beam_width": beam_width,
                "total_evaluated": 0,
                "message": "No combinations provided for evaluation"
            })
        
        # Score all combinations
        scored_combinations = []
        for combination in current_combinations:
            score = self._calculate_combination_score(combination, client_requirements)
            scored_combinations.append({
                "combination": combination,
                "score": round(score, 4)
            })
        
        # Sort by score (highest first) and keep top k
        scored_combinations.sort(key=lambda x: x['score'], reverse=True)
        top_combinations = scored_combinations[:beam_width]
        
        result = {
            "top_combinations": top_combinations,
            "beam_width": beam_width,
            "total_evaluated": len(current_combinations),
            "score_range": {
                "highest": top_combinations[0]['score'] if top_combinations else 0,
                "lowest": top_combinations[-1]['score'] if top_combinations else 0
            },
            "recommendations": []
        }
        
        # Add recommendations based on scores
        if top_combinations:
            best_score = top_combinations[0]['score']
            if best_score >= 0.8:
                result["recommendations"].append("Excellent combinations found - ready for client presentation")
            elif best_score >= 0.6:
                result["recommendations"].append("Good combinations available - minor optimizations possible")
            else:
                result["recommendations"].append("Consider exploring additional vendor options for better matches")
        
        return json.dumps(result, indent=2)


class StateManagementToolInput(BaseModel):
    """Input schema for StateManagementTool"""
    workflow_state: dict = Field(..., description="Current workflow state to manage")
    action: str = Field(..., description="Action to perform: save, load, update, or reset")
    state_key: str = Field(default="current", description="State key for storage")


class StateManagementTool(BaseTool):
    """
    Manages workflow state for LangGraph integration and persistence.
    Handles state transitions and checkpointing for complex workflows.
    """
    name: str = "Workflow State Management Tool"
    description: str = "Manages workflow state persistence and transitions for event planning processes"
    args_schema: type[BaseModel] = StateManagementToolInput

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._state_storage = {}  # In-memory storage (would be database in production)

    def _run(self, workflow_state: dict, action: str, state_key: str = "current") -> str:
        """
        Execute state management operations.
        """
        result = {
            "action": action,
            "state_key": state_key,
            "timestamp": "2024-01-01T00:00:00Z",  # Would use actual timestamp
            "success": False,
            "message": ""
        }
        
        try:
            if action == "save":
                self._state_storage[state_key] = workflow_state.copy()
                result["success"] = True
                result["message"] = f"State saved successfully with key '{state_key}'"
                
            elif action == "load":
                if state_key in self._state_storage:
                    result["workflow_state"] = self._state_storage[state_key]
                    result["success"] = True
                    result["message"] = f"State loaded successfully from key '{state_key}'"
                else:
                    result["message"] = f"No state found with key '{state_key}'"
                    
            elif action == "update":
                if state_key in self._state_storage:
                    self._state_storage[state_key].update(workflow_state)
                    result["success"] = True
                    result["message"] = f"State updated successfully for key '{state_key}'"
                else:
                    # Create new state if doesn't exist
                    self._state_storage[state_key] = workflow_state.copy()
                    result["success"] = True
                    result["message"] = f"New state created with key '{state_key}'"
                    
            elif action == "reset":
                if state_key in self._state_storage:
                    del self._state_storage[state_key]
                    result["success"] = True
                    result["message"] = f"State reset for key '{state_key}'"
                else:
                    result["message"] = f"No state found to reset with key '{state_key}'"
                    
            else:
                result["message"] = f"Unknown action '{action}'. Valid actions: save, load, update, reset"
                
        except Exception as e:
            result["message"] = f"Error during {action} operation: {str(e)}"
        
        return json.dumps(result, indent=2)


class ClientCommunicationToolInput(BaseModel):
    """Input schema for ClientCommunicationTool"""
    message_type: str = Field(..., description="Type of communication: status_update, options_presentation, or confirmation_request")
    content: dict = Field(..., description="Content to communicate to client")
    client_context: dict = Field(..., description="Client context and preferences")


class ClientCommunicationTool(BaseTool):
    """
    Handles client interactions and communication during the planning process.
    Formats information for client presentation and manages feedback collection.
    """
    name: str = "Client Communication Tool"
    description: str = "Manages client communication, status updates, and option presentations"
    args_schema: type[BaseModel] = ClientCommunicationToolInput

    def _format_status_update(self, content: dict, client_context: dict) -> dict:
        """Format workflow status update for client"""
        client_name = client_context.get('clientName', 'Valued Client')
        
        status_message = {
            "greeting": f"Hello {client_name},",
            "status": content.get('current_status', 'Processing your event planning request'),
            "progress": {
                "completed_steps": content.get('completed_steps', []),
                "current_step": content.get('current_step', 'Vendor sourcing'),
                "next_steps": content.get('next_steps', [])
            },
            "estimated_completion": content.get('estimated_completion', 'Within 24 hours'),
            "message": "We're working diligently to create the perfect event plan for you."
        }
        
        return status_message

    def _format_options_presentation(self, content: dict, client_context: dict) -> dict:
        """Format vendor combination options for client review"""
        client_name = client_context.get('clientName', 'Valued Client')
        combinations = content.get('vendor_combinations', [])
        
        presentation = {
            "greeting": f"Dear {client_name},",
            "message": "We've identified the best vendor combinations for your event. Please review the options below:",
            "options": [],
            "selection_instructions": "Please select your preferred combination, or let us know if you'd like to see additional options."
        }
        
        for i, combo in enumerate(combinations[:3], 1):  # Present top 3
            option = {
                "option_number": i,
                "overall_score": combo.get('score', 0),
                "vendors": {},
                "estimated_total_cost": 0,
                "highlights": []
            }
            
            vendors = combo.get('combination', {}).get('vendors', {})
            budget_allocation = combo.get('combination', {}).get('budget_allocation', {})
            
            total_cost = 0
            for service_type, vendor in vendors.items():
                service_title = service_type.replace('_', ' ').title()
                vendor_info = {
                    "name": vendor.get('name', 'Unknown'),
                    "location": vendor.get('location_city', 'TBD'),
                    "allocated_budget": budget_allocation.get(service_type, 0)
                }
                
                # Add estimated cost
                if service_type == 'venue':
                    cost = vendor.get('rental_cost', 0)
                elif service_type == 'caterer':
                    price_per_plate = vendor.get('min_veg_price', 0)
                    guest_count = max(client_context.get('guestCount', {}).values() or [200])
                    cost = price_per_plate * guest_count
                elif service_type == 'photographer':
                    cost = vendor.get('photo_package_price', 0)
                elif service_type == 'makeup_artist':
                    cost = vendor.get('bridal_makeup_price', 0)
                else:
                    cost = 0
                
                vendor_info["estimated_cost"] = cost
                total_cost += cost
                
                option["vendors"][service_title] = vendor_info
            
            option["estimated_total_cost"] = total_cost
            
            # Add highlights based on score
            score = combo.get('score', 0)
            if score >= 0.8:
                option["highlights"].append("Excellent match for your requirements")
            if total_cost < sum(budget_allocation.values()) * 0.9:
                option["highlights"].append("Great value within budget")
            
            presentation["options"].append(option)
        
        return presentation

    def _format_confirmation_request(self, content: dict, client_context: dict) -> dict:
        """Format confirmation request for client approval"""
        client_name = client_context.get('clientName', 'Valued Client')
        
        confirmation = {
            "greeting": f"Dear {client_name},",
            "message": "Please confirm the following details for your event:",
            "details_to_confirm": content.get('confirmation_items', []),
            "next_steps": content.get('next_steps', []),
            "response_required": True,
            "deadline": content.get('response_deadline', 'Within 48 hours')
        }
        
        return confirmation

    def _run(self, message_type: str, content: dict, client_context: dict) -> str:
        """
        Execute client communication based on message type.
        """
        try:
            if message_type == "status_update":
                formatted_message = self._format_status_update(content, client_context)
            elif message_type == "options_presentation":
                formatted_message = self._format_options_presentation(content, client_context)
            elif message_type == "confirmation_request":
                formatted_message = self._format_confirmation_request(content, client_context)
            else:
                return json.dumps({
                    "error": f"Unknown message type: {message_type}",
                    "valid_types": ["status_update", "options_presentation", "confirmation_request"]
                })
            
            result = {
                "message_type": message_type,
                "formatted_message": formatted_message,
                "delivery_status": "ready_for_delivery",
                "client_id": client_context.get('clientId', 'unknown'),
                "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": f"Failed to format {message_type}: {str(e)}",
                "message_type": message_type
            })


def create_orchestrator_agent() -> Agent:
    """
    Create and configure the Orchestrator Agent with beam search coordination capabilities.
    
    Returns:
        Agent: Configured CrewAI Orchestrator Agent
    """
    # Initialize LLM
    llm = OllamaLLM(model="gemma:2b")
    
    # Initialize tools
    beam_search_tool = BeamSearchTool()
    state_management_tool = StateManagementTool()
    client_communication_tool = ClientCommunicationTool()
    
    # Create agent
    orchestrator_agent = Agent(
        role="Event Planning Coordinator",
        goal="Find optimal event combinations through collaborative agent workflow and manage the overall planning process",
        backstory="""You are an expert event planning coordinator with deep knowledge of vendor optimization 
        and workflow management. You excel at coordinating multiple agents, managing complex workflows, 
        and ensuring client satisfaction through systematic planning approaches. Your expertise includes 
        beam search optimization, state management, and seamless client communication.""",
        verbose=True,
        allow_delegation=True,
        tools=[beam_search_tool, state_management_tool, client_communication_tool],
        llm=llm,
        max_iter=10,
        memory=True
    )
    
    return orchestrator_agent


def create_orchestrator_tasks(client_data: dict) -> List[Task]:
    """
    Create tasks for the Orchestrator Agent.
    
    Args:
        client_data: Client requirements and context
        
    Returns:
        List[Task]: List of tasks for the orchestrator agent
    """
    
    # Task 1: Initialize planning workflow
    initialization_task = Task(
        description=f"""Initialize the event planning workflow for client: {client_data.get('clientName', 'Unknown')}
        
        Client Requirements:
        - Guest Count: {client_data.get('guestCount', {})}
        - Vision: {client_data.get('clientVision', '')}
        - Budget: {client_data.get('budget', 'TBD')}
        
        Your responsibilities:
        1. Set up workflow state management
        2. Send initial status update to client
        3. Coordinate with other agents for vendor sourcing and budget allocation
        4. Establish beam search parameters (k=3)
        
        Expected Output: Workflow initialization status and next steps for agent coordination""",
        expected_output="JSON object containing workflow initialization status, client communication confirmation, and coordination plan for other agents",
        agent=None,  # Will be set when creating the crew
        tools=[StateManagementTool(), ClientCommunicationTool()]
    )
    
    # Task 2: Coordinate beam search optimization
    beam_search_task = Task(
        description="""Coordinate beam search optimization across vendor combinations.
        
        Your responsibilities:
        1. Collect vendor combinations from sourcing agents
        2. Apply beam search algorithm with k=3 optimization
        3. Evaluate combinations using fitness scoring
        4. Maintain top 3 combinations for client presentation
        
        Expected Output: Top 3 optimized vendor combinations with scores and rationale""",
        expected_output="JSON object with top 3 vendor combinations, their fitness scores, and optimization rationale",
        agent=None,  # Will be set when creating the crew
        tools=[BeamSearchTool(), StateManagementTool()]
    )
    
    # Task 3: Present options to client
    client_presentation_task = Task(
        description="""Present optimized vendor combinations to client for selection.
        
        Your responsibilities:
        1. Format vendor combinations for client presentation
        2. Include cost breakdowns and highlights
        3. Provide clear selection instructions
        4. Manage client feedback and selection process
        
        Expected Output: Formatted client presentation and selection confirmation""",
        expected_output="Professional client presentation with vendor options, cost analysis, and selection interface",
        agent=None,  # Will be set when creating the crew
        tools=[ClientCommunicationTool(), StateManagementTool()]
    )
    
    return [initialization_task, beam_search_task, client_presentation_task]