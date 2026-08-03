class ComplianceEngine:
    def __init__(self):
        self.rules = {
            "SEC": ["scope_1_direct", "scope_2_indirect", "governance_oversight"],
            "CSRD": ["scope_1_direct", "scope_2_indirect", "scope_3_supply_chain", "net_zero_targets", "double_materiality"],
            "ISO 14064": ["greenhouse_gas_inventory", "quantification_methodology", "data_uncertainty_assessment"],
            "GRI": ["esg_governance_board", "material_topics_index", "direct_emissions_reporting"]
        }

    def audit_compliance(self, framework_name, input_data):
        """
        Validates the current carbon metrics against a target framework's checklist.
        """
        requirements = self.rules.get(framework_name.upper(), [])
        if not requirements:
            return {"status": "unsupported_framework", "score": 0.0}
            
        checklist = {}
        passed_count = 0
        
        for req in requirements:
            val = input_data.get(req)
            # Requirements are passed if data is present and non-zero/non-empty
            passed = val is not None and val != 0.0 and val != ""
            checklist[req] = "PASSED" if passed else "MISSING"
            if passed:
                passed_count += 1
                
        score = (passed_count / len(requirements)) * 100.0 if requirements else 0.0
        
        return {
            "framework": framework_name,
            "compliance_score_pct": round(score, 2),
            "checklist": checklist,
            "status": "Compliant" if score == 100.0 else "Non-Compliant",
            "ai_recommendations": [
                f"Please provide '{req.replace('_', ' ')}' values to achieve 100% compliance."
                for req, status in checklist.items() if status == "MISSING"
              ] or ["All requirements satisfied. Document is ready for ESG filing."]
        }

if __name__ == "__main__":
    engine = ComplianceEngine()
    mock_data = {
        "scope_1_direct": 5000,
        "scope_2_indirect": 12000,
        "governance_oversight": "Board committee appointed"
    }
    res = engine.audit_compliance("SEC", mock_data)
    import json
    print(json.dumps(res, indent=2))
