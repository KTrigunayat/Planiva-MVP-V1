# Requirements Document - Streamlit GUI CRM & Task Management Integration

## Introduction

This document outlines the requirements for integrating the CRM Communication Engine and Task Management Agent features into the existing Streamlit GUI for Event Planning Agent v2. The integration will provide users with comprehensive interfaces to manage client communications, view communication analytics, manage task lists, visualize timelines, and resolve conflicts through an intuitive web interface.

The integration builds upon the existing Streamlit GUI (already implemented with pages for home, create_plan, plan_status, plan_results, and plan_blueprint) and adds new pages and components for CRM and Task Management functionality.

## Glossary

- **CRM Communication Engine**: The backend system that manages multi-channel client communications (email, SMS, WhatsApp)
- **Task Management Agent**: The backend system that generates extended task lists with priorities, dependencies, and vendor assignments
- **Streamlit GUI**: The web-based user interface for Event Planning Agent v2
- **Extended Task List**: Comprehensive task list with timeline, vendor assignments, logistics, and conflicts
- **Communication Preferences**: Client settings for preferred communication channels, timezone, and quiet hours

## Requirements

### Requirement 1: CRM Communication Preferences Management

**User Story:** As a client, I want to manage my communication preferences through the Streamlit GUI, so that I receive notifications through my preferred channels at convenient times.

#### Acceptance Criteria

1. WHEN I access the preferences page THEN the system SHALL display my current communication preferences including preferred channels, timezone, and quiet hours
2. WHEN I select preferred channels THEN the system SHALL provide checkboxes for Email, SMS, and WhatsApp with multi-select capability
3. WHEN I set my timezone THEN the system SHALL provide a dropdown with all standard timezones
4. WHEN I configure quiet hours THEN the system SHALL provide time pickers for start and end times
5. WHEN I opt out of a channel THEN the system SHALL provide toggle switches for each communication channel
6. WHEN I save preferences THEN the system SHALL call the POST /api/crm/preferences endpoint and update the crm_client_preferences table
7. IF preference update fails THEN the system SHALL display an error message with retry option

### Requirement 2: Communication History Viewer

**User Story:** As a client, I want to view my communication history in the Streamlit GUI, so that I can track all interactions with the event planning system.

#### Acceptance Criteria

1. WHEN I access the communication history page THEN the system SHALL display all communications for my event plan sorted by date
2. WHEN viewing communications THEN the system SHALL show message type, channel, status, sent time, and delivery status for each communication
3. WHEN I filter communications THEN the system SHALL provide filters for channel (Email, SMS, WhatsApp), status (sent, delivered, opened, failed), and date range
4. WHEN I select a communication THEN the system SHALL display the full message content in an expandable section
5. WHEN viewing email communications THEN the system SHALL show open and click tracking information if available
6. WHEN a communication failed THEN the system SHALL display the error message and retry status
7. IF no communications exist THEN the system SHALL display a message indicating no communication history

### Requirement 3: CRM Analytics Dashboard

**User Story:** As a system administrator, I want to view communication analytics in the Streamlit GUI, so that I can monitor communication effectiveness and identify issues.

#### Acceptance Criteria

1. WHEN I access the analytics dashboard THEN the system SHALL display key metrics including total sent, delivered, opened, clicked, and failed communications
2. WHEN viewing channel performance THEN the system SHALL show delivery rates, open rates, and click-through rates for each channel (Email, SMS, WhatsApp)
3. WHEN analyzing message types THEN the system SHALL display performance metrics grouped by message type (welcome, budget_summary, vendor_options, etc.)
4. WHEN viewing trends THEN the system SHALL provide timeline charts showing communication volume and engagement over time
5. WHEN comparing channels THEN the system SHALL provide side-by-side comparison visualizations
6. WHEN I select a date range THEN the system SHALL filter all analytics data to the specified period
7. WHEN I export data THEN the system SHALL provide CSV download functionality for detailed analysis

### Requirement 4: Extended Task List Viewer

**User Story:** As an event planner, I want to view the extended task list in the Streamlit GUI, so that I can see all tasks with their priorities, timelines, and assignments.

#### Acceptance Criteria

1. WHEN the extended task list is generated THEN the system SHALL display it in a structured, hierarchical view showing parent tasks and sub-tasks
2. WHEN viewing tasks THEN the system SHALL show task name, description, priority level, estimated duration, and status for each task
3. WHEN I expand a task THEN the system SHALL display detailed information including dependencies, assigned vendors, logistics status, and conflicts
4. WHEN I filter tasks THEN the system SHALL provide filters for priority level (Critical, High, Medium, Low), status, and assigned vendor
5. WHEN I sort tasks THEN the system SHALL provide sorting options by priority, start date, duration, and task name
6. WHEN viewing task dependencies THEN the system SHALL display prerequisite tasks and dependent tasks with visual indicators
7. IF a task has errors or warnings THEN the system SHALL highlight it with appropriate visual indicators and display error messages

### Requirement 5: Task Timeline Visualization

**User Story:** As an event planner, I want to visualize the task timeline in the Streamlit GUI, so that I can understand the event schedule and identify potential issues.

#### Acceptance Criteria

1. WHEN I access the timeline view THEN the system SHALL display a Gantt chart showing all tasks with their start dates, end dates, and durations
2. WHEN viewing the timeline THEN the system SHALL use color coding to indicate priority levels (Critical=red, High=orange, Medium=yellow, Low=green)
3. WHEN I hover over a task THEN the system SHALL display a tooltip with task details including name, duration, assigned vendor, and dependencies
4. WHEN viewing dependencies THEN the system SHALL draw connecting lines between dependent tasks
5. WHEN conflicts exist THEN the system SHALL highlight conflicting tasks with visual indicators
6. WHEN I zoom the timeline THEN the system SHALL provide controls to adjust the time scale (day, week, month view)
7. WHEN I filter the timeline THEN the system SHALL allow filtering by vendor, priority, or task type

### Requirement 6: Conflict Resolution Interface

**User Story:** As an event planner, I want to view and resolve conflicts in the Streamlit GUI, so that I can address scheduling and resource conflicts before they become problems.

#### Acceptance Criteria

1. WHEN conflicts are detected THEN the system SHALL display a conflicts panel showing all conflicts with severity levels
2. WHEN viewing a conflict THEN the system SHALL show conflict type (timeline, resource, venue), affected tasks, and conflict description
3. WHEN I select a conflict THEN the system SHALL display suggested resolutions from the Conflict Check Tool
4. WHEN I apply a resolution THEN the system SHALL update the task timeline and mark the conflict as resolved
5. WHEN viewing timeline conflicts THEN the system SHALL highlight overlapping tasks in the timeline visualization
6. WHEN viewing resource conflicts THEN the system SHALL show which resources are double-booked and when
7. IF no conflicts exist THEN the system SHALL display a success message indicating all tasks are conflict-free

### Requirement 7: Vendor Assignment Display

**User Story:** As an event planner, I want to see vendor assignments for each task in the Streamlit GUI, so that I know which vendors are responsible for which activities.

#### Acceptance Criteria

1. WHEN viewing tasks THEN the system SHALL display assigned vendor information including vendor name, type, and contact details
2. WHEN a vendor is assigned THEN the system SHALL show the fitness score and assignment rationale from the Vendor Task Tool
3. WHEN viewing vendor workload THEN the system SHALL provide a vendor-centric view showing all tasks assigned to each vendor
4. WHEN a task requires manual assignment THEN the system SHALL flag it with a visual indicator and provide an assignment interface
5. WHEN I filter by vendor THEN the system SHALL show only tasks assigned to the selected vendor
6. WHEN viewing vendor details THEN the system SHALL provide a link to the full vendor profile from the selected combination
7. IF no vendor is assigned THEN the system SHALL display a message indicating manual assignment is required

### Requirement 8: Logistics Status Display

**User Story:** As an event planner, I want to view logistics status for each task in the Streamlit GUI, so that I can identify and address logistical issues early.

#### Acceptance Criteria

1. WHEN viewing task details THEN the system SHALL display logistics status including transportation, equipment, and setup verification
2. WHEN logistics are verified THEN the system SHALL show green checkmarks for each logistics component
3. WHEN logistics issues exist THEN the system SHALL display warning icons with detailed issue descriptions
4. WHEN viewing transportation status THEN the system SHALL show transportation requirements and availability notes
5. WHEN viewing equipment status THEN the system SHALL show required equipment and availability status
6. WHEN viewing setup requirements THEN the system SHALL show setup time, space requirements, and venue constraints
7. IF logistics data is missing THEN the system SHALL display a message indicating additional information is required

### Requirement 9: Task Management Navigation Integration

**User Story:** As a user, I want seamless navigation between task management features in the Streamlit GUI, so that I can easily access different views and functionalities.

#### Acceptance Criteria

1. WHEN I access the application THEN the system SHALL add new navigation items for "📋 Tasks" and "💬 Communications" in the sidebar
2. WHEN I click "📋 Tasks" THEN the system SHALL display a sub-menu with options for "Task List", "Timeline", "Conflicts", and "Vendors"
3. WHEN I click "💬 Communications" THEN the system SHALL display a sub-menu with options for "Preferences", "History", and "Analytics"
4. WHEN viewing a task THEN the system SHALL provide quick links to related vendors, timeline, and conflicts
5. WHEN viewing communications THEN the system SHALL provide quick links to related event plans and preferences
6. WHEN the extended task list is not yet generated THEN the system SHALL disable task management navigation items
7. WHEN CRM is not configured THEN the system SHALL display a setup message in communication pages

### Requirement 10: Real-Time Updates for Communications

**User Story:** As a client, I want to see real-time updates for communication status in the Streamlit GUI, so that I know when messages are sent, delivered, and opened.

#### Acceptance Criteria

1. WHEN a communication is sent THEN the system SHALL update the communication history view in real-time
2. WHEN a delivery status changes THEN the system SHALL update the status indicator without requiring page refresh
3. WHEN viewing communication history THEN the system SHALL poll the GET /api/crm/communications endpoint every 30 seconds for updates
4. WHEN an email is opened THEN the system SHALL update the opened_at timestamp and increment the open count
5. WHEN a link is clicked THEN the system SHALL update the clicked_at timestamp and increment the click count
6. WHEN a communication fails THEN the system SHALL display a notification with error details
7. IF polling fails THEN the system SHALL display a connection status warning and retry

### Requirement 11: Task Progress Tracking

**User Story:** As an event planner, I want to track task completion progress in the Streamlit GUI, so that I can monitor event preparation status.

#### Acceptance Criteria

1. WHEN viewing the task list THEN the system SHALL display a progress bar showing overall completion percentage
2. WHEN I mark a task as complete THEN the system SHALL update the task status and recalculate the progress percentage
3. WHEN viewing task details THEN the system SHALL provide a checkbox to mark the task as complete
4. WHEN a task is completed THEN the system SHALL update dependent tasks to show they can now begin
5. WHEN viewing progress by priority THEN the system SHALL show completion rates for Critical, High, Medium, and Low priority tasks
6. WHEN viewing progress by vendor THEN the system SHALL show completion rates for each assigned vendor
7. IF a task is overdue THEN the system SHALL highlight it with a red indicator and display the number of days overdue

### Requirement 12: Mobile Responsiveness for New Features

**User Story:** As a user, I want the CRM and Task Management features to work well on mobile devices, so that I can access them from anywhere.

#### Acceptance Criteria

1. WHEN I access CRM features on mobile THEN the system SHALL display responsive layouts that adapt to small screens
2. WHEN I access Task Management features on mobile THEN the system SHALL provide touch-friendly controls and collapsible sections
3. WHEN viewing the timeline on mobile THEN the system SHALL provide horizontal scrolling and pinch-to-zoom functionality
4. WHEN viewing task lists on mobile THEN the system SHALL use card-based layouts that stack vertically
5. WHEN managing preferences on mobile THEN the system SHALL use mobile-optimized form controls
6. WHEN viewing analytics on mobile THEN the system SHALL display charts that resize appropriately for small screens
7. WHEN using navigation on mobile THEN the system SHALL provide a hamburger menu for task and communication sub-menus

### Requirement 13: Error Handling and User Feedback

**User Story:** As a user, I want clear error messages and feedback in the Streamlit GUI, so that I understand what's happening and can take appropriate action.

#### Acceptance Criteria

1. WHEN an API call fails THEN the system SHALL display a user-friendly error message with suggested actions
2. WHEN data is loading THEN the system SHALL display loading spinners or progress indicators
3. WHEN an action succeeds THEN the system SHALL display a success message with confirmation details
4. WHEN validation fails THEN the system SHALL highlight invalid fields and display specific error messages
5. WHEN the backend is unavailable THEN the system SHALL display a connection error message with retry option
6. WHEN data is stale THEN the system SHALL display a warning and provide a refresh button
7. IF an unexpected error occurs THEN the system SHALL log the error and display a generic error message with support contact information

### Requirement 14: Data Export Functionality

**User Story:** As an event planner, I want to export task and communication data from the Streamlit GUI, so that I can share information with stakeholders and perform offline analysis.

#### Acceptance Criteria

1. WHEN viewing the task list THEN the system SHALL provide an "Export Tasks" button that downloads data as CSV
2. WHEN viewing communication history THEN the system SHALL provide an "Export Communications" button that downloads data as CSV
3. WHEN viewing analytics THEN the system SHALL provide an "Export Report" button that generates a PDF report
4. WHEN exporting tasks THEN the CSV SHALL include all task fields including name, priority, timeline, vendor, and status
5. WHEN exporting communications THEN the CSV SHALL include message type, channel, status, timestamps, and delivery metrics
6. WHEN generating PDF reports THEN the system SHALL include charts, tables, and summary statistics
7. IF export fails THEN the system SHALL display an error message and log the failure

### Requirement 15: Integration with Existing Blueprint

**User Story:** As a user, I want the extended task list to be included in the final event blueprint, so that I have a comprehensive document with all planning details.

#### Acceptance Criteria

1. WHEN the blueprint is generated THEN the system SHALL include the extended task list section with all task details
2. WHEN viewing the blueprint THEN the system SHALL display tasks organized by priority and timeline
3. WHEN the blueprint includes tasks THEN it SHALL show vendor assignments, dependencies, and logistics status
4. WHEN conflicts exist THEN the blueprint SHALL include a conflicts section with resolution recommendations
5. WHEN downloading the blueprint THEN the system SHALL include task data in PDF, JSON, and text formats
6. WHEN the extended task list is not available THEN the blueprint SHALL include a message indicating tasks are being generated
7. IF task generation fails THEN the blueprint SHALL include available task data with a note about incomplete information

## Success Criteria

The CRM and Task Management integration will be considered successful when:

1. ✅ Users can manage communication preferences through an intuitive interface
2. ✅ Communication history is viewable with filtering and search capabilities
3. ✅ Analytics dashboard provides actionable insights on communication effectiveness
4. ✅ Extended task list is displayed with hierarchical structure and detailed information
5. ✅ Timeline visualization provides clear view of event schedule with conflict indicators
6. ✅ Conflicts can be viewed and resolved through the interface
7. ✅ Vendor assignments are clearly displayed with workload distribution
8. ✅ Logistics status is visible for all tasks with issue flagging
9. ✅ Navigation between features is seamless and intuitive
10. ✅ Real-time updates keep communication status current
11. ✅ Task progress tracking provides visibility into event preparation
12. ✅ All features work well on mobile devices
13. ✅ Error handling provides clear feedback and recovery options
14. ✅ Data export functionality enables offline analysis and sharing
15. ✅ Extended task list is integrated into the final blueprint

## Out of Scope

The following items are explicitly out of scope for this integration:

- Modifying the CRM Communication Engine backend logic
- Modifying the Task Management Agent backend logic
- Adding new communication channels beyond Email, SMS, WhatsApp
- Implementing task assignment workflow (tasks are auto-assigned by backend)
- Creating custom task templates or task types
- Implementing collaborative editing of tasks
- Adding real-time chat or messaging features
- Implementing advanced project management features (resource leveling, critical path analysis)

## Dependencies

This integration depends on:

1. Existing Streamlit GUI implementation (app.py, pages, components, utils)
2. CRM Communication Engine backend with all endpoints operational
3. Task Management Agent backend with extended task list generation
4. PostgreSQL database with crm_* and task_management_* tables
5. FastAPI backend with CRM and Task Management API endpoints
6. Existing authentication and session management

## Assumptions

1. CRM Communication Engine backend is fully implemented and operational
2. Task Management Agent backend is fully implemented and operational
3. All required API endpoints are available and documented
4. Database schema includes all CRM and Task Management tables
5. Users have appropriate permissions to access CRM and Task Management features
6. The existing Streamlit GUI infrastructure supports adding new pages and components
