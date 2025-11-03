"""
Main Streamlit application for Event Planning Agent v2 GUI
"""
import streamlit as st
from datetime import datetime
import sys
import os

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.config import config
from utils.helpers import init_session_state, show_error, show_info
from utils.performance import perf_monitor, LoadingSpinner, MemoryOptimizer
from components.health_monitor import health_monitor
from components.mobile_nav import render_mobile_hamburger_menu
from components.styles import CRM_CSS, TASK_MANAGEMENT_CSS
from components.performance_dashboard import render_performance_toggle, render_performance_dashboard, render_performance_badge

# Configure Streamlit page
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS for responsive design and better styling
st.markdown("""
<style>
    /* Main layout improvements */
    .main-header {
        padding: 1rem 0;
        border-bottom: 2px solid #f0f2f6;
        margin-bottom: 2rem;
    }
    
    .status-widget {
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .nav-button {
        width: 100%;
        margin-bottom: 0.5rem;
    }
    
    .progress-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    .error-container {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
    }
    
    .success-container {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
    
    /* Responsive design improvements */
    @media (max-width: 768px) {
        .main-header {
            padding: 0.5rem 0;
            margin-bottom: 1rem;
        }
        
        .status-widget {
            padding: 0.4rem;
            font-size: 0.9rem;
        }
        
        .progress-container {
            padding: 0.75rem;
            margin: 0.5rem 0;
        }
        
        /* Streamlit specific mobile optimizations */
        .stButton > button {
            width: 100%;
            margin-bottom: 0.5rem;
        }
        
        .stSelectbox > div > div {
            font-size: 0.9rem;
        }
        
        .stTextInput > div > div > input {
            font-size: 0.9rem;
        }
        
        .stTextArea > div > div > textarea {
            font-size: 0.9rem;
        }
    }
    
    @media (max-width: 576px) {
        .main-header h1 {
            font-size: 1.5rem;
        }
        
        .status-widget {
            padding: 0.3rem;
            font-size: 0.8rem;
        }
        
        .stButton > button {
            padding: 0.4rem 0.8rem;
            font-size: 0.9rem;
        }
        
        .stColumns > div {
            padding: 0.25rem;
        }
    }
    
    /* Performance optimizations */
    .stApp {
        max-width: 100%;
    }
    
    /* Loading animations */
    .loading-spinner {
        border: 3px solid #f3f3f3;
        border-top: 3px solid #007bff;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        animation: spin 1s linear infinite;
        margin: 10px auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Improved accessibility */
    .stButton > button:focus {
        outline: 2px solid #007bff;
        outline-offset: 2px;
    }
    
    .stSelectbox > div > div:focus-within {
        outline: 2px solid #007bff;
        outline-offset: 2px;
    }
    
    /* Touch-friendly interactions */
    @media (hover: none) and (pointer: coarse) {
        .stButton > button {
            min-height: 44px;
            min-width: 44px;
        }
        
        .stSelectbox > div > div {
            min-height: 44px;
        }
    }
    
    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .status-widget {
            background-color: #2d3748;
            color: #e2e8f0;
        }
        
        .progress-container {
            background-color: #2d3748;
            color: #e2e8f0;
        }
    }
    
    /* Print styles */
    @media print {
        .stSidebar {
            display: none;
        }
        
        .main-header {
            border-bottom: 1px solid #000;
        }
    }
</style>
""", unsafe_allow_html=True)

class EventPlanningApp:
    """Main application class"""
    
    def __init__(self):
        self.initialize_session_state()
        self.setup_navigation()
    
    def initialize_session_state(self):
        """Initialize all session state variables"""
        # Navigation state
        init_session_state('current_page', 'home')
        init_session_state('navigation_history', ['home'])
        
        # Plan state
        init_session_state('current_plan_id', None)
        init_session_state('plan_data', {})
        init_session_state('plan_status', None)
        
        # Form state
        init_session_state('form_data', {})
        init_session_state('form_step', 1)
        init_session_state('form_completed', False)
        init_session_state('form_errors', [])
        
        # Results state
        init_session_state('plan_combinations', [])
        init_session_state('selected_combination', None)
        init_session_state('plan_blueprint', None)
        
        # UI state
        init_session_state('show_sidebar', True)
        init_session_state('last_activity', datetime.now())
        
        # API state
        init_session_state('api_connected', False)
        init_session_state('api_health_status', {'status': 'unknown'})
        
        # Task Management state
        init_session_state('extended_task_list', None)
        init_session_state('task_list_available', False)
        
        # CRM state
        init_session_state('crm_configured', False)
        init_session_state('crm_preferences', None)
    
    def setup_navigation(self):
        """Setup navigation structure with grouped navigation"""
        # Main pages
        self.main_pages = {
            'home': {
                'title': '🏠 Home',
                'description': 'Dashboard and plan overview',
                'module': 'pages.home',
                'requires_plan': False
            },
            'create_plan': {
                'title': '➕ Create Plan',
                'description': 'Create a new event plan',
                'module': 'pages.create_plan',
                'requires_plan': False
            },
            'plan_status': {
                'title': '📊 Plan Status',
                'description': 'Monitor planning progress',
                'module': 'pages.plan_status',
                'requires_plan': True
            },
            'plan_results': {
                'title': '🎯 Results',
                'description': 'View and select combinations',
                'module': 'pages.plan_results',
                'requires_plan': True
            },
            'plan_blueprint': {
                'title': '📋 Blueprint',
                'description': 'Final event blueprint',
                'module': 'pages.plan_blueprint',
                'requires_plan': True
            }
        }
        
        # Task Management pages
        self.task_pages = {
            'task_list': {
                'title': '📝 Task List',
                'description': 'View and manage tasks',
                'module': 'pages.task_list',
                'requires_plan': True,
                'requires_tasks': True
            },
            'timeline_view': {
                'title': '📅 Timeline',
                'description': 'Visualize task timeline',
                'module': 'pages.timeline_view',
                'requires_plan': True,
                'requires_tasks': True
            },
            'conflicts': {
                'title': '⚠️ Conflicts',
                'description': 'View and resolve conflicts',
                'module': 'pages.conflicts',
                'requires_plan': True,
                'requires_tasks': True
            },
            'vendors': {
                'title': '👥 Vendors',
                'description': 'View vendor assignments and workload',
                'module': 'pages.vendors',
                'requires_plan': True,
                'requires_tasks': True
            }
        }
        
        # CRM Communication pages
        self.crm_pages = {
            'crm_preferences': {
                'title': '⚙️ Preferences',
                'description': 'Manage communication preferences',
                'module': 'pages.crm_preferences',
                'requires_plan': True,
                'requires_crm': True
            },
            'communication_history': {
                'title': '📜 History',
                'description': 'View communication history',
                'module': 'pages.communication_history',
                'requires_plan': True,
                'requires_crm': True
            },
            'crm_analytics': {
                'title': '📊 Analytics',
                'description': 'View communication analytics',
                'module': 'pages.crm_analytics',
                'requires_plan': True,
                'requires_crm': True
            }
        }
        
        # Combine all pages for routing
        self.pages = {**self.main_pages, **self.task_pages, **self.crm_pages}
    
    @perf_monitor.time_operation("render_header")
    def render_header(self):
        """Render the main application header with responsive design"""
        # Inject mobile-responsive CSS for CRM and Task Management
        st.markdown(CRM_CSS, unsafe_allow_html=True)
        st.markdown(TASK_MANAGEMENT_CSS, unsafe_allow_html=True)
        
        st.markdown('<div class="main-header">', unsafe_allow_html=True)
        
        # Render mobile hamburger menu (only visible on mobile)
        render_mobile_hamburger_menu()
        
        # Use responsive columns that stack on mobile
        col1, col2, col3 = st.columns([2, 3, 2])
        
        with col1:
            # Responsive title that adjusts on mobile
            if st.session_state.get('mobile_view', False):
                st.markdown(f"### {config.APP_ICON} {config.APP_TITLE}")
            else:
                st.title(f"{config.APP_ICON} {config.APP_TITLE}")
        
        with col2:
            # Show current plan info if available
            if st.session_state.current_plan_id:
                st.info(f"📋 Current Plan: {st.session_state.current_plan_id}")
        
        with col3:
            # Connection status with responsive display
            health_monitor.display_status_widget(key_suffix="header")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_sidebar(self):
        """Render the navigation sidebar with grouped navigation"""
        with st.sidebar:
            st.title("Navigation")
            
            # Main navigation section
            st.subheader("Main")
            for page_key, page_info in self.main_pages.items():
                disabled = page_info.get('requires_plan', False) and not st.session_state.current_plan_id
                
                if st.button(
                    page_info['title'],
                    key=f"nav_{page_key}",
                    help=page_info['description'] if not disabled else "Create a plan first",
                    use_container_width=True,
                    disabled=disabled
                ):
                    self.navigate_to(page_key)
            
            st.divider()
            
            # Task Management navigation section
            st.subheader("📋 Tasks")
            
            # Check if task list is available
            task_list_available = st.session_state.get('task_list_available', False)
            
            if not st.session_state.current_plan_id:
                st.caption("⚠️ Create a plan first")
            elif not task_list_available:
                st.caption("⚠️ Tasks not yet generated")
            
            for page_key, page_info in self.task_pages.items():
                disabled = (
                    (page_info.get('requires_plan', False) and not st.session_state.current_plan_id) or
                    (page_info.get('requires_tasks', False) and not task_list_available)
                )
                
                help_text = page_info['description']
                if disabled:
                    if not st.session_state.current_plan_id:
                        help_text = "Create a plan first"
                    elif not task_list_available:
                        help_text = "Tasks not yet generated"
                
                if st.button(
                    page_info['title'],
                    key=f"nav_{page_key}",
                    help=help_text,
                    use_container_width=True,
                    disabled=disabled
                ):
                    self.navigate_to(page_key)
            
            st.divider()
            
            # CRM Communication navigation section
            st.subheader("💬 Communications")
            
            # Check if CRM is configured
            crm_configured = st.session_state.get('crm_configured', False)
            
            if not st.session_state.current_plan_id:
                st.caption("⚠️ Create a plan first")
            elif not crm_configured:
                st.caption("⚠️ CRM not configured")
            
            for page_key, page_info in self.crm_pages.items():
                disabled = (
                    (page_info.get('requires_plan', False) and not st.session_state.current_plan_id) or
                    (page_info.get('requires_crm', False) and not crm_configured)
                )
                
                help_text = page_info['description']
                if disabled:
                    if not st.session_state.current_plan_id:
                        help_text = "Create a plan first"
                    elif not crm_configured:
                        help_text = "CRM not configured"
                
                if st.button(
                    page_info['title'],
                    key=f"nav_{page_key}",
                    help=help_text,
                    use_container_width=True,
                    disabled=disabled
                ):
                    self.navigate_to(page_key)
            
            st.divider()
            
            # Quick actions
            st.subheader("Quick Actions")
            
            # Performance dashboard toggle
            render_performance_toggle()
            
            if st.button("🔄 Refresh Status", use_container_width=True, key="sidebar_refresh_status"):
                health_monitor.check_connection(force=True)
                st.rerun()
            
            if st.button("🗑️ Clear Session", use_container_width=True, key="sidebar_clear_session"):
                if st.session_state.get('confirm_clear_session'):
                    # Clear session data
                    keys_to_clear = [
                        'current_plan_id', 'plan_data', 'plan_status',
                        'form_data', 'form_step', 'form_completed', 'form_errors',
                        'plan_combinations', 'selected_combination', 'plan_blueprint',
                        'extended_task_list', 'task_list_available', 'crm_configured', 'crm_preferences'
                    ]
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    st.session_state.confirm_clear_session = False
                    show_info("Session cleared successfully")
                    st.rerun()
                else:
                    st.session_state.confirm_clear_session = True
                    st.warning("Click again to confirm session clear")
            
            st.divider()
            
            # Performance dashboard
            render_performance_dashboard()
            
            # Performance badge
            render_performance_badge()
            
            # Configuration info
            with st.expander("Configuration"):
                st.write(f"**API URL:** {config.API_BASE_URL}")
                st.write(f"**Environment:** {'Development' if config.is_development() else 'Production'}")
                st.write(f"**Timeout:** {config.API_TIMEOUT}s")
                st.write(f"**Retry Attempts:** {config.API_RETRY_ATTEMPTS}")
                st.write(f"**Cache TTL:** {config.CACHE_TTL}s")
            
            # Debug info (only in development)
            if config.is_development():
                with st.expander("Debug Info"):
                    st.write("**Session State Keys:**")
                    for key in sorted(st.session_state.keys()):
                        st.write(f"- {key}")
    
    def navigate_to(self, page_key: str):
        """Navigate to a specific page"""
        if page_key in self.pages:
            # Update navigation state
            st.session_state.current_page = page_key
            
            # Update navigation history
            if page_key not in st.session_state.navigation_history[-3:]:
                st.session_state.navigation_history.append(page_key)
            
            # Update last activity
            st.session_state.last_activity = datetime.now()
            
            st.rerun()
    
    def check_feature_availability(self):
        """Check availability of Task Management and CRM features"""
        # This method can be called to update feature availability status
        # In a real implementation, this would check the API for feature status
        
        # For now, we'll check if we have data in session state
        if st.session_state.current_plan_id:
            # Check if extended task list exists
            if st.session_state.get('extended_task_list'):
                st.session_state.task_list_available = True
            
            # Check if CRM preferences exist (indicating CRM is configured)
            if st.session_state.get('crm_preferences'):
                st.session_state.crm_configured = True
    
    def render_current_page(self):
        """Render the current page content"""
        current_page = st.session_state.current_page
        
        if current_page not in self.pages:
            show_error(f"Unknown page: {current_page}")
            return
        
        page_info = self.pages[current_page]
        
        try:
            # Import and render the page module
            if current_page == 'home':
                self.render_home_page()
            elif current_page == 'create_plan':
                self.render_create_plan_page()
            elif current_page == 'plan_status':
                self.render_plan_status_page()
            elif current_page == 'plan_results':
                self.render_plan_results_page()
            elif current_page == 'plan_blueprint':
                self.render_plan_blueprint_page()
            elif current_page == 'task_list':
                self.render_task_list_page()
            elif current_page == 'timeline_view':
                self.render_timeline_view_page()
            elif current_page == 'conflicts':
                self.render_conflicts_page()
            elif current_page == 'vendors':
                self.render_vendors_page()
            elif current_page == 'crm_preferences':
                self.render_crm_preferences_page()
            elif current_page == 'communication_history':
                self.render_communication_history_page()
            elif current_page == 'crm_analytics':
                self.render_crm_analytics_page()
            else:
                st.error(f"Page '{current_page}' is not implemented yet")
                
        except Exception as e:
            show_error(f"Error loading page: {str(e)}")
            if config.is_development():
                st.exception(e)
    
    def render_home_page(self):
        """Render the home page (placeholder)"""
        st.header("🏠 Welcome to Event Planning Agent")
        
        st.markdown("""
        Welcome to the Event Planning Agent v2 GUI! This interface allows you to:
        
        - **Create Event Plans**: Input your event requirements and preferences
        - **Monitor Progress**: Track real-time planning progress with our AI agents
        - **Review Results**: Compare vendor combinations and select the best options
        - **Get Blueprints**: Download comprehensive event plans and vendor information
        - **Manage Tasks**: View task lists, timelines, and resolve conflicts
        - **Track Communications**: Manage preferences and view communication analytics
        
        ### Getting Started
        
        1. Click **"➕ Create Plan"** to start planning a new event
        2. Fill out the event details and preferences
        3. Monitor the planning process in **"📊 Plan Status"**
        4. Review results and select combinations in **"🎯 Results"**
        5. Download your final blueprint from **"📋 Blueprint"**
        6. View tasks and timeline in **"📋 Tasks"** section
        7. Manage communications in **"💬 Communications"** section
        
        ### System Status
        """)
        
        # Show detailed connection status
        health_monitor.display_status_widget(show_details=True, key_suffix="home")
        
        # Show recent plans if any
        if st.session_state.current_plan_id:
            st.subheader("Current Plan")
            st.info(f"Plan ID: {st.session_state.current_plan_id}")
            
            # Quick links section
            st.subheader("Quick Links")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📊 View Status", key="home_view_status", use_container_width=True):
                    self.navigate_to('plan_status')
                
                if st.button("🎯 View Results", key="home_view_results", use_container_width=True):
                    self.navigate_to('plan_results')
            
            with col2:
                if st.button("📋 View Blueprint", key="home_view_blueprint", use_container_width=True):
                    self.navigate_to('plan_blueprint')
                
                # Task list quick link (disabled if not available)
                task_available = st.session_state.get('task_list_available', False)
                if st.button(
                    "📝 View Tasks", 
                    key="home_view_tasks", 
                    use_container_width=True,
                    disabled=not task_available,
                    help="Tasks not yet generated" if not task_available else "View task list"
                ):
                    self.navigate_to('task_list')
            
            with col3:
                # Timeline quick link (disabled if not available)
                if st.button(
                    "📅 View Timeline", 
                    key="home_view_timeline", 
                    use_container_width=True,
                    disabled=not task_available,
                    help="Tasks not yet generated" if not task_available else "View timeline"
                ):
                    self.navigate_to('timeline_view')
                
                # CRM quick link (disabled if not configured)
                crm_configured = st.session_state.get('crm_configured', False)
                if st.button(
                    "💬 Communications", 
                    key="home_view_crm", 
                    use_container_width=True,
                    disabled=not crm_configured,
                    help="CRM not configured" if not crm_configured else "View communications"
                ):
                    self.navigate_to('communication_history')
            
            # Feature status indicators
            st.divider()
            st.subheader("Feature Status")
            
            col1, col2 = st.columns(2)
            with col1:
                if task_available:
                    st.success("✅ Task Management Available")
                else:
                    st.warning("⏳ Task Management: Generating...")
            
            with col2:
                if crm_configured:
                    st.success("✅ CRM Communications Available")
                else:
                    st.info("ℹ️ CRM Communications: Not Configured")
    
    def render_create_plan_page(self):
        """Render the create plan page"""
        from pages.create_plan import render_create_plan_page
        render_create_plan_page()
    
    def render_plan_status_page(self):
        """Render the plan status page"""
        from pages.plan_status import render_plan_status_page
        render_plan_status_page()
    
    def render_plan_results_page(self):
        """Render the plan results page"""
        from pages.plan_results import render_plan_results_page
        render_plan_results_page()
    
    def render_plan_blueprint_page(self):
        """Render the plan blueprint page"""
        from pages.plan_blueprint import render_plan_blueprint_page
        render_plan_blueprint_page()
    
    def render_task_list_page(self):
        """Render the task list page"""
        from pages.task_list import render_task_list_page
        render_task_list_page()
    
    def render_timeline_view_page(self):
        """Render the timeline view page"""
        from pages.timeline_view import render_timeline_view_page
        render_timeline_view_page()
    
    def render_conflicts_page(self):
        """Render the conflicts page"""
        from pages.conflicts import render_conflicts_page
        render_conflicts_page()
    
    def render_vendors_page(self):
        """Render the vendors page"""
        from pages.vendors import render_vendors_page
        render_vendors_page()
    
    def render_crm_preferences_page(self):
        """Render the CRM preferences page"""
        from pages.crm_preferences import render_crm_preferences_page
        render_crm_preferences_page()
    
    def render_communication_history_page(self):
        """Render the communication history page"""
        from pages.communication_history import render_communication_history_page
        render_communication_history_page()
    
    def render_crm_analytics_page(self):
        """Render the CRM analytics page"""
        from pages.crm_analytics import render_crm_analytics_page
        render_crm_analytics_page()
    
    @perf_monitor.time_operation("app_run")
    def run(self):
        """Run the main application with performance monitoring"""
        try:
            # Detect mobile view based on viewport
            self.detect_mobile_view()
            
            # Auto-check connection health
            health_monitor.auto_check_connection()
            
            # Check feature availability
            self.check_feature_availability()
            
            # Memory cleanup every 5 minutes
            self.periodic_cleanup()
            
            # Render the application with loading spinner for heavy operations
            with LoadingSpinner("Loading application...") if st.session_state.get('show_loading', False) else st.container():
                self.render_header()
                self.render_sidebar()
                self.render_current_page()
            
            # Update last activity
            st.session_state.last_activity = datetime.now()
            
            # Show performance metrics in development
            if config.is_development():
                self.show_performance_metrics()
                
        except Exception as e:
            show_error(f"Application error: {str(e)}")
            if config.is_development():
                st.exception(e)
    
    def detect_mobile_view(self):
        """Detect if user is on mobile device"""
        # This is a simple heuristic - in a real app you might use JavaScript
        # For now, we'll use session state to allow manual toggle
        if 'mobile_view' not in st.session_state:
            st.session_state.mobile_view = False
    
    def periodic_cleanup(self):
        """Perform periodic memory cleanup"""
        current_time = datetime.now()
        last_cleanup = st.session_state.get('last_cleanup', current_time)
        
        # Cleanup every 5 minutes
        if (current_time - last_cleanup).total_seconds() > 300:
            MemoryOptimizer.cleanup_session_state()
            st.session_state.last_cleanup = current_time
    
    def show_performance_metrics(self):
        """Show performance metrics in development mode"""
        with st.expander("Performance Metrics (Dev Only)"):
            metrics = perf_monitor.get_metrics()
            if metrics:
                for operation, data in metrics.items():
                    st.write(f"**{operation}**: {data.get('last_execution_time', 0):.3f}s ({data.get('status', 'unknown')})")
            else:
                st.write("No performance data available")

def main():
    """Main application entry point"""
    try:
        app = EventPlanningApp()
        app.run()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        if config.is_development():
            st.exception(e)

if __name__ == "__main__":
    main()