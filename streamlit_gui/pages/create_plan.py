"""
Create Event Plan page - Comprehensive event planning form interface
"""
import streamlit as st
from datetime import datetime
import json
from typing import Dict, Any

from components.forms import EventPlanningForm
from components.api_client import APIClient
from utils.helpers import show_error, show_success, show_info, show_warning
from utils.config import config

class CreatePlanPage:
    """Create Event Plan page handler"""
    
    def __init__(self):
        self.form = EventPlanningForm()
        self.api_client = APIClient()
    
    def reset_form(self):
        """Reset the form to initial state"""
        keys_to_reset = [
            'form_data', 'form_step', 'form_completed', 'form_errors',
            'show_section_selector'
        ]
        
        for key in keys_to_reset:
            if key in st.session_state:
                del st.session_state[key]
        
        # Reinitialize form
        st.session_state.form_data = {}
        st.session_state.form_step = 1
        st.session_state.form_completed = False
        st.session_state.form_errors = []
        
        show_info("Form has been reset")
        st.rerun()
    
    def save_form_draft(self):
        """Save form as draft to session state"""
        if st.session_state.form_data:
            # Add metadata
            draft_data = {
                'form_data': st.session_state.form_data,
                'form_step': st.session_state.form_step,
                'saved_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            st.session_state.form_draft = draft_data
            show_success("Form draft saved successfully!")
        else:
            show_warning("No form data to save")
    
    def load_form_draft(self):
        """Load form draft from session state"""
        if 'form_draft' in st.session_state:
            draft = st.session_state.form_draft
            st.session_state.form_data = draft.get('form_data', {})
            st.session_state.form_step = draft.get('form_step', 1)
            show_success("Form draft loaded successfully!")
            st.rerun()
        else:
            show_warning("No saved draft found")
    
    def export_form_data(self):
        """Export form data as JSON"""
        if st.session_state.form_data:
            export_data = {
                'form_data': st.session_state.form_data,
                'exported_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            json_str = json.dumps(export_data, indent=2, default=str)
            
            st.download_button(
                label="📥 Download Form Data (JSON)",
                data=json_str,
                file_name=f"event_plan_form_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                help="Download your form data as a JSON file for backup"
            )
        else:
            show_warning("No form data to export")
    
    def import_form_data(self):
        """Import form data from JSON file"""
        uploaded_file = st.file_uploader(
            "Upload Form Data (JSON)",
            type=['json'],
            help="Upload a previously exported form data file"
        )
        
        if uploaded_file is not None:
            try:
                import_data = json.load(uploaded_file)
                
                if 'form_data' in import_data:
                    st.session_state.form_data = import_data['form_data']
                    st.session_state.form_step = import_data.get('form_step', 1)
                    show_success("Form data imported successfully!")
                    st.rerun()
                else:
                    show_error("Invalid file format - missing form_data")
            except json.JSONDecodeError:
                show_error("Invalid JSON file")
            except Exception as e:
                show_error(f"Error importing file: {str(e)}")
    
    def prepare_api_request(self, form_data: Dict) -> Dict:
        """Prepare form data for API submission - matches backend EventPlanRequest schema"""
        # Build client vision from multiple fields
        vision_parts = []
        if form_data.get('client_vision'):
            vision_parts.append(form_data['client_vision'])
        if form_data.get('event_theme'):
            vision_parts.append(f"Theme: {form_data['event_theme']}")
        if form_data.get('color_scheme'):
            vision_parts.append(f"Colors: {form_data['color_scheme']}")
        if form_data.get('must_haves'):
            vision_parts.append(f"Must-haves: {form_data['must_haves']}")
        
        client_vision = ". ".join(vision_parts) if vision_parts else "Modern elegant event"
        
        # Build guest count (required field)
        total_guests = form_data.get('total_guests', 100)
        guest_count = {
            "total": total_guests,
            "Reception": form_data.get('reception_guests', total_guests),
            "Ceremony": form_data.get('ceremony_guests', total_guests)
        }
        
        # Transform to match API schema (camelCase)
        api_request = {
            # Required fields
            'clientName': form_data.get('client_name', 'Unknown Client'),
            'guestCount': guest_count,
            'clientVision': client_vision,
            
            # Optional fields
            'venuePreferences': form_data.get('venue_types', []),
            'essentialVenueAmenities': form_data.get('essential_amenities', []),
            'budget': form_data.get('total_budget'),
            'eventDate': form_data.get('event_date').isoformat() if form_data.get('event_date') else None,
            'location': form_data.get('location'),
            
            # Nested objects
            'decorationAndAmbiance': {
                'theme': form_data.get('event_theme', ''),
                'colorScheme': form_data.get('color_scheme', ''),
                'stylePreferences': form_data.get('style_preferences', []),
                'atmosphereGoals': form_data.get('atmosphere_goals', [])
            } if any([form_data.get('event_theme'), form_data.get('color_scheme')]) else None,
            
            'foodAndCatering': {
                'cuisinePreferences': form_data.get('cuisine_preferences', []),
                'dietaryRestrictions': form_data.get('dietary_restrictions', []),
                'serviceStyle': form_data.get('service_style', ''),
                'specialRequirements': form_data.get('catering_special_requirements', '')
            } if any([form_data.get('cuisine_preferences'), form_data.get('dietary_restrictions')]) else None,
            
            'additionalRequirements': {
                'photographyNeeded': form_data.get('photography_needed', False),
                'photographyStyle': form_data.get('photography_style', []),
                'videographyNeeded': form_data.get('videography_needed', False),
                'makeupNeeded': form_data.get('makeup_needed', False),
                'makeupStyle': form_data.get('makeup_style', []),
                'additionalServices': form_data.get('additional_services', []),
                'specialTraditions': form_data.get('special_traditions', ''),
                'transportationNeeds': form_data.get('transportation_needs', [])
            } if any([form_data.get('photography_needed'), form_data.get('videography_needed')]) else None
        }
        
        # Remove None values and empty strings/lists
        cleaned_request = {}
        for key, value in api_request.items():
            if value is not None and value != '' and value != []:
                cleaned_request[key] = value
        
        return cleaned_request
    
    async def submit_to_api(self, form_data: Dict) -> bool:
        """Submit form data to the API"""
        try:
            # Prepare API request
            api_request = self.prepare_api_request(form_data)
            
            # Show submission progress
            with st.spinner("Submitting event plan to API..."):
                # Call the API
                response = await self.api_client.create_plan_async(api_request)
                
                if response and 'plan_id' in response:
                    # Store plan information in session state
                    st.session_state.current_plan_id = response['plan_id']
                    st.session_state.plan_data = response
                    st.session_state.plan_status = response.get('status', 'submitted')
                    
                    show_success(f"Event plan submitted successfully! Plan ID: {response['plan_id']}")
                    
                    # Clear form data after successful submission
                    st.session_state.form_completed = True
                    
                    return True
                else:
                    show_error("API response missing plan_id")
                    return False
                    
        except Exception as e:
            show_error(f"Error submitting to API: {str(e)}")
            if config.is_development():
                st.exception(e)
            return False
    
    def render_form_actions(self):
        """Render form action buttons"""
        st.markdown("### Form Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 Save Draft", use_container_width=True, help="Save current form progress", key="create_save_draft"):
                self.save_form_draft()
        
        with col2:
            if st.button("📂 Load Draft", use_container_width=True, help="Load previously saved draft", key="create_load_draft"):
                self.load_form_draft()
        
        with col3:
            if st.button("🔄 Reset Form", use_container_width=True, help="Clear all form data and start over", key="create_reset_form"):
                if st.session_state.get('confirm_reset'):
                    self.reset_form()
                else:
                    st.session_state.confirm_reset = True
                    show_warning("Click again to confirm form reset")
        
        with col4:
            self.export_form_data()
        
        # Import section
        with st.expander("📤 Import Form Data"):
            self.import_form_data()
    
    def render_form_summary(self):
        """Render a summary of the completed form"""
        if not st.session_state.form_data:
            return
        
        st.markdown("### Form Summary")
        
        form_data = st.session_state.form_data
        
        # Basic info summary
        with st.expander("📋 Basic Information", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Client:** {form_data.get('client_name', 'N/A')}")
                st.write(f"**Event Type:** {form_data.get('event_type', 'N/A')}")
                st.write(f"**Date:** {form_data.get('event_date', 'N/A')}")
            with col2:
                st.write(f"**Location:** {form_data.get('location', 'N/A')}")
                st.write(f"**Guests:** {form_data.get('total_guests', 'N/A')}")
                st.write(f"**Budget:** ${form_data.get('total_budget', 0):,.2f}")
        
        # Preferences summary
        with st.expander("🎯 Key Preferences"):
            if form_data.get('venue_types'):
                st.write(f"**Venue Types:** {', '.join(form_data['venue_types'])}")
            if form_data.get('cuisine_preferences'):
                st.write(f"**Cuisine:** {', '.join(form_data['cuisine_preferences'])}")
            if form_data.get('style_preferences'):
                st.write(f"**Style:** {', '.join(form_data['style_preferences'])}")
        
        # Services summary
        with st.expander("📸 Services"):
            services = []
            if form_data.get('photography_needed'):
                services.append("Photography")
            if form_data.get('videography_needed'):
                services.append("Videography")
            if form_data.get('makeup_needed'):
                services.append("Makeup")
            if form_data.get('additional_services'):
                services.extend(form_data['additional_services'])
            
            if services:
                st.write(f"**Services Needed:** {', '.join(services)}")
            else:
                st.write("**Services:** None specified")
        
        # Vision summary
        if form_data.get('client_vision'):
            with st.expander("✨ Client Vision"):
                st.write(form_data['client_vision'])
    
    def render_success_actions(self):
        """Render actions after successful form submission"""
        st.markdown("### What's Next?")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Monitor Progress", use_container_width=True, type="primary", key="create_monitor_progress"):
                # Navigate to plan status page
                st.session_state.current_page = 'plan_status'
                st.rerun()
        
        with col2:
            if st.button("➕ Create Another Plan", use_container_width=True, key="create_another_plan"):
                # Reset form for new plan
                self.reset_form()
        
        with col3:
            if st.button("🏠 Go to Home", use_container_width=True, key="create_go_home"):
                # Navigate to home page
                st.session_state.current_page = 'home'
                st.rerun()
        
        # Show current plan info
        if st.session_state.current_plan_id:
            st.info(f"✅ Your event plan has been submitted with ID: **{st.session_state.current_plan_id}**")
            st.write("You can monitor the planning progress in the 'Plan Status' section.")
    
    def render(self):
        """Render the create plan page"""
        st.header("➕ Create New Event Plan")
        
        # Check if form is completed
        if st.session_state.get('form_completed', False):
            st.success("🎉 Event Plan Submitted Successfully!")
            
            # Show form summary
            self.render_form_summary()
            
            # Show next actions
            self.render_success_actions()
            
            return
        
        # Show introduction
        st.markdown("""
        Welcome to the Event Planning Form! This comprehensive form will gather all the information 
        needed to create your perfect event plan. The form is divided into 7 sections:
        
        1. **Basic Information** - Event details and contact info
        2. **Guest Information** - Guest count and demographics  
        3. **Budget & Priorities** - Budget allocation and priorities
        4. **Venue Preferences** - Venue types and requirements
        5. **Catering Preferences** - Food and beverage preferences
        6. **Photography & Services** - Photography and additional services
        7. **Client Vision & Theme** - Your vision and style preferences
        
        You can navigate between sections, save drafts, and return to complete the form later.
        """)
        
        # Show form actions
        self.render_form_actions()
        
        st.divider()
        
        # Render the main form
        form_submitted = self.form.render_form()
        
        # Handle form submission
        if form_submitted:
            # Show submission confirmation
            st.balloons()
            
            # Attempt to submit to API
            if st.button("🚀 Submit to Event Planning System", type="primary", use_container_width=True, key="create_submit_plan"):
                # Use asyncio to handle async API call
                import asyncio
                
                try:
                    # Create new event loop if none exists
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    # Submit to API
                    success = loop.run_until_complete(self.submit_to_api(st.session_state.form_data))
                    
                    if success:
                        st.rerun()
                    
                except Exception as e:
                    show_error(f"Error during submission: {str(e)}")
                    if config.is_development():
                        st.exception(e)
            
            # Show form summary while waiting for API submission
            st.markdown("---")
            st.markdown("### 📋 Review Your Event Plan")
            self.render_form_summary()

def render_create_plan_page():
    """Main function to render the create plan page"""
    page = CreatePlanPage()
    page.render()

# For compatibility with the main app
if __name__ == "__main__":
    render_create_plan_page()