"""
Reusable CRM UI components for the Streamlit GUI
"""
import streamlit as st
from typing import Dict, List, Optional, Any
from datetime import datetime


def communication_status_badge(status: str) -> str:
    """
    Create a colored badge for communication status.
    
    Args:
        status: Communication status (sent, delivered, opened, clicked, failed, pending)
        
    Returns:
        HTML string for the status badge
    """
    status_lower = status.lower()
    
    status_config = {
        'sent': {'color': '#0066cc', 'icon': '📤', 'label': 'Sent'},
        'delivered': {'color': '#00aa00', 'icon': '✅', 'label': 'Delivered'},
        'opened': {'color': '#00cc66', 'icon': '👁️', 'label': 'Opened'},
        'clicked': {'color': '#00dd88', 'icon': '🔗', 'label': 'Clicked'},
        'failed': {'color': '#ff4444', 'icon': '❌', 'label': 'Failed'},
        'pending': {'color': '#ffaa00', 'icon': '⏳', 'label': 'Pending'},
        'queued': {'color': '#888888', 'icon': '📋', 'label': 'Queued'},
    }
    
    config = status_config.get(status_lower, {'color': '#666666', 'icon': '❓', 'label': status.title()})
    
    return f"""
    <span style="
        background-color: {config['color']};
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85em;
        font-weight: 600;
        display: inline-block;
        white-space: nowrap;
    ">
        {config['icon']} {config['label']}
    </span>
    """


def channel_icon(channel: str, size: str = "medium") -> str:
    """
    Create an icon for communication channel.
    
    Args:
        channel: Channel name (email, sms, whatsapp)
        size: Icon size (small, medium, large)
        
    Returns:
        HTML string for the channel icon
    """
    channel_lower = channel.lower()
    
    channel_config = {
        'email': {'icon': '📧', 'color': '#0066cc', 'label': 'Email'},
        'sms': {'icon': '💬', 'color': '#00aa00', 'label': 'SMS'},
        'whatsapp': {'icon': '📱', 'color': '#25D366', 'label': 'WhatsApp'},
    }
    
    size_config = {
        'small': {'font_size': '1.2em', 'padding': '4px'},
        'medium': {'font_size': '1.5em', 'padding': '6px'},
        'large': {'font_size': '2em', 'padding': '8px'},
    }
    
    config = channel_config.get(channel_lower, {'icon': '📨', 'color': '#666666', 'label': channel.title()})
    size_style = size_config.get(size, size_config['medium'])
    
    return f"""
    <span style="
        font-size: {size_style['font_size']};
        padding: {size_style['padding']};
        display: inline-block;
    " title="{config['label']}">
        {config['icon']}
    </span>
    """


def metrics_card(title: str, value: Any, subtitle: Optional[str] = None, 
                 delta: Optional[str] = None, icon: Optional[str] = None,
                 color: str = "#0066cc") -> None:
    """
    Display a metrics card for analytics.
    
    Args:
        title: Card title
        value: Main metric value
        subtitle: Optional subtitle text
        delta: Optional delta/change indicator
        icon: Optional emoji icon
        color: Card accent color
    """
    icon_html = f'<span style="font-size: 2em; margin-right: 10px;">{icon}</span>' if icon else ''
    subtitle_html = f'<div style="font-size: 0.9em; color: #666; margin-top: 4px;">{subtitle}</div>' if subtitle else ''
    delta_html = ''
    
    if delta:
        delta_color = '#00aa00' if delta.startswith('+') else '#ff4444' if delta.startswith('-') else '#666666'
        delta_html = f'<div style="font-size: 0.85em; color: {delta_color}; margin-top: 4px; font-weight: 600;">{delta}</div>'
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {color}15 0%, {color}05 100%);
        border-left: 4px solid {color};
        padding: 20px;
        border-radius: 8px;
        margin: 10px 0;
    ">
        <div style="display: flex; align-items: center;">
            {icon_html}
            <div style="flex: 1;">
                <div style="font-size: 0.9em; color: #666; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px;">
                    {title}
                </div>
                <div style="font-size: 2em; font-weight: 700; color: #333; margin-top: 8px;">
                    {value}
                </div>
                {subtitle_html}
                {delta_html}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def communication_card(communication: Dict) -> None:
    """
    Display a communication card with details.
    
    Args:
        communication: Communication dictionary with details
    """
    message_type = communication.get('message_type', 'Unknown')
    channel = communication.get('channel', 'Unknown')
    status = communication.get('status', 'Unknown')
    sent_at = communication.get('sent_at', '')
    subject = communication.get('subject', 'No subject')
    
    # Format timestamp
    if sent_at:
        try:
            dt = datetime.fromisoformat(sent_at.replace('Z', '+00:00'))
            sent_at_formatted = dt.strftime("%b %d, %Y at %I:%M %p")
        except:
            sent_at_formatted = sent_at
    else:
        sent_at_formatted = 'N/A'
    
    # Get tracking info
    opened_at = communication.get('opened_at')
    clicked_at = communication.get('clicked_at')
    open_count = communication.get('open_count', 0)
    click_count = communication.get('click_count', 0)
    
    tracking_html = ''
    if channel.lower() == 'email':
        tracking_parts = []
        if opened_at:
            tracking_parts.append(f'👁️ Opened {open_count} time(s)')
        if clicked_at:
            tracking_parts.append(f'🔗 Clicked {click_count} time(s)')
        
        if tracking_parts:
            tracking_html = f"""
            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee;">
                <div style="font-size: 0.85em; color: #666;">
                    {' • '.join(tracking_parts)}
                </div>
            </div>
            """
    
    # Error message if failed
    error_html = ''
    if status.lower() == 'failed':
        error_message = communication.get('error_message', 'Unknown error')
        error_html = f"""
        <div style="margin-top: 10px; padding: 8px; background-color: #fff3f3; border-left: 3px solid #ff4444; border-radius: 4px;">
            <div style="font-size: 0.85em; color: #cc0000;">
                <strong>Error:</strong> {error_message}
            </div>
        </div>
        """
    
    st.markdown(f"""
    <div style="
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 16px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    ">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
            <div style="flex: 1;">
                <div style="font-weight: 600; font-size: 1.1em; color: #333; margin-bottom: 4px;">
                    {subject}
                </div>
                <div style="font-size: 0.85em; color: #666;">
                    {message_type.replace('_', ' ').title()} • {sent_at_formatted}
                </div>
            </div>
            <div style="margin-left: 16px;">
                {channel_icon(channel, 'medium')}
            </div>
        </div>
        <div>
            {communication_status_badge(status)}
        </div>
        {tracking_html}
        {error_html}
    </div>
    """, unsafe_allow_html=True)


def channel_performance_chart(channel_data: Dict) -> None:
    """
    Display channel performance metrics.
    
    Args:
        channel_data: Dictionary with channel performance data
    """
    channel = channel_data.get('channel', 'Unknown')
    total_sent = channel_data.get('total_sent', 0)
    delivered = channel_data.get('delivered', 0)
    opened = channel_data.get('opened', 0)
    clicked = channel_data.get('clicked', 0)
    failed = channel_data.get('failed', 0)
    
    # Calculate rates
    delivery_rate = (delivered / total_sent * 100) if total_sent > 0 else 0
    open_rate = (opened / delivered * 100) if delivered > 0 else 0
    click_rate = (clicked / opened * 100) if opened > 0 else 0
    
    st.markdown(f"""
    <div style="
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px;
        margin: 10px 0;
    ">
        <div style="display: flex; align-items: center; margin-bottom: 16px;">
            {channel_icon(channel, 'large')}
            <h3 style="margin: 0 0 0 12px; color: #333;">{channel.title()}</h3>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 16px;">
            <div>
                <div style="font-size: 0.85em; color: #666; margin-bottom: 4px;">Total Sent</div>
                <div style="font-size: 1.5em; font-weight: 700; color: #333;">{total_sent}</div>
            </div>
            <div>
                <div style="font-size: 0.85em; color: #666; margin-bottom: 4px;">Delivered</div>
                <div style="font-size: 1.5em; font-weight: 700; color: #00aa00;">{delivered}</div>
            </div>
        </div>
        
        <div style="margin-top: 16px;">
            <div style="margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="font-size: 0.85em; color: #666;">Delivery Rate</span>
                    <span style="font-size: 0.85em; font-weight: 600; color: #00aa00;">{delivery_rate:.1f}%</span>
                </div>
                <div style="background: #f0f0f0; height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: #00aa00; height: 100%; width: {delivery_rate}%;"></div>
                </div>
            </div>
            
            <div style="margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="font-size: 0.85em; color: #666;">Open Rate</span>
                    <span style="font-size: 0.85em; font-weight: 600; color: #0066cc;">{open_rate:.1f}%</span>
                </div>
                <div style="background: #f0f0f0; height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: #0066cc; height: 100%; width: {open_rate}%;"></div>
                </div>
            </div>
            
            <div style="margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="font-size: 0.85em; color: #666;">Click Rate</span>
                    <span style="font-size: 0.85em; font-weight: 600; color: #ff8800;">{click_rate:.1f}%</span>
                </div>
                <div style="background: #f0f0f0; height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: #ff8800; height: 100%; width: {click_rate}%;"></div>
                </div>
            </div>
        </div>
        
        {f'<div style="margin-top: 12px; padding: 8px; background: #fff3f3; border-radius: 4px;"><span style="color: #ff4444; font-size: 0.85em;">⚠️ {failed} failed</span></div>' if failed > 0 else ''}
    </div>
    """, unsafe_allow_html=True)


def preference_summary_card(preferences: Dict) -> None:
    """
    Display a summary card of communication preferences.
    
    Args:
        preferences: Preferences dictionary
    """
    preferred_channels = preferences.get('preferred_channels', [])
    timezone = preferences.get('timezone', 'UTC')
    quiet_hours_start = preferences.get('quiet_hours_start', 'Not set')
    quiet_hours_end = preferences.get('quiet_hours_end', 'Not set')
    
    # Opt-out status
    opt_outs = []
    if preferences.get('opt_out_email'):
        opt_outs.append('Email')
    if preferences.get('opt_out_sms'):
        opt_outs.append('SMS')
    if preferences.get('opt_out_whatsapp'):
        opt_outs.append('WhatsApp')
    
    opt_out_html = ''
    if opt_outs:
        opt_out_html = f"""
        <div style="margin-top: 12px; padding: 8px; background: #fff3f3; border-left: 3px solid #ff4444; border-radius: 4px;">
            <div style="font-size: 0.85em; color: #cc0000;">
                <strong>Opted out:</strong> {', '.join(opt_outs)}
            </div>
        </div>
        """
    
    channels_html = ' '.join([channel_icon(ch, 'small') for ch in preferred_channels]) if preferred_channels else 'None selected'
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #0066cc15 0%, #0066cc05 100%);
        border-left: 4px solid #0066cc;
        border-radius: 8px;
        padding: 20px;
        margin: 10px 0;
    ">
        <h4 style="margin: 0 0 16px 0; color: #333;">Current Preferences</h4>
        
        <div style="margin-bottom: 12px;">
            <div style="font-size: 0.85em; color: #666; margin-bottom: 4px;">Preferred Channels</div>
            <div style="font-size: 1em;">{channels_html}</div>
        </div>
        
        <div style="margin-bottom: 12px;">
            <div style="font-size: 0.85em; color: #666; margin-bottom: 4px;">Timezone</div>
            <div style="font-size: 1em; font-weight: 600; color: #333;">🌍 {timezone}</div>
        </div>
        
        <div style="margin-bottom: 12px;">
            <div style="font-size: 0.85em; color: #666; margin-bottom: 4px;">Quiet Hours</div>
            <div style="font-size: 1em; font-weight: 600; color: #333;">🌙 {quiet_hours_start} - {quiet_hours_end}</div>
        </div>
        
        {opt_out_html}
    </div>
    """, unsafe_allow_html=True)


def empty_state_message(icon: str, title: str, message: str, action_text: Optional[str] = None) -> None:
    """
    Display an empty state message.
    
    Args:
        icon: Emoji icon
        title: Title text
        message: Message text
        action_text: Optional action button text
    """
    action_html = f'<div style="margin-top: 16px; font-size: 0.9em; color: #0066cc; font-weight: 600;">{action_text}</div>' if action_text else ''
    
    st.markdown(f"""
    <div style="
        text-align: center;
        padding: 60px 20px;
        background: #f9f9f9;
        border-radius: 8px;
        margin: 20px 0;
    ">
        <div style="font-size: 4em; margin-bottom: 16px;">{icon}</div>
        <h3 style="color: #333; margin-bottom: 8px;">{title}</h3>
        <p style="color: #666; font-size: 1em; max-width: 500px; margin: 0 auto;">
            {message}
        </p>
        {action_html}
    </div>
    """, unsafe_allow_html=True)
