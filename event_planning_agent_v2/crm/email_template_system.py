"""
Email Template System for CRM Communication Engine.

This module provides template loading, caching, rendering with Jinja2,
and HTML validation for professional email communications.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import re

try:
    from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    Template = None

from .models import MessageType


logger = logging.getLogger(__name__)


class EmailTemplateSystem:
    """
    Manages email templates with loading, caching, and rendering capabilities.
    
    Features:
    - Template loading from filesystem with caching
    - Variable substitution using Jinja2
    - HTML structure validation
    - Responsive design support
    - Template versioning
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize the email template system.
        
        Args:
            templates_dir: Directory containing email templates.
                          Defaults to crm/templates/email/
        """
        if templates_dir is None:
            # Default to crm/templates/email/ directory
            templates_dir = Path(__file__).parent / "templates" / "email"
        
        self.templates_dir = Path(templates_dir)
        self.template_cache: Dict[str, Template] = {}
        
        # Initialize Jinja2 environment if available
        if JINJA2_AVAILABLE:
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.templates_dir)),
                autoescape=True,
                trim_blocks=True,
                lstrip_blocks=True
            )
            # Add custom filters
            self.jinja_env.filters['format_currency'] = self._format_currency
            self.jinja_env.filters['format_date'] = self._format_date
        else:
            self.jinja_env = None
            logger.warning("Jinja2 not available. Using simple string substitution.")
        
        # Ensure templates directory exists
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"EmailTemplateSystem initialized with templates_dir: {self.templates_dir}")
    
    def load_template(self, template_name: str) -> Template:
        """
        Load template from filesystem with caching.
        
        Args:
            template_name: Name of the template file (e.g., 'welcome.html')
        
        Returns:
            Jinja2 Template object
        
        Raises:
            TemplateNotFound: If template file doesn't exist
        """
        # Check cache first
        if template_name in self.template_cache:
            logger.debug(f"Template '{template_name}' loaded from cache")
            return self.template_cache[template_name]
        
        # Load template
        if self.jinja_env:
            try:
                template = self.jinja_env.get_template(template_name)
                self.template_cache[template_name] = template
                logger.info(f"Template '{template_name}' loaded and cached")
                return template
            except TemplateNotFound:
                logger.error(f"Template '{template_name}' not found in {self.templates_dir}")
                raise
        else:
            # Fallback to simple file reading
            template_path = self.templates_dir / template_name
            if not template_path.exists():
                raise FileNotFoundError(f"Template '{template_name}' not found at {template_path}")
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Create a simple template wrapper
            self.template_cache[template_name] = template_content
            logger.info(f"Template '{template_name}' loaded and cached (simple mode)")
            return template_content
    
    def render(
        self,
        template_name: str,
        context: Dict[str, Any],
        validate: bool = True
    ) -> Tuple[str, str]:
        """
        Render template with context data.
        
        Args:
            template_name: Name of the template file
            context: Dictionary of variables to substitute
            validate: Whether to validate HTML structure
        
        Returns:
            Tuple of (subject, html_body)
        
        Raises:
            ValueError: If template rendering fails or HTML is invalid
        """
        try:
            template = self.load_template(template_name)
            
            # Add default context variables
            full_context = self._add_default_context(context)
            
            # Render template
            if self.jinja_env and isinstance(template, Template):
                html_body = template.render(**full_context)
            else:
                # Simple string substitution fallback
                html_body = self._simple_render(template, full_context)
            
            # Extract subject from context or template
            subject = full_context.get('email_subject', self._extract_subject(html_body))
            
            # Validate HTML if requested
            if validate and not self.validate_html(html_body):
                logger.warning(f"Template '{template_name}' produced invalid HTML")
            
            logger.info(f"Template '{template_name}' rendered successfully")
            return subject, html_body
            
        except Exception as e:
            logger.error(f"Failed to render template '{template_name}': {e}")
            raise ValueError(f"Template rendering failed: {e}")
    
    def validate_html(self, html: str) -> bool:
        """
        Validate HTML structure.
        
        Performs basic validation:
        - Has DOCTYPE declaration
        - Has opening and closing html tags
        - Has head and body sections
        - Has proper tag nesting (basic check)
        
        Args:
            html: HTML string to validate
        
        Returns:
            True if HTML appears valid, False otherwise
        """
        if not html or not html.strip():
            logger.warning("Empty HTML content")
            return False
        
        # Check for DOCTYPE
        if not re.search(r'<!DOCTYPE\s+html>', html, re.IGNORECASE):
            logger.warning("Missing DOCTYPE declaration")
            return False
        
        # Check for html tags
        if not re.search(r'<html[^>]*>', html, re.IGNORECASE):
            logger.warning("Missing opening <html> tag")
            return False
        
        if not re.search(r'</html>', html, re.IGNORECASE):
            logger.warning("Missing closing </html> tag")
            return False
        
        # Check for head section
        if not re.search(r'<head[^>]*>.*?</head>', html, re.IGNORECASE | re.DOTALL):
            logger.warning("Missing or malformed <head> section")
            return False
        
        # Check for body section
        if not re.search(r'<body[^>]*>.*?</body>', html, re.IGNORECASE | re.DOTALL):
            logger.warning("Missing or malformed <body> section")
            return False
        
        # Basic tag nesting check (count opening vs closing tags)
        common_tags = ['div', 'p', 'table', 'tr', 'td', 'ul', 'li', 'h1', 'h2', 'h3']
        for tag in common_tags:
            opening = len(re.findall(f'<{tag}[^>]*>', html, re.IGNORECASE))
            closing = len(re.findall(f'</{tag}>', html, re.IGNORECASE))
            if opening != closing:
                logger.warning(f"Mismatched <{tag}> tags: {opening} opening, {closing} closing")
                # Don't fail validation for this, just warn
        
        logger.debug("HTML validation passed")
        return True
    
    def get_template_for_message_type(self, message_type: MessageType) -> str:
        """
        Get the template filename for a given message type.
        
        Args:
            message_type: Type of message
        
        Returns:
            Template filename
        """
        template_map = {
            MessageType.WELCOME: "welcome.html",
            MessageType.BUDGET_SUMMARY: "budget_summary.html",
            MessageType.VENDOR_OPTIONS: "vendor_options.html",
            MessageType.SELECTION_CONFIRMATION: "selection_confirmation.html",
            MessageType.BLUEPRINT_DELIVERY: "blueprint_delivery.html",
            MessageType.ERROR_NOTIFICATION: "error_notification.html",
            MessageType.REMINDER: "reminder.html",
        }
        return template_map.get(message_type, "generic.html")
    
    def clear_cache(self, template_name: Optional[str] = None):
        """
        Clear template cache.
        
        Args:
            template_name: Specific template to clear, or None to clear all
        """
        if template_name:
            if template_name in self.template_cache:
                del self.template_cache[template_name]
                logger.info(f"Cleared cache for template '{template_name}'")
        else:
            self.template_cache.clear()
            logger.info("Cleared all template cache")
    
    # Private helper methods
    
    def _add_default_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Add default context variables."""
        defaults = {
            'current_year': datetime.now().year,
            'company_name': 'Planiva',
            'support_email': 'support@planiva.com',
            'website_url': 'https://planiva.com',
        }
        # Merge with provided context (provided context takes precedence)
        return {**defaults, **context}
    
    def _simple_render(self, template: str, context: Dict[str, Any]) -> str:
        """Simple string substitution for when Jinja2 is not available."""
        result = template
        for key, value in context.items():
            # Replace {{key}} with value
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    def _extract_subject(self, html: str) -> str:
        """Extract subject from HTML title tag or use default."""
        match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return "Event Planning Update"
    
    def _format_currency(self, value: float, currency: str = "USD") -> str:
        """Format currency for display."""
        if currency == "USD":
            return f"${value:,.2f}"
        return f"{value:,.2f} {currency}"
    
    def _format_date(self, value: Any, format: str = "%B %d, %Y") -> str:
        """Format date for display."""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                return value
        
        if isinstance(value, datetime):
            return value.strftime(format)
        
        return str(value)
