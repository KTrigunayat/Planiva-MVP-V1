"""
Vendor Task Tool for Task Management Agent

This tool assigns vendors from the selected combination to appropriate tasks based on:
- Task requirements and resource needs
- Vendor capabilities and service types
- Fitness scores from beam search results
- Task-vendor matching logic

Integrates with:
- EventPlanningState.selected_combination for vendor data
- Database for additional vendor details
- MCP vendor server (if available) for enhanced information
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.data_models import VendorAssignment, Resource
from ..models.consolidated_models import ConsolidatedTask, ConsolidatedTaskData
from ..exceptions import ToolExecutionError
from ....workflows.state_models import EventPlanningState
from ....database.connection import get_connection_manager
from ....database.models import Venue, Caterer, Photographer, MakeupArtist

logger = logging.getLogger(__name__)


class VendorTaskTool:
    """
    Tool for assigning vendors to tasks based on selected combination and task requirements.
    
    This tool:
    1. Analyzes task resource requirements
    2. Matches vendors from selected_combination to tasks
    3. Uses fitness scores from beam search for prioritization
    4. Queries database for additional vendor details
    5. Optionally uses MCP vendor server for enhanced information
    6. Flags tasks requiring manual vendor assignment
    """
    
    def __init__(self, db_connection=None, use_mcp: bool = True):
        """
        Initialize Vendor Task Tool
        
        Args:
            db_connection: Optional database connection (uses default if None)
            use_mcp: Whether to attempt using MCP vendor server for enhanced data
        """
        self.db_manager = db_connection or get_connection_manager()
        self.use_mcp = use_mcp
        self.mcp_available = False
        
        # Try to initialize MCP vendor server connection
        if self.use_mcp:
            self._check_mcp_availability()
        
        logger.info(f"VendorTaskTool initialized (MCP available: {self.mcp_available})")
    
    def _check_mcp_availability(self):
        """Check if MCP vendor server is available"""
        try:
            # Try to import MCP vendor server
            from ....mcp_servers.vendor_server import VendorDataServer
            self.mcp_server = VendorDataServer()
            self.mcp_available = True
            logger.info("MCP vendor server is available")
        except Exception as e:
            logger.warning(f"MCP vendor server not available: {e}")
            self.mcp_available = False
    
    def assign_vendors(
        self,
        consolidated_data: ConsolidatedTaskData,
        state: EventPlanningState
    ) -> List[VendorAssignment]:
        """
        Assign vendors to tasks based on selected combination and task requirements
        
        Args:
            consolidated_data: Consolidated task data from sub-agents
            state: Current EventPlanningState with selected_combination
            
        Returns:
            List of VendorAssignment objects
            
        Raises:
            ToolExecutionError: If vendor assignment fails critically
        """
        try:
            logger.info(f"Starting vendor assignment for {len(consolidated_data.tasks)} tasks")
            
            # Extract selected combination from state
            selected_combination = state.get('selected_combination')
            if not selected_combination:
                logger.warning("No selected_combination found in state, cannot assign vendors")
                return self._create_empty_assignments(consolidated_data.tasks)
            
            # Extract vendors from selected combination
            available_vendors = self._extract_vendors_from_combination(selected_combination)
            
            if not available_vendors:
                logger.warning("No vendors found in selected_combination")
                return self._create_empty_assignments(consolidated_data.tasks)
            
            # Assign vendors to tasks
            assignments = []
            for task in consolidated_data.tasks:
                task_assignments = self._assign_vendors_to_task(
                    task, available_vendors, state
                )
                assignments.extend(task_assignments)
            
            logger.info(f"Completed vendor assignment: {len(assignments)} assignments created")
            return assignments
            
        except Exception as e:
            logger.error(f"Vendor assignment failed: {e}")
            raise ToolExecutionError(f"Failed to assign vendors to tasks: {e}")
    
    def _extract_vendors_from_combination(
        self,
        selected_combination: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract vendor information from selected combination
        
        Args:
            selected_combination: Selected vendor combination from state
            
        Returns:
            Dictionary mapping vendor types to vendor data
        """
        vendors = {}
        
        # Extract each vendor type
        vendor_types = ['venue', 'caterer', 'photographer', 'makeup_artist']
        
        for vendor_type in vendor_types:
            vendor_data = selected_combination.get(vendor_type)
            if vendor_data:
                vendors[vendor_type] = {
                    'vendor_id': vendor_data.get('vendor_id') or vendor_data.get('id'),
                    'name': vendor_data.get('name', 'Unknown'),
                    'vendor_type': vendor_type,
                    'fitness_score': selected_combination.get('fitness_score', 0.0),
                    'data': vendor_data
                }
                logger.debug(f"Extracted {vendor_type}: {vendors[vendor_type]['name']}")
        
        return vendors
    
    def _get_vendor_from_combination(
        self,
        vendor_type: str,
        state: EventPlanningState
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve specific vendor details from EventPlanningState.selected_combination
        
        Args:
            vendor_type: Type of vendor to retrieve (venue, caterer, photographer, makeup_artist)
            state: Current EventPlanningState
            
        Returns:
            Vendor data dictionary if found, None otherwise
        """
        selected_combination = state.get('selected_combination')
        if not selected_combination:
            logger.warning("No selected_combination found in state")
            return None
        
        vendor_data = selected_combination.get(vendor_type)
        if not vendor_data:
            logger.debug(f"No {vendor_type} found in selected_combination")
            return None
        
        # Normalize vendor data structure
        return {
            'vendor_id': vendor_data.get('vendor_id') or vendor_data.get('id'),
            'name': vendor_data.get('name', 'Unknown'),
            'vendor_type': vendor_type,
            'fitness_score': selected_combination.get('fitness_score', 0.0),
            'data': vendor_data
        }
    
    def _assign_vendors_to_task(
        self,
        task: ConsolidatedTask,
        available_vendors: Dict[str, Dict[str, Any]],
        state: EventPlanningState
    ) -> List[VendorAssignment]:
        """
        Assign appropriate vendors to a single task
        
        Args:
            task: Task to assign vendors to
            available_vendors: Available vendors from selected combination
            state: Current EventPlanningState
            
        Returns:
            List of VendorAssignment objects for this task
        """
        assignments = []
        
        # Analyze task requirements
        required_vendor_types = self._identify_required_vendor_types(task)
        
        if not required_vendor_types:
            logger.debug(f"Task {task.task_id} does not require vendor assignment")
            return assignments
        
        # Match vendors to task
        for vendor_type in required_vendor_types:
            vendor = available_vendors.get(vendor_type)
            
            if vendor:
                # Create assignment
                assignment = self._create_vendor_assignment(
                    task, vendor, state
                )
                assignments.append(assignment)
            else:
                # Flag for manual assignment
                assignment = self._flag_manual_assignment(
                    task, vendor_type
                )
                assignments.append(assignment)
        
        return assignments
    
    def _identify_required_vendor_types(
        self,
        task: ConsolidatedTask
    ) -> List[str]:
        """
        Identify which vendor types are required for a task
        
        Args:
            task: Task to analyze
            
        Returns:
            List of required vendor types
        """
        required_types = []
        
        # Check task name and description for vendor keywords
        task_text = f"{task.task_name} {task.task_description}".lower()
        
        # Venue-related keywords
        venue_keywords = [
            'venue', 'location', 'space', 'hall', 'room', 'setup', 'decoration',
            'seating', 'layout', 'floor plan', 'site visit'
        ]
        if any(keyword in task_text for keyword in venue_keywords):
            required_types.append('venue')
        
        # Catering-related keywords
        catering_keywords = [
            'catering', 'food', 'menu', 'meal', 'dining', 'cuisine', 'buffet',
            'service', 'beverage', 'refreshment', 'tasting'
        ]
        if any(keyword in task_text for keyword in catering_keywords):
            required_types.append('caterer')
        
        # Photography-related keywords
        photography_keywords = [
            'photo', 'video', 'camera', 'shoot', 'album', 'coverage',
            'cinematography', 'videography', 'portrait', 'candid'
        ]
        if any(keyword in task_text for keyword in photography_keywords):
            required_types.append('photographer')
        
        # Makeup-related keywords
        makeup_keywords = [
            'makeup', 'hair', 'beauty', 'styling', 'bridal look', 'grooming',
            'cosmetic', 'hairstyle', 'trial'
        ]
        if any(keyword in task_text for keyword in makeup_keywords):
            required_types.append('makeup_artist')
        
        # Also check resource requirements
        for resource in task.resources_required:
            if resource.resource_type == 'vendor':
                # Try to map resource name to vendor type
                resource_name = resource.resource_name.lower()
                if 'venue' in resource_name and 'venue' not in required_types:
                    required_types.append('venue')
                elif 'cater' in resource_name and 'caterer' not in required_types:
                    required_types.append('caterer')
                elif 'photo' in resource_name and 'photographer' not in required_types:
                    required_types.append('photographer')
                elif 'makeup' in resource_name and 'makeup_artist' not in required_types:
                    required_types.append('makeup_artist')
        
        return required_types
    
    def _create_vendor_assignment(
        self,
        task: ConsolidatedTask,
        vendor: Dict[str, Any],
        state: EventPlanningState
    ) -> VendorAssignment:
        """
        Create a vendor assignment for a task
        
        Args:
            task: Task to assign vendor to
            vendor: Vendor information
            state: Current EventPlanningState
            
        Returns:
            VendorAssignment object
        """
        vendor_id = vendor['vendor_id']
        vendor_type = vendor['vendor_type']
        
        # Get additional vendor details from database
        vendor_details = self._query_vendor_details(vendor_id, vendor_type)
        
        # Optionally enhance with MCP server data
        if self.mcp_available:
            mcp_data = self._check_mcp_vendor_server(vendor_id, vendor_type, state)
            if mcp_data:
                vendor_details.update(mcp_data)
        
        # Calculate match score
        match_score = self._match_vendor_to_task(task, vendor, vendor_details)
        
        # Generate assignment rationale
        rationale = self._generate_assignment_rationale(
            task, vendor, vendor_details, match_score
        )
        
        return VendorAssignment(
            task_id=task.task_id,
            vendor_id=vendor_id,
            vendor_name=vendor['name'],
            vendor_type=vendor_type,
            fitness_score=match_score,
            assignment_rationale=rationale,
            requires_manual_assignment=False
        )
    
    def _match_vendor_to_task(
        self,
        task: ConsolidatedTask,
        vendor: Dict[str, Any],
        vendor_details: Dict[str, Any]
    ) -> float:
        """
        Calculate match score between vendor and task
        
        Args:
            task: Task to match
            vendor: Vendor information
            vendor_details: Additional vendor details from database
            
        Returns:
            Match score between 0.0 and 1.0
        """
        # Start with base fitness score from beam search
        base_score = vendor.get('fitness_score', 0.5)
        
        # Adjust based on task priority
        priority_multiplier = {
            'Critical': 1.2,
            'High': 1.1,
            'Medium': 1.0,
            'Low': 0.9
        }.get(task.priority_level, 1.0)
        
        # Adjust based on vendor capabilities
        capability_score = 1.0
        
        # Check if vendor has required capabilities
        vendor_data = vendor.get('data', {})
        task_text = f"{task.task_name} {task.task_description}".lower()
        
        # Venue-specific matching
        if vendor['vendor_type'] == 'venue':
            # Check capacity if mentioned in task
            if 'capacity' in task_text or 'seating' in task_text:
                capacity = vendor_details.get('max_seating_capacity', 0)
                if capacity > 0:
                    capability_score *= 1.1
        
        # Caterer-specific matching
        elif vendor['vendor_type'] == 'caterer':
            # Check cuisine preferences
            if 'cuisine' in task_text or 'menu' in task_text:
                capability_score *= 1.1
        
        # Photographer-specific matching
        elif vendor['vendor_type'] == 'photographer':
            # Check video requirement
            if 'video' in task_text:
                has_video = vendor_details.get('video_available', False)
                capability_score *= 1.2 if has_video else 0.8
        
        # Calculate final match score
        match_score = base_score * priority_multiplier * capability_score
        
        # Normalize to 0.0-1.0 range
        return min(1.0, max(0.0, match_score))
    
    def _query_vendor_details(
        self,
        vendor_id: str,
        vendor_type: str
    ) -> Dict[str, Any]:
        """
        Query database for additional vendor details
        
        Args:
            vendor_id: Vendor ID
            vendor_type: Type of vendor
            
        Returns:
            Dictionary with vendor details
        """
        try:
            # Map vendor types to database models
            model_map = {
                'venue': Venue,
                'caterer': Caterer,
                'photographer': Photographer,
                'makeup_artist': MakeupArtist
            }
            
            model_class = model_map.get(vendor_type)
            if not model_class:
                logger.warning(f"Unknown vendor type: {vendor_type}")
                return {}
            
            # Query database
            with self.db_manager.get_sync_session() as session:
                vendor = session.query(model_class).filter(
                    model_class.vendor_id == vendor_id
                ).first()
                
                if not vendor:
                    logger.warning(f"Vendor {vendor_id} not found in database")
                    return {}
                
                # Extract relevant details based on vendor type
                details = {
                    'name': vendor.name,
                    'location_city': vendor.location_city,
                    'location_full': vendor.location_full,
                    'attributes': vendor.attributes or {}
                }
                
                # Add type-specific details
                if vendor_type == 'venue':
                    details.update({
                        'max_seating_capacity': vendor.max_seating_capacity,
                        'ideal_capacity': vendor.ideal_capacity,
                        'rental_cost': vendor.rental_cost,
                        'room_count': vendor.room_count,
                        'room_cost': vendor.room_cost
                    })
                elif vendor_type == 'caterer':
                    details.update({
                        'min_veg_price': vendor.min_veg_price,
                        'min_non_veg_price': vendor.min_non_veg_price,
                        'veg_only': vendor.veg_only,
                        'max_guest_capacity': vendor.max_guest_capacity
                    })
                elif vendor_type == 'photographer':
                    details.update({
                        'photo_package_price': vendor.photo_package_price,
                        'video_available': vendor.video_available
                    })
                elif vendor_type == 'makeup_artist':
                    details.update({
                        'bridal_makeup_price': vendor.bridal_makeup_price,
                        'on_site_service': vendor.on_site_service
                    })
                
                return details
                
        except Exception as e:
            logger.error(f"Failed to query vendor details: {e}")
            return {}
    
    def _check_mcp_vendor_server(
        self,
        vendor_id: str,
        vendor_type: str,
        state: EventPlanningState
    ) -> Optional[Dict[str, Any]]:
        """
        Use MCP vendor server for enhanced vendor information
        
        Args:
            vendor_id: Vendor ID
            vendor_type: Type of vendor
            state: Current EventPlanningState
            
        Returns:
            Enhanced vendor data if available, None otherwise
        """
        if not self.mcp_available:
            return None
        
        try:
            # Get event date from state for availability check
            client_request = state.get('client_request', {})
            event_date = client_request.get('date')
            
            if not event_date:
                logger.debug("No event date available for MCP availability check")
                return None
            
            # Call MCP vendor server for availability and enhanced data
            # This is a simplified version - actual implementation would use async
            logger.debug(f"Checking MCP vendor server for {vendor_id}")
            
            # For now, return None as MCP integration would require async context
            # In a full implementation, this would call:
            # availability = await self.mcp_server.vendor_availability_check(...)
            return None
            
        except Exception as e:
            logger.warning(f"MCP vendor server check failed: {e}")
            return None
    
    def _generate_assignment_rationale(
        self,
        task: ConsolidatedTask,
        vendor: Dict[str, Any],
        vendor_details: Dict[str, Any],
        match_score: float
    ) -> str:
        """
        Generate human-readable rationale for vendor assignment
        
        Args:
            task: Task being assigned
            vendor: Vendor information
            vendor_details: Additional vendor details
            match_score: Calculated match score
            
        Returns:
            Assignment rationale string
        """
        rationale_parts = []
        
        # Base assignment reason
        rationale_parts.append(
            f"{vendor['name']} assigned to '{task.task_name}' "
            f"(match score: {match_score:.2f})"
        )
        
        # Add priority context
        if task.priority_level in ['Critical', 'High']:
            rationale_parts.append(
                f"Task has {task.priority_level} priority, requiring reliable vendor"
            )
        
        # Add vendor-specific context
        vendor_type = vendor['vendor_type']
        if vendor_type == 'venue':
            capacity = vendor_details.get('max_seating_capacity')
            if capacity:
                rationale_parts.append(f"Venue capacity: {capacity} guests")
        
        elif vendor_type == 'caterer':
            veg_only = vendor_details.get('veg_only')
            if veg_only:
                rationale_parts.append("Provides vegetarian-only catering")
        
        elif vendor_type == 'photographer':
            video = vendor_details.get('video_available')
            if video:
                rationale_parts.append("Offers both photography and videography")
        
        elif vendor_type == 'makeup_artist':
            on_site = vendor_details.get('on_site_service')
            if on_site:
                rationale_parts.append("Provides on-site service")
        
        # Add location context
        location = vendor_details.get('location_city')
        if location:
            rationale_parts.append(f"Located in {location}")
        
        return ". ".join(rationale_parts)
    
    def _flag_manual_assignment(
        self,
        task: ConsolidatedTask,
        vendor_type: str
    ) -> VendorAssignment:
        """
        Create a vendor assignment flagged for manual review
        
        Args:
            task: Task requiring vendor
            vendor_type: Type of vendor needed
            
        Returns:
            VendorAssignment flagged for manual assignment
        """
        return VendorAssignment(
            task_id=task.task_id,
            vendor_id="",
            vendor_name=f"[Manual Assignment Required: {vendor_type}]",
            vendor_type=vendor_type,
            fitness_score=0.0,
            assignment_rationale=(
                f"No {vendor_type} found in selected combination. "
                f"Manual vendor assignment required for task '{task.task_name}'"
            ),
            requires_manual_assignment=True
        )
    
    def _create_empty_assignments(
        self,
        tasks: List[ConsolidatedTask]
    ) -> List[VendorAssignment]:
        """
        Create empty assignments when no vendors are available
        
        Args:
            tasks: List of tasks
            
        Returns:
            List of empty VendorAssignment objects
        """
        assignments = []
        
        for task in tasks:
            # Only create empty assignments for tasks that likely need vendors
            required_types = self._identify_required_vendor_types(task)
            
            for vendor_type in required_types:
                assignment = self._flag_manual_assignment(task, vendor_type)
                assignments.append(assignment)
        
        return assignments
