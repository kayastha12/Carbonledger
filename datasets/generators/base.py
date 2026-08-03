import os
import hashlib
from datetime import datetime
import pandas as pd
import polars as pl
from utils.corruption import inject_corruption

class BaseGenerator:
    def __init__(self, config, settings, batch_id="BATCH-001", version="1.0.0"):
        self.config = config
        self.settings = settings
        self.batch_id = batch_id
        self.version = version
        self.seed = config.get("seed", 42)
        
    def add_lineage_and_audit(self, df, table_name, pk_col):
        """Appends standard auditing and data lineage columns to a pandas DataFrame."""
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        df["CreatedDate"] = now
        df["UpdatedDate"] = now
        df["Status"] = "Active"
        
        # Add Data Lineage
        df["BatchID"] = self.batch_id
        df["GeneratorVersion"] = self.version
        df["CreatedByGenerator"] = f"Generator_{table_name}"
        df["GenerationTimestamp"] = now
        df["Source"] = "Synthetic_ERP"
        
        # Generate row-level checksum based on primary key and timestamp
        df["Checksum"] = df[pk_col].apply(
            lambda x: hashlib.md5(f"{table_name}_{x}_{now}".encode()).hexdigest()
        )
        return df

    def save_data(self, df, output_dir, table_name, is_master=True, pk_col="ID"):
        """Exports the DataFrame to CSV and Parquet after optionally injecting corruption."""
        # Add lineage and audit
        df = self.add_lineage_and_audit(df, table_name, pk_col)
        
        # Inject corruption if it is a transactional table and corruption rate is configured
        if not is_master:
            corruption_rate = self.config.get("corruption_rate", 0.02)
            df = inject_corruption(df, corruption_rate, table_name)
            
        # Determine paths
        subfolder = "master" if is_master else "transactional"
        target_dir = os.path.join(output_dir, subfolder)
        os.makedirs(target_dir, exist_ok=True)
        
        formats = self.config.get("output_formats", ["csv"])
        
        # Export
        if "csv" in formats:
            csv_path = os.path.join(target_dir, f"{table_name}.csv")
            df.to_csv(csv_path, index=False, encoding="utf-8")
            
        if "parquet" in formats:
            parquet_path = os.path.join(target_dir, f"{table_name}.parquet")
            df.to_parquet(parquet_path, index=False)
            
        if "json" in formats:
            json_path = os.path.join(target_dir, f"{table_name}.json")
            df.to_json(json_path, orient="records", date_format="iso", indent=2)

        return len(df)
