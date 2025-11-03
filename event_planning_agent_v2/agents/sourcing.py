"""
Sourcing Agent for Event Planning System

This agent specializes in vendor procurement and qualification,
implementing TinyLLaMA for requirement parsing while preserving existing
SQL filtering and vendor ranking algorithms.
"""

import json
from typing import Dict, List, Any, Optional
from crewai import Agent, Task
try:
    from langchain_ollama import OllamaLLM
except ImportError:
    from langchain_community.llms import Ollama as OllamaLLM

# Import existing vendor tools
from ..tools.vendor_tools import HybridFilterTool, VendorDatabaseTool, VendorRankingTool


def create_sourcing_agent() -> Agent:
    """
    Create and configure the Sourcing Agent with TinyLLaMA for requirement parsing.
    
    Preserves existing SQL filtering and vendor ranking algorithms while
    integrating with vendor data MCP server for enhanced capabilities.
    
    Returns:
        Agent: Configured CrewAI Sourcing Agent
    """
    # Initialize TinyLLaMA for requirement parsing
    llm = OllamaLLM(model="tinyllama")
    
    # Initialize vendor tools (preserving existing logic)
    hybrid_filter_tool = HybridFilterTool()
    vendor_database_tool = VendorDatabaseTool()
    vendor_ranking_tool = VendorRankingTool()
    
    # Create sourcing agent
    sourcing_agent = Agent(
        role="Vendor Sourcing Specialist",
        goal="Find and rank optimal vendors based on client requirements using advanced filtering and scoring algorithms",
        backstory="""You are a procurement expert with deep vendor network knowledge and advanced filtering capabilities. 
        You excel at parsing complex client requirements, executing sophisticated database queries, and ranking vendors 
        using weighted linear scoring models. Your expertise includes the preserved SQL filtering algorithms, 
        hybrid requirement processing, and integration with enhanced vendor data services for comprehensive sourcing.""",
        verbose=True,
        allow_delegation=False,  # Sourcing agent works independently
        tools=[hybrid_filter_tool, vendor_database_tool, vendor_ranking_tool],
        llm=llm,
        max_iter=8,  # More iterations for complex sourcing tasks
        memory=True
    )
    
    return sourcing_agent


def create_vendor_sourcing_task(client_requirements: dict, 
                               service_type: str, 
                               budget_allocation: dict) -> Task:
    """
    Create vendor sourcing task for a specific service type.
    
    Args:
        client_requirements: Client requirements and preferences
        service_type: Type of service to source (venue, caterer, photographer, makeup_artist)
        budget_allocation: Budget allocation for this service type
        
    Returns:
        Task: Vendor sourcing task
    """
    
    allocated_budget = budget_allocation.get(service_type, 0)
    client_vision = client_requirements.get('clientVision', '')
    guest_count = max(client_requirements.get('guestCount', {}).values() or [200])
    
    task = Task(
        description=f"""Source and rank optimal {service_type.replace('_', ' ')} vendors for the event.
        
        Sourcing Parameters:
        - Service Type: {service_type}
        - Allocated Budget: ₹{allocated_budget:,}
        - Guest Count: {guest_count}
        - Client Vision: "{client_vision}"
        
        Your responsibilities:
        1. Use HybridFilterTool to process client requirements into hard filters and soft preferences
        2. Apply VendorDatabaseTool to query PostgreSQL database with preserved SQL filtering logic
        3. Execute weighted linear scoring model to rank vendors
        4. Use VendorRankingTool to generate vendor summaries with LLM analysis
        5. Return top 5 ranked vendors with detailed scoring breakdown
        
        Preserve existing algorithms:
        - Deterministic hard filter logic
        - Parameterized SQL queries
        - Weighted linear scoring model
        - LLM-based soft preference extraction
        
        Expected Output: Top 5 ranked vendors with scores, summaries, and selection rationale""",
        expected_output=f"""JSON object containing:
        - service_type: "{service_type}"
        - allocated_budget: budget amount
        - hard_filters_applied: list of deterministic filters used
        - soft_preferences_extracted: LLM-parsed preferences
        - vendor_candidates: top 5 vendors with ranking scores
        - vendor_summaries: LLM-generated summaries for each vendor
        - selection_rationale: explanation of ranking methodology""",
        agent=None,  # Will be set when creating the crew
        tools=[HybridFilterTool(), VendorDatabaseTool(), VendorRankingTool()]
    )
    
    return task


def create_multi_service_sourcing_task(client_requirements: dict, 
                                     budget_allocation: dict, 
                                     service_types: List[str]) -> Task:
    """
    Create comprehensive sourcing task for multiple service types.
    
    Args:
        client_requirements: Client requirements and preferences
        budget_allocation: Budget allocation for all services
        service_types: List of service types to source
        
    Returns:
        Task: Multi-service sourcing task
    """
    
    total_budget = sum(budget_allocation.get(st, 0) for st in service_types)
    
    task = Task(
        description=f"""Source vendors for all required services with coordinated optimization.
        
        Multi-Service Sourcing:
        - Service Types: {', '.join(service_types)}
        - Total Budget: ₹{total_budget:,}
        - Services Count: {len(service_types)}
        
        Your responsibilities:
        1. Process client requirements for each service type using HybridFilterTool
        2. Execute coordinated database queries for all services
        3. Apply service-specific ranking algorithms while maintaining consistency
        4. Consider cross-service compatibility (location, timing, style)
        5. Generate comprehensive vendor summaries for client review
        6. Optimize for overall combination quality, not just individual service scores
        
        Use preserved algorithms for each service while ensuring compatibility across services.
        
        Expected Output: Comprehensive vendor sourcing results for all services with compatibility analysis""",
        expected_output="""JSON object containing:
        - services_sourced: array of service types processed
        - total_budget_allocated: sum of all service budgets
        - vendor_results: results for each service type with top candidates
        - compatibility_analysis: cross-service compatibility assessment
        - location_distribution: geographic distribution of recommended vendors
        - coordination_recommendations: suggestions for vendor coordination""",
        agent=None,  # Will be set when creating the crew
        tools=[HybridFilterTool(), VendorDatabaseTool(), VendorRankingTool()]
    )
    
    return task


def create_vendor_validation_task(vendor_combinations: List[dict], 
                                client_requirements: dict) -> Task:
    """
    Create vendor validation task to verify sourced vendors meet requirements.
    
    Args:
        vendor_combinations: List of vendor combinations to validate
        client_requirements: Original client requirements
        
    Returns:
        Task: Vendor validation task
    """
    
    task = Task(
        description=f"""Validate sourced vendor combinations against client requirements.
        
        Validation Context:
        - Combinations to Validate: {len(vendor_combinations)}
        - Client Vision: "{client_requirements.get('clientVision', '')}"
        
        Your responsibilities:
        1. Re-verify each vendor against original hard filters
        2. Validate soft preference matching using LLM analysis
        3. Check vendor availability and capacity constraints
        4. Assess vendor combination compatibility
        5. Identify any requirement gaps or mismatches
        6. Generate validation report with pass/fail status
        
        Use HybridFilterTool to re-process requirements and VendorRankingTool 
        to generate updated summaries if needed.
        
        Expected Output: Comprehensive validation report with recommendations""",
        expected_output="""JSON object containing:
        - validation_summary: overall validation results
        - combination_results: validation status for each combination
        - requirement_compliance: detailed compliance check results
        - identified_issues: list of any problems found
        - recommendations: suggestions for addressing issues
        - approved_combinations: combinations that pass all validations""",
        agent=None,  # Will be set when creating the crew
        tools=[HybridFilterTool(), VendorDatabaseTool(), VendorRankingTool()]
    )
    
    return task


class SourcingAgentCoordinator:
    """
    Coordinator class for managing Sourcing Agent workflows and MCP server integration.
    
    This class handles the integration between CrewAI sourcing agent and vendor data
    MCP server while preserving existing algorithm logic.
    """
    
    def __init__(self):
        self.agent = create_sourcing_agent()
        self.mcp_integration_enabled = False  # Will be enabled when MCP servers are available
        self.vendor_cache = {}  # Cache for frequently accessed vendor data
    
    def source_vendors_for_service(self, client_requirements: dict, 
                                 service_type: str, 
                                 allocated_budget: float) -> dict:
        """
        Source vendors for a specific service type.
        
        Args:
            client_requirements: Client requirements and preferences
            service_type: Service type to source
            allocated_budget: Budget allocated for this service
            
        Returns:
            dict: Sourcing results with ranked vendors
        """
        # Step 1: Process client requirements into filters
        hybrid_filter_tool = HybridFilterTool()
        filter_result = hybrid_filter_tool._run(
            client_data=client_requirements,
            service_type=service_type
        )
        
        filter_data = json.loads(filter_result)
        
        # Add budget to hard filters
        filter_data['hard_filters']['budget'] = allocated_budget
        
        # Step 2: Query database with filters
        vendor_db_tool = VendorDatabaseTool()
        vendor_result = vendor_db_tool._run(
            filter_json_string=json.dumps(filter_data)
        )
        
        vendors = json.loads(vendor_result)
        
        # Step 3: Generate vendor summaries
        if vendors and len(vendors) > 0:
            ranking_tool = VendorRankingTool()
            summary_result = ranking_tool._run(
                vendors_json_string=json.dumps(vendors),
                client_vision=client_requirements.get('clientVision', '')
            )
            
            summaries = json.loads(summary_result)
        else:
            summaries = {}
        
        # Combine results
        sourcing_results = {
            'service_type': service_type,
            'allocated_budget': allocated_budget,
            'filters_applied': filter_data,
            'vendors_found': len(vendors) if isinstance(vendors, list) else 0,
            'top_vendors': vendors[:5] if isinstance(vendors, list) else [],
            'vendor_summaries': summaries,
            'sourcing_status': 'success' if vendors else 'no_vendors_found'
        }
        
        return sourcing_results
    
    def source_all_services(self, client_requirements: dict, 
                          budget_allocation: dict) -> dict:
        """
        Source vendors for all required services.
        
        Args:
            client_requirements: Client requirements and preferences
            budget_allocation: Budget allocation for all services
            
        Returns:
            dict: Comprehensive sourcing results
        """
        service_types = list(budget_allocation.keys())
        all_results = {}
        
        for service_type in service_types:
            allocated_budget = budget_allocation.get(service_type, 0)
            
            if allocated_budget > 0:
                service_results = self.source_vendors_for_service(
                    client_requirements, service_type, allocated_budget
                )
                all_results[service_type] = service_results
        
        # Analyze compatibility across services
        compatibility_analysis = self._analyze_cross_service_compatibility(all_results)
        
        return {
            'services_sourced': service_types,
            'total_services': len(service_types),
            'sourcing_results': all_results,
            'compatibility_analysis': compatibility_analysis,
            'overall_status': self._determine_overall_status(all_results)
        }
    
    def generate_vendor_combinations(self, sourcing_results: dict, 
                                   max_combinations: int = 10) -> List[dict]:
        """
        Generate vendor combinations from sourcing results.
        
        Args:
            sourcing_results: Results from source_all_services
            max_combinations: Maximum number of combinations to generate
            
        Returns:
            List[dict]: List of vendor combinations
        """
        combinations = []
        service_results = sourcing_results.get('sourcing_results', {})
        
        # Get top vendors for each service
        service_vendors = {}
        for service_type, results in service_results.items():
            top_vendors = results.get('top_vendors', [])
            if top_vendors:
                service_vendors[service_type] = top_vendors[:3]  # Top 3 per service
        
        # Generate combinations (simplified - would use more sophisticated logic in production)
        if len(service_vendors) > 0:
            # For now, create combinations using first vendor from each service
            # In a full implementation, this would generate all permutations up to max_combinations
            
            base_combination = {}
            for service_type, vendors in service_vendors.items():
                if vendors:
                    base_combination[service_type] = vendors[0]
            
            if base_combination:
                combinations.append({
                    'combination_id': 1,
                    'vendors': base_combination,
                    'total_services': len(base_combination),
                    'generation_method': 'top_vendor_selection'
                })
        
        return combinations
    
    def _analyze_cross_service_compatibility(self, sourcing_results: dict) -> dict:
        """Analyze compatibility between vendors across services."""
        compatibility = {
            'location_analysis': {},
            'style_consistency': {},
            'coordination_complexity': 'low'
        }
        
        # Analyze location distribution
        locations = []
        for service_type, results in sourcing_results.items():
            top_vendors = results.get('top_vendors', [])
            for vendor in top_vendors[:3]:  # Top 3 per service
                location = vendor.get('location_city')
                if location:
                    locations.append(location)
        
        unique_locations = set(locations)
        compatibility['location_analysis'] = {
            'total_locations': len(unique_locations),
            'locations': list(unique_locations),
            'coordination_complexity': 'low' if len(unique_locations) <= 2 else 'high'
        }
        
        return compatibility
    
    def _determine_overall_status(self, sourcing_results: dict) -> str:
        """Determine overall sourcing status."""
        successful_services = sum(1 for results in sourcing_results.values() 
                                if results.get('sourcing_status') == 'success')
        total_services = len(sourcing_results)
        
        if successful_services == total_services:
            return 'all_services_sourced'
        elif successful_services > 0:
            return 'partial_sourcing_success'
        else:
            return 'sourcing_failed'
    
    def integrate_mcp_vendor_server(self, mcp_client):
        """
        Integrate with vendor data MCP server for enhanced capabilities.
        
        Args:
            mcp_client: MCP client for vendor data server
        """
        self.mcp_client = mcp_client
        self.mcp_integration_enabled = True
        
        # In a full implementation, this would enable enhanced vendor capabilities:
        # - Real-time vendor availability checking
        # - Enhanced vendor search with ML-based ranking
        # - Vendor compatibility checking
        # - Dynamic pricing updates
    
    def get_cached_vendors(self, service_type: str, filters: dict) -> Optional[List[dict]]:
        """Get cached vendor results if available."""
        cache_key = f"{service_type}_{hash(str(sorted(filters.items())))}"
        return self.vendor_cache.get(cache_key)
    
    def cache_vendors(self, service_type: str, filters: dict, vendors: List[dict]):
        """Cache vendor results for future use."""
        cache_key = f"{service_type}_{hash(str(sorted(filters.items())))}"
        self.vendor_cache[cache_key] = vendors
    
    def get_agent_performance_metrics(self) -> dict:
        """
        Get performance metrics for the sourcing agent.
        
        Returns:
            dict: Performance metrics and statistics
        """
        return {
            'agent_type': 'sourcing',
            'llm_model': 'tinyllama',
            'tools_available': ['HybridFilterTool', 'VendorDatabaseTool', 'VendorRankingTool'],
            'mcp_integration': self.mcp_integration_enabled,
            'cache_size': len(self.vendor_cache),
            'capabilities': [
                'Hybrid requirement processing',
                'SQL-based vendor filtering',
                'Weighted linear scoring',
                'LLM-based vendor summaries',
                'Cross-service compatibility analysis'
            ],
            'preserved_algorithms': [
                'Deterministic hard filters',
                'Parameterized SQL queries',
                'Weighted linear scoring model',
                'LLM soft preference extraction'
            ]
        }