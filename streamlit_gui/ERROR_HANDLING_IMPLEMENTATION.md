# Error Handling and User Feedback Implementation

## Overview

This document describes the comprehensive error handling and user feedback system implemented for the Streamlit GUI. The system provides consistent, user-friendly error messages, loading states, validation, and recovery mechanisms across all pages and components.

## Components

### 1. Error Handling Utilities (`utils/error_handling.py`)

The core error handling module provides:

#### ErrorHandler Class
- **`handle_api_error()`**: Handles API errors with context-specific messages
  - 404 errors: "Not Found" with suggestions
  - 400 errors: "Invalid Request" with input validation hints
  - 401/403 errors: Authentication/authorization messages
  - 500+ errors: Server error messages with retry suggestions
  - Connection errors: Network connectivity messages
  - Timeout errors: Request timeout messages

- **`handle_unexpected_error()`**: Handles unexpected exceptions
  - Shows generic error message to user
  - Provides expandable error details for support
  - Logs full stack trace

- **`show_validation_error()`**: Shows field-level validation errors
- **`show_success()`**: Shows success messages with optional details
- **`show_warning()`**: Shows warning messages
- **`show_info()`**: Shows informational messages

#### Decorators

**`@with_error_handling`**: Wraps functions with automatic error handling
```python
@with_error_handling(context="loading data", show_spinner=True, spinner_text="Loading...")
def load_data():
    return api_client.get_data()
```

**`@with_retry`**: Adds retry logic for transient failures
```python
@with_retry(max_attempts=3, delay=1.0, backoff=2.0)
def fetch_data():
    return api_client.get_data()
```

#### Components

**`LoadingState`**: Context manager for loading states
```python
with LoadingState("Loading data...", show_progress=True) as loading:
    data = fetch_data()
    loading.update_progress(0.5, "Processing...")
```

**`RetryButton`**: Renders retry buttons after errors
```python
if RetryButton.render("retry_key", on_click=reload_data):
    st.rerun()
```

**`StaleDataWarning`**: Shows warnings for stale data
```python
if StaleDataWarning.render(last_updated, threshold_seconds=300):
    reload_data()
```

#### Validators

Common validation functions:
- `Validators.required()`: Check if value is not empty
- `Validators.email()`: Validate email format
- `Validators.min_length(n)`: Minimum length validator
- `Validators.max_length(n)`: Maximum length validator
- `Validators.numeric()`: Check if value is numeric
- `Validators.positive()`: Check if value is positive
- `Validators.in_range(min, max)`: Range validator

**`validate_form_field()`**: Validate fields with multiple validators
```python
validators = {
    "Required": Validators.required,
    "Email format": Validators.email
}
is_valid = validate_form_field(email, "Email", validators)
```

### 2. API Wrapper (`components/api_wrapper.py`)

Provides wrapped API calls with built-in error handling:

#### CRM API Methods
- `get_preferences_safe()`: Get preferences with error handling
- `update_preferences_safe()`: Update preferences with success messages
- `get_communications_safe()`: Get communications with retry logic
- `get_analytics_safe()`: Get analytics with error handling

#### Task Management API Methods
- `get_extended_task_list_safe()`: Get tasks with error handling
- `get_timeline_data_safe()`: Get timeline with retry logic
- `get_conflicts_safe()`: Get conflicts with error handling
- `update_task_status_safe()`: Update task with success messages
- `resolve_conflict_safe()`: Resolve conflict with feedback

#### Plan API Methods
- `get_plan_status_safe()`: Get plan status with error handling
- `get_plan_results_safe()`: Get results with retry logic
- `get_blueprint_safe()`: Get blueprint with error handling
- `create_plan_safe()`: Create plan with success messages
- `select_combination_safe()`: Select combination with feedback

#### Utility Methods
- `health_check_safe()`: Check API health
- `render_retry_button()`: Render retry button
- `check_stale_data()`: Check and warn about stale data

### 3. Updated Helpers (`utils/helpers.py`)

Enhanced helper functions that integrate with error handling:
- `show_success()`: Now supports optional details parameter
- `show_error()`: Enhanced with details support
- `show_warning()`: Enhanced with details support
- `show_info()`: Enhanced with details support

## Usage Examples

### Example 1: Loading Data with Error Handling

```python
from components.api_wrapper import api_wrapper

def render_page():
    # Load data with automatic error handling
    data = api_wrapper.get_extended_task_list_safe(plan_id, show_loading=True)
    
    if data is None:
        # Error already displayed, show retry button
        if st.button("🔄 Retry", type="primary"):
            st.rerun()
        return
    
    # Process data
    render_tasks(data)
```

### Example 2: Form Validation

```python
from utils.error_handling import error_handler, validate_form_field, Validators

def validate_form(form_data):
    # Validate email
    email_validators = {
        "Required": Validators.required,
        "Valid email format": Validators.email
    }
    
    if not validate_form_field(form_data['email'], "Email", email_validators):
        return False
    
    # Validate budget
    budget_validators = {
        "Required": Validators.required,
        "Must be numeric": Validators.numeric,
        "Must be positive": Validators.positive
    }
    
    if not validate_form_field(form_data['budget'], "Budget", budget_validators):
        return False
    
    return True
```

### Example 3: Saving Data with Feedback

```python
from components.api_wrapper import api_wrapper

def save_preferences(preferences_data):
    # Save with automatic error handling and success message
    result = api_wrapper.update_preferences_safe(preferences_data, show_loading=True)
    
    if result:
        # Success message already shown
        st.balloons()
        st.rerun()
    else:
        # Error already displayed
        pass
```

### Example 4: Stale Data Warning

```python
from utils.error_handling import StaleDataWarning
from datetime import datetime

def render_data_view():
    # Check if data is stale
    last_updated = st.session_state.get('data_last_updated')
    
    if last_updated and StaleDataWarning.render(last_updated, threshold_seconds=300):
        # User clicked refresh
        reload_data()
        st.rerun()
    
    # Display data
    render_data()
```

### Example 5: Custom Error Handling

```python
from utils.error_handling import with_error_handling, with_retry

@with_error_handling(context="processing data", show_spinner=True)
@with_retry(max_attempts=3)
def process_data(data):
    # Process data with automatic error handling and retry
    result = complex_processing(data)
    return result
```

## Error Message Guidelines

### User-Friendly Messages

All error messages follow these principles:

1. **Clear and Concise**: Explain what went wrong in simple terms
2. **Actionable**: Provide suggestions for what the user can do
3. **Contextual**: Include relevant context about the operation
4. **Consistent**: Use consistent language and formatting

### Error Message Format

```
❌ **Error Type**

[Description of what went wrong]

💡 **Suggestion**: [What the user can do to resolve it]
```

### Examples

**404 Not Found**:
```
❌ **Not Found**

The requested resource was not found.

💡 **Suggestion**: Check that the ID is correct or try refreshing the page.
```

**Connection Error**:
```
🔌 **Connection Error**

Cannot connect to the server.

💡 **Suggestion**: Check your internet connection and verify the server is running.
```

**Validation Error**:
```
❌ **Email**: Invalid email format

💡 **Suggestion**: Please enter a valid email address (e.g., user@example.com)
```

## Loading States

### Spinner Messages

Use descriptive spinner messages:
- "Loading preferences..."
- "Saving preferences..."
- "Loading communications..."
- "Loading tasks..."
- "Updating task..."
- "Applying resolution..."

### Progress Indicators

For long-running operations, use progress bars:
```python
with LoadingState("Processing...", show_progress=True) as loading:
    for i, item in enumerate(items):
        process_item(item)
        loading.update_progress((i + 1) / len(items))
```

## Success Messages

### Format

```
✅ [Action completed successfully]

[Optional details]
```

### Examples

- "✅ Preferences updated successfully!"
- "✅ Task status updated to 'completed'"
- "✅ Conflict resolved successfully!"
- "✅ Event plan created successfully!"

## Validation

### Field-Level Validation

Show validation errors immediately next to the field:
```python
error_handler.show_validation_error("Email", "Invalid email format")
```

### Form-Level Validation

Collect all validation errors and display them together:
```python
validation_errors = []

if not email:
    error_handler.show_validation_error("Email", "Required")
    validation_errors.append("email")

if not budget:
    error_handler.show_validation_error("Budget", "Required")
    validation_errors.append("budget")

if validation_errors:
    st.stop()
```

## Retry Mechanisms

### Automatic Retry

Use `@with_retry` decorator for automatic retry on transient failures:
```python
@with_retry(max_attempts=3, delay=1.0, backoff=2.0)
def fetch_data():
    return api_client.get_data()
```

### Manual Retry

Provide retry buttons for user-initiated retry:
```python
if data is None:
    if st.button("🔄 Retry", type="primary"):
        st.rerun()
```

## Testing

### Unit Tests

Run error handling tests:
```bash
pytest streamlit_gui/tests/test_error_handling.py -v
```

### Test Coverage

The test suite covers:
- Error handler methods
- Decorators (with_error_handling, with_retry)
- Validators
- Form validation
- Loading states
- Retry buttons
- Stale data warnings

## Best Practices

1. **Always use API wrapper methods** instead of direct API client calls
2. **Provide retry buttons** after errors
3. **Show loading spinners** for all data fetching operations
4. **Validate forms** before submission
5. **Show success messages** after successful operations
6. **Log errors** for debugging and monitoring
7. **Use consistent error message format** across all pages
8. **Provide actionable suggestions** in error messages
9. **Handle stale data** with warnings and refresh options
10. **Test error scenarios** thoroughly

## Integration Checklist

When adding error handling to a new page or component:

- [ ] Import error handling utilities
- [ ] Use API wrapper methods for all API calls
- [ ] Add loading spinners for data fetching
- [ ] Implement form validation with field-level errors
- [ ] Show success messages after successful operations
- [ ] Provide retry buttons after errors
- [ ] Handle stale data with warnings
- [ ] Log errors appropriately
- [ ] Test error scenarios
- [ ] Update documentation

## Future Enhancements

Potential improvements for the error handling system:

1. **Error Analytics**: Track error rates and types
2. **User Feedback**: Allow users to report errors
3. **Offline Support**: Handle offline scenarios gracefully
4. **Error Recovery**: Automatic recovery from certain errors
5. **Internationalization**: Translate error messages
6. **Custom Error Pages**: Dedicated error pages for critical failures
7. **Error Notifications**: Email/SMS notifications for critical errors
8. **Performance Monitoring**: Track API response times
9. **Circuit Breaker**: Prevent cascading failures
10. **Fallback Data**: Show cached data when API fails

## Support

For questions or issues with error handling:
- Review this documentation
- Check the test suite for examples
- Consult the inline code documentation
- Contact the development team

## Changelog

### Version 1.0 (Current)
- Initial implementation of error handling system
- API wrapper with error handling
- Validators and form validation
- Loading states and retry mechanisms
- Stale data warnings
- Comprehensive test suite
- Documentation

