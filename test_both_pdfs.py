import time
from services.document_ai_service import DocumentAIService

doc_ai = DocumentAIService()

print("=== Test 1: 50 Materials Invoice ===")
t0 = time.time()
res1 = doc_ai.extract_document("tests/fixtures/INV-005_TechManufacturing_50Materials_Invoice.pdf")
t1 = time.time()
recs1 = res1.get("records", [])
print(f"INV-005 Extracted Records: {len(recs1)} in {t1 - t0:.3f}s")
if recs1:
    print(f"Sample INV-005 record: mat={recs1[0].get('activity', {}).get('material')}, qty={recs1[0].get('activity', {}).get('quantity')} {recs1[0].get('activity', {}).get('unit')}")

print("\n=== Test 2: Deepseek Multi-phase PDF ===")
t0 = time.time()
res2 = doc_ai.extract_document("tests/fixtures/deepseek_html_20260731_54ad15 (1).pdf")
t1 = time.time()
recs2 = res2.get("records", [])
print(f"Deepseek Extracted Records: {len(recs2)} in {t1 - t0:.3f}s")
for idx, r in enumerate(recs2):
    act = r.get('activity', {})
    print(f"  [{idx+1}] type={act.get('activity_type')} | mat={act.get('material')} | qty={act.get('quantity')} {act.get('unit')} | mode={act.get('transport_mode')} | fuel={act.get('fuel_type')}")
