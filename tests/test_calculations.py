import unittest
from services.calculation_engine import CalculationEngine

class TestCarbonCalculations(unittest.TestCase):
    def setUp(self):
        self.engine = CalculationEngine()

    def test_unit_conversions(self):
        # 1 tonne should convert to 1000 kg
        self.assertAlmostEqual(self.engine.convert_units(1.0, "t", "kg"), 1000.0)
        # 1000 kg should convert to 1 tonne
        self.assertAlmostEqual(self.engine.convert_units(1000.0, "kg", "t"), 1.0)
        # 1 liter should convert to 0.001 cubic meters
        self.assertAlmostEqual(self.engine.convert_units(1.0, "liters", "cubic meters"), 0.001)

    def test_scope_1_calculation(self):
        res = self.engine.calculate_scope_1("Diesel", 100.0, "liters")
        self.assertGreater(res["co2e_kg"], 0)
        self.assertAlmostEqual(res["ch4_kg"], res["co2e_kg"] * 0.0008, places=3)
        self.assertAlmostEqual(res["n2o_kg"], res["co2e_kg"] * 0.0022, places=3)

    def test_scope_2_calculation(self):
        res = self.engine.calculate_scope_2(2000.0, "UK")
        self.assertGreater(res["location_based_co2e_kg"], 0)
        self.assertGreater(res["market_based_co2e_kg"], 0)

    def test_scope_3_category_1_calculation(self):
        res = self.engine.calculate_scope_3_category_1("Steel", 500.0, "kg")
        self.assertGreater(res["co2e_kg"], 0)

    def test_scope_3_category_4_calculation(self):
        res = self.engine.calculate_scope_3_category_4(10.0, 500.0, "road")
        self.assertGreater(res["co2e_kg"], 0)
        self.assertGreater(res["factor_used"], 0)

    def test_cbam_calculations(self):
        res = self.engine.calculate_cbam_embedded_emissions(10.0, 20000.0, 5000.0)
        self.assertAlmostEqual(res["specific_direct_t_per_t"], 2.0)
        self.assertAlmostEqual(res["specific_indirect_t_per_t"], 0.5)
        self.assertAlmostEqual(res["total_specific_t_per_t"], 2.5)

if __name__ == "__main__":
    unittest.main()
