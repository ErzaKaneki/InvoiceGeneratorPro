# File: templates.py
# Location: InvoiceGeneratorPro/pdf_generator/templates.py

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from database.models import Invoice
from utils.calculations import CurrencyFormatter, DateCalculator
from config import PDF_MARGIN

class InvoiceTemplate:
    """Base template class for invoice PDFs"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.page_size = letter
        self.margin = PDF_MARGIN
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Setup base styles - can be overridden by subclasses"""
        pass
    
    def generate_pdf(self, invoice: Invoice, output_path: str) -> str:
        """Generate PDF using this template"""
        raise NotImplementedError("Subclasses must implement generate_pdf")

class ModernTemplate(InvoiceTemplate):
    """Modern, clean template with blue accent colors"""
    
    def __init__(self):
        # Set colors first, before calling super().__init__
        self.primary_color = colors.HexColor('#2E86AB')
        self.secondary_color = colors.HexColor('#2C3E50')
        self.accent_color = colors.HexColor('#ECF0F1')
        
        super().__init__(
            name="Modern Professional",
            description="Clean, modern design with blue accents and minimal styling"
        )
    
    def _setup_styles(self):
        """Setup modern template styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='ModernTitle',
            parent=self.styles['Title'],
            fontSize=28,
            spaceAfter=20,
            textColor=self.primary_color,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        # Header style
        self.styles.add(ParagraphStyle(
            name='ModernHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=12,
            textColor=self.secondary_color,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        # Company info style
        self.styles.add(ParagraphStyle(
            name='ModernCompany',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            textColor=self.secondary_color,
            alignment=TA_LEFT
        ))
        
        # Client info style
        self.styles.add(ParagraphStyle(
            name='ModernClient',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            textColor=self.secondary_color,
            alignment=TA_LEFT
        ))
    
    def generate_pdf(self, invoice: Invoice, output_path: str) -> str:
        """Generate modern template PDF"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.page_size,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        story = []
        
        # Modern header with large INVOICE text
        story.append(Paragraph("INVOICE", self.styles['ModernTitle']))
        story.append(Spacer(1, 10))
        
        # Invoice number and dates in a clean layout
        header_data = [
            [f"Invoice #: {invoice.formatted_invoice_number}", ""],
            [f"Date: {DateCalculator.format_date_for_display(invoice.invoice_date)}", ""],
            [f"Due: {DateCalculator.format_date_for_display(invoice.due_date)}", ""]
        ]
        
        header_table = Table(header_data, colWidths=[3*inch, 3*inch])
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.secondary_color),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 30))
        
        # Company and client info side by side
        story.extend(self._build_modern_info_section(invoice))
        story.append(Spacer(1, 30))
        
        # Items table with modern styling
        story.extend(self._build_modern_items_table(invoice))
        story.append(Spacer(1, 20))
        
        # Modern totals section
        story.extend(self._build_modern_totals(invoice))
        
        # Notes and footer
        if invoice.notes:
            story.append(Spacer(1, 20))
            story.append(Paragraph("Notes", self.styles['ModernHeader']))
            story.append(Paragraph(invoice.notes, self.styles['Normal']))
        
        doc.build(story)
        return output_path
    
    def _build_modern_info_section(self, invoice: Invoice) -> list:
        """Build modern info section"""
        elements = []
        
        # From section
        from_info = [Paragraph("FROM", self.styles['ModernHeader'])]
        if invoice.company_name:
            from_info.append(Paragraph(f"<b>{invoice.company_name}</b>", self.styles['ModernCompany']))
        if invoice.company_address:
            for line in invoice.company_address.split('\n'):
                if line.strip():
                    from_info.append(Paragraph(line.strip(), self.styles['ModernCompany']))
        if invoice.company_email:
            from_info.append(Paragraph(invoice.company_email, self.styles['ModernCompany']))
        if invoice.company_phone:
            from_info.append(Paragraph(invoice.company_phone, self.styles['ModernCompany']))
        
        # To section
        to_info = [Paragraph("BILL TO", self.styles['ModernHeader'])]
        if invoice.client:
            if invoice.client.name:
                to_info.append(Paragraph(f"<b>{invoice.client.name}</b>", self.styles['ModernClient']))
            if invoice.client.full_address:
                for line in invoice.client.full_address.split('\n'):
                    if line.strip():
                        to_info.append(Paragraph(line.strip(), self.styles['ModernClient']))
            if invoice.client.email:
                to_info.append(Paragraph(invoice.client.email, self.styles['ModernClient']))
            if invoice.client.phone:
                to_info.append(Paragraph(invoice.client.phone, self.styles['ModernClient']))
        
        # Create table
        info_table = Table([
            [from_info, to_info]
        ], colWidths=[3*inch, 3*inch])
        
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(info_table)
        return elements
    
    def _build_modern_items_table(self, invoice: Invoice) -> list:
        """Build modern items table"""
        elements = []
        
        # Headers
        headers = ["Description", "Qty", "Rate", "Total"]
        table_data = [headers]
        
        # Items
        for item in invoice.items:
            table_data.append([
                item.description,
                f"{item.quantity:g}",
                CurrencyFormatter.format_currency(item.rate, invoice.currency),
                CurrencyFormatter.format_currency(item.total, invoice.currency)
            ])
        
        # Create table
        items_table = Table(table_data, colWidths=[3.5*inch, 0.7*inch, 1*inch, 1*inch])
        
        # Modern styling
        items_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            
            # Clean lines
            ('LINEBELOW', (0, 0), (-1, 0), 2, self.primary_color),
            ('LINEBELOW', (0, -1), (-1, -1), 1, colors.grey),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(items_table)
        return elements
    
    def _build_modern_totals(self, invoice: Invoice) -> list:
        """Build modern totals section"""
        elements = []
        
        totals_data = []
        
        # Subtotal
        totals_data.append(["Subtotal", CurrencyFormatter.format_currency(invoice.subtotal, invoice.currency)])
        
        # Tax
        if invoice.tax_rate > 0:
            totals_data.append([
                f"Tax ({CurrencyFormatter.format_percentage(invoice.tax_rate)})",
                CurrencyFormatter.format_currency(invoice.tax_amount, invoice.currency)
            ])
        
        # Total
        totals_data.append(["TOTAL", CurrencyFormatter.format_currency(invoice.total, invoice.currency)])
        
        totals_table = Table(totals_data, colWidths=[1.5*inch, 1.2*inch])
        totals_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -2), 11),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, -1), (-1, -1), self.primary_color),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('LINEABOVE', (0, -1), (-1, -1), 2, self.primary_color),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        # Right align
        wrapper = Table([[totals_table]], colWidths=[6.5*inch])
        wrapper.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'RIGHT')]))
        
        elements.append(wrapper)
        return elements

class ClassicTemplate(InvoiceTemplate):
    """Traditional, formal template with elegant styling"""
    
    def __init__(self):
        # Set colors first, before calling super().__init__
        self.primary_color = colors.HexColor('#1C2833')
        self.secondary_color = colors.HexColor('#34495E')
        self.accent_color = colors.HexColor('#D5DBDB')
        
        super().__init__(
            name="Classic Elegant",
            description="Traditional business design with formal styling and elegant typography"
        )
    
    def _setup_styles(self):
        """Setup classic template styles"""
        self.styles.add(ParagraphStyle(
            name='ClassicTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=self.primary_color,
            alignment=TA_CENTER,
            fontName='Times-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='ClassicHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=10,
            textColor=self.primary_color,
            fontName='Times-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='ClassicBody',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.secondary_color,
            fontName='Times-Roman'
        ))
    
    def generate_pdf(self, invoice: Invoice, output_path: str) -> str:
        """Generate classic template PDF"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.page_size,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        story = []
        
        # Elegant header with centered title
        story.append(Paragraph("INVOICE", self.styles['ClassicTitle']))
        story.append(HRFlowable(width="100%", thickness=2, color=self.primary_color))
        story.append(Spacer(1, 20))
        
        # Invoice details in formal layout
        details_data = [
            ["Invoice Number:", invoice.formatted_invoice_number, "Invoice Date:", DateCalculator.format_date_for_display(invoice.invoice_date)],
            ["Payment Terms:", invoice.payment_terms, "Due Date:", DateCalculator.format_date_for_display(invoice.due_date)]
        ]
        
        details_table = Table(details_data, colWidths=[1.2*inch, 1.5*inch, 1.2*inch, 1.5*inch])
        details_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Times-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Times-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (3, 0), (3, -1), 'LEFT'),
        ]))
        
        story.append(details_table)
        story.append(Spacer(1, 30))
        
        # Company and client info with formal styling
        story.extend(self._build_classic_info_section(invoice))
        story.append(Spacer(1, 30))
        
        # Items table with classic styling
        story.extend(self._build_classic_items_table(invoice))
        story.append(Spacer(1, 20))
        
        # Classic totals section
        story.extend(self._build_classic_totals(invoice))
        
        # Footer with formal closing
        story.append(Spacer(1, 40))
        story.append(HRFlowable(width="100%", thickness=1, color=self.accent_color))
        story.append(Spacer(1, 10))
        story.append(Paragraph("Thank you for your business.", self.styles['ClassicBody']))
        
        doc.build(story)
        return output_path
    
    def _build_classic_info_section(self, invoice: Invoice) -> list:
        """Build classic info section"""
        elements = []
        
        # Formal company section
        elements.append(Paragraph("From:", self.styles['ClassicHeader']))
        if invoice.company_name:
            elements.append(Paragraph(invoice.company_name, self.styles['ClassicBody']))
        if invoice.company_address:
            elements.append(Paragraph(invoice.company_address.replace('\n', '<br/>'), self.styles['ClassicBody']))
        
        elements.append(Spacer(1, 15))
        
        # Formal client section
        elements.append(Paragraph("Bill To:", self.styles['ClassicHeader']))
        if invoice.client:
            if invoice.client.name:
                elements.append(Paragraph(invoice.client.name, self.styles['ClassicBody']))
            if invoice.client.full_address:
                elements.append(Paragraph(invoice.client.full_address.replace('\n', '<br/>'), self.styles['ClassicBody']))
        
        return elements
    
    def _build_classic_items_table(self, invoice: Invoice) -> list:
        """Build classic items table"""
        elements = []
        
        headers = ["Description", "Quantity", "Rate", "Amount"]
        table_data = [headers]
        
        for item in invoice.items:
            table_data.append([
                item.description,
                f"{item.quantity:g}",
                CurrencyFormatter.format_currency(item.rate, invoice.currency),
                CurrencyFormatter.format_currency(item.total, invoice.currency)
            ])
        
        items_table = Table(table_data, colWidths=[3.5*inch, 0.7*inch, 1*inch, 1*inch])
        
        items_table.setStyle(TableStyle([
            # Header with elegant styling
            ('BACKGROUND', (0, 0), (-1, 0), self.accent_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.primary_color),
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            
            # Elegant borders
            ('LINEBELOW', (0, 0), (-1, 0), 2, self.primary_color),
            ('LINEBELOW', (0, -1), (-1, -1), 1, self.primary_color),
            ('GRID', (0, 0), (-1, -1), 0.5, self.accent_color),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(items_table)
        return elements
    
    def _build_classic_totals(self, invoice: Invoice) -> list:
        """Build classic totals section"""
        elements = []
        
        totals_data = [
            ["Subtotal:", CurrencyFormatter.format_currency(invoice.subtotal, invoice.currency)]
        ]
        
        if invoice.tax_rate > 0:
            totals_data.append([
                f"Tax ({CurrencyFormatter.format_percentage(invoice.tax_rate)}):",
                CurrencyFormatter.format_currency(invoice.tax_amount, invoice.currency)
            ])
        
        totals_data.append([
            "Total Amount Due:",
            CurrencyFormatter.format_currency(invoice.total, invoice.currency)
        ])
        
        totals_table = Table(totals_data, colWidths=[2*inch, 1.2*inch])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -2), 'Times-Roman'),
            ('FONTNAME', (0, -1), (-1, -1), 'Times-Bold'),
            ('FONTSIZE', (0, 0), (-1, -2), 10),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('TEXTCOLOR', (0, -1), (-1, -1), self.primary_color),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('LINEABOVE', (0, -1), (-1, -1), 2, self.primary_color),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        # Right align
        wrapper = Table([[totals_table]], colWidths=[6.5*inch])
        wrapper.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'RIGHT')]))
        
        elements.append(wrapper)
        return elements

class MinimalTemplate(InvoiceTemplate):
    """Minimal, clean template with lots of white space"""
    
    def __init__(self):
        # Set colors first, before calling super().__init__
        self.primary_color = colors.HexColor('#000000')
        self.secondary_color = colors.HexColor('#666666')
        self.accent_color = colors.HexColor('#F5F5F5')
        
        super().__init__(
            name="Minimal Clean",
            description="Ultra-clean design with minimal colors and maximum white space"
        )
    
    def generate_pdf(self, invoice: Invoice, output_path: str) -> str:
        """Generate minimal template PDF"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.page_size,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        story = []
        
        # Simple invoice header
        story.append(Spacer(1, 20))
        story.append(Paragraph("Invoice", ParagraphStyle(
            name='MinimalTitle',
            fontSize=32,
            textColor=self.primary_color,
            fontName='Helvetica-Light',
            alignment=TA_LEFT
        )))
        story.append(Spacer(1, 40))
        
        # Basic info in clean layout
        info_data = [
            [f"#{invoice.formatted_invoice_number}", ""],
            [DateCalculator.format_date_for_display(invoice.invoice_date), ""],
            ["", ""]
        ]
        
        if invoice.client and invoice.client.name:
            info_data.append([f"For: {invoice.client.name}", ""])
        
        info_table = Table(info_data, colWidths=[3*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.secondary_color),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 40))
        
        # Ultra-clean items list
        for item in invoice.items:
            item_data = [
                [item.description, CurrencyFormatter.format_currency(item.total, invoice.currency)]
            ]
            
            item_table = Table(item_data, colWidths=[4.5*inch, 1.5*inch])
            item_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, 0), 'Helvetica'),
                ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            story.append(item_table)
        
        story.append(Spacer(1, 30))
        
        # Simple total
        total_data = [
            ["Total", CurrencyFormatter.format_currency(invoice.total, invoice.currency)]
        ]
        
        total_table = Table(total_data, colWidths=[4.5*inch, 1.5*inch])
        total_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 16),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('LINEABOVE', (0, 0), (-1, -1), 1, self.primary_color),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        story.append(total_table)
        
        doc.build(story)
        return output_path

# Template registry
AVAILABLE_TEMPLATES = {
    'modern': ModernTemplate(),
    'classic': ClassicTemplate(),
    'minimal': MinimalTemplate()
}

def get_template(template_name: str) -> InvoiceTemplate:
    """Get a template by name"""
    return AVAILABLE_TEMPLATES.get(template_name, ModernTemplate())

def get_available_templates() -> dict:
    """Get all available templates"""
    return {name: template.description for name, template in AVAILABLE_TEMPLATES.items()}

def generate_invoice_with_template(invoice: Invoice, template_name: str, output_path: str) -> str:
    """Generate invoice PDF with specified template"""
    template = get_template(template_name)
    return template.generate_pdf(invoice, output_path)