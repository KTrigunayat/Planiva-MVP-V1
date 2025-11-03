"""
Venue Lookup Tool for Task Management Agent

This tool retrieves and attaches venue information to tasks by:
- Extracting venue from EventPlanningState.selected_combination
- Querying database for detailed venue information (capacity, equipment, setup/teardown times, restrictions)
- Using MCP vendor server if available for enhanced venue information
- Flagging tasks requiring venue selection

Integrates with:
- EventPlanningState.selected_combination for venue data
- Database for detailed venue information
- MCP vendor server (if available) for enhanced information
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import timedelta

from ..models.data_models import VenueInfo
from ..models.consolidated_models import ConsolidatedTask, ConsolidatedTaskData
from ..exceptions import ToolExecutionError
from ....workflows.state_models import EventPlanningState
from ....database.connection import get_connection_manager
from ....database.models import Venue

logger = logging.getLogger(__name__)


class VenueLookupTool:
    """
    Tool for retrieving venue information for tasks.
    
    This tool:
    1. Extracts venue from selected_combination in EventPlanningState
    2. Queries database for detailed venue information
    3. Optionally uses MCP vendor server for enhanced data
    4. Attaches venue information to relevant tasks
    5. Flags tasks requiring venue selection
    """
    
    def __init__(self, db_connection=None, use_mcp: bool = True):
        """
        Initialize Venue Lookup Tool
        
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
        
        logger.info(f"VenueLookupTool initialized (MCP available: {self.mcp_available})")
    
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
    
    def lookup_venues(
        self,
        consolidated_data: ConsolidatedTaskData,
        state: EventPlanningState
    ) -> List[VenueInfo]:
        """
        Retrieve venue information for tasks
        
        Args:
            consolidated_data: Consolidated task data from sub-agents
            state: Current EventPlanningState with selected_combination
            
        Returns:
            List of VenueInfo objects
            
        Raises:
            ToolExecutionError: If venue lookup fails critically
        """
        try:
            logger.info(f"Starting venue lookup for {len(consolidated_data.tasks)} tasks")
            
            # Extract venue from selected combination
            venue_data = self._get_venue_from_combination(state)
            
            if not venue_data:
                logger.warning("No venue found in selected_combination")
                return self._create_missing_venue_info(consolidated_data.tasks)
            
            # Get detailed venue information from database
            venue_details = self._get_venue_details(venue_data['vendor_id'])
            
            if not venue_details:
                logger.warning(f"Venue {venue_data['vendor_id']} not found in database")
                return self._create_missing_venue_info(consolidated_data.tasks)
            
            # Optionally enhance with MCP server data
            if self.mcp_available:
                mcp_data = self._check_mcp_vendor_server(
                    venue_data['vendor_id'], state
                )
                if mcp_data:
                    venue_details.update(mcp_data)
            
            # Create venue info for relevant tasks
            venue_infos = []
            for task in consolidated_data.tasks:
                if self._task_requires_venue(task):
                    venue_info = self._create_venue_info(
                        task, venue_details
                    )
                    venue_infos.append(venue_info)
            
            logger.info(
                f"Completed venue lookup: {len(venue_infos)} tasks with venue information"
            )
            
            return venue_infos
            
        except Exception as e:
            logger.error(f"Venue lookup failed: {e}")
            raise ToolExecutionError(
                tool_name="VenueLookupTool",
                message=f"Failed to lookup venue information: {e}",
                details={'error_type': type(e).__name__}
            )
    
    def _get_venue_from_combination(
        self,
        state: EventPlanningState
    ) -> Optional[Dict[str, Any]]:
        """
        Extract venue from EventPlanningState.selected_combination
        
        Args:
            state: Current EventPlanningState
            
        Returns:
            Venue data dictionary if found, None otherwise
        """
        selected_combination = state.get('selected_combination')
        if not selected_combination:
            logger.warning("No selected_combination found in state")
            return None
        
        venue_data = selected_combination.get('venue')
        if not venue_data:
            logger.debug("No venue found in selected_combination")
            return None
        
        # Extract venue ID (handle different possible field names)
        venue_id = venue_data.get('vendor_id') or venue_data.get('id')
        if not venue_id:
            logger.warning("Venue ID not found in venue data")
            return None
        
        # Normalize venue data structure
        return {
            'vendor_id': str(venue_id),
            'name': venue_data.get('name', 'Unknown Venue'),
            'data': venue_data
        }
    
    def _get_venue_details(
        self,
        venue_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Query database for detailed venue information (capacity, equipment, 
        setup/teardown times, restrictions)
        
        Args:
            venue_id: Venue ID to query
            
        Returns:
            Dictionary with detailed venue information, None if not found
        """
        try:
            with self.db_manager.get_sync_session() as session:
                venue = session.query(Venue).filter(
                    Venue.vendor_id == venue_id
                ).first()
                
                if not venue:
                    logger.warning(f"Venue {venue_id} not found in database")
                    return None
                
                # Extract venue details
                details = {
                    'vendor_id': str(venue.vendor_id),
                    'name': venue.name,
                    'venue_type': venue.area_type or 'General',
                    'location_city': venue.location_city,
                    'location_full': venue.location_full,
                    'capacity': venue.max_seating_capacity or 0,
                    'ideal_capacity': venue.ideal_capacity or 0,
                    'room_count': venue.room_count or 1,
                    'rental_cost': venue.rental_cost or 0,
                    'room_cost': venue.room_cost or 0,
                    'decor_options': venue.decor_options or {},
                    'attributes': venue.attributes or {},
                    'policies': venue.policies or {}
                }
                
                # Extract available equipment from decor options and attributes
                available_equipment = []
                
                # Add equipment from decor options
                if isinstance(details['decor_options'], dict):
                    available_equipment.extend(details['decor_options'].keys())
                
                # Add equipment from attributes
                if isinstance(details['attributes'], dict):
                    available_equipment.extend(details['attributes'].keys())
                
                details['available_equipment'] = list(set(available_equipment))
                
                # Extract setup/teardown times from policies or use defaults
                policies = details['policies']
                if isinstance(policies, dict):
                    # Look for setup/teardown time information in policies
                    setup_hours = policies.get('setup_time_hours', 2)
                    teardown_hours = policies.get('teardown_time_hours', 1)
                else:
                    # Default values
                    setup_hours = 2
                    teardown_hours = 1
                
                details['setup_time_required'] = timedelta(hours=setup_hours)
                details['teardown_time_required'] = timedelta(hours=teardown_hours)
                
                # Extract access restrictions from policies
                access_restrictions = []
                if isinstance(policies, dict):
                    if policies.get('no_outside_decorators'):
                        access_restrictions.append('No outside decorators allowed')
                    if policies.get('no_outside_catering'):
                        access_restrictions.append('No outside catering allowed')
                    if policies.get('limited_setup_time'):
                        access_restrictions.append('Limited setup time')
                    if policies.get('noise_restrictions'):
                        access_restrictions.append('Noise restrictions apply')
                    if policies.get('parking_limited'):
                        access_restrictions.append('Limited parking available')
                    
                    # Add any other restriction fields
                    for key, value in policies.items():
                        if 'restriction' in key.lower() and value:
                            access_restrictions.append(f"{key.replace('_', ' ').title()}")
                
                details['access_restrictions'] = access_restrictions
                
                logger.debug(
                    f"Retrieved venue details: {details['name']} "
                    f"(capacity: {details['capacity']}, "
                    f"equipment: {len(details['available_equipment'])})"
                )
                
                return details
                
        except Exception as e:
            logger.error(f"Failed to query venue details: {e}")
            return None
    
    def _check_mcp_vendor_server(
        self,
        venue_id: str,
        state: EventPlanningState
    ) -> Optional[Dict[str, Any]]:
        """
        Use MCP vendor server if available for enhanced venue information
        
        Args:
            venue_id: Venue ID
            state: Current EventPlanningState
            
        Returns:
            Enhanced venue data if available, None otherwise
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
            logger.debug(f"Checking MCP vendor server for venue {venue_id}")
            
            # For now, return None as MCP integration would require async context
            # In a full implementation, this would call:
            # availability = await self.mcp_server.venue_availability_check(...)
            # enhanced_data = await self.mcp_server.get_venue_details(...)
            return None
            
        except Exception as e:
            logger.warning(f"MCP vendor server check failed: {e}")
            return None
    
    def _task_requires_venue(self, task: ConsolidatedTask) -> bool:
        """
        Determine if a task requires venue information
        
        Args:
            task: Task to check
            
        Returns:
            True if task requires venue information, False otherwise
        """
        # Check task name and description for venue-related keywords
        task_text = f"{task.task_name} {task.task_description}".lower()
        
        venue_keywords = [
            'venue', 'location', 'space', 'hall', 'room', 'setup', 'decoration',
            'seating', 'layout', 'floor plan', 'site visit', 'capacity',
            'equipment', 'facility', 'premises', 'site', 'place'
        ]
        
        if any(keyword in task_text for keyword in venue_keywords):
            return True
        
        # Check resource requirements
        for resource in task.resources_required:
            if resource.resource_type == 'venue':
                return True
            if resource.resource_type == 'equipment':
                # Equipment tasks often need venue information
                return True
        
        return False
    
    def _create_venue_info(
        self,
        task: ConsolidatedTask,
        venue_details: Dict[str, Any]
    ) -> VenueInfo:
        """
        Create VenueInfo object for a task
        
        Args:
            task: Task to create venue info for
            venue_details: Detailed venue information from database
            
        Returns:
            VenueInfo object
        """
        return VenueInfo(
            task_id=task.task_id,
            venue_id=venue_details['vendor_id'],
            venue_name=venue_details['name'],
            venue_type=venue_details['venue_type'],
            capacity=venue_details['capacity'],
            available_equipment=venue_details['available_equipment'],
            setup_time_required=venue_details['setup_time_required'],
            teardown_time_required=venue_details['teardown_time_required'],
            access_restrictions=venue_details['access_restrictions'],
            requires_venue_selection=False
        )
    
    def _flag_venue_selection_needed(
        self,
        task: ConsolidatedTask
    ) -> VenueInfo:
        """
        Mark tasks requiring venue selection
        
        Args:
            task: Task requiring venue selection
            
        Returns:
            VenueInfo object flagged for venue selection
        """
        return VenueInfo(
            task_id=task.task_id,
            venue_id="",
            venue_name="[Venue Selection Required]",
            venue_type="Unknown",
            capacity=0,
            available_equipment=[],
            setup_time_required=timedelta(hours=2),
            teardown_time_required=timedelta(hours=1),
            access_restrictions=[],
            requires_venue_selection=True
        )
    
    def _create_missing_venue_info(
        self,
        tasks: List[ConsolidatedTask]
    ) -> List[VenueInfo]:
        """
        Create venue info for tasks when venue data is missing
        
        Args:
            tasks: List of tasks
            
        Returns:
            List of VenueInfo objects flagged for venue selection
        """
        venue_infos = []
        
        for task in tasks:
            # Only create venue info for tasks that require venue
            if self._task_requires_venue(task):
                venue_info = self._flag_venue_selection_needed(task)
                venue_infos.append(venue_info)
        
        return venue_infos
