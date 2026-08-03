import unittest
from services.demo_data_loader import DemoDataLoader

class TestPhase5DemoSystem(unittest.TestCase):
    def test_demo_organization_data(self):
        org = DemoDataLoader.load_demo_organization()
        self.assertEqual(org["name"], "EcoSteel Europe")
        self.assertEqual(org["eori"], "EU882312091")

    def test_demo_suppliers_generation(self):
        sups = DemoDataLoader.generate_demo_suppliers()
        self.assertEqual(len(sups), 50)
        self.assertEqual(sups[0]["id"], 1)
        self.assertIn("kg", sups[0]["historical_emissions"])

    def test_demo_invoices_generation(self):
        invs = DemoDataLoader.generate_demo_invoices()
        self.assertEqual(len(invs), 500)
        self.assertIn("INV-2026-", invs[0]["number"])

if __name__ == "__main__":
    unittest.main()
