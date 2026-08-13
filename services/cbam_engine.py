import os
import sqlite3
from typing import Optional
from api.database import get_db_connection

class CBAMEngine:
    """
    Computes CBAM financial exposure by applying carbon price values from setting tables to embedded emissions.
    """
    def __init__(self, default_price: float = 85.0):
        self.default_price = default_price

    def get_carbon_price(self) -> float:
        """
        Retrieves current carbon price configuration from SQLite app settings.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM app_settings WHERE key = 'carbon_price_eur_per_ton'")
            row = cursor.fetchone()
            conn.close()
            if row:
                return float(row["value"])
        except Exception:
            pass
        return self.default_price

    def calculate_cbam_cost(self, co2e_kg: float, carbon_price: Optional[float] = None) -> float:
        """
        CBAM Cost (€) = Embedded CO2e (tonnes) * Carbon Price (€/t)
        """
        if carbon_price is None:
            carbon_price = self.get_carbon_price()
        co2e_tonnes = co2e_kg / 1000.0
        return round(co2e_tonnes * carbon_price, 2)
