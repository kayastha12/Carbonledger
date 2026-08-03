import unittest
import os
import torch
import pandas as pd
from models.document_classifier import DocumentClassifier
from models.ner_extractor import NERExtractor
from models.supplier_risk_model import SupplierRiskModel
from services.recommendation_engine import RecommendationEngine
from services.rag_service import RAGService

class TestPhase2Models(unittest.TestCase):
    def setUp(self):
        self.device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')

    def test_document_classifier_inference(self):
        classifier = DocumentClassifier()
        sample = "INVOICE #INV-12345. Supplier: SteelCorp. Item: Steel Sheet. Total: 500 EUR."
        res = classifier.classify(sample)
        self.assertIn(res, ["Invoice", "Purchase Order", "Shipping Manifest", "Utility Bill", "Other"])

    def test_ner_extractor_inference(self):
        extractor = NERExtractor()
        sample = "=== CarbonLedger ERP Document === | Document Type: Invoice | Reference Number: INV-999 | Supplier ID: 888 | Total Value: 5000 |"
        res = extractor.extract(sample)
        self.assertEqual(res["invoice_number"], "INV-999")
        self.assertEqual(res["cost"], 5000.0)

    def test_supplier_risk_model(self):
        risk_model = SupplierRiskModel()
        # Test similarity
        sim = risk_model.find_supplier_similarity("SteelCorp Inc", "SteelCorp Corporation")
        self.assertGreater(sim["confidence_score"], 0.0)
        self.assertIn("is_duplicate", sim)
        
        # Test risk
        risk = risk_model.calculate_risk_score("Supplier_1")
        self.assertIn("risk_score", risk)
        self.assertIn("emission_risk", risk)

    def test_recommendation_engine(self):
        recommender = RecommendationEngine()
        mock_df = pd.DataFrame([
            {"supplier_name": "Supplier_1", "co2e_kg": 15000.0, "category": "Invoice", "mode": None}
        ])
        recs = recommender.generate_recommendations(mock_df)
        self.assertGreater(len(recs), 0)
        self.assertIn("expected_roi_pct", recs[0])
        self.assertIn("expected_co2_reduction_pct", recs[0])

    def test_rag_hybrid_query(self):
        rag = RAGService()
        res = rag.query("What is the OCR accuracy?", tenant_id="tenant_abc")
        self.assertIn("response", res)
        self.assertIn("citations", res)

if __name__ == "__main__":
    unittest.main()
