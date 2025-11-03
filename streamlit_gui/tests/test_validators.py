"""
Unit tests for form validation functionality
"""
import pytest
from datetime import datetime, date, timedelta
from utils.validators import (
    validate_email, validate_phone, validate_budget, validate_guest_count,
    validate_event_date, validate_required_field, validate_text_length,
    FormValidator, ValidationError
)

class TestBasicValidators:
    """Test cases for basic validation functions"""
    
    def test_validate_email_valid(self):
        """Test valid email addresses"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@example.com"
        ]
        
        for email in valid_emails:
            assert validate_email(email) == True
    
    def test_validate_email_invalid(self):
        """Test invalid email addresses"""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test..test@example.com",
            "",
            None
        ]
        
        for email in invalid_emails:
            assert validate_email(email) == False
    
    def test_validate_phone_valid(self):
        """Test valid phone numbers"""
        valid_phones = [
            "+1-555-123-4567",
            "(555) 123-4567",
            "555.123.4567",
            "5551234567",
            "+44 20 7946 0958"
        ]
        
        for phone in valid_phones:
            assert validate_phone(phone) == True
    
    def test_validate_phone_invalid(self):
        """Test invalid phone numbers"""
        invalid_phones = [
            "123",
            "abc-def-ghij",
            "",
            None,
            "555-123"
        ]
        
        for phone in invalid_phones:
            assert validate_phone(phone) == False
    
    def test_validate_budget_valid(self):
        """Test valid budget values"""
        valid_budgets = [1000, 50000, 100000.50, "25000", "75000.00"]
        
        for budget in valid_budgets:
            assert validate_budget(budget) == True
    
    def test_validate_budget_invalid(self):
        """Test invalid budget values"""
        invalid_budgets = [-1000, 0, "abc", "", None, "25,000"]
        
        for budget in invalid_budgets:
            assert validate_budget(budget) == False
    
    def test_validate_guest_count_valid(self):
        """Test valid guest counts"""
        valid_counts = [1, 50, 500, "100", "250"]
        
        for count in valid_counts:
            assert validate_guest_count(count) == True
    
    def test_validate_guest_count_invalid(self):
        """Test invalid guest counts"""
        invalid_counts = [-1, 0, "abc", "", None, 10001]
        
        for count in invalid_counts:
            assert validate_guest_count(count) == False
    
    def test_validate_event_date_valid(self):
        """Test valid event dates"""
        future_date = date.today() + timedelta(days=30)
        valid_dates = [
            future_date,
            datetime.now() + timedelta(days=60),
            future_date.strftime("%Y-%m-%d")
        ]
        
        for event_date in valid_dates:
            assert validate_event_date(event_date) == True
    
    def test_validate_event_date_invalid(self):
        """Test invalid event dates"""
        past_date = date.today() - timedelta(days=30)
        invalid_dates = [
            past_date,
            datetime.now() - timedelta(days=60),
            "invalid-date",
            "",
            None
        ]
        
        for event_date in invalid_dates:
            assert validate_event_date(event_date) == False
    
    def test_validate_required_field_valid(self):
        """Test valid required fields"""
        valid_values = ["test", "  test  ", 123, True, ["item"]]
        
        for value in valid_values:
            assert validate_required_field(value) == True
    
    def test_validate_required_field_invalid(self):
        """Test invalid required fields"""
        invalid_values = ["", "   ", None, [], {}]
        
        for value in invalid_values:
            assert validate_required_field(value) == False
    
    def test_validate_text_length_valid(self):
        """Test valid text length"""
        assert validate_text_length("test", min_length=1, max_length=10) == True
        assert validate_text_length("hello world", min_length=5, max_length=20) == True
        assert validate_text_length("", min_length=0, max_length=5) == True
    
    def test_validate_text_length_invalid(self):
        """Test invalid text length"""
        assert validate_text_length("", min_length=1, max_length=10) == False
        assert validate_text_length("a", min_length=5, max_length=10) == False
        assert validate_text_length("very long text here", min_length=1, max_length=10) == False

class TestFormValidator:
    """Test cases for FormValidator class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = FormValidator()
    
    def test_add_rule(self):
        """Test adding validation rules"""
        self.validator.add_rule("email", validate_email, "Invalid email format")
        
        assert "email" in self.validator.rules
        assert len(self.validator.rules["email"]) == 1
    
    def test_validate_field_success(self):
        """Test successful field validation"""
        self.validator.add_rule("email", validate_email, "Invalid email")
        
        result = self.validator.validate_field("email", "test@example.com")
        assert result.is_valid == True
        assert len(result.errors) == 0
    
    def test_validate_field_failure(self):
        """Test failed field validation"""
        self.validator.add_rule("email", validate_email, "Invalid email")
        
        result = self.validator.validate_field("email", "invalid-email")
        assert result.is_valid == False
        assert len(result.errors) == 1
        assert "Invalid email" in result.errors
    
    def test_validate_form_success(self):
        """Test successful form validation"""
        self.validator.add_rule("client_name", validate_required_field, "Name is required")
        self.validator.add_rule("email", validate_email, "Invalid email")
        self.validator.add_rule("budget", validate_budget, "Invalid budget")
        
        form_data = {
            "client_name": "John Doe",
            "email": "john@example.com",
            "budget": 50000
        }
        
        result = self.validator.validate_form(form_data)
        assert result.is_valid == True
        assert len(result.errors) == 0
    
    def test_validate_form_failure(self):
        """Test failed form validation"""
        self.validator.add_rule("client_name", validate_required_field, "Name is required")
        self.validator.add_rule("email", validate_email, "Invalid email")
        self.validator.add_rule("budget", validate_budget, "Invalid budget")
        
        form_data = {
            "client_name": "",
            "email": "invalid-email",
            "budget": -1000
        }
        
        result = self.validator.validate_form(form_data)
        assert result.is_valid == False
        assert len(result.errors) == 3
    
    def test_validate_form_partial(self):
        """Test partial form validation"""
        self.validator.add_rule("client_name", validate_required_field, "Name is required")
        self.validator.add_rule("email", validate_email, "Invalid email")
        
        form_data = {
            "client_name": "John Doe",
            "email": "invalid-email",
            "other_field": "value"
        }
        
        result = self.validator.validate_form(form_data)
        assert result.is_valid == False
        assert len(result.errors) == 1
        assert "Invalid email" in result.errors
    
    def test_multiple_rules_same_field(self):
        """Test multiple validation rules for the same field"""
        self.validator.add_rule("password", validate_required_field, "Password is required")
        self.validator.add_rule("password", 
                              lambda x: validate_text_length(x, min_length=8), 
                              "Password must be at least 8 characters")
        
        # Test with empty password
        result = self.validator.validate_field("password", "")
        assert result.is_valid == False
        assert len(result.errors) == 2
        
        # Test with short password
        result = self.validator.validate_field("password", "123")
        assert result.is_valid == False
        assert len(result.errors) == 1
        assert "Password must be at least 8 characters" in result.errors
        
        # Test with valid password
        result = self.validator.validate_field("password", "validpassword")
        assert result.is_valid == True
        assert len(result.errors) == 0
    
    def test_custom_validator_function(self):
        """Test custom validator function"""
        def validate_even_number(value):
            try:
                num = int(value)
                return num % 2 == 0
            except (ValueError, TypeError):
                return False
        
        self.validator.add_rule("even_number", validate_even_number, "Must be an even number")
        
        assert self.validator.validate_field("even_number", 4).is_valid == True
        assert self.validator.validate_field("even_number", 3).is_valid == False
        assert self.validator.validate_field("even_number", "abc").is_valid == False

class TestValidationError:
    """Test cases for ValidationError exception"""
    
    def test_validation_error_creation(self):
        """Test ValidationError creation"""
        errors = ["Error 1", "Error 2"]
        error = ValidationError("Validation failed", errors)
        
        assert str(error) == "Validation failed"
        assert error.errors == errors
    
    def test_validation_error_single_error(self):
        """Test ValidationError with single error"""
        error = ValidationError("Single error", "Error message")
        
        assert str(error) == "Single error"
        assert error.errors == ["Error message"]

class TestEventSpecificValidators:
    """Test cases for event-specific validation logic"""
    
    def test_wedding_specific_validation(self):
        """Test wedding-specific validation rules"""
        validator = FormValidator()
        
        # Add wedding-specific rules
        validator.add_rule("ceremony_guests", validate_guest_count, "Invalid ceremony guest count")
        validator.add_rule("reception_guests", validate_guest_count, "Invalid reception guest count")
        
        def validate_guest_split(form_data):
            ceremony = form_data.get("ceremony_guests", 0)
            reception = form_data.get("reception_guests", 0)
            try:
                ceremony = int(ceremony)
                reception = int(reception)
                return ceremony <= reception
            except (ValueError, TypeError):
                return False
        
        validator.add_form_rule(validate_guest_split, "Reception guests must be >= ceremony guests")
        
        # Test valid split
        valid_data = {"ceremony_guests": 50, "reception_guests": 100}
        result = validator.validate_form(valid_data)
        assert result.is_valid == True
        
        # Test invalid split
        invalid_data = {"ceremony_guests": 100, "reception_guests": 50}
        result = validator.validate_form(invalid_data)
        assert result.is_valid == False
    
    def test_budget_allocation_validation(self):
        """Test budget allocation validation"""
        validator = FormValidator()
        
        def validate_budget_allocation(form_data):
            total_budget = form_data.get("total_budget", 0)
            venue_budget = form_data.get("venue_budget", 0)
            catering_budget = form_data.get("catering_budget", 0)
            
            try:
                total = float(total_budget)
                venue = float(venue_budget)
                catering = float(catering_budget)
                
                return (venue + catering) <= total
            except (ValueError, TypeError):
                return False
        
        validator.add_form_rule(validate_budget_allocation, "Allocated budget exceeds total budget")
        
        # Test valid allocation
        valid_data = {
            "total_budget": 50000,
            "venue_budget": 20000,
            "catering_budget": 15000
        }
        result = validator.validate_form(valid_data)
        assert result.is_valid == True
        
        # Test invalid allocation
        invalid_data = {
            "total_budget": 30000,
            "venue_budget": 20000,
            "catering_budget": 15000
        }
        result = validator.validate_form(invalid_data)
        assert result.is_valid == False

if __name__ == "__main__":
    pytest.main([__file__])