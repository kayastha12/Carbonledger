import json
import pandas as pd
from models.document_classifier import DocumentClassifier
from models.ner_extractor import NERExtractor
from services.matching_service import MatchingService
from services.calculation_engine import CalculationEngine
from services.recommendation_engine import RecommendationEngine

def run_end_to_end_pipeline(ocr_text, facility_name="Main Plant"):
    print("=" * 60)
    print("CarbonLedger End-to-End AI Audit Pipeline Running")
    print("=" * 60)
    
    # 1. Classification
    print("\n[Step 1] Classifying document...")
    classifier = DocumentClassifier()
    doc_class = classifier.classify(ocr_text)
    print(f"-> Classified as: {doc_class}")
    
    # 2. NER Extraction
    print("\n[Step 2] Extracting line items and entities...")
    extractor = NERExtractor()
    entities = extractor.extract(ocr_text)
    print(f"-> Extracted Material: {entities['material']}")
    print(f"-> Extracted Qty: {entities['quantity']} {entities['unit']}")
    
    # 3. Supplier Matching
    print("\n[Step 3] Matching Supplier...")
    matcher = MatchingService()
    sup_match = matcher.match_supplier(entities["supplier_name"])
    print(f"-> Fuzzy Match Name: {sup_match['matched_name']} (Confidence: {sup_match['confidence']:.2%})")
    
    # 4. Factor Matching
    print("\n[Step 4] Matching Emission Factors semantically...")
    query_term = entities["material"] if entities["material"] else doc_class
    factors = matcher.match_emission_factor(query_term, top_n=3)
    best_factor = factors[0] if factors else None
    if best_factor:
        print(f"-> Semantic Match: {best_factor['category']} - {best_factor['activity']}")
        print(f"-> Factor: {best_factor['factor']} {best_factor['ghg_unit']}/{best_factor['uom']} (Conf: {best_factor['confidence']:.2%})")
    else:
        print("-> No matching factor found in vector DB.")
        
    # 5. Calculation
    print("\n[Step 5] Calculating greenhouse gas emissions...")
    calculator = CalculationEngine()
    emission_result = {}
    
    factor_id = best_factor["id"] if best_factor else None
    
    if doc_class == "Invoice" or doc_class == "Purchase Order":
        emission_result = calculator.calculate_scope_3_category_1(
            material=entities["material"],
            quantity=entities["quantity"],
            unit=entities["unit"],
            factor_id=factor_id
        )
    elif doc_class == "Utility Bill":
        if "Electricity" in ocr_text or entities["electricity_consumption"] > 0:
            emission_result = calculator.calculate_scope_2(
                consumption_kwh=entities["electricity_consumption"] or 1000.0,
                country=entities["country"] or "GB",
                factor_id=factor_id
            )
        else:
            emission_result = calculator.calculate_scope_1(
                fuel_type=entities["fuel_type"],
                quantity=entities["quantity"],
                unit=entities["unit"],
                factor_id=factor_id
            )
    elif doc_class == "Shipping Manifest":
        emission_result = calculator.calculate_scope_3_category_4(
            weight_tonnes=entities["weight"] or 10.0,
            distance_km=entities["distance"] or 100.0,
            mode=entities["vehicle"] or "road",
            factor_id=factor_id
        )
        
    print(f"-> Calculation Output: {json.dumps(emission_result, indent=2)}")
    
    # 6. Recommendation
    print("\n[Step 6] Generating optimization recommendations...")
    recommender = RecommendationEngine()
    
    # Pack single item into dataframe to test recommendations logic
    sample_df = pd.DataFrame([{
        "supplier_name": sup_match["matched_name"],
        "co2e_kg": emission_result.get("co2e_kg", emission_result.get("location_based_co2e_kg", 0.0)),
        "category": doc_class,
        "mode": entities["vehicle"]
    }])
    
    recs = recommender.generate_recommendations(sample_df)
    print(f"-> Recommendations Generated: {len(recs)} suggestions.")
    print(json.dumps(recs[0], indent=2))
    
    print("\n" + "=" * 60)
    print("PIPELINE EXECUTION COMPLETE")
    print("=" * 60)
    
    return {
        "classification": doc_class,
        "entities": entities,
        "supplier": sup_match,
        "factor": best_factor,
        "emissions": emission_result,
        "recommendations": recs
    }

if __name__ == "__main__":
    # Test invoice OCR string
    test_ocr = (
        "=== CarbonLedger ERP Document === | Document Type: Invoice | "
        "Reference Number: INV-242358 | Date: 2026-10-12 | Company ID: 38 | "
        "Supplier ID: 3739 | Total Value: 109987.85 | Language: English |"
    )
    run_end_to_end_pipeline(test_ocr)
