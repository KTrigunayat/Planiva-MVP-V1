# Task Management User Guide

This guide covers the Task Management features of the Event Planning Agent v2 Streamlit GUI.

## Overview

The Task Management module helps you organize, track, and manage all tasks required for your event. It provides a comprehensive view of task dependencies, vendor assignments, logistics, and potential conflicts.

## Features

### 1. Extended Task List

The Task List page provides a detailed view of all tasks with hierarchical organization.

#### Accessing the Task List
1. Navigate to **"📋 Tasks"** → **"Task List"** in the sidebar
2. The page will load all tasks for your current event plan

#### Task Information Displayed
Each task card shows:
- **Task Name**: Brief description of the task
- **Priority Level**: Critical, High, Medium, or Low (color-coded)
- **Status**: Pending, In Progress, Completed, or Failed
- **Estimated Duration**: Time required to complete the task
- **Timeline**: Start and end times
- **Vendor Assignment**: Assigned vendor with contact details
- **Dependencies**: Tasks that must be completed first
- **Logistics Status**: Transportation, equipment, and setup requirements
- **Conflicts**: Any scheduling or resource conflicts

#### Filtering and Sorting
- **Filter by Priority**: Show only Critical, High, Medium, or Low priority tasks
- **Filter by Status**: View Pending, In Progress, or Completed tasks
- **Filter by Vendor**: See tasks assigned to specific vendors
- **Sort Options**:
  - By Priority (Critical first)
  - By Start Date (earliest first)
  - By Duration (longest first)
  - By Task Name (alphabetical)

#### Marking Tasks Complete
1. Click the checkbox next to a task to mark it as complete
2. The system will automatically update dependent tasks
3. Progress bars will update to reflect completion

#### Understanding Task Dependencies
- Tasks with dependencies show a "Depends on" section
- Dependent tasks cannot start until prerequisites are complete
- Visual indicators show the dependency chain

### 2. Timeline Visualization

The Timeline page provides an interactive Gantt chart for visual task scheduling.

#### Accessing the Timeline
1. Navigate to **"📋 Tasks"** → **"Timeline"** in the sidebar
2. The Gantt chart will display all tasks on a timeline

#### Timeline Features
- **Color Coding**: Tasks are colored by priority level
  - Red: Critical priority
  - Orange: High priority
  - Yellow: Medium priority
  - Green: Low priority
- **Task Bars**: Show duration and scheduling
- **Dependency Lines**: Connect related tasks
- **Conflict Indicators**: Red borders highlight conflicting tasks
- **Hover Tooltips**: Show detailed task information

#### Zoom Controls
- **Day View**: See hourly breakdown
- **Week View**: See daily breakdown
- **Month View**: See weekly breakdown
- Use the zoom slider to adjust the time scale

#### Filtering Timeline
- Filter by vendor to see specific vendor's tasks
- Filter by priority to focus on critical items
- Filter by task type to group similar tasks

### 3. Conflict Resolution

The Conflicts page helps identify and resolve scheduling and resource conflicts.

#### Types of Conflicts
1. **Timeline Overlap**: Tasks scheduled at the same time that conflict
2. **Resource Conflict**: Same vendor or equipment double-booked
3. **Venue Conflict**: Multiple tasks requiring the same space
4. **Dependency Violation**: Task scheduled before its prerequisites

#### Viewing Conflicts
1. Navigate to **"📋 Tasks"** → **"Conflicts"** in the sidebar
2. Conflicts are displayed with severity indicators:
   - Critical: Must be resolved immediately
   - High: Should be resolved soon
   - Medium: Can be addressed later
   - Low: Minor issues

#### Conflict Information
Each conflict card shows:
- **Conflict Type**: Category of the conflict
- **Severity Level**: How urgent the resolution is
- **Affected Tasks**: Which tasks are involved
- **Description**: Detailed explanation of the issue
- **Suggested Resolution**: Recommended fix from the system

#### Resolving Conflicts
1. Review the suggested resolution
2. Click **"Apply Resolution"** to implement the fix
3. The system will update affected tasks automatically
4. Refresh to see updated conflict status

#### No Conflicts
If no conflicts exist, you'll see a success message confirming all tasks are properly scheduled.

### 4. Vendor Management

The Vendors page provides a vendor-centric view of task assignments.

#### Accessing Vendor Management
1. Navigate to **"📋 Tasks"** → **"Vendors"** in the sidebar
2. View all vendors and their assigned tasks

#### Vendor Information
Each vendor card displays:
- **Vendor Name**: Business name
- **Vendor Type**: Category (caterer, decorator, photographer, etc.)
- **Contact Information**: Email and phone
- **Fitness Score**: How well-suited the vendor is (0-100)
- **Workload Level**: Low, Medium, or High
- **Assigned Tasks**: List of all tasks assigned to this vendor

#### Vendor Workload Distribution
- View a chart showing task distribution across vendors
- Identify overloaded vendors
- See which vendors have capacity for more tasks

#### Filtering Vendors
- Filter by vendor type to see specific categories
- Filter by workload to identify availability
- Search by vendor name

#### Vendor Task Details
Expand each vendor card to see:
- Task priorities and statuses
- Task timelines
- Dependencies affecting the vendor's schedule
- Any conflicts involving the vendor

## Best Practices

### Task Management
1. **Review tasks daily**: Check the task list regularly for updates
2. **Monitor conflicts**: Address conflicts as soon as they appear
3. **Track progress**: Use the progress bars to ensure you're on schedule
4. **Update statuses**: Mark tasks complete promptly to update dependencies

### Timeline Planning
1. **Use the timeline view**: Visualize the entire event schedule
2. **Check for gaps**: Ensure no critical tasks are missing
3. **Verify dependencies**: Confirm tasks are in the correct order
4. **Adjust as needed**: Work with vendors to resolve scheduling issues

### Vendor Coordination
1. **Balance workload**: Ensure no vendor is overloaded
2. **Verify assignments**: Confirm vendors are appropriate for tasks
3. **Maintain contact**: Keep vendor information up to date
4. **Monitor fitness scores**: High scores indicate good vendor-task matches

### Conflict Resolution
1. **Prioritize critical conflicts**: Address high-severity issues first
2. **Review suggestions**: Consider the system's recommended resolutions
3. **Communicate changes**: Inform affected vendors of schedule changes
4. **Verify resolution**: Check that conflicts are truly resolved

## Troubleshooting

### Tasks Not Loading
- Ensure your event plan has been created
- Check that the backend API is running
- Verify your network connection
- Refresh the page

### Timeline Not Displaying
- Ensure tasks have valid start and end times
- Check that the timeline data is available
- Try adjusting the zoom level
- Clear your browser cache

### Conflicts Not Resolving
- Verify the resolution was applied successfully
- Check if new conflicts were created
- Ensure dependent tasks were updated
- Contact support if issues persist

### Vendor Information Missing
- Confirm vendors have been assigned to tasks
- Check that vendor data is complete in the backend
- Verify the API connection
- Refresh the vendor list

## Tips and Tricks

1. **Use filters effectively**: Narrow down large task lists to focus on what matters
2. **Export data**: Use the export feature to share task lists with your team
3. **Monitor progress**: Check the overall completion percentage regularly
4. **Plan ahead**: Use the timeline to identify potential issues early
5. **Stay organized**: Keep task statuses updated for accurate tracking
6. **Communicate**: Share the timeline view with vendors for coordination
7. **Review conflicts daily**: Catch and resolve issues before they become problems
8. **Balance priorities**: Don't let low-priority tasks delay critical ones

## Keyboard Shortcuts

- **Ctrl/Cmd + R**: Refresh current page
- **Ctrl/Cmd + F**: Search/filter tasks
- **Esc**: Close expanded task details
- **Tab**: Navigate between form fields

## Mobile Usage

The Task Management features are fully responsive:
- **Task List**: Displays as cards on mobile devices
- **Timeline**: Horizontal scrolling enabled for small screens
- **Conflicts**: Touch-friendly buttons and controls
- **Vendors**: Collapsible sections for easy navigation

## Support

For additional help:
1. Check the main README.md for general troubleshooting
2. Review the API documentation for backend issues
3. Contact your system administrator for access problems
4. Report bugs through your organization's support channel
