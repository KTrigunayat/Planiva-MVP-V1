# User Guide - Event Planning Agent v2 GUI

Welcome to the Event Planning Agent v2 Streamlit GUI! This guide will help you navigate and use all the features of the application.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Creating Your First Event Plan](#creating-your-first-event-plan)
3. [Monitoring Progress](#monitoring-progress)
4. [Reviewing Results](#reviewing-results)
5. [Managing Your Plans](#managing-your-plans)
6. [Downloading Blueprints](#downloading-blueprints)
7. [Tips and Best Practices](#tips-and-best-practices)
8. [Troubleshooting](#troubleshooting)

## Getting Started

### Accessing the Application

1. Open your web browser
2. Navigate to the application URL (typically `http://localhost:8501` for local development)
3. You should see the Event Planning Agent homepage

### Navigation

The application uses a sidebar navigation with the following sections:
- 🏠 **Home**: Overview and plan management
- ➕ **Create Plan**: Start a new event plan
- 📊 **Plan Status**: Monitor active plans
- 🎯 **Results**: Review vendor combinations
- 📋 **Blueprint**: View and download final plans

## Creating Your First Event Plan

### Step 1: Basic Information

1. Click on "➕ Create Plan" in the sidebar
2. Fill out the basic information:
   - **Client Name**: Enter the name of the person/organization
   - **Client Email**: Contact email address
   - **Client Phone**: Phone number for contact
   - **Event Type**: Select from dropdown (Wedding, Corporate Event, Birthday Party, etc.)
   - **Event Date**: Choose the date using the date picker
   - **Location**: Enter the city or area for the event

### Step 2: Guest Information

1. **Total Guests**: Enter the expected number of attendees
2. **Ceremony vs Reception Split** (for weddings):
   - Ceremony Guests: Number attending the ceremony
   - Reception Guests: Number attending the reception
3. **Special Considerations**: Any specific guest requirements

### Step 3: Budget Planning

1. **Total Budget**: Enter your overall budget for the event
2. **Budget Priorities**: Use sliders to indicate how you want to allocate budget:
   - Venue (typically 40-50% of budget)
   - Catering (typically 25-35% of budget)
   - Photography (typically 10-15% of budget)
   - Other services (remaining budget)

### Step 4: Venue Preferences

Select your preferences for:
- **Venue Types**: Indoor, Outdoor, Garden, Ballroom, etc.
- **Essential Amenities**: Parking, Kitchen, Sound System, etc.
- **Location Preferences**: Specific areas or neighborhoods
- **Capacity Requirements**: Minimum and maximum capacity

### Step 5: Catering Preferences

Choose your catering options:
- **Cuisine Types**: Italian, American, Asian, Mediterranean, etc.
- **Dietary Restrictions**: Vegetarian, Vegan, Gluten-free, etc.
- **Service Style**: Buffet, Plated, Family Style, Cocktail
- **Beverage Preferences**: Full bar, Wine only, Non-alcoholic

### Step 6: Additional Services

Specify requirements for:
- **Photography**: Style preferences, package requirements
- **Videography**: Coverage needs, editing requirements
- **Makeup Services**: Bridal makeup, number of people
- **Entertainment**: DJ, Band, Special performances
- **Transportation**: Guest shuttles, special vehicle needs

### Step 7: Client Vision

1. **Detailed Description**: Describe the overall vision and atmosphere
2. **Theme Preferences**: Specific themes or styles
3. **Color Scheme**: Preferred colors or color combinations
4. **Style Preferences**: Elegant, Casual, Modern, Traditional, etc.

### Step 8: Review and Submit

1. Review all entered information
2. Make any necessary corrections
3. Click "Submit Plan" to start the planning process

## Monitoring Progress

### Real-Time Updates

Once you submit a plan, navigate to "📊 Plan Status" to monitor progress:

1. **Progress Bar**: Shows overall completion percentage
2. **Current Step**: Indicates which phase is currently active:
   - 🚀 Initializing Planning Process
   - 💰 Analyzing Budget Requirements
   - 🔍 Sourcing Vendors
   - 🎯 Optimizing Combinations
   - 👤 Awaiting Selection
   - 📋 Generating Blueprint

3. **Agent Activity**: Shows which AI agent is currently working
4. **Estimated Time**: Remaining time for completion
5. **Status Messages**: Real-time updates from the system

### Understanding the Process

The planning process involves several AI agents:
- **Orchestrator Agent**: Manages the overall workflow
- **Budget Agent**: Analyzes and allocates budget
- **Sourcing Agent**: Finds and evaluates vendors
- **Optimization Agent**: Creates optimal vendor combinations

## Reviewing Results

### Viewing Combinations

When planning is complete, go to "🎯 Results" to see vendor combinations:

1. **Combination Cards**: Each card shows:
   - Fitness Score (how well it matches your requirements)
   - Total Cost
   - Vendor summary for each category

2. **Detailed View**: Click "View Details" to see:
   - Complete vendor information
   - Contact details
   - Pricing breakdown
   - Amenities and features

### Comparison Tools

Use the comparison features to evaluate options:

1. **Sort Options**:
   - By Fitness Score (highest first)
   - By Total Cost (lowest first)
   - By Venue Location

2. **Filter Options**:
   - Minimum fitness score
   - Maximum budget
   - Specific vendor types

3. **Side-by-Side Comparison**:
   - Select multiple combinations
   - Compare key metrics
   - Highlight differences

### Making Your Selection

1. Review all available combinations
2. Consider both fitness score and total cost
3. Read vendor details carefully
4. Click "Select This Combination" on your preferred option

## Managing Your Plans

### Plan Overview

The "🏠 Home" section shows all your plans:

1. **Active Plans**: Currently in progress
2. **Completed Plans**: Finished plans with blueprints
3. **Draft Plans**: Saved but not submitted

### Plan Actions

For each plan, you can:
- **View Details**: See plan information
- **Monitor Progress**: Check current status
- **View Results**: See vendor combinations (when ready)
- **Download Blueprint**: Get final plan document
- **Delete Plan**: Remove unwanted plans

### Search and Filter

Use the search and filter tools to find specific plans:
- Search by client name or event type
- Filter by status (Active, Completed, Draft)
- Sort by date created or event date

## Downloading Blueprints

### Blueprint Contents

The final blueprint includes:

1. **Executive Summary**: Overview of the event plan
2. **Event Timeline**: Detailed schedule of activities
3. **Vendor Contact Sheet**: All vendor information
4. **Logistics Plan**: Setup, coordination details
5. **Budget Breakdown**: Detailed cost analysis
6. **Next Steps Checklist**: Action items for implementation

### Download Options

Choose from multiple formats:

1. **PDF Download**: Professional formatted document
2. **JSON Export**: Machine-readable data format
3. **Formatted Text**: Simple text version
4. **Email Sharing**: Send directly to stakeholders

### Using Your Blueprint

The blueprint serves as your complete event planning guide:
- Share with vendors for coordination
- Use timeline for day-of coordination
- Reference contact sheet for communications
- Follow next steps checklist for implementation

## Tips and Best Practices

### Planning Tips

1. **Be Specific**: Provide detailed requirements for better matches
2. **Realistic Budget**: Set achievable budget expectations
3. **Flexible Dates**: Consider multiple date options if possible
4. **Priority Setting**: Clearly indicate what's most important

### Using the Interface

1. **Save Progress**: The system auto-saves form data
2. **Mobile Friendly**: Works well on tablets and phones
3. **Browser Compatibility**: Use modern browsers for best experience
4. **Session Management**: Plans remain accessible across sessions

### Getting Better Results

1. **Complete All Sections**: More information leads to better matches
2. **Review Preferences**: Double-check all selections before submitting
3. **Consider Alternatives**: Review multiple combinations before deciding
4. **Ask Questions**: Contact vendors directly for clarification

## Troubleshooting

### Common Issues

#### Plan Not Submitting
- Check that all required fields are filled
- Ensure budget is realistic for requirements
- Verify date is in the future
- Check internet connection

#### Slow Loading
- Refresh the page
- Clear browser cache
- Check internet connection
- Try a different browser

#### Missing Results
- Wait for processing to complete (can take 10-30 minutes)
- Check plan status for any errors
- Verify API connection is working
- Contact support if issues persist

#### Download Problems
- Ensure pop-ups are allowed in browser
- Try different download format
- Check available disk space
- Use "Save As" if direct download fails

### Error Messages

#### "API Connection Failed"
- Check internet connection
- Verify API server is running
- Contact system administrator

#### "Validation Error"
- Review form inputs for errors
- Check required fields are completed
- Ensure data formats are correct

#### "Processing Timeout"
- Plan may be too complex
- Try simplifying requirements
- Contact support for assistance

### Getting Help

If you encounter issues:

1. **Check Status Page**: Look for system-wide issues
2. **Review User Guide**: Ensure you're following correct procedures
3. **Contact Support**: Use the help contact information
4. **Report Bugs**: Provide detailed error descriptions

### Browser Requirements

For optimal experience:
- **Chrome**: Version 90 or later
- **Firefox**: Version 88 or later
- **Safari**: Version 14 or later
- **Edge**: Version 90 or later

### Performance Tips

1. **Close Unused Tabs**: Improves browser performance
2. **Clear Cache**: Regularly clear browser cache
3. **Stable Connection**: Use reliable internet connection
4. **Modern Device**: Use devices with adequate processing power

## Advanced Features

### Bulk Operations
- Create multiple plans simultaneously
- Export multiple blueprints
- Batch status checking

### Integration Options
- Calendar integration for event dates
- Email notifications for status updates
- API access for custom integrations

### Customization
- Save preference templates
- Custom vendor requirements
- Personalized dashboard views

This user guide covers all major features of the Event Planning Agent v2 GUI. For additional support or feature requests, please contact the development team.