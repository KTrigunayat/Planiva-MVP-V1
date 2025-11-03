"""
Demo script to showcase the results display functionality
Run with: streamlit run demo_results.py
"""
import streamlit as st
import sys
import os

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from components.results import results_manager, plan_manager
from components.styles import RESULTS_CSS
from utils.helpers import format_currency

# Configure Streamlit page
st.set_page_config(
    page_title="Results Display Demo",
    page_icon="🎯",
    layout="wide"
)

# Add CSS
st.markdown(RESULTS_CSS, unsafe_allow_html=True)

def create_sample_combinations():
    """Create sample vendor combinations for demo"""
    return [
        {
            "combination_id": "combo_001",
            "fitness_score": 92.5,
            "total_cost": 18500,
            "fitness_details": {
                "venue_match": 95.0,
                "budget_fit": 88.0,
                "style_alignment": 94.0,
                "location_preference": 92.0
            },
            "venue": {
                "name": "Grand Ballroom at The Plaza",
                "location": "Downtown Manhattan, NY",
                "cost": 12000,
                "contact_phone": "(555) 123-4567",
                "contact_email": "events@theplaza.com",
                "amenities": [
                    "Crystal Chandeliers",
                    "Marble Dance Floor", 
                    "Professional Sound System",
                    "Valet Parking",
                    "Bridal Suite",
                    "Garden Terrace"
                ]
            },
            "caterer": {
                "name": "Gourmet Excellence Catering",
                "cost": 4200,
                "contact_phone": "(555) 234-5678",
                "contact_email": "info@gourmetexcellence.com",
                "cuisine_types": ["French", "Italian", "Contemporary American"],
                "amenities": ["Farm-to-Table", "Dietary Accommodations", "Wine Pairing"]
            },
            "photographer": {
                "name": "Perfect Moments Photography",
                "cost": 1800,
                "contact_phone": "(555) 345-6789",
                "contact_email": "hello@perfectmoments.com",
                "amenities": ["Engagement Session", "Online Gallery", "Print Package"]
            },
            "makeup_artist": {
                "name": "Beauty by Isabella",
                "cost": 500,
                "contact_phone": "(555) 456-7890",
                "contact_email": "isabella@beautybyisabella.com",
                "amenities": ["Trial Session", "Touch-up Kit", "Bridal Party Discounts"]
            }
        },
        {
            "combination_id": "combo_002",
            "fitness_score": 87.3,
            "total_cost": 15200,
            "fitness_details": {
                "venue_match": 85.0,
                "budget_fit": 92.0,
                "style_alignment": 88.0,
                "location_preference": 84.0
            },
            "venue": {
                "name": "Riverside Garden Pavilion",
                "location": "Brooklyn Heights, NY",
                "cost": 8500,
                "contact_phone": "(555) 567-8901",
                "contact_email": "events@riversidepavilion.com",
                "amenities": [
                    "Waterfront Views",
                    "Garden Ceremony Space",
                    "Outdoor Reception Area",
                    "String Light Canopy",
                    "Fire Pit Lounge"
                ]
            },
            "caterer": {
                "name": "Fresh & Local Catering Co",
                "cost": 3800,
                "contact_phone": "(555) 678-9012",
                "contact_email": "orders@freshandlocal.com",
                "cuisine_types": ["Farm-to-Table", "Vegetarian", "Organic"],
                "amenities": ["Sustainable Practices", "Local Sourcing", "Custom Menus"]
            },
            "photographer": {
                "name": "Natural Light Studios",
                "cost": 1600,
                "contact_phone": "(555) 789-0123",
                "contact_email": "bookings@naturallightstudios.com",
                "amenities": ["Drone Photography", "Same-Day Preview", "USB Drive"]
            },
            "makeup_artist": {
                "name": "Glamour Touch by Sarah",
                "cost": 1300,
                "contact_phone": "(555) 890-1234",
                "contact_email": "sarah@glamourtouch.com",
                "amenities": ["Airbrush Makeup", "Hair Styling", "Group Packages"]
            }
        },
        {
            "combination_id": "combo_003",
            "fitness_score": 81.7,
            "total_cost": 22800,
            "fitness_details": {
                "venue_match": 90.0,
                "budget_fit": 65.0,
                "style_alignment": 85.0,
                "location_preference": 87.0
            },
            "venue": {
                "name": "Metropolitan Museum Rooftop",
                "location": "Upper East Side, NY",
                "cost": 15000,
                "contact_phone": "(555) 901-2345",
                "contact_email": "private@metmuseum.org",
                "amenities": [
                    "City Skyline Views",
                    "Museum Access",
                    "Historic Architecture",
                    "Professional Lighting",
                    "Climate Control"
                ]
            },
            "caterer": {
                "name": "Luxury Events Catering",
                "cost": 5500,
                "contact_phone": "(555) 012-3456",
                "contact_email": "events@luxurycatering.com",
                "cuisine_types": ["International Fusion", "Gourmet", "Molecular Gastronomy"],
                "amenities": ["Michelin-Star Chefs", "Wine Sommelier", "Custom Presentations"]
            },
            "photographer": {
                "name": "Elite Wedding Photography",
                "cost": 1800,
                "contact_phone": "(555) 123-4567",
                "contact_email": "info@eliteweddings.com",
                "amenities": ["Second Shooter", "Engagement Session", "Album Design"]
            },
            "makeup_artist": {
                "name": "Couture Beauty Studio",
                "cost": 500,
                "contact_phone": "(555) 234-5678",
                "contact_email": "studio@couturebeauty.com",
                "amenities": ["Luxury Products", "On-Site Service", "Bridal Party Packages"]
            }
        },
        {
            "combination_id": "combo_004",
            "fitness_score": 76.2,
            "total_cost": 12900,
            "fitness_details": {
                "venue_match": 78.0,
                "budget_fit": 95.0,
                "style_alignment": 72.0,
                "location_preference": 60.0
            },
            "venue": {
                "name": "Community Center Ballroom",
                "location": "Queens, NY",
                "cost": 6000,
                "contact_phone": "(555) 345-6789",
                "contact_email": "rentals@communitycenter.org",
                "amenities": [
                    "Large Dance Floor",
                    "Full Kitchen Access",
                    "Parking Available",
                    "Wheelchair Accessible",
                    "Basic AV Equipment"
                ]
            },
            "caterer": {
                "name": "Budget Friendly Catering",
                "cost": 2800,
                "contact_phone": "(555) 456-7890",
                "contact_email": "info@budgetcatering.com",
                "cuisine_types": ["American", "Italian", "Mexican"],
                "amenities": ["Buffet Style", "Family Portions", "Flexible Menu"]
            },
            "photographer": {
                "name": "Affordable Memories Photo",
                "cost": 900,
                "contact_phone": "(555) 567-8901",
                "contact_email": "book@affordablememories.com",
                "amenities": ["Digital Gallery", "Basic Editing", "Print Rights"]
            },
            "makeup_artist": {
                "name": "Simple Beauty Services",
                "cost": 3200,
                "contact_phone": "(555) 678-9012",
                "contact_email": "simple@beautyservices.com",
                "amenities": ["Basic Makeup", "Hair Styling", "Group Rates"]
            }
        }
    ]

def create_sample_plans():
    """Create sample plans for demo"""
    return [
        {
            "plan_id": "plan_001",
            "client_name": "Emily & Michael Johnson",
            "event_type": "Wedding",
            "status": "completed",
            "created_at": "2024-01-15T10:30:00Z",
            "event_date": "2024-06-15",
            "budget": 25000,
            "location": "New York, NY"
        },
        {
            "plan_id": "plan_002",
            "client_name": "TechCorp Inc.",
            "event_type": "Corporate Gala",
            "status": "in_progress",
            "created_at": "2024-01-20T14:15:00Z",
            "event_date": "2024-03-10",
            "budget": 50000,
            "location": "San Francisco, CA"
        },
        {
            "plan_id": "plan_003",
            "client_name": "Sarah Martinez",
            "event_type": "Birthday Party",
            "status": "pending",
            "created_at": "2024-01-25T09:45:00Z",
            "event_date": "2024-02-28",
            "budget": 8000,
            "location": "Los Angeles, CA"
        },
        {
            "plan_id": "plan_004",
            "client_name": "David & Lisa Chen",
            "event_type": "Anniversary Celebration",
            "status": "failed",
            "created_at": "2024-01-10T16:20:00Z",
            "event_date": "2024-02-14",
            "budget": 15000,
            "location": "Chicago, IL"
        },
        {
            "plan_id": "plan_005",
            "client_name": "University Alumni Association",
            "event_type": "Reunion Dinner",
            "status": "cancelled",
            "created_at": "2024-01-05T11:00:00Z",
            "event_date": "2024-05-20",
            "budget": 30000,
            "location": "Boston, MA",
            "archived": True
        }
    ]

def main():
    """Main demo application"""
    st.title("🎯 Results Display Demo")
    st.markdown("This demo showcases the vendor combination display and plan management features.")
    
    # Create tabs for different demos
    tab1, tab2, tab3 = st.tabs(["🎯 Combination Display", "📊 Comparison View", "📋 Plan Management"])
    
    with tab1:
        st.header("Vendor Combination Display")
        st.markdown("This shows how vendor combinations are displayed with different view modes.")
        
        # Load sample data
        combinations = create_sample_combinations()
        
        # Display combinations
        selected_combination = results_manager.display_combinations(combinations, "card")
        
        if selected_combination:
            st.success(f"Selected combination: {selected_combination}")
            st.balloons()
    
    with tab2:
        st.header("Comparison View Demo")
        st.markdown("Compare multiple vendor combinations side by side.")
        
        combinations = create_sample_combinations()
        
        # Force comparison view
        selected_combination = results_manager._display_comparison_view(combinations)
        
        if selected_combination:
            st.success(f"Selected combination from comparison: {selected_combination}")
    
    with tab3:
        st.header("Plan Management Demo")
        st.markdown("Manage multiple event plans with search and filtering.")
        
        # Mock the plans cache for demo
        plans = create_sample_plans()
        plan_manager.plans_cache = {"plans": plans}
        plan_manager.last_refresh = st.session_state.get("demo_refresh_time")
        
        # Display plan management interface
        plan_manager.display_plan_management_interface()
    
    # Demo controls
    st.sidebar.header("Demo Controls")
    
    if st.sidebar.button("🔄 Reset Demo"):
        # Clear any demo session state
        for key in list(st.session_state.keys()):
            if key.startswith("demo_") or key.startswith("confirm_"):
                del st.session_state[key]
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Demo Features:**")
    st.sidebar.markdown("• Card, Table, and Comparison views")
    st.sidebar.markdown("• Sorting and filtering")
    st.sidebar.markdown("• Detailed vendor information")
    st.sidebar.markdown("• Plan management interface")
    st.sidebar.markdown("• Responsive design")
    
    # Show sample data info
    with st.sidebar.expander("Sample Data Info"):
        st.write("**Combinations:** 4 sample vendor combinations")
        st.write("**Plans:** 5 sample event plans")
        st.write("**Statuses:** Various plan statuses")
        st.write("**Budgets:** Range from $8K to $50K")

if __name__ == "__main__":
    main()