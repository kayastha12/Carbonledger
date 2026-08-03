import os
import pandas as pd

def generate_files():
    report_dir = "d:/internship/carbonledger/output/reports"
    os.makedirs(report_dir, exist_ok=True)
    
    # 1. Excel Report
    excel_path = os.path.join(report_dir, "cbam_quarterly_report_q2_2026.xlsx")
    df_cbam = pd.DataFrame([
        {"Section": "Declaration Info", "Field": "Importer Name", "Value": "EcoSteel Corp Europe"},
        {"Section": "Declaration Info", "Field": "Importer EORI", "Value": "EU882312091"},
        {"Section": "Declaration Info", "Field": "Exporter Name", "Value": "SteelCorp Inc India"},
        {"Section": "Declaration Info", "Field": "Exporter Location", "Value": "Mumbai Plant, IN"},
        {"Section": "Declaration Info", "Field": "Country of Origin", "Value": "India (IN)"},
        {"Section": "Product Info", "Field": "CN / HS Code", "Value": "7208 51 20"},
        {"Section": "Product Info", "Field": "Material Group", "Value": "Iron and Steel"},
        {"Section": "Product Info", "Field": "Production Route", "Value": "Electric Arc Furnace (EAF)"},
        {"Section": "Emissions Specifics", "Field": "Direct Emissions (t/t)", "Value": 1.25},
        {"Section": "Emissions Specifics", "Field": "Indirect Emissions (t/t)", "Value": 0.45},
        {"Section": "Emissions Specifics", "Field": "Total Specific Emissions (t/t)", "Value": 1.70},
        {"Section": "Verification", "Field": "Audit Status", "Value": "Verified"},
        {"Section": "Verification", "Field": "AI Confidence Score", "Value": 0.95}
    ])
    df_cbam.to_excel(excel_path, index=False, sheet_name="CBAM Q2 2026")
    print("Generated Excel report:", excel_path)
    
    # 2. PDF Report (Compliant text PDF layout representation)
    pdf_path = os.path.join(report_dir, "cbam_quarterly_report_q2_2026.pdf")
    pdf_content = """%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 500 >>
stream
BT
/F1 14 Tf
70 800 Td (CARBONLEDGER COMPLIANT CBAM DECLARATION REPORT) Tj
/F1 10 Tf
0 -30 Td (Reporting Period: Q2 2026) Tj
0 -20 Td (Importer: EcoSteel Corp Europe (EORI: EU882312091)) Tj
0 -15 Td (Exporter: SteelCorp Inc India (Mumbai Plant, IN)) Tj
0 -15 Td (Country of Origin: India (IN)) Tj
0 -30 Td (Product Classification Details:) Tj
0 -15 Td (CN Code: 7208 51 20 - Iron and Steel (Electric Arc Furnace route)) Tj
0 -30 Td (Specific Embedded Carbon Intensities:) Tj
0 -15 Td (Embedded Direct Emissions: 1.25 tCO2e/tonne) Tj
0 -15 Td (Embedded Indirect Emissions: 0.45 tCO2e/tonne) Tj
0 -15 Td (Total Specific Intensity: 1.70 tCO2e/tonne) Tj
0 -30 Td (Verification Audit Status: Audited & Verified) Tj
0 -15 Td (AI Verification Confidence: 95.00%) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000056 00000 n 
0000000111 00000 n 
0000000244 00000 n 
0000000806 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
895
%%EOF
"""
    with open(pdf_path, "wb") as f:
        f.write(pdf_content.encode("utf-8", errors="ignore"))
    print("Generated PDF report:", pdf_path)

if __name__ == "__main__":
    generate_files()
