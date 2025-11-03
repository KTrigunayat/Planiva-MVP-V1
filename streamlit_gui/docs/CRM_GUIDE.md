# CRM & Communication Management User Guide

This guide covers the CRM and Communication Management features of the Event Planning Agent v2 Streamlit GUI.

## Overview

The CRM module helps you manage client communication preferences, track all interactions, and analyze communication effectiveness. It ensures clients receive timely, relevant information through their preferred channels.

## Features

### 1. Communication Preferences

The Preferences page allows you to configure how and when clients receive communications.

#### Accessing Preferences
1. Navigate to **"💬 Communications"** → **"Preferences"** in the sidebar
2. Enter or select the client ID/email
3. The system will load existing preferences or show defaults

#### Setting Up Preferences

##### Preferred Communication Channels
Select one or more channels for client communications:
- **Email**: Traditional email communications
- **SMS**: Text message notifications
- **WhatsApp**: WhatsApp messages

You can select multiple channels. The system will use all selected channels based on message type and urgency.

##### Timezone Configuration
1. Select the client's timezone from the dropdown
2. This ensures messages are sent at appropriate local times
3. All timestamps in communications will be displayed in this timezone

##### Quiet Hours
Set times when the client should not receive non-urgent communications:
1. **Start Time**: When quiet hours begin (e.g., 10:00 PM)
2. **End Time**: When quiet hours end (e.g., 8:00 AM)
3. Critical messages may still be sent during quiet hours

##### Opt-Out Options
Allow clients to opt out of specific communication types:
- **Email Opt-Out**: Stop all email communications
- **SMS Opt-Out**: Stop all SMS messages
- **WhatsApp Opt-Out**: Stop all WhatsApp messages

Note: Critical event-related communications may still be sent even if opted out.

#### Saving Preferences
1. Review all settings
2. Click **"Save Preferences"**
3. A success message will confirm the update
4. Preferences take effect immediately

#### Updating Preferences
1. Load existing preferences by entering the client ID
2. Modify any settings
3. Save to update

### 2. Communication History

The History page provides a complete record of all client communications.

#### Accessing Communication History
1. Navigate to **"💬 Communications"** → **"History"** in the sidebar
2. Enter the client ID to view their communication history
3. The system will load all communications for that client

#### Communication Information
Each communication entry shows:
- **Message Type**: Category of the message (welcome, budget_summary, vendor_options, etc.)
- **Channel**: How it was sent (Email, SMS, WhatsApp)
- **Status**: Current delivery status
  - Sent: Message has been sent
  - Delivered: Message reached the recipient
  - Opened: Recipient opened the message (email only)
  - Clicked: Recipient clicked a link (email only)
  - Failed: Delivery failed
- **Sent Time**: When the message was sent
- **Delivery Time**: When the message was delivered
- **Subject**: Message subject line (email only)
- **Content Preview**: First few lines of the message

#### Filtering Communications
Use filters to narrow down the list:
- **By Channel**: Show only Email, SMS, or WhatsApp
- **By Status**: Filter by Sent, Delivered, Opened, Failed
- **By Date Range**: Select start and end dates
- **By Message Type**: Filter by specific message categories

#### Viewing Full Message Content
1. Click on a communication entry to expand it
2. View the complete message content
3. See all metadata (timestamps, tracking info)
4. Check engagement metrics for emails

#### Email Engagement Tracking
For email communications, you can see:
- **Open Rate**: Whether the email was opened
- **Open Time**: When it was first opened
- **Click Tracking**: Which links were clicked
- **Click Time**: When links were clicked

#### Real-Time Updates
The communication history automatically refreshes every 30 seconds to show:
- New delivery confirmations
- Updated engagement metrics
- Status changes for pending messages

#### Exporting Communication History
1. Apply any desired filters
2. Click **"Export to CSV"**
3. Download the CSV file with all filtered communications
4. Use for reporting, analysis, or record-keeping

### 3. Analytics Dashboard

The Analytics page provides insights into communication effectiveness.

#### Accessing Analytics
1. Navigate to **"💬 Communications"** → **"Analytics"** in the sidebar
2. Select a date range for analysis
3. View comprehensive metrics and charts

#### Key Metrics Overview
The dashboard displays five key metrics:
1. **Total Sent**: Number of messages sent
2. **Total Delivered**: Successfully delivered messages
3. **Total Opened**: Messages opened by recipients (email only)
4. **Total Clicked**: Messages with link clicks (email only)
5. **Total Failed**: Failed delivery attempts

Each metric shows:
- Current value
- Percentage change from previous period
- Visual indicator (up/down arrow)

#### Channel Performance
Compare effectiveness across communication channels:

**Metrics by Channel:**
- **Sent**: Messages sent via this channel
- **Delivered**: Successfully delivered
- **Delivery Rate**: Percentage successfully delivered
- **Open Rate**: Percentage opened (email only)
- **Click-Through Rate**: Percentage with clicks (email only)

**Channel Comparison Chart:**
- Bar chart comparing delivery rates
- Pie chart showing channel distribution
- Line chart showing trends over time

#### Message Type Performance
Analyze effectiveness by message category:
- Welcome messages
- Budget summaries
- Vendor options
- Timeline updates
- Confirmation messages
- Reminder messages

**Metrics by Type:**
- Sent count
- Delivery rate
- Engagement rate
- Average time to open

#### Timeline Analysis
View communication trends over time:
- **Volume Chart**: Messages sent per day/week
- **Engagement Chart**: Opens and clicks over time
- **Delivery Success**: Delivery rate trends
- **Channel Mix**: How channel usage changes over time

#### Exporting Analytics
1. Click **"Export Analytics"**
2. Choose format:
   - CSV: Detailed data for spreadsheet analysis
   - PDF: Formatted report with charts
3. Download and share with stakeholders

## Best Practices

### Setting Preferences
1. **Confirm timezone**: Verify the client's timezone is correct
2. **Respect quiet hours**: Set appropriate quiet hours for the client's schedule
3. **Multiple channels**: Enable multiple channels for redundancy
4. **Update regularly**: Review and update preferences as client needs change

### Managing Communications
1. **Monitor delivery**: Check history regularly for failed deliveries
2. **Track engagement**: Use open and click rates to gauge interest
3. **Respond to failures**: Investigate and resolve delivery failures promptly
4. **Maintain records**: Export history periodically for compliance

### Analyzing Performance
1. **Review weekly**: Check analytics at least weekly
2. **Compare channels**: Identify which channels work best
3. **Optimize timing**: Use engagement data to improve send times
4. **Test message types**: Experiment with different message formats
5. **Track trends**: Monitor changes in engagement over time

### Privacy and Compliance
1. **Honor opt-outs**: Respect client communication preferences
2. **Secure data**: Keep client information confidential
3. **Maintain records**: Keep communication logs for compliance
4. **Update preferences**: Ensure preferences are current and accurate

## Troubleshooting

### Preferences Not Saving
- Check that all required fields are filled
- Verify the client ID is correct
- Ensure you have network connectivity
- Check for error messages
- Try refreshing the page

### Communications Not Appearing
- Verify the correct client ID is entered
- Check that communications have been sent
- Ensure the date range includes the messages
- Clear any active filters
- Refresh the page

### Analytics Not Loading
- Confirm the date range is valid
- Check that communications exist in the period
- Verify API connectivity
- Try a different date range
- Clear browser cache

### Failed Deliveries
Common reasons for delivery failures:
- Invalid recipient contact information
- Temporary service outages
- Recipient's inbox full (email)
- Number not in service (SMS)
- Blocked sender (any channel)

**Resolution steps:**
1. Verify contact information is correct
2. Check service status for the channel
3. Try an alternative channel
4. Contact the recipient to confirm details
5. Review error messages for specific issues

### Engagement Tracking Not Working
- Ensure tracking is enabled for the channel
- Verify the message type supports tracking
- Check that the recipient's email client allows tracking
- Some email clients block tracking pixels
- SMS and WhatsApp don't support open tracking

## Tips and Tricks

1. **Use filters effectively**: Narrow down large communication lists quickly
2. **Export regularly**: Keep offline records of important communications
3. **Monitor trends**: Watch for patterns in engagement
4. **Test channels**: Try different channels to see what works best
5. **Timing matters**: Use analytics to find optimal send times
6. **Personalize**: Use client preferences to tailor communications
7. **Follow up**: Check for opens and clicks, follow up on unopened messages
8. **Keep it clean**: Regularly update and verify contact information

## Understanding Metrics

### Delivery Rate
- **Formula**: (Delivered / Sent) × 100
- **Good Rate**: 95% or higher
- **Low Rate**: Below 90% indicates issues

### Open Rate (Email)
- **Formula**: (Opened / Delivered) × 100
- **Good Rate**: 20-30% for event communications
- **Low Rate**: Below 15% may indicate poor subject lines or timing

### Click-Through Rate (Email)
- **Formula**: (Clicked / Opened) × 100
- **Good Rate**: 10-20% for event communications
- **Low Rate**: Below 5% may indicate poor content or unclear calls-to-action

### Engagement Score
- Combines delivery, open, and click rates
- Higher scores indicate more effective communications
- Use to compare message types and channels

## Mobile Usage

The CRM features are fully responsive:
- **Preferences**: Easy-to-use form on mobile devices
- **History**: Scrollable list with touch-friendly controls
- **Analytics**: Charts optimized for small screens
- **Filters**: Collapsible filter panels for mobile

## Integration with Task Management

CRM and Task Management work together:
- Task updates can trigger client communications
- Communication preferences affect notification timing
- Analytics help optimize task-related messages
- Client engagement influences task prioritization

## Compliance and Privacy

### Data Protection
- All client data is encrypted
- Communication logs are secure
- Access is controlled and audited
- Data retention follows regulations

### Opt-Out Compliance
- Opt-outs are honored immediately
- Critical messages may override opt-outs
- Opt-out status is clearly displayed
- Easy opt-in process available

### Record Keeping
- All communications are logged
- Timestamps are accurate and immutable
- Export capabilities for compliance reporting
- Audit trail for all preference changes

## Support

For additional help:
1. Check the main README.md for general troubleshooting
2. Review the API documentation for backend issues
3. Contact your system administrator for access problems
4. Report bugs through your organization's support channel
5. Consult privacy team for compliance questions
