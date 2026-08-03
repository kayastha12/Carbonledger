import unittest

from services.compliance_engine import ComplianceEngine
from services.digital_twin import SupplyChainDigitalTwin
from services.predictive_analytics import PredictiveAnalyticsService

class TestPhase6EnterpriseFeatures(unittest.TestCase):
    def setUp(self):
        self.compliance = ComplianceEngine()
        self.twin = SupplyChainDigitalTwin()
        self.predictor = PredictiveAnalyticsService()

    def test_compliance_auditing(self):
        # Mapped SEC requirements are: ["scope_1_direct", "scope_2_indirect", "governance_oversight"]
        mock_inputs = {
            "scope_1_direct": 4000.0,
            "scope_2_indirect": 12000.0,
            "governance_oversight": "Board oversight committee established"
        }
        res = self.compliance.audit_compliance("SEC", mock_inputs)
        self.assertEqual(res["compliance_score_pct"], 100.0)
        self.assertEqual(res["status"], "Compliant")
        
        # Missing field
        mock_incomplete = {
            "scope_1_direct": 4000.0
        }
        res2 = self.compliance.audit_compliance("SEC", mock_incomplete)
        self.assertEqual(res2["compliance_score_pct"], 33.33)
        self.assertEqual(res2["status"], "Non-Compliant")

    def test_digital_twin_graph(self):
        graph = self.twin.get_digital_twin_model()
        self.assertEqual(graph["organization"], "EcoSteel Europe")
        self.assertGreater(len(graph["nodes"]), 0)
        self.assertEqual(graph["nodes"][0]["id"], "plant_mumbai")

    def test_what_if_predictive_simulations(self):
        res = self.predictor.run_what_if_scenario("rail_freight")
        # Rail freight reduction is 75%
        self.assertEqual(res["co2_reduction_pct"], 75.0)
        self.assertGreater(res["tariff_savings_euro"], 0.0)
        self.assertGreater(res["estimated_annual_roi_pct"], 0.0)

if __name__ == "__main__":
    unittest.main()
