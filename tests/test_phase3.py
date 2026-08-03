import unittest
import os
import pandas as pd
from models.document_classifier import DocumentClassifier
from models.ner_extractor import NERExtractor
from services.matching_service import MatchingService
from services.calculation_engine import CalculationEngine
from services.recommendation_engine import RecommendationEngine

# Phase 3 Components
from services.autonomous_agents import AutonomousWorkflow
from services.erp_connectors import ERPConnectorService
from services.report_generator import ReportGenerator
from services.notification_engine import NotificationEngine
from services.governance import GovernanceService
from services.active_learning import ActiveLearningService

class TestPhase3Platform(unittest.TestCase):
    def setUp(self):
        cls_model = DocumentClassifier()
        ner_model = NERExtractor()
        match_service = MatchingService()
        calc_engine = CalculationEngine()
        rec_engine = RecommendationEngine()
        
        self.wf = AutonomousWorkflow(cls_model, ner_model, match_service, calc_engine, rec_engine)
        self.erp = ERPConnectorService(self.wf)
        self.rep = ReportGenerator()
        self.notif = NotificationEngine()
        self.gov = GovernanceService()
        self.al = ActiveLearningService()

    def test_multi_agent_pipeline_execution(self):
        test_ocr = (
            "=== CarbonLedger ERP Document === | Document Type: Invoice | "
            "Reference Number: INV-9812 | Date: 2026-10-12 | Company ID: 38 | "
            "Supplier ID: 3739 | Total Value: 50000 | Language: English |"
        )
        state = self.wf.run_document_audit_pipeline(test_ocr)
        self.assertEqual(state["document_type"], "Invoice")
        self.assertGreater(len(state["execution_audit_trail"]), 0)
        self.assertIn("emissions_calc", state)
        self.assertIn("recommendations", state)

    def test_erp_sync_sap(self):
        res = self.erp.sync_sap_s4hana({})
        self.assertGreater(len(res), 0)
        self.assertEqual(res[0]["document_type"], "Invoice")

    def test_report_generation(self):
        summary = {
            "scope_1_co2e_kg": 1000,
            "scope_2_location_co2e_kg": 3000,
            "scope_3_co2e_kg": 15000
        }
        cbam = {
            "specific_direct_t_per_t": 0.8,
            "specific_indirect_t_per_t": 0.2,
            "total_specific_t_per_t": 1.0
        }
        j, ex = self.rep.generate_corporate_inventory(summary)
        tx = self.rep.generate_executive_esg_report(summary, cbam)
        
        self.assertTrue(os.path.exists(j))
        self.assertTrue(os.path.exists(ex))
        self.assertTrue(os.path.exists(tx))

    def test_notification_engine(self):
        res = self.notif.trigger_notifications("calculation_failed", "Calculations for invoice DYN-901 timed out.")
        self.assertEqual(res["status"], "success")

    def test_rbac_governance(self):
        # Admin must have all access
        self.assertTrue(self.gov.verify_role_access("Company Administrator", "submit_report", "tenant_1"))
        # Procurement must not be allowed to submit report
        self.assertFalse(self.gov.verify_role_access("Procurement Team", "submit_report", "tenant_1"))

    def test_active_learning_feedback(self):
        res = self.al.log_feedback("INV-98", "Utility Bill", "Invoice", "document_class")
        self.assertEqual(res["status"], "success")

if __name__ == "__main__":
    unittest.main()
