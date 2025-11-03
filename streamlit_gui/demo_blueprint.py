"""
Demo script for blueprint functionality
Run this to test the blueprint page without the full Streamlit app
"""
import streamlit as st
import sys
import os

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pages.plan_blueprint import BlueprintManager
from components.blueprint import BlueprintExporter, TimelineGenerator
from utils.helpers import format_currency
from datetime import datetime

# Configure Streamlit page
st.set_page_config(
    page_title="Blueprint Demo",
    page_icon="📋",
    layout="wide"
)

def create_demo_blueprint_data():
    """Create comprehensive demo blueprint data"""
    return {
        'event_info': {
            'client_name': 'Sarah & Michael Johnson',
            'event_type': 'Wedding Reception',
            'event_date': '2024-08-15',
            'event_time': '18:00',
            'guest_count': 120,
            'budget': 35000,
            'location': 'Riverside Gardens, California',
            'client_vision': 'A romantic garden wedding with elegant touches, featuring soft pastels, string lights, and a mix of rustic and modern elements. We want our guests to feel like they are in a fairy tale.'
        },
        'selected_combination': {
            'combination_id': 'combo_wedding_001',
            'fitness_score': 94.2,
            'total_cost': 32750,
            'venue': {
                'name': 'Riverside Gardens Event Center',
                'cost': 12000,
                'contact_phone': '(555) 123-4567',
                'contact_email': 'events@riversidegardens.com',
                'website': 'www.riversidegardens.com',
                'location': '456 Garden View Drive, Riverside, CA 92501',
                'capacity': {'max_guests': 150, 'ceremony': 100, 'reception': 120},
                'amenities': [
                    'Outdoor ceremony pavilion',
                    'Indoor reception hall with garden views',
                    'Bridal suite with private entrance',
                    'Groom preparation room',
                    'Professional catering kitchen',
                    'Parking for 80 vehicles',
                    'Built-in sound system',
                    'String light installations',
                    'Garden photo locations'
                ],
                'notes': 'Includes tables, chairs, linens, and basic lighting. Setup begins at 8 AM.'
            },
            'caterer': {
                'name': 'Artisan Culinary Creations',
                'cost': 14500,
                'contact_phone': '(555) 234-5678',
                'contact_email': 'catering@artisancreations.com',
                'website': 'www.artisancreations.com',
                'location': '789 Culinary Way, Riverside, CA 92502',
                'cuisine_types': ['Contemporary American', 'Mediterranean', 'Farm-to-Table'],
                'service_style': 'Plated dinner with cocktail hour and dessert station',
                'menu_highlights': [
                    'Herb-crusted salmon with lemon risotto',
                    'Grass-fed beef tenderloin with roasted vegetables',
                    'Vegetarian stuffed portobello mushrooms',
                    'Artisan cheese and charcuterie display',
                    'Seasonal fruit and dessert bar'
                ],
                'notes': 'Includes service staff, linens, china, and glassware. Dietary restrictions accommodated.'
            },
            'photographer': {
                'name': 'Moments in Time Photography',
                'cost': 4500,
                'contact_phone': '(555) 345-6789',
                'contact_email': 'bookings@momentsintime.com',
                'website': 'www.momentsintime.com',
                'location': 'Mobile service throughout California',
                'packages': [
                    '8-hour wedding day coverage',
                    'Complimentary engagement session',
                    'Online gallery with high-resolution images',
                    'Print release for personal use',
                    'USB drive with all edited photos',
                    'Wedding album design consultation'
                ],
                'style': 'Romantic, candid, and artistic photography',
                'notes': 'Second photographer included for ceremony and reception coverage.'
            },
            'makeup_artist': {
                'name': 'Bella Rosa Beauty Studio',
                'cost': 1750,
                'contact_phone': '(555) 456-7890',
                'contact_email': 'bella@bellarosabeauty.com',
                'website': 'www.bellarosabeauty.com',
                'location': 'Mobile service to venue',
                'services': [
                    'Bridal makeup application',
                    'Bridal hair styling',
                    'Makeup trial session (included)',
                    'Touch-up kit for reception',
                    'Maid of honor makeup (optional)',
                    'Hair accessories and styling tools'
                ],
                'style': 'Natural, romantic, and long-lasting looks',
                'notes': 'Arrives 3 hours before ceremony. Eco-friendly and cruelty-free products used.'
            }
        },
        'timeline': {
            'pre_event': [
                {
                    'date': '2024-07-15',
                    'task': 'Send save-the-dates to all guests',
                    'responsible': 'Client',
                    'days_before': 31,
                    'status': 'pending'
                },
                {
                    'date': '2024-07-25',
                    'task': 'Send formal wedding invitations',
                    'responsible': 'Client',
                    'days_before': 21,
                    'status': 'pending'
                },
                {
                    'date': '2024-08-01',
                    'task': 'Confirm final details with all vendors',
                    'responsible': 'Client',
                    'days_before': 14,
                    'status': 'pending'
                },
                {
                    'date': '2024-08-08',
                    'task': 'Finalize guest count and dietary restrictions',
                    'responsible': 'Client',
                    'days_before': 7,
                    'status': 'pending'
                },
                {
                    'date': '2024-08-12',
                    'task': 'Makeup and hair trial session',
                    'responsible': 'Bella Rosa Beauty Studio',
                    'days_before': 3,
                    'status': 'scheduled'
                },
                {
                    'date': '2024-08-13',
                    'task': 'Final venue walkthrough and setup confirmation',
                    'responsible': 'Riverside Gardens + Client',
                    'days_before': 2,
                    'status': 'pending'
                },
                {
                    'date': '2024-08-14',
                    'task': 'Prepare vendor payments and gratuity envelopes',
                    'responsible': 'Client',
                    'days_before': 1,
                    'status': 'pending'
                }
            ],
            'event_day': [
                {
                    'time': '08:00',
                    'activity': 'Venue setup and decoration begins',
                    'vendor': 'Riverside Gardens Event Center',
                    'notes': 'Florist and decoration team arrival',
                    'duration': '4 hours'
                },
                {
                    'time': '10:00',
                    'activity': 'Catering team setup and food preparation',
                    'vendor': 'Artisan Culinary Creations',
                    'notes': 'Kitchen prep and equipment setup',
                    'duration': '8 hours'
                },
                {
                    'time': '12:00',
                    'activity': 'Photography equipment setup and venue scouting',
                    'vendor': 'Moments in Time Photography',
                    'notes': 'Location scouting and lighting assessment',
                    'duration': '30 minutes'
                },
                {
                    'time': '14:00',
                    'activity': 'Final venue inspection and vendor coordination',
                    'vendor': 'All vendors + Wedding coordinator',
                    'notes': 'Timeline review and last-minute adjustments',
                    'duration': '1 hour'
                },
                {
                    'time': '15:00',
                    'activity': 'Bridal beauty services begin',
                    'vendor': 'Bella Rosa Beauty Studio',
                    'notes': 'Hair and makeup in bridal suite',
                    'duration': '3 hours'
                },
                {
                    'time': '16:30',
                    'activity': 'Photography - getting ready shots',
                    'vendor': 'Moments in Time Photography',
                    'notes': 'Bridal preparations and detail shots',
                    'duration': '1.5 hours'
                },
                {
                    'time': '17:30',
                    'activity': 'Guest arrival and cocktail hour begins',
                    'vendor': 'All vendors',
                    'notes': 'Welcome drinks and appetizers served',
                    'duration': '30 minutes'
                },
                {
                    'time': '18:00',
                    'activity': 'Wedding ceremony begins',
                    'vendor': 'All vendors',
                    'notes': 'Processional music and ceremony',
                    'duration': '30 minutes'
                },
                {
                    'time': '18:30',
                    'activity': 'Cocktail hour and photography session',
                    'vendor': 'Artisan Culinary + Moments in Time',
                    'notes': 'Couple portraits and family photos',
                    'duration': '1.5 hours'
                },
                {
                    'time': '20:00',
                    'activity': 'Reception dinner service begins',
                    'vendor': 'Artisan Culinary Creations',
                    'notes': 'Plated dinner service with wine pairings',
                    'duration': '2 hours'
                },
                {
                    'time': '22:00',
                    'activity': 'Dancing and celebration continues',
                    'vendor': 'All vendors',
                    'notes': 'Open bar and dessert station available',
                    'duration': '2 hours'
                },
                {
                    'time': '24:00',
                    'activity': 'Event conclusion and cleanup begins',
                    'vendor': 'Riverside Gardens + Artisan Culinary',
                    'notes': 'Guest departure and vendor breakdown',
                    'duration': '2 hours'
                }
            ],
            'post_event': [
                {
                    'task': 'Venue cleanup and equipment breakdown',
                    'deadline': 'Same night (by 2 AM)',
                    'responsible': 'Riverside Gardens + Artisan Culinary',
                    'priority': 'high'
                },
                {
                    'task': 'Photography equipment pickup and initial photo review',
                    'deadline': '1 day after event',
                    'responsible': 'Moments in Time Photography',
                    'priority': 'medium'
                },
                {
                    'task': 'Final vendor payments and gratuities distribution',
                    'deadline': '2 days after event',
                    'responsible': 'Client',
                    'priority': 'high'
                },
                {
                    'task': 'Photo editing and gallery preparation',
                    'deadline': '2 weeks after event',
                    'responsible': 'Moments in Time Photography',
                    'priority': 'medium'
                },
                {
                    'task': 'Thank you notes to vendors and key guests',
                    'deadline': '1 week after event',
                    'responsible': 'Client',
                    'priority': 'low'
                },
                {
                    'task': 'Wedding album design consultation',
                    'deadline': '3 weeks after event',
                    'responsible': 'Moments in Time Photography + Client',
                    'priority': 'low'
                }
            ]
        },
        'additional_costs': [
            {
                'description': 'Floral arrangements and centerpieces',
                'amount': 2500,
                'vendor': 'Garden Blooms Florist',
                'category': 'Decoration'
            },
            {
                'description': 'Wedding cake and dessert station',
                'amount': 1200,
                'vendor': 'Sweet Dreams Bakery',
                'category': 'Catering'
            },
            {
                'description': 'String lighting and additional decorations',
                'amount': 800,
                'vendor': 'Riverside Gardens (add-on)',
                'category': 'Venue'
            },
            {
                'description': 'Transportation for bridal party',
                'amount': 600,
                'vendor': 'Luxury Limo Services',
                'category': 'Transportation'
            },
            {
                'description': 'Wedding coordinator day-of services',
                'amount': 1500,
                'vendor': 'Perfect Day Coordination',
                'category': 'Planning'
            }
        ],
        'payment_schedule': [
            {
                'due_date': '2024-06-15',
                'amount': 8000,
                'description': 'Initial deposit (25% of total)',
                'status': 'paid',
                'vendors': ['Riverside Gardens', 'Artisan Culinary']
            },
            {
                'due_date': '2024-07-15',
                'amount': 12000,
                'description': 'Second payment (35% of total)',
                'status': 'pending',
                'vendors': ['All vendors']
            },
            {
                'due_date': '2024-08-01',
                'amount': 8000,
                'description': 'Third payment (25% of total)',
                'status': 'pending',
                'vendors': ['Moments in Time', 'Bella Rosa Beauty']
            },
            {
                'due_date': '2024-08-15',
                'amount': 4750,
                'description': 'Final payment and gratuities (15% of total)',
                'status': 'pending',
                'vendors': ['All vendors + tips']
            }
        ],
        'fitness_details': {
            'budget_compatibility': 95.5,
            'style_match': 92.8,
            'location_convenience': 94.0,
            'vendor_reputation': 96.2,
            'service_quality': 93.5,
            'availability_match': 94.8
        }
    }

def main():
    """Main demo function"""
    st.title("📋 Blueprint Functionality Demo")
    
    st.markdown("""
    This demo showcases the blueprint display and export functionality for event planning.
    The blueprint includes comprehensive event details, vendor information, timeline, and export options.
    """)
    
    # Create demo data
    blueprint_data = create_demo_blueprint_data()
    
    # Initialize session state for demo
    if 'current_plan_id' not in st.session_state:
        st.session_state.current_plan_id = 'demo_wedding_001'
    
    if 'plan_blueprint' not in st.session_state:
        st.session_state.plan_blueprint = blueprint_data
    
    # Display blueprint using the BlueprintManager
    blueprint_manager = BlueprintManager()
    blueprint_manager.display_blueprint(blueprint_data)
    
    # Additional demo information
    st.markdown("---")
    st.subheader("🔧 Demo Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Features Demonstrated:**
        - Comprehensive event overview
        - Detailed vendor information
        - Interactive timeline display
        - Budget breakdown and analysis
        - Contact directory
        - Next steps and recommendations
        """)
    
    with col2:
        st.markdown("""
        **Export Formats Available:**
        - PDF with professional formatting
        - JSON for data integration
        - Text for simple sharing
        - HTML for web viewing
        - Contact list download
        """)
    
    # Test export functionality
    st.subheader("🧪 Test Export Functions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    exporter = BlueprintExporter()
    
    with col1:
        if st.button("Test JSON Export"):
            try:
                exporter._export_json(blueprint_data)
            except Exception as e:
                st.error(f"Export test failed: {e}")
    
    with col2:
        if st.button("Test Text Export"):
            try:
                exporter._export_text(blueprint_data)
            except Exception as e:
                st.error(f"Export test failed: {e}")
    
    with col3:
        if st.button("Test HTML Export"):
            try:
                exporter._export_html(blueprint_data)
            except Exception as e:
                st.error(f"Export test failed: {e}")
    
    with col4:
        if st.button("Test PDF Export"):
            try:
                exporter._export_pdf(blueprint_data)
            except Exception as e:
                st.error(f"PDF export requires reportlab: {e}")
    
    # Timeline generator test
    st.subheader("📅 Timeline Generator Test")
    
    if st.button("Generate New Timeline"):
        timeline_gen = TimelineGenerator()
        new_timeline = timeline_gen.generate_timeline(blueprint_data)
        
        st.success("Timeline generated successfully!")
        st.json(new_timeline)

if __name__ == "__main__":
    main()