"""
Helper utilities for the Streamlit GUI
"""
import re
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union
import streamlit as st

# Import error handling utilities
try:
    from utils.error_handling import error_handler
except ImportError:
    # Fallback if error_handling module is not available
    error_handler = None

def format_currency(amount: Union[int, float], currency: str = "USD") -> str:
    """Format a number as currency"""
    if currency == "USD":
        return f"${amount:,.2f}"
    return f"{amount:,.2f} {currency}"

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    # Check if it's a valid length (10-15 digits)
    return 10 <= len(digits) <= 15

def format_date(date_obj: Union[date, datetime, str]) -> str:
    """Format date for display"""
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
        except:
            return date_obj
    
    if isinstance(date_obj, datetime):
        return date_obj.strftime("%B %d, %Y")
    elif isinstance(date_obj, date):
        return date_obj.strftime("%B %d, %Y")
    
    return str(date_obj)

def safe_get(dictionary: Dict, key: str, default: Any = None) -> Any:
    """Safely get a value from a dictionary"""
    try:
        keys = key.split('.')
        value = dictionary
        for k in keys:
            value = value[k]
        return value
    except (KeyError, TypeError):
        return default

def show_success(message: str, details: Optional[str] = None):
    """Show a success message"""
    if error_handler:
        error_handler.show_success(message, details)
    else:
        st.success(f"✅ {message}")
        if details:
            st.caption(details)

def show_error(message: str, details: Optional[str] = None):
    """Show an error message"""
    if error_handler:
        # Use basic error display (not API error)
        st.error(f"❌ {message}")
        if details:
            st.caption(details)
    else:
        st.error(f"❌ {message}")
        if details:
            st.caption(details)

def show_warning(message: str, details: Optional[str] = None):
    """Show a warning message"""
    if error_handler:
        error_handler.show_warning(message, details)
    else:
        st.warning(f"⚠️ {message}")
        if details:
            st.caption(details)

def show_info(message: str, details: Optional[str] = None):
    """Show an info message"""
    if error_handler:
        error_handler.show_info(message, details)
    else:
        st.info(f"ℹ️ {message}")
        if details:
            st.caption(details)

def init_session_state(key: str, default_value: Any):
    """Initialize a session state variable if it doesn't exist"""
    if key not in st.session_state:
        st.session_state[key] = default_value

def clear_session_state(keys: Optional[List[str]] = None):
    """Clear session state variables"""
    if keys is None:
        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
    else:
        # Clear specific keys
        for key in keys:
            if key in st.session_state:
                del st.session_state[key]

def get_progress_color(percentage: float) -> str:
    """Get color based on progress percentage"""
    if percentage < 25:
        return "#ff4444"  # Red
    elif percentage < 50:
        return "#ff8800"  # Orange
    elif percentage < 75:
        return "#ffaa00"  # Yellow
    elif percentage < 100:
        return "#00aa00"  # Green
    else:
        return "#0066cc"  # Blue

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to a maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def parse_budget_input(budget_str: str) -> Optional[float]:
    """Parse budget input string to float"""
    if not budget_str:
        return None
    
    # Remove currency symbols and commas
    cleaned = re.sub(r'[$,\s]', '', budget_str)
    
    try:
        return float(cleaned)
    except ValueError:
        return None

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def create_download_link(data: str, filename: str, mime_type: str = "text/plain") -> str:
    """Create a download link for data"""
    import base64
    
    b64 = base64.b64encode(data.encode()).decode()
    return f'<a href="data:{mime_type};base64,{b64}" download="{filename}">Download {filename}</a>'

def save_form_data_to_session(form_data: Dict, step: int = 1):
    """Save form data to session state with metadata"""
    st.session_state.form_data = form_data
    st.session_state.form_step = step
    st.session_state.form_last_saved = datetime.now()

def load_form_data_from_session() -> tuple[Dict, int]:
    """Load form data from session state"""
    form_data = st.session_state.get('form_data', {})
    form_step = st.session_state.get('form_step', 1)
    return form_data, form_step

def get_form_completion_percentage(form_data: Dict) -> float:
    """Calculate form completion percentage based on required fields"""
    required_fields = [
        'client_name', 'event_type', 'event_date', 'location', 
        'total_guests', 'total_budget'
    ]
    
    completed_fields = sum(1 for field in required_fields if form_data.get(field))
    return (completed_fields / len(required_fields)) * 100

def validate_form_section(section_data: Dict, section_number: int) -> tuple[bool, List[str]]:
    """Validate a specific form section"""
    from utils.validators import EventPlanValidator
    
    errors = []
    
    if section_number == 1:
        errors.extend(EventPlanValidator.validate_basic_info(section_data))
    elif section_number == 2:
        errors.extend(EventPlanValidator.validate_guest_info(section_data))
    elif section_number == 3:
        errors.extend(EventPlanValidator.validate_budget_info(section_data))
    else:
        errors.extend(EventPlanValidator.validate_preferences(section_data))
    
    return len(errors) == 0, errors

def format_form_summary(form_data: Dict) -> str:
    """Format form data as a readable summary"""
    summary_lines = []
    
    # Basic info
    if form_data.get('client_name'):
        summary_lines.append(f"Client: {form_data['client_name']}")
    if form_data.get('event_type'):
        summary_lines.append(f"Event Type: {form_data['event_type']}")
    if form_data.get('event_date'):
        summary_lines.append(f"Date: {format_date(form_data['event_date'])}")
    if form_data.get('location'):
        summary_lines.append(f"Location: {form_data['location']}")
    
    # Guest and budget info
    if form_data.get('total_guests'):
        summary_lines.append(f"Guests: {form_data['total_guests']}")
    if form_data.get('total_budget'):
        summary_lines.append(f"Budget: {format_currency(form_data['total_budget'])}")
    
    # Key preferences
    if form_data.get('venue_types'):
        summary_lines.append(f"Venue Types: {', '.join(form_data['venue_types'])}")
    if form_data.get('cuisine_preferences'):
        summary_lines.append(f"Cuisine: {', '.join(form_data['cuisine_preferences'])}")
    
    return '\n'.join(summary_lines)

def export_form_to_json(form_data: Dict) -> str:
    """Export form data to JSON string"""
    import json
    
    export_data = {
        'form_data': form_data,
        'exported_at': datetime.now().isoformat(),
        'version': '1.0',
        'app': 'Event Planning Agent GUI'
    }
    
    return json.dumps(export_data, indent=2, default=str)

def import_form_from_json(json_str: str) -> Optional[Dict]:
    """Import form data from JSON string"""
    import json
    
    try:
        data = json.loads(json_str)
        if 'form_data' in data:
            return data['form_data']
        return data
    except json.JSONDecodeError:
        return None

def get_section_icon(section_number: int) -> str:
    """Get icon for form section"""
    icons = {
        1: "📋",  # Basic Information
        2: "👥",  # Guest Information
        3: "💰",  # Budget & Priorities
        4: "🏛️", # Venue Preferences
        5: "🍽️", # Catering Preferences
        6: "📸",  # Photography & Services
        7: "✨"   # Client Vision & Theme
    }
    return icons.get(section_number, "📄")

def create_form_progress_bar(current_step: int, total_steps: int) -> str:
    """Create a visual progress bar for the form"""
    progress = (current_step - 1) / total_steps
    filled_blocks = int(progress * 20)  # 20 character progress bar
    empty_blocks = 20 - filled_blocks
    
    progress_bar = "█" * filled_blocks + "░" * empty_blocks
    percentage = int(progress * 100)
    
    return f"Progress: [{progress_bar}] {percentage}% (Step {current_step}/{total_steps})"

# ========== Task Progress Tracking Functions ==========

def calculate_task_progress(tasks: List[Dict]) -> Dict[str, Any]:
    """
    Calculate overall task progress metrics.
    
    Args:
        tasks: List of task dictionaries
        
    Returns:
        Dictionary with progress metrics including:
        - total_tasks: Total number of tasks
        - completed_tasks: Number of completed tasks
        - in_progress_tasks: Number of in-progress tasks
        - pending_tasks: Number of pending tasks
        - blocked_tasks: Number of blocked tasks
        - overdue_tasks: Number of overdue tasks
        - completion_percentage: Overall completion percentage
    """
    if not tasks:
        return {
            'total_tasks': 0,
            'completed_tasks': 0,
            'in_progress_tasks': 0,
            'pending_tasks': 0,
            'blocked_tasks': 0,
            'overdue_tasks': 0,
            'completion_percentage': 0.0
        }
    
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task.get('status', '').lower() == 'completed')
    in_progress_tasks = sum(1 for task in tasks if task.get('status', '').lower() == 'in_progress')
    pending_tasks = sum(1 for task in tasks if task.get('status', '').lower() == 'pending')
    blocked_tasks = sum(1 for task in tasks if task.get('status', '').lower() == 'blocked')
    overdue_tasks = sum(1 for task in tasks if task.get('is_overdue', False))
    
    completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
    
    return {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'in_progress_tasks': in_progress_tasks,
        'pending_tasks': pending_tasks,
        'blocked_tasks': blocked_tasks,
        'overdue_tasks': overdue_tasks,
        'completion_percentage': completion_percentage
    }

def calculate_progress_by_priority(tasks: List[Dict]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate task progress grouped by priority level.
    
    Args:
        tasks: List of task dictionaries
        
    Returns:
        Dictionary mapping priority levels to progress metrics
    """
    priorities = ['Critical', 'High', 'Medium', 'Low']
    progress_by_priority = {}
    
    for priority in priorities:
        priority_tasks = [t for t in tasks if t.get('priority', '').lower() == priority.lower()]
        
        if priority_tasks:
            total = len(priority_tasks)
            completed = sum(1 for t in priority_tasks if t.get('status', '').lower() == 'completed')
            in_progress = sum(1 for t in priority_tasks if t.get('status', '').lower() == 'in_progress')
            overdue = sum(1 for t in priority_tasks if t.get('is_overdue', False))
            
            progress_by_priority[priority] = {
                'total': total,
                'completed': completed,
                'in_progress': in_progress,
                'overdue': overdue,
                'completion_percentage': (completed / total * 100) if total > 0 else 0.0
            }
        else:
            progress_by_priority[priority] = {
                'total': 0,
                'completed': 0,
                'in_progress': 0,
                'overdue': 0,
                'completion_percentage': 0.0
            }
    
    return progress_by_priority

def calculate_progress_by_vendor(tasks: List[Dict]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate task progress grouped by assigned vendor.
    
    Args:
        tasks: List of task dictionaries
        
    Returns:
        Dictionary mapping vendor names to progress metrics
    """
    progress_by_vendor = {}
    
    # Group tasks by vendor
    for task in tasks:
        vendor = task.get('assigned_vendor', {})
        vendor_name = vendor.get('name', 'Unassigned')
        
        if vendor_name not in progress_by_vendor:
            progress_by_vendor[vendor_name] = {
                'tasks': [],
                'vendor_type': vendor.get('type', 'N/A')
            }
        
        progress_by_vendor[vendor_name]['tasks'].append(task)
    
    # Calculate metrics for each vendor
    for vendor_name, vendor_data in progress_by_vendor.items():
        vendor_tasks = vendor_data['tasks']
        total = len(vendor_tasks)
        completed = sum(1 for t in vendor_tasks if t.get('status', '').lower() == 'completed')
        in_progress = sum(1 for t in vendor_tasks if t.get('status', '').lower() == 'in_progress')
        overdue = sum(1 for t in vendor_tasks if t.get('is_overdue', False))
        
        vendor_data.update({
            'total': total,
            'completed': completed,
            'in_progress': in_progress,
            'overdue': overdue,
            'completion_percentage': (completed / total * 100) if total > 0 else 0.0
        })
        
        # Remove the tasks list to keep the result clean
        del vendor_data['tasks']
    
    return progress_by_vendor

def get_overdue_tasks(tasks: List[Dict]) -> List[Dict]:
    """
    Get list of overdue tasks with days overdue calculated.
    
    Args:
        tasks: List of task dictionaries
        
    Returns:
        List of overdue tasks with days_overdue field added
    """
    from datetime import datetime, date
    
    overdue_tasks = []
    today = date.today()
    
    for task in tasks:
        if task.get('is_overdue', False):
            # Calculate days overdue
            end_date_str = task.get('end_date')
            days_overdue = 0
            
            if end_date_str:
                try:
                    # Parse end date
                    if isinstance(end_date_str, str):
                        end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00')).date()
                    elif isinstance(end_date_str, datetime):
                        end_date = end_date_str.date()
                    elif isinstance(end_date_str, date):
                        end_date = end_date_str
                    else:
                        end_date = today
                    
                    # Calculate days overdue
                    days_overdue = (today - end_date).days
                except:
                    days_overdue = 0
            
            # Add days_overdue to task
            task_copy = task.copy()
            task_copy['days_overdue'] = days_overdue
            overdue_tasks.append(task_copy)
    
    return overdue_tasks

def get_dependent_tasks(tasks: List[Dict], completed_task_id: str) -> List[Dict]:
    """
    Get tasks that depend on a specific task.
    
    Args:
        tasks: List of all tasks
        completed_task_id: ID of the completed task
        
    Returns:
        List of tasks that have the completed task as a dependency
    """
    dependent_tasks = []
    
    for task in tasks:
        dependencies = task.get('dependencies', [])
        
        # Check if completed_task_id is in dependencies
        for dep in dependencies:
            dep_id = dep.get('task_id') if isinstance(dep, dict) else dep
            if str(dep_id) == str(completed_task_id):
                dependent_tasks.append(task)
                break
    
    return dependent_tasks

def check_prerequisites_complete(task: Dict, all_tasks: List[Dict]) -> bool:
    """
    Check if all prerequisite tasks for a given task are completed.
    
    Args:
        task: Task to check
        all_tasks: List of all tasks
        
    Returns:
        True if all prerequisites are completed, False otherwise
    """
    dependencies = task.get('dependencies', [])
    
    if not dependencies:
        return True
    
    # Create a map of task IDs to tasks for quick lookup
    task_map = {str(t.get('id', t.get('task_id', ''))): t for t in all_tasks}
    
    # Check each dependency
    for dep in dependencies:
        dep_id = str(dep.get('task_id') if isinstance(dep, dict) else dep)
        dep_task = task_map.get(dep_id)
        
        if not dep_task:
            # Dependency not found - assume not complete
            return False
        
        if dep_task.get('status', '').lower() != 'completed':
            return False
    
    return True