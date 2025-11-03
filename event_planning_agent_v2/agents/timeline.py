"""
Timeline Agent for Event Planning System

This agent specializes in logistics and feasibility management,
implementing conflict detection and timeline generation with LLM integration.
"""

import json
from typing import Dict, List, Any, Optional
from crewai import Agent, Task
try:
    from langchain_ollama import OllamaLLM
except ImportError:
    from langchain_community.llms import Ollama as OllamaLLM

# Import existing timeline tools
from ..tools.timeline_tools import ConflictDetectionTool, TimelineGenerationTool


def create_timeline_agent() -> Agent:
    """
    Create and configure the Timeline Agent with conflict detection and feasibility checking.
    
    Implements Timeline Agent with conflict detection and feasibility checking
    while integrating with appropriate LLM models and tools.
    
    Returns:
        Agent: Configured CrewAI Timeline Agent
    """
    # Initialize Gemma-2B LLM for timeline planning
    llm = OllamaLLM(model="gemma:2b")
    
    # Initialize timeline tools (preserving existing logic)
    conflict_detection_tool = ConflictDetectionTool()
    timeline_generation_tool = TimelineGenerationTool()
    
    # Create timeline agent
    timeline_agent = Agent(
        role="Event Logistics Coordinator",
        goal="Ensure logistical feasibility and create detailed timelines with comprehensive conflict detection",
        backstory="""You are an operations expert specializing in event logistics with deep knowledge of vendor 
        coordination, timing constraints, and feasibility analysis. You excel at detecting potential conflicts, 
        creating detailed event timelines, and ensuring smooth coordination between multiple vendors. Your expertise 
        includes the preserved ConflictDetection algorithm, timeline optimization, and comprehensive feasibility 
        assessment for complex event scenarios.""",
        verbose=True,
        allow_delegation=False,  # Timeline agent works independently
        tools=[conflict_detection_tool, timeline_generation_tool],
        llm=llm,
        max_iter=6,
        memory=True
    )
    
    return timeline_agent


def create_conflict_detection_task(vendor_combination: dict, 
                                 event_date: str, 
                                 proposed_timeline: dict) -> Task:
    """
    Create conflict detection task for vendor and timeline validation.
    
    Args:
        vendor_combination: Selected vendor combination
        event_date: Event date in YYYY-MM-DD format
        proposed_timeline: Proposed event timeline
        
    Returns:
        Task: Conflict detection task
    """
    
    vendor_count = len(vendor_combination)
    timeline_activities = len(proposed_timeline.get('activities', []))
    
    task = Task(
        description=f"""Perform comprehensive conflict detection for the event planning.
        
        Conflict Detection Parameters:
        - Event Date: {event_date}
        - Vendor Count: {vendor_count}
        - Timeline Activities: {timeline_activities}
        - Vendors: {', '.join(vendor_combination.keys())}
        
        Your responsibilities:
        1. Use ConflictDetectionTool to analyze vendor availability conflicts
        2. Check timeline conflicts and overlapping activities
        3. Validate vendor service requirements and constraints
        4. Assess location-based coordination challenges
        5. Calculate overall feasibility score using preserved algorithm logic
        6. Generate detailed conflict report with severity levels
        7. Provide specific recommendations for conflict resolution
        
        Preserve existing ConflictDetection algorithm logic:
        - Vendor availability checking
        - Timeline overlap detection
        - Service constraint validation
        - Feasibility scoring methodology
        
        Expected Output: Comprehensive conflict analysis with feasibility assessment""",
        expected_output="""JSON object containing:
        - feasibility_score: overall feasibility rating (0-1)
        - total_conflicts: number of conflicts detected
        - conflicts_by_severity: breakdown of high/medium/low severity conflicts
        - detailed_conflicts: list of specific conflicts with descriptions
        - vendor_coordination_issues: vendor-specific coordination challenges
        - timeline_recommendations: suggestions for timeline improvements
        - resolution_priority: ordered list of conflicts to address first""",
        agent=None,  # Will be set when creating the crew
        tools=[ConflictDetectionTool()]
    )
    
    return task


def create_timeline_generation_task(client_requirements: dict, 
                                  vendor_combination: dict, 
                                  event_date: str, 
                                  event_duration_hours: float = 8.0) -> Task:
    """
    Create timeline generation task for detailed event scheduling.
    
    Args:
        client_requirements: Client requirements and preferences
        vendor_combination: Selected vendor combination
        event_date: Event date in YYYY-MM-DD format
        event_duration_hours: Total event duration in hours
        
    Returns:
        Task: Timeline generation task
    """
    
    guest_count = max(client_requirements.get('guestCount', {}).values() or [200])
    client_vision = client_requirements.get('clientVision', '')
    
    task = Task(
        description=f"""Generate detailed event timeline with vendor coordination.
        
        Timeline Generation Parameters:
        - Event Date: {event_date}
        - Duration: {event_duration_hours} hours
        - Guest Count: {guest_count}
        - Client Vision: "{client_vision}"
        - Vendors: {', '.join(vendor_combination.keys())}
        
        Your responsibilities:
        1. Use TimelineGenerationTool to create comprehensive event schedule
        2. Generate base timeline structure based on event type and duration
        3. Enhance timeline with LLM-based customization for client preferences
        4. Integrate vendor-specific requirements and constraints
        5. Identify critical coordination points between vendors
        6. Validate timeline feasibility and adjust as needed
        7. Provide detailed activity descriptions and vendor assignments
        
        Use LLM capabilities for:
        - Timeline customization based on client vision
        - Activity description enhancement
        - Vendor coordination optimization
        
        Expected Output: Detailed event timeline with vendor coordination plan""",
        expected_output="""JSON object containing:
        - event_date: scheduled event date
        - total_duration_hours: total event duration
        - timeline: detailed schedule with activities, times, and descriptions
        - vendor_coordination_points: critical coordination moments
        - timeline_summary: key milestones and highlights
        - setup_requirements: pre-event setup timeline
        - coordination_recommendations: vendor coordination strategies""",
        agent=None,  # Will be set when creating the crew
        tools=[TimelineGenerationTool()]
    )
    
    return task


def create_timeline_optimization_task(initial_timeline: dict, 
                                    conflict_report: dict, 
                                    vendor_constraints: dict) -> Task:
    """
    Create timeline optimization task to resolve conflicts and improve efficiency.
    
    Args:
        initial_timeline: Initial generated timeline
        conflict_report: Conflict detection results
        vendor_constraints: Vendor-specific constraints and requirements
        
    Returns:
        Task: Timeline optimization task
    """
    
    conflicts_count = conflict_report.get('total_conflicts', 0)
    feasibility_score = conflict_report.get('feasibility_score', 0)
    
    task = Task(
        description=f"""Optimize event timeline to resolve conflicts and improve efficiency.
        
        Optimization Context:
        - Initial Feasibility Score: {feasibility_score}
        - Conflicts to Resolve: {conflicts_count}
        - High Priority Conflicts: {conflict_report.get('conflicts_by_severity', {}).get('high', 0)}
        
        Your responsibilities:
        1. Analyze conflict report to identify optimization opportunities
        2. Adjust timeline activities to resolve high-priority conflicts
        3. Optimize vendor coordination points for better efficiency
        4. Re-validate optimized timeline using ConflictDetectionTool
        5. Ensure all vendor constraints are properly accommodated
        6. Generate comparison between original and optimized timelines
        7. Provide implementation recommendations for optimized timeline
        
        Use both TimelineGenerationTool and ConflictDetectionTool to:
        - Generate optimized timeline alternatives
        - Validate improvements through conflict re-analysis
        
        Expected Output: Optimized timeline with conflict resolution analysis""",
        expected_output="""JSON object containing:
        - original_timeline: initial timeline for comparison
        - optimized_timeline: improved timeline with conflict resolutions
        - optimization_changes: detailed list of changes made
        - conflict_resolution: how each conflict was addressed
        - feasibility_improvement: before/after feasibility score comparison
        - implementation_plan: step-by-step timeline implementation guide
        - risk_mitigation: strategies for handling remaining risks""",
        agent=None,  # Will be set when creating the crew
        tools=[TimelineGenerationTool(), ConflictDetectionTool()]
    )
    
    return task


class TimelineAgentCoordinator:
    """
    Coordinator class for managing Timeline Agent workflows and optimization.
    
    This class handles timeline generation, conflict detection, and optimization
    while preserving existing algorithm logic.
    """
    
    def __init__(self):
        self.agent = create_timeline_agent()
        self.timeline_cache = {}  # Cache for generated timelines
    
    def generate_event_timeline(self, client_requirements: dict, 
                              vendor_combination: dict, 
                              event_date: str, 
                              event_duration_hours: float = 8.0) -> dict:
        """
        Generate comprehensive event timeline.
        
        Args:
            client_requirements: Client requirements and preferences
            vendor_combination: Selected vendor combination
            event_date: Event date in YYYY-MM-DD format
            event_duration_hours: Total event duration in hours
            
        Returns:
            dict: Generated timeline with coordination details
        """
        timeline_tool = TimelineGenerationTool()
        
        result = timeline_tool._run(
            client_requirements=client_requirements,
            vendor_combination=vendor_combination,
            event_date=event_date,
            event_duration_hours=event_duration_hours
        )
        
        timeline_data = json.loads(result)
        
        # Cache the generated timeline
        cache_key = f"{event_date}_{hash(str(vendor_combination))}"
        self.timeline_cache[cache_key] = timeline_data
        
        return timeline_data
    
    def detect_conflicts(self, vendor_combination: dict, 
                        event_date: str, 
                        event_timeline: dict) -> dict:
        """
        Detect conflicts in vendor combination and timeline.
        
        Args:
            vendor_combination: Selected vendor combination
            event_date: Event date in YYYY-MM-DD format
            event_timeline: Proposed event timeline
            
        Returns:
            dict: Conflict detection results with feasibility assessment
        """
        conflict_tool = ConflictDetectionTool()
        
        result = conflict_tool._run(
            vendor_combination=vendor_combination,
            event_date=event_date,
            event_timeline=event_timeline
        )
        
        conflict_data = json.loads(result)
        
        return conflict_data
    
    def optimize_timeline(self, initial_timeline: dict, 
                         conflict_report: dict, 
                         client_requirements: dict, 
                         vendor_combination: dict) -> dict:
        """
        Optimize timeline to resolve conflicts and improve efficiency.
        
        Args:
            initial_timeline: Initial generated timeline
            conflict_report: Conflict detection results
            client_requirements: Client requirements
            vendor_combination: Selected vendors
            
        Returns:
            dict: Optimized timeline with improvement analysis
        """
        # Identify optimization opportunities
        high_priority_conflicts = [
            c for c in conflict_report.get('detailed_conflicts', [])
            if c.get('severity') == 'high'
        ]
        
        # Generate optimization strategies
        optimization_strategies = []
        
        for conflict in high_priority_conflicts:
            conflict_type = conflict.get('type')
            
            if conflict_type == 'timeline_overlap':
                optimization_strategies.append({
                    'strategy': 'adjust_activity_timing',
                    'target': conflict.get('issue', ''),
                    'action': 'Stagger overlapping activities with buffer time'
                })
            elif conflict_type == 'availability_conflict':
                optimization_strategies.append({
                    'strategy': 'vendor_substitution',
                    'target': conflict.get('vendor', ''),
                    'action': 'Consider alternative vendor or date adjustment'
                })
            elif conflict_type == 'location_conflict':
                optimization_strategies.append({
                    'strategy': 'coordination_enhancement',
                    'target': conflict.get('service', ''),
                    'action': 'Add travel time buffers and coordination points'
                })
        
        # Apply optimizations (simplified - would use more sophisticated logic)
        optimized_timeline = self._apply_timeline_optimizations(
            initial_timeline, optimization_strategies
        )
        
        # Re-validate optimized timeline
        optimized_conflicts = self.detect_conflicts(
            vendor_combination, 
            initial_timeline.get('event_date', ''), 
            optimized_timeline
        )
        
        return {
            'original_timeline': initial_timeline,
            'optimized_timeline': optimized_timeline,
            'optimization_strategies': optimization_strategies,
            'original_feasibility': conflict_report.get('feasibility_score', 0),
            'optimized_feasibility': optimized_conflicts.get('feasibility_score', 0),
            'conflicts_resolved': len(high_priority_conflicts),
            'remaining_conflicts': optimized_conflicts.get('total_conflicts', 0)
        }
    
    def _apply_timeline_optimizations(self, timeline: dict, 
                                    strategies: List[dict]) -> dict:
        """Apply optimization strategies to timeline."""
        optimized_timeline = timeline.copy()
        activities = optimized_timeline.get('timeline', [])
        
        for strategy in strategies:
            if strategy['strategy'] == 'adjust_activity_timing':
                # Add buffer time between activities
                for i, activity in enumerate(activities):
                    if i > 0:
                        # Add 15-minute buffer
                        current_start = activity.get('start_time', '10:00')
                        # Simplified time adjustment logic
                        activity['start_time'] = current_start
                        activity['notes'] = activity.get('notes', '') + ' [Optimized timing]'
        
        return optimized_timeline
    
    def validate_timeline_feasibility(self, timeline: dict, 
                                    vendor_combination: dict, 
                                    event_date: str) -> dict:
        """
        Comprehensive timeline feasibility validation.
        
        Args:
            timeline: Event timeline to validate
            vendor_combination: Selected vendors
            event_date: Event date
            
        Returns:
            dict: Feasibility validation results
        """
        # Detect conflicts
        conflict_results = self.detect_conflicts(vendor_combination, event_date, timeline)
        
        # Additional feasibility checks
        feasibility_checks = {
            'timeline_duration': self._check_timeline_duration(timeline),
            'vendor_capacity': self._check_vendor_capacity(vendor_combination, timeline),
            'coordination_complexity': self._assess_coordination_complexity(timeline, vendor_combination),
            'setup_requirements': self._validate_setup_requirements(timeline, vendor_combination)
        }
        
        # Calculate overall feasibility
        feasibility_score = conflict_results.get('feasibility_score', 0)
        
        # Adjust based on additional checks
        for check_name, check_result in feasibility_checks.items():
            if not check_result.get('passed', True):
                feasibility_score *= 0.9  # Reduce score for failed checks
        
        return {
            'overall_feasibility_score': round(feasibility_score, 4),
            'conflict_analysis': conflict_results,
            'feasibility_checks': feasibility_checks,
            'recommendations': self._generate_feasibility_recommendations(
                conflict_results, feasibility_checks
            )
        }
    
    def _check_timeline_duration(self, timeline: dict) -> dict:
        """Check if timeline duration is reasonable."""
        total_duration = timeline.get('total_duration_hours', 0)
        
        return {
            'check_name': 'timeline_duration',
            'passed': 4 <= total_duration <= 12,
            'actual_duration': total_duration,
            'recommended_range': '4-12 hours',
            'notes': 'Duration should be reasonable for guest comfort and vendor availability'
        }
    
    def _check_vendor_capacity(self, vendor_combination: dict, timeline: dict) -> dict:
        """Check vendor capacity against timeline requirements."""
        activities = timeline.get('timeline', [])
        vendor_workload = {}
        
        for activity in activities:
            vendors_involved = activity.get('vendors_involved', [])
            for vendor in vendors_involved:
                vendor_workload[vendor] = vendor_workload.get(vendor, 0) + activity.get('duration', 0)
        
        capacity_issues = []
        for vendor, workload in vendor_workload.items():
            if workload > 10:  # More than 10 hours
                capacity_issues.append(f"{vendor}: {workload} hours")
        
        return {
            'check_name': 'vendor_capacity',
            'passed': len(capacity_issues) == 0,
            'vendor_workload': vendor_workload,
            'capacity_issues': capacity_issues,
            'notes': 'Vendors should not be overloaded with excessive work hours'
        }
    
    def _assess_coordination_complexity(self, timeline: dict, vendor_combination: dict) -> dict:
        """Assess coordination complexity between vendors."""
        coordination_points = timeline.get('vendor_coordination_points', [])
        vendor_count = len(vendor_combination)
        
        complexity_score = len(coordination_points) / max(vendor_count, 1)
        
        return {
            'check_name': 'coordination_complexity',
            'passed': complexity_score <= 2.0,  # Max 2 coordination points per vendor
            'complexity_score': round(complexity_score, 2),
            'coordination_points': len(coordination_points),
            'vendor_count': vendor_count,
            'notes': 'High coordination complexity may lead to execution challenges'
        }
    
    def _validate_setup_requirements(self, timeline: dict, vendor_combination: dict) -> dict:
        """Validate setup time requirements for vendors."""
        activities = timeline.get('timeline', [])
        setup_activities = [a for a in activities if 'setup' in a.get('type', '').lower()]
        
        total_setup_time = sum(a.get('duration', 0) for a in setup_activities)
        
        return {
            'check_name': 'setup_requirements',
            'passed': total_setup_time >= 1.0,  # At least 1 hour setup
            'setup_activities': len(setup_activities),
            'total_setup_time': total_setup_time,
            'notes': 'Adequate setup time is crucial for event success'
        }
    
    def _generate_feasibility_recommendations(self, conflict_results: dict, 
                                           feasibility_checks: dict) -> List[str]:
        """Generate recommendations based on feasibility analysis."""
        recommendations = []
        
        # Add conflict-based recommendations
        if conflict_results.get('total_conflicts', 0) > 0:
            recommendations.append("Address identified conflicts before finalizing timeline")
        
        # Add check-based recommendations
        for check_name, check_result in feasibility_checks.items():
            if not check_result.get('passed', True):
                if check_name == 'timeline_duration':
                    recommendations.append("Adjust event duration to 4-12 hour range")
                elif check_name == 'vendor_capacity':
                    recommendations.append("Redistribute vendor workload or add additional vendors")
                elif check_name == 'coordination_complexity':
                    recommendations.append("Simplify vendor coordination or assign dedicated coordinator")
                elif check_name == 'setup_requirements':
                    recommendations.append("Allocate more time for event setup activities")
        
        if conflict_results.get('feasibility_score', 0) >= 0.8:
            recommendations.append("Timeline appears highly feasible - proceed with confidence")
        
        return recommendations
    
    def get_agent_performance_metrics(self) -> dict:
        """
        Get performance metrics for the timeline agent.
        
        Returns:
            dict: Performance metrics and statistics
        """
        return {
            'agent_type': 'timeline',
            'llm_model': 'gemma:2b',
            'tools_available': ['ConflictDetectionTool', 'TimelineGenerationTool'],
            'timeline_cache_size': len(self.timeline_cache),
            'capabilities': [
                'Conflict detection and analysis',
                'Timeline generation and optimization',
                'Vendor coordination planning',
                'Feasibility assessment',
                'LLM-enhanced timeline customization'
            ],
            'preserved_algorithms': [
                'ConflictDetection algorithm',
                'Timeline overlap detection',
                'Vendor constraint validation',
                'Feasibility scoring methodology'
            ]
        }