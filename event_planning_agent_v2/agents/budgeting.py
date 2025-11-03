"""
Budgeting Agent for Event Planning System

This agent specializes in financial optimization and budget allocation,
implementing Gemma-2B LLM integration while preserving existing budget 
allocation and fitness calculation logic.
"""

import json
from typing import Dict, List, Any, Optional
from crewai import Agent, Task
try:
    from langchain_ollama import OllamaLLM
except ImportError:
    from langchain_community.llms import Ollama as OllamaLLM

# Import existing budget tools
from ..tools.budget_tools import BudgetAllocationTool, FitnessCalculationTool


def create_budgeting_agent() -> Agent:
    """
    Create and configure the Budgeting Agent with Gemma-2B LLM integration.
    
    Preserves existing budget allocation and fitness calculation logic while
    adding integration with calculation MCP server capabilities.
    
    Returns:
        Agent: Configured CrewAI Budgeting Agent
    """
    # Initialize Gemma-2B LLM
    llm = OllamaLLM(model="gemma:2b")
    
    # Initialize budget tools (preserving existing logic)
    budget_allocation_tool = BudgetAllocationTool()
    fitness_calculation_tool = FitnessCalculationTool()
    
    # Create budgeting agent
    budgeting_agent = Agent(
        role="Financial Optimization Specialist",
        goal="Optimize budget allocation and calculate combination fitness scores to maximize value within client constraints",
        backstory="""You are a financial expert specializing in event budget optimization with deep knowledge 
        of cost allocation strategies and vendor pricing models. You excel at creating multiple budget scenarios, 
        calculating fitness scores for vendor combinations, and ensuring optimal financial outcomes. Your expertise 
        includes the preserved calculateFitnessScore algorithm, multi-strategy budget allocation, and integration 
        with advanced calculation services for enhanced optimization.""",
        verbose=True,
        allow_delegation=False,  # Budgeting agent works independently
        tools=[budget_allocation_tool, fitness_calculation_tool],
        llm=llm,
        max_iter=5,
        memory=True
    )
    
    return budgeting_agent


def create_budget_allocation_task(client_requirements: dict, total_budget: float) -> Task:
    """
    Create budget allocation task for the Budgeting Agent.
    
    Args:
        client_requirements: Client requirements and preferences
        total_budget: Total budget amount for allocation
        
    Returns:
        Task: Budget allocation task
    """
    
    guest_count = max(client_requirements.get('guestCount', {}).values() or [200])
    client_vision = client_requirements.get('clientVision', '')
    service_types = ["venue", "caterer", "photographer", "makeup_artist"]
    
    task = Task(
        description=f"""Generate optimal budget allocation strategies for the event planning.
        
        Client Details:
        - Total Budget: ₹{total_budget:,}
        - Guest Count: {guest_count}
        - Client Vision: "{client_vision}"
        - Required Services: {', '.join(service_types)}
        
        Your responsibilities:
        1. Analyze client requirements to determine event type (luxury, standard, intimate)
        2. Generate 3 different budget allocation strategies using preserved allocation templates
        3. Calculate fitness scores for each strategy using existing calculateFitnessScore algorithm
        4. Provide detailed breakdown with percentages and absolute amounts
        5. Recommend the optimal strategy based on client preferences
        
        Use the BudgetAllocationTool to generate multiple allocation strategies and ensure 
        compatibility with existing fitness calculation logic.
        
        Expected Output: Comprehensive budget allocation with 3 strategies, fitness scores, and recommendation""",
        expected_output="""JSON object containing:
        - total_budget: budget amount
        - event_type: determined event category
        - allocation_strategies: array of 3 strategies with allocations and fitness scores
        - recommended_strategy: best strategy with rationale
        - service_breakdown: detailed per-service allocation with percentages""",
        agent=None,  # Will be set when creating the crew
        tools=[BudgetAllocationTool()]
    )
    
    return task


def create_fitness_calculation_task(vendor_combinations: List[dict], 
                                  client_requirements: dict, 
                                  budget_allocation: dict) -> Task:
    """
    Create fitness calculation task for evaluating vendor combinations.
    
    Args:
        vendor_combinations: List of vendor combinations to evaluate
        client_requirements: Client requirements and preferences
        budget_allocation: Budget allocation strategy
        
    Returns:
        Task: Fitness calculation task
    """
    
    task = Task(
        description=f"""Calculate comprehensive fitness scores for vendor combinations.
        
        Evaluation Context:
        - Number of Combinations: {len(vendor_combinations)}
        - Client Vision: "{client_requirements.get('clientVision', '')}"
        - Budget Strategy: {budget_allocation.get('strategy', 'Unknown')}
        
        Your responsibilities:
        1. Evaluate each vendor combination using the preserved calculateFitnessScore algorithm
        2. Calculate budget fitness (40% weight) - how well vendors fit within allocated budgets
        3. Calculate preference fitness (45% weight) - how well vendors match client preferences
        4. Calculate compatibility fitness (15% weight) - vendor coordination feasibility
        5. Provide detailed component scores and overall fitness for each combination
        6. Generate recommendations for optimization
        
        Use the FitnessCalculationTool to maintain compatibility with existing scoring logic
        while providing enhanced analysis capabilities.
        
        Expected Output: Detailed fitness analysis for all vendor combinations with component breakdowns""",
        expected_output="""JSON object containing:
        - evaluated_combinations: array of combinations with detailed fitness scores
        - component_analysis: breakdown of budget, preference, and compatibility scores
        - ranking: combinations sorted by overall fitness score
        - optimization_recommendations: suggestions for improving low-scoring combinations
        - summary_statistics: min, max, average fitness scores""",
        agent=None,  # Will be set when creating the crew
        tools=[FitnessCalculationTool()]
    )
    
    return task


def create_budget_optimization_task(initial_allocation: dict, 
                                  vendor_feedback: dict, 
                                  client_requirements: dict) -> Task:
    """
    Create budget optimization task for refining allocations based on vendor feedback.
    
    Args:
        initial_allocation: Initial budget allocation strategy
        vendor_feedback: Feedback from vendor sourcing (costs, availability)
        client_requirements: Client requirements and preferences
        
    Returns:
        Task: Budget optimization task
    """
    
    task = Task(
        description=f"""Optimize budget allocation based on real vendor pricing and availability feedback.
        
        Optimization Context:
        - Initial Strategy: {initial_allocation.get('strategy', 'Unknown')}
        - Total Budget: ₹{initial_allocation.get('total_budget', 0):,}
        - Vendor Feedback Available: {len(vendor_feedback)} service categories
        
        Your responsibilities:
        1. Analyze actual vendor costs vs. initial budget allocations
        2. Identify budget overruns and opportunities for reallocation
        3. Generate optimized allocation that maximizes value within constraints
        4. Preserve client priorities while adjusting for market realities
        5. Calculate fitness scores for optimized allocation
        6. Provide clear rationale for all budget adjustments
        
        Use both BudgetAllocationTool and FitnessCalculationTool to create an optimized
        allocation that balances client preferences with vendor market realities.
        
        Expected Output: Optimized budget allocation with detailed adjustment rationale""",
        expected_output="""JSON object containing:
        - original_allocation: initial budget strategy
        - optimized_allocation: adjusted allocation based on vendor feedback
        - adjustments_made: detailed list of changes and rationale
        - cost_variance_analysis: comparison of budgeted vs actual vendor costs
        - fitness_improvement: before/after fitness score comparison
        - risk_assessment: potential issues with optimized allocation""",
        agent=None,  # Will be set when creating the crew
        tools=[BudgetAllocationTool(), FitnessCalculationTool()]
    )
    
    return task


class BudgetingAgentCoordinator:
    """
    Coordinator class for managing Budgeting Agent workflows and MCP server integration.
    
    This class handles the integration between CrewAI budgeting agent and calculation
    MCP server while preserving existing algorithm logic.
    """
    
    def __init__(self):
        self.agent = create_budgeting_agent()
        self.mcp_integration_enabled = False  # Will be enabled when MCP servers are available
    
    def generate_budget_strategies(self, client_requirements: dict, total_budget: float) -> dict:
        """
        Generate multiple budget allocation strategies for client requirements.
        
        Args:
            client_requirements: Client requirements and preferences
            total_budget: Total budget amount
            
        Returns:
            dict: Budget allocation strategies with fitness scores
        """
        # Create and execute budget allocation task
        task = create_budget_allocation_task(client_requirements, total_budget)
        task.agent = self.agent
        
        # Execute task (in a real implementation, this would be part of a Crew)
        # For now, we'll use the tool directly to demonstrate functionality
        budget_tool = BudgetAllocationTool()
        
        result = budget_tool._run(
            total_budget=total_budget,
            client_requirements=client_requirements,
            service_types=["venue", "caterer", "photographer", "makeup_artist"]
        )
        
        return json.loads(result)
    
    def calculate_combination_fitness(self, vendor_combinations: List[dict], 
                                    client_requirements: dict, 
                                    budget_allocation: dict) -> List[dict]:
        """
        Calculate fitness scores for vendor combinations.
        
        Args:
            vendor_combinations: List of vendor combinations to evaluate
            client_requirements: Client requirements and preferences
            budget_allocation: Budget allocation strategy
            
        Returns:
            List[dict]: Vendor combinations with fitness scores
        """
        fitness_tool = FitnessCalculationTool()
        scored_combinations = []
        
        for combination in vendor_combinations:
            # Calculate fitness for each combination
            result = fitness_tool._run(
                vendor_combination=combination.get('vendors', {}),
                client_requirements=client_requirements,
                budget_allocation=budget_allocation.get('allocation', {})
            )
            
            fitness_data = json.loads(result)
            
            # Add fitness data to combination
            combination['fitness_analysis'] = fitness_data
            combination['overall_fitness_score'] = fitness_data.get('overall_fitness_score', 0)
            
            scored_combinations.append(combination)
        
        # Sort by fitness score (highest first)
        scored_combinations.sort(key=lambda x: x.get('overall_fitness_score', 0), reverse=True)
        
        return scored_combinations
    
    def optimize_budget_allocation(self, initial_allocation: dict, 
                                 vendor_costs: dict, 
                                 client_requirements: dict) -> dict:
        """
        Optimize budget allocation based on actual vendor costs.
        
        Args:
            initial_allocation: Initial budget allocation
            vendor_costs: Actual vendor costs from sourcing
            client_requirements: Client requirements
            
        Returns:
            dict: Optimized budget allocation
        """
        # Analyze cost variances
        variances = {}
        total_budget = initial_allocation.get('total_budget', 0)
        original_allocation = initial_allocation.get('allocation', {})
        
        for service_type, allocated_amount in original_allocation.items():
            actual_cost = vendor_costs.get(service_type, 0)
            variance = actual_cost - allocated_amount
            variance_percentage = (variance / allocated_amount) * 100 if allocated_amount > 0 else 0
            
            variances[service_type] = {
                'allocated': allocated_amount,
                'actual': actual_cost,
                'variance': variance,
                'variance_percentage': variance_percentage
            }
        
        # Generate optimized allocation
        budget_tool = BudgetAllocationTool()
        
        # Adjust client requirements to reflect cost realities
        adjusted_requirements = client_requirements.copy()
        adjusted_requirements['cost_feedback'] = vendor_costs
        
        optimized_result = budget_tool._run(
            total_budget=total_budget,
            client_requirements=adjusted_requirements,
            service_types=list(original_allocation.keys())
        )
        
        optimized_data = json.loads(optimized_result)
        
        return {
            'original_allocation': initial_allocation,
            'optimized_allocation': optimized_data.get('recommended_strategy', {}),
            'cost_variances': variances,
            'optimization_rationale': self._generate_optimization_rationale(variances),
            'total_budget': total_budget
        }
    
    def _generate_optimization_rationale(self, variances: dict) -> List[str]:
        """Generate rationale for budget optimization decisions."""
        rationale = []
        
        for service_type, variance_data in variances.items():
            variance_pct = variance_data['variance_percentage']
            
            if variance_pct > 20:
                rationale.append(f"{service_type.title()} costs exceed budget by {variance_pct:.1f}% - reallocation needed")
            elif variance_pct < -10:
                rationale.append(f"{service_type.title()} costs are {abs(variance_pct):.1f}% under budget - opportunity for upgrade")
            else:
                rationale.append(f"{service_type.title()} costs align well with budget allocation")
        
        return rationale
    
    def integrate_mcp_calculation_server(self, mcp_client):
        """
        Integrate with calculation MCP server for enhanced optimization.
        
        Args:
            mcp_client: MCP client for calculation server
        """
        self.mcp_client = mcp_client
        self.mcp_integration_enabled = True
        
        # In a full implementation, this would enable enhanced calculation capabilities
        # through the MCP server, such as:
        # - Advanced optimization algorithms
        # - Machine learning-based cost prediction
        # - Market trend analysis
        # - Risk assessment calculations
    
    def get_agent_performance_metrics(self) -> dict:
        """
        Get performance metrics for the budgeting agent.
        
        Returns:
            dict: Performance metrics and statistics
        """
        return {
            'agent_type': 'budgeting',
            'llm_model': 'gemma:2b',
            'tools_available': ['BudgetAllocationTool', 'FitnessCalculationTool'],
            'mcp_integration': self.mcp_integration_enabled,
            'capabilities': [
                'Multi-strategy budget allocation',
                'Fitness score calculation',
                'Cost variance analysis',
                'Budget optimization',
                'Client preference integration'
            ],
            'preserved_algorithms': [
                'calculateFitnessScore',
                'Budget allocation templates',
                'Weighted linear scoring'
            ]
        }