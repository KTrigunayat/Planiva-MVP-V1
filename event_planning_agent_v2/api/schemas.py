"""
Pydantic schemas for Event Planning Agent v2 API
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Supported event types"""
    WEDDING = "wedding"
    CORPORATE = "corporate"
    BIRTHDAY = "birthday"
    ANNIVERSARY = "anniversary"
    CONFERENCE = "conference"


class PlanStatus(str, Enum):
    """Event plan status values"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GuestCount(BaseModel):
    """Guest count for different event segments"""
    Reception: Optional[int] = Field(None, ge=1, description="Reception guest count")
    Ceremony: Optional[int] = Field(None, ge=1, description="Ceremony guest count")
    total: Optional[int] = Field(None, ge=1, description="Total guest count")


class VenuePreferences(BaseModel):
    """Venue preferences and requirements"""
    venue_types: Optional[List[str]] = Field(None, description="Preferred venue types")
    essential_amenities: Optional[List[str]] = Field(None, description="Essential venue amenities")
    location_preferences: Optional[List[str]] = Field(None, description="Preferred locations")


class DecorationAndAmbiance(BaseModel):
    """Decoration and ambiance preferences"""
    desired_theme: Optional[str] = Field(None, description="Desired event theme")
    color_scheme: Optional[List[str]] = Field(None, description="Preferred color scheme")
    style_preferences: Optional[List[str]] = Field(None, description="Style preferences")


class FoodAndCatering(BaseModel):
    """Food and catering preferences"""
    cuisine_preferences: Optional[List[str]] = Field(None, description="Preferred cuisines")
    dietary_options: Optional[List[str]] = Field(None, description="Dietary requirements")
    beverages: Optional[Dict[str, Any]] = Field(None, description="Beverage preferences")
    service_style: Optional[str] = Field(None, description="Service style preference")


class AdditionalRequirements(BaseModel):
    """Additional service requirements"""
    photography: Optional[str] = Field(None, description="Photography requirements")
    videography: Optional[str] = Field(None, description="Videography requirements")
    makeup: Optional[str] = Field(None, description="Makeup requirements")
    entertainment: Optional[str] = Field(None, description="Entertainment requirements")
    transportation: Optional[str] = Field(None, description="Transportation requirements")


class EventPlanRequest(BaseModel):
    """Request schema for creating an event plan - matches existing format"""
    clientName: str = Field(..., description="Client name")
    guestCount: Union[GuestCount, Dict[str, int], int] = Field(..., description="Guest count information")
    clientVision: str = Field(..., description="Client's vision for the event")
    venuePreferences: Optional[List[str]] = Field(None, description="Venue type preferences")
    essentialVenueAmenities: Optional[List[str]] = Field(None, description="Essential venue amenities")
    decorationAndAmbiance: Optional[DecorationAndAmbiance] = Field(None, description="Decoration preferences")
    foodAndCatering: Optional[FoodAndCatering] = Field(None, description="Food and catering preferences")
    additionalRequirements: Optional[AdditionalRequirements] = Field(None, description="Additional requirements")
    budget: Optional[float] = Field(None, gt=0, description="Total budget")
    eventDate: Optional[str] = Field(None, description="Event date")
    location: Optional[str] = Field(None, description="Event location")
    
    @validator('guestCount', pre=True)
    def validate_guest_count(cls, v):
        """Validate and normalize guest count"""
        if isinstance(v, int):
            return {"total": v, "Reception": v}
        elif isinstance(v, dict):
            return v
        return v


class VendorInfo(BaseModel):
    """Vendor information schema"""
    vendor_id: str = Field(..., description="Vendor identifier")
    name: str = Field(..., description="Vendor name")
    service_type: str = Field(..., description="Type of service provided")
    location_city: Optional[str] = Field(None, description="Vendor location")
    ranking_score: Optional[float] = Field(None, description="Vendor ranking score")
    price_info: Optional[Dict[str, Any]] = Field(None, description="Pricing information")
    contact_info: Optional[Dict[str, Any]] = Field(None, description="Contact information")
    amenities: Optional[List[str]] = Field(None, description="Available amenities")
    capacity: Optional[int] = Field(None, description="Venue capacity")


class EventCombination(BaseModel):
    """Event vendor combination schema"""
    combination_id: str = Field(..., description="Unique combination identifier")
    venue: Optional[VendorInfo] = Field(None, description="Selected venue")
    caterer: Optional[VendorInfo] = Field(None, description="Selected caterer")
    photographer: Optional[VendorInfo] = Field(None, description="Selected photographer")
    makeup_artist: Optional[VendorInfo] = Field(None, description="Selected makeup artist")
    total_score: Optional[float] = Field(None, description="Total combination score")
    estimated_cost: Optional[float] = Field(None, description="Estimated total cost")
    feasibility_score: Optional[float] = Field(None, description="Feasibility score")


class WorkflowStatus(BaseModel):
    """Workflow execution status"""
    current_step: str = Field(..., description="Current workflow step")
    progress_percentage: float = Field(..., ge=0, le=100, description="Progress percentage")
    steps_completed: List[str] = Field(default_factory=list, description="Completed steps")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class EventPlanResponse(BaseModel):
    """Response schema for event plan"""
    plan_id: str = Field(..., description="Unique plan identifier")
    status: PlanStatus = Field(..., description="Plan status")
    client_name: str = Field(..., description="Client name")
    combinations: List[EventCombination] = Field(default_factory=list, description="Available combinations")
    selected_combination: Optional[EventCombination] = Field(None, description="Selected combination")
    final_blueprint: Optional[str] = Field(None, description="Final event blueprint")
    workflow_status: Optional[WorkflowStatus] = Field(None, description="Workflow execution status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        use_enum_values = True


class CombinationSelection(BaseModel):
    """Schema for selecting a combination"""
    combination_id: str = Field(..., description="ID of the selected combination")
    notes: Optional[str] = Field(None, description="Additional notes")
    client_feedback: Optional[Dict[str, Any]] = Field(None, description="Client feedback")


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class HealthResponse(BaseModel):
    """Health check response schema"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    components: Optional[Dict[str, str]] = Field(None, description="Component health status")


class PlanListResponse(BaseModel):
    """Response schema for listing plans"""
    plans: List[EventPlanResponse] = Field(..., description="List of event plans")
    total_count: int = Field(..., description="Total number of plans")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=10, description="Page size")


class AsyncTaskResponse(BaseModel):
    """Response for asynchronous task creation"""
    task_id: str = Field(..., description="Async task identifier")
    plan_id: str = Field(..., description="Associated plan identifier")
    status: str = Field(..., description="Task status")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    status_url: str = Field(..., description="URL to check task status")