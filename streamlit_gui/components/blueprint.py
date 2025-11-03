"""
Blueprint components for event plan display and export
"""
import streamlit as st
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import base64
from io import BytesIO
import tempfile
import os

from utils.helpers import show_error, show_success, show_info, format_currency


class BlueprintExporter:
    """Handles blueprint export functionality"""
    
    def __init__(self):
        self.supported_formats = ["PDF", "JSON", "Text", "HTML"]
    
    def export_blueprint(self, blueprint_data: Dict, format_type: str) -> bool:
        """Export blueprint in the specified format"""
        try:
            if format_type == "PDF":
                return self._export_pdf(blueprint_data)
            elif format_type == "JSON":
                return self._export_json(blueprint_data)
            elif format_type == "Text":
                return self._export_text(blueprint_data)
            elif format_type == "HTML":
                return self._export_html(blueprint_data)
            else:
                show_error(f"Unsupported export format: {format_type}")
                return False
                
        except Exception as e:
            show_error(f"Export failed: {str(e)}")
            return False
    
    def _export_pdf(self, blueprint_data: Dict) -> bool:
        """Export blueprint as PDF using reportlab"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            
            # Create PDF buffer
            buffer = BytesIO()
            
            # Create document
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
            styles = getSampleStyleSheet()
            story = []
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.HexColor('#2E86AB')
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.HexColor('#A23B72')
            )
            
            # Title page
            event_info = blueprint_data.get('event_info', {})
            title = f"Event Blueprint: {event_info.get('event_type', 'Event')}"
            story.append(Paragraph(title, title_style))
            
            subtitle = f"for {event_info.get('client_name', 'Client')}"
            story.append(Paragraph(subtitle, styles['Heading2']))
            story.append(Spacer(1, 20))
            
            # Event overview table
            story.append(Paragraph("Event Overview", heading_style))
            
            overview_data = [
                ['Event Date', event_info.get('event_date', 'TBD')],
                ['Event Time', event_info.get('event_time', 'TBD')],
                ['Guest Count', str(event_info.get('guest_count', 'TBD'))],
                ['Location', event_info.get('location', 'TBD')],
                ['Budget', format_currency(event_info.get('budget', 0))],
            ]
            
            overview_table = Table(overview_data, colWidths=[2*inch, 3*inch])
            overview_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F0F8FF')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(overview_table)
            story.append(Spacer(1, 20))
            
            # Vendor information
            story.append(Paragraph("Selected Vendors", heading_style))
            
            selected_combination = blueprint_data.get('selected_combination', {})
            vendors = ['venue', 'caterer', 'photographer', 'makeup_artist']
            vendor_names = {
                'venue': 'Venue',
                'caterer': 'Catering',
                'photographer': 'Photography',
                'makeup_artist': 'Makeup & Beauty'
            }
            
            vendor_data = [['Service', 'Vendor', 'Contact', 'Cost']]
            
            for vendor_type in vendors:
                vendor = selected_combination.get(vendor_type, {})
                if vendor.get('name'):
                    vendor_data.append([
                        vendor_names[vendor_type],
                        vendor['name'],
                        vendor.get('contact_phone', 'N/A'),
                        format_currency(vendor.get('cost', 0))
                    ])
            
            vendor_table = Table(vendor_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 1*inch])
            vendor_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
            ]))
            
            story.append(vendor_table)
            story.append(Spacer(1, 20))
            
            # Total cost
            total_cost = selected_combination.get('total_cost', 0)
            fitness_score = selected_combination.get('fitness_score', 0)
            
            summary_data = [
                ['Total Investment', format_currency(total_cost)],
                ['Fitness Score', f"{fitness_score:.1f}%"],
                ['Generated On', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#E8F5E8')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(summary_table)
            
            # Build PDF
            doc.build(story)
            
            # Prepare download
            buffer.seek(0)
            
            # Generate filename
            client_name = event_info.get('client_name', 'Client').replace(' ', '_')
            event_type = event_info.get('event_type', 'Event').replace(' ', '_')
            filename = f"{client_name}_{event_type}_Blueprint.pdf"
            
            # Create download button
            st.download_button(
                label="📄 Download PDF Blueprint",
                data=buffer.getvalue(),
                file_name=filename,
                mime="application/pdf",
                use_container_width=True
            )
            
            show_success("PDF blueprint generated successfully!")
            return True
            
        except ImportError:
            show_error("PDF export requires reportlab. Please install it: pip install reportlab")
            return False
        except Exception as e:
            show_error(f"PDF export failed: {str(e)}")
            return False
    
    def _export_json(self, blueprint_data: Dict) -> bool:
        """Export blueprint as JSON"""
        try:
            # Clean and format the data
            export_data = {
                'export_info': {
                    'generated_at': datetime.now().isoformat(),
                    'format': 'JSON',
                    'version': '1.0',
                    'generator': 'Event Planning Agent v2'
                },
                'blueprint': blueprint_data
            }
            
            # Convert to JSON with proper formatting
            json_data = json.dumps(export_data, indent=2, default=str, ensure_ascii=False)
            
            # Generate filename
            event_info = blueprint_data.get('event_info', {})
            client_name = event_info.get('client_name', 'Client').replace(' ', '_')
            event_type = event_info.get('event_type', 'Event').replace(' ', '_')
            filename = f"{client_name}_{event_type}_Blueprint.json"
            
            # Create download button
            st.download_button(
                label="📊 Download JSON Blueprint",
                data=json_data,
                file_name=filename,
                mime="application/json",
                use_container_width=True
            )
            
            show_success("JSON blueprint generated successfully!")
            return True
            
        except Exception as e:
            show_error(f"JSON export failed: {str(e)}")
            return False
    
    def _export_text(self, blueprint_data: Dict) -> bool:
        """Export blueprint as formatted text"""
        try:
            lines = []
            
            # Header
            event_info = blueprint_data.get('event_info', {})
            lines.append("=" * 80)
            lines.append("EVENT BLUEPRINT".center(80))
            lines.append("=" * 80)
            lines.append("")
            lines.append(f"Event Type: {event_info.get('event_type', 'Event')}")
            lines.append(f"Client: {event_info.get('client_name', 'Client')}")
            lines.append(f"Date: {event_info.get('event_date', 'TBD')}")
            lines.append(f"Time: {event_info.get('event_time', 'TBD')}")
            lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")
            
            # Event details section
            lines.append("EVENT DETAILS")
            lines.append("-" * 40)
            lines.append(f"Guest Count: {event_info.get('guest_count', 'TBD')}")
            lines.append(f"Budget: {format_currency(event_info.get('budget', 0))}")
            lines.append(f"Location: {event_info.get('location', 'TBD')}")
            
            # Client vision
            client_vision = event_info.get('client_vision', '')
            if client_vision:
                lines.append(f"Client Vision: {client_vision}")
            
            lines.append("")
            
            # Vendors section
            lines.append("SELECTED VENDORS")
            lines.append("-" * 40)
            
            selected_combination = blueprint_data.get('selected_combination', {})
            vendors = ['venue', 'caterer', 'photographer', 'makeup_artist']
            vendor_names = {
                'venue': 'VENUE',
                'caterer': 'CATERING',
                'photographer': 'PHOTOGRAPHY',
                'makeup_artist': 'MAKEUP & BEAUTY'
            }
            
            total_cost = 0
            
            for vendor_type in vendors:
                vendor = selected_combination.get(vendor_type, {})
                if vendor.get('name'):
                    lines.append(f"\n{vendor_names[vendor_type]}:")
                    lines.append(f"  Name: {vendor['name']}")
                    lines.append(f"  Cost: {format_currency(vendor.get('cost', 0))}")
                    lines.append(f"  Phone: {vendor.get('contact_phone', 'N/A')}")
                    lines.append(f"  Email: {vendor.get('contact_email', 'N/A')}")
                    
                    if vendor.get('location'):
                        lines.append(f"  Location: {vendor['location']}")
                    
                    # Add service-specific details
                    if vendor_type == 'venue':
                        capacity = vendor.get('capacity', {})
                        if capacity:
                            lines.append(f"  Capacity: {capacity.get('max_guests', 'N/A')} guests")
                        
                        amenities = vendor.get('amenities', [])
                        if amenities:
                            lines.append(f"  Amenities: {', '.join(amenities[:5])}")
                    
                    elif vendor_type == 'caterer':
                        cuisine_types = vendor.get('cuisine_types', [])
                        if cuisine_types:
                            lines.append(f"  Cuisine: {', '.join(cuisine_types)}")
                        
                        service_style = vendor.get('service_style', '')
                        if service_style:
                            lines.append(f"  Service Style: {service_style}")
                    
                    total_cost += vendor.get('cost', 0)
            
            lines.append("")
            
            # Summary section
            lines.append("SUMMARY")
            lines.append("-" * 40)
            lines.append(f"Total Investment: {format_currency(selected_combination.get('total_cost', total_cost))}")
            lines.append(f"Fitness Score: {selected_combination.get('fitness_score', 0):.1f}%")
            
            budget = event_info.get('budget', 0)
            if budget > 0:
                difference = selected_combination.get('total_cost', total_cost) - budget
                if difference > 0:
                    lines.append(f"Over Budget: {format_currency(difference)}")
                else:
                    lines.append(f"Under Budget: {format_currency(abs(difference))}")
            
            lines.append("")
            
            # Next steps
            lines.append("NEXT STEPS")
            lines.append("-" * 40)
            lines.append("1. Contact all vendors to confirm details and timeline")
            lines.append("2. Finalize guest count and dietary restrictions")
            lines.append("3. Create detailed day-of timeline with vendors")
            lines.append("4. Prepare vendor payments and tip envelopes")
            lines.append("5. Confirm setup and breakdown logistics")
            lines.append("")
            
            # Footer
            lines.append("=" * 80)
            lines.append("Generated by Event Planning Agent v2".center(80))
            lines.append("=" * 80)
            
            # Join lines
            text_content = "\n".join(lines)
            
            # Generate filename
            client_name = event_info.get('client_name', 'Client').replace(' ', '_')
            event_type = event_info.get('event_type', 'Event').replace(' ', '_')
            filename = f"{client_name}_{event_type}_Blueprint.txt"
            
            # Create download button
            st.download_button(
                label="📝 Download Text Blueprint",
                data=text_content,
                file_name=filename,
                mime="text/plain",
                use_container_width=True
            )
            
            show_success("Text blueprint generated successfully!")
            return True
            
        except Exception as e:
            show_error(f"Text export failed: {str(e)}")
            return False
    
    def _export_html(self, blueprint_data: Dict) -> bool:
        """Export blueprint as HTML"""
        try:
            event_info = blueprint_data.get('event_info', {})
            selected_combination = blueprint_data.get('selected_combination', {})
            
            # Generate HTML content with enhanced styling
            html_content = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Event Blueprint - {event_info.get('client_name', 'Client')}</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        margin: 0;
                        padding: 40px;
                        background-color: #f8f9fa;
                        color: #333;
                        line-height: 1.6;
                    }}
                    
                    .container {{
                        max-width: 800px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 15px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                        overflow: hidden;
                    }}
                    
                    .header {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 40px;
                        text-align: center;
                    }}
                    
                    .header h1 {{
                        margin: 0;
                        font-size: 2.5em;
                        font-weight: 300;
                    }}
                    
                    .header h2 {{
                        margin: 10px 0 0 0;
                        font-size: 1.5em;
                        font-weight: 300;
                        opacity: 0.9;
                    }}
                    
                    .content {{
                        padding: 40px;
                    }}
                    
                    .section {{
                        margin-bottom: 40px;
                    }}
                    
                    .section h2 {{
                        color: #2c3e50;
                        border-bottom: 3px solid #3498db;
                        padding-bottom: 10px;
                        margin-bottom: 20px;
                    }}
                    
                    .event-details {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 20px;
                        margin-bottom: 30px;
                    }}
                    
                    .detail-item {{
                        background: #f8f9fa;
                        padding: 15px;
                        border-radius: 8px;
                        border-left: 4px solid #3498db;
                    }}
                    
                    .detail-label {{
                        font-weight: bold;
                        color: #2c3e50;
                        margin-bottom: 5px;
                    }}
                    
                    .vendor {{
                        background: #ffffff;
                        border: 1px solid #e9ecef;
                        border-radius: 10px;
                        padding: 20px;
                        margin-bottom: 20px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                    }}
                    
                    .vendor-header {{
                        display: flex;
                        align-items: center;
                        margin-bottom: 15px;
                    }}
                    
                    .vendor-icon {{
                        font-size: 2em;
                        margin-right: 15px;
                    }}
                    
                    .vendor-name {{
                        font-size: 1.3em;
                        font-weight: bold;
                        color: #2c3e50;
                    }}
                    
                    .vendor-details {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 15px;
                    }}
                    
                    .cost {{
                        font-weight: bold;
                        color: #27ae60;
                        font-size: 1.1em;
                    }}
                    
                    .total-section {{
                        background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
                        color: white;
                        padding: 30px;
                        border-radius: 10px;
                        text-align: center;
                        margin: 30px 0;
                    }}
                    
                    .total-cost {{
                        font-size: 2.5em;
                        font-weight: bold;
                        margin-bottom: 10px;
                    }}
                    
                    .fitness-score {{
                        font-size: 1.2em;
                        opacity: 0.9;
                    }}
                    
                    .footer {{
                        text-align: center;
                        padding: 20px;
                        background: #f8f9fa;
                        color: #6c757d;
                        font-size: 0.9em;
                    }}
                    
                    @media print {{
                        body {{ padding: 0; }}
                        .container {{ box-shadow: none; }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 {event_info.get('event_type', 'Event')}</h1>
                        <h2>for {event_info.get('client_name', 'Client')}</h2>
                        <p>📅 {event_info.get('event_date', 'TBD')}</p>
                    </div>
                    
                    <div class="content">
                        <div class="section">
                            <h2>Event Details</h2>
                            <div class="event-details">
                                <div class="detail-item">
                                    <div class="detail-label">Guest Count</div>
                                    <div>{event_info.get('guest_count', 'TBD')}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Budget</div>
                                    <div>{format_currency(event_info.get('budget', 0))}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Location</div>
                                    <div>{event_info.get('location', 'TBD')}</div>
                                </div>
                                <div class="detail-item">
                                    <div class="detail-label">Time</div>
                                    <div>{event_info.get('event_time', 'TBD')}</div>
                                </div>
                            </div>
            """
            
            # Add client vision if available
            client_vision = event_info.get('client_vision', '')
            if client_vision:
                html_content += f"""
                            <div class="detail-item" style="grid-column: 1 / -1;">
                                <div class="detail-label">Client Vision</div>
                                <div>{client_vision}</div>
                            </div>
                """
            
            html_content += """
                        </div>
                        
                        <div class="section">
                            <h2>Selected Vendors</h2>
            """
            
            # Add vendor information
            vendors = ['venue', 'caterer', 'photographer', 'makeup_artist']
            vendor_icons = {'venue': '🏛️', 'caterer': '🍽️', 'photographer': '📸', 'makeup_artist': '💄'}
            vendor_names = {
                'venue': 'Venue',
                'caterer': 'Catering',
                'photographer': 'Photography',
                'makeup_artist': 'Makeup & Beauty'
            }
            
            for vendor_type in vendors:
                vendor = selected_combination.get(vendor_type, {})
                if vendor.get('name'):
                    icon = vendor_icons.get(vendor_type, '📋')
                    vendor_name = vendor_names[vendor_type]
                    
                    html_content += f"""
                    <div class="vendor">
                        <div class="vendor-header">
                            <div class="vendor-icon">{icon}</div>
                            <div>
                                <div class="vendor-name">{vendor['name']}</div>
                                <div style="color: #6c757d;">{vendor_name}</div>
                            </div>
                        </div>
                        <div class="vendor-details">
                            <div>
                                <strong>Cost:</strong><br>
                                <span class="cost">{format_currency(vendor.get('cost', 0))}</span>
                            </div>
                            <div>
                                <strong>Phone:</strong><br>
                                {vendor.get('contact_phone', 'N/A')}
                            </div>
                            <div>
                                <strong>Email:</strong><br>
                                {vendor.get('contact_email', 'N/A')}
                            </div>
                    """
                    
                    if vendor.get('location'):
                        html_content += f"""
                            <div>
                                <strong>Location:</strong><br>
                                {vendor['location']}
                            </div>
                        """
                    
                    html_content += """
                        </div>
                    </div>
                    """
            
            # Add total cost and summary
            total_cost = selected_combination.get('total_cost', 0)
            fitness_score = selected_combination.get('fitness_score', 0)
            
            html_content += f"""
                        </div>
                        
                        <div class="total-section">
                            <div class="total-cost">{format_currency(total_cost)}</div>
                            <div class="fitness-score">Fitness Score: {fitness_score:.1f}%</div>
                        </div>
                    </div>
                    
                    <div class="footer">
                        Generated by Event Planning Agent v2 on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Generate filename
            client_name = event_info.get('client_name', 'Client').replace(' ', '_')
            event_type = event_info.get('event_type', 'Event').replace(' ', '_')
            filename = f"{client_name}_{event_type}_Blueprint.html"
            
            # Create download button
            st.download_button(
                label="🌐 Download HTML Blueprint",
                data=html_content,
                file_name=filename,
                mime="text/html",
                use_container_width=True
            )
            
            show_success("HTML blueprint generated successfully!")
            return True
            
        except Exception as e:
            show_error(f"HTML export failed: {str(e)}")
            return False


class TimelineGenerator:
    """Generates event timelines and schedules"""
    
    def __init__(self):
        self.default_timeline_items = {
            'pre_event': [
                {'days_before': 30, 'task': 'Send save-the-dates', 'responsible': 'Client'},
                {'days_before': 21, 'task': 'Send formal invitations', 'responsible': 'Client'},
                {'days_before': 14, 'task': 'Confirm vendor details and timeline', 'responsible': 'Client'},
                {'days_before': 7, 'task': 'Finalize guest count with caterer', 'responsible': 'Client'},
                {'days_before': 3, 'task': 'Confirm setup logistics with venue', 'responsible': 'Venue'},
                {'days_before': 1, 'task': 'Prepare vendor payments and tips', 'responsible': 'Client'},
            ],
            'event_day': [
                {'time': '08:00', 'activity': 'Venue setup begins', 'vendor': 'Venue'},
                {'time': '10:00', 'activity': 'Catering setup', 'vendor': 'Caterer'},
                {'time': '12:00', 'activity': 'Photography equipment setup', 'vendor': 'Photographer'},
                {'time': '14:00', 'activity': 'Final venue walkthrough', 'vendor': 'All'},
                {'time': '15:00', 'activity': 'Makeup and beauty services begin', 'vendor': 'Makeup Artist'},
                {'time': '17:00', 'activity': 'Event begins', 'vendor': 'All'},
            ],
            'post_event': [
                {'task': 'Venue cleanup and breakdown', 'deadline': 'Same day', 'responsible': 'Venue'},
                {'task': 'Photo delivery timeline confirmation', 'deadline': '1 day after', 'responsible': 'Photographer'},
                {'task': 'Final vendor payments', 'deadline': '3 days after', 'responsible': 'Client'},
                {'task': 'Thank you notes to vendors', 'deadline': '1 week after', 'responsible': 'Client'},
            ]
        }
    
    def generate_timeline(self, blueprint_data: Dict) -> Dict:
        """Generate a comprehensive timeline for the event"""
        event_info = blueprint_data.get('event_info', {})
        selected_combination = blueprint_data.get('selected_combination', {})
        
        # Parse event date
        event_date_str = event_info.get('event_date', '')
        try:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
        except:
            event_date = datetime.now() + timedelta(days=30)  # Default to 30 days from now
        
        timeline = {
            'pre_event': self._generate_pre_event_timeline(event_date, selected_combination),
            'event_day': self._generate_event_day_timeline(event_info, selected_combination),
            'post_event': self._generate_post_event_timeline(selected_combination)
        }
        
        return timeline
    
    def _generate_pre_event_timeline(self, event_date: datetime, selected_combination: Dict) -> List[Dict]:
        """Generate pre-event timeline items"""
        timeline_items = []
        
        for item in self.default_timeline_items['pre_event']:
            task_date = event_date - timedelta(days=item['days_before'])
            
            timeline_items.append({
                'date': task_date.strftime('%Y-%m-%d'),
                'task': item['task'],
                'responsible': item['responsible'],
                'days_before': item['days_before']
            })
        
        # Add vendor-specific tasks
        vendors = ['venue', 'caterer', 'photographer', 'makeup_artist']
        for vendor_type in vendors:
            vendor = selected_combination.get(vendor_type, {})
            if vendor.get('name'):
                confirm_date = event_date - timedelta(days=7)
                timeline_items.append({
                    'date': confirm_date.strftime('%Y-%m-%d'),
                    'task': f'Final confirmation with {vendor["name"]}',
                    'responsible': 'Client',
                    'days_before': 7
                })
        
        # Sort by date
        timeline_items.sort(key=lambda x: x['date'])
        
        return timeline_items
    
    def _generate_event_day_timeline(self, event_info: Dict, selected_combination: Dict) -> List[Dict]:
        """Generate event day timeline"""
        timeline_items = []
        
        # Base timeline
        for item in self.default_timeline_items['event_day']:
            timeline_items.append({
                'time': item['time'],
                'activity': item['activity'],
                'vendor': item['vendor'],
                'notes': ''
            })
        
        # Customize based on vendors
        venue = selected_combination.get('venue', {})
        if venue.get('name'):
            timeline_items.append({
                'time': '07:00',
                'activity': f'Venue access begins at {venue["name"]}',
                'vendor': venue['name'],
                'notes': 'Coordinate with venue manager'
            })
        
        caterer = selected_combination.get('caterer', {})
        if caterer.get('name'):
            timeline_items.append({
                'time': '16:00',
                'activity': f'Final food preparation by {caterer["name"]}',
                'vendor': caterer['name'],
                'notes': 'Confirm guest count and dietary restrictions'
            })
        
        # Sort by time
        timeline_items.sort(key=lambda x: x['time'])
        
        return timeline_items
    
    def _generate_post_event_timeline(self, selected_combination: Dict) -> List[Dict]:
        """Generate post-event timeline"""
        timeline_items = []
        
        # Base timeline
        for item in self.default_timeline_items['post_event']:
            timeline_items.append({
                'task': item['task'],
                'deadline': item['deadline'],
                'responsible': item['responsible']
            })
        
        # Add vendor-specific follow-ups
        photographer = selected_combination.get('photographer', {})
        if photographer.get('name'):
            timeline_items.append({
                'task': f'Follow up with {photographer["name"]} on photo delivery',
                'deadline': '3 days after',
                'responsible': 'Client'
            })
        
        return timeline_items


# Global instances
blueprint_exporter = BlueprintExporter()
timeline_generator = TimelineGenerator()