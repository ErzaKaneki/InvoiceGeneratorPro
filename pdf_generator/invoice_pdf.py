# File: invoice_pdf.py
# Location: InvoiceGeneratorPro/pdf_generator/invoice_pdf.py

import os
import re
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

from database.models import Invoice
from utils.calculations import CurrencyFormatter, DateCalculator
from config import (
    PDF_MARGIN, PDF_HEADER_FONT_SIZE, PDF_TITLE_FONT_SIZE,
    DEFAULT_LOGO_PATH, EXPORT_DIR, APP_NAME
)

class InvoicePDFGenerator:
    """Generates professional PDF invoices"""
    
    def __init__(self):
        self.page_size = letter
        self.margin = PDF_MARGIN
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Set up custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Title'],
            fontSize=PDF_TITLE_FONT_SIZE,
            spaceAfter=20,
            textColor=colors.HexColor('#2E86AB'),
            alignment=TA_CENTER
        ))
        
        # Header style
        self.styles.add(ParagraphStyle(
            name='InvoiceHeader',
            parent=self.styles['Heading1'],
            fontSize=PDF_HEADER_FONT_SIZE,
            spaceAfter=12,
            textColor=colors.HexColor('#2C3E50'),
            alignment=TA_LEFT
        ))
        
        # Company info style
        self.styles.add(ParagraphStyle(
            name='CompanyInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            textColor=colors.HexColor('#2C3E50'),
            alignment=TA_RIGHT
        ))
        
        # Client info style
        self.styles.add(ParagraphStyle(
            name='ClientInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            textColor=colors.HexColor('#2C3E50'),
            alignment=TA_LEFT
        ))
        
        # Invoice details style
        self.styles.add(ParagraphStyle(
            name='InvoiceDetails',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=3,
            textColor=colors.HexColor('#34495E'),
            alignment=TA_LEFT
        ))
        
        # Total style
        self.styles.add(ParagraphStyle(
            name='TotalAmount',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#2E86AB'),
            alignment=TA_RIGHT,
            fontName='Helvetica-Bold'
        ))
    
    def generate_invoice_pdf(self, invoice: Invoice, output_path: str | None = None) -> str:
        """Generate PDF for an invoice"""
        if not output_path:
            filename = f"Invoice_{invoice.formatted_invoice_number}_{datetime.now().strftime('%Y%m%d')}.pdf"
            output_path = os.path.join(EXPORT_DIR, filename)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.page_size,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        # Build PDF content
        story = []
        
        # Add header section
        story.extend(self._build_header(invoice))
        story.append(Spacer(1, 20))
        
        # Add company and client info
        story.extend(self._build_info_section(invoice))
        story.append(Spacer(1, 20))
        
        # Add invoice details
        story.extend(self._build_invoice_details(invoice))
        story.append(Spacer(1, 15))
        
        # Add items table
        story.extend(self._build_items_table(invoice))
        story.append(Spacer(1, 15))
        
        # Add totals section
        story.extend(self._build_totals_section(invoice))
        story.append(Spacer(1, 20))
        
        # Add notes if present
        if invoice.notes:
            story.extend(self._build_notes_section(invoice))
            story.append(Spacer(1, 15))
        
        # Add footer
        story.extend(self._build_footer(invoice))
        
        # Build PDF
        doc.build(story)
        
        return output_path
    
    def _build_header(self, invoice: Invoice) -> list:
        """Build PDF header section"""
        elements = []
        
        # Left side - Logo (if exists) or Company Name
        left_content = []
        if os.path.exists(DEFAULT_LOGO_PATH):
            try:
                logo = Image(DEFAULT_LOGO_PATH, width=120, height=60)
                left_content.append(logo)
            except (OSError, IOError, ValueError):
                # If logo fails to load, use company name
                left_content.append(Paragraph(
                    invoice.company_name or APP_NAME,
                    self.styles['InvoiceHeader']
                ))
        else:
            left_content.append(Paragraph(
                invoice.company_name or APP_NAME,
                self.styles['InvoiceHeader']
            ))
        
        # Right side - Invoice title and number
        right_content = [
            Paragraph("INVOICE", self.styles['InvoiceTitle']),
            Paragraph(f"#{invoice.formatted_invoice_number}", self.styles['InvoiceHeader'])
        ]
        
        # Create table
        header_table = Table([
            [left_content, right_content]
        ], colWidths=[3*inch, 3*inch])
        
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        
        elements.append(header_table)
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2E86AB')))
        
        return elements
    
    def _build_info_section(self, invoice: Invoice) -> list:
        """Build company and client information section"""
        elements = []
        
        # Company info (left) and Client info (right)
        company_info = self._format_company_info(invoice)
        client_info = self._format_client_info(invoice)
        
        info_table = Table([
            [company_info, client_info]
        ], colWidths=[3*inch, 3*inch])
        
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
        ]))
        
        elements.append(info_table)
        
        return elements
    
    def _format_company_info(self, invoice: Invoice) -> list:
        """Format company information"""
        info = []
        
        info.append(Paragraph("<b>From:</b>", self.styles['InvoiceDetails']))
        
        if invoice.company_name:
            info.append(Paragraph(f"<b>{invoice.company_name}</b>", self.styles['ClientInfo']))
        
        if invoice.company_address:
            # Split address into lines
            address_lines = invoice.company_address.split('\n')
            for line in address_lines:
                if line.strip():
                    info.append(Paragraph(line.strip(), self.styles['ClientInfo']))
        
        if invoice.company_phone:
            info.append(Paragraph(f"Phone: {invoice.company_phone}", self.styles['ClientInfo']))
        
        if invoice.company_email:
            info.append(Paragraph(f"Email: {invoice.company_email}", self.styles['ClientInfo']))
        
        if invoice.company_website:
            info.append(Paragraph(f"Web: {invoice.company_website}", self.styles['ClientInfo']))
        
        return info
    
    def _format_client_info(self, invoice: Invoice) -> list:
        """Format client information"""
        info = []
        
        info.append(Paragraph("<b>Bill To:</b>", self.styles['InvoiceDetails']))
        
        if invoice.client and invoice.client.name:
            info.append(Paragraph(f"<b>{invoice.client.name}</b>", self.styles['ClientInfo']))
        
        if invoice.client and invoice.client.full_address:
            # Split address into lines
            address_lines = invoice.client.full_address.split('\n')
            for line in address_lines:
                if line.strip():
                    info.append(Paragraph(line.strip(), self.styles['ClientInfo']))
        
        if invoice.client and invoice.client.phone:
            info.append(Paragraph(f"Phone: {invoice.client.phone}", self.styles['ClientInfo']))
        
        if invoice.client and invoice.client.email:
            info.append(Paragraph(f"Email: {invoice.client.email}", self.styles['ClientInfo']))
        
        return info
    
    def _build_invoice_details(self, invoice: Invoice) -> list:
        """Build invoice details section"""
        elements = []
        
        # Invoice details table
        details_data = [
            ["Invoice Date:", DateCalculator.format_date_for_display(invoice.invoice_date)],
            ["Due Date:", DateCalculator.format_date_for_display(invoice.due_date)],
            ["Payment Terms:", invoice.payment_terms],
            ["Status:", invoice.status]
        ]
        
        details_table = Table(details_data, colWidths=[1.5*inch, 2*inch])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (0, -1), 10),
        ]))
        
        elements.append(details_table)
        
        return elements
    
    def _build_items_table(self, invoice: Invoice) -> list:
        """Build invoice items table"""
        elements = []
        
        # Table headers
        headers = ["Description", "Qty", "Rate", "Amount"]
        
        # Table data
        table_data = [headers]
        
        for item in invoice.items:
            row = [
                item.description,
                f"{item.quantity:g}",  # Remove trailing zeros
                CurrencyFormatter.format_currency(item.rate, invoice.currency),
                CurrencyFormatter.format_currency(item.total, invoice.currency)
            ]
            table_data.append(row)
        
        # Create table
        items_table = Table(table_data, colWidths=[3.5*inch, 0.7*inch, 1*inch, 1*inch])
        
        # Style the table
        items_table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),    # Description left
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Quantity center
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # Rate and Amount right
            
            # Grid lines
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
            
            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(items_table)
        
        return elements
    
    def _build_totals_section(self, invoice: Invoice) -> list:
        """Build invoice totals section"""
        elements = []
        
        # Totals data
        totals_data = []
        
        # Subtotal
        totals_data.append([
            "Subtotal:",
            CurrencyFormatter.format_currency(invoice.subtotal, invoice.currency)
        ])
        
        # Tax (if applicable)
        if invoice.tax_rate > 0:
            tax_label = f"Tax ({CurrencyFormatter.format_percentage(invoice.tax_rate)}):"
            totals_data.append([
                tax_label,
                CurrencyFormatter.format_currency(invoice.tax_amount, invoice.currency)
            ])
        
        # Total
        totals_data.append([
            "TOTAL:",
            CurrencyFormatter.format_currency(invoice.total, invoice.currency)
        ])
        
        # Create totals table
        totals_table = Table(totals_data, colWidths=[1.5*inch, 1.2*inch])
        totals_table.setStyle(TableStyle([
            # General styling
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Subtotal and tax rows
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('TEXTCOLOR', (0, 0), (-1, -2), colors.HexColor('#2C3E50')),
            
            # Total row (last row)
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#2E86AB')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ECF0F1')),
            
            # Borders
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#2E86AB')),
            ('LINEBELOW', (0, -1), (-1, -1), 2, colors.HexColor('#2E86AB')),
            
            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        # Right-align the totals table
        totals_wrapper = Table([[totals_table]], colWidths=[6.5*inch])
        totals_wrapper.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
        ]))
        
        elements.append(totals_wrapper)
        
        return elements
    
    def _build_notes_section(self, invoice: Invoice) -> list:
        """Build notes section"""
        elements = []
        
        elements.append(Paragraph("<b>Notes:</b>", self.styles['InvoiceHeader']))
        elements.append(Paragraph(invoice.notes, self.styles['Normal']))
        
        return elements
    
    def _build_footer(self, invoice: Invoice) -> list:
        """Build footer section"""
        elements = []
        
        # Payment instructions or footer text
        footer_text = "Thank you for your business!"
        if invoice.status == "Sent":
            if invoice.payment_terms == "Due on Receipt":
                footer_text = "Payment is due upon receipt of this invoice."
            else:
                due_date = DateCalculator.format_date_for_display(invoice.due_date)
                footer_text = f"Payment is due by {due_date}. Thank you for your business!"
        
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#BDC3C7')))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(footer_text, self.styles['Normal']))
        
        # Generated timestamp
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            f"<i>Generated on {timestamp} by {APP_NAME}</i>",
            ParagraphStyle(
                name='Timestamp',
                parent=self.styles['Normal'],
                fontSize=8,
                textColor=colors.HexColor('#7F8C8D'),
                alignment=TA_CENTER
            )
        ))
        
        return elements

@staticmethod
def generate_invoice_pdf(invoice: Invoice, output_path: str | None = None) -> str:
    """Convenience function to generate invoice PDF"""
    generator = InvoicePDFGenerator()
    return generator.generate_invoice_pdf(invoice, output_path)

def generate_invoice_filename(invoice: Invoice) -> str:
    """Generate a standard filename for an invoice PDF"""
    safe_client_name = ""
    if invoice.client and invoice.client.name:
        # Clean client name for filename
        safe_client_name = re.sub(r'[^\w\s-]', '', invoice.client.name)
        safe_client_name = re.sub(r'[-\s]+', '_', safe_client_name)
        safe_client_name = f"_{safe_client_name}"
    
    date_str = datetime.now().strftime('%Y%m%d')
    return f"Invoice_{invoice.formatted_invoice_number}{safe_client_name}_{date_str}.pdf"