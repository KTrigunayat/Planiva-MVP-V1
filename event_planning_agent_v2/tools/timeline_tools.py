"""
Timeline and conflict detection CrewAI tools for event planning agents
"""

import json
from datetime import datetime, timedelta
from typing import Type, Dict, List, Any, Optional, ClassVar
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
try:
    from langchain_ollama import OllamaLLM
except ImportError:
    from langchain_community.llms import Ollama as OllamaLLM


class ConflictDetectionInput(BaseModel):
    """Input schema for ConflictDetectionTool"""
    vendor_combination: dict = Field(..., description="Dictionary of selected vendors for each service type")
    event_date: str = Field(..., description="Event date in YYYY-MM-DD format")
    event_timeline: dict = Field(..., description="Proposed event timeline with activities and timings")


class ConflictDetectionTool(BaseTool):
    """
    Maintains existing ConflictDetection algorithm logic for vendor and timeline validation.
    
    This tool checks for conflicts between vendors, timing constraints, and logistical
    requirements while preserving the existing algorithm's decision-making logic.
    """
    name: str = "Conflict Detection Tool"
    description: str = "Detects conflicts between vendors, timing constraints, and logistical requirements for event planning"
    args_schema: Type[BaseModel] = ConflictDetectionInput

    # Standard event activity durations (in hours)
    ACTIVITY_DURATIONS: ClassVar[Dict[str, float]] = {
        "setup": 2.0,
        "guest_arrival": 0.5,
        "ceremony": 1.5,
        "cocktail_hour": 1.0,
        "photography_session": 1.0,
        "reception_dinner": 2.5,
        "entertainment": 2.0,
        "cleanup": 1.5
    }

    # Vendor service windows and constraints
    VENDOR_CONSTRAINTS: ClassVar[Dict[str, Dict[str, float]]] = {
        "venue": {
            "setup_time_required": 2.0,  # hours before event
            "cleanup_time_required": 1.5,  # hours after event
            "max_event_duration": 12.0  # maximum hours venue can be booked
        },
        "caterer": {
            "setup_time_required": 1.5,
            "service_duration_min": 2.0,  # minimum service time
            "cleanup_time_required": 1.0
        },
        "photographer": {
            "arrival_before_event": 0.5,  # arrive 30 min before
            "max_continuous_hours": 8.0,  # maximum continuous shooting
            "break_required_after": 4.0  # break needed after 4 hours
        },
        "makeup_artist": {
            "service_duration": 2.0,  # typical makeup session duration
            "arrival_before_ceremony": 3.0,  # arrive 3 hours before ceremony
            "travel_time_buffer": 0.5  # buffer for travel between locations
        }
    }

    def _parse_event_date(self, event_date: str) -> datetime:
        """Parse event date string to datetime object"""
        try:
            return datetime.strptime(event_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {event_date}. Expected YYYY-MM-DD")

    def _detect_vendor_availability_conflicts(self, vendor_combination: dict, 
                                            event_date: str) -> List[Dict[str, Any]]:
        """
        Detect vendor availability conflicts for the event date.
        Maintains existing algorithm logic for availability checking.
        """
        conflicts = []
        parsed_date = self._parse_event_date(event_date)
        
        for service_type, vendor in vendor_combination.items():
            # Check if vendor has availability information
            if 'availability' in vendor:
                availability = vendor['availability']
                
                # Check if event date is in blackout dates
                blackout_dates = availability.get('blackout_dates', [])
                if event_date in blackout_dates:
                    conflicts.append({
                        "type": "availability_conflict",
                        "service": service_type,
                        "vendor": vendor.get('name', 'Unknown'),
                        "issue": f"Vendor not available on {event_date}",
                        "severity": "high"
                    })
                
                # Check day of week restrictions
                day_of_week = parsed_date.strftime('%A').lower()
                restricted_days = availability.get('restricted_days', [])
                if day_of_week in [day.lower() for day in restricted_days]:
                    conflicts.append({
                        "type": "day_restriction",
                        "service": service_type,
                        "vendor": vendor.get('name', 'Unknown'),
                        "issue": f"Vendor doesn't work on {day_of_week.title()}s",
                        "severity": "medium"
                    })
            
            # Check location-based conflicts
            vendor_location = vendor.get('location_city')
            if vendor_location:
                # Check if all vendors are in reasonable proximity
                # (This is a simplified check - real implementation would use actual distances)
                for other_service, other_vendor in vendor_combination.items():
                    if other_service != service_type:
                        other_location = other_vendor.get('location_city')
                        if other_location and vendor_location != other_location:
                            conflicts.append({
                                "type": "location_conflict",
                                "service": f"{service_type} & {other_service}",
                                "vendor": f"{vendor.get('name', 'Unknown')} & {other_vendor.get('name', 'Unknown')}",
                                "issue": f"Vendors in different cities: {vendor_location} vs {other_location}",
                                "severity": "medium"
                            })
        
        return conflicts

    def _detect_timeline_conflicts(self, event_timeline: dict, 
                                 vendor_combination: dict) -> List[Dict[str, Any]]:
        """
        Detect conflicts in the event timeline and vendor service requirements.
        Preserves existing ConflictDetection algorithm logic.
        """
        conflicts = []
        
        # Parse timeline activities
        activities = event_timeline.get('activities', [])
        if not activities:
            return [{
                "type": "timeline_missing",
                "service": "general",
                "vendor": "N/A",
                "issue": "No timeline activities provided",
                "severity": "high"
            }]
        
        # Sort activities by start time
        sorted_activities = sorted(activities, key=lambda x: x.get('start_time', '00:00'))
        
        # Check for overlapping activities
        for i in range(len(sorted_activities) - 1):
            current = sorted_activities[i]
            next_activity = sorted_activities[i + 1]
            
            current_end = self._calculate_end_time(
                current.get('start_time', '00:00'),
                current.get('duration', self.ACTIVITY_DURATIONS.get(current.get('type', 'unknown'), 1.0))
            )
            next_start = next_activity.get('start_time', '00:00')
            
            if current_end > next_start:
                conflicts.append({
                    "type": "timeline_overlap",
                    "service": "timeline",
                    "vendor": "N/A",
                    "issue": f"Activity '{current.get('name', 'Unknown')}' overlaps with '{next_activity.get('name', 'Unknown')}'",
                    "severity": "high"
                })
        
        # Check vendor-specific timeline requirements
        for service_type, vendor in vendor_combination.items():
            constraints = self.VENDOR_CONSTRAINTS.get(service_type, {})
            
            if service_type == "venue":
                # Check total event duration
                first_activity = sorted_activities[0] if sorted_activities else None
                last_activity = sorted_activities[-1] if sorted_activities else None
                
                if first_activity and last_activity:
                    event_start = first_activity.get('start_time', '00:00')
                    last_end = self._calculate_end_time(
                        last_activity.get('start_time', '00:00'),
                        last_activity.get('duration', 1.0)
                    )
                    
                    total_duration = self._calculate_duration_hours(event_start, last_end)
                    max_duration = constraints.get('max_event_duration', 12.0)
                    
                    if total_duration > max_duration:
                        conflicts.append({
                            "type": "duration_exceeded",
                            "service": service_type,
                            "vendor": vendor.get('name', 'Unknown'),
                            "issue": f"Event duration ({total_duration:.1f}h) exceeds venue limit ({max_duration}h)",
                            "severity": "high"
                        })
            
            elif service_type == "photographer":
                # Check continuous shooting duration
                photo_activities = [a for a in activities if 'photo' in a.get('type', '').lower()]
                if photo_activities:
                    total_photo_time = sum(a.get('duration', 1.0) for a in photo_activities)
                    max_continuous = constraints.get('max_continuous_hours', 8.0)
                    
                    if total_photo_time > max_continuous:
                        conflicts.append({
                            "type": "photographer_overwork",
                            "service": service_type,
                            "vendor": vendor.get('name', 'Unknown'),
                            "issue": f"Photography duration ({total_photo_time:.1f}h) exceeds recommended limit ({max_continuous}h)",
                            "severity": "medium"
                        })
            
            elif service_type == "makeup_artist":
                # Check makeup timing relative to ceremony
                ceremony_activities = [a for a in activities if 'ceremony' in a.get('type', '').lower()]
                makeup_activities = [a for a in activities if 'makeup' in a.get('type', '').lower()]
                
                if ceremony_activities and not makeup_activities:
                    conflicts.append({
                        "type": "makeup_timing_missing",
                        "service": service_type,
                        "vendor": vendor.get('name', 'Unknown'),
                        "issue": "No makeup session scheduled before ceremony",
                        "severity": "medium"
                    })
        
        return conflicts

    def _calculate_end_time(self, start_time: str, duration_hours: float) -> str:
        """Calculate end time given start time and duration"""
        try:
            start_dt = datetime.strptime(start_time, "%H:%M")
            end_dt = start_dt + timedelta(hours=duration_hours)
            return end_dt.strftime("%H:%M")
        except ValueError:
            return "23:59"  # Default fallback

    def _calculate_duration_hours(self, start_time: str, end_time: str) -> float:
        """Calculate duration in hours between start and end time"""
        try:
            start_dt = datetime.strptime(start_time, "%H:%M")
            end_dt = datetime.strptime(end_time, "%H:%M")
            
            # Handle next day scenarios
            if end_dt < start_dt:
                end_dt += timedelta(days=1)
            
            duration = end_dt - start_dt
            return duration.total_seconds() / 3600
        except ValueError:
            return 0.0

    def _run(self, vendor_combination: dict, event_date: str, event_timeline: dict) -> str:
        """
        Main execution method for conflict detection.
        Maintains existing ConflictDetection algorithm logic.
        """
        all_conflicts = []
        
        # Detect vendor availability conflicts
        availability_conflicts = self._detect_vendor_availability_conflicts(
            vendor_combination, event_date
        )
        all_conflicts.extend(availability_conflicts)
        
        # Detect timeline conflicts
        timeline_conflicts = self._detect_timeline_conflicts(
            event_timeline, vendor_combination
        )
        all_conflicts.extend(timeline_conflicts)
        
        # Categorize conflicts by severity
        high_severity = [c for c in all_conflicts if c.get('severity') == 'high']
        medium_severity = [c for c in all_conflicts if c.get('severity') == 'medium']
        low_severity = [c for c in all_conflicts if c.get('severity') == 'low']
        
        # Determine overall feasibility
        feasibility_score = 1.0
        if high_severity:
            feasibility_score -= len(high_severity) * 0.3
        if medium_severity:
            feasibility_score -= len(medium_severity) * 0.15
        if low_severity:
            feasibility_score -= len(low_severity) * 0.05
        
        feasibility_score = max(0.0, feasibility_score)
        
        # Generate recommendations
        recommendations = []
        if high_severity:
            recommendations.append("Critical conflicts detected - immediate resolution required")
        if medium_severity:
            recommendations.append("Moderate conflicts detected - consider adjustments")
        if feasibility_score >= 0.8:
            recommendations.append("Timeline appears feasible with minor adjustments")
        elif feasibility_score >= 0.6:
            recommendations.append("Timeline needs significant adjustments")
        else:
            recommendations.append("Timeline requires major restructuring")
        
        result = {
            "feasibility_score": round(feasibility_score, 4),
            "total_conflicts": len(all_conflicts),
            "conflicts_by_severity": {
                "high": len(high_severity),
                "medium": len(medium_severity),
                "low": len(low_severity)
            },
            "detailed_conflicts": all_conflicts,
            "recommendations": recommendations,
            "event_date": event_date,
            "vendor_count": len(vendor_combination)
        }
        
        return json.dumps(result, indent=2)


class TimelineGenerationInput(BaseModel):
    """Input schema for TimelineGenerationTool"""
    client_requirements: dict = Field(..., description="Client requirements and preferences")
    vendor_combination: dict = Field(..., description="Selected vendors for the event")
    event_date: str = Field(..., description="Event date in YYYY-MM-DD format")
    event_duration_hours: float = Field(default=8.0, description="Total event duration in hours")


class TimelineGenerationTool(BaseTool):
    """
    LLM-based timeline creation tool that generates detailed event schedules.
    
    This tool uses LLM capabilities to create comprehensive timelines while
    incorporating vendor constraints and client preferences.
    """
    name: str = "Timeline Generation Tool"
    description: str = "Generates detailed event timelines using LLM-based planning with vendor constraints and client preferences"
    args_schema: Type[BaseModel] = TimelineGenerationInput
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._llm = None
    
    @property
    def llm(self):
        if self._llm is None:
            self._llm = OllamaLLM(model="gemma:2b")
        return self._llm

    # Standard timeline templates for different event types
    TIMELINE_TEMPLATES: ClassVar[Dict[str, List[Dict[str, Any]]]] = {
        "wedding": [
            {"activity": "Venue Setup", "duration": 2.0, "type": "setup"},
            {"activity": "Bridal Makeup", "duration": 2.0, "type": "makeup"},
            {"activity": "Photography - Getting Ready", "duration": 1.0, "type": "photography"},
            {"activity": "Guest Arrival", "duration": 0.5, "type": "arrival"},
            {"activity": "Wedding Ceremony", "duration": 1.5, "type": "ceremony"},
            {"activity": "Cocktail Hour & Photography", "duration": 1.5, "type": "cocktail"},
            {"activity": "Reception Dinner", "duration": 2.5, "type": "reception"},
            {"activity": "Entertainment & Dancing", "duration": 2.0, "type": "entertainment"},
            {"activity": "Event Conclusion", "duration": 0.5, "type": "conclusion"}
        ]
    }

    def _generate_base_timeline(self, client_requirements: dict, 
                              event_duration_hours: float) -> List[Dict[str, Any]]:
        """
        Generate a base timeline structure based on client requirements.
        """
        # Determine event type (default to wedding for now)
        event_type = "wedding"  # Could be expanded based on client requirements
        
        base_template = self.TIMELINE_TEMPLATES.get(event_type, self.TIMELINE_TEMPLATES["wedding"])
        
        # Adjust durations to fit within total event duration
        total_template_duration = sum(activity["duration"] for activity in base_template)
        scale_factor = event_duration_hours / total_template_duration
        
        # Generate timeline with scaled durations
        timeline = []
        current_time = datetime.strptime("10:00", "%H:%M")  # Default start time
        
        for activity in base_template:
            scaled_duration = activity["duration"] * scale_factor
            
            timeline_item = {
                "name": activity["activity"],
                "type": activity["type"],
                "start_time": current_time.strftime("%H:%M"),
                "duration": round(scaled_duration, 1),
                "end_time": (current_time + timedelta(hours=scaled_duration)).strftime("%H:%M")
            }
            
            timeline.append(timeline_item)
            current_time += timedelta(hours=scaled_duration)
        
        return timeline

    def _enhance_timeline_with_llm(self, base_timeline: List[Dict[str, Any]], 
                                 client_requirements: dict, 
                                 vendor_combination: dict) -> List[Dict[str, Any]]:
        """
        Use LLM to enhance and customize the timeline based on specific requirements.
        """
        # Prepare context for LLM
        timeline_json = json.dumps(base_timeline, indent=2)
        client_vision = client_requirements.get('clientVision', '')
        guest_count = max(client_requirements.get('guestCount', {}).values() or [200])
        
        # Prepare vendor information
        vendor_info = []
        for service_type, vendor in vendor_combination.items():
            vendor_info.append(f"{service_type.title()}: {vendor.get('name', 'Unknown')}")
        
        vendor_summary = "\n".join(vendor_info)
        
        prompt = f"""
        You are an expert event planner. Your task is to enhance and customize the following event timeline based on the client's specific requirements and selected vendors.

        CURRENT TIMELINE:
        {timeline_json}

        CLIENT VISION:
        "{client_vision}"

        GUEST COUNT: {guest_count}

        SELECTED VENDORS:
        {vendor_summary}

        INSTRUCTIONS:
        1. Review the current timeline and suggest improvements
        2. Add specific details based on client vision and vendor capabilities
        3. Ensure timing is realistic and allows for smooth transitions
        4. Consider guest count for activity durations
        5. Add any missing activities that would enhance the event

        Respond with a JSON array of timeline activities. Each activity should have:
        - "name": descriptive activity name
        - "type": activity category
        - "start_time": in HH:MM format
        - "duration": in hours (decimal)
        - "end_time": in HH:MM format
        - "description": detailed description of what happens
        - "vendors_involved": list of vendor types involved
        - "notes": any special considerations

        JSON OUTPUT:
        """
        
        try:
            response = self.llm.invoke(prompt)
            # Clean up the response
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            
            enhanced_timeline = json.loads(cleaned_response)
            return enhanced_timeline
        except (json.JSONDecodeError, Exception) as e:
            # Fallback to base timeline if LLM fails
            print(f"LLM enhancement failed: {e}")
            return base_timeline

    def _validate_timeline(self, timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and fix any issues in the generated timeline.
        """
        validated_timeline = []
        
        for i, activity in enumerate(timeline):
            # Ensure required fields exist
            if not activity.get('name'):
                activity['name'] = f"Activity {i+1}"
            if not activity.get('type'):
                activity['type'] = "general"
            if not activity.get('start_time'):
                activity['start_time'] = "10:00"
            if not activity.get('duration'):
                activity['duration'] = 1.0
            
            # Calculate end_time if missing
            if not activity.get('end_time'):
                start_dt = datetime.strptime(activity['start_time'], "%H:%M")
                end_dt = start_dt + timedelta(hours=activity['duration'])
                activity['end_time'] = end_dt.strftime("%H:%M")
            
            # Add default values for optional fields
            if not activity.get('description'):
                activity['description'] = f"Event activity: {activity['name']}"
            if not activity.get('vendors_involved'):
                activity['vendors_involved'] = []
            if not activity.get('notes'):
                activity['notes'] = ""
            
            validated_timeline.append(activity)
        
        return validated_timeline

    def _run(self, client_requirements: dict, vendor_combination: dict, 
             event_date: str, event_duration_hours: float = 8.0) -> str:
        """
        Main execution method for timeline generation.
        Creates detailed event timeline using LLM-based planning.
        """
        # Generate base timeline structure
        base_timeline = self._generate_base_timeline(client_requirements, event_duration_hours)
        
        # Enhance timeline with LLM
        enhanced_timeline = self._enhance_timeline_with_llm(
            base_timeline, client_requirements, vendor_combination
        )
        
        # Validate the final timeline
        final_timeline = self._validate_timeline(enhanced_timeline)
        
        # Calculate timeline statistics
        total_activities = len(final_timeline)
        total_duration = sum(activity.get('duration', 0) for activity in final_timeline)
        
        # Identify critical path activities
        critical_activities = [
            activity for activity in final_timeline 
            if activity.get('type') in ['ceremony', 'reception', 'setup']
        ]
        
        result = {
            "event_date": event_date,
            "total_duration_hours": round(total_duration, 1),
            "total_activities": total_activities,
            "timeline": final_timeline,
            "critical_activities": len(critical_activities),
            "vendor_coordination_points": self._identify_coordination_points(final_timeline, vendor_combination),
            "timeline_summary": {
                "start_time": final_timeline[0].get('start_time') if final_timeline else "10:00",
                "end_time": final_timeline[-1].get('end_time') if final_timeline else "18:00",
                "key_milestones": [
                    activity['name'] for activity in final_timeline 
                    if activity.get('type') in ['ceremony', 'reception', 'entertainment']
                ]
            }
        }
        
        return json.dumps(result, indent=2)

    def _identify_coordination_points(self, timeline: List[Dict[str, Any]], 
                                    vendor_combination: dict) -> List[Dict[str, Any]]:
        """
        Identify points in the timeline where vendor coordination is critical.
        """
        coordination_points = []
        
        for activity in timeline:
            vendors_involved = activity.get('vendors_involved', [])
            if len(vendors_involved) > 1:
                coordination_points.append({
                    "time": activity.get('start_time'),
                    "activity": activity.get('name'),
                    "vendors": vendors_involved,
                    "coordination_type": "multi_vendor"
                })
        
        return coordination_points