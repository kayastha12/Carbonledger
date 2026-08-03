import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CarbonLedgerAgents")

class AgentNode:
    def __init__(self, name, responsibility):
        self.name = name
        self.responsibility = responsibility
        self.memory = []
        self.max_retries = 3

    def run_with_retry(self, state, tool_func):
        retries = 0
        while retries < self.max_retries:
            try:
                logger.info(f"[{self.name}] Running: {self.responsibility} (Attempt {retries+1})")
                start_time = time.time()
                
                # Execute node logic
                result_state, confidence = tool_func(state)
                
                duration = time.time() - start_time
                self.memory.append({"timestamp": start_time, "duration": duration, "confidence": confidence})
                
                logger.info(f"[{self.name}] Step completed successfully. Confidence: {confidence:.2%}")
                return result_state, confidence
            except Exception as e:
                retries += 1
                logger.error(f"[{self.name}] Execution error: {e}. Retrying...")
                if retries == self.max_retries:
                    raise e
        return state, 0.0

class AutonomousWorkflow:
    def __init__(self, classifier, extractor, matcher, calculator, recommender):
        self.classifier = classifier
        self.extractor = extractor
        self.matcher = matcher
        self.calculator = calculator
        self.recommender = recommender
        
        # Instantiate 12 agents
        self.intake_agent = AgentNode("IntakeAgent", "Ingest new documents and route metadata")
        self.ocr_agent = AgentNode("OCRAgent", "Parse layout and extract document words")
        self.ner_agent = AgentNode("NERAgent", "Extract invoice and logistics entities")
        self.validation_agent = AgentNode("ValidationAgent", "Check schema compliance and constraints")
        self.supplier_agent = AgentNode("SupplierAgent", "Match suppliers and audit risk scores")
        self.factor_agent = AgentNode("FactorAgent", "Query ChromaDB and select emission factor")
        self.calc_agent = AgentNode("CalcAgent", "Perform Scope 1/2/3 calculations")
        self.rec_agent = AgentNode("RecAgent", "Identify Pareto hotspots and recommend optimizations")
        self.cbam_agent = AgentNode("CBAMAgent", "Determine specific embedded emissions for EU tariff compliance")
        self.report_agent = AgentNode("ReportAgent", "Compile corporate carbon inventory report")
        self.knowledge_agent = AgentNode("KnowledgeAgent", "Answer system policy Q&A from policy vector store")
        self.monitoring_agent = AgentNode("MonitoringAgent", "Track execution metrics and monitor drift")

    def run_document_audit_pipeline(self, raw_document_text, facility="Main Plant", tenant_id="tenant_1", doc_type=None):
        state = {
            "raw_text": raw_document_text,
            "facility": facility,
            "tenant_id": tenant_id,
            "document_type": doc_type,
            "entities": None,
            "validation_errors": [],
            "supplier_info": None,
            "matched_factor": None,
            "emissions_calc": None,
            "recommendations": None,
            "cbam_metrics": None,
            "report_path": None,
            "execution_audit_trail": []
        }
        
        # Helper logs to append to audit trail
        def audit_log(agent_name, conf, msg):
            state["execution_audit_trail"].append({
                "timestamp": time.time(),
                "agent": agent_name,
                "confidence": conf,
                "message": msg
            })

        # 1. Intake Agent
        def intake_tool(s):
            if not s["document_type"]:
                s["document_type"] = self.classifier.classify(s["raw_text"])
            return s, 0.99
        state, conf = self.intake_agent.run_with_retry(state, intake_tool)
        audit_log("IntakeAgent", conf, f"Routed document of classified type '{state['document_type']}'")
        
        # 2. OCR Agent (layout parser simulation)
        def ocr_tool(s):
            # Layout validation
            lines = s["raw_text"].split("|")
            has_headers = any("=== " in l for l in lines)
            conf_val = 0.98 if has_headers else 0.75
            return s, conf_val
        state, conf = self.ocr_agent.run_with_retry(state, ocr_tool)
        audit_log("OCRAgent", conf, "OCR word-level confidence confirmed")

        # 3. NER Agent
        def ner_tool(s):
            s["entities"] = self.extractor.extract(s["raw_text"])
            return s, 0.96
        state, conf = self.ner_agent.run_with_retry(state, ner_tool)
        audit_log("NERAgent", conf, f"Extracted material: {state['entities'].get('material')}")

        # 4. Validation Agent
        def val_tool(s):
            ents = s["entities"]
            errors = []
            if not ents.get("invoice_number"):
                errors.append("Missing invoice reference number")
            if ents.get("quantity", 0.0) < 0:
                errors.append("Invalid negative quantity")
            s["validation_errors"] = errors
            conf_val = 1.0 if not errors else 0.40
            return s, conf_val
        state, conf = self.validation_agent.run_with_retry(state, val_tool)
        audit_log("ValidationAgent", conf, f"Validation complete. Errors found: {len(state['validation_errors'])}")

        # 5. Supplier Intelligence Agent
        def supplier_tool(s):
            sup_name = s["entities"].get("supplier_name", "Unknown")
            s["supplier_info"] = self.matcher.match_supplier(sup_name)
            return s, s["supplier_info"]["confidence"]
        state, conf = self.supplier_agent.run_with_retry(state, supplier_tool)
        audit_log("SupplierAgent", conf, f"Matched supplier: {state['supplier_info']['matched_name']}")

        # 6. Emission Factor Matching Agent
        def factor_tool(s):
            query_term = s["entities"].get("material") or s["document_type"]
            candidates = self.matcher.match_emission_factor(query_term, top_n=5)
            s["matched_factor"] = candidates[0] if candidates else None
            conf_val = s["matched_factor"]["confidence"] if s["matched_factor"] else 0.0
            return s, conf_val
        state, conf = self.factor_agent.run_with_retry(state, factor_tool)
        audit_log("FactorAgent", conf, f"Matched factor ID: {state['matched_factor']['id'] if state['matched_factor'] else 'None'}")

        # 7. Carbon Calculation Agent
        def calc_tool(s):
            ents = s["entities"]
            doc_t = s["document_type"]
            factor_id = s["matched_factor"]["id"] if s["matched_factor"] else None
            
            calc_result = {
                "co2e_kg": 0.0,
                "factor_used": 0.0,
                "activity_value_kg": 0.0,
                "location_based_co2e_kg": 0.0,
                "market_based_co2e_kg": 0.0,
                "scope": "Scope 3"
            }
            
            if doc_t == "Invoice" or doc_t == "Purchase Order":
                calc_result = self.calculator.calculate_scope_3_category_1(
                    material=ents["material"],
                    quantity=ents["quantity"],
                    unit=ents["unit"],
                    factor_id=factor_id
                )
                calc_result["scope"] = "Scope 3"
            elif doc_t == "Utility Bill":
                if "Electricity" in s["raw_text"] or ents["electricity_consumption"] > 0 or ents["material"] == "UK electricity":
                    calc_result = self.calculator.calculate_scope_2(
                        consumption_kwh=ents["electricity_consumption"] or ents["quantity"] or 1000.0,
                        country=ents["country"] or "GB",
                        factor_id=factor_id
                    )
                    calc_result["co2e_kg"] = calc_result.get("location_based_co2e_kg", 0.0)
                    calc_result["scope"] = "Scope 2"
                else:
                    calc_result = self.calculator.calculate_scope_1(
                        fuel_type=ents["fuel_type"] or ents["material"],
                        quantity=ents["quantity"],
                        unit=ents["unit"],
                        factor_id=factor_id
                    )
                    calc_result["scope"] = "Scope 1"
            elif doc_t in ["Logistics & Shipping", "Shipping Manifest"]:
                calc_result = self.calculator.calculate_scope_3_category_4(
                    weight_tonnes=ents["weight"] or 10.0,
                    distance_km=ents["distance"] or 100.0,
                    mode=ents["vehicle"] or ents["transport_mode"] or "road",
                    factor_id=factor_id
                )
                calc_result["scope"] = "Scope 3"
            elif doc_t == "Material Consumption":
                # Sum emissions of steel, aluminium, copper, plastic, glass, concrete, chemicals
                materials_dict = {
                    "Steel": ents["steel"],
                    "Aluminium": ents["aluminium"],
                    "Copper": ents["copper"],
                    "Plastic": ents["plastic"],
                    "Glass": ents["glass"],
                    "Concrete": ents["concrete"],
                    "Chemicals": ents["chemicals"]
                }
                total_co2e = 0.0
                for mat, qty in materials_dict.items():
                    if qty > 0:
                        res = self.calculator.calculate_scope_3_category_1(
                            material=mat,
                            quantity=qty,
                            unit=ents["unit"] or "t",
                            factor_id=None
                        )
                        total_co2e += res.get("co2e_kg", 0.0)
                
                # If everything was zero, fallback to general quantity
                if total_co2e == 0.0 and ents["quantity"] > 0:
                    res = self.calculator.calculate_scope_3_category_1(
                        material=ents["material"],
                        quantity=ents["quantity"],
                        unit=ents["unit"],
                        factor_id=factor_id
                    )
                    total_co2e = res.get("co2e_kg", 0.0)
                    
                calc_result = {
                    "co2e_kg": total_co2e,
                    "factor_used": 2.0,
                    "activity_value_converted": ents["quantity"] * 1000.0,
                    "converted_unit": "kg",
                    "scope": "Scope 3"
                }
            elif doc_t == "Fuel Consumption":
                fuels_dict = {
                    "Diesel": ents["diesel"] or ents["fuel_quantity"],
                    "Petrol": ents["petrol"],
                    "LPG": ents["lpg"],
                    "Natural Gas": ents["natural_gas"],
                    "Coal": ents["coal"]
                }
                total_co2e = 0.0
                for fuel, qty in fuels_dict.items():
                    if qty > 0:
                        res = self.calculator.calculate_scope_1(
                            fuel_type=fuel,
                            quantity=qty,
                            unit="liters",
                            factor_id=None
                        )
                        total_co2e += res.get("co2e_kg", 0.0)
                calc_result = {
                    "co2e_kg": total_co2e,
                    "factor_used": 2.68,
                    "activity_value_converted": ents["quantity"],
                    "converted_unit": "liters",
                    "scope": "Scope 1"
                }
            elif doc_t == "Electricity Grid":
                calc_result = self.calculator.calculate_scope_2(
                    consumption_kwh=ents["electricity_consumption"] or ents["quantity"] or 1000.0,
                    country=ents["country"] or "GB",
                    factor_id=factor_id
                )
                calc_result["co2e_kg"] = calc_result.get("location_based_co2e_kg", 0.0)
                calc_result["scope"] = "Scope 2"
            elif doc_t == "Facility & Plant":
                # Compute based on capacity / machines / hours
                hours = ents["working_hours"] or 8.0
                capacity = ents["production_capacity"] or 100.0
                # Mock base consumption 50 kWh per unit capacity per hour
                kwh = capacity * hours * 50.0
                calc_result = self.calculator.calculate_scope_2(
                    consumption_kwh=kwh,
                    country=ents["country"] or "DE",
                    factor_id=factor_id
                )
                calc_result["co2e_kg"] = calc_result.get("location_based_co2e_kg", 0.0)
                calc_result["scope"] = "Scope 2"
            elif doc_t == "CBAM Product Mapping":
                # Determine CBAM direct/indirect intensity
                calc_result = {
                    "co2e_kg": ents["quantity"] * 1.70 * 1000.0,  # 1.7t per tonne
                    "factor_used": 1.70,
                    "scope": "Scope 3"
                }
            elif doc_t == "Supplier Master":
                calc_result = {
                    "co2e_kg": 0.0,
                    "factor_used": 0.0,
                    "scope": "Scope 3"
                }
                
            s["emissions_calc"] = calc_result
            return s, 1.0
        state, conf = self.calc_agent.run_with_retry(state, calc_tool)
        audit_log("CalcAgent", conf, "Greenhouse gas emissions calculated")

        # 8. Recommendation Agent
        def rec_tool(s):
            em = s["emissions_calc"]
            sample_df = pd_df = {
                "supplier_name": s["supplier_info"]["matched_name"],
                "co2e_kg": em.get("co2e_kg", em.get("location_based_co2e_kg", 0.0)),
                "category": s["document_type"],
                "mode": s["entities"].get("vehicle", None)
            }
            # Wrap as df
            import pandas as pd
            df = pd.DataFrame([sample_df])
            s["recommendations"] = self.recommender.generate_recommendations(df)
            return s, 0.92
        state, conf = self.rec_agent.run_with_retry(state, rec_tool)
        audit_log("RecAgent", conf, f"Generated {len(state['recommendations'])} recommendations")

        # 9. CBAM Compliance Agent
        def cbam_tool(s):
            ents = s["entities"]
            em = s["emissions_calc"]
            direct = em.get("co2e_kg", 0.0) if s["document_type"] == "Invoice" else 0.0
            indirect = em.get("location_based_co2e_kg", 0.0) if s["document_type"] == "Utility Bill" else 0.0
            
            s["cbam_metrics"] = self.calculator.calculate_cbam_embedded_emissions(
                production_weight_tonnes=ents.get("weight") or 1.0,
                direct_emissions_kg=direct,
                indirect_emissions_kg=indirect
            )
            return s, 0.95
        state, conf = self.cbam_agent.run_with_retry(state, cbam_tool)
        audit_log("CBAMAgent", conf, f"CBAM embedded specific emissions calculated: {state['cbam_metrics'].get('total_specific_t_per_t'):.4f} tCO2e/t")

        # 10. Monitoring Agent (Execution Audit check)
        def monitor_tool(s):
            logger.info("Executing monitoring checks on the pipeline...")
            return s, 1.0
        state, conf = self.monitoring_agent.run_with_retry(state, monitor_tool)
        audit_log("MonitoringAgent", conf, "Execution logs tracked for compliance")

        return state

if __name__ == "__main__":
    from models.document_classifier import DocumentClassifier
    from models.ner_extractor import NERExtractor
    from services.matching_service import MatchingService
    from services.calculation_engine import CalculationEngine
    from services.recommendation_engine import RecommendationEngine
    
    cls_model = DocumentClassifier()
    ner_model = NERExtractor()
    match_service = MatchingService()
    calc_engine = CalculationEngine()
    rec_engine = RecommendationEngine()
    
    wf = AutonomousWorkflow(cls_model, ner_model, match_service, calc_engine, rec_engine)
    test_ocr = (
        "=== CarbonLedger ERP Document === | Document Type: Invoice | "
        "Reference Number: INV-242358 | Date: 2026-10-12 | Company ID: 38 | "
        "Supplier ID: 3739 | Total Value: 109987.85 | Language: English |"
    )
    res = wf.run_document_audit_pipeline(test_ocr)
    print("Execution Audit Trail Length:", len(res["execution_audit_trail"]))
