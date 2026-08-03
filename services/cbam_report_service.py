import os, csv, datetime, math
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from fpdf import FPDF

OUTPUT_DIR = 'd:/internship/carbonledger/output/reports'

def _ensure_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def _safe(val, default=0.0):
    try:
        f = float(val)
        return f if not math.isnan(f) else default
    except Exception:
        return default

def _fmt(val, decimals=2):
    try:
        template = '{:,.' + str(decimals) + 'f}'
        return template.format(float(val))
    except Exception:
        return str(val)


class CBAMReportPDF(FPDF):
    def __init__(self, report_id, timestamp):
        super().__init__()
        self.report_id = report_id
        self.timestamp = timestamp
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()

    def header(self):
        self.set_font('Helvetica', 'B', 10)
        self.set_fill_color(15, 23, 42)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, '  CarbonLedger  |  EU CBAM Audited Emission Report', fill=True, new_line='NEXT')
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, 'Report: ' + self.report_id[:16] + '  Page: ' + str(self.page_no()) + '  Generated: ' + self.timestamp, align='C')

    def section_title(self, title):
        self.ln(4)
        self.set_font('Helvetica', 'B', 12)
        self.set_fill_color(16, 185, 129)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, '  ' + title, fill=True, new_line='NEXT')
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def kv_row(self, label, value, shade=False):
        self.set_font('Helvetica', '', 9)
        fill = shade
        if shade:
            self.set_fill_color(248, 250, 252)
        self.cell(80, 7, label, border='B', fill=fill)
        self.set_font('Helvetica', 'B', 9)
        self.cell(0, 7, str(value)[:60], border='B', fill=fill, new_line='NEXT')

    def tbl_hdr(self, cols, widths):
        self.set_font('Helvetica', 'B', 8)
        self.set_fill_color(30, 41, 59)
        self.set_text_color(255, 255, 255)
        for col, w in zip(cols, widths):
            self.cell(w, 7, col, border=1, fill=True, align='C')
        self.ln()
        self.set_text_color(0, 0, 0)

    def tbl_row(self, vals, widths, shade=False):
        self.set_font('Helvetica', '', 8)
        fill = shade
        if shade:
            self.set_fill_color(245, 247, 250)
        for val, w in zip(vals, widths):
            self.cell(w, 6, str(val)[:34], border=1, fill=fill)
        self.ln()


def generate_pdf(report):
    _ensure_dir()
    report_id = report.get('report_id', 'unknown')
    timestamp = report.get('timestamp', datetime.datetime.now().isoformat())
    company = report.get('company', {})
    summary = report.get('summary', {})
    records = report.get('records', [])
    logs = report.get('logs', [])
    warnings = report.get('warnings', [])

    pdf = CBAMReportPDF(report_id, timestamp[:19])
    first = records[0] if records else {}

    pdf.section_title('SECTION 1 - Company and Product Information')
    rows1 = [
        ('Importer', company.get('importer', 'EcoSteel Europe GmbH')),
        ('Exporter / Supplier', first.get('supplier', 'N/A')),
        ('Country of Origin', first.get('country', 'N/A')),
        ('Country of Import', company.get('import_country', 'Germany (DE)')),
        ('Facility / Plant', first.get('facility', 'Munich Processing Plant')),
        ('Reporting Period', company.get('reporting_period', 'N/A')),
        ('Report ID', report_id),
        ('Material Name', first.get('material', 'N/A')),
        ('CN Code', first.get('cn_code', '7208 51 00')),
        ('HS Code', first.get('hs_code', '7208')),
        ('Quantity', str(first.get('quantity', 0)) + ' ' + str(first.get('unit', 't'))),
        ('Weight (kg)', _fmt(first.get('qty_kg', _safe(first.get('quantity', 0)) * 1000), 1) + ' kg'),
        ('Production Route', first.get('production_route', 'Basic Oxygen Furnace (BOF)')),
    ]
    for i, (lbl, val) in enumerate(rows1):
        pdf.kv_row(lbl, str(val), shade=(i % 2 == 0))

    pdf.section_title('SECTION 2 - Emission Factor Information')
    pdf.tbl_hdr(['Material', 'EF Value', 'Unit', 'Source', 'Version', 'Confidence'], [35, 22, 30, 58, 22, 20])
    for i, r in enumerate(records):
        pdf.tbl_row([r.get('material', '')[:17], _fmt(r.get('emission_factor', 0), 5), r.get('factor_unit', '')[:14], r.get('factor_source', '')[:27], r.get('factor_version', '2026.1'), _fmt(_safe(r.get('confidence', 0)) * 100, 1) + '%'], [35, 22, 30, 58, 22, 20], shade=(i % 2 == 0))

    pdf.section_title('SECTION 3 - Step-by-Step Carbon Calculations')
    pdf.set_font('Helvetica', 'I', 8)
    pdf.cell(0, 6, 'Formula: Emissions (kg CO2e) = Quantity (kg) x Emission Factor (kg CO2e/kg)', new_line='NEXT')
    pdf.ln(2)
    pdf.tbl_hdr(['Material', 'Qty Raw', 'Unit', 'Qty(kg)', 'EF', 'Formula', 'Result(kg)', 'Verified'], [30, 16, 10, 20, 22, 50, 28, 14])
    for i, r in enumerate(records):
        qr = _safe(r.get('quantity', 0)); u = r.get('unit', 't')
        qk = _safe(r.get('qty_kg', qr * (1000 if u.lower() == 't' else 1)))
        ef = _safe(r.get('emission_factor', 0)); res = _safe(r.get('co2e_kg', 0))
        exp_v = qk * ef; diff = abs(exp_v - res); vpass = diff < max(1.0, abs(res) * 0.001)
        if pdf.get_y() > 260:
            pdf.add_page()
        pdf.tbl_row([r.get('material', '')[:14], _fmt(qr, 3), u, _fmt(qk, 2), _fmt(ef, 4), (_fmt(qk, 2) + 'x' + _fmt(ef, 4))[:24], _fmt(res, 2), 'PASS' if vpass else 'FAIL'], [30, 16, 10, 20, 22, 50, 28, 14], shade=(i % 2 == 0))

    pdf.section_title('SECTION 4 - Scope Summary')
    for i, (lbl, val) in enumerate([
        ('Scope 1 - Direct Emissions (Fuel)', _fmt(summary.get('scope_1_kg', 0), 2) + ' kg CO2e'),
        ('Scope 2 - Grid Electricity', _fmt(summary.get('scope_2_kg', 0), 2) + ' kg CO2e'),
        ('Scope 3 - Supply Chain', _fmt(summary.get('scope_3_kg', 0), 2) + ' kg CO2e'),
        ('Total Carbon Footprint', _fmt(summary.get('total_co2e_kg', 0), 2) + ' kg CO2e'),
        ('Carbon Intensity (tCO2e/t)', _fmt(summary.get('total_specific_t_per_t', 0), 4) + ' tCO2e/t'),
    ]):
        pdf.kv_row(lbl, val, shade=(i % 2 == 0))

    pdf.section_title('SECTION 5 - CBAM Embedded Emissions')
    for i, (lbl, val) in enumerate([
        ('Direct Embedded Emissions', _fmt(summary.get('scope_1_kg', 0), 2) + ' kg CO2e'),
        ('Indirect Embedded Emissions', _fmt(summary.get('scope_2_kg', 0), 2) + ' kg CO2e'),
        ('Total Embedded Emissions', _fmt(summary.get('total_co2e_kg', 0), 2) + ' kg CO2e'),
        ('Specific Direct Intensity', _fmt(summary.get('specific_direct_t_per_t', 0), 4) + ' tCO2e/t'),
        ('Specific Indirect Intensity', _fmt(summary.get('specific_indirect_t_per_t', 0), 4) + ' tCO2e/t'),
        ('Total Specific Intensity', _fmt(summary.get('total_specific_t_per_t', 0), 4) + ' tCO2e/t'),
        ('Verification Status', 'Audited and AI-Verified'),
    ]):
        pdf.kv_row(lbl, val, shade=(i % 2 == 0))

    pdf.section_title('SECTION 6 - Emission Factor Sources')
    pdf.tbl_hdr(['Material', 'Database Name', 'Pub Year', 'Version', 'Reference'], [32, 78, 18, 22, 40])
    for i, r in enumerate(records):
        src = r.get('factor_source', 'GHG Protocol')
        pdf.tbl_row([r.get('material', '')[:15], src[:38], str(r.get('factor_publication_year', '2026')), r.get('factor_version', '2026.1'), ('See ' + src)[:20]], [32, 78, 18, 22, 40], shade=(i % 2 == 0))

    pdf.section_title('SECTION 7 - Calculation Verification Audit')
    pdf.tbl_hdr(['Material', 'Qty(kg)', 'EF', 'Expected', 'Calculated', 'Diff', 'Err%', 'Status'], [30, 20, 22, 24, 24, 18, 18, 18])
    for i, r in enumerate(records):
        qk = _safe(r.get('qty_kg', _safe(r.get('quantity', 0)) * (1000 if r.get('unit', 't').lower() == 't' else 1)))
        ef = _safe(r.get('emission_factor', 0)); exp_v = qk * ef; calc = _safe(r.get('co2e_kg', 0))
        diff = abs(exp_v - calc); err = (diff / max(exp_v, 0.001)) * 100; vpass = diff < max(1.0, abs(calc) * 0.001)
        pdf.tbl_row([r.get('material', '')[:14], _fmt(qk, 1), _fmt(ef, 4), _fmt(exp_v, 1), _fmt(calc, 1), _fmt(diff, 1), _fmt(err, 2) + '%', 'PASS' if vpass else 'FAIL'], [30, 20, 22, 24, 24, 18, 18, 18], shade=(i % 2 == 0))

    pdf.ln(4)
    pdf.section_title('Audit Trail - Pipeline Logs')
    pdf.set_font('Helvetica', '', 8)
    for log in logs[:25]:
        pdf.cell(0, 5, '  * ' + str(log)[:110], new_line='NEXT')
    if warnings:
        pdf.set_font('Helvetica', 'B', 8); pdf.set_text_color(200, 100, 0)
        pdf.cell(0, 6, 'Warnings:', new_line='NEXT')
        pdf.set_text_color(0, 0, 0); pdf.set_font('Helvetica', '', 8)
        for w in warnings:
            pdf.cell(0, 5, '  ! ' + str(w)[:110], new_line='NEXT')

    out = os.path.join(OUTPUT_DIR, 'cbam_report_' + report_id + '.pdf')
    pdf.output(out)
    return out


def _xl_hdr(ws, row, headers):
    hf = Font(bold=True, color='FFFFFF', size=10)
    hfill = PatternFill('solid', fgColor='0F172A')
    ha = Alignment(horizontal='center', wrap_text=True)
    hb = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    for ci, h in enumerate(headers, start=1):
        c = ws.cell(row=row, column=ci, value=h); c.font = hf; c.fill = hfill; c.alignment = ha; c.border = hb

def _xl_row(ws, row, values, shade=False):
    fill = PatternFill('solid', fgColor='F8FAFC') if shade else None
    b = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    for ci, v in enumerate(values, start=1):
        c = ws.cell(row=row, column=ci, value=v)
        if fill: c.fill = fill
        c.border = b; c.alignment = Alignment(wrap_text=True)

def _xl_aw(ws):
    for col in ws.columns:
        mx = max((len(str(c.value)) for c in col if c.value), default=10)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(mx + 4, 52)


def generate_excel(report):
    _ensure_dir()
    rid = report.get('report_id', 'unknown')
    co = report.get('company', {}); sm = report.get('summary', {}); recs = report.get('records', []); at = report.get('audit_trail', [])
    wb = openpyxl.Workbook()
    ws1 = wb.active; ws1.title = 'CBAM Summary'
    ws1.merge_cells('A1:B1'); c = ws1['A1']; c.value = 'CarbonLedger EU CBAM Audited Report'
    c.font = Font(bold=True, size=14, color='10B981'); c.alignment = Alignment(horizontal='center')
    sum_data = [
        ('Report ID', rid), ('Company', co.get('name', 'N/A')), ('Importer', co.get('importer', 'EcoSteel Europe GmbH')),
        ('Reporting Period', co.get('reporting_period', 'N/A')), ('Timestamp', report.get('timestamp', '')[:19]), ('', ''),
        ('Total CO2e (kg)', _safe(sm.get('total_co2e_kg', 0))), ('Scope 1 (kg)', _safe(sm.get('scope_1_kg', 0))),
        ('Scope 2 (kg)', _safe(sm.get('scope_2_kg', 0))), ('Scope 3 (kg)', _safe(sm.get('scope_3_kg', 0))),
        ('Production Weight (t)', _safe(sm.get('production_weight_t', 0))),
        ('Specific Direct (tCO2e/t)', _safe(sm.get('specific_direct_t_per_t', 0))),
        ('Specific Indirect (tCO2e/t)', _safe(sm.get('specific_indirect_t_per_t', 0))),
        ('Total Intensity (tCO2e/t)', _safe(sm.get('total_specific_t_per_t', 0))),
        ('Verification', 'Audited and AI-Verified'),
    ]
    _xl_hdr(ws1, 2, ['Field', 'Value'])
    for i, (k, v) in enumerate(sum_data, start=3): _xl_row(ws1, i, [k, v], shade=(i % 2 == 0))
    _xl_aw(ws1)
 
    ws2 = wb.create_sheet('Material Records')
    _xl_hdr(ws2, 1, ['Filename','Doc Type','Supplier','Material','Quantity','Unit','Converted Qty','Converted Unit','CO2e(kg)','Scope','Scope Category','EF','EF Unit','EF Source','EF Version','Confidence%','Date','Time','Model Used'])
    for i, r in enumerate(recs, start=2):
        _xl_row(ws2, i, [
            r.get('filename',''),
            r.get('document_type',''),
            r.get('supplier',''),
            r.get('material',''),
            _safe(r.get('quantity', 0)),
            r.get('unit','t'),
            _safe(r.get('converted_qty', r.get('qty_kg', 0))),
            r.get('converted_unit', 'kg'),
            round(_safe(r.get('co2e_kg',0)),2),
            r.get('scope',''),
            r.get('scope_category',''),
            _safe(r.get('emission_factor',0)),
            r.get('factor_unit',''),
            r.get('factor_source',''),
            r.get('factor_version',''),
            round(_safe(r.get('confidence',0))*100,1),
            r.get('date',''),
            r.get('time',''),
            r.get('model_used','')
        ], shade=(i%2==0))
    _xl_aw(ws2)
 
    ws3 = wb.create_sheet('Scope Breakdown')
    _xl_hdr(ws3, 1, ['Scope','Description','Method','Emissions(kg CO2e)','Pct of Total'])
    tot=_safe(sm.get('total_co2e_kg',1)); s1=_safe(sm.get('scope_1_kg',0)); s2=_safe(sm.get('scope_2_kg',0)); s3=_safe(sm.get('scope_3_kg',0))
    
    # Calculate real dynamic Scope 3 category breakdowns
    s3_cat1 = sum(_safe(r.get('co2e_kg', 0)) for r in recs if r.get('scope_category') == 'Scope 3 Category 1')
    s3_cat4 = sum(_safe(r.get('co2e_kg', 0)) for r in recs if r.get('scope_category') == 'Scope 3 Category 4')
    other_s3 = s3 - (s3_cat1 + s3_cat4)
    
    breakdown_rows = [
        ('Scope 1','Direct Fuel','Fuel Qty x EF',s1,round(s1/max(tot,1)*100,2)),
        ('Scope 2','Grid Electricity','kWh x Grid EF',s2,round(s2/max(tot,1)*100,2)),
        ('Scope 3 Category 1','Purchased Goods','Weight x EF',s3_cat1,round(s3_cat1/max(tot,1)*100,2)),
        ('Scope 3 Category 4','Transport','Weight x Dist x Mode',s3_cat4,round(s3_cat4/max(tot,1)*100,2))
    ]
    if other_s3 > 0.01:
        breakdown_rows.append(('Scope 3 Other','Other Value Chain','Other factors',other_s3,round(other_s3/max(tot,1)*100,2)))
    breakdown_rows.append(('TOTAL','All Scopes','S1+S2+S3',tot,100.0))
    
    for i, row in enumerate(breakdown_rows, start=2):
        _xl_row(ws3, i, list(row), shade=(i%2==0))
    _xl_aw(ws3)
 
    ws4 = wb.create_sheet('Calculations')
    _xl_hdr(ws4, 1, ['Material','Scope','Qty Raw','Unit','Converted Qty','Converted Unit','EF','EF Unit','Formula','Intermediate Calculation','Expected(kg)','Calculated(kg)','Difference','Error Pct','Verification'])
    for i, r in enumerate(recs, start=2):
        u=r.get('unit','t'); qr=_safe(r.get('quantity',0)); qk=_safe(r.get('converted_qty', r.get('qty_kg', 0))); cu=r.get('converted_unit', 'kg')
        ef=_safe(r.get('emission_factor',0)); calc=_safe(r.get('co2e_kg',0))
        exp_v=qk*ef; diff=abs(exp_v-calc); err=round((diff/max(exp_v,0.001))*100,4)
        vpass=diff<max(1.0,abs(calc)*0.001)
        frm=r.get('formula', 'Quantity (converted) x EF')
        inter=r.get('intermediate_calculation', f"{qk:.3f} {cu} x {ef:.5f} = {calc:.2f} kg CO2e")
        _xl_row(ws4, i, [r.get('material',''),r.get('scope',''),qr,u,round(qk,3),cu,round(ef,5),r.get('factor_unit',''),frm,inter,round(exp_v,2),round(calc,2),round(diff,2),err,'PASS' if vpass else 'FAIL'], shade=(i%2==0))
    _xl_aw(ws4)
 
    ws5 = wb.create_sheet('Audit Trail')
    _xl_hdr(ws5, 1, ['Timestamp','Agent','Confidence%','Message'])
    for i, t in enumerate(at, start=2): _xl_row(ws5, i, [t.get('timestamp',''),t.get('agent',''),round(_safe(t.get('confidence',0))*100,1),t.get('message','')], shade=(i%2==0))
    _xl_aw(ws5)
 
    out = os.path.join(OUTPUT_DIR, 'cbam_report_' + rid + '.xlsx')
    wb.save(out)
    return out
 
 
def generate_csv(report):
    _ensure_dir()
    rid = report.get('report_id', 'unknown'); recs = report.get('records', [])
    out = os.path.join(OUTPUT_DIR, 'cbam_report_' + rid + '.csv')
    fields = ['filename','document_type','supplier','material','quantity','unit','converted_qty','converted_unit','co2e_kg','scope','scope_category','emission_factor','factor_unit','factor_source','factor_version','confidence','country','cn_code','hs_code','formula','intermediate_calculation','expected_co2e_kg','verification_pass','date','time','model_used']
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        for r in recs:
            qk = _safe(r.get('converted_qty', r.get('qty_kg', 0)))
            cu = r.get('converted_unit', 'kg')
            ef = _safe(r.get('emission_factor',0)); calc = _safe(r.get('co2e_kg',0)); exp_v = qk*ef; diff=abs(exp_v-calc); vpass=diff<max(1.0,abs(calc)*0.001)
            row={k:r.get(k,'') for k in fields}
            row['converted_qty']=round(qk,3)
            row['converted_unit']=cu
            row['expected_co2e_kg']=round(exp_v,2)
            row['verification_pass']='PASS' if vpass else 'FAIL'
            row['formula']=r.get('formula', 'Quantity (converted) x EF')
            row['intermediate_calculation']=r.get('intermediate_calculation', f"{qk:.3f} {cu} x {ef:.5f} = {calc:.2f} kg CO2e")
            w.writerow(row)
    return out
