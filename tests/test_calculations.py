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
        # Diesel factor matched from database: 2.58354 kg CO2e / liter
        res = self.engine.calculate_scope_1("Diesel", 100.0, "liters")
        self.assertAlmostEqual(res["co2e_kg"], 258.354, places=3)
        self.assertAlmostEqual(res["ch4_kg"], 258.354 * 0.0008, places=3)
        self.assertAlmostEqual(res["n2o_kg"], 258.354 * 0.0022, places=3)

    def test_scope_2_calculation(self):
        # 2000 kWh of grid electricity in Germany (DE factor matched from database = 0.13096)
        res = self.engine.calculate_scope_2(2000.0, "DE")
        self.assertAlmostEqual(res["location_based_co2e_kg"], 261.92, places=2)
        # Market-based fallback residual mix/grid factor
        self.assertAlmostEqual(res["market_based_co2e_kg"], 261.92, places=2)

    def test_scope_3_category_1_calculation(self):
        # Material purchase: 500 kg steel (factor matched from database = 2861.58251 kg CO2e / t)
        # 500 kg converted to tonnes = 0.5 t -> 0.5 * 2861.58251 = 1430.791255 kg CO2e
        res = self.engine.calculate_scope_3_category_1("Steel", 500.0, "kg")
        self.assertAlmostEqual(res["co2e_kg"], 1430.791255, places=3)

    def test_scope_3_category_4_calculation(self):
        # Transport: 10 tonnes over 500 km by Road (matched factor from database for HGV/road = 0.39508 kg CO2e / tonne.km)
        # 10 * 500 * 0.39508 = 1975.40 kg CO2e
        res = self.engine.calculate_scope_3_category_4(10.0, 500.0, "road")
        self.assertAlmostEqual(res["co2e_kg"], 1975.40, places=2)

    def test_cbam_calculations(self):
        # Product weight = 10 tonnes, direct emissions = 20000 kg, indirect = 5000 kg
        res = self.engine.calculate_cbam_embedded_emissions(10.0, 20000.0, 5000.0)
        # specific direct = (20000/1000) / 10 = 2.0 tCO2e/t
        self.assertAlmostEqual(res["specific_direct_t_per_t"], 2.0)
        # specific indirect = (5000/1000) / 10 = 0.5 tCO2e/t
        self.assertAlmostEqual(res["specific_indirect_t_per_t"], 0.5)
        self.assertAlmostEqual(res["total_specific_t_per_t"], 2.5)

if __name__ == "__main__":
    unittest.main()
