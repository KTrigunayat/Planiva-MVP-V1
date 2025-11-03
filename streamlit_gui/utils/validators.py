"""
Input validation utilities
"""
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
import re

class ValidationError(Exception):
    """Custom validation error"""
    pass

class FormValidator:
    """Form validation utilities"""
    
    @staticmethod
    def validate_required_field(value: Any, field_name: str) -> None:
        """Validate that a required field has a value"""
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"{field_name} is required")
    
    @staticmethod
    def validate_email(email: str) -> None:
        """Validate email format"""
        if not email:
            return
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError("Invalid email format")
    
    @staticmethod
    def validate_phone(phone: str) -> None:
        """Validate phone number"""
        if not phone:
            return
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        if not (10 <= len(digits) <= 15):
            raise ValidationError("Phone number must be 10-15 digits")
    
    @staticmethod
    def validate_budget(budget: float, min_budget: float = 1000) -> None:
        """Validate budget amount"""
        if budget <= 0:
            raise ValidationError("Budget must be greater than 0")
        if budget < min_budget:
            raise ValidationError(f"Budget must be at least ${min_budget:,.2f}")
    
    @staticmethod
    def validate_guest_count(guests: int) -> None:
        """Validate guest count"""
        if guests <= 0:
            raise ValidationError("Guest count must be greater than 0")
        if guests > 10000:
            raise ValidationError("Guest count seems unreasonably high")
    
    @staticmethod
    def validate_event_date(event_date) -> None:
        """Validate event date"""
        from datetime import timedelta
        
        # Convert string to date if needed
        if isinstance(event_date, str):
            try:
                event_date = datetime.fromisoformat(event_date).date()
            except ValueError:
                raise ValidationError("Invalid date format")
        elif isinstance(event_date, datetime):
            event_date = event_date.date()
        
        today = date.today()
        if event_date < today:
            raise ValidationError("Event date cannot be in the past")
        
        # Check if date is too far in the future (2 years)
        max_date = today + timedelta(days=730)
        if event_date > max_date:
            raise ValidationError("Event date cannot be more than 2 years in the future")
    
    @staticmethod
    def validate_text_length(text: str, field_name: str, max_length: int = 1000) -> None:
        """Validate text length"""
        if len(text) > max_length:
            raise ValidationError(f"{field_name} cannot exceed {max_length} characters")
    
    @staticmethod
    def validate_selection(value: Any, options: List[Any], field_name: str) -> None:
        """Validate that a selection is from valid options"""
        if value not in options:
            raise ValidationError(f"Invalid selection for {field_name}")

class EventPlanValidator:
    """Validator for event plan data"""
    
    @staticmethod
    def validate_basic_info(data: Dict) -> List[str]:
        """Validate basic event information"""
        errors = []
        
        try:
            FormValidator.validate_required_field(data.get('client_name'), 'Client name')
        except ValidationError as e:
            errors.append(str(e))
        
        try:
            FormValidator.validate_required_field(data.get('event_type'), 'Event type')
        except ValidationError as e:
            errors.append(str(e))
        
        try:
            FormValidator.validate_required_field(data.get('event_date'), 'Event date')
            if data.get('event_date'):
                FormValidator.validate_event_date(data['event_date'])
        except ValidationError as e:
            errors.append(str(e))
        
        try:
            FormValidator.validate_required_field(data.get('location'), 'Location')
        except ValidationError as e:
            errors.append(str(e))
        
        # Validate contact info if provided
        if data.get('client_email'):
            try:
                FormValidator.validate_email(data['client_email'])
            except ValidationError as e:
                errors.append(str(e))
        
        if data.get('client_phone'):
            try:
                FormValidator.validate_phone(data['client_phone'])
            except ValidationError as e:
                errors.append(str(e))
        
        return errors
    
    @staticmethod
    def validate_guest_info(data: Dict) -> List[str]:
        """Validate guest information"""
        errors = []
        
        try:
            FormValidator.validate_required_field(data.get('total_guests'), 'Total guests')
            if data.get('total_guests'):
                FormValidator.validate_guest_count(data['total_guests'])
        except ValidationError as e:
            errors.append(str(e))
        
        # Validate ceremony/reception split if provided
        ceremony_guests = data.get('ceremony_guests')
        reception_guests = data.get('reception_guests')
        total_guests = data.get('total_guests', 0)
        
        if ceremony_guests is not None and reception_guests is not None:
            if ceremony_guests + reception_guests != total_guests:
                errors.append("Ceremony and reception guest counts must add up to total guests")
        
        return errors
    
    @staticmethod
    def validate_budget_info(data: Dict) -> List[str]:
        """Validate budget information"""
        errors = []
        
        try:
            FormValidator.validate_required_field(data.get('total_budget'), 'Total budget')
            if data.get('total_budget'):
                FormValidator.validate_budget(data['total_budget'])
        except ValidationError as e:
            errors.append(str(e))
        
        # Validate budget allocation if provided
        allocations = data.get('budget_allocation', {})
        if allocations:
            total_percentage = sum(allocations.values())
            if abs(total_percentage - 100) > 1:  # Allow 1% tolerance
                errors.append("Budget allocation percentages must add up to 100%")
        
        return errors
    
    @staticmethod
    def validate_preferences(data: Dict) -> List[str]:
        """Validate preference selections"""
        errors = []
        
        # Validate text fields length
        for field, max_length in [
            ('client_vision', 2000),
            ('special_requirements', 1000),
            ('theme_description', 500)
        ]:
            if data.get(field):
                try:
                    FormValidator.validate_text_length(data[field], field.replace('_', ' ').title(), max_length)
                except ValidationError as e:
                    errors.append(str(e))
        
        return errors
    
    @staticmethod
    def validate_complete_form(data: Dict) -> Tuple[bool, List[str]]:
        """Validate the complete event planning form"""
        all_errors = []
        
        # Validate all sections
        all_errors.extend(EventPlanValidator.validate_basic_info(data))
        all_errors.extend(EventPlanValidator.validate_guest_info(data))
        all_errors.extend(EventPlanValidator.validate_budget_info(data))
        all_errors.extend(EventPlanValidator.validate_preferences(data))
        
        return len(all_errors) == 0, all_errors