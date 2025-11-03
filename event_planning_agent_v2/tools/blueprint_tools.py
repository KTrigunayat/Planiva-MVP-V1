"""
Blueprint and document generation CrewAI tools for event planning agents
"""

import json
from datetime import datetime
from typing import Type, Dict, List, Any
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
try:
    from langchain_ollama import OllamaLLM
except ImportError:
    from langchain_community.llms import Ollama as OllamaLLM


class BlueprintGenerationInput(BaseModel):
    """Input schema for BlueprintGenerationTool"""
    client_requirements: dict = Field(..., description="Complete client requirements and preferences")
    vendor_combination: dict = Field(..., description="Final selected vendor combination")
    event_timeline: dict = Field(..., description="Detailed event timeline")
    budget_allocation: dict = Field(..., description="Budget allocation and costs")


class BlueprintGenerationTool(BaseTool):
    """
    Maintains final document generation capabilities for comprehensive event blueprints.
    
    This tool compiles all event planning components into a professional, 
    comprehensive blueprint document for client delivery.
    """
    name: str = "Blueprint Generation Tool"
    description: str = "Generates comprehensive event blueprints and documentation from planning components"
    args_schema: Type[BaseModel] = BlueprintGenerationInput
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._llm = None
    
    @property
    def llm(self):
        if self._llm is None:
            self._llm = OllamaLLM(model="gemma:2b")
        return self._llm

    def _generate_executive_summary(self, client_requirements: dict, 
                                  vendor_combination: dict) -> str:
        """Generate executive summary section of the blueprint"""
        client_name = client_requirements.get('clientName', 'Valued Client')
        guest_count = max(client_requirements.get('guestCount', {}).values() or [0])
        vision = client_requirements.get('clientVision', '')
        
        # Count selected vendors
        vendor_count = len(vendor_combination)
        vendor_types = list(vendor_combination.keys())
        
        summary = f"""
# Executive Summary

**Client:** {client_name}
**Event Type:** Wedding Celebration
**Expected Guests:** {guest_count}
**Vendor Partners:** {vendor_count} selected service providers

## Event Vision
{vision}

## Service Categories
{', '.join([vt.replace('_', ' ').title() for vt in vendor_types])}

This comprehensive event blueprint outlines the complete planning strategy, vendor selection rationale, timeline coordination, and budget allocation for your special celebration.
"""
        return summary.strip()

    def _generate_vendor_details(self, vendor_combination: dict) -> str:
        """Generate detailed vendor information section"""
        vendor_details = "\n# Selected Vendor Partners\n"
        
        for service_type, vendor in vendor_combination.items():
            service_title = service_type.replace('_', ' ').title()
            vendor_name = vendor.get('name', 'Unknown Vendor')
            location = vendor.get('location_city', 'Location TBD')
            
            vendor_details += f"\n## {service_title}\n"
            vendor_details += f"**Vendor:** {vendor_name}\n"
            vendor_details += f"**Location:** {location}\n"
            
            # Add service-specific details
            if service_type == 'venue':
                capacity = vendor.get('max_seating_capacity', 'N/A')
                venue_type = vendor.get('venue_type', 'N/A')
                vendor_details += f"**Capacity:** {capacity} guests\n"
                vendor_details += f"**Venue Type:** {venue_type}\n"
                
                amenities = vendor.get('amenities', [])
                if amenities:
                    vendor_details += f"**Amenities:** {', '.join(amenities)}\n"
            
            elif service_type == 'caterer':
                cuisines = vendor.get('attributes', {}).get('cuisines', [])
                if cuisines:
                    vendor_details += f"**Cuisine Specialties:** {', '.join(cuisines)}\n"
                
                veg_price = vendor.get('min_veg_price')
                nonveg_price = vendor.get('min_nonveg_price')
                if veg_price:
                    vendor_details += f"**Vegetarian Price:** ₹{veg_price}/plate\n"
                if nonveg_price:
                    vendor_details += f"**Non-Vegetarian Price:** ₹{nonveg_price}/plate\n"
            
            elif service_type == 'photographer':
                photo_price = vendor.get('photo_package_price')
                video_price = vendor.get('video_package_price')
                if photo_price:
                    vendor_details += f"**Photography Package:** ₹{photo_price:,}\n"
                if video_price:
                    vendor_details += f"**Videography Package:** ₹{video_price:,}\n"
            
            elif service_type == 'makeup_artist':
                bridal_price = vendor.get('bridal_makeup_price')
                if bridal_price:
                    vendor_details += f"**Bridal Makeup:** ₹{bridal_price:,}\n"
            
            # Add ranking score if available
            ranking_score = vendor.get('ranking_score')
            if ranking_score:
                vendor_details += f"**Selection Score:** {ranking_score}/1.0\n"
            
            vendor_details += "\n"
        
        return vendor_details

    def _generate_timeline_section(self, event_timeline: dict) -> str:
        """Generate detailed timeline section"""
        timeline_section = "\n# Event Timeline\n"
        
        event_date = event_timeline.get('event_date', 'TBD')
        total_duration = event_timeline.get('total_duration_hours', 0)
        activities = event_timeline.get('timeline', [])
        
        timeline_section += f"**Event Date:** {event_date}\n"
        timeline_section += f"**Total Duration:** {total_duration} hours\n\n"
        
        if activities:
            timeline_section += "## Detailed Schedule\n\n"
            
            for activity in activities:
                name = activity.get('name', 'Unknown Activity')
                start_time = activity.get('start_time', 'TBD')
                end_time = activity.get('end_time', 'TBD')
                duration = activity.get('duration', 0)
                description = activity.get('description', '')
                vendors_involved = activity.get('vendors_involved', [])
                
                timeline_section += f"### {start_time} - {end_time} | {name}\n"
                timeline_section += f"**Duration:** {duration} hours\n"
                
                if description:
                    timeline_section += f"**Description:** {description}\n"
                
                if vendors_involved:
                    timeline_section += f"**Vendors Involved:** {', '.join(vendors_involved)}\n"
                
                timeline_section += "\n"
        
        # Add coordination points if available
        coordination_points = event_timeline.get('vendor_coordination_points', [])
        if coordination_points:
            timeline_section += "## Critical Coordination Points\n\n"
            for point in coordination_points:
                time = point.get('time', 'TBD')
                activity = point.get('activity', 'Unknown')
                vendors = point.get('vendors', [])
                timeline_section += f"- **{time}:** {activity} - Coordination required between {', '.join(vendors)}\n"
        
        return timeline_section

    def _generate_budget_section(self, budget_allocation: dict, vendor_combination: dict) -> str:
        """Generate budget breakdown section"""
        budget_section = "\n# Budget Allocation\n"
        
        total_budget = budget_allocation.get('total_budget', 0)
        strategy = budget_allocation.get('recommended_strategy', {})
        
        budget_section += f"**Total Budget:** ₹{total_budget:,}\n"
        
        if strategy:
            strategy_name = strategy.get('strategy', 'Unknown')
            fitness_score = strategy.get('fitness_score', 0)
            allocation = strategy.get('allocation', {})
            
            budget_section += f"**Allocation Strategy:** {strategy_name.replace('_', ' ').title()}\n"
            budget_section += f"**Strategy Fitness Score:** {fitness_score}/1.0\n\n"
            
            budget_section += "## Service-wise Budget Breakdown\n\n"
            
            total_estimated_cost = 0
            
            for service_type, allocated_amount in allocation.items():
                service_title = service_type.replace('_', ' ').title()
                percentage = (allocated_amount / total_budget) * 100
                
                budget_section += f"### {service_title}\n"
                budget_section += f"**Allocated Budget:** ₹{allocated_amount:,} ({percentage:.1f}%)\n"
                
                # Add actual vendor cost if available
                if service_type in vendor_combination:
                    vendor = vendor_combination[service_type]
                    
                    # Get actual cost based on service type
                    actual_cost = None
                    if service_type == 'venue':
                        actual_cost = vendor.get('rental_cost')
                    elif service_type == 'caterer':
                        price_per_plate = vendor.get('min_veg_price')
                        if price_per_plate:
                            # Estimate based on guest count (simplified)
                            guest_count = 200  # Default estimate
                            actual_cost = price_per_plate * guest_count
                    elif service_type == 'photographer':
                        actual_cost = vendor.get('photo_package_price')
                    elif service_type == 'makeup_artist':
                        actual_cost = vendor.get('bridal_makeup_price')
                    
                    if actual_cost:
                        budget_section += f"**Estimated Cost:** ₹{actual_cost:,}\n"
                        budget_section += f"**Budget Remaining:** ₹{allocated_amount - actual_cost:,}\n"
                        total_estimated_cost += actual_cost
                
                budget_section += "\n"
            
            if total_estimated_cost > 0:
                budget_section += f"## Budget Summary\n"
                budget_section += f"**Total Estimated Cost:** ₹{total_estimated_cost:,}\n"
                budget_section += f"**Total Budget Remaining:** ₹{total_budget - total_estimated_cost:,}\n"
                budget_section += f"**Budget Utilization:** {(total_estimated_cost/total_budget)*100:.1f}%\n"
        
        return budget_section

    def _generate_recommendations(self, client_requirements: dict, 
                                vendor_combination: dict, 
                                event_timeline: dict) -> str:
        """Generate recommendations and next steps section"""
        recommendations = "\n# Recommendations & Next Steps\n"
        
        recommendations += "## Immediate Action Items\n"
        recommendations += "1. **Vendor Confirmation:** Confirm availability and finalize contracts with selected vendors\n"
        recommendations += "2. **Timeline Coordination:** Share detailed timeline with all vendors for coordination\n"
        recommendations += "3. **Budget Approval:** Review and approve final budget allocation\n"
        recommendations += "4. **Venue Walkthrough:** Schedule site visit with venue and key vendors\n\n"
        
        recommendations += "## Timeline Considerations\n"
        
        # Check for potential issues
        total_duration = event_timeline.get('total_duration_hours', 0)
        if total_duration > 10:
            recommendations += "- Consider breaking up the event or providing guest rest areas for the extended duration\n"
        
        coordination_points = event_timeline.get('vendor_coordination_points', [])
        if len(coordination_points) > 3:
            recommendations += "- Assign a dedicated coordinator for managing multiple vendor interactions\n"
        
        recommendations += "- Confirm all vendor arrival times and setup requirements\n"
        recommendations += "- Establish communication protocols between vendors\n\n"
        
        recommendations += "## Quality Assurance\n"
        recommendations += "- Schedule final vendor meetings 2 weeks before the event\n"
        recommendations += "- Prepare contingency plans for weather and vendor emergencies\n"
        recommendations += "- Confirm all vendor insurance and licensing requirements\n"
        
        return recommendations

    def _run(self, client_requirements: dict, vendor_combination: dict, 
             event_timeline: dict, budget_allocation: dict) -> str:
        """
        Main execution method for blueprint generation.
        Compiles comprehensive event blueprint document.
        """
        # Generate document sections
        executive_summary = self._generate_executive_summary(client_requirements, vendor_combination)
        vendor_details = self._generate_vendor_details(vendor_combination)
        timeline_section = self._generate_timeline_section(event_timeline)
        budget_section = self._generate_budget_section(budget_allocation, vendor_combination)
        recommendations = self._generate_recommendations(
            client_requirements, vendor_combination, event_timeline
        )
        
        # Compile complete blueprint
        blueprint = f"""
# Event Planning Blueprint

**Generated on:** {datetime.now().strftime('%B %d, %Y')}
**Document Version:** 1.0

{executive_summary}

{vendor_details}

{timeline_section}

{budget_section}

{recommendations}

---

*This blueprint was generated by the Planiva Event Planning System. Please review all details carefully and confirm with your event coordinator before proceeding.*
"""
        
        # Prepare result with both formatted blueprint and structured data
        result = {
            "blueprint_document": blueprint.strip(),
            "document_metadata": {
                "generated_date": datetime.now().isoformat(),
                "client_name": client_requirements.get('clientName', 'Unknown'),
                "vendor_count": len(vendor_combination),
                "timeline_activities": len(event_timeline.get('timeline', [])),
                "total_budget": budget_allocation.get('total_budget', 0),
                "document_sections": [
                    "Executive Summary",
                    "Vendor Partners", 
                    "Event Timeline",
                    "Budget Allocation",
                    "Recommendations"
                ]
            },
            "next_steps": [
                "Review blueprint with client",
                "Obtain client approval",
                "Initiate vendor contracts",
                "Schedule coordination meetings"
            ]
        }
        
        return json.dumps(result, indent=2)


class DocumentFormattingInput(BaseModel):
    """Input schema for DocumentFormattingTool"""
    blueprint_content: str = Field(..., description="Raw blueprint content to format")
    format_type: str = Field(default="markdown", description="Output format type (markdown, html, pdf)")
    client_branding: dict = Field(default={}, description="Client branding preferences")


class DocumentFormattingTool(BaseTool):
    """
    Enhanced document formatting tool for professional blueprint presentation.
    
    This tool formats blueprint documents into various professional formats
    while maintaining consistency and readability.
    """
    name: str = "Document Formatting Tool"
    description: str = "Formats blueprint documents into professional presentation formats with branding options"
    args_schema: Type[BaseModel] = DocumentFormattingInput

    def _format_as_markdown(self, content: str, client_branding: dict) -> str:
        """Format content as enhanced Markdown"""
        # Add client branding if provided
        if client_branding.get('company_name'):
            header = f"# {client_branding['company_name']} - Event Planning Blueprint\n\n"
            content = header + content
        
        # Enhance markdown formatting
        formatted_content = content
        
        # Add table of contents
        toc = "\n## Table of Contents\n"
        toc += "1. [Executive Summary](#executive-summary)\n"
        toc += "2. [Selected Vendor Partners](#selected-vendor-partners)\n"
        toc += "3. [Event Timeline](#event-timeline)\n"
        toc += "4. [Budget Allocation](#budget-allocation)\n"
        toc += "5. [Recommendations & Next Steps](#recommendations--next-steps)\n\n"
        
        # Insert TOC after the first header
        lines = formatted_content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('# ') and i > 0:
                lines.insert(i + 1, toc)
                break
        
        formatted_content = '\n'.join(lines)
        
        return formatted_content

    def _format_as_html(self, content: str, client_branding: dict) -> str:
        """Format content as HTML with styling"""
        # Convert markdown-style headers to HTML
        html_content = content
        
        # Replace markdown headers with HTML
        html_content = html_content.replace('# ', '<h1>')
        html_content = html_content.replace('## ', '<h2>')
        html_content = html_content.replace('### ', '<h3>')
        
        # Add closing tags (simplified)
        lines = html_content.split('\n')
        formatted_lines = []
        
        for line in lines:
            if line.startswith('<h1>'):
                formatted_lines.append(line + '</h1>')
            elif line.startswith('<h2>'):
                formatted_lines.append(line + '</h2>')
            elif line.startswith('<h3>'):
                formatted_lines.append(line + '</h3>')
            elif line.startswith('**') and line.endswith('**'):
                # Bold text
                formatted_lines.append(f"<strong>{line[2:-2]}</strong>")
            elif line.strip():
                formatted_lines.append(f"<p>{line}</p>")
            else:
                formatted_lines.append('<br>')
        
        html_body = '\n'.join(formatted_lines)
        
        # Create complete HTML document
        css_styles = """
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; }
            h2 { color: #34495e; margin-top: 30px; }
            h3 { color: #7f8c8d; }
            p { line-height: 1.6; }
            strong { color: #2c3e50; }
        </style>
        """
        
        if client_branding.get('primary_color'):
            css_styles = css_styles.replace('#3498db', client_branding['primary_color'])
        
        html_document = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Event Planning Blueprint</title>
            {css_styles}
        </head>
        <body>
            {html_body}
        </body>
        </html>
        """
        
        return html_document

    def _run(self, blueprint_content: str, format_type: str = "markdown", 
             client_branding: dict = None) -> str:
        """
        Main execution method for document formatting.
        Formats blueprint content into specified professional format.
        """
        if client_branding is None:
            client_branding = {}
        
        if format_type.lower() == "html":
            formatted_content = self._format_as_html(blueprint_content, client_branding)
        elif format_type.lower() == "pdf":
            # For PDF, we'll format as HTML first (PDF generation would require additional libraries)
            formatted_content = self._format_as_html(blueprint_content, client_branding)
            formatted_content = "<!-- PDF generation requires additional setup -->\n" + formatted_content
        else:
            # Default to markdown
            formatted_content = self._format_as_markdown(blueprint_content, client_branding)
        
        result = {
            "formatted_document": formatted_content,
            "format_type": format_type,
            "character_count": len(formatted_content),
            "estimated_pages": max(1, len(formatted_content) // 3000),  # Rough estimate
            "formatting_metadata": {
                "branding_applied": bool(client_branding),
                "format_features": {
                    "table_of_contents": format_type == "markdown",
                    "styling": format_type in ["html", "pdf"],
                    "responsive_design": format_type == "html"
                }
            }
        }
        
        return json.dumps(result, indent=2)