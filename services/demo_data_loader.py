import random

class DemoDataLoader:
    @staticmethod
    def load_demo_organization():
        return {
            "name": "EcoSteel Europe",
            "importer": "EcoSteel GmbH (Germany)",
            "exporter": "SteelCorp India (Mumbai Plant)",
            "eori": "EU882312091"
        }

    @staticmethod
    def generate_demo_suppliers():
        suppliers = []
        countries = ["DE", "IN", "CN", "PL", "FR", "US", "ZA", "GB"]
        for i in range(1, 51):
            country = random.choice(countries)
            rating = round(random.uniform(2.0, 5.0), 1)
            risk = "High" if rating < 3.0 else "Medium" if rating < 4.0 else "Low"
            suppliers.append({
                "id": i,
                "name": f"Supplier_{i}",
                "country": country,
                "rating": f"{rating}/5.0",
                "risk_score": f"{round((6.0 - rating) * 16.0, 1)} ({risk})",
                "historical_emissions": f"{random.randint(10000, 500000):,} kg"
            })
        return suppliers

    @staticmethod
    def generate_demo_invoices():
        invoices = []
        materials = ["Steel Sheets", "Cement Blend", "Iron Bars", "Aluminium Ingot", "Electricity", "HGV Freight"]
        status_options = ["Calculated", "Audited"]
        
        for i in range(1, 501):
            mat = random.choice(materials)
            qty = random.randint(10, 200)
            unit = "t" if mat not in ["Electricity", "HGV Freight"] else "kWh" if mat == "Electricity" else "km"
            co2 = qty * (2.85 if unit == "t" else 0.45 if unit == "kWh" else 0.15)
            
            invoices.append({
                "number": f"INV-2026-{100 + i}",
                "supplier": f"Supplier_{random.randint(1, 50)}",
                "material": mat,
                "qty": f"{qty} {unit}",
                "status": random.choice(status_options),
                "co2e": f"{round(co2, 1):,} kg"
            })
        return invoices

if __name__ == "__main__":
    loader = DemoDataLoader()
    sups = loader.generate_demo_suppliers()
    invs = loader.generate_demo_invoices()
    print(f"Generated {len(sups)} demo suppliers and {len(invs)} demo invoices successfully.")
