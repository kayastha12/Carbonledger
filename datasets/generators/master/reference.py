import os
import pandas as pd
from generators.base import BaseGenerator

class ReferenceGenerator(BaseGenerator):
    def generate(self, output_dir):
        # 1. Countries
        countries_data = []
        for c, details in self.settings.GEOGRAPHY_MAPPING.items():
            countries_data.append({
                "CountryID": len(countries_data) + 1,
                "CountryName": c,
                "Currency": details["currency"],
                "TaxLabel": details["tax_label"]
            })
        countries_df = pd.DataFrame(countries_data)
        self.save_data(countries_df, output_dir, "countries", is_master=True, pk_col="CountryID")

        # 2. Cities
        cities_data = []
        for c, details in self.settings.GEOGRAPHY_MAPPING.items():
            for city in details["cities"]:
                cities_data.append({
                    "CityID": len(cities_data) + 1,
                    "CityName": city,
                    "CountryName": c
                })
        cities_df = pd.DataFrame(cities_data)
        self.save_data(cities_df, output_dir, "cities", is_master=True, pk_col="CityID")

        # 3. Ports
        ports_data = []
        for c, details in self.settings.GEOGRAPHY_MAPPING.items():
            for port in details["ports"]:
                ports_data.append({
                    "PortID": len(ports_data) + 1,
                    "PortName": port,
                    "CountryName": c
                })
        ports_df = pd.DataFrame(ports_data)
        self.save_data(ports_df, output_dir, "ports", is_master=True, pk_col="PortID")

        # 4. Transport Modes
        modes = ["Ocean", "Rail", "Road", "Air"]
        modes_df = pd.DataFrame([{"TransportModeID": i + 1, "ModeName": m} for i, m in enumerate(modes)])
        self.save_data(modes_df, output_dir, "transport_modes", is_master=True, pk_col="TransportModeID")

        # 5. Currencies
        currencies = ["USD", "EUR", "INR", "JPY", "CNY"]
        currencies_df = pd.DataFrame([{"CurrencyID": i + 1, "CurrencyCode": c} for i, c in enumerate(currencies)])
        self.save_data(currencies_df, output_dir, "currencies", is_master=True, pk_col="CurrencyID")

        # 6. Material Categories
        mat_cats = list(self.settings.EMISSION_FACTORS["material"].keys())
        mat_cats_df = pd.DataFrame([{"MaterialCategoryID": i + 1, "CategoryName": c} for i, c in enumerate(mat_cats)])
        self.save_data(mat_cats_df, output_dir, "material_categories", is_master=True, pk_col="MaterialCategoryID")

        # 7. Emission Factors
        factors_data = []
        factor_idx = 1
        for cat, activities in self.settings.EMISSION_FACTORS.items():
            for act, gases in activities.items():
                factors_data.append({
                    "FactorID": factor_idx,
                    "Category": cat,
                    "Activity": act,
                    "CO2": gases.get("CO2", 0.0),
                    "CH4": gases.get("CH4", 0.0),
                    "N2O": gases.get("N2O", 0.0),
                    "CO2e": gases.get("CO2e", 0.0)
                })
                factor_idx += 1
        factors_df = pd.DataFrame(factors_data)
        self.save_data(factors_df, output_dir, "emission_factors", is_master=True, pk_col="FactorID")

        print("Master Reference Datasets Generated successfully.")
