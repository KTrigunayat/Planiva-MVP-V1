"""
Streamlit GUI Components for CRM Client Preference Management

Provides interactive UI for clients to manage their communication preferences.
"""

import streamlit as st
import logging
from typing import Dict, Any, List, Optional
from datetime import time
import pytz

from components.api_client import api_client, APIError
from components.api_wrapper import api_wrapper
from utils.helpers import show_error, show_success, show_warning, show_info
from utils.error_handling import error_handler, validate_form_field, Validators

logger = logging.getLogger(__name__)


class CRMPreferencesComponent:
    """
    Streamlit component for managing client communication preferences.
    
    Features:
    - Channel selection (Email, SMS, WhatsApp)
    - Timezone configuration
    - Quiet hours settings
    - Opt-out management
    - Language preference
    """
    
    def __init__(self):
        """Initialize preferences component."""
        self.api_client = api_client
    
    def render(self, client_id: str) -> None:
        """
        Render the preferences management UI.
        
        Args:
            client_id: Client identifier
        """
        st.header("📬 Communication Preferences")
        st.markdown("Manage how and when you receive updates about your event planning.")
        
        # Load current preferences using API wrapper with error handling
        current_prefs = api_wrapper.get_preferences_safe(client_id, show_loading=True)
        
        if current_prefs is None:
            # Error already displayed by API wrapper
            if st.button("🔄 Retry", key="retry_load_prefs", type="primary"):
                st.rerun()
            return
        
        # Create form for preference updates
        with st.form("preferences_form"):
            st.subheader("Preferred Communication Channels")
            st.markdown("Select your preferred ways to receive updates:")
            
            # Channel selection
            col1, col2, col3 = st.columns(3)
            
            with col1:
                email_enabled = st.checkbox(
                    "📧 Email",
                    value="email" in current_prefs.get("preferred_channels", []),
                    help="Receive detailed updates via email"
                )
            
            with col2:
                sms_enabled = st.checkbox(
                    "📱 SMS",
                    value="sms" in current_prefs.get("preferred_channels", []),
                    help="Receive quick notifications via text message"
                )
            
            with col3:
                whatsapp_enabled = st.checkbox(
                    "💬 WhatsApp",
                    value="whatsapp" in current_prefs.get("preferred_channels", []),
                    help="Receive updates via WhatsApp"
                )
            
            st.divider()
            
            # Opt-out settings
            st.subheader("Opt-Out Settings")
            st.markdown("Temporarily disable specific channels:")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                opt_out_email = st.checkbox(
                    "Opt out of Email",
                    value=current_prefs.get("opt_out_email", False),
                    help="Stop receiving emails (overrides preference above)"
                )
            
            with col2:
                opt_out_sms = st.checkbox(
                    "Opt out of SMS",
                    value=current_prefs.get("opt_out_sms", False),
                    help="Stop receiving SMS messages"
                )
            
            with col3:
                opt_out_whatsapp = st.checkbox(
                    "Opt out of WhatsApp",
                    value=current_prefs.get("opt_out_whatsapp", False),
                    help="Stop receiving WhatsApp messages"
                )
            
            st.divider()
            
            # Timezone selection
            st.subheader("⏰ Timezone & Quiet Hours")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Get all available timezones
                all_timezones = pytz.all_timezones
                
                # Common timezones for quick access
                common_timezones = [
                    "UTC",
                    "America/New_York",
                    "America/Chicago",
                    "America/Denver",
                    "America/Los_Angeles",
                    "America/Toronto",
                    "America/Mexico_City",
                    "Europe/London",
                    "Europe/Paris",
                    "Europe/Berlin",
                    "Europe/Moscow",
                    "Asia/Tokyo",
                    "Asia/Shanghai",
                    "Asia/Hong_Kong",
                    "Asia/Singapore",
                    "Asia/Dubai",
                    "Asia/Kolkata",
                    "Australia/Sydney",
                    "Australia/Melbourne",
                    "Pacific/Auckland"
                ]
                
                current_tz = current_prefs.get("timezone", "UTC")
                
                # Use common timezones by default, with option to show all
                show_all_tz = st.checkbox("Show all timezones", value=False, key="show_all_timezones")
                
                timezone_options = all_timezones if show_all_tz else common_timezones
                
                # Ensure current timezone is in the list
                if current_tz not in timezone_options:
                    timezone_options = [current_tz] + list(timezone_options)
                
                timezone = st.selectbox(
                    "Your Timezone",
                    options=timezone_options,
                    index=timezone_options.index(current_tz) if current_tz in timezone_options else 0,
                    help="Select your local timezone for optimal message timing"
                )
            
            with col2:
                language = st.selectbox(
                    "Language Preference",
                    options=["en", "es", "fr", "de", "hi", "zh"],
                    index=["en", "es", "fr", "de", "hi", "zh"].index(
                        current_prefs.get("language_preference", "en")
                    ),
                    format_func=lambda x: {
                        "en": "English",
                        "es": "Español",
                        "fr": "Français",
                        "de": "Deutsch",
                        "hi": "हिन्दी",
                        "zh": "中文"
                    }.get(x, x),
                    help="Preferred language for communications"
                )
            
            # Quiet hours
            st.markdown("**Quiet Hours** (No non-urgent messages during this time)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                quiet_start = st.time_input(
                    "Start Time",
                    value=self._parse_time(current_prefs.get("quiet_hours_start", "22:00")),
                    help="Start of quiet hours (e.g., 10:00 PM)"
                )
            
            with col2:
                quiet_end = st.time_input(
                    "End Time",
                    value=self._parse_time(current_prefs.get("quiet_hours_end", "08:00")),
                    help="End of quiet hours (e.g., 8:00 AM)"
                )
            
            st.divider()
            
            # Submit button
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col2:
                submitted = st.form_submit_button(
                    "💾 Save Preferences",
                    use_container_width=True,
                    type="primary"
                )
            
            if submitted:
                # Build preferred channels list
                preferred_channels = []
                if email_enabled:
                    preferred_channels.append("email")
                if sms_enabled:
                    preferred_channels.append("sms")
                if whatsapp_enabled:
                    preferred_channels.append("whatsapp")
                
                # Validate form data with enhanced error handling
                validation_errors = []
                
                # Validate at least one channel is selected
                if not preferred_channels:
                    error_handler.show_validation_error(
                        "Communication Channels",
                        "Please select at least one communication channel."
                    )
                    validation_errors.append("channels")
                
                # Validate that if a channel is opted out, it shouldn't be in preferred channels
                if opt_out_email and "email" in preferred_channels:
                    error_handler.show_validation_error(
                        "Email Settings",
                        "Email is opted out but also selected as preferred. Please uncheck one."
                    )
                    validation_errors.append("email")
                if opt_out_sms and "sms" in preferred_channels:
                    error_handler.show_validation_error(
                        "SMS Settings",
                        "SMS is opted out but also selected as preferred. Please uncheck one."
                    )
                    validation_errors.append("sms")
                if opt_out_whatsapp and "whatsapp" in preferred_channels:
                    error_handler.show_validation_error(
                        "WhatsApp Settings",
                        "WhatsApp is opted out but also selected as preferred. Please uncheck one."
                    )
                    validation_errors.append("whatsapp")
                
                # Validate timezone
                if timezone not in pytz.all_timezones:
                    error_handler.show_validation_error(
                        "Timezone",
                        "Invalid timezone selected."
                    )
                    validation_errors.append("timezone")
                
                # Validate quiet hours
                if quiet_start == quiet_end:
                    error_handler.show_validation_error(
                        "Quiet Hours",
                        "Start and end times cannot be the same."
                    )
                    validation_errors.append("quiet_hours")
                
                # Stop if there are validation errors
                if validation_errors:
                    st.stop()
                
                # Build preferences payload
                preferences_data = {
                    "client_id": client_id,
                    "preferred_channels": preferred_channels,
                    "timezone": timezone,
                    "quiet_hours_start": quiet_start.strftime("%H:%M"),
                    "quiet_hours_end": quiet_end.strftime("%H:%M"),
                    "opt_out_email": opt_out_email,
                    "opt_out_sms": opt_out_sms,
                    "opt_out_whatsapp": opt_out_whatsapp,
                    "language_preference": language
                }
                
                # Save preferences using API wrapper with error handling
                result = api_wrapper.update_preferences_safe(preferences_data, show_loading=True)
                
                if result:
                    # Success message already shown by API wrapper
                    st.balloons()
                    # Reload preferences to show updated values
                    st.rerun()
                else:
                    # Error already displayed by API wrapper
                    pass
        
        # Display current effective settings
        self._display_effective_settings(current_prefs)
    
    def _load_preferences(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Load client preferences from API.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Preferences dictionary or None on error
        """
        try:
            preferences = self.api_client.get_preferences(client_id)
            return preferences
        except APIError as e:
            logger.error(f"Error loading preferences: {e.message}")
            # Return default preferences if not found
            if e.status_code == 404:
                return {
                    "client_id": client_id,
                    "preferred_channels": ["email"],
                    "timezone": "UTC",
                    "quiet_hours_start": "22:00",
                    "quiet_hours_end": "08:00",
                    "opt_out_email": False,
                    "opt_out_sms": False,
                    "opt_out_whatsapp": False,
                    "language_preference": "en",
                    "available_channels": []
                }
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading preferences: {e}")
            return None
    
    def _save_preferences(self, preferences_data: Dict[str, Any]) -> bool:
        """
        Save client preferences via API.
        
        Args:
            preferences_data: Preferences to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.api_client.update_preferences(preferences_data)
            logger.info(f"Preferences saved for client {preferences_data['client_id']}")
            return True
        except APIError as e:
            logger.error(f"Error saving preferences: {e.message}")
            if e.response_data:
                show_error(f"Failed to save: {e.response_data.get('detail', e.message)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving preferences: {e}")
            return False
    
    def _parse_time(self, time_str: str) -> time:
        """
        Parse time string to time object.
        
        Args:
            time_str: Time string in HH:MM format
            
        Returns:
            time object
        """
        try:
            parts = time_str.split(":")
            return time(hour=int(parts[0]), minute=int(parts[1]))
        except (ValueError, IndexError):
            return time(hour=22, minute=0)
    
    def _display_effective_settings(self, preferences: Dict[str, Any]) -> None:
        """
        Display effective communication settings.
        
        Args:
            preferences: Current preferences
        """
        st.divider()
        st.subheader("📊 Current Effective Settings")
        
        available_channels = preferences.get("available_channels", [])
        
        if not available_channels:
            st.warning("⚠️ No communication channels are currently active. You may miss important updates!")
        else:
            st.success(f"✅ Active channels: {', '.join(available_channels).upper()}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Timezone",
                preferences.get("timezone", "UTC")
            )
        
        with col2:
            quiet_start = preferences.get("quiet_hours_start", "22:00")
            quiet_end = preferences.get("quiet_hours_end", "08:00")
            st.metric(
                "Quiet Hours",
                f"{quiet_start} - {quiet_end}"
            )


def render_preferences_page(client_id: str):
    """
    Render standalone preferences page.
    
    Args:
        client_id: Client identifier
    """
    st.set_page_config(
        page_title="Communication Preferences",
        page_icon="📬",
        layout="wide"
    )
    
    component = CRMPreferencesComponent()
    component.render(client_id)


def render_preferences_sidebar(client_id: str):
    """
    Render compact preferences widget in sidebar.
    
    Args:
        client_id: Client identifier
    """
    with st.sidebar:
        st.subheader("📬 Quick Preferences")
        
        component = CRMPreferencesComponent()
        
        # Load current preferences
        current_prefs = component._load_preferences(client_id)
        
        if current_prefs:
            available_channels = current_prefs.get("available_channels", [])
            
            if available_channels:
                show_success(f"Active: {', '.join(available_channels).upper()}")
            else:
                show_warning("No active channels")
            
            if st.button("⚙️ Manage Preferences", use_container_width=True):
                st.switch_page("pages/crm_preferences.py")
        else:
            show_error("Failed to load preferences")
