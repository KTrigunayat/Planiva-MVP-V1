"""
CRM Export Module

Provides export functionality for analytics data in CSV and PDF formats.
"""

import logging
import csv
import io
from typing import Dict, Any, List, Optional
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus import Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT

logger = logging.getLogger(__name__)


class CRMExporter:
    """
    Export engine for CRM analytics data.
    
    Provides methods for exporting analytics to CSV and PDF formats.
    """
    
    def __init__(self):
        """Initialize exporter"""
        logger.info("CRMExporter initialized")
    
    def export_to_csv(
        self,
        data: Dict[str, Any],
        export_type: str = 'comprehensive'
    ) -> str:
        """
        Export analytics data to CSV format.
        
        Args:
            data: Analytics data dictionary
            export_type: Type of export ('comprehensive', 'channel', 'message_type', 'timeline')
            
        Returns:
            CSV content as string
        """
        output = io.StringIO()
        
        if export_type == 'comprehensive':
            self._export_comprehensive_csv(data, output)
        elif export_type == 'channel':
            self._export_channel_csv(data, output)
        elif export_type == 'message_type':
            self._export_message_type_csv(data, output)
        elif export_type == 'timeline':
            self._export_timeline_csv(data, output)
        else:
            raise ValueError(f"Unknown export type: {export_type}")
        
        csv_content = output.getvalue()
        logger.info(f"Exported {export_type} data to CSV")
        return csv_content
    
    def _export_comprehensive_csv(self, data: Dict[str, Any], output: io.StringIO):
        """Export comprehensive analytics to CSV"""
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['CRM Communication Analytics Report'])
        writer.writerow(['Generated:', datetime.utcnow().isoformat()])
        writer.writerow([])
        
        # Period
        if 'period' in data:
            writer.writerow(['Period'])
            writer.writerow(['Start Date:', data['period'].get('start_date', 'N/A')])
            writer.writerow(['End Date:', data['period'].get('end_date', 'N/A')])
            writer.writerow([])
        
        # Delivery Metrics
        if 'delivery_metrics' in data:
            writer.writerow(['Delivery Metrics'])
            writer.writerow(['Metric', 'Value'])
            for key, value in data['delivery_metrics'].items():
                writer.writerow([key.replace('_', ' ').title(), value])
            writer.writerow([])
        
        # Engagement Metrics
        if 'engagement_metrics' in data:
            writer.writerow(['Engagement Metrics'])
            for metric_type, metrics in data['engagement_metrics'].items():
                writer.writerow([metric_type.replace('_', ' ').title()])
                writer.writerow(['Metric', 'Value'])
                for key, value in metrics.items():
                    writer.writerow([key.replace('_', ' ').title(), value])
                writer.writerow([])
        
        # Channel Performance
        if 'channel_performance' in data:
            writer.writerow(['Channel Performance'])
            writer.writerow(['Channel', 'Total Sent', 'Delivered', 'Opened', 'Clicked', 'Failed', 
                           'Delivery Rate %', 'Open Rate %', 'CTR %', 'Failure Rate %'])
            for channel, metrics in data['channel_performance'].items():
                writer.writerow([
                    channel,
                    metrics.get('total_sent', 0),
                    metrics.get('delivered_count', 0),
                    metrics.get('opened_count', 0),
                    metrics.get('clicked_count', 0),
                    metrics.get('failed_count', 0),
                    metrics.get('delivery_rate', 0),
                    metrics.get('open_rate', 0),
                    metrics.get('click_through_rate', 0),
                    metrics.get('failure_rate', 0)
                ])
            writer.writerow([])
        
        # Message Type Performance
        if 'message_type_performance' in data:
            writer.writerow(['Message Type Performance'])
            writer.writerow(['Message Type', 'Total Sent', 'Delivered', 'Opened', 'Clicked',
                           'Delivery Rate %', 'Open Rate %', 'CTR %'])
            for msg_type, metrics in data['message_type_performance'].items():
                writer.writerow([
                    msg_type,
                    metrics.get('total_sent', 0),
                    metrics.get('delivered_count', 0),
                    metrics.get('opened_count', 0),
                    metrics.get('clicked_count', 0),
                    metrics.get('delivery_rate', 0),
                    metrics.get('open_rate', 0),
                    metrics.get('click_through_rate', 0)
                ])
            writer.writerow([])
        
        # Engagement Funnel
        if 'engagement_funnel' in data:
            writer.writerow(['Engagement Funnel'])
            funnel = data['engagement_funnel']
            if 'funnel_stages' in funnel:
                writer.writerow(['Stage', 'Count'])
                for stage, count in funnel['funnel_stages'].items():
                    writer.writerow([stage.title(), count])
            writer.writerow([])
            if 'conversion_rates' in funnel:
                writer.writerow(['Conversion Rates'])
                writer.writerow(['Conversion', 'Rate %'])
                for conversion, rate in funnel['conversion_rates'].items():
                    writer.writerow([conversion.replace('_', ' ').title(), rate])
            writer.writerow([])
    
    def _export_channel_csv(self, data: Dict[str, Any], output: io.StringIO):
        """Export channel performance to CSV"""
        writer = csv.writer(output)
        
        writer.writerow(['Channel Performance Report'])
        writer.writerow(['Generated:', datetime.utcnow().isoformat()])
        writer.writerow([])
        
        writer.writerow(['Channel', 'Total Sent', 'Delivered', 'Opened', 'Clicked', 'Failed',
                        'Delivery Rate %', 'Open Rate %', 'CTR %', 'Failure Rate %',
                        'Avg Delivery Time (s)', 'Avg Time to Open (s)'])
        
        for channel, metrics in data.items():
            writer.writerow([
                channel,
                metrics.get('total_sent', 0),
                metrics.get('delivered_count', 0),
                metrics.get('opened_count', 0),
                metrics.get('clicked_count', 0),
                metrics.get('failed_count', 0),
                metrics.get('delivery_rate', 0),
                metrics.get('open_rate', 0),
                metrics.get('click_through_rate', 0),
                metrics.get('failure_rate', 0),
                metrics.get('avg_delivery_time_seconds', 0),
                metrics.get('avg_time_to_open_seconds', 0)
            ])
    
    def _export_message_type_csv(self, data: Dict[str, Any], output: io.StringIO):
        """Export message type performance to CSV"""
        writer = csv.writer(output)
        
        writer.writerow(['Message Type Performance Report'])
        writer.writerow(['Generated:', datetime.utcnow().isoformat()])
        writer.writerow([])
        
        writer.writerow(['Message Type', 'Total Sent', 'Delivered', 'Opened', 'Clicked',
                        'Delivery Rate %', 'Open Rate %', 'CTR %',
                        'Avg Delivery Time (s)', 'Avg Time to Open (s)', 'Avg Time to Click (s)'])
        
        for msg_type, metrics in data.items():
            writer.writerow([
                msg_type,
                metrics.get('total_sent', 0),
                metrics.get('delivered_count', 0),
                metrics.get('opened_count', 0),
                metrics.get('clicked_count', 0),
                metrics.get('delivery_rate', 0),
                metrics.get('open_rate', 0),
                metrics.get('click_through_rate', 0),
                metrics.get('avg_delivery_time_seconds', 0),
                metrics.get('avg_time_to_open_seconds', 0),
                metrics.get('avg_time_to_click_seconds', 0)
            ])
    
    def _export_timeline_csv(self, data: List[Dict[str, Any]], output: io.StringIO):
        """Export timeline data to CSV"""
        writer = csv.writer(output)
        
        writer.writerow(['Timeline Report'])
        writer.writerow(['Generated:', datetime.utcnow().isoformat()])
        writer.writerow([])
        
        writer.writerow(['Timestamp', 'Total Sent', 'Delivered', 'Opened', 'Clicked', 'Failed', 'Delivery Rate %'])
        
        for data_point in data:
            writer.writerow([
                data_point.get('timestamp', ''),
                data_point.get('total_sent', 0),
                data_point.get('delivered_count', 0),
                data_point.get('opened_count', 0),
                data_point.get('clicked_count', 0),
                data_point.get('failed_count', 0),
                data_point.get('delivery_rate', 0)
            ])
    
    def export_to_pdf(
        self,
        data: Dict[str, Any],
        title: str = "CRM Communication Analytics Report"
    ) -> bytes:
        """
        Export analytics data to PDF format.
        
        Args:
            data: Analytics data dictionary
            title: Report title
            
        Returns:
            PDF content as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
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
        elements.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Period
        if 'period' in data:
            period_text = f"<b>Period:</b> {data['period'].get('start_date', 'N/A')} to {data['period'].get('end_date', 'N/A')}"
            elements.append(Paragraph(period_text, styles['Normal']))
            elements.append(Spacer(1, 0.2*inch))
        
        # Delivery Metrics
        if 'delivery_metrics' in data:
            elements.append(Paragraph("Delivery Metrics", heading_style))
            delivery_data = [['Metric', 'Value']]
            for key, value in data['delivery_metrics'].items():
                delivery_data.append([key.replace('_', ' ').title(), str(value)])
            
            table = Table(delivery_data, colWidths=[3*inch, 2*inch])
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
        if 'channel_performance' in data:
            elements.append(Paragraph("Channel Performance", heading_style))
            channel_data = [['Channel', 'Sent', 'Delivered', 'Delivery %', 'Open %', 'CTR %']]
            for channel, metrics in data['channel_performance'].items():
                channel_data.append([
                    channel,
                    str(metrics.get('total_sent', 0)),
                    str(metrics.get('delivered_count', 0)),
                    f"{metrics.get('delivery_rate', 0)}%",
                    f"{metrics.get('open_rate', 0)}%",
                    f"{metrics.get('click_through_rate', 0)}%"
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
        if 'message_type_performance' in data:
            elements.append(Paragraph("Message Type Performance", heading_style))
            msg_data = [['Message Type', 'Sent', 'Delivered', 'Delivery %', 'Open %']]
            for msg_type, metrics in data['message_type_performance'].items():
                msg_data.append([
                    msg_type.replace('_', ' ').title(),
                    str(metrics.get('total_sent', 0)),
                    str(metrics.get('delivered_count', 0)),
                    f"{metrics.get('delivery_rate', 0)}%",
                    f"{metrics.get('open_rate', 0)}%"
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
        
        # Engagement Funnel
        if 'engagement_funnel' in data:
            elements.append(Paragraph("Engagement Funnel", heading_style))
            funnel = data['engagement_funnel']
            
            if 'funnel_stages' in funnel:
                funnel_data = [['Stage', 'Count', 'Conversion %']]
                stages = funnel['funnel_stages']
                conversions = funnel.get('conversion_rates', {})
                
                funnel_data.append(['Sent', str(stages.get('sent', 0)), '100%'])
                funnel_data.append(['Delivered', str(stages.get('delivered', 0)), 
                                  f"{conversions.get('sent_to_delivered', 0)}%"])
                funnel_data.append(['Opened', str(stages.get('opened', 0)), 
                                  f"{conversions.get('delivered_to_opened', 0)}%"])
                funnel_data.append(['Clicked', str(stages.get('clicked', 0)), 
                                  f"{conversions.get('opened_to_clicked', 0)}%"])
                
                table = Table(funnel_data, colWidths=[2*inch, 2*inch, 2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
        
        # Build PDF
        doc.build(elements)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        logger.info("Exported analytics data to PDF")
        return pdf_content


# Singleton instance
_exporter_instance = None


def get_exporter() -> CRMExporter:
    """Get singleton exporter instance"""
    global _exporter_instance
    if _exporter_instance is None:
        _exporter_instance = CRMExporter()
    return _exporter_instance