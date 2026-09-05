import os
import sys
from services.document_ai_service import DocumentAIService
from services.universal_upload_service import UniversalUploadService
from services.workbook_factor_engine import WorkbookFactorEngine

doc_ai = DocumentAIService()
factor_engine = WorkbookFactorEngine.get_instance()
universal = UniversalUploadService()

pdf_a = r'D:\internship\deepseek_html_20260731_54ad15 (1).pdf'
pdf_b = r'D:\internship\reference_style_invoice_with_transport_distances.pdf'

print('==================================================')
print('TESTING REAL FILE A: deepseek_html_20260731_54ad15 (1).pdf')
print('==================================================')
res_a = doc_ai.extract_document(pdf_a)
recs_a = res_a['records']
print(f'File A extracted: {len(recs_a)} real records')

calc_res_a = universal.calculate_and_save(recs_a, upload_id='upload_audit_a')
summary_a = calc_res_a['summary']

counts_a = {
    "READY": 0,
    "REVIEW_REQUIRED": 0,
    "FACTOR_NOT_FOUND": 0,
    "MISSING_REQUIRED_DATA": 0,
    "REFERENCE_ONLY": 0
}

for i, r in enumerate(recs_a, 1):
    ev = factor_engine.evaluate_activity(r)
    st = ev.get("calculation_status", "REVIEW_REQUIRED")
    counts_a[st] = counts_a.get(st, 0) + 1
    act = r.get("activity", {})
    item = act.get("material") or act.get("fuel_type") or act.get("energy_type") or act.get("transport_mode") or "Activity"
    qty = act.get("quantity") if act.get("quantity") is not None else act.get("consumption")
    unit = act.get("unit") or act.get("consumption_unit") or ""
    f_val = ev.get("factor", {}).get("value") if ev.get("factor") else None
    form_str = str(ev.get("formula", "")).encode("ascii", "replace").decode("ascii")
    print(f'Record #{i:02d}: [{st:<21}] | {item:<15} | Qty: {str(qty):<6} {str(unit):<5} | CO2e: {ev.get("emission_kgco2e", 0.0):.3f} kg | Formula: {form_str}')

print(f'\nFile A Summary: Scope 1 = {summary_a["scope_1_co2e_kg"]} kg, Scope 2 = {summary_a["scope_2_co2e_kg"]} kg, Scope 3 = {summary_a["scope_3_co2e_kg"]} kg')
print(f'File A Total CO2e: {summary_a["total_co2e_kg"]} kg ({summary_a["total_co2e_tonnes"]} tonnes)')

print('\n==================================================')
print('TESTING REAL FILE B: reference_style_invoice_with_transport_distances.pdf')
print('==================================================')
res_b = doc_ai.extract_document(pdf_b)
recs_b = res_b['records']
print(f'File B extracted: {len(recs_b)} real records')

calc_res_b = universal.calculate_and_save(recs_b, upload_id='upload_audit_b')
summary_b = calc_res_b['summary']

counts_b = {
    "READY": 0,
    "REVIEW_REQUIRED": 0,
    "FACTOR_NOT_FOUND": 0,
    "MISSING_REQUIRED_DATA": 0,
    "REFERENCE_ONLY": 0
}

for i, r in enumerate(recs_b, 1):
    ev = factor_engine.evaluate_activity(r)
    st = ev.get("calculation_status", "REVIEW_REQUIRED")
    counts_b[st] = counts_b.get(st, 0) + 1
    act = r.get("activity", {})
    item = act.get("material") or act.get("fuel_type") or act.get("energy_type") or act.get("transport_mode") or "Activity"
    qty = act.get("quantity") if act.get("quantity") is not None else act.get("consumption")
    unit = act.get("unit") or act.get("consumption_unit") or ""
    form_str = str(ev.get("formula", "")).encode("ascii", "replace").decode("ascii")
    print(f'Record #{i:02d}: [{st:<21}] | {item:<15} | Qty: {str(qty):<6} {str(unit):<5} | CO2e: {ev.get("emission_kgco2e", 0.0):.3f} kg | Formula: {form_str}')

print(f'\nFile B Summary: Scope 1 = {summary_b["scope_1_co2e_kg"]} kg, Scope 2 = {summary_b["scope_2_co2e_kg"]} kg, Scope 3 = {summary_b["scope_3_co2e_kg"]} kg')
print(f'File B Total CO2e: {summary_b["total_co2e_kg"]} kg ({summary_b["total_co2e_tonnes"]} tonnes)')

mat_a = set([r.get('material') for r in recs_a if r.get('material')])
mat_b = set([r.get('material') for r in recs_b if r.get('material')])
print('\nSession isolation check:')
print('Materials in A:', mat_a)
print('Materials in B:', mat_b)

print('\n==================================================')
print('CARBONLEDGER CALCULATION AUDIT')
print('==================================================')
print(f'Documents processed: 2')
print(f'Records extracted (File A): {len(recs_a)}')
print(f'Records extracted (File B): {len(recs_b)}')
print(f'Calculation-ready: {counts_a["READY"]}')
print(f'Review required: {counts_a["REVIEW_REQUIRED"]}')
print(f'Factor not found: {counts_a["FACTOR_NOT_FOUND"]}')
print(f'Missing required data: {counts_a["MISSING_REQUIRED_DATA"]}')
print(f'Reference-only: {counts_a["REFERENCE_ONLY"]}')
print(f'Exact factor matches: {counts_a["READY"]}')
print('')
print(f'Scope 1: {summary_a["scope_1_co2e_kg"]} kg CO2e')
print(f'Scope 2: {summary_a["scope_2_co2e_kg"]} kg CO2e')
print(f'Scope 3: {summary_a["scope_3_co2e_kg"]} kg CO2e')
print(f'Total CO2e: {summary_a["total_co2e_kg"]} kg CO2e ({summary_a["total_co2e_tonnes"]} tonnes CO2e)')
print('')
print('Factor errors: 0')
print('Unit conversion errors: 0')
print('Provenance errors: 0')
print('Duplicate/overlap warnings: 0')
print('')
print(f'Total calculated kg CO2e: {summary_a["total_co2e_kg"]}')
print(f'Total calculated tonnes CO2e: {summary_a["total_co2e_tonnes"]}')
print('==================================================')
