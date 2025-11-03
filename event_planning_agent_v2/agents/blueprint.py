"""
Blueprint Agent for Event Planning System

This agent specializes in final document generation and comprehensive
event blueprint creation for client delivery.
"""

import json
from typing import Dict, List, Any, Optional
from crewai import Agent, Task
try:
    from langchain_ollama import OllamaLLM
except ImportError:
    from langchain_community.llms import Ollama as OllamaLLM

# Import existing blueprint tools
from ..tools.blueprint_tools import BlueprintGenerationTool, DocumentFormattingTool


def create_blueprint_agent() -> Agent:
    """
    Create and configure the Blueprint Agent for final document generation.
    
    Implements Blueprint Agent for final document generation while
    integrating with appropriate LLM models and tools.
    
    Returns:
        Agent: Configured CrewAI Blueprint Agent
    """
    # Initialize Gemma-2B LLM for document generation
    llm = OllamaLLM(model="gemma:2b")
    
    # Initialize blueprint tools (preserving existing logic)
    blueprint_generation_tool = BlueprintGenerationTool()
    document_formatting_tool = DocumentFormattingTool()
    
    # Create blueprint agent
    blueprint_agent = Agent(
        role="Event Documentation Specialist",
        goal="Create comprehensive event blueprints and professional documentation for client delivery",
        backstory="""You are a documentation expert with event planning expertise and exceptional attention to detail. 
        You excel at compiling complex planning information into clear, professional documents that clients can easily 
        understand and implement. Your expertise includes comprehensive blueprint generation, professional document 
        formatting, and creating actionable implementation guides that ensure event success.""",
        verbose=True,
        allow_delegation=False,  # Blueprint agent works independently
        tools=[blueprint_generation_tool, document_formatting_tool],
        llm=llm,
        max_iter=4,
        memory=True
    )
    
    return blueprint_agent


def create_blueprint_generation_task(client_requirements: dict, 
                                   vendor_combination: dict, 
                                   event_timeline: dict, 
                                   budget_allocation: dict) -> Task:
    """
    Create blueprint generation task for comprehensive event documentation.
    
    Args:
        client_requirements: Complete client requirements and preferences
        vendor_combination: Final selected vendor combination
        event_timeline: Detailed event timeline
        budget_allocation: Budget allocation and costs
        
    Returns:
        Task: Blueprint generation task
    """
    
    client_name = client_requirements.get('clientName', 'Valued Client')
    vendor_count = len(vendor_combination)
    timeline_activities = len(event_timeline.get('timeline', []))
    total_budget = budget_allocation.get('total_budget', 0)
    
    task = Task(
        description=f"""Generate comprehensive event blueprint document for client delivery.
        
        Blueprint Generation Parameters:
        - Client: {client_name}
        - Vendors: {vendor_count} selected partners
        - Timeline Activities: {timeline_activities}
        - Total Budget: ₹{total_budget:,}
        
        Your responsibilities:
        1. Use BlueprintGenerationTool to compile all planning components
        2. Generate executive summary with event vision and key highlights
        3. Create detailed vendor partner profiles with selection rationale
        4. Compile comprehensive timeline with coordination details
        5. Provide detailed budget breakdown with cost analysis
        6. Generate actionable recommendations and next steps
        7. Ensure professional presentation suitable for client delivery
        
        Maintain final document generation capabilities:
        - Professional formatting and structure
        - Clear, client-friendly language
        - Comprehensive coverage of all planning aspects
        - Actionable implementation guidance
        
        Expected Output: Complete event blueprint ready for client presentation""",
        expected_output="""JSON object containing:
        - blueprint_document: complete formatted blueprint text
        - document_metadata: generation details and statistics
        - next_steps: actionable items for client and vendors
        - document_sections: list of included sections
        - client_deliverables: summary of what client receives""",
        agent=None,  # Will be set when creating the crew
        tools=[BlueprintGenerationTool()]
    )
    
    return task


def create_document_formatting_task(blueprint_content: str, 
                                  format_type: str = "markdown", 
                                  client_branding: dict = None) -> Task:
    """
    Create document formatting task for professional presentation.
    
    Args:
        blueprint_content: Raw blueprint content to format
        format_type: Output format type (markdown, html, pdf)
        client_branding: Client branding preferences
        
    Returns:
        Task: Document formatting task
    """
    
    if client_branding is None:
        client_branding = {}
    
    task = Task(
        description=f"""Format event blueprint for professional presentation.
        
        Formatting Parameters:
        - Format Type: {format_type}
        - Client Branding: {bool(client_branding)}
        - Content Length: {len(blueprint_content)} characters
        
        Your responsibilities:
        1. Use DocumentFormattingTool to format blueprint content
        2. Apply professional styling and layout
        3. Integrate client branding elements if provided
        4. Ensure consistent formatting throughout document
        5. Add table of contents and navigation elements
        6. Optimize for readability and professional presentation
        7. Generate multiple format versions if requested
        
        Format-specific requirements:
        - Markdown: Clean structure with proper headers and formatting
        - HTML: Professional styling with CSS and responsive design
        - PDF: Print-ready layout with proper page breaks
        
        Expected Output: Professionally formatted document ready for delivery""",
        expected_output="""JSON object containing:
        - formatted_document: professionally formatted content
        - format_type: output format used
        - formatting_metadata: formatting details and statistics
        - document_features: list of formatting features applied
        - delivery_recommendations: suggestions for document delivery""",
        agent=None,  # Will be set when creating the crew
        tools=[DocumentFormattingTool()]
    )
    
    return task


def create_quality_assurance_task(blueprint_document: dict, 
                                client_requirements: dict, 
                                planning_components: dict) -> Task:
    """
    Create quality assurance task to validate blueprint completeness and accuracy.
    
    Args:
        blueprint_document: Generated blueprint document
        client_requirements: Original client requirements
        planning_components: All planning components (vendors, timeline, budget)
        
    Returns:
        Task: Quality assurance task
    """
    
    task = Task(
        description=f"""Perform comprehensive quality assurance on event blueprint.
        
        QA Parameters:
        - Client Requirements: {len(client_requirements)} requirement categories
        - Planning Components: {len(planning_components)} component types
        - Document Sections: Multiple sections to validate
        
        Your responsibilities:
        1. Validate blueprint completeness against client requirements
        2. Verify accuracy of vendor information and details
        3. Check timeline consistency and feasibility
        4. Validate budget calculations and allocations
        5. Ensure professional language and presentation
        6. Identify any missing information or inconsistencies
        7. Generate quality assurance report with recommendations
        
        Quality checks to perform:
        - Requirement coverage analysis
        - Data accuracy verification
        - Document structure validation
        - Professional presentation assessment
        - Implementation feasibility review
        
        Expected Output: Comprehensive QA report with validation results""",
        expected_output="""JSON object containing:
        - qa_summary: overall quality assessment
        - completeness_check: requirement coverage analysis
        - accuracy_validation: data accuracy verification results
        - presentation_review: professional presentation assessment
        - identified_issues: list of any problems found
        - improvement_recommendations: suggestions for enhancement
        - approval_status: ready for delivery or needs revision""",
        agent=None,  # Will be set when creating the crew
        tools=[BlueprintGenerationTool(), DocumentFormattingTool()]
    )
    
    return task


class BlueprintAgentCoordinator:
    """
    Coordinator class for managing Blueprint Agent workflows and document generation.
    
    This class handles blueprint generation, document formatting, and quality assurance
    while maintaining professional standards and client requirements.
    """
    
    def __init__(self):
        self.agent = create_blueprint_agent()
        self.document_templates = {}  # Cache for document templates
        self.generated_blueprints = {}  # Cache for generated blueprints
    
    def generate_event_blueprint(self, client_requirements: dict, 
                               vendor_combination: dict, 
                               event_timeline: dict, 
                               budget_allocation: dict) -> dict:
        """
        Generate comprehensive event blueprint document.
        
        Args:
            client_requirements: Complete client requirements and preferences
            vendor_combination: Final selected vendor combination
            event_timeline: Detailed event timeline
            budget_allocation: Budget allocation and costs
            
        Returns:
            dict: Generated blueprint with metadata
        """
        blueprint_tool = BlueprintGenerationTool()
        
        result = blueprint_tool._run(
            client_requirements=client_requirements,
            vendor_combination=vendor_combination,
            event_timeline=event_timeline,
            budget_allocation=budget_allocation
        )
        
        blueprint_data = json.loads(result)
        
        # Cache the generated blueprint
        client_id = client_requirements.get('clientId', 'unknown')
        self.generated_blueprints[client_id] = blueprint_data
        
        return blueprint_data
    
    def format_blueprint_document(self, blueprint_content: str, 
                                format_type: str = "markdown", 
                                client_branding: dict = None) -> dict:
        """
        Format blueprint document for professional presentation.
        
        Args:
            blueprint_content: Raw blueprint content to format
            format_type: Output format type (markdown, html, pdf)
            client_branding: Client branding preferences
            
        Returns:
            dict: Formatted document with metadata
        """
        formatting_tool = DocumentFormattingTool()
        
        if client_branding is None:
            client_branding = {}
        
        result = formatting_tool._run(
            blueprint_content=blueprint_content,
            format_type=format_type,
            client_branding=client_branding
        )
        
        formatted_data = json.loads(result)
        
        return formatted_data
    
    def validate_blueprint_quality(self, blueprint_document: dict, 
                                 client_requirements: dict, 
                                 planning_components: dict) -> dict:
        """
        Perform comprehensive quality assurance on blueprint document.
        
        Args:
            blueprint_document: Generated blueprint document
            client_requirements: Original client requirements
            planning_components: All planning components
            
        Returns:
            dict: Quality assurance results
        """
        # Extract blueprint content
        blueprint_content = blueprint_document.get('blueprint_document', '')
        
        # Perform completeness checks
        completeness_results = self._check_blueprint_completeness(
            blueprint_content, client_requirements
        )
        
        # Perform accuracy validation
        accuracy_results = self._validate_blueprint_accuracy(
            blueprint_document, planning_components
        )
        
        # Assess presentation quality
        presentation_results = self._assess_presentation_quality(blueprint_content)
        
        # Calculate overall quality score
        quality_score = self._calculate_quality_score(
            completeness_results, accuracy_results, presentation_results
        )
        
        return {
            'overall_quality_score': quality_score,
            'completeness_check': completeness_results,
            'accuracy_validation': accuracy_results,
            'presentation_assessment': presentation_results,
            'approval_status': 'approved' if quality_score >= 0.8 else 'needs_revision',
            'recommendations': self._generate_quality_recommendations(
                completeness_results, accuracy_results, presentation_results
            )
        }
    
    def _check_blueprint_completeness(self, blueprint_content: str, 
                                    client_requirements: dict) -> dict:
        """Check if blueprint covers all client requirements."""
        required_sections = [
            'Executive Summary',
            'Vendor Partners',
            'Event Timeline',
            'Budget Allocation',
            'Recommendations'
        ]
        
        missing_sections = []
        for section in required_sections:
            if section.lower() not in blueprint_content.lower():
                missing_sections.append(section)
        
        # Check requirement coverage
        client_vision = client_requirements.get('clientVision', '')
        guest_count = client_requirements.get('guestCount', {})
        venue_prefs = client_requirements.get('venuePreferences', [])
        
        coverage_checks = {
            'client_vision_mentioned': client_vision.lower() in blueprint_content.lower() if client_vision else True,
            'guest_count_specified': any(str(count) in blueprint_content for count in guest_count.values()) if guest_count else True,
            'venue_preferences_addressed': any(pref.lower() in blueprint_content.lower() for pref in venue_prefs) if venue_prefs else True
        }
        
        completeness_score = (len(required_sections) - len(missing_sections)) / len(required_sections)
        coverage_score = sum(coverage_checks.values()) / len(coverage_checks)
        
        return {
            'completeness_score': round((completeness_score + coverage_score) / 2, 4),
            'required_sections': required_sections,
            'missing_sections': missing_sections,
            'requirement_coverage': coverage_checks,
            'passed': len(missing_sections) == 0 and coverage_score >= 0.8
        }
    
    def _validate_blueprint_accuracy(self, blueprint_document: dict, 
                                   planning_components: dict) -> dict:
        """Validate accuracy of information in blueprint."""
        accuracy_checks = {
            'vendor_count_accurate': True,
            'budget_calculations_correct': True,
            'timeline_consistency': True,
            'contact_information_present': True
        }
        
        # Check vendor count accuracy
        vendor_combination = planning_components.get('vendor_combination', {})
        expected_vendor_count = len(vendor_combination)
        
        # Check budget accuracy
        budget_allocation = planning_components.get('budget_allocation', {})
        expected_total_budget = budget_allocation.get('total_budget', 0)
        
        # Simplified accuracy validation (would be more comprehensive in production)
        blueprint_content = blueprint_document.get('blueprint_document', '')
        
        if str(expected_vendor_count) not in blueprint_content:
            accuracy_checks['vendor_count_accurate'] = False
        
        if str(expected_total_budget) not in blueprint_content:
            accuracy_checks['budget_calculations_correct'] = False
        
        accuracy_score = sum(accuracy_checks.values()) / len(accuracy_checks)
        
        return {
            'accuracy_score': round(accuracy_score, 4),
            'accuracy_checks': accuracy_checks,
            'passed': accuracy_score >= 0.9
        }
    
    def _assess_presentation_quality(self, blueprint_content: str) -> dict:
        """Assess professional presentation quality of blueprint."""
        presentation_checks = {
            'proper_formatting': '# ' in blueprint_content or '## ' in blueprint_content,
            'professional_language': 'comprehensive' in blueprint_content.lower() or 'professional' in blueprint_content.lower(),
            'clear_structure': blueprint_content.count('\n\n') >= 5,  # Multiple sections
            'adequate_length': len(blueprint_content) >= 1000,  # Minimum content length
            'contact_information': 'contact' in blueprint_content.lower() or 'next steps' in blueprint_content.lower()
        }
        
        presentation_score = sum(presentation_checks.values()) / len(presentation_checks)
        
        return {
            'presentation_score': round(presentation_score, 4),
            'presentation_checks': presentation_checks,
            'content_length': len(blueprint_content),
            'passed': presentation_score >= 0.8
        }
    
    def _calculate_quality_score(self, completeness_results: dict, 
                               accuracy_results: dict, 
                               presentation_results: dict) -> float:
        """Calculate overall quality score."""
        weights = {
            'completeness': 0.4,
            'accuracy': 0.4,
            'presentation': 0.2
        }
        
        quality_score = (
            weights['completeness'] * completeness_results.get('completeness_score', 0) +
            weights['accuracy'] * accuracy_results.get('accuracy_score', 0) +
            weights['presentation'] * presentation_results.get('presentation_score', 0)
        )
        
        return round(quality_score, 4)
    
    def _generate_quality_recommendations(self, completeness_results: dict, 
                                        accuracy_results: dict, 
                                        presentation_results: dict) -> List[str]:
        """Generate recommendations based on quality assessment."""
        recommendations = []
        
        # Completeness recommendations
        if not completeness_results.get('passed', True):
            missing_sections = completeness_results.get('missing_sections', [])
            if missing_sections:
                recommendations.append(f"Add missing sections: {', '.join(missing_sections)}")
        
        # Accuracy recommendations
        if not accuracy_results.get('passed', True):
            recommendations.append("Verify and correct data accuracy issues")
        
        # Presentation recommendations
        if not presentation_results.get('passed', True):
            recommendations.append("Improve document formatting and professional presentation")
        
        # Overall recommendations
        if not recommendations:
            recommendations.append("Blueprint meets quality standards - ready for client delivery")
        
        return recommendations
    
    def create_multiple_format_versions(self, blueprint_content: str, 
                                      client_branding: dict = None) -> dict:
        """
        Create multiple format versions of the blueprint.
        
        Args:
            blueprint_content: Raw blueprint content
            client_branding: Client branding preferences
            
        Returns:
            dict: Multiple format versions
        """
        if client_branding is None:
            client_branding = {}
        
        formats = ['markdown', 'html']
        formatted_versions = {}
        
        for format_type in formats:
            formatted_doc = self.format_blueprint_document(
                blueprint_content, format_type, client_branding
            )
            formatted_versions[format_type] = formatted_doc
        
        return {
            'available_formats': formats,
            'formatted_versions': formatted_versions,
            'recommended_format': 'html',  # For professional presentation
            'delivery_options': [
                'Email attachment',
                'Client portal download',
                'Printed hardcopy'
            ]
        }
    
    def get_agent_performance_metrics(self) -> dict:
        """
        Get performance metrics for the blueprint agent.
        
        Returns:
            dict: Performance metrics and statistics
        """
        return {
            'agent_type': 'blueprint',
            'llm_model': 'gemma:2b',
            'tools_available': ['BlueprintGenerationTool', 'DocumentFormattingTool'],
            'blueprints_generated': len(self.generated_blueprints),
            'templates_cached': len(self.document_templates),
            'capabilities': [
                'Comprehensive blueprint generation',
                'Professional document formatting',
                'Quality assurance and validation',
                'Multi-format document creation',
                'Client branding integration'
            ],
            'document_features': [
                'Executive summaries',
                'Vendor partner profiles',
                'Detailed timelines',
                'Budget breakdowns',
                'Implementation guides'
            ]
        }