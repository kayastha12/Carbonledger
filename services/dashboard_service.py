import json
import sqlite3
import pandas as pd
from typing import List, Dict, Any
from api.database import get_db_connection

class DashboardService:
    """
    Dashboard service for aggregating session metrics, tracking KPIs, and persisting results to database tables.
    """
    def __init__(self):
        pass

    def build_summary(self, 
                      inventory_records: List[Dict[str, Any]], 
                      upload_id: str, 
                      filename: str, 
                      validation_scores: Dict[str, Any], 
                      carbon_price: float) -> Dict[str, Any]:
        """
        Creates centralized KPI totals and persists results.
        """
        total_records_count = len(inventory_records)
        
        scope_1_kg = sum(r["co2e_kg"] for r in inventory_records if r["scope"] == "Scope 1")
        scope_2_kg = sum(r["co2e_kg"] for r in inventory_records if r["scope"] == "Scope 2")
        scope_3_kg = sum(r["co2e_kg"] for r in inventory_records if r["scope"] == "Scope 3")
        total_cbam_cost_eur = sum(r["cbam_cost_eur"] for r in inventory_records)
        total_co2e_kg = round(scope_1_kg + scope_2_kg + scope_3_kg, 2)
        
        matched_factors_count = sum(1 for r in inventory_records if r["calculation_status"] == "Calculated")

        summary = {
            "documents_processed": len(set([r["source_document"] for r in inventory_records])) if inventory_records else 0,
            "rows_extracted": total_records_count,
            "rows_validated": total_records_count,
            "rows_calculated": matched_factors_count,
            "rows_manual_review": total_records_count - matched_factors_count,
            "total_co2e_kg": total_co2e_kg,
            "total_co2e_tonnes": round(total_co2e_kg / 1000.0, 3),
            "total_cbam_cost_eur": round(total_cbam_cost_eur, 2),
            "carbon_price_eur_per_ton": carbon_price,
            "scope_1_co2e_kg": round(scope_1_kg, 2),
            "scope_2_co2e_kg": round(scope_2_kg, 2),
            "scope_3_co2e_kg": round(scope_3_kg, 2),
            "materials_count": len(set([r["material"] for r in inventory_records])) if inventory_records else 0,
            "suppliers_count": len(set([r["supplier"] for r in inventory_records])) if inventory_records else 0,
            "overall_confidence_pct": validation_scores.get("overall_confidence_pct", 0.0)
        }

        # Save session to SQLite database
        self.persist_session(upload_id, filename, total_co2e_kg, total_cbam_cost_eur, validation_scores.get("overall_confidence_pct", 0.0), inventory_records)

        return summary

    def persist_session(self, 
                        upload_id: str, 
                        filename: str, 
                        total_co2e_kg: float, 
                        total_cbam_cost_eur: float, 
                        overall_confidence: float, 
                        inventory_records: List[Dict[str, Any]]):
        """
        Inserts session execution details and row inventories into SQLite databases.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO upload_sessions 
            (upload_id, filename, pages_count, tables_count, total_co2e_kg, total_cbam_cost_eur, overall_confidence_pct, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (upload_id, filename, 1, 1, total_co2e_kg, total_cbam_cost_eur, overall_confidence, pd.Timestamp.now().isoformat()))
            
            for inv_r in inventory_records:
                cursor.execute("""
                INSERT INTO calculation_results
                (upload_id, material, supplier, quantity, unit, matched_material, factor_id, factor_source, scope, emission_factor, co2_kg, ch4_kg, n2o_kg, co2e_kg, cbam_cost_eur, calculation_status, formula, trace_json, is_anomaly, anomaly_reason, is_duplicate, ocr_error, recommendations_json, po_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    upload_id, inv_r["material"], inv_r["supplier"], inv_r["quantity"], inv_r["unit"],
                    inv_r["matched_material"], inv_r["factor_id"], inv_r["factor_source"], inv_r["scope"],
                    inv_r["emission_factor"], inv_r["co2_kg"], inv_r["ch4_kg"], inv_r["n2o_kg"], inv_r["co2e_kg"],
                    inv_r["cbam_cost_eur"], inv_r["calculation_status"], inv_r["formula"], json.dumps(inv_r["calculation_trace"]),
                    inv_r.get("is_anomaly", 0), inv_r.get("anomaly_reason", ""), inv_r.get("is_duplicate", 0), inv_r.get("ocr_error", 0), json.dumps(inv_r.get("recommendations", [])),
                    inv_r.get("po_number")
                ))
            conn.commit()
            conn.close()
        except Exception as e:
            print("DB Save Warning:", e)
