"""
CSS styles for the Streamlit GUI components
"""

# CSS for results display components
RESULTS_CSS = """
<style>
    /* Combination card styling */
    .combination-card {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .combination-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
        border-color: #007bff;
    }
    
    .combination-card.selected {
        border-color: #28a745;
        background: linear-gradient(135deg, #f8fff9 0%, #e8f5e9 100%);
    }
    
    /* Fitness score styling */
    .fitness-score {
        font-size: 2rem;
        font-weight: bold;
        color: #28a745;
        text-align: center;
    }
    
    .fitness-score.excellent {
        color: #28a745;
    }
    
    .fitness-score.good {
        color: #ffc107;
    }
    
    .fitness-score.fair {
        color: #fd7e14;
    }
    
    .fitness-score.poor {
        color: #dc3545;
    }
    
    /* Cost display styling */
    .cost-display {
        font-size: 1.5rem;
        font-weight: bold;
        color: #007bff;
        text-align: center;
    }
    
    /* Vendor info styling */
    .vendor-info {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .vendor-name {
        font-weight: bold;
        color: #495057;
        margin-bottom: 0.25rem;
    }
    
    .vendor-details {
        font-size: 0.9rem;
        color: #6c757d;
    }
    
    /* Comparison table styling */
    .comparison-table {
        border-collapse: collapse;
        width: 100%;
        margin: 1rem 0;
    }
    
    .comparison-table th,
    .comparison-table td {
        border: 1px solid #dee2e6;
        padding: 0.75rem;
        text-align: left;
    }
    
    .comparison-table th {
        background-color: #e9ecef;
        font-weight: bold;
    }
    
    .comparison-table tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    .comparison-table tr:hover {
        background-color: #e3f2fd;
    }
    
    /* Plan management styling */
    .plan-card {
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: #ffffff;
        transition: all 0.2s ease;
    }
    
    .plan-card:hover {
        border-color: #007bff;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .plan-status {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
        text-transform: uppercase;
    }
    
    .plan-status.completed {
        background-color: #d4edda;
        color: #155724;
    }
    
    .plan-status.in-progress {
        background-color: #cce7ff;
        color: #004085;
    }
    
    .plan-status.pending {
        background-color: #fff3cd;
        color: #856404;
    }
    
    .plan-status.failed {
        background-color: #f8d7da;
        color: #721c24;
    }
    
    .plan-status.cancelled {
        background-color: #e2e3e5;
        color: #383d41;
    }
    
    /* Action buttons */
    .action-button {
        margin: 0.25rem;
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        font-weight: bold;
        transition: all 0.2s ease;
    }
    
    .action-button.primary {
        background-color: #007bff;
        color: white;
    }
    
    .action-button.primary:hover {
        background-color: #0056b3;
    }
    
    .action-button.success {
        background-color: #28a745;
        color: white;
    }
    
    .action-button.success:hover {
        background-color: #1e7e34;
    }
    
    .action-button.danger {
        background-color: #dc3545;
        color: white;
    }
    
    .action-button.danger:hover {
        background-color: #c82333;
    }
    
    /* Loading animations */
    .loading-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #007bff;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Responsive design */
    @media (max-width: 1200px) {
        .combination-card {
            margin-bottom: 1.5rem;
        }
        
        .comparison-table {
            font-size: 0.9rem;
        }
    }
    
    @media (max-width: 992px) {
        .combination-card {
            padding: 1.25rem;
        }
        
        .vendor-info {
            padding: 0.75rem;
        }
        
        .comparison-table th,
        .comparison-table td {
            padding: 0.5rem;
        }
    }
    
    @media (max-width: 768px) {
        .combination-card {
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .fitness-score {
            font-size: 1.5rem;
        }
        
        .cost-display {
            font-size: 1.2rem;
        }
        
        .vendor-info {
            padding: 0.5rem;
            margin: 0.25rem 0;
        }
        
        .vendor-name {
            font-size: 0.95rem;
        }
        
        .vendor-details {
            font-size: 0.85rem;
        }
        
        .comparison-table {
            font-size: 0.8rem;
            display: block;
            overflow-x: auto;
            white-space: nowrap;
        }
        
        .action-button {
            padding: 0.4rem 0.8rem;
            font-size: 0.9rem;
            margin: 0.2rem;
        }
        
        .plan-card {
            padding: 0.75rem;
        }
    }
    
    @media (max-width: 576px) {
        .combination-card {
            padding: 0.75rem;
            border-radius: 8px;
        }
        
        .fitness-score {
            font-size: 1.25rem;
        }
        
        .cost-display {
            font-size: 1rem;
        }
        
        .vendor-info {
            padding: 0.4rem;
        }
        
        .vendor-name {
            font-size: 0.9rem;
        }
        
        .vendor-details {
            font-size: 0.8rem;
        }
        
        .action-button {
            padding: 0.3rem 0.6rem;
            font-size: 0.85rem;
            display: block;
            width: 100%;
            margin: 0.2rem 0;
        }
        
        .plan-card {
            padding: 0.5rem;
        }
        
        .plan-status {
            font-size: 0.75rem;
            padding: 0.2rem 0.4rem;
        }
        
        .form-section {
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .form-section-title {
            font-size: 1.1rem;
        }
        
        .progress-container {
            padding: 0.75rem;
        }
    }
    
    /* Container responsive utilities */
    .responsive-container {
        max-width: 100%;
        margin: 0 auto;
        padding: 0 1rem;
    }
    
    @media (min-width: 576px) {
        .responsive-container {
            max-width: 540px;
        }
    }
    
    @media (min-width: 768px) {
        .responsive-container {
            max-width: 720px;
        }
    }
    
    @media (min-width: 992px) {
        .responsive-container {
            max-width: 960px;
        }
    }
    
    @media (min-width: 1200px) {
        .responsive-container {
            max-width: 1140px;
        }
    }
    
    /* Mobile-first grid system */
    .row {
        display: flex;
        flex-wrap: wrap;
        margin: 0 -0.5rem;
    }
    
    .col {
        flex: 1;
        padding: 0 0.5rem;
        min-width: 0;
    }
    
    .col-12 { flex: 0 0 100%; max-width: 100%; }
    .col-6 { flex: 0 0 50%; max-width: 50%; }
    .col-4 { flex: 0 0 33.333333%; max-width: 33.333333%; }
    .col-3 { flex: 0 0 25%; max-width: 25%; }
    
    @media (max-width: 768px) {
        .col-md-12 { flex: 0 0 100%; max-width: 100%; }
        .col-6, .col-4, .col-3 {
            flex: 0 0 100%;
            max-width: 100%;
        }
    }
    
    /* Touch-friendly interactions */
    @media (hover: none) and (pointer: coarse) {
        .combination-card:hover {
            transform: none;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .action-button {
            min-height: 44px;
            min-width: 44px;
        }
        
        .plan-card:hover {
            box-shadow: none;
        }
    }
    
    /* Utility classes */
    .text-center {
        text-align: center;
    }
    
    .text-muted {
        color: #6c757d;
    }
    
    .mb-1 {
        margin-bottom: 0.25rem;
    }
    
    .mb-2 {
        margin-bottom: 0.5rem;
    }
    
    .mb-3 {
        margin-bottom: 1rem;
    }
    
    .mt-1 {
        margin-top: 0.25rem;
    }
    
    .mt-2 {
        margin-top: 0.5rem;
    }
    
    .mt-3 {
        margin-top: 1rem;
    }
</style>
"""

# CSS for form components
FORM_CSS = """
<style>
    /* Form section styling */
    .form-section {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .form-section-header {
        border-bottom: 2px solid #007bff;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .form-section-title {
        font-size: 1.25rem;
        font-weight: bold;
        color: #495057;
        margin: 0;
    }
    
    .form-section-description {
        font-size: 0.9rem;
        color: #6c757d;
        margin-top: 0.25rem;
    }
    
    /* Progress indicator */
    .progress-container {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1.5rem;
    }
    
    .progress-bar {
        background-color: #e9ecef;
        border-radius: 4px;
        height: 8px;
        overflow: hidden;
        margin-bottom: 0.5rem;
    }
    
    .progress-fill {
        background-color: #007bff;
        height: 100%;
        transition: width 0.3s ease;
    }
    
    .progress-text {
        font-size: 0.9rem;
        color: #495057;
        text-align: center;
    }
</style>
"""

def get_fitness_score_class(score: float) -> str:
    """Get CSS class based on fitness score"""
    if score >= 90:
        return "excellent"
    elif score >= 75:
        return "good"
    elif score >= 60:
        return "fair"
    else:
        return "poor"

def get_plan_status_class(status: str) -> str:
    """Get CSS class based on plan status"""
    status_classes = {
        "completed": "completed",
        "in_progress": "in-progress", 
        "pending": "pending",
        "failed": "failed",
        "cancelled": "cancelled"
    }
    return status_classes.get(status.lower(), "pending")


# CSS for CRM pages (mobile-responsive)
CRM_CSS = """
<style>
    /* CRM Preferences Page */
    .crm-preferences-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 1rem;
    }
    
    .preference-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .preference-header {
        font-size: 1.25rem;
        font-weight: bold;
        color: #495057;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .channel-option {
        display: flex;
        align-items: center;
        padding: 1rem;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        margin-bottom: 0.75rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .channel-option:hover {
        border-color: #007bff;
        background-color: #f8f9fa;
    }
    
    .channel-option.selected {
        border-color: #28a745;
        background-color: #e8f5e9;
    }
    
    .channel-icon {
        font-size: 1.5rem;
        margin-right: 1rem;
    }
    
    /* Communication History Page */
    .comm-history-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 1rem;
    }
    
    .comm-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        transition: all 0.2s ease;
    }
    
    .comm-card:hover {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        border-color: #007bff;
    }
    
    .comm-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    
    .comm-status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: bold;
        text-transform: uppercase;
    }
    
    .comm-status-badge.sent {
        background-color: #fff3cd;
        color: #856404;
    }
    
    .comm-status-badge.delivered {
        background-color: #d4edda;
        color: #155724;
    }
    
    .comm-status-badge.opened {
        background-color: #cce7ff;
        color: #004085;
    }
    
    .comm-status-badge.clicked {
        background-color: #e7d4ff;
        color: #4a0085;
    }
    
    .comm-status-badge.failed {
        background-color: #f8d7da;
        color: #721c24;
    }
    
    .comm-status-badge.pending {
        background-color: #e2e3e5;
        color: #383d41;
    }
    
    .comm-details {
        font-size: 0.9rem;
        color: #6c757d;
        line-height: 1.6;
    }
    
    /* CRM Analytics Page */
    .analytics-container {
        max-width: 1600px;
        margin: 0 auto;
        padding: 1rem;
    }
    
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #007bff;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .chart-container {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    /* Mobile Responsive - CRM Pages */
    @media (max-width: 768px) {
        .crm-preferences-container,
        .comm-history-container,
        .analytics-container {
            padding: 0.5rem;
        }
        
        .preference-card,
        .comm-card,
        .chart-container {
            padding: 1rem;
            border-radius: 8px;
        }
        
        .preference-header {
            font-size: 1.1rem;
        }
        
        .channel-option {
            padding: 0.75rem;
            margin-bottom: 0.5rem;
        }
        
        .channel-icon {
            font-size: 1.25rem;
            margin-right: 0.75rem;
        }
        
        .comm-header {
            flex-direction: column;
            align-items: flex-start;
        }
        
        .comm-status-badge {
            font-size: 0.75rem;
            padding: 0.2rem 0.6rem;
        }
        
        .metrics-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
        }
        
        .metric-card {
            padding: 1rem;
        }
        
        .metric-value {
            font-size: 1.75rem;
        }
        
        .metric-label {
            font-size: 0.8rem;
        }
    }
    
    @media (max-width: 576px) {
        .metrics-grid {
            grid-template-columns: 1fr;
        }
        
        .preference-card,
        .comm-card {
            padding: 0.75rem;
        }
        
        .channel-option {
            padding: 0.5rem;
        }
        
        .metric-card {
            padding: 0.75rem;
        }
        
        .metric-value {
            font-size: 1.5rem;
        }
    }
</style>
"""


# CSS for Task Management pages (mobile-responsive)
TASK_MANAGEMENT_CSS = """
<style>
    /* Task List Page */
    .task-list-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 1rem;
    }
    
    .task-card {
        background-color: #ffffff;
        border-left: 4px solid #007bff;
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease;
    }
    
    .task-card:hover {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        transform: translateX(2px);
    }
    
    .task-card.priority-critical {
        border-left-color: #dc3545;
    }
    
    .task-card.priority-high {
        border-left-color: #fd7e14;
    }
    
    .task-card.priority-medium {
        border-left-color: #ffc107;
    }
    
    .task-card.priority-low {
        border-left-color: #28a745;
    }
    
    .task-card.completed {
        opacity: 0.7;
        background-color: #f8f9fa;
    }
    
    .task-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 0.75rem;
        gap: 1rem;
    }
    
    .task-title {
        font-size: 1.1rem;
        font-weight: bold;
        color: #495057;
        flex: 1;
    }
    
    .task-priority-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: bold;
        text-transform: uppercase;
        white-space: nowrap;
    }
    
    .task-priority-badge.critical {
        background-color: #f8d7da;
        color: #721c24;
    }
    
    .task-priority-badge.high {
        background-color: #fff3cd;
        color: #856404;
    }
    
    .task-priority-badge.medium {
        background-color: #fff8e1;
        color: #f57c00;
    }
    
    .task-priority-badge.low {
        background-color: #d4edda;
        color: #155724;
    }
    
    .task-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        font-size: 0.9rem;
        color: #6c757d;
        margin-bottom: 0.75rem;
    }
    
    .task-meta-item {
        display: flex;
        align-items: center;
        gap: 0.25rem;
    }
    
    .task-description {
        font-size: 0.95rem;
        color: #495057;
        line-height: 1.6;
        margin-bottom: 0.75rem;
    }
    
    .task-details-section {
        background-color: #f8f9fa;
        border-radius: 6px;
        padding: 1rem;
        margin-top: 0.75rem;
    }
    
    .task-dependency {
        display: inline-block;
        background-color: #e9ecef;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.85rem;
        margin: 0.25rem;
    }
    
    .task-vendor-info {
        background-color: #e7f3ff;
        border-left: 3px solid #007bff;
        padding: 0.75rem;
        border-radius: 4px;
        margin-top: 0.5rem;
    }
    
    .task-logistics-status {
        display: flex;
        gap: 1rem;
        margin-top: 0.5rem;
        flex-wrap: wrap;
    }
    
    .logistics-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.9rem;
    }
    
    .logistics-item.verified {
        color: #28a745;
    }
    
    .logistics-item.issue {
        color: #dc3545;
    }
    
    /* Timeline Visualization */
    .timeline-container {
        max-width: 100%;
        margin: 0 auto;
        padding: 1rem;
        overflow-x: auto;
    }
    
    .timeline-controls {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
        align-items: center;
    }
    
    .timeline-zoom-controls {
        display: flex;
        gap: 0.5rem;
    }
    
    .timeline-zoom-btn {
        padding: 0.5rem 1rem;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        background-color: #ffffff;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .timeline-zoom-btn:hover {
        background-color: #007bff;
        color: #ffffff;
        border-color: #007bff;
    }
    
    .timeline-zoom-btn.active {
        background-color: #007bff;
        color: #ffffff;
        border-color: #007bff;
    }
    
    .gantt-chart-wrapper {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        min-height: 400px;
        overflow-x: auto;
        overflow-y: auto;
    }
    
    /* Conflicts Page */
    .conflicts-container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 1rem;
    }
    
    .conflict-card {
        background-color: #ffffff;
        border: 2px solid #dc3545;
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(220, 53, 69, 0.1);
    }
    
    .conflict-card.severity-critical {
        border-color: #dc3545;
        background-color: #fff5f5;
    }
    
    .conflict-card.severity-high {
        border-color: #fd7e14;
        background-color: #fff8f0;
    }
    
    .conflict-card.severity-medium {
        border-color: #ffc107;
        background-color: #fffbf0;
    }
    
    .conflict-card.severity-low {
        border-color: #17a2b8;
        background-color: #f0f9ff;
    }
    
    .conflict-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    
    .conflict-type {
        font-size: 1.1rem;
        font-weight: bold;
        color: #495057;
    }
    
    .conflict-severity-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: bold;
        text-transform: uppercase;
    }
    
    .conflict-severity-badge.critical {
        background-color: #dc3545;
        color: #ffffff;
    }
    
    .conflict-severity-badge.high {
        background-color: #fd7e14;
        color: #ffffff;
    }
    
    .conflict-severity-badge.medium {
        background-color: #ffc107;
        color: #000000;
    }
    
    .conflict-severity-badge.low {
        background-color: #17a2b8;
        color: #ffffff;
    }
    
    .conflict-description {
        font-size: 0.95rem;
        color: #495057;
        margin-bottom: 1rem;
        line-height: 1.6;
    }
    
    .conflict-affected-tasks {
        background-color: #f8f9fa;
        border-radius: 6px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .conflict-resolution {
        background-color: #e8f5e9;
        border-left: 3px solid #28a745;
        padding: 1rem;
        border-radius: 4px;
    }
    
    .resolution-option {
        padding: 0.75rem;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        margin-bottom: 0.5rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .resolution-option:hover {
        background-color: #f8f9fa;
        border-color: #007bff;
    }
    
    .resolution-option.selected {
        background-color: #e7f3ff;
        border-color: #007bff;
    }
    
    .no-conflicts-message {
        text-align: center;
        padding: 3rem 1rem;
        background-color: #d4edda;
        border-radius: 12px;
        color: #155724;
    }
    
    .no-conflicts-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
    }
    
    /* Progress Tracking */
    .progress-overview {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #ffffff;
        border-radius: 12px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    .progress-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1.5rem;
        margin-top: 1.5rem;
    }
    
    .progress-stat {
        text-align: center;
    }
    
    .progress-stat-value {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.25rem;
    }
    
    .progress-stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Mobile Responsive - Task Management Pages */
    @media (max-width: 992px) {
        .timeline-controls {
            flex-direction: column;
            align-items: stretch;
        }
        
        .timeline-zoom-controls {
            justify-content: center;
        }
        
        .gantt-chart-wrapper {
            padding: 0.75rem;
        }
    }
    
    @media (max-width: 768px) {
        .task-list-container,
        .timeline-container,
        .conflicts-container {
            padding: 0.5rem;
        }
        
        .task-card,
        .conflict-card {
            padding: 1rem;
            border-radius: 6px;
        }
        
        .task-header,
        .conflict-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.5rem;
        }
        
        .task-title,
        .conflict-type {
            font-size: 1rem;
        }
        
        .task-meta {
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .task-details-section,
        .conflict-affected-tasks,
        .conflict-resolution {
            padding: 0.75rem;
        }
        
        .task-vendor-info {
            padding: 0.5rem;
        }
        
        .task-logistics-status {
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .progress-overview {
            padding: 1.5rem;
        }
        
        .progress-stats {
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
        }
        
        .progress-stat-value {
            font-size: 1.5rem;
        }
        
        .timeline-zoom-btn {
            padding: 0.4rem 0.8rem;
            font-size: 0.9rem;
        }
        
        .gantt-chart-wrapper {
            padding: 0.5rem;
            min-height: 300px;
        }
        
        /* Card-based layout for mobile */
        .task-card {
            border-left-width: 3px;
        }
        
        .conflict-card {
            border-width: 1px;
            border-left-width: 4px;
        }
    }
    
    @media (max-width: 576px) {
        .task-card,
        .conflict-card {
            padding: 0.75rem;
        }
        
        .task-priority-badge,
        .conflict-severity-badge {
            font-size: 0.7rem;
            padding: 0.2rem 0.6rem;
        }
        
        .task-description,
        .conflict-description {
            font-size: 0.9rem;
        }
        
        .progress-overview {
            padding: 1rem;
        }
        
        .progress-stats {
            grid-template-columns: 1fr;
            gap: 0.75rem;
        }
        
        .progress-stat-value {
            font-size: 1.25rem;
        }
        
        .progress-stat-label {
            font-size: 0.85rem;
        }
        
        .timeline-zoom-controls {
            flex-wrap: wrap;
        }
        
        .timeline-zoom-btn {
            flex: 1;
            min-width: 80px;
        }
        
        .no-conflicts-icon {
            font-size: 3rem;
        }
    }
    
    /* Touch-friendly controls for mobile */
    @media (hover: none) and (pointer: coarse) {
        .task-card,
        .conflict-card,
        .resolution-option {
            min-height: 44px;
        }
        
        .timeline-zoom-btn {
            min-height: 44px;
            min-width: 44px;
        }
        
        .task-card:hover,
        .conflict-card:hover {
            transform: none;
        }
        
        /* Larger touch targets */
        .task-priority-badge,
        .conflict-severity-badge {
            padding: 0.4rem 0.8rem;
            font-size: 0.8rem;
        }
    }
    
    /* Horizontal scrolling for timeline on mobile */
    @media (max-width: 768px) {
        .gantt-chart-wrapper {
            -webkit-overflow-scrolling: touch;
            scroll-behavior: smooth;
        }
        
        .gantt-chart-wrapper::-webkit-scrollbar {
            height: 8px;
        }
        
        .gantt-chart-wrapper::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 4px;
        }
        
        .gantt-chart-wrapper::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 4px;
        }
        
        .gantt-chart-wrapper::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
    }
    
    /* Collapsible sections for mobile */
    .collapsible-section {
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        margin-bottom: 0.75rem;
        overflow: hidden;
    }
    
    .collapsible-header {
        background-color: #f8f9fa;
        padding: 0.75rem 1rem;
        cursor: pointer;
        display: flex;
        justify-content: space-between;
        align-items: center;
        user-select: none;
    }
    
    .collapsible-header:hover {
        background-color: #e9ecef;
    }
    
    .collapsible-content {
        padding: 1rem;
        background-color: #ffffff;
    }
    
    .collapsible-icon {
        transition: transform 0.2s ease;
    }
    
    .collapsible-icon.expanded {
        transform: rotate(180deg);
    }
    
    @media (max-width: 768px) {
        .collapsible-header {
            padding: 0.6rem 0.75rem;
            font-size: 0.95rem;
        }
        
        .collapsible-content {
            padding: 0.75rem;
        }
    }
</style>
"""