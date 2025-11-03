"""
Reusable Task Management UI components for the Streamlit GUI
"""
import streamlit as st
from typing import Dict, List, Optional, Any
from datetime import datetime, date


def priority_badge(priority: str, size: str = "medium") -> str:
    """
    Create a colored badge for task priority.
    
    Args:
        priority: Priority level (Critical, High, Medium, Low)
        size: Badge size (small, medium, large)
        
    Returns:
        HTML string for the priority badge
    """
    priority_lower = priority.lower()
    
    priority_config = {
        'critical': {'color': '#ff4444', 'icon': '🔴', 'label': 'Critical'},
        'high': {'color': '#ff8800', 'icon': '🟠', 'label': 'High'},
        'medium': {'color': '#ffaa00', 'icon': '🟡', 'label': 'Medium'},
        'low': {'color': '#00aa00', 'icon': '🟢', 'label': 'Low'},
    }
    
    size_config = {
        'small': {'font_size': '0.75em', 'padding': '2px 8px'},
        'medium': {'font_size': '0.85em', 'padding': '4px 12px'},
        'large': {'font_size': '1em', 'padding': '6px 16px'},
    }
    
    config = priority_config.get(priority_lower, {'color': '#666666', 'icon': '⚪', 'label': priority.title()})
    size_style = size_config.get(size, size_config['medium'])
    
    return f"""
    <span style="
        background-color: {config['color']};
        color: white;
        padding: {size_style['padding']};
        border-radius: 12px;
        font-size: {size_style['font_size']};
        font-weight: 600;
        display: inline-block;
        white-space: nowrap;
    ">
        {config['icon']} {config['label']}
    </span>
    """


def task_status_badge(status: str) -> str:
    """
    Create a colored badge for task status.
    
    Args:
        status: Task status (pending, in_progress, completed, blocked)
        
    Returns:
        HTML string for the status badge
    """
    status_lower = status.lower()
    
    status_config = {
        'pending': {'color': '#888888', 'icon': '⏸️', 'label': 'Pending'},
        'in_progress': {'color': '#0066cc', 'icon': '▶️', 'label': 'In Progress'},
        'completed': {'color': '#00aa00', 'icon': '✅', 'label': 'Completed'},
        'blocked': {'color': '#ff4444', 'icon': '🚫', 'label': 'Blocked'},
    }
    
    config = status_config.get(status_lower, {'color': '#666666', 'icon': '❓', 'label': status.title()})
    
    return f"""
    <span style="
        background-color: {config['color']};
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85em;
        font-weight: 600;
        display: inline-block;
        white-space: nowrap;
    ">
        {config['icon']} {config['label']}
    </span>
    """


def task_card(task: Dict, show_details: bool = False, on_complete_callback: Optional[callable] = None) -> None:
    """
    Display a task card with details.
    
    Args:
        task: Task dictionary with details
        show_details: Whether to show expanded details
        on_complete_callback: Optional callback function when task is marked complete
    """
    task_id = task.get('id', task.get('task_id', 'unknown'))
    task_name = task.get('name', 'Unnamed Task')
    description = task.get('description', '')
    priority = task.get('priority', 'Medium')
    status = task.get('status', 'Pending')
    estimated_duration = task.get('estimated_duration', 'N/A')
    start_date = task.get('start_date', '')
    end_date = task.get('end_date', '')
    is_overdue = task.get('is_overdue', False)
    
    # Format dates
    date_range = 'Not scheduled'
    if start_date and end_date:
        try:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00')).strftime("%b %d")
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00')).strftime("%b %d, %Y")
            date_range = f"{start} - {end}"
        except:
            date_range = f"{start_date} - {end_date}"
    
    # Overdue indicator
    overdue_html = ''
    if is_overdue:
        days_overdue = task.get('days_overdue', 0)
        overdue_html = f"""
        <div style="margin-top: 8px; padding: 6px 10px; background: #fff3f3; border-left: 3px solid #ff4444; border-radius: 4px;">
            <span style="color: #cc0000; font-size: 0.85em; font-weight: 600;">
                ⚠️ Overdue by {days_overdue} day(s)
            </span>
        </div>
        """
    
    # Details section
    details_html = ''
    if show_details:
        # Dependencies
        dependencies = task.get('dependencies', [])
        dep_html = ''
        if dependencies:
            dep_items = []
            for dep in dependencies:
                dep_name = dep.get('name', dep.get('task_id', 'Unknown'))
                dep_items.append(f'<li style="margin: 4px 0;">{dep_name}</li>')
            dep_html = f"""
            <div style="margin-top: 12px;">
                <div style="font-size: 0.85em; color: #666; font-weight: 600; margin-bottom: 4px;">Dependencies:</div>
                <ul style="margin: 0; padding-left: 20px; font-size: 0.85em; color: #333;">
                    {''.join(dep_items)}
                </ul>
            </div>
            """
        
        # Vendor assignment
        vendor = task.get('assigned_vendor', {})
        vendor_html = ''
        if vendor and vendor.get('name'):
            vendor_html = f"""
            <div style="margin-top: 12px;">
                <div style="font-size: 0.85em; color: #666; font-weight: 600; margin-bottom: 4px;">Assigned Vendor:</div>
                <div style="font-size: 0.9em; color: #333;">
                    {vendor_badge(vendor)}
                </div>
            </div>
            """
        
        # Logistics status
        logistics = task.get('logistics_status', {})
        logistics_html = ''
        if logistics:
            logistics_html = f"""
            <div style="margin-top: 12px;">
                <div style="font-size: 0.85em; color: #666; font-weight: 600; margin-bottom: 4px;">Logistics:</div>
                <div style="font-size: 0.85em;">
                    {logistics_status_indicator(logistics)}
                </div>
            </div>
            """
        
        # Conflicts
        conflicts = task.get('conflicts', [])
        conflict_html = ''
        if conflicts:
            conflict_items = []
            for conflict in conflicts:
                conflict_items.append(conflict_indicator(conflict, inline=True))
            conflict_html = f"""
            <div style="margin-top: 12px;">
                <div style="font-size: 0.85em; color: #666; font-weight: 600; margin-bottom: 4px;">Conflicts:</div>
                <div>
                    {''.join(conflict_items)}
                </div>
            </div>
            """
        
        details_html = f"""
        <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #e0e0e0;">
            {dep_html}
            {vendor_html}
            {logistics_html}
            {conflict_html}
        </div>
        """
    
    # Completion checkbox
    checkbox_html = ''
    if status.lower() != 'completed' and on_complete_callback:
        checkbox_id = f"task_complete_{task_id}"
        checkbox_html = f"""
        <div style="margin-top: 12px;">
            <label style="display: flex; align-items: center; cursor: pointer; font-size: 0.9em;">
                <input type="checkbox" id="{checkbox_id}" style="margin-right: 8px; cursor: pointer;">
                <span style="color: #666;">Mark as complete</span>
            </label>
        </div>
        """
    
    st.markdown(f"""
    <div style="
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 16px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    ">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
            <div style="flex: 1;">
                <div style="font-weight: 600; font-size: 1.1em; color: #333; margin-bottom: 8px;">
                    {task_name}
                </div>
                {f'<div style="font-size: 0.9em; color: #666; margin-bottom: 8px;">{description}</div>' if description else ''}
                <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px;">
                    {priority_badge(priority, 'small')}
                    {task_status_badge(status)}
                </div>
                <div style="font-size: 0.85em; color: #666;">
                    📅 {date_range} • ⏱️ {estimated_duration}
                </div>
            </div>
        </div>
        {overdue_html}
        {details_html}
        {checkbox_html}
    </div>
    """, unsafe_allow_html=True)


def dependency_indicator(dependencies: List[Dict], compact: bool = False) -> str:
    """
    Create a visual indicator for task dependencies.
    
    Args:
        dependencies: List of dependency dictionaries
        compact: Whether to show compact view
        
    Returns:
        HTML string for dependency indicator
    """
    if not dependencies:
        return '<span style="color: #666; font-size: 0.85em;">No dependencies</span>'
    
    count = len(dependencies)
    
    if compact:
        return f"""
        <span style="
            background-color: #0066cc15;
            color: #0066cc;
            padding: 2px 8px;
            border-radius: 8px;
            font-size: 0.75em;
            font-weight: 600;
            display: inline-block;
        ">
            🔗 {count} dep{'' if count == 1 else 's'}
        </span>
        """
    
    dep_items = []
    for dep in dependencies:
        dep_name = dep.get('name', dep.get('task_id', 'Unknown'))
        dep_status = dep.get('status', 'unknown')
        status_icon = '✅' if dep_status.lower() == 'completed' else '⏳'
        dep_items.append(f"""
        <div style="
            padding: 6px 10px;
            background: #f9f9f9;
            border-left: 3px solid #0066cc;
            border-radius: 4px;
            margin: 4px 0;
            font-size: 0.85em;
        ">
            {status_icon} {dep_name}
        </div>
        """)
    
    return f"""
    <div style="margin: 8px 0;">
        <div style="font-size: 0.85em; color: #666; font-weight: 600; margin-bottom: 4px;">
            🔗 Dependencies ({count}):
        </div>
        {''.join(dep_items)}
    </div>
    """


def conflict_indicator(conflict: Dict, inline: bool = False) -> str:
    """
    Create a visual indicator for conflicts.
    
    Args:
        conflict: Conflict dictionary
        inline: Whether to show inline (compact) view
        
    Returns:
        HTML string for conflict indicator
    """
    conflict_type = conflict.get('type', 'Unknown')
    severity = conflict.get('severity', 'Medium')
    description = conflict.get('description', 'No description')
    
    severity_config = {
        'critical': {'color': '#ff4444', 'icon': '🔴'},
        'high': {'color': '#ff8800', 'icon': '🟠'},
        'medium': {'color': '#ffaa00', 'icon': '🟡'},
        'low': {'color': '#00aa00', 'icon': '🟢'},
    }
    
    config = severity_config.get(severity.lower(), {'color': '#666666', 'icon': '⚪'})
    
    if inline:
        return f"""
        <span style="
            background-color: {config['color']}15;
            color: {config['color']};
            padding: 4px 10px;
            border-left: 3px solid {config['color']};
            border-radius: 4px;
            font-size: 0.85em;
            display: inline-block;
            margin: 4px 4px 4px 0;
        ">
            {config['icon']} {conflict_type.replace('_', ' ').title()}
        </span>
        """
    
    return f"""
    <div style="
        background-color: {config['color']}15;
        border-left: 4px solid {config['color']};
        padding: 12px;
        border-radius: 4px;
        margin: 8px 0;
    ">
        <div style="font-weight: 600; color: #333; margin-bottom: 4px;">
            {config['icon']} {conflict_type.replace('_', ' ').title()} - {severity.title()} Severity
        </div>
        <div style="font-size: 0.9em; color: #666;">
            {description}
        </div>
    </div>
    """


def vendor_badge(vendor: Dict, show_details: bool = False) -> str:
    """
    Create a badge for vendor assignment.
    
    Args:
        vendor: Vendor dictionary with details
        show_details: Whether to show detailed information
        
    Returns:
        HTML string for vendor badge
    """
    vendor_name = vendor.get('name', 'Unassigned')
    vendor_type = vendor.get('type', 'N/A')
    fitness_score = vendor.get('fitness_score', 0)
    
    if vendor_name == 'Unassigned' or not vendor_name:
        return """
        <span style="
            background-color: #f0f0f0;
            color: #666;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
            display: inline-block;
        ">
            ⚠️ Manual Assignment Required
        </span>
        """
    
    # Color based on fitness score
    if fitness_score >= 80:
        color = '#00aa00'
    elif fitness_score >= 60:
        color = '#ffaa00'
    else:
        color = '#ff8800'
    
    details_html = ''
    if show_details:
        contact = vendor.get('contact', {})
        phone = contact.get('phone', 'N/A')
        email = contact.get('email', 'N/A')
        rationale = vendor.get('assignment_rationale', 'N/A')
        
        details_html = f"""
        <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #e0e0e0; font-size: 0.85em;">
            <div style="margin: 4px 0;"><strong>Type:</strong> {vendor_type}</div>
            <div style="margin: 4px 0;"><strong>Phone:</strong> {phone}</div>
            <div style="margin: 4px 0;"><strong>Email:</strong> {email}</div>
            <div style="margin: 4px 0;"><strong>Fitness Score:</strong> {fitness_score}/100</div>
            <div style="margin: 4px 0;"><strong>Rationale:</strong> {rationale}</div>
        </div>
        """
    
    return f"""
    <div style="
        background: linear-gradient(135deg, {color}15 0%, {color}05 100%);
        border-left: 3px solid {color};
        padding: 10px 14px;
        border-radius: 6px;
        display: inline-block;
    ">
        <div style="font-weight: 600; color: #333; font-size: 0.95em;">
            👤 {vendor_name}
        </div>
        <div style="font-size: 0.8em; color: #666; margin-top: 2px;">
            {vendor_type} • Score: {fitness_score}/100
        </div>
        {details_html}
    </div>
    """


def logistics_status_indicator(logistics: Dict) -> str:
    """
    Create a visual indicator for logistics status.
    
    Args:
        logistics: Logistics status dictionary
        
    Returns:
        HTML string for logistics indicator
    """
    transportation = logistics.get('transportation', {})
    equipment = logistics.get('equipment', {})
    setup = logistics.get('setup', {})
    
    def status_icon(verified: bool, has_issues: bool = False) -> str:
        if verified and not has_issues:
            return '<span style="color: #00aa00;">✅</span>'
        elif has_issues:
            return '<span style="color: #ff4444;">⚠️</span>'
        else:
            return '<span style="color: #888;">⏳</span>'
    
    transport_verified = transportation.get('verified', False)
    transport_issues = transportation.get('issues', '')
    
    equipment_verified = equipment.get('verified', False)
    equipment_issues = equipment.get('issues', '')
    
    setup_verified = setup.get('verified', False)
    setup_issues = setup.get('issues', '')
    
    return f"""
    <div style="font-size: 0.9em;">
        <div style="margin: 6px 0; display: flex; align-items: center;">
            {status_icon(transport_verified, bool(transport_issues))}
            <span style="margin-left: 8px; color: #333;">
                <strong>Transportation:</strong> {transportation.get('notes', 'Not specified')}
            </span>
        </div>
        {f'<div style="margin-left: 28px; font-size: 0.85em; color: #cc0000;">{transport_issues}</div>' if transport_issues else ''}
        
        <div style="margin: 6px 0; display: flex; align-items: center;">
            {status_icon(equipment_verified, bool(equipment_issues))}
            <span style="margin-left: 8px; color: #333;">
                <strong>Equipment:</strong> {equipment.get('notes', 'Not specified')}
            </span>
        </div>
        {f'<div style="margin-left: 28px; font-size: 0.85em; color: #cc0000;">{equipment_issues}</div>' if equipment_issues else ''}
        
        <div style="margin: 6px 0; display: flex; align-items: center;">
            {status_icon(setup_verified, bool(setup_issues))}
            <span style="margin-left: 8px; color: #333;">
                <strong>Setup:</strong> {setup.get('time', 'Not specified')} • {setup.get('space', 'Not specified')}
            </span>
        </div>
        {f'<div style="margin-left: 28px; font-size: 0.85em; color: #cc0000;">{setup_issues}</div>' if setup_issues else ''}
    </div>
    """


def progress_bar(percentage: float, label: Optional[str] = None, show_percentage: bool = True,
                 height: str = "24px", color: Optional[str] = None) -> None:
    """
    Display a progress bar.
    
    Args:
        percentage: Progress percentage (0-100)
        label: Optional label text
        show_percentage: Whether to show percentage text
        height: Bar height
        color: Optional custom color (auto-calculated if not provided)
    """
    # Auto-calculate color based on percentage if not provided
    if color is None:
        if percentage < 25:
            color = '#ff4444'
        elif percentage < 50:
            color = '#ff8800'
        elif percentage < 75:
            color = '#ffaa00'
        elif percentage < 100:
            color = '#00aa00'
        else:
            color = '#0066cc'
    
    label_html = f'<div style="font-size: 0.9em; color: #666; margin-bottom: 6px; font-weight: 500;">{label}</div>' if label else ''
    percentage_text = f'{percentage:.1f}%' if show_percentage else ''
    
    st.markdown(f"""
    <div style="margin: 12px 0;">
        {label_html}
        <div style="position: relative; background: #f0f0f0; height: {height}; border-radius: 12px; overflow: hidden;">
            <div style="
                background: linear-gradient(90deg, {color} 0%, {color}dd 100%);
                height: 100%;
                width: {percentage}%;
                transition: width 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: flex-end;
                padding-right: 12px;
            ">
                {f'<span style="color: white; font-weight: 600; font-size: 0.85em;">{percentage_text}</span>' if show_percentage and percentage > 10 else ''}
            </div>
            {f'<span style="position: absolute; right: 12px; top: 50%; transform: translateY(-50%); color: #666; font-weight: 600; font-size: 0.85em;">{percentage_text}</span>' if show_percentage and percentage <= 10 else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)


def timeline_legend() -> None:
    """Display a legend for timeline/Gantt chart colors."""
    st.markdown("""
    <div style="
        display: flex;
        gap: 16px;
        flex-wrap: wrap;
        padding: 12px;
        background: #f9f9f9;
        border-radius: 8px;
        margin: 12px 0;
    ">
        <div style="display: flex; align-items: center; gap: 6px;">
            <div style="width: 16px; height: 16px; background: #ff4444; border-radius: 3px;"></div>
            <span style="font-size: 0.85em; color: #666;">Critical</span>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
            <div style="width: 16px; height: 16px; background: #ff8800; border-radius: 3px;"></div>
            <span style="font-size: 0.85em; color: #666;">High</span>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
            <div style="width: 16px; height: 16px; background: #ffaa00; border-radius: 3px;"></div>
            <span style="font-size: 0.85em; color: #666;">Medium</span>
        </div>
        <div style="display: flex; align-items: center; gap: 6px;">
            <div style="width: 16px; height: 16px; background: #00aa00; border-radius: 3px;"></div>
            <span style="font-size: 0.85em; color: #666;">Low</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def task_summary_metrics(tasks: List[Dict]) -> None:
    """
    Display summary metrics for a list of tasks.
    
    Args:
        tasks: List of task dictionaries
    """
    from utils.helpers import calculate_task_progress
    
    metrics = calculate_task_progress(tasks)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="text-align: center; padding: 16px; background: #f9f9f9; border-radius: 8px;">
            <div style="font-size: 2em; font-weight: 700; color: #333;">{metrics['total_tasks']}</div>
            <div style="font-size: 0.85em; color: #666; margin-top: 4px;">Total Tasks</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 16px; background: #e6f7e6; border-radius: 8px;">
            <div style="font-size: 2em; font-weight: 700; color: #00aa00;">{metrics['completed_tasks']}</div>
            <div style="font-size: 0.85em; color: #666; margin-top: 4px;">Completed</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="text-align: center; padding: 16px; background: #e6f0ff; border-radius: 8px;">
            <div style="font-size: 2em; font-weight: 700; color: #0066cc;">{metrics['in_progress_tasks']}</div>
            <div style="font-size: 0.85em; color: #666; margin-top: 4px;">In Progress</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="text-align: center; padding: 16px; background: #ffe6e6; border-radius: 8px;">
            <div style="font-size: 2em; font-weight: 700; color: #ff4444;">{metrics['overdue_tasks']}</div>
            <div style="font-size: 0.85em; color: #666; margin-top: 4px;">Overdue</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Overall progress bar
    progress_bar(
        metrics['completion_percentage'],
        label="Overall Progress",
        show_percentage=True,
        height="32px"
    )
