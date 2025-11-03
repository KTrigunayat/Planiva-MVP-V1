"""
Export Utilities for Streamlit GUI

Provides export functionality for tasks, communications, and analytics data
in CSV and PDF formats with progress indicators and error handling.
"""

import logging
import csv
import io
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)


def with_export_error_handling(func: Callable) -> Callable:
    """
    Decorator for export functions to add consistent error handling.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ImportError as e:
            logger.error(f"Missing dependency for {func.__name__}: {e}")
            raise ImportError(
                f"Required library not installed. "
                f"Please install missing dependencies."
            )
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            raise RuntimeError(f"Export failed: {str(e)}")
    
    return wrapper


class DataExporter:
    """
    Export engine for Streamlit GUI data.
    
    Provides methods for exporting tasks, communications, and analytics
    to CSV and PDF formats.
    """
    
    def __init__(self):
        """Initialize exporter."""
        logger.info("DataExporter initialized")
    
    # ========== Task Export Methods ==========
    
    @with_export_error_handling
    def export_tasks_to_csv(self, tasks: List[Dict[str, Any]]) -> str:
        """
        Export task list to CSV format.
        
        Args:
            tasks: List of task dictionaries
            
        Returns:
            CSV content as string
        """
        output = io.StringIO()
        
        # Define CSV columns
        fieldnames = [
            'task_id', 'name', 'description', 'priority', 'status',
            'start_date', 'end_date', 'estimated_duration', 'estimated_duration_hours',
            'task_type', 'parent_task_id', 'assigned_vendor_name', 'assigned_vendor_type',
            'assigned_vendor_contact', 'fitness_score', 'dependencies',
            'logistics_transportation', 'logistics_equipment', 'logistics_setup',
            'conflicts', 'is_overdue', 'has_errors', 'has_warnings',
            'created_at', 'updated_at'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        
        # Write header
        writer.writerow({field: field.replace('_', ' ').title() for field in fieldnames})
        
        # Write task data
        for task in tasks:
            # Flatten nested data
            row = {
                'task_id': task.get('id', task.get('task_id', '')),
                'name': task.get('name', ''),
                'description': task.get('description', ''),
                'priority': task.get('priority', ''),
                'status': task.get('status', ''),
                'start_date': task.get('start_date', ''),
                'end_date': task.get('end_date', ''),
                'estimated_duration': task.get('estimated_duration', ''),
                'estimated_duration_hours': task.get('estimated_duration_hours', ''),
                'task_type': task.get('task_type', ''),
                'parent_task_id': task.get('parent_task_id', ''),
                'is_overdue': task.get('is_overdue', False),
                'has_errors': task.get('has_errors', False),
                'has_warnings': task.get('has_warnings', False),
                'created_at': task.get('created_at', ''),
                'updated_at': task.get('updated_at', '')
            }
            
            # Extract vendor information
            vendor = task.get('assigned_vendor', {})
            if vendor:
                row['assigned_vendor_name'] = vendor.get('name', '')
                row['assigned_vendor_type'] = vendor.get('type', '')
                row['assigned_vendor_contact'] = vendor.get('contact', '')
                row['fitness_score'] = vendor.get('fitness_score', '')
            
            # Extract dependencies
            dependencies = task.get('dependencies', [])
            if dependencies:
                dep_names = []
                for dep in dependencies:
                    if isinstance(dep, dict):
                        dep_names.append(dep.get('task_name', dep.get('task_id', '')))
                    else:
                        dep_names.append(str(dep))
                row['dependencies'] = '; '.join(dep_names)
            else:
                row['dependencies'] = ''
            
            # Extract logistics information
            logistics = task.get('logistics', {})
            if logistics:
                row['logistics_transportation'] = logistics.get('transportation', {}).get('status', '')
                row['logistics_equipment'] = logistics.get('equipment', {}).get('status', '')
                row['logistics_setup'] = logistics.get('setup', {}).get('status', '')
            
            # Extract conflicts
            conflicts = task.get('conflicts', [])
            if conflicts:
                conflict_descriptions = []
                for conflict in conflicts:
                    if isinstance(conflict, dict):
                        conflict_descriptions.append(
                            f"{conflict.get('type', 'unknown')}: {conflict.get('description', '')}"
                        )
                    else:
                        conflict_descriptions.append(str(conflict))
                row['conflicts'] = '; '.join(conflict_descriptions)
            else:
                row['conflicts'] = ''
            
            writer.writerow(row)
        
        csv_content = output.getvalue()
        logger.info(f"Exported {len(tasks)} tasks to CSV")
        return csv_content
    
    # ========== Communication Export Methods ==========
    
    @with_export_error_handling
    def export_communications_to_csv(self, communications: List[Dict[str, Any]]) -> str:
        """
        Export communication history to CSV format.
        
        Args:
            communications: List of communication dictionaries
            
        Returns:
            CSV content as string
        """
        output = io.StringIO()
        
        # Define CSV columns
        fieldnames = [
            'communication_id', 'plan_id', 'client_id', 'channel',
            'message_type', 'status', 'delivery_status', 'recipient',
            'subject', 'priority', 'sent_at', 'delivered_at', 'opened_at',
            'clicked_at', 'open_count', 'click_count', 'retry_count',
            'error_message', 'created_at'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        
        # Write header
        writer.writerow({field: field.replace('_', ' ').title() for field in fieldnames})
        
        # Write communication data
        for comm in communications:
            row = {
                'communication_id': comm.get('communication_id', ''),
                'plan_id': comm.get('plan_id', ''),
                'client_id': comm.get('client_id', ''),
                'channel': comm.get('channel', ''),
                'message_type': comm.get('message_type', ''),
                'status': comm.get('status', ''),
                'delivery_status': comm.get('delivery_status', ''),
                'recipient': comm.get('recipient', ''),
                'subject': comm.get('subject', ''),
                'priority': comm.get('priority', ''),
                'sent_at': comm.get('sent_at', ''),
                'delivered_at': comm.get('delivered_at', ''),
                'opened_at': comm.get('opened_at', ''),
                'clicked_at': comm.get('clicked_at', ''),
                'open_count': comm.get('open_count', 0),
                'click_count': comm.get('click_count', 0),
                'retry_count': comm.get('retry_count', 0),
                'error_message': comm.get('error_message', ''),
                'created_at': comm.get('created_at', '')
            }
            
            writer.writerow(row)
        
        csv_content = output.getvalue()
        logger.info(f"Exported {len(communications)} communications to CSV")
        return csv_content
    
    # ========== Analytics Export Methods ==========
    
    @with_export_error_handling
    def export_analytics_to_csv(self, analytics_data: Dict[str, Any]) -> str:
        """
        Export analytics data to CSV format.
        
        Args:
            analytics_data: Analytics data dictionary
            
        Returns:
            CSV content as string
        """
        output = io.StringIO()
        
        # Export key metrics
        output.write("KEY METRICS\n")
        output.write("Metric,Value\n")
        
        metrics = analytics_data.get("metrics", {})
        for key, value in metrics.items():
            output.write(f"{key.replace('_', ' ').title()},{value}\n")
        
        output.write("\n")
        
        # Export channel performance
        output.write("CHANNEL PERFORMANCE\n")
        channel_performance = analytics_data.get("channel_performance", [])
        
        if channel_performance:
            # Get all keys from first item
            if isinstance(channel_performance, list) and channel_performance:
                fieldnames = list(channel_performance[0].keys())
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(channel_performance)
            elif isinstance(channel_performance, dict):
                # Handle dict format
                output.write("Channel,Sent,Delivered,Opened,Clicked,Failed,Delivery Rate,Open Rate,CTR\n")
                for channel, data in channel_performance.items():
                    output.write(
                        f"{channel},"
                        f"{data.get('sent', 0)},"
                        f"{data.get('delivered', 0)},"
                        f"{data.get('opened', 0)},"
                        f"{data.get('clicked', 0)},"
                        f"{data.get('failed', 0)},"
                        f"{data.get('delivery_rate', 0)},"
                        f"{data.get('open_rate', 0)},"
                        f"{data.get('click_through_rate', 0)}\n"
                    )
        
        output.write("\n")
        
        # Export message type performance
        output.write("MESSAGE TYPE PERFORMANCE\n")
        message_type_performance = analytics_data.get("message_type_performance", [])
        
        if message_type_performance:
            if isinstance(message_type_performance, list) and message_type_performance:
                fieldnames = list(message_type_performance[0].keys())
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(message_type_performance)
            elif isinstance(message_type_performance, dict):
                # Handle dict format
                output.write("Message Type,Sent,Delivered,Opened,Clicked,Delivery Rate,Open Rate,CTR\n")
                for msg_type, data in message_type_performance.items():
                    output.write(
                        f"{msg_type},"
                        f"{data.get('sent', 0)},"
                        f"{data.get('delivered', 0)},"
                        f"{data.get('opened', 0)},"
                        f"{data.get('clicked', 0)},"
                        f"{data.get('delivery_rate', 0)},"
                        f"{data.get('open_rate', 0)},"
                        f"{data.get('click_through_rate', 0)}\n"
                    )
        
        output.write("\n")
        
        # Export timeline data
        output.write("TIMELINE DATA\n")
        timeline_data = analytics_data.get("timeline_data", [])
        
        if timeline_data and isinstance(timeline_data, list) and timeline_data:
            fieldnames = list(timeline_data[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(timeline_data)
        
        csv_content = output.getvalue()
        logger.info("Exported analytics data to CSV")
        return csv_content
    
    # ========== PDF Export Methods ==========
    
    def export_analytics_to_pdf(
        self,
        analytics_data: Dict[str, Any],
        title: str = "Communication Analytics Report"
    ) -> bytes:
        """
        Export analytics data to PDF format.
        
        Args:
            analytics_data: Analytics data dictionary
            title: Report title
            
        Returns:
            PDF content as bytes
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.enums import TA_CENTER
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch,
                leftMargin=0.75*inch,
                rightMargin=0.75*inch
            )
            
            # Container for PDF elements
            elements = []
            
            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1f77b4'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=12,
                spaceBefore=12
            )
            
            # Title
            elements.append(Paragraph(title, title_style))
            elements.append(
                Paragraph(
                    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    styles['Normal']
                )
            )
            elements.append(Spacer(1, 0.3*inch))
            
            # Key Metrics
            metrics = analytics_data.get("metrics", {})
            if metrics:
                elements.append(Paragraph("Key Metrics", heading_style))
                
                metrics_data = [['Metric', 'Value']]
                for key, value in metrics.items():
                    metrics_data.append([key.replace('_', ' ').title(), str(value)])
                
                table = Table(metrics_data, colWidths=[3*inch, 2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
                elements.append(Spacer(1, 0.3*inch))
            
            # Channel Performance
            channel_performance = analytics_data.get("channel_performance", [])
            if channel_performance:
                elements.append(Paragraph("Channel Performance", heading_style))
                
                channel_data = [['Channel', 'Sent', 'Delivered', 'Delivery %', 'Open %', 'CTR %']]
                
                # Handle both list and dict formats
                if isinstance(channel_performance, list):
                    for item in channel_performance:
                        channel_data.append([
                            item.get('channel', ''),
                            str(item.get('sent', 0)),
                            str(item.get('delivered', 0)),
                            f"{item.get('delivery_rate', 0):.1f}%",
                            f"{item.get('open_rate', 0):.1f}%",
                            f"{item.get('click_through_rate', 0):.1f}%"
                        ])
                elif isinstance(channel_performance, dict):
                    for channel, metrics in channel_performance.items():
                        channel_data.append([
                            channel,
                            str(metrics.get('total_sent', 0)),
                            str(metrics.get('delivered_count', 0)),
                            f"{metrics.get('delivery_rate', 0):.1f}%",
                            f"{metrics.get('open_rate', 0):.1f}%",
                            f"{metrics.get('click_through_rate', 0):.1f}%"
                        ])
                
                table = Table(channel_data, colWidths=[1.2*inch, 0.8*inch, 1*inch, 1*inch, 1*inch, 1*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
                elements.append(Spacer(1, 0.3*inch))
            
            # Message Type Performance
            message_type_performance = analytics_data.get("message_type_performance", [])
            if message_type_performance:
                elements.append(Paragraph("Message Type Performance", heading_style))
                
                msg_data = [['Message Type', 'Sent', 'Delivered', 'Delivery %', 'Open %']]
                
                # Handle both list and dict formats
                if isinstance(message_type_performance, list):
                    for item in message_type_performance:
                        msg_data.append([
                            item.get('message_type', '').replace('_', ' ').title(),
                            str(item.get('sent', 0)),
                            str(item.get('delivered', 0)),
                            f"{item.get('delivery_rate', 0):.1f}%",
                            f"{item.get('open_rate', 0):.1f}%"
                        ])
                elif isinstance(message_type_performance, dict):
                    for msg_type, metrics in message_type_performance.items():
                        msg_data.append([
                            msg_type.replace('_', ' ').title(),
                            str(metrics.get('total_sent', 0)),
                            str(metrics.get('delivered_count', 0)),
                            f"{metrics.get('delivery_rate', 0):.1f}%",
                            f"{metrics.get('open_rate', 0):.1f}%"
                        ])
                
                table = Table(msg_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch, 1*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
                elements.append(Spacer(1, 0.3*inch))
            
            # Build PDF
            doc.build(elements)
            pdf_content = buffer.getvalue()
            buffer.close()
            
            logger.info("Exported analytics data to PDF")
            return pdf_content
            
        except ImportError as e:
            logger.error(f"ReportLab not installed: {e}")
            raise ImportError(
                "ReportLab is required for PDF export. "
                "Install it with: pip install reportlab"
            )
        except Exception as e:
            logger.error(f"Error exporting to PDF: {e}")
            raise


# Singleton instance
_exporter_instance = None


def get_exporter() -> DataExporter:
    """Get singleton exporter instance."""
    global _exporter_instance
    if _exporter_instance is None:
        _exporter_instance = DataExporter()
    return _exporter_instance
