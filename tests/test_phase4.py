import unittest
import json

from services.saas_billing import SaasBillingService
from services.copilot_engine import CopilotEngine
from services.mcp_ecosystem import MCPEcosystemService

from models.document_classifier import DocumentClassifier
from models.ner_extractor import NERExtractor
from services.matching_service import MatchingService
from services.calculation_engine import CalculationEngine
from services.recommendation_engine import RecommendationEngine

class TestPhase4SaaSAndMCP(unittest.TestCase):
    def setUp(self):
        self.billing = SaasBillingService()
        self.copilot = CopilotEngine()
        
        # Instantiate dependencies for MCP testing
        matcher = MatchingService()
        calculator = CalculationEngine()
        recommender = RecommendationEngine()
        self.mcp = MCPEcosystemService(matcher, calculator, recommender, None)

    def test_saas_plan_limitations(self):
        # Default Free Plan starts with 4 uploads, allowed max is 5
        ok1, msg1 = self.billing.track_usage("tenant_default")
        self.assertTrue(ok1)
        
        # 5th upload reached. 6th should fail.
        ok2, msg2 = self.billing.track_usage("tenant_default")
        self.assertFalse(ok2)
        self.assertIn("limit exceeded", msg2)

    def test_stripe_webhook_parsing(self):
        payload = {
            "type": "invoice.paid",
            "data": {
                "object": {
                    "customer_email": "billing@ecosteel.com"
                }
            }
        }
        res = self.billing.process_stripe_webhook("invoice.paid", payload)
        self.assertEqual(res["status"], "billing_renewed")
        self.assertEqual(res["email"], "billing@ecosteel.com")

    def test_compliance_reports(self):
        summary = {"scope_1_co2e_kg": 2000, "scope_2_location_co2e_kg": 5000, "scope_3_co2e_kg": 15000}
        sec_report = self.copilot.generate_sec_climate_disclosure("EcoCorp", summary)
        self.assertIn("REGULATION S-K", sec_report)
        self.assertIn("Scope 1 (Direct Emissions)", sec_report)
        
        csrd_report = self.copilot.generate_csrd_report("EcoCorp", summary)
        self.assertIn("ESRS E1 Climate Change", csrd_report)

    def test_mcp_tool_routing(self):
        # List tools
        tools = self.mcp.list_tools()
        self.assertEqual(len(tools), 3)
        self.assertEqual(tools[0]["name"], "lookup_emission_factor")
        
        # Call tool calculation
        args = {"material": "Steel", "quantity": 10, "unit": "t"}
        res = self.mcp.call_tool("calculate_scope_3", args)
        self.assertIn("content", res)
        # Parse output
        output_txt = res["content"][0]["text"]
        output_data = json.loads(output_txt)
        self.assertIn("co2e_kg", output_data)

if __name__ == "__main__":
    unittest.main()
