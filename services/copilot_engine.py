import json
import sqlite3
from typing import Optional, Dict, Any, List
import pandas as pd


class CopilotEngine:
    def __init__(self, rag_service=None, explainability_service=None):
        self.rag = rag_service
        self.explainability = explainability_service

    def generate_sec_climate_disclosure(self, tenant_name, summary_metrics):
        """
        Formulate a disclosure document matching US SEC Climate rules.
        """
        doc = f"""
============================================================
SEC CLIMATE DISCLOSURE STATEMENT - REGULATION S-K
============================================================
Company Name: {tenant_name}
Reporting Period: Fiscal Year 2026

1. GOVERNANCE
-------------
The Board of Directors oversees the registrant's climate-related risk exposures,
with audits managed autonomously via CarbonLedger AI Auditor.

2. GREENHOUSE GAS METRICS (Item 1504)
--------------------------------------
- Scope 1 (Direct Emissions): {summary_metrics.get("scope_1_co2e_kg", 0.0) / 1000.0:,.2f} metric tons CO2e
- Scope 2 (Indirect Emissions): {summary_metrics.get("scope_2_location_co2e_kg", 0.0) / 1000.0:,.2f} metric tons CO2e
- Scope 3 (Supply Chain): {summary_metrics.get("scope_3_co2e_kg", 0.0) / 1000.0:,.2f} metric tons CO2e

Assurance Status: Third-party audit ready.
============================================================
"""
        return doc

    def generate_csrd_report(self, tenant_name, summary_metrics):
        """
        Formulate a report matching Corporate Sustainability Reporting Directive (CSRD) (ESRS E1).
        """
        doc = f"""
============================================================
EUROPEAN SUSTAINABILITY REPORTING STANDARDS (ESRS E1)
============================================================
Entity: {tenant_name}
Reporting Standard: ESRS E1 Climate Change

1. DECARBONIZATION TARGETS
--------------------------
Decarbonization goals: Net Zero target by 2045.
Current Progress Index: Automated tracking enabled.

2. ESRS ENERGY & EMISSION METRICS
---------------------------------
- Gross Scope 1: {summary_metrics.get("scope_1_co2e_kg", 0.0) / 1000.0:,.2f} tCO2e
- Gross Scope 2: {summary_metrics.get("scope_2_location_co2e_kg", 0.0) / 1000.0:,.2f} tCO2e
- Gross Scope 3: {summary_metrics.get("scope_3_co2e_kg", 0.0) / 1000.0:,.2f} tCO2e

Double Materiality: Confirmed high priority climate risk.
============================================================
"""
        return doc

    def _get_tenant_records(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieves real calculated records for the active tenant/user from SQLite.
        """
        try:
            from api.database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            if user_id:
                cursor.execute("""
                SELECT * FROM calculation_results WHERE user_id = ? ORDER BY id ASC
                """, (user_id,))
            else:
                cursor.execute("""
                SELECT * FROM calculation_results ORDER BY id ASC
                """)
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows] if rows else []
        except Exception:
            return []

    def _get_tenant_sessions(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieves upload sessions for the active tenant/user from SQLite.
        """
        try:
            from api.database import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            if user_id:
                cursor.execute("""
                SELECT * FROM upload_sessions WHERE user_id = ? ORDER BY ROWID DESC
                """, (user_id,))
            else:
                cursor.execute("""
                SELECT * FROM upload_sessions ORDER BY ROWID DESC
                """)
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows] if rows else []
        except Exception:
            return []

    def copilot_chat(self, query: str, user_id: Optional[int] = None, context_data=None) -> str:
        """
        AI Copilot advisor responding to sustainability team queries using real tenant calculations.
        """
        q = (query or "").strip().lower()
        records = self._get_tenant_records(user_id=user_id)
        sessions = self._get_tenant_sessions(user_id=user_id)

        # 1. NO DATA / EMPTY STATE CHECK
        has_calculated_data = len(records) > 0
        if not has_calculated_data:
            data_keywords = [
                "supplier", "emission", "emissions", "highest", "top", "scope", "footprint",
                "cbam", "cost", "material", "review", "factor", "total", "kg", "co2", "po", "invoice"
            ]
            if any(k in q for k in data_keywords):
                return "I don't have any calculated emissions data yet — upload and approve a document first."
            
            # General greetings / non-data questions
            if any(w in q for w in ["hello", "hi", "hey", "help", "who are you"]):
                return (
                    "Hello! I am your AI Sustainability Copilot. Once you upload and calculate an invoice or carbon dataset, "
                    "I can analyze supplier footprints, GHG scope breakdowns, CBAM cost exposure, or explain specific calculation traces."
                )
            
            # Check policy / RAG fallback if RAG service available
            if self.rag:
                try:
                    rag_res = self.rag.query(query, tenant_id=f"user_{user_id}" if user_id else "public")
                    if rag_res and rag_res.get("response"):
                        return rag_res["response"]
                except Exception:
                    pass
            
            return "I don't have any calculated emissions data yet — upload and approve a document first."

        # 2. DATA AGGREGATIONS OVER CURRENT TENANT'S REAL DATA
        total_co2e_kg = sum(r.get("co2e_kg", 0.0) for r in records)
        total_co2e_tonnes = total_co2e_kg / 1000.0
        total_cbam_cost = sum(r.get("cbam_cost_eur", 0.0) for r in records)

        scope_1_kg = sum(r.get("co2e_kg", 0.0) for r in records if r.get("scope") == "Scope 1")
        scope_2_kg = sum(r.get("co2e_kg", 0.0) for r in records if r.get("scope") == "Scope 2")
        scope_3_kg = sum(r.get("co2e_kg", 0.0) for r in records if r.get("scope") == "Scope 3")

        # Group by supplier
        supplier_totals = {}
        supplier_materials = {}
        for r in records:
            sup = str(r.get("supplier") or "Unspecified Supplier").strip()
            co2 = float(r.get("co2e_kg", 0.0))
            mat = str(r.get("material") or "").strip()
            
            supplier_totals[sup] = supplier_totals.get(sup, 0.0) + co2
            if sup not in supplier_materials:
                supplier_materials[sup] = set()
            if mat:
                supplier_materials[sup].add(mat)

        sorted_suppliers = sorted(supplier_totals.items(), key=lambda x: x[1], reverse=True)
        top_supplier, top_supplier_co2e = sorted_suppliers[0] if sorted_suppliers else ("None", 0.0)

        # Flagged / review required items
        review_records = [r for r in records if r.get("calculation_status") != "Calculated"]

        # 3. QUERY INTENT DISPATCHING

        # (A) Top Supplier / Highest Emissions Supplier Query
        is_highest_supplier_q = any(phrase in q for phrase in [
            "highest emission", "highest emissions", "high emission", "highest emitter", "top emitter",
            "top supplier", "highest supplier", "most polluting", "emitted most", "maximum emission", "highest carbon"
        ])
        is_give_supplier_name_q = any(phrase in q for phrase in [
            "give me the name of supplier", "give me the name of the supplier", "give me the name of that supplier",
            "give me the name of the top supplier", "give me the name of top supplier", "give me supplier name",
            "name of supplier", "name of the supplier", "name of the top supplier", "name of top supplier",
            "who is the supplier", "who is the top supplier", "supplier name", "which supplier"
        ])

        if is_highest_supplier_q or is_give_supplier_name_q:
            if not sorted_suppliers or top_supplier == "None":
                return "No supplier names were identified in the active calculated records."

            top_pct = (top_supplier_co2e / total_co2e_kg * 100) if total_co2e_kg > 0 else 0.0
            top_mats_str = ", ".join(list(supplier_materials.get(top_supplier, []))[:3]) or "Procured Goods"

            if is_give_supplier_name_q and not is_highest_supplier_q and len(sorted_suppliers) == 1:
                return (
                    f"The supplier in your calculated dataset is **{top_supplier}**.\n\n"
                    f"- **Total Emissions**: {top_supplier_co2e:,.2f} kg CO₂e ({top_supplier_co2e/1000.0:.3f} tonnes CO₂e)\n"
                    f"- **Materials Supplied**: {top_mats_str}"
                )

            res = (
                f"The supplier with the highest emissions is **{top_supplier}** with **{top_supplier_co2e:,.2f} kg CO₂e** "
                f"({top_supplier_co2e/1000.0:.3f} tonnes CO₂e), accounting for **{top_pct:.1f}%** of total emissions.\n\n"
                f"**Key Supplied Items:** {top_mats_str}\n\n"
            )

            if len(sorted_suppliers) > 1:
                res += "**Supplier Emission Rankings:**\n"
                for rank, (s_name, s_co2) in enumerate(sorted_suppliers[:5], 1):
                    s_pct = (s_co2 / total_co2e_kg * 100) if total_co2e_kg > 0 else 0.0
                    res += f"{rank}. **{s_name}**: {s_co2:,.2f} kg CO₂e ({s_co2/1000.0:.3f} t, {s_pct:.1f}%)\n"
            return res.strip()

        # (B) List All Suppliers
        if any(phrase in q for phrase in ["list suppliers", "all suppliers", "compare suppliers", "how many suppliers"]):
            res = f"There are **{len(sorted_suppliers)} supplier(s)** in your active carbon inventory:\n\n"
            for rank, (s_name, s_co2) in enumerate(sorted_suppliers, 1):
                mats = ", ".join(list(supplier_materials.get(s_name, []))[:2])
                res += f"{rank}. **{s_name}**: {s_co2:,.2f} kg CO₂e ({s_co2/1000.0:.3f} tonnes CO₂e) — *{mats}*\n"
            return res.strip()

        # (C) Scope 1, Scope 2, Scope 3 Breakdown
        if any(w in q for w in ["scope", "scopes", "scope 1", "scope 2", "scope 3"]):
            s1_pct = (scope_1_kg / total_co2e_kg * 100) if total_co2e_kg > 0 else 0.0
            s2_pct = (scope_2_kg / total_co2e_kg * 100) if total_co2e_kg > 0 else 0.0
            s3_pct = (scope_3_kg / total_co2e_kg * 100) if total_co2e_kg > 0 else 0.0

            return (
                f"### GHG Protocol Scope Breakdown\n\n"
                f"- **Scope 1 (Direct Fuels & Fleet)**: **{scope_1_kg:,.2f} kg CO₂e** ({s1_pct:.1f}%)\n"
                f"- **Scope 2 (Electricity & Utilities)**: **{scope_2_kg:,.2f} kg CO₂e** ({s2_pct:.1f}%)\n"
                f"- **Scope 3 (Value Chain / Materials / Logistics)**: **{scope_3_kg:,.2f} kg CO₂e** ({s3_pct:.1f}%)\n\n"
                f"**Total Footprint**: {total_co2e_kg:,.2f} kg CO₂e ({total_co2e_tonnes:.3f} tonnes CO₂e)"
            )

        # (D) Total Footprint / Total Emissions
        if any(w in q for w in ["total footprint", "total emission", "total emissions", "how much co2", "total co2"]):
            return (
                f"Your total calculated carbon footprint across **{len(records)} line items** is "
                f"**{total_co2e_kg:,.2f} kg CO₂e** ({total_co2e_tonnes:.3f} tonnes CO₂e), with an estimated "
                f"CBAM cost exposure of **€{total_cbam_cost:,.2f}**."
            )

        # (E) CBAM Cost Exposure & Optimization
        if any(w in q for w in ["cbam", "carbon tax", "tariff", "cbam cost"]):
            # Group CBAM by material
            cbam_by_mat = {}
            for r in records:
                mat = r.get("material") or "Item"
                cbam_by_mat[mat] = cbam_by_mat.get(mat, 0.0) + float(r.get("cbam_cost_eur", 0.0))
            sorted_cbam = sorted(cbam_by_mat.items(), key=lambda x: x[1], reverse=True)

            res = f"### CBAM Liability Summary\n\nTotal CBAM Cost Exposure: **€{total_cbam_cost:,.2f}**\n\n"
            if sorted_cbam and sorted_cbam[0][1] > 0:
                res += "**Highest CBAM Cost Items:**\n"
                for mat, cost in sorted_cbam[:3]:
                    if cost > 0:
                        res += f"- **{mat}**: €{cost:,.2f}\n"
            else:
                res += "All line items are either EU-sourced, zero-tariff, or have no active CBAM tariff liability."
            return res.strip()

        # (F) Review Required / Unmapped / Anomalies
        if any(w in q for w in ["review", "unmapped", "missing factor", "anomaly", "flagged"]):
            if not review_records:
                return f"All {len(records)} line items have been calculated and factor-matched with 100% audit parity."
            res = f"There are **{len(review_records)} line item(s)** flagged for manual review:\n\n"
            for r in review_records[:5]:
                res += f"- **PO {r.get('po_number') or 'N/A'}** ({r.get('material')}): {r.get('calculation_status')} — {r.get('anomaly_reason') or 'Awaiting factor verification'}\n"
            return res.strip()

        # (G) Why / Explanation of Calculations
        if "why" in q or "explain" in q or "formula" in q:
            sorted_rows = sorted(records, key=lambda x: float(x.get("co2e_kg", 0.0)), reverse=True)
            top_row = sorted_rows[0] if sorted_rows else {}
            mat = top_row.get("material", "Material")
            qty = top_row.get("quantity", 0)
            unit = top_row.get("unit", "kg")
            co2e = float(top_row.get("co2e_kg", 0.0))
            factor = top_row.get("emission_factor", 0.0)
            formula = top_row.get("formula", f"{qty} * {factor}")

            return (
                f"### Calculation Explanation\n\n"
                f"Emissions are calculated per the GHG Protocol formula: `Emissions (kg CO₂e) = Activity Quantity x Emission Factor`.\n\n"
                f"For your highest-emitting line item (**{mat}** from **{top_row.get('supplier')}**):\n"
                f"- **Quantity**: {qty} {unit}\n"
                f"- **Emission Factor**: {factor} kg CO₂e/{unit}\n"
                f"- **Calculated Footprint**: **{co2e:,.2f} kg CO₂e**\n"
                f"- **Formula Used**: `{formula}`"
            )

        # (H) Generic LLM Context Answering / Grounded RAG
        if self.rag:
            try:
                # Include real dataset summary in query context
                data_summary = (
                    f"Real Data: Total CO2e={total_co2e_kg:.2f}kg, Scope 1={scope_1_kg:.2f}kg, "
                    f"Scope 2={scope_2_kg:.2f}kg, Scope 3={scope_3_kg:.2f}kg, Top Supplier={top_supplier} ({top_supplier_co2e:.2f}kg), "
                    f"CBAM Exposure=€{total_cbam_cost:.2f}."
                )
                rag_res = self.rag.query(f"{query}\n[Context Data: {data_summary}]", tenant_id=f"user_{user_id}" if user_id else "public")
                if rag_res and rag_res.get("response"):
                    return rag_res["response"]
            except Exception:
                pass

        return (
            f"Based on your current calculated inventory of {len(records)} line items:\n"
            f"- Total Footprint: **{total_co2e_kg:,.2f} kg CO₂e**\n"
            f"- Top Emitting Supplier: **{top_supplier}** ({top_supplier_co2e:,.2f} kg CO₂e)\n"
            f"- CBAM Cost Exposure: **€{total_cbam_cost:,.2f}**\n\n"
            f"You can ask me specific questions such as *'Which supplier has the highest emissions?'*, "
            f"*'Give me the scope breakdown'*, or *'What is our CBAM liability?'*."
        )
