import os
import pandas as pd
import json

def clean_and_build_master(excel_path, output_csv_path, output_json_path):
    print(f"Reading Excel workbook from: {excel_path}")
    xl = pd.ExcelFile(excel_path)
    
    master_records = []
    
    # We will read 'All Factors (Flat)' as our primary source, as it represents the unified set
    if "All Factors (Flat)" in xl.sheet_names:
        df_flat = xl.parse("All Factors (Flat)")
        # Standardize columns
        df_flat.columns = [c.strip() for c in df_flat.columns]
        
        # Mapping columns to standardized keys
        for idx, row in df_flat.iterrows():
            record = {
                "id": str(row.get("ID", "")).strip(),
                "scope": str(row.get("Scope", "")).strip(),
                "category": str(row.get("Level 1", "")).strip(),
                "subcategory": str(row.get("Level 2", "")).strip(),
                "activity": str(row.get("Level 3", "")).strip(),
                "detail": str(row.get("Level 4", "")).strip(),
                "text": str(row.get("Column Text", "")).strip(),
                "uom": str(row.get("UOM", "")).strip(),
                "ghg_unit": str(row.get("GHG/Unit", "")).strip(),
                "factor": float(row.get("Conversion Factor", 0.0)) if pd.notnull(row.get("Conversion Factor")) else 0.0,
                "source_sheet": "All Factors (Flat)",
                "factor_version": "2026.1"
            }
            master_records.append(record)
    else:
        print("Warning: 'All Factors (Flat)' sheet not found! Parsing sheet-by-sheet...")
        
    # Read sheet specific data to get WTT and other properties or to verify coverage
    for sheet in xl.sheet_names:
        if sheet in ["Index", "All Factors (Flat)", "Fuel Properties", "Unit Conversions", "Haul Definitions"]:
            continue
        
        df = xl.parse(sheet)
        df.columns = [c.strip() for c in df.columns]
        
        for idx, row in df.iterrows():
            record_id = str(row.get("ID", f"{sheet}_{idx}")).strip()
            # Avoid duplicating what we already have from All Factors (Flat)
            if any(r["id"] == record_id for r in master_records):
                continue
                
            record = {
                "id": record_id,
                "scope": str(row.get("Scope", "Scope 3" if "WTT" in sheet else "Scope 1")).strip(),
                "category": sheet,
                "subcategory": str(row.get("Level 2", "")).strip(),
                "activity": str(row.get("Level 3", "")).strip(),
                "detail": str(row.get("Level 4", "")).strip(),
                "text": str(row.get("Column Text", "")).strip(),
                "uom": str(row.get("UOM", "")).strip(),
                "ghg_unit": str(row.get("GHG/Unit", "kg CO2e")).strip(),
                "factor": float(row.get("Conversion Factor", 0.0)) if pd.notnull(row.get("Conversion Factor")) else 0.0,
                "source_sheet": sheet,
                "factor_version": "2026.1"
            }
            master_records.append(record)
            
    # Normalize units
    for r in master_records:
        r["uom"] = r["uom"].lower().replace("litres", "liters").replace("tonnes", "t").replace("kilograms", "kg")
        
    df_master = pd.DataFrame(master_records)
    
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    df_master.to_csv(output_csv_path, index=False)
    
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(master_records, f, indent=2)
        
    print(f"Master factors saved: {len(master_records)} records written.")
    return df_master

if __name__ == "__main__":
    excel = r"d:\internship\carbonledger\datasets/CarbonLedger_GHG_Factors_2026_Clean.xlsx"
    out_csv = r"d:\internship\carbonledger\preprocessing\master_factors_cleaned.csv"
    out_json = r"d:\internship\carbonledger\preprocessing\master_factors_cleaned.json"
    clean_and_build_master(excel, out_csv, out_json)
