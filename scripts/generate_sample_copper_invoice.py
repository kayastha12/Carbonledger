import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_copper_invoice(output_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    doc = SimpleDocTemplate(output_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1e293b")
    )

    story.append(Paragraph("<b>TAX INVOICE — ABC METALS LTD</b>", title_style))
    story.append(Paragraph("GSTIN: 27AABCA1234F1Z5 | Mumbai, Maharashtra, India", styles['Normal']))
    story.append(Spacer(1, 12))

    # Invoice Header Grid
    header_data = [
        ["Invoice No:", "INV-2026-901", "Invoice Date:", "01-Mar-2026"],
        ["Supplier:", "ABC Metals Ltd", "Place of Supply:", "Maharashtra (India)"],
        ["Customer:", "EcoManufacturing Global", "PO Number:", "PO-ABC-4401"]
    ]
    t_header = Table(header_data, colWidths=[90, 180, 90, 180])
    t_header.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#334155')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 18))

    # Line Items Table
    table_data = [
        ["Item Code", "Material Description", "Quantity", "Unit", "Unit Cost", "Total Amount (INR)"],
        ["COP-001", "Copper Wire", "750", "kg", "160.00", "120,000.00"],
        ["BRS-002", "Brass Rod", "300", "kg", "216.67", "65,000.00"],
        ["FST-003", "Stainless Steel Fasteners", "1500", "pcs", "30.00", "45,000.00"],
    ]

    t_items = Table(table_data, colWidths=[65, 180, 65, 55, 75, 100])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t_items)
    story.append(Spacer(1, 20))

    story.append(Paragraph("<b>Total Taxable Value: INR 230,000.00</b>", styles['Normal']))
    story.append(Paragraph("Declaration: The carbon accounting parameters and weights above are certified accurate.", styles['Italic']))

    doc.build(story)
    print(f"Generated invoice at: {output_path}")

if __name__ == "__main__":
    generate_copper_invoice("output/temp/sample_copper_invoice.pdf")
