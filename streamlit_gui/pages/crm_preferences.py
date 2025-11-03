"""
CRM Preferences Page - Communication Preferences Management

Allows clients to manage their communication preferences including channels,
timezone, quiet hours, and opt-out settings.
"""

import streamlit as st
from components.crm_preferences import CRMPreferencesComponent
from utils.helpers import show_warning, show_info, init_session_state


def render_crm_preferences_page():
    """Main rendering function for CRM preferences page"""
    
    st.header("💬 Communication Preferences")
    st.markdown("Manage how and when you receive updates about your event planning.")
    
    # Initialize session state for client_id
    init_session_state('client_id', '')
    init_session_state('current_plan_id', None)
    
    # Get client ID from session state or plan data
    client_id = st.session_state.get('client_id', '')
    
    # If we have a current plan, try to get client ID from plan data
    if not client_id and st.session_state.get('current_plan_id'):
        plan_data = st.session_state.get('plan_data', {})
        client_id = plan_data.get('client_id', '')
    
    # Client ID input section
    with st.expander("🔑 Client Identification", expanded=not bool(client_id)):
        st.markdown("""
        Enter your Client ID to manage your communication preferences.
        In production, this would be automatically populated from your authentication session.
        """)
        
        input_client_id = st.text_input(
            "Client ID",
            value=client_id,
            help="Enter your client ID (e.g., email address or unique identifier)",
            key="client_id_input"
        )
        
        if input_client_id and input_client_id != client_id:
            st.session_state.client_id = input_client_id
            client_id = input_client_id
            st.rerun()
    
    # Main content
    if not client_id:
        show_warning("Please enter your Client ID above to manage preferences.")
        
        st.markdown("---")
        st.markdown("### 📬 About Communication Preferences")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **📧 Email**
            
            Receive detailed updates with:
            - Event planning progress
            - Vendor recommendations
            - Budget summaries
            - Attachments and documents
            """)
        
        with col2:
            st.markdown("""
            **📱 SMS**
            
            Get quick notifications for:
            - Urgent updates
            - Time-sensitive decisions
            - Appointment reminders
            - Status changes
            """)
        
        with col3:
            st.markdown("""
            **💬 WhatsApp**
            
            Enjoy rich media messages:
            - Images and videos
            - Interactive messages
            - Quick replies
            - Group coordination
            """)
        
        st.markdown("---")
        
        with st.expander("ℹ️ How It Works"):
            st.markdown("""
            **Managing Your Preferences**
            
            1. **Select Channels**: Choose your preferred communication methods
            2. **Set Timezone**: Ensure messages arrive at the right time
            3. **Configure Quiet Hours**: No non-urgent messages during sleep
            4. **Opt-Out Options**: Temporarily disable specific channels
            
            All changes take effect immediately and are saved securely.
            """)
        
        return
    
    # Render the preferences component
    component = CRMPreferencesComponent()
    component.render(client_id)
    
    # Additional information sections
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("🔒 Privacy & Data Protection"):
            st.markdown("""
            **Your Privacy Matters**
            
            - Your preferences are encrypted and stored securely
            - We comply with GDPR and CAN-SPAM regulations
            - You can request data deletion at any time
            - Opt-out requests are honored immediately
            - No data is shared with third parties without consent
            
            For privacy concerns, contact: privacy@eventplanning.com
            """)
    
    with col2:
        with st.expander("📞 Contact Support"):
            st.markdown("""
            **Need Help?**
            
            - **Email**: support@eventplanning.com
            - **Phone**: 1-800-EVENT-PLAN
            - **Live Chat**: Available 9 AM - 6 PM EST
            - **Response Time**: Within 24 hours
            
            For technical issues with preferences, please include your Client ID.
            """)
    
    # Tips section
    with st.expander("💡 Tips for Best Experience"):
        st.markdown("""
        **Optimize Your Communication Experience**
        
        - ✅ Enable at least one channel to receive important updates
        - ⏰ Set your correct timezone for timely notifications
        - 🌙 Configure quiet hours to avoid late-night messages
        - 📧 Use email for detailed information and documents
        - 📱 Use SMS for urgent, time-sensitive updates
        - 💬 Use WhatsApp for rich media and interactive content
        - 🔄 Review and update preferences as your needs change
        """)


# For standalone execution
if __name__ == "__main__":
    st.set_page_config(
        page_title="Communication Preferences - Event Planning Agent",
        page_icon="📬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    render_crm_preferences_page()
