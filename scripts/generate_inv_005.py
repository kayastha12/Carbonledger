import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_inv_005(pdf_path: str):
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=14,
        leading=16,
        textColor=colors.black
    )
    sub_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#444444")
    )
    header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=7,
        leading=8,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor("#1e293b")
    )
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor("#0f172a")
    )
    
    story = []
    
    # 1. Header
    story.append(Paragraph("<b>TAX INVOICE</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>CarbonLedger Sample Dataset</b>", title_style))
    story.append(Paragraph("Phase 1 - Invoice Upload<br/>TechManufacturing India Ltd. | FY 2025-2026", sub_style))
    story.append(Spacer(1, 8))
    
    # Header Info Table
    header_data = [
        [
            Paragraph("<b>SUPPLIER (SOLD BY)</b><br/>Bharat Multimetal & Polymer Supplies Pvt Ltd<br/>Plot 14, Chakan Industrial Area, Phase II, Pune 410501, Maharashtra, India<br/>GSTIN: 27AAFCB5678K1ZP<br/>Supplier ID: SUP-004 | ESG Rating: A<br/>Certification: ISO 14001 / ISO 9001", cell_style),
            Paragraph("<b>BUYER (SHIP TO)</b><br/>TechManufacturing India Ltd.<br/>Main Manufacturing Plant (FAC-001), MIDC Andheri East, Mumbai 400093, Maharashtra, India<br/>GSTIN: 27AABCT1234M1Z5<br/>Company ID: CL-TCH-001 | FY: 2025-2026", cell_style),
            Paragraph("<b>Invoice No.</b> INV-005<br/><b>Invoice Date</b> 2025-01-28<br/><b>PO Reference</b> PO2025-005 (2025-01-16)<br/><b>Place of Supply</b> Maharashtra (27)<br/><b>Payment Terms</b> Net 30 days<br/><b>Currency</b> INR", cell_style)
        ]
    ]
    t_head = Table(header_data, colWidths=[180, 180, 180])
    t_head.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_head)
    story.append(Spacer(1, 10))
    
    # Material items definition (50 items)
    materials = [
        (1, "MAT-201", "Structural Steel Section (primary metal)", "7216", "Construction", "1,500", "kg", "58.00", "87,000.00", "1,500.0", "Line A"),
        (2, "MAT-202", "Structural Steel Section (closed-loop recycled)", "7216", "Construction", "1,200", "kg", "46.00", "55,200.00", "1,200.0", "Line A"),
        (3, "MAT-203", "Tinplate Steel Sheet for Can Bodies (primary)", "7210", "Metal", "400", "kg", "96.00", "38,400.00", "400.0", "Line A"),
        (4, "MAT-204", "Tinplate Steel Sheet (closed-loop recycled)", "7210", "Metal", "350", "kg", "78.00", "27,300.00", "350.0", "Line A"),
        (5, "MAT-205", "Metal Scrap Feedstock (primary route)", "7204", "Metal", "900", "kg", "32.00", "28,800.00", "900.0", "Line A"),
        (6, "MAT-206", "Metal Scrap Feedstock (closed-loop recycled)", "7204", "Metal", "800", "kg", "28.00", "22,400.00", "800.0", "Line A"),
        (7, "MAT-207", "Mixed Metal Can Stock (primary)", "7310", "Metal", "200", "kg", "190.00", "38,000.00", "200.0", "Line A"),
        (8, "MAT-208", "Mixed Metal Can Stock (closed-loop recycled)", "7310", "Metal", "180", "kg", "150.00", "27,000.00", "180.0", "Line A"),
        (9, "MAT-209", "Aluminium Foil Stock 0.05 mm (primary)", "7607", "Metal", "300", "kg", "320.00", "96,000.00", "300.0", "Line B"),
        (10, "MAT-210", "Aluminium Foil Stock (closed-loop recycled)", "7607", "Metal", "250", "kg", "245.00", "61,250.00", "250.0", "Line B"),
        (11, "MAT-211", "Mixed Plastic Granules, average (primary)", "3902", "Plastic", "400", "kg", "118.00", "47,200.00", "400.0", "Line C"),
        (12, "MAT-212", "Mixed Plastic Granules (closed-loop recycled)", "3902", "Plastic", "350", "kg", "92.00", "32,200.00", "350.0", "Line C"),
        (13, "MAT-213", "Plastic Film Stock, average (primary)", "3920", "Plastic", "200", "kg", "135.00", "27,000.00", "200.0", "Line C"),
        (14, "MAT-214", "Plastic Film Stock (closed-loop recycled)", "3920", "Plastic", "180", "kg", "105.00", "18,900.00", "180.0", "Line C"),
        (15, "MAT-215", "Rigid Plastic Moulding Compound (primary)", "3926", "Plastic", "300", "kg", "142.00", "42,600.00", "300.0", "Line C"),
        (16, "MAT-216", "Rigid Plastic Moulding Compound (recycled)", "3926", "Plastic", "260", "kg", "110.00", "28,600.00", "260.0", "Line C"),
        (17, "MAT-217", "HDPE Granules, injection grade (primary)", "3901", "Plastic", "450", "kg", "112.00", "50,400.00", "450.0", "Line C"),
        (18, "MAT-218", "HDPE Granules (closed-loop recycled)", "3901", "Plastic", "400", "kg", "88.00", "35,200.00", "400.0", "Line C"),
        (19, "MAT-219", "LLDPE Granules, film grade (primary)", "3901", "Plastic", "300", "kg", "116.00", "34,800.00", "300.0", "Line C"),
        (20, "MAT-220", "LLDPE Granules (closed-loop recycled)", "3901", "Plastic", "280", "kg", "90.00", "25,200.00", "280.0", "Line C"),
        (21, "MAT-221", "PET Resin, bottle grade (primary)", "3907", "Plastic", "250", "kg", "105.00", "26,250.00", "250.0", "Line C"),
        (22, "MAT-222", "rPET Resin (closed-loop recycled)", "3907", "Plastic", "220", "kg", "88.00", "19,360.00", "220.0", "Line C"),
        (23, "MAT-223", "Polypropylene Granules, homopolymer (primary)", "3902", "Plastic", "500", "kg", "118.00", "59,000.00", "500.0", "Line C"),
        (24, "MAT-224", "Polypropylene Granules (closed-loop recycled)", "3902", "Plastic", "420", "kg", "95.00", "39,900.00", "420.0", "Line C"),
        (25, "MAT-225", "Polystyrene Granules (primary)", "3903", "Plastic", "150", "kg", "128.00", "19,200.00", "150.0", "Line C"),
        (26, "MAT-226", "Polystyrene Granules (closed-loop recycled)", "3903", "Plastic", "130", "kg", "98.00", "12,740.00", "130.0", "Line C"),
        (27, "MAT-227", "PVC Resin K67 (primary)", "3904", "Plastic", "400", "kg", "98.00", "39,200.00", "400.0", "Line C"),
        (28, "MAT-228", "PVC Resin (closed-loop recycled)", "3904", "Plastic", "350", "kg", "76.00", "26,600.00", "350.0", "Line C"),
        (29, "MAT-229", "Corrugated Board Sheet (primary)", "4808", "Paper", "500", "kg", "48.00", "24,000.00", "500.0", "Line C"),
        (30, "MAT-230", "Corrugated Board Sheet (closed-loop recycled)", "4808", "Paper", "450", "kg", "38.00", "17,100.00", "450.0", "Line C"),
        (31, "MAT-231", "Mixed Paper & Board Packaging (primary)", "4819", "Paper", "300", "kg", "52.00", "15,600.00", "300.0", "Line C"),
        (32, "MAT-232", "Mixed Paper & Board Packaging (recycled)", "4819", "Paper", "280", "kg", "41.00", "11,480.00", "280.0", "Line C"),
        (33, "MAT-233", "Kraft Paper Roll (primary)", "4804", "Paper", "200", "kg", "65.00", "13,000.00", "200.0", "Line C"),
        (34, "MAT-234", "Kraft Paper Roll (closed-loop recycled)", "4804", "Paper", "180", "kg", "50.00", "9,000.00", "180.0", "Line C"),
        (35, "MAT-235", "Refrigeration / Cooling Unit Assembly", "8418", "Electrical items", "120", "kg", "620.00", "74,400.00", "120.0", "Line B"),
        (36, "MAT-236", "Large Electrical Appliance Sub-assembly", "8537", "Electrical items", "150", "kg", "480.00", "72,000.00", "150.0", "Line B"),
        (37, "MAT-237", "IT Hardware - Line Control PC & Panel", "8471", "Electrical items", "40", "kg", "2,800.00", "112,000.00", "40.0", "Line B"),
        (38, "MAT-238", "Small Electrical Components Kit", "8536", "Electrical items", "60", "kg", "950.00", "57,000.00", "60.0", "Line B"),
        (39, "MAT-239", "Alkaline Battery Pack", "8506", "Electrical items", "50", "kg", "720.00", "36,000.00", "50.0", "Line B"),
        (40, "MAT-240", "Lithium-ion Battery Module", "8507", "Electrical items", "80", "kg", "1,850.00", "148,000.00", "80.0", "Line B"),
        (41, "MAT-241", "NiMH Battery Pack", "8507", "Electrical items", "30", "kg", "1,450.00", "43,500.00", "30.0", "Line B"),
        (42, "MAT-242", "Glass Sheet 4 mm (primary)", "7005", "Other", "350", "kg", "95.00", "33,250.00", "350.0", "Line B"),
        (43, "MAT-243", "Glass Cullet Feedstock (closed-loop recycled)", "7001", "Other", "300", "kg", "42.00", "12,600.00", "300.0", "Line B"),
        (44, "MAT-244", "Foundry Sand / Aggregate", "2517", "Construction", "1,200", "kg", "4.50", "5,400.00", "1,200.0", "Line A"),
        (45, "MAT-245", "Refractory Brick - Furnace Lining", "6902", "Construction", "600", "kg", "48.00", "28,800.00", "600.0", "Line A"),
        (46, "MAT-246", "Precast Concrete Machine Base", "6810", "Construction", "1,500", "kg", "12.00", "18,000.00", "1,500.0", "Line A"),
        (47, "MAT-247", "Thermal Insulation Board - Oven Panels", "6806", "Construction", "120", "kg", "340.00", "40,800.00", "120.0", "Line A"),
        (48, "MAT-248", "Mineral Oil - Hydraulic ISO VG 68", "2710", "Construction", "200", "kg", "245.00", "49,000.00", "200.0", "Line A"),
        (49, "MAT-249", "Forklift Tyre Set", "4011", "Construction", "180", "kg", "420.00", "75,600.00", "180.0", "Line A"),
        (50, "MAT-250", "Wooden Pallets / Timber Packing", "4415", "Construction", "700", "kg", "38.00", "26,600.00", "700.0", "Line C"),
    ]
    
    # Table A - Material items (all 50 rows in a single flow table that splits across page 1 and page 2)
    story.append(Paragraph("<b>A. MATERIAL LINE ITEMS (50)</b>", styles['Heading2']))
    
    mat_headers = ["#", "Material ID", "Description", "HS Code", "Category", "Qty", "Unit", "Rate (INR)", "Amount (INR)", "Weight (kg)", "Line"]
    table_data = [[Paragraph(f"<b>{h}</b>", header_style) for h in mat_headers]]
    
    for row in materials:
        row_cells = [
            Paragraph(str(row[0]), cell_style),
            Paragraph(str(row[1]), cell_style),
            Paragraph(str(row[2]), cell_style),
            Paragraph(str(row[3]), cell_style),
            Paragraph(str(row[4]), cell_style),
            Paragraph(str(row[5]), cell_style),
            Paragraph(str(row[6]), cell_style),
            Paragraph(str(row[7]), cell_style),
            Paragraph(str(row[8]), cell_style),
            Paragraph(str(row[9]), cell_style),
            Paragraph(str(row[10]), cell_style)
        ]
        table_data.append(row_cells)
        
    t_mat = Table(table_data, colWidths=[16, 45, 150, 35, 55, 30, 22, 42, 50, 50, 35], repeatRows=1)
    t_mat.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.lightgrey),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_mat)
    story.append(Spacer(1, 8))
    
    # Total net weight line
    story.append(Paragraph("Total line items: 50 | Total net weight: 19,210.0 kg (19.210 MT)", cell_style))
    story.append(Spacer(1, 8))
    
    # Section B: Transport Table
    story.append(Paragraph("<b>B. TRANSPORT / DELIVERY - SINGLE LEG, SINGLE DAY</b>", styles['Heading2']))
    trans_headers = ["Ship ID", "Date", "Transport Mode", "Vehicle No.", "LR No.", "Origin", "Destination", "Distance km", "Gross Wt kg", "Fuel", "Trips"]
    trans_data = [
        [Paragraph(f"<b>{h}</b>", header_style) for h in trans_headers],
        [
            Paragraph("SHIP-005", cell_style),
            Paragraph("2025-01-28", cell_style),
            Paragraph("Road - HGV articulated (>3.5-33 t), non-refrigerated diesel", cell_style),
            Paragraph("MH-14-GQ-8421", cell_style),
            Paragraph("LR-2025-0128-77", cell_style),
            Paragraph("Pune, Maharashtra", cell_style),
            Paragraph("Mumbai, Maharashtra (FAC-001)", cell_style),
            Paragraph("180", cell_style),
            Paragraph("19,210.0", cell_style),
            Paragraph("Diesel", cell_style),
            Paragraph("1", cell_style)
        ]
    ]
    t_trans = Table(trans_data, colWidths=[42, 45, 115, 52, 55, 60, 75, 35, 42, 32, 20])
    t_trans.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.lightgrey),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_trans)
    story.append(Spacer(1, 4))
    story.append(Paragraph("Single delivery leg on 2025-01-28 - one vehicle, one trip, one day, no intermediate hop. Load factor: 50% laden (single full-truck load).", cell_style))
    story.append(Spacer(1, 8))
    
    # Section C: Summary & Totals
    story.append(Paragraph("<b>C. SUMMARY & TOTALS</b>", styles['Heading2']))
    sum_data = [
        [Paragraph("<b>Category</b>", header_style), Paragraph("<b>Weight (kg)</b>", header_style), Paragraph("<b>Value (INR)</b>", header_style), Paragraph("<b>Material subtotal (50 items)</b>", header_style), Paragraph("1,988,830.00", cell_style)],
        [Paragraph("Construction", cell_style), Paragraph("7,200.0", cell_style), Paragraph("386,400.00", cell_style), Paragraph("<b>Freight / transport charge (SHIP-005)</b>", cell_style), Paragraph("42,000.00", cell_style)],
        [Paragraph("Plastic", cell_style), Paragraph("5,540.0", cell_style), Paragraph("584,350.00", cell_style), Paragraph("<b>Taxable value</b>", cell_style), Paragraph("2,030,830.00", cell_style)],
        [Paragraph("Metal", cell_style), Paragraph("3,380.0", cell_style), Paragraph("339,150.00", cell_style), Paragraph("<b>CGST @ 9%</b>", cell_style), Paragraph("182,774.70", cell_style)],
        [Paragraph("Paper", cell_style), Paragraph("1,910.0", cell_style), Paragraph("90,180.00", cell_style), Paragraph("<b>SGST @ 9%</b>", cell_style), Paragraph("182,774.70", cell_style)],
        [Paragraph("Other", cell_style), Paragraph("650.0", cell_style), Paragraph("45,850.00", cell_style), Paragraph("<b>Rounding</b>", cell_style), Paragraph("-0.40", cell_style)],
        [Paragraph("Electrical items", cell_style), Paragraph("530.0", cell_style), Paragraph("542,900.00", cell_style), Paragraph("<b>GRAND TOTAL (INR)</b>", header_style), Paragraph("<b>2,396,379.00</b>", header_style)],
        [Paragraph("<b>Total</b>", header_style), Paragraph("<b>19,210.0</b>", header_style), Paragraph("<b>1,988,830.00</b>", header_style), Paragraph("", cell_style), Paragraph("", cell_style)]
    ]
    t_sum = Table(sum_data, colWidths=[75, 55, 65, 140, 75])
    t_sum.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.grey),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.lightgrey),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
    ]))
    story.append(t_sum)
    story.append(Spacer(1, 6))
    
    story.append(Paragraph("Declaration: the particulars given above are true and correct. Goods once sold will not be taken back. Interest @ 18% p.a. is chargeable on invoices not settled within the agreed credit period. Subject to Mumbai jurisdiction. This is a computer-generated invoice.<br/>Synthetic sample data for CarbonLedger system testing - not a real commercial document.", cell_style))
    
    doc.build(story)
    print(f"Generated test PDF: {pdf_path}")

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "fixtures")
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "INV-005_TechManufacturing_50Materials_Invoice.pdf")
    generate_inv_005(target)
