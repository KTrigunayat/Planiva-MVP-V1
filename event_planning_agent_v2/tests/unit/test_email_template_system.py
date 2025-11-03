"""
Unit tests for Email Template System.

Tests template loading, caching, rendering with Jinja2, and HTML validation.
"""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from crm.email_template_system import EmailTemplateSystem
from crm.models import MessageType


class TestEmailTemplateSystem:
    """Test suite for EmailTemplateSystem class."""
    
    @pytest.fixture
    def temp_templates_dir(self):
        """Create a temporary templates directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def template_system(self, temp_templates_dir):
        """Create an EmailTemplateSystem instance with temp directory."""
        return EmailTemplateSystem(templates_dir=temp_templates_dir)
    
    @pytest.fixture
    def sample_template_content(self):
        """Sample HTML template content."""
        return """<!DOCTYPE html>
<html>
<head>
    <title>{{ email_subject }}</title>
</head>
<body>
    <h1>Hello {{ client_name }}!</h1>
    <p>Your plan ID is {{ plan_id }}.</p>
    <p>Event: {{ event_type }}</p>
</body>
</html>"""
    
    def test_initialization(self, temp_templates_dir):
        """Test EmailTemplateSystem initialization."""
        system = EmailTemplateSystem(templates_dir=temp_templates_dir)
        
        assert system.templates_dir == temp_templates_dir
        assert system.template_cache == {}
        assert temp_templates_dir.exists()
    
    def test_initialization_default_directory(self):
        """Test initialization with default templates directory."""
        system = EmailTemplateSystem()
        
        expected_dir = Path(__file__).parent.parent.parent / "crm" / "templates" / "email"
        assert system.templates_dir == expected_dir

    def test_load_template_success(self, template_system, temp_templates_dir, sample_template_content):
        """Test successful template loading."""
        # Create a test template file
        template_file = temp_templates_dir / "test.html"
        template_file.write_text(sample_template_content, encoding='utf-8')
        
        # Load template
        template = template_system.load_template("test.html")
        
        assert template is not None
        assert "test.html" in template_system.template_cache
    
    def test_load_template_caching(self, template_system, temp_templates_dir, sample_template_content):
        """Test that templates are cached after first load."""
        # Create a test template file
        template_file = temp_templates_dir / "cached.html"
        template_file.write_text(sample_template_content, encoding='utf-8')
        
        # Load template twice
        template1 = template_system.load_template("cached.html")
        template2 = template_system.load_template("cached.html")
        
        # Should be the same object from cache
        assert template1 is template2
        assert "cached.html" in template_system.template_cache
    
    def test_load_template_not_found(self, template_system):
        """Test loading a non-existent template raises error."""
        with pytest.raises((FileNotFoundError, Exception)):
            template_system.load_template("nonexistent.html")
    
    def test_render_template_with_context(self, template_system, temp_templates_dir, sample_template_content):
        """Test rendering template with context variables."""
        # Create template file
        template_file = temp_templates_dir / "render_test.html"
        template_file.write_text(sample_template_content, encoding='utf-8')
        
        # Render with context
        context = {
            "email_subject": "Test Email",
            "client_name": "John Doe",
            "plan_id": "plan-123",
            "event_type": "Wedding"
        }
        
        subject, html_body = template_system.render("render_test.html", context)
        
        assert subject == "Test Email"
        assert "John Doe" in html_body
        assert "plan-123" in html_body
        assert "Wedding" in html_body
    
    def test_render_with_default_context(self, template_system, temp_templates_dir):
        """Test that default context variables are added."""
        template_content = """<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
    <p>Company: {{ company_name }}</p>
    <p>Year: {{ current_year }}</p>
    <p>Support: {{ support_email }}</p>
</body>
</html>"""
        
        template_file = temp_templates_dir / "defaults.html"
        template_file.write_text(template_content, encoding='utf-8')
        
        subject, html_body = template_system.render("defaults.html", {})
        
        assert "Planiva" in html_body
        assert str(datetime.now().year) in html_body
        assert "support@planiva.com" in html_body

    def test_validate_html_valid(self, template_system):
        """Test HTML validation with valid HTML."""
        valid_html = """<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
</head>
<body>
    <div>
        <p>Content</p>
    </div>
</body>
</html>"""
        
        assert template_system.validate_html(valid_html) is True
    
    def test_validate_html_missing_doctype(self, template_system):
        """Test HTML validation fails without DOCTYPE."""
        invalid_html = """<html>
<head><title>Test</title></head>
<body><p>Content</p></body>
</html>"""
        
        assert template_system.validate_html(invalid_html) is False
    
    def test_validate_html_missing_head(self, template_system):
        """Test HTML validation fails without head section."""
        invalid_html = """<!DOCTYPE html>
<html>
<body><p>Content</p></body>
</html>"""
        
        assert template_system.validate_html(invalid_html) is False
    
    def test_validate_html_missing_body(self, template_system):
        """Test HTML validation fails without body section."""
        invalid_html = """<!DOCTYPE html>
<html>
<head><title>Test</title></head>
</html>"""
        
        assert template_system.validate_html(invalid_html) is False
    
    def test_validate_html_empty_content(self, template_system):
        """Test HTML validation fails with empty content."""
        assert template_system.validate_html("") is False
        assert template_system.validate_html("   ") is False
    
    def test_get_template_for_message_type(self, template_system):
        """Test getting template filename for message types."""
        assert template_system.get_template_for_message_type(MessageType.WELCOME) == "welcome.html"
        assert template_system.get_template_for_message_type(MessageType.BUDGET_SUMMARY) == "budget_summary.html"
        assert template_system.get_template_for_message_type(MessageType.VENDOR_OPTIONS) == "vendor_options.html"
        assert template_system.get_template_for_message_type(MessageType.SELECTION_CONFIRMATION) == "selection_confirmation.html"
        assert template_system.get_template_for_message_type(MessageType.BLUEPRINT_DELIVERY) == "blueprint_delivery.html"
        assert template_system.get_template_for_message_type(MessageType.ERROR_NOTIFICATION) == "error_notification.html"
        assert template_system.get_template_for_message_type(MessageType.REMINDER) == "reminder.html"
    
    def test_clear_cache_specific_template(self, template_system, temp_templates_dir, sample_template_content):
        """Test clearing cache for specific template."""
        # Create and load template
        template_file = temp_templates_dir / "cache_test.html"
        template_file.write_text(sample_template_content, encoding='utf-8')
        template_system.load_template("cache_test.html")
        
        assert "cache_test.html" in template_system.template_cache
        
        # Clear specific template
        template_system.clear_cache("cache_test.html")
        
        assert "cache_test.html" not in template_system.template_cache

    def test_clear_cache_all_templates(self, template_system, temp_templates_dir, sample_template_content):
        """Test clearing all template cache."""
        # Create and load multiple templates
        for i in range(3):
            template_file = temp_templates_dir / f"template{i}.html"
            template_file.write_text(sample_template_content, encoding='utf-8')
            template_system.load_template(f"template{i}.html")
        
        assert len(template_system.template_cache) == 3
        
        # Clear all cache
        template_system.clear_cache()
        
        assert len(template_system.template_cache) == 0
    
    def test_format_currency_filter(self, template_system):
        """Test currency formatting filter."""
        result = template_system._format_currency(1234.56)
        assert result == "$1,234.56"
        
        result = template_system._format_currency(1000000.00)
        assert result == "$1,000,000.00"
    
    def test_format_date_filter(self, template_system):
        """Test date formatting filter."""
        test_date = datetime(2025, 10, 23, 14, 30)
        result = template_system._format_date(test_date)
        assert "October 23, 2025" in result
        
        # Test with ISO string
        result = template_system._format_date("2025-10-23")
        assert "2025" in result
    
    def test_render_with_jinja2_filters(self, template_system, temp_templates_dir):
        """Test rendering with custom Jinja2 filters."""
        template_content = """<!DOCTYPE html>
<html>
<head><title>Test Filters</title></head>
<body>
    <p>Cost: {{ total_cost|format_currency }}</p>
    <p>Date: {{ event_date|format_date }}</p>
</body>
</html>"""
        
        template_file = temp_templates_dir / "filters.html"
        template_file.write_text(template_content, encoding='utf-8')
        
        context = {
            "total_cost": 5000.00,
            "event_date": datetime(2025, 12, 25)
        }
        
        subject, html_body = template_system.render("filters.html", context)
        
        assert "$5,000.00" in html_body
        assert "December 25, 2025" in html_body
    
    def test_render_without_validation(self, template_system, temp_templates_dir):
        """Test rendering without HTML validation."""
        # Create invalid HTML template
        invalid_template = "<html><body>{{ message }}</body></html>"
        template_file = temp_templates_dir / "no_validate.html"
        template_file.write_text(invalid_template, encoding='utf-8')
        
        context = {"message": "Test message"}
        
        # Should not raise error even with invalid HTML when validate=False
        subject, html_body = template_system.render("no_validate.html", context, validate=False)
        
        assert "Test message" in html_body
    
    def test_extract_subject_from_title(self, template_system):
        """Test extracting subject from HTML title tag."""
        html = "<html><head><title>My Subject</title></head><body></body></html>"
        subject = template_system._extract_subject(html)
        assert subject == "My Subject"
    
    def test_extract_subject_default(self, template_system):
        """Test default subject when no title tag."""
        html = "<html><head></head><body></body></html>"
        subject = template_system._extract_subject(html)
        assert subject == "Event Planning Update"


class TestEmailTemplateSystemIntegration:
    """Integration tests using actual template files."""
    
    @pytest.fixture
    def real_template_system(self):
        """Create EmailTemplateSystem with real templates directory."""
        templates_dir = Path(__file__).parent.parent.parent / "crm" / "templates" / "email"
        return EmailTemplateSystem(templates_dir=templates_dir)
    
    def test_load_real_welcome_template(self, real_template_system):
        """Test loading the actual welcome template."""
        template = real_template_system.load_template("welcome.html")
        assert template is not None
    
    def test_render_real_welcome_template(self, real_template_system):
        """Test rendering the actual welcome template."""
        context = {
            "client_name": "Jane Smith",
            "plan_id": "plan-456",
            "event_type": "Corporate Event",
            "event_date": datetime(2025, 11, 15),
            "guest_count": 150
        }
        
        subject, html_body = real_template_system.render("welcome.html", context)
        
        assert "Jane Smith" in html_body
        assert "plan-456" in html_body
        assert "Corporate Event" in html_body
        assert real_template_system.validate_html(html_body)
