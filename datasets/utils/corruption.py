import random
import string
import pandas as pd
import numpy as np

def inject_corruption(df, corruption_rate, table_name):
    """Corrupts a dataframe's columns based on a configurable corruption rate and table type."""
    if corruption_rate <= 0 or len(df) == 0:
        return df

    # Work on a copy of the dataframe to avoid modifications in-place
    df_corrupt = df.copy()
    num_rows = len(df_corrupt)
    num_to_corrupt = int(num_rows * corruption_rate)
    
    if num_to_corrupt == 0:
        return df_corrupt

    # Select random indices to corrupt
    corrupt_indices = np.random.choice(df_corrupt.index, size=num_to_corrupt, replace=False)

    if table_name == "invoices":
        # 1. Duplicate Invoices or Invoice Numbers
        # 2. Negative GrandTotal
        for idx in corrupt_indices[:num_to_corrupt // 2]:
            if "InvoiceNumber" in df_corrupt.columns:
                df_corrupt.loc[idx, "InvoiceNumber"] = df_corrupt.loc[idx, "InvoiceNumber"] + "_DUP"
        for idx in corrupt_indices[num_to_corrupt // 2:]:
            if "GrandTotal" in df_corrupt.columns:
                df_corrupt.loc[idx, "GrandTotal"] = -abs(df_corrupt.loc[idx, "GrandTotal"])
            if "Subtotal" in df_corrupt.columns:
                df_corrupt.loc[idx, "Subtotal"] = -abs(df_corrupt.loc[idx, "Subtotal"])

    elif table_name == "purchase_orders":
        # 1. Invalid Dates (Expected Delivery prior to PO Date)
        # 2. Missing status
        for idx in corrupt_indices[:num_to_corrupt // 2]:
            if "ExpectedDelivery" in df_corrupt.columns and "PODate" in df_corrupt.columns:
                po_date = df_corrupt.loc[idx, "PODate"]
                if isinstance(po_date, str):
                    po_dt = pd.to_datetime(po_date)
                    df_corrupt.loc[idx, "ExpectedDelivery"] = (po_dt - pd.Timedelta(days=random.randint(5, 30))).strftime("%Y-%m-%d")
                else:
                    df_corrupt.loc[idx, "ExpectedDelivery"] = po_date - pd.Timedelta(days=random.randint(5, 30))
        for idx in corrupt_indices[num_to_corrupt // 2:]:
            if "Status" in df_corrupt.columns:
                df_corrupt.loc[idx, "Status"] = None

    elif table_name == "suppliers" or table_name == "companies" or table_name == "customers":
        # 1. Malformed GST numbers
        # 2. Typographical errors in Country/State
        for idx in corrupt_indices:
            cols = [c for c in ["GSTNumber", "GST", "Country"] if c in df_corrupt.columns]
            if cols:
                col_to_corrupt = random.choice(cols)
                val = df_corrupt.loc[idx, col_to_corrupt]
                if val and isinstance(val, str):
                    if "GST" in col_to_corrupt:
                        df_corrupt.loc[idx, col_to_corrupt] = "INVALID_GST_1234"
                    elif col_to_corrupt == "Country":
                        df_corrupt.loc[idx, col_to_corrupt] = val + "x" # Typo (e.g. Germanyx)

    elif table_name == "purchase_order_items" or table_name == "manufacturing_orders":
        # 1. Negative quantity
        # 2. Zero price
        # 3. Unit mismatch
        for idx in corrupt_indices[:num_to_corrupt // 2]:
            if "Quantity" in df_corrupt.columns:
                df_corrupt.loc[idx, "Quantity"] = -abs(df_corrupt.loc[idx, "Quantity"])
            elif "QuantityProduced" in df_corrupt.columns:
                df_corrupt.loc[idx, "QuantityProduced"] = -abs(df_corrupt.loc[idx, "QuantityProduced"])
        for idx in corrupt_indices[num_to_corrupt // 2:]:
            if "Unit" in df_corrupt.columns:
                df_corrupt.loc[idx, "Unit"] = "InvalidUnit"
            if "UnitPrice" in df_corrupt.columns:
                df_corrupt.loc[idx, "UnitPrice"] = 0.0

    elif table_name in ["electricity_bills", "fuel_logs", "water_bills", "waste_logs"]:
        # 1. Outlier emission values (carbon values mismatched, negative values, etc.)
        for idx in corrupt_indices:
            cols = [c for c in ["CO2Emission", "CO2eEmission", "CO2e", "ConsumptionKWh", "FuelVolume"] if c in df_corrupt.columns]
            if cols:
                col = random.choice(cols)
                val = df_corrupt.loc[idx, col]
                if val is not None:
                    # Inject negative value or extreme multiplier
                    df_corrupt.loc[idx, col] = val * -2.0 if random.random() < 0.5 else val * 100.0

    return df_corrupt
