"""
Logistics Check Tool for Task Management Agent

This tool verifies logistics feasibility for tasks by checking:
- Transportation requirements and availability based on venue location
- Equipment availability from vendor and venue resources
- Setup time, space requirements, and venue constraints
- Overall logistics feasibility scoring

Integrates with:
- Database for venue and vendor details
- EventPlanningState for selected combination data
- Resource requirements from consolidated task data
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import timedelta

from ..models.data_models import LogisticsStatus, Resource
from ..models.consolidated_models import ConsolidatedTask, ConsolidatedTaskData
from ..exceptions import ToolExecutionError
from ....workflows.state_models import EventPlanningState
from ....database.connection import get_connection_manager
from ....database.models import Venue, Caterer, Photographer, MakeupArtist

logger = logging.getLogger(__name__)


class LogisticsCheckTool:
    """
    Tool for verifying logistics feasibility for tasks.
    
    This tool:
    1. Checks transportation requirements based on venue location
    2. Verifies equipment availability from vendors and venue
    3. Validates setup time and space requirements
    4. Calculates overall logistics feasibility scores
    5. Flags tasks with logistical issues
    """
    
    def __init__(self, db_connection=None):
        """
        Initialize Logistics Check Tool
        
        Args:
            db_connection: Optional database connection (uses default if None)
        """
        self.db_manager = db_connection or get_connection_manager()
        logger.info("LogisticsCheckTool initialized")
    
    def verify_logistics(
        self,
        consolidated_data: ConsolidatedTaskData,
        state: EventPlanningState
    ) -> List[LogisticsStatus]:
        """
        Verify logistics feasibility for all tasks
        
        Args:
            consolidated_data: Consolidated task data from sub-agents
            state: Current EventPlanningState with selected_combination
            
        Returns:
            List of LogisticsStatus objects
            
        Raises:
            ToolExecutionError: If logistics verification fails critically
        """
        try:
            logger.info(f"Starting logistics verification for {len(consolidated_data.tasks)} tasks")
            
            # Extract venue and vendor information from state
            selected_combination = state.get('selected_combination')
            if not selected_combination:
                logger.warning("No selected_combination found in state")
                return self._create_missing_data_statuses(consolidated_data.tasks)
            
            # Get venue details
            venue_info = self._get_venue_info(selected_combination)
            
            # Get vendor details
            vendor_info = self._get_vendor_info(selected_combination)
            
            # Verify logistics for each task
            logistics_statuses = []
            for task in consolidated_data.tasks:
                status = self._verify_task_logistics(
                    task, venue_info, vendor_info, state
                )
                logistics_statuses.append(status)
            
            logger.info(
                f"Completed logistics verification: "
                f"{sum(1 for s in logistics_statuses if s.overall_feasibility == 'feasible')} feasible, "
                f"{sum(1 for s in logistics_statuses if s.overall_feasibility == 'needs_attention')} need attention, "
                f"{sum(1 for s in logistics_statuses if s.overall_feasibility == 'not_feasible')} not feasible"
            )
            
            return logistics_statuses
            
        except Exception as e:
            logger.error(f"Logistics verification failed: {e}")
            raise ToolExecutionError(
                tool_name="LogisticsCheckTool",
                message=f"Failed to verify logistics: {e}",
                details={'error_type': type(e).__name__}
            )
    
    def _get_venue_info(self, selected_combination: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract venue information from selected combination
        
        Args:
            selected_combination: Selected vendor combination from state
            
        Returns:
            Venue information dictionary or None
        """
        venue_data = selected_combination.get('venue')
        if not venue_data:
            logger.warning("No venue found in selected_combination")
            return None
        
        venue_id = venue_data.get('vendor_id') or venue_data.get('id')
        if not venue_id:
            logger.warning("Venue ID not found in venue data")
            return None
        
        # Query database for detailed venue information
        try:
            with self.db_manager.get_sync_session() as session:
                venue = session.query(Venue).filter(
                    Venue.vendor_id == venue_id
                ).first()
                
                if not venue:
                    logger.warning(f"Venue {venue_id} not found in database")
                    return None
                
                return {
                    'vendor_id': str(venue.vendor_id),
                    'name': venue.name,
                    'location_city': venue.location_city,
                    'location_full': venue.location_full,
                    'max_seating_capacity': venue.max_seating_capacity,
                    'ideal_capacity': venue.ideal_capacity,
                    'room_count': venue.room_count,
                    'decor_options': venue.decor_options or {},
                    'attributes': venue.attributes or {},
                    'policies': venue.policies or {}
                }
        except Exception as e:
            logger.error(f"Failed to query venue details: {e}")
            return None
    
    def _get_vendor_info(self, selected_combination: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Extract vendor information from selected combination
        
        Args:
            selected_combination: Selected vendor combination from state
            
        Returns:
            Dictionary mapping vendor types to vendor information
        """
        vendors = {}
        
        # Extract caterer
        caterer_data = selected_combination.get('caterer')
        if caterer_data:
            caterer_id = caterer_data.get('vendor_id') or caterer_data.get('id')
            if caterer_id:
                vendors['caterer'] = self._query_caterer_details(caterer_id)
        
        # Extract photographer
        photographer_data = selected_combination.get('photographer')
        if photographer_data:
            photographer_id = photographer_data.get('vendor_id') or photographer_data.get('id')
            if photographer_id:
                vendors['photographer'] = self._query_photographer_details(photographer_id)
        
        # Extract makeup artist
        makeup_data = selected_combination.get('makeup_artist')
        if makeup_data:
            makeup_id = makeup_data.get('vendor_id') or makeup_data.get('id')
            if makeup_id:
                vendors['makeup_artist'] = self._query_makeup_artist_details(makeup_id)
        
        return vendors
    
    def _query_caterer_details(self, caterer_id: str) -> Optional[Dict[str, Any]]:
        """Query database for caterer details"""
        try:
            with self.db_manager.get_sync_session() as session:
                caterer = session.query(Caterer).filter(
                    Caterer.vendor_id == caterer_id
                ).first()
                
                if not caterer:
                    return None
                
                return {
                    'vendor_id': str(caterer.vendor_id),
                    'name': caterer.name,
                    'location_city': caterer.location_city,
                    'max_guest_capacity': caterer.max_guest_capacity,
                    'attributes': caterer.attributes or {}
                }
        except Exception as e:
            logger.error(f"Failed to query caterer details: {e}")
            return None
    
    def _query_photographer_details(self, photographer_id: str) -> Optional[Dict[str, Any]]:
        """Query database for photographer details"""
        try:
            with self.db_manager.get_sync_session() as session:
                photographer = session.query(Photographer).filter(
                    Photographer.vendor_id == photographer_id
                ).first()
                
                if not photographer:
                    return None
                
                return {
                    'vendor_id': str(photographer.vendor_id),
                    'name': photographer.name,
                    'location_city': photographer.location_city,
                    'video_available': photographer.video_available,
                    'attributes': photographer.attributes or {}
                }
        except Exception as e:
            logger.error(f"Failed to query photographer details: {e}")
            return None
    
    def _query_makeup_artist_details(self, makeup_id: str) -> Optional[Dict[str, Any]]:
        """Query database for makeup artist details"""
        try:
            with self.db_manager.get_sync_session() as session:
                makeup_artist = session.query(MakeupArtist).filter(
                    MakeupArtist.vendor_id == makeup_id
                ).first()
                
                if not makeup_artist:
                    return None
                
                return {
                    'vendor_id': str(makeup_artist.vendor_id),
                    'name': makeup_artist.name,
                    'location_city': makeup_artist.location_city,
                    'on_site_service': makeup_artist.on_site_service,
                    'attributes': makeup_artist.attributes or {}
                }
        except Exception as e:
            logger.error(f"Failed to query makeup artist details: {e}")
            return None
    
    def _verify_task_logistics(
        self,
        task: ConsolidatedTask,
        venue_info: Optional[Dict[str, Any]],
        vendor_info: Dict[str, Dict[str, Any]],
        state: EventPlanningState
    ) -> LogisticsStatus:
        """
        Verify logistics for a single task
        
        Args:
            task: Task to verify
            venue_info: Venue information
            vendor_info: Vendor information
            state: Current EventPlanningState
            
        Returns:
            LogisticsStatus object
        """
        # Check transportation
        transportation_result = self._check_transportation(task, venue_info)
        
        # Check equipment
        equipment_result = self._check_equipment(task, venue_info, vendor_info)
        
        # Check setup requirements
        setup_result = self._check_setup_requirements(task, venue_info)
        
        # Calculate overall feasibility
        feasibility_score = self._calculate_feasibility_score(
            transportation_result, equipment_result, setup_result
        )
        
        # Determine overall feasibility status
        if feasibility_score >= 0.8:
            overall_feasibility = "feasible"
        elif feasibility_score >= 0.5:
            overall_feasibility = "needs_attention"
        else:
            overall_feasibility = "not_feasible"
        
        # Collect all issues
        issues = []
        issues.extend(transportation_result.get('issues', []))
        issues.extend(equipment_result.get('issues', []))
        issues.extend(setup_result.get('issues', []))
        
        return LogisticsStatus(
            task_id=task.task_id,
            transportation_status=transportation_result['status'],
            transportation_notes=transportation_result['notes'],
            equipment_status=equipment_result['status'],
            equipment_notes=equipment_result['notes'],
            setup_status=setup_result['status'],
            setup_notes=setup_result['notes'],
            overall_feasibility=overall_feasibility,
            issues=issues
        )
    
    def _check_transportation(
        self,
        task: ConsolidatedTask,
        venue_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Verify transportation requirements and availability based on venue location
        
        Args:
            task: Task to check
            venue_info: Venue information
            
        Returns:
            Dictionary with status, notes, and issues
        """
        issues = []
        
        # Check if venue information is available
        if not venue_info:
            return {
                'status': 'missing_data',
                'notes': 'Venue information not available for transportation check',
                'issues': ['Missing venue information']
            }
        
        # Analyze task for transportation needs
        task_text = f"{task.task_name} {task.task_description}".lower()
        transportation_keywords = [
            'transport', 'delivery', 'pickup', 'travel', 'move', 'ship',
            'logistics', 'arrival', 'departure'
        ]
        
        needs_transportation = any(keyword in task_text for keyword in transportation_keywords)
        
        if not needs_transportation:
            return {
                'status': 'verified',
                'notes': 'No specific transportation requirements identified',
                'issues': []
            }
        
        # Check venue location accessibility
        venue_location = venue_info.get('location_city', '')
        venue_full_location = venue_info.get('location_full', '')
        
        if not venue_location:
            issues.append('Venue location not specified')
        
        # Check for resource transportation needs
        for resource in task.resources_required:
            if resource.resource_type == 'equipment':
                # Equipment may need transportation
                if 'large' in resource.resource_name.lower() or 'heavy' in resource.resource_name.lower():
                    issues.append(f'Large equipment ({resource.resource_name}) may require special transportation')
        
        # Determine status
        if issues:
            status = 'issue'
            notes = f"Transportation to {venue_location} requires attention. {len(issues)} issue(s) identified."
        else:
            status = 'verified'
            notes = f"Transportation to {venue_location} appears feasible"
        
        return {
            'status': status,
            'notes': notes,
            'issues': issues
        }
    
    def _check_equipment(
        self,
        task: ConsolidatedTask,
        venue_info: Optional[Dict[str, Any]],
        vendor_info: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Verify equipment availability from vendor and venue resources
        
        Args:
            task: Task to check
            venue_info: Venue information
            vendor_info: Vendor information
            
        Returns:
            Dictionary with status, notes, and issues
        """
        issues = []
        
        # Get equipment requirements from task resources
        equipment_resources = [
            r for r in task.resources_required 
            if r.resource_type == 'equipment'
        ]
        
        if not equipment_resources:
            return {
                'status': 'verified',
                'notes': 'No equipment requirements identified',
                'issues': []
            }
        
        # Check venue equipment availability
        venue_equipment = []
        if venue_info:
            decor_options = venue_info.get('decor_options', {})
            attributes = venue_info.get('attributes', {})
            
            # Extract available equipment from venue
            if isinstance(decor_options, dict):
                venue_equipment.extend(decor_options.keys())
            if isinstance(attributes, dict):
                venue_equipment.extend(attributes.keys())
        
        # Check each equipment requirement
        for equipment in equipment_resources:
            equipment_name = equipment.resource_name.lower()
            
            # Check if venue provides this equipment
            venue_has_equipment = any(
                equip.lower() in equipment_name or equipment_name in equip.lower()
                for equip in venue_equipment
            )
            
            if not venue_has_equipment:
                # Check if any vendor can provide it
                vendor_has_equipment = False
                
                for vendor_type, vendor_data in vendor_info.items():
                    if vendor_data:
                        vendor_attrs = vendor_data.get('attributes', {})
                        if isinstance(vendor_attrs, dict):
                            vendor_has_equipment = any(
                                equip.lower() in equipment_name or equipment_name in equip.lower()
                                for equip in vendor_attrs.keys()
                            )
                            if vendor_has_equipment:
                                break
                
                if not vendor_has_equipment:
                    issues.append(
                        f"Equipment '{equipment.resource_name}' not available from venue or vendors"
                    )
        
        # Determine status
        if issues:
            status = 'issue'
            notes = f"{len(equipment_resources)} equipment item(s) required, {len(issues)} unavailable"
        else:
            status = 'verified'
            notes = f"All {len(equipment_resources)} equipment item(s) available"
        
        return {
            'status': status,
            'notes': notes,
            'issues': issues
        }
    
    def _check_setup_requirements(
        self,
        task: ConsolidatedTask,
        venue_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Verify setup time, space requirements, and venue constraints
        
        Args:
            task: Task to check
            venue_info: Venue information
            
        Returns:
            Dictionary with status, notes, and issues
        """
        issues = []
        
        if not venue_info:
            return {
                'status': 'missing_data',
                'notes': 'Venue information not available for setup verification',
                'issues': ['Missing venue information']
            }
        
        # Analyze task for setup requirements
        task_text = f"{task.task_name} {task.task_description}".lower()
        setup_keywords = ['setup', 'install', 'arrange', 'prepare', 'configure', 'decorate']
        
        needs_setup = any(keyword in task_text for keyword in setup_keywords)
        
        if not needs_setup:
            return {
                'status': 'verified',
                'notes': 'No specific setup requirements identified',
                'issues': []
            }
        
        # Check venue capacity constraints
        max_capacity = venue_info.get('max_seating_capacity', 0)
        ideal_capacity = venue_info.get('ideal_capacity', 0)
        
        # Check if task mentions guest count or capacity
        if 'guest' in task_text or 'seating' in task_text or 'capacity' in task_text:
            if max_capacity == 0:
                issues.append('Venue capacity not specified, cannot verify space requirements')
        
        # Check setup time requirements
        estimated_duration = task.estimated_duration
        
        # Tasks requiring significant setup time
        if any(keyword in task_text for keyword in ['decoration', 'stage', 'lighting', 'sound']):
            # These typically need several hours
            if estimated_duration < timedelta(hours=2):
                issues.append(
                    f"Task may require more setup time than estimated "
                    f"({estimated_duration.total_seconds() / 3600:.1f} hours)"
                )
        
        # Check venue policies and restrictions
        venue_policies = venue_info.get('policies', {})
        if isinstance(venue_policies, dict):
            # Check for restrictive policies
            if venue_policies.get('no_outside_decorators'):
                if 'decor' in task_text or 'decoration' in task_text:
                    issues.append('Venue does not allow outside decorators')
            
            if venue_policies.get('limited_setup_time'):
                issues.append('Venue has limited setup time restrictions')
        
        # Check room availability for multi-room setups
        room_count = venue_info.get('room_count', 1)
        if 'multiple room' in task_text or 'different room' in task_text:
            if room_count < 2:
                issues.append('Task requires multiple rooms but venue has limited rooms')
        
        # Determine status
        if issues:
            status = 'issue'
            notes = f"Setup requirements need attention. {len(issues)} constraint(s) identified."
        else:
            status = 'verified'
            notes = "Setup requirements appear feasible within venue constraints"
        
        return {
            'status': status,
            'notes': notes,
            'issues': issues
        }
    
    def _calculate_feasibility_score(
        self,
        transportation_result: Dict[str, Any],
        equipment_result: Dict[str, Any],
        setup_result: Dict[str, Any]
    ) -> float:
        """
        Determine overall logistics feasibility score
        
        Args:
            transportation_result: Transportation check results
            equipment_result: Equipment check results
            setup_result: Setup check results
            
        Returns:
            Feasibility score between 0.0 and 1.0
        """
        # Define weights for each component
        weights = {
            'transportation': 0.3,
            'equipment': 0.4,
            'setup': 0.3
        }
        
        # Calculate component scores
        def status_to_score(status: str) -> float:
            """Convert status to numerical score"""
            if status == 'verified':
                return 1.0
            elif status == 'issue':
                return 0.5
            elif status == 'missing_data':
                return 0.3
            else:
                return 0.0
        
        transportation_score = status_to_score(transportation_result['status'])
        equipment_score = status_to_score(equipment_result['status'])
        setup_score = status_to_score(setup_result['status'])
        
        # Penalize based on number of issues
        transportation_penalty = len(transportation_result.get('issues', [])) * 0.1
        equipment_penalty = len(equipment_result.get('issues', [])) * 0.1
        setup_penalty = len(setup_result.get('issues', [])) * 0.1
        
        transportation_score = max(0.0, transportation_score - transportation_penalty)
        equipment_score = max(0.0, equipment_score - equipment_penalty)
        setup_score = max(0.0, setup_score - setup_penalty)
        
        # Calculate weighted average
        overall_score = (
            transportation_score * weights['transportation'] +
            equipment_score * weights['equipment'] +
            setup_score * weights['setup']
        )
        
        return min(1.0, max(0.0, overall_score))
    
    def _flag_logistics_issues(
        self,
        task: ConsolidatedTask,
        issues: List[str]
    ) -> LogisticsStatus:
        """
        Mark tasks with logistical problems
        
        Args:
            task: Task with issues
            issues: List of identified issues
            
        Returns:
            LogisticsStatus flagged with issues
        """
        return LogisticsStatus(
            task_id=task.task_id,
            transportation_status='issue',
            transportation_notes='Logistics issues identified',
            equipment_status='issue',
            equipment_notes='Logistics issues identified',
            setup_status='issue',
            setup_notes='Logistics issues identified',
            overall_feasibility='not_feasible',
            issues=issues
        )
    
    def _create_missing_data_statuses(
        self,
        tasks: List[ConsolidatedTask]
    ) -> List[LogisticsStatus]:
        """
        Create logistics statuses when venue/vendor data is missing
        
        Args:
            tasks: List of tasks
            
        Returns:
            List of LogisticsStatus objects with missing_data status
        """
        statuses = []
        
        for task in tasks:
            status = LogisticsStatus(
                task_id=task.task_id,
                transportation_status='missing_data',
                transportation_notes='Venue information not available',
                equipment_status='missing_data',
                equipment_notes='Venue and vendor information not available',
                setup_status='missing_data',
                setup_notes='Venue information not available',
                overall_feasibility='needs_attention',
                issues=['Missing venue and vendor information for logistics verification']
            )
            statuses.append(status)
        
        return statuses
