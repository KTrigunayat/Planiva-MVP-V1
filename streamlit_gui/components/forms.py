"""
Reusable form components for the Event Planning GUI
"""
import streamlit as st
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from utils.validators import EventPlanValidator, ValidationError
from utils.helpers import show_error, show_success, show_warning

class EventPlanningForm:
    """Comprehensive event planning form with multi-section layout"""
    
    def __init__(self):
        self.sections = [
            "Basic Information",
            "Guest Information", 
            "Budget & Priorities",
            "Venue Preferences",
            "Catering Preferences",
            "Photography & Services",
            "Client Vision & Theme"
        ]
        
        # Initialize form data in session state if not exists
        if 'form_data' not in st.session_state:
            st.session_state.form_data = {}
        
        if 'form_step' not in st.session_state:
            st.session_state.form_step = 1
            
        if 'form_errors' not in st.session_state:
            st.session_state.form_errors = []
    
    def render_progress_indicator(self):
        """Render form progress indicator"""
        current_step = st.session_state.form_step
        total_steps = len(self.sections)
        
        progress = (current_step - 1) / total_steps
        
        st.markdown("### Form Progress")
        st.progress(progress)
        st.write(f"Step {current_step} of {total_steps}: {self.sections[current_step - 1]}")
        
        # Show section navigation
        cols = st.columns(total_steps)
        for i, section in enumerate(self.sections):
            with cols[i]:
                if i + 1 == current_step:
                    st.markdown(f"**{i+1}. {section[:10]}...**")
                elif i + 1 < current_step:
                    st.markdown(f"✅ {i+1}. {section[:10]}...")
                else:
                    st.markdown(f"{i+1}. {section[:10]}...")
    
    def render_section_1_basic_info(self) -> Dict:
        """Render basic information section"""
        st.subheader("📋 Basic Event Information")
        
        data = {}
        
        col1, col2 = st.columns(2)
        
        with col1:
            data['client_name'] = st.text_input(
                "Client Name *",
                value=st.session_state.form_data.get('client_name', ''),
                help="Full name of the client or primary contact"
            )
            
            data['client_email'] = st.text_input(
                "Client Email",
                value=st.session_state.form_data.get('client_email', ''),
                help="Primary email for communication"
            )
            
            data['event_type'] = st.selectbox(
                "Event Type *",
                options=["", "Wedding", "Corporate Event", "Birthday Party", "Anniversary", "Graduation", "Baby Shower", "Other"],
                index=0 if not st.session_state.form_data.get('event_type') else 
                      ["", "Wedding", "Corporate Event", "Birthday Party", "Anniversary", "Graduation", "Baby Shower", "Other"].index(st.session_state.form_data.get('event_type')),
                help="Type of event being planned"
            )
            
            if data['event_type'] == "Other":
                data['custom_event_type'] = st.text_input(
                    "Specify Event Type",
                    value=st.session_state.form_data.get('custom_event_type', ''),
                    help="Please specify the type of event"
                )
        
        with col2:
            data['client_phone'] = st.text_input(
                "Client Phone",
                value=st.session_state.form_data.get('client_phone', ''),
                help="Primary phone number for communication"
            )
            
            # Event date with validation
            min_date = date.today() + timedelta(days=1)
            max_date = date.today() + timedelta(days=730)  # 2 years
            
            data['event_date'] = st.date_input(
                "Event Date *",
                value=st.session_state.form_data.get('event_date', min_date),
                min_value=min_date,
                max_value=max_date,
                help="Date of the event"
            )
            
            data['location'] = st.text_input(
                "Event Location/City *",
                value=st.session_state.form_data.get('location', ''),
                help="City or area where the event will take place"
            )
            
            data['backup_date'] = st.date_input(
                "Backup Date (Optional)",
                value=st.session_state.form_data.get('backup_date'),
                min_value=min_date,
                max_value=max_date,
                help="Alternative date in case primary date is not available"
            )
        
        # Event timing
        st.markdown("#### Event Timing")
        time_col1, time_col2 = st.columns(2)
        
        with time_col1:
            data['start_time'] = st.time_input(
                "Start Time",
                value=st.session_state.form_data.get('start_time', datetime.strptime("18:00", "%H:%M").time()),
                help="Expected start time of the event"
            )
        
        with time_col2:
            data['duration_hours'] = st.number_input(
                "Duration (hours)",
                min_value=1,
                max_value=24,
                value=st.session_state.form_data.get('duration_hours', 4),
                help="Expected duration of the event in hours"
            )
        
        return data
    
    def render_section_2_guest_info(self) -> Dict:
        """Render guest information section"""
        st.subheader("👥 Guest Information")
        
        data = {}
        
        col1, col2 = st.columns(2)
        
        with col1:
            data['total_guests'] = st.number_input(
                "Total Number of Guests *",
                min_value=1,
                max_value=10000,
                value=st.session_state.form_data.get('total_guests', 50),
                help="Total expected number of guests"
            )
            
            # Guest split option
            data['has_ceremony_reception_split'] = st.checkbox(
                "Different guest counts for ceremony and reception",
                value=st.session_state.form_data.get('has_ceremony_reception_split', False),
                help="Check if ceremony and reception will have different guest counts"
            )
            
            if data['has_ceremony_reception_split']:
                data['ceremony_guests'] = st.number_input(
                    "Ceremony Guests",
                    min_value=1,
                    max_value=data['total_guests'],
                    value=st.session_state.form_data.get('ceremony_guests', data['total_guests']),
                    help="Number of guests for ceremony"
                )
                
                data['reception_guests'] = st.number_input(
                    "Reception Guests", 
                    min_value=1,
                    max_value=data['total_guests'],
                    value=st.session_state.form_data.get('reception_guests', data['total_guests']),
                    help="Number of guests for reception"
                )
        
        with col2:
            st.markdown("#### Guest Demographics (Optional)")
            
            data['adult_guests'] = st.number_input(
                "Adult Guests",
                min_value=0,
                max_value=data['total_guests'],
                value=st.session_state.form_data.get('adult_guests', int(data['total_guests'] * 0.8)),
                help="Number of adult guests"
            )
            
            data['child_guests'] = st.number_input(
                "Children (under 12)",
                min_value=0,
                max_value=data['total_guests'],
                value=st.session_state.form_data.get('child_guests', data['total_guests'] - int(data['total_guests'] * 0.8)),
                help="Number of children under 12"
            )
            
            data['special_needs_guests'] = st.number_input(
                "Guests with Special Needs",
                min_value=0,
                max_value=data['total_guests'],
                value=st.session_state.form_data.get('special_needs_guests', 0),
                help="Number of guests requiring special accommodations"
            )
        
        # Guest preferences
        st.markdown("#### Guest Preferences")
        data['guest_preferences'] = st.multiselect(
            "Special Considerations",
            options=[
                "Wheelchair accessibility required",
                "Elderly guests (need easy access)",
                "Young children (need child-friendly facilities)",
                "International guests (need translation services)",
                "VIP guests (need special treatment)",
                "Large families (need family seating)",
                "Business associates (need professional atmosphere)"
            ],
            default=st.session_state.form_data.get('guest_preferences', []),
            help="Select any special considerations for your guests"
        )
        
        return data
    
    def render_section_3_budget_priorities(self) -> Dict:
        """Render budget and priorities section"""
        st.subheader("💰 Budget & Priorities")
        
        data = {}
        
        col1, col2 = st.columns(2)
        
        with col1:
            data['total_budget'] = st.number_input(
                "Total Budget ($) *",
                min_value=1000,
                max_value=1000000,
                value=st.session_state.form_data.get('total_budget', 15000),
                step=500,
                help="Total budget available for the event"
            )
            
            data['budget_flexibility'] = st.selectbox(
                "Budget Flexibility",
                options=["Strict - Cannot exceed budget", "Flexible - Can go 10% over", "Very flexible - Can go 20% over"],
                index=0 if not st.session_state.form_data.get('budget_flexibility') else
                      ["Strict - Cannot exceed budget", "Flexible - Can go 10% over", "Very flexible - Can go 20% over"].index(st.session_state.form_data.get('budget_flexibility', "Strict - Cannot exceed budget")),
                help="How flexible is your budget?"
            )
        
        with col2:
            st.markdown("#### Budget Allocation Preferences")
            st.write("Adjust the sliders to indicate how you'd like to allocate your budget:")
            
            # Budget allocation sliders
            venue_pct = st.slider("Venue", 0, 100, st.session_state.form_data.get('venue_budget_pct', 40), help="Percentage for venue costs")
            catering_pct = st.slider("Catering", 0, 100, st.session_state.form_data.get('catering_budget_pct', 35), help="Percentage for catering costs")
            photography_pct = st.slider("Photography", 0, 100, st.session_state.form_data.get('photography_budget_pct', 15), help="Percentage for photography costs")
            other_pct = st.slider("Other Services", 0, 100, st.session_state.form_data.get('other_budget_pct', 10), help="Percentage for other services")
            
            total_pct = venue_pct + catering_pct + photography_pct + other_pct
            
            if total_pct != 100:
                st.warning(f"Budget allocation totals {total_pct}%. Please adjust to equal 100%.")
            
            data['budget_allocation'] = {
                'venue': venue_pct,
                'catering': catering_pct,
                'photography': photography_pct,
                'other': other_pct
            }
        
        # Priority ranking
        st.markdown("#### Priority Ranking")
        st.write("Rank these aspects by importance (1 = most important):")
        
        priorities = ["Cost", "Quality", "Location/Convenience", "Vendor Reputation", "Unique Features"]
        
        priority_cols = st.columns(len(priorities))
        data['priorities'] = {}
        
        for i, priority in enumerate(priorities):
            with priority_cols[i]:
                data['priorities'][priority.lower().replace('/', '_').replace(' ', '_')] = st.selectbox(
                    priority,
                    options=[1, 2, 3, 4, 5],
                    index=st.session_state.form_data.get('priorities', {}).get(priority.lower().replace('/', '_').replace(' ', '_'), i+1) - 1,
                    key=f"priority_{priority}"
                )
        
        return data
    
    def render_section_4_venue_preferences(self) -> Dict:
        """Render venue preferences section"""
        st.subheader("🏛️ Venue Preferences")
        
        data = {}
        
        col1, col2 = st.columns(2)
        
        with col1:
            data['venue_types'] = st.multiselect(
                "Preferred Venue Types",
                options=[
                    "Banquet Hall", "Hotel", "Restaurant", "Outdoor Garden", 
                    "Beach", "Historic Building", "Museum", "Country Club",
                    "Winery", "Barn", "Rooftop", "Private Estate", "Other"
                ],
                default=st.session_state.form_data.get('venue_types', []),
                help="Select all venue types you would consider"
            )
            
            data['venue_style'] = st.multiselect(
                "Venue Style Preferences",
                options=[
                    "Modern", "Traditional", "Rustic", "Elegant", "Casual",
                    "Luxury", "Intimate", "Grand", "Unique", "Classic"
                ],
                default=st.session_state.form_data.get('venue_style', []),
                help="Select preferred venue styles"
            )
            
            data['indoor_outdoor'] = st.selectbox(
                "Indoor/Outdoor Preference",
                options=["No preference", "Indoor only", "Outdoor only", "Indoor with outdoor space", "Outdoor with indoor backup"],
                index=0 if not st.session_state.form_data.get('indoor_outdoor') else
                      ["No preference", "Indoor only", "Outdoor only", "Indoor with outdoor space", "Outdoor with indoor backup"].index(st.session_state.form_data.get('indoor_outdoor', "No preference")),
                help="Indoor/outdoor preference"
            )
        
        with col2:
            data['essential_amenities'] = st.multiselect(
                "Essential Amenities",
                options=[
                    "Parking", "Wheelchair Accessible", "Kitchen Facilities",
                    "Sound System", "Lighting Control", "Air Conditioning",
                    "Bridal Suite", "Dance Floor", "Bar Area", "Outdoor Space",
                    "Photography Restrictions", "Decoration Flexibility"
                ],
                default=st.session_state.form_data.get('essential_amenities', []),
                help="Select amenities that are essential for your event"
            )
            
            data['nice_to_have_amenities'] = st.multiselect(
                "Nice-to-Have Amenities",
                options=[
                    "Ocean/Lake View", "Garden/Landscape", "Historic Character",
                    "Unique Architecture", "Multiple Rooms", "Vendor Flexibility",
                    "Setup/Cleanup Service", "Coordination Services", "Valet Parking"
                ],
                default=st.session_state.form_data.get('nice_to_have_amenities', []),
                help="Select amenities that would be nice but not essential"
            )
        
        # Location preferences
        st.markdown("#### Location Preferences")
        location_col1, location_col2 = st.columns(2)
        
        with location_col1:
            data['max_distance_miles'] = st.number_input(
                "Maximum Distance from City Center (miles)",
                min_value=1,
                max_value=100,
                value=st.session_state.form_data.get('max_distance_miles', 25),
                help="Maximum acceptable distance from the city center"
            )
        
        with location_col2:
            data['transportation_needs'] = st.multiselect(
                "Transportation Considerations",
                options=[
                    "Easy highway access", "Public transportation nearby",
                    "Airport proximity", "Hotel proximity", "Uber/taxi friendly",
                    "Guest shuttle needed", "Parking for large vehicles"
                ],
                default=st.session_state.form_data.get('transportation_needs', []),
                help="Select transportation considerations"
            )
        
        return data
    
    def render_section_5_catering_preferences(self) -> Dict:
        """Render catering preferences section"""
        st.subheader("🍽️ Catering Preferences")
        
        data = {}
        
        col1, col2 = st.columns(2)
        
        with col1:
            data['cuisine_preferences'] = st.multiselect(
                "Cuisine Preferences",
                options=[
                    "American", "Italian", "Mexican", "Asian", "Mediterranean",
                    "French", "Indian", "BBQ", "Seafood", "Vegetarian/Vegan",
                    "Fusion", "Local Specialties", "International Buffet"
                ],
                default=st.session_state.form_data.get('cuisine_preferences', []),
                help="Select preferred cuisine types"
            )
            
            data['service_style'] = st.selectbox(
                "Service Style",
                options=["No preference", "Plated dinner", "Buffet", "Family style", "Cocktail reception", "Food stations", "Mixed service"],
                index=0 if not st.session_state.form_data.get('service_style') else
                      ["No preference", "Plated dinner", "Buffet", "Family style", "Cocktail reception", "Food stations", "Mixed service"].index(st.session_state.form_data.get('service_style', "No preference")),
                help="Preferred service style"
            )
            
            data['meal_courses'] = st.selectbox(
                "Number of Courses",
                options=["Appetizers only", "2 courses", "3 courses", "4+ courses", "Cocktail style"],
                index=0 if not st.session_state.form_data.get('meal_courses') else
                      ["Appetizers only", "2 courses", "3 courses", "4+ courses", "Cocktail style"].index(st.session_state.form_data.get('meal_courses', "3 courses")),
                help="Preferred number of meal courses"
            )
        
        with col2:
            data['dietary_restrictions'] = st.multiselect(
                "Dietary Restrictions & Preferences",
                options=[
                    "Vegetarian options needed", "Vegan options needed",
                    "Gluten-free options needed", "Kosher requirements",
                    "Halal requirements", "Nut allergies", "Dairy-free options",
                    "Low-sodium options", "Diabetic-friendly options", "Children's menu needed"
                ],
                default=st.session_state.form_data.get('dietary_restrictions', []),
                help="Select any dietary restrictions or special requirements"
            )
            
            data['beverage_preferences'] = st.multiselect(
                "Beverage Preferences",
                options=[
                    "Full bar service", "Beer and wine only", "Signature cocktails",
                    "Non-alcoholic beverages only", "Coffee service", "Late night snacks",
                    "Champagne toast", "Welcome drinks", "Specialty beverages"
                ],
                default=st.session_state.form_data.get('beverage_preferences', []),
                help="Select beverage service preferences"
            )
        
        # Special catering requirements
        st.markdown("#### Special Catering Requirements")
        data['catering_special_requirements'] = st.text_area(
            "Special Catering Requirements",
            value=st.session_state.form_data.get('catering_special_requirements', ''),
            height=100,
            help="Describe any special catering requirements, cultural considerations, or specific requests",
            max_chars=1000
        )
        
        return data
    
    def render_section_6_photography_services(self) -> Dict:
        """Render photography and services section"""
        st.subheader("📸 Photography & Additional Services")
        
        data = {}
        
        # Photography section
        st.markdown("#### Photography Requirements")
        photo_col1, photo_col2 = st.columns(2)
        
        with photo_col1:
            data['photography_needed'] = st.checkbox(
                "Photography Services Needed",
                value=st.session_state.form_data.get('photography_needed', True),
                help="Check if you need photography services"
            )
            
            if data['photography_needed']:
                data['photography_style'] = st.multiselect(
                    "Photography Style Preferences",
                    options=[
                        "Traditional/Classic", "Photojournalistic", "Artistic/Creative",
                        "Candid/Natural", "Formal Portraits", "Black & White",
                        "Vintage Style", "Modern/Contemporary"
                    ],
                    default=st.session_state.form_data.get('photography_style', []),
                    help="Select preferred photography styles"
                )
                
                data['photography_coverage'] = st.multiselect(
                    "Photography Coverage Needed",
                    options=[
                        "Pre-event preparation", "Ceremony", "Reception",
                        "Cocktail hour", "Dancing", "Cake cutting",
                        "Speeches/Toasts", "Guest interactions", "Detail shots"
                    ],
                    default=st.session_state.form_data.get('photography_coverage', ["Ceremony", "Reception"]),
                    help="Select what parts of the event need photography coverage"
                )
        
        with photo_col2:
            data['videography_needed'] = st.checkbox(
                "Videography Services Needed",
                value=st.session_state.form_data.get('videography_needed', False),
                help="Check if you need videography services"
            )
            
            if data['videography_needed']:
                data['videography_style'] = st.multiselect(
                    "Videography Style",
                    options=[
                        "Cinematic", "Documentary", "Traditional", "Highlight reel",
                        "Live streaming", "Drone footage", "Multiple angles"
                    ],
                    default=st.session_state.form_data.get('videography_style', []),
                    help="Select preferred videography styles"
                )
        
        # Makeup and beauty services
        st.markdown("#### Beauty & Styling Services")
        beauty_col1, beauty_col2 = st.columns(2)
        
        with beauty_col1:
            data['makeup_needed'] = st.checkbox(
                "Makeup Services Needed",
                value=st.session_state.form_data.get('makeup_needed', False),
                help="Check if you need professional makeup services"
            )
            
            if data['makeup_needed']:
                data['makeup_style'] = st.multiselect(
                    "Makeup Style Preferences",
                    options=[
                        "Natural/Subtle", "Glamorous", "Classic", "Modern",
                        "Airbrush", "Traditional", "Bold/Dramatic", "Vintage"
                    ],
                    default=st.session_state.form_data.get('makeup_style', []),
                    help="Select preferred makeup styles"
                )
                
                data['makeup_services'] = st.multiselect(
                    "Makeup Services Needed",
                    options=[
                        "Bridal makeup", "Bridesmaids makeup", "Mother of bride/groom",
                        "Flower girl makeup", "Touch-up services", "Hair styling",
                        "Trial session", "On-site services"
                    ],
                    default=st.session_state.form_data.get('makeup_services', []),
                    help="Select specific makeup services needed"
                )
        
        with beauty_col2:
            # Additional services
            st.markdown("#### Other Services")
            data['additional_services'] = st.multiselect(
                "Additional Services Needed",
                options=[
                    "DJ/Music", "Live band", "Entertainment", "Florist",
                    "Decorator", "Wedding planner", "Transportation",
                    "Security", "Childcare", "Valet parking", "Coat check"
                ],
                default=st.session_state.form_data.get('additional_services', []),
                help="Select any additional services you might need"
            )
        
        # Service requirements
        data['service_requirements'] = st.text_area(
            "Special Service Requirements",
            value=st.session_state.form_data.get('service_requirements', ''),
            height=100,
            help="Describe any special requirements for photography, makeup, or other services",
            max_chars=1000
        )
        
        return data
    
    def render_section_7_client_vision(self) -> Dict:
        """Render client vision and theme section"""
        st.subheader("✨ Client Vision & Theme")
        
        data = {}
        
        col1, col2 = st.columns(2)
        
        with col1:
            data['event_theme'] = st.text_input(
                "Event Theme",
                value=st.session_state.form_data.get('event_theme', ''),
                help="Main theme or concept for the event (e.g., 'Rustic Elegance', 'Modern Minimalist')"
            )
            
            data['color_scheme'] = st.text_input(
                "Color Scheme",
                value=st.session_state.form_data.get('color_scheme', ''),
                help="Primary colors for the event (e.g., 'Navy and Gold', 'Blush and Sage')"
            )
            
            data['style_preferences'] = st.multiselect(
                "Style Preferences",
                options=[
                    "Elegant", "Casual", "Formal", "Rustic", "Modern",
                    "Vintage", "Bohemian", "Classic", "Romantic", "Fun/Playful",
                    "Sophisticated", "Unique/Creative", "Traditional", "Contemporary"
                ],
                default=st.session_state.form_data.get('style_preferences', []),
                help="Select styles that match your vision"
            )
        
        with col2:
            data['atmosphere_goals'] = st.multiselect(
                "Desired Atmosphere",
                options=[
                    "Intimate and cozy", "Grand and impressive", "Fun and energetic",
                    "Elegant and refined", "Relaxed and casual", "Romantic and dreamy",
                    "Professional and polished", "Unique and memorable", "Traditional and timeless"
                ],
                default=st.session_state.form_data.get('atmosphere_goals', []),
                help="Select the atmosphere you want to create"
            )
            
            data['inspiration_sources'] = st.text_input(
                "Inspiration Sources",
                value=st.session_state.form_data.get('inspiration_sources', ''),
                help="Any specific inspirations (Pinterest boards, movies, other events, etc.)"
            )
        
        # Detailed vision
        st.markdown("#### Detailed Vision")
        data['client_vision'] = st.text_area(
            "Describe Your Vision",
            value=st.session_state.form_data.get('client_vision', ''),
            height=150,
            help="Describe your overall vision for the event. Include any specific ideas, must-haves, or things you want to avoid.",
            max_chars=2000
        )
        
        data['special_traditions'] = st.text_area(
            "Special Traditions or Cultural Elements",
            value=st.session_state.form_data.get('special_traditions', ''),
            height=100,
            help="Describe any cultural traditions, family customs, or special elements to incorporate",
            max_chars=1000
        )
        
        data['must_haves'] = st.text_area(
            "Must-Have Elements",
            value=st.session_state.form_data.get('must_haves', ''),
            height=100,
            help="List any specific elements that are absolutely essential for your event",
            max_chars=1000
        )
        
        data['avoid_elements'] = st.text_area(
            "Elements to Avoid",
            value=st.session_state.form_data.get('avoid_elements', ''),
            height=100,
            help="List any elements, styles, or approaches you want to avoid",
            max_chars=1000
        )
        
        return data
    
    def validate_current_section(self, section_data: Dict) -> Tuple[bool, List[str]]:
        """Validate the current section data"""
        current_step = st.session_state.form_step
        errors = []
        
        if current_step == 1:  # Basic Information
            errors.extend(EventPlanValidator.validate_basic_info(section_data))
        elif current_step == 2:  # Guest Information
            errors.extend(EventPlanValidator.validate_guest_info(section_data))
        elif current_step == 3:  # Budget & Priorities
            errors.extend(EventPlanValidator.validate_budget_info(section_data))
            
            # Additional validation for budget allocation
            if 'budget_allocation' in section_data:
                total_pct = sum(section_data['budget_allocation'].values())
                if abs(total_pct - 100) > 1:
                    errors.append("Budget allocation percentages must add up to 100%")
        
        # For other sections, we mainly check text length limits
        elif current_step >= 4:
            errors.extend(EventPlanValidator.validate_preferences(section_data))
        
        return len(errors) == 0, errors
    
    def render_navigation_buttons(self, section_data: Dict):
        """Render navigation buttons for the form"""
        current_step = st.session_state.form_step
        total_steps = len(self.sections)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if current_step > 1:
                if st.button("← Previous", use_container_width=True, key="form_nav_previous"):
                    # Save current section data before going back
                    st.session_state.form_data.update(section_data)
                    st.session_state.form_step -= 1
                    st.rerun()
        
        with col3:
            if current_step < total_steps:
                if st.button("Next →", use_container_width=True, key="form_nav_next"):
                    # Validate current section
                    is_valid, errors = self.validate_current_section(section_data)
                    
                    if is_valid:
                        # Save data and move to next step
                        st.session_state.form_data.update(section_data)
                        st.session_state.form_step += 1
                        st.session_state.form_errors = []
                        st.rerun()
                    else:
                        st.session_state.form_errors = errors
                        for error in errors:
                            show_error(error)
            else:
                # Final step - show submit button
                if st.button("Submit Event Plan", use_container_width=True, type="primary", key="form_nav_submit"):
                    # Validate current section and complete form
                    is_valid, errors = self.validate_current_section(section_data)
                    
                    if is_valid:
                        # Save final section data
                        st.session_state.form_data.update(section_data)
                        
                        # Validate complete form
                        complete_valid, complete_errors = EventPlanValidator.validate_complete_form(st.session_state.form_data)
                        
                        if complete_valid:
                            st.session_state.form_completed = True
                            st.session_state.form_errors = []
                            show_success("Event plan submitted successfully!")
                            return True
                        else:
                            st.session_state.form_errors = complete_errors
                            for error in complete_errors:
                                show_error(error)
                    else:
                        st.session_state.form_errors = errors
                        for error in errors:
                            show_error(error)
        
        with col2:
            # Show section jump buttons
            if st.button("Jump to Section...", use_container_width=True, key="form_nav_jump"):
                st.session_state.show_section_selector = not st.session_state.get('show_section_selector', False)
        
        # Section selector
        if st.session_state.get('show_section_selector', False):
            selected_section = st.selectbox(
                "Jump to section:",
                options=list(range(1, total_steps + 1)),
                format_func=lambda x: f"{x}. {self.sections[x-1]}",
                index=current_step - 1
            )
            
            if st.button("Go to Section", key="form_nav_go_to_section"):
                # Save current data before jumping
                st.session_state.form_data.update(section_data)
                st.session_state.form_step = selected_section
                st.session_state.show_section_selector = False
                st.rerun()
        
        return False
    
    def render_form(self) -> bool:
        """Render the complete multi-section form"""
        # Show progress indicator
        self.render_progress_indicator()
        
        # Show any validation errors
        if st.session_state.form_errors:
            st.error("Please fix the following errors:")
            for error in st.session_state.form_errors:
                st.write(f"• {error}")
        
        st.divider()
        
        # Render current section
        current_step = st.session_state.form_step
        section_data = {}
        
        if current_step == 1:
            section_data = self.render_section_1_basic_info()
        elif current_step == 2:
            section_data = self.render_section_2_guest_info()
        elif current_step == 3:
            section_data = self.render_section_3_budget_priorities()
        elif current_step == 4:
            section_data = self.render_section_4_venue_preferences()
        elif current_step == 5:
            section_data = self.render_section_5_catering_preferences()
        elif current_step == 6:
            section_data = self.render_section_6_photography_services()
        elif current_step == 7:
            section_data = self.render_section_7_client_vision()
        
        st.divider()
        
        # Render navigation buttons and handle submission
        return self.render_navigation_buttons(section_data)