import os
import json
import uuid
import pandas as pd
from fpdf import FPDF
from typing import Dict, Any, List


class ReportGeneratorService:
    """
    Enterprise Report Generator Service.
    Generates 5 session-specific compliance reports from the current upload session ONLY.
    Never reuses previous reports — every invocation creates fresh output.

    Reports:
        1. Carbon Report PDF
        2. CBAM Report Excel
        3. Carbon Inventory Excel
        4. Audit Trail JSON
        5. Executive ESG Report PDF

    Every report contains:
        Executive Summary, Document Summary, Materials, Emission Summary,
        Scope 1, Scope 2, Scope 3, CBAM Cost, Top Emitters, Recommendations, Audit Trail.

    Every row contains:
        Factor ID, Formula, Confidence, Timestamp, Report ID.
    """

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_all_reports(self,
                             upload_id: str,
                             summary: Dict[str, Any],
                             validation_scores: Dict[str, Any],
                             inventory_records: List[Dict[str, Any]],
                             audit_rows: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Generates all 5 reports from the CURRENT session only.
        Clears any previous reports in the session folder before writing.
        Returns download URL mappings.
        """
        # Fresh session folder — purge any stale artifacts
        upload_dir = os.path.join(self.output_dir, "uploads", upload_id)
        if os.path.exists(upload_dir):
            for f in os.listdir(upload_dir):
                try:
                    os.remove(os.path.join(upload_dir, f))
                except Exception:
                    pass
        os.makedirs(upload_dir, exist_ok=True)

        report_id = f"RPT-{upload_id}-{uuid.uuid4().hex[:8].upper()}"
        timestamp = pd.Timestamp.now().isoformat()
        carbon_price = summary.get("carbon_price_eur_per_ton", 85.0)
        overall_confidence = summary.get("overall_confidence_pct", 0.0)

        df = pd.DataFrame(inventory_records)

        # Stamp every row with report-level metadata
        df["report_id"] = report_id
        df["report_timestamp"] = timestamp

        # Ensure required row-level columns exist with safe defaults
        for col, default in [("factor_id", "N/A"), ("formula", "N/A"),
                             ("confidence", 0.0), ("extraction_confidence", 0.0)]:
            if col not in df.columns:
                df[col] = default

        # Pre-compute section data used across reports
        sections = self._build_sections(df, summary, validation_scores, carbon_price, report_id, timestamp, upload_id)

        # 1. Carbon Report PDF
        pdf_path = self._generate_carbon_report_pdf(upload_dir, sections)

        # 2. CBAM Report Excel
        cbam_path = self._generate_cbam_report_excel(upload_dir, df, sections)

        # 3. Carbon Inventory Excel
        inventory_path = self._generate_inventory_excel(upload_dir, df, sections)

        # 4. Audit Trail JSON
        audit_path = self._generate_audit_json(upload_dir, df, sections, audit_rows)

        # 5. Executive ESG Report PDF
        esg_path = self._generate_executive_esg_pdf(upload_dir, sections)

        return {
            "carbon_report_pdf": f"/api/reports/download?path={pdf_path}",
            "cbam_report_excel": f"/api/reports/download?path={cbam_path}",
            "inventory_excel": f"/api/reports/download?path={inventory_path}",
            "audit_json": f"/api/reports/download?path={audit_path}",
            "executive_esg_pdf": f"/api/reports/download?path={esg_path}"
        }

    # ---------------------------------------------------------------
    # SECTION DATA BUILDER
    # ---------------------------------------------------------------
    def _build_sections(self, df: pd.DataFrame, summary: Dict, validation_scores: Dict,
                        carbon_price: float, report_id: str, timestamp: str, upload_id: str) -> Dict[str, Any]:
        """Build all 11 report sections from current session data."""

        total_co2e_kg = summary.get("total_co2e_kg", 0.0)
        total_co2e_t = summary.get("total_co2e_tonnes", 0.0)
        total_cbam = summary.get("total_cbam_cost_eur", 0.0)
        s1 = summary.get("scope_1_co2e_kg", 0.0)
        s2 = summary.get("scope_2_co2e_kg", 0.0)
        s3 = summary.get("scope_3_co2e_kg", 0.0)
        rows_count = len(df)
        overall_confidence = validation_scores.get("overall_confidence_pct", summary.get("overall_confidence_pct", 0.0))

        # Scope subtables
        df_s1 = df[df["scope"] == "Scope 1"] if "scope" in df.columns else pd.DataFrame()
        df_s2 = df[df["scope"] == "Scope 2"] if "scope" in df.columns else pd.DataFrame()
        df_s3 = df[df["scope"] == "Scope 3"] if "scope" in df.columns else pd.DataFrame()

        # Top emitters by CO2e
        top_materials = []
        if "material" in df.columns and "co2e_kg" in df.columns:
            top_materials = (
                df.groupby("material")["co2e_kg"].sum()
                .sort_values(ascending=False)
                .head(10)
                .reset_index()
                .to_dict("records")
            )

        top_suppliers = []
        if "supplier" in df.columns and "co2e_kg" in df.columns:
            top_suppliers = (
                df.groupby("supplier")["co2e_kg"].sum()
                .sort_values(ascending=False)
                .head(10)
                .reset_index()
                .to_dict("records")
            )

        # Materials summary
        materials_summary = []
        if "material" in df.columns:
            mat_grp = df.groupby("material").agg({
                "co2e_kg": "sum",
                "quantity": "sum",
                "cbam_cost_eur": "sum"
            }).reset_index()
            mat_grp["count"] = df.groupby("material").size().values
            materials_summary = mat_grp.to_dict("records")

        # Recommendations (rule-based from data)
        recommendations = self._generate_recommendations(df, s1, s2, s3, total_cbam, top_materials, top_suppliers)

        return {
            "report_id": report_id,
            "timestamp": timestamp,
            "upload_id": upload_id,
            "carbon_price": carbon_price,
            "executive_summary": {
                "report_id": report_id,
                "generated_at": timestamp,
                "upload_session": upload_id,
                "total_rows_processed": rows_count,
                "total_co2e_kg": round(total_co2e_kg, 2),
                "total_co2e_tonnes": round(total_co2e_t, 3),
                "total_cbam_cost_eur": round(total_cbam, 2),
                "carbon_price_eur_per_ton": carbon_price,
                "overall_confidence_pct": overall_confidence,
                "materials_count": summary.get("materials_count", 0),
                "suppliers_count": summary.get("suppliers_count", 0),
                "rows_calculated": summary.get("rows_calculated", 0),
                "rows_manual_review": summary.get("rows_manual_review", 0),
            },
            "document_summary": {
                "documents_processed": summary.get("documents_processed", 1),
                "rows_extracted": summary.get("rows_extracted", rows_count),
                "rows_validated": summary.get("rows_validated", rows_count),
                "ocr_confidence_pct": validation_scores.get("ocr_confidence_pct", 0.0),
                "material_match_pct": validation_scores.get("material_match_pct", 0.0),
                "factor_match_pct": validation_scores.get("factor_match_pct", 0.0),
            },
            "materials": materials_summary,
            "emission_summary": {
                "total_co2e_kg": round(total_co2e_kg, 2),
                "scope_1_co2e_kg": round(s1, 2),
                "scope_2_co2e_kg": round(s2, 2),
                "scope_3_co2e_kg": round(s3, 2),
                "scope_1_pct": round(s1 / total_co2e_kg * 100, 1) if total_co2e_kg > 0 else 0,
                "scope_2_pct": round(s2 / total_co2e_kg * 100, 1) if total_co2e_kg > 0 else 0,
                "scope_3_pct": round(s3 / total_co2e_kg * 100, 1) if total_co2e_kg > 0 else 0,
            },
            "scope_1": {
                "total_kg": round(s1, 2),
                "rows_count": len(df_s1),
                "records": df_s1[["material", "supplier", "quantity", "unit", "factor_id",
                                  "emission_factor", "formula", "co2e_kg", "cbam_cost_eur",
                                  "calculation_status", "report_id", "report_timestamp"]].to_dict("records") if len(df_s1) > 0 else [],
            },
            "scope_2": {
                "total_kg": round(s2, 2),
                "rows_count": len(df_s2),
                "records": df_s2[["material", "supplier", "quantity", "unit", "factor_id",
                                  "emission_factor", "formula", "co2e_kg", "cbam_cost_eur",
                                  "calculation_status", "report_id", "report_timestamp"]].to_dict("records") if len(df_s2) > 0 else [],
            },
            "scope_3": {
                "total_kg": round(s3, 2),
                "rows_count": len(df_s3),
                "records": df_s3[["material", "supplier", "quantity", "unit", "factor_id",
                                  "emission_factor", "formula", "co2e_kg", "cbam_cost_eur",
                                  "calculation_status", "report_id", "report_timestamp"]].to_dict("records") if len(df_s3) > 0 else [],
            },
            "cbam_cost": {
                "carbon_price_eur_per_ton": carbon_price,
                "total_embedded_co2e_tonnes": round(total_co2e_t, 3),
                "total_cbam_cost_eur": round(total_cbam, 2),
                "formula": f"CBAM Cost = Embedded CO2e (tonnes) x Carbon Price (EUR/t) = {total_co2e_t:.3f} x {carbon_price} = EUR {total_cbam:.2f}",
            },
            "top_emitters": {
                "by_material": top_materials,
                "by_supplier": top_suppliers,
            },
            "recommendations": recommendations,
            "validation_scores": validation_scores,
        }

    # ---------------------------------------------------------------
    # RECOMMENDATIONS ENGINE
    # ---------------------------------------------------------------
    def _generate_recommendations(self, df, s1, s2, s3, total_cbam, top_materials, top_suppliers) -> List[Dict]:
        """Generate actionable recommendations from current session data."""
        recs = []
        total = s1 + s2 + s3

        if total == 0:
            return [{"priority": "INFO", "category": "General", "recommendation": "No emissions data available for recommendations."}]

        # Scope 1 dominant
        if total > 0 and s1 / total > 0.4:
            recs.append({
                "priority": "HIGH",
                "category": "Scope 1 Reduction",
                "recommendation": f"Scope 1 contributes {s1/total*100:.0f}% of total emissions ({s1:.0f} kg). Consider switching from fossil fuels to renewable alternatives, electrifying fleet vehicles, or improving combustion efficiency."
            })

        # Scope 2 dominant
        if total > 0 and s2 / total > 0.3:
            recs.append({
                "priority": "HIGH",
                "category": "Scope 2 Reduction",
                "recommendation": f"Scope 2 contributes {s2/total*100:.0f}% of total emissions. Consider purchasing renewable energy certificates (RECs), switching to green electricity tariffs, or installing on-site solar generation."
            })

        # Scope 3 dominant (usually the case)
        if total > 0 and s3 / total > 0.5:
            recs.append({
                "priority": "HIGH",
                "category": "Supply Chain Decarbonization",
                "recommendation": f"Scope 3 (supply chain) dominates at {s3/total*100:.0f}% of total emissions ({s3:.0f} kg). Engage top-emitting suppliers for science-based targets and consider sourcing from lower-carbon alternatives."
            })

        # Top material emitter
        if top_materials:
            top_mat = top_materials[0]
            recs.append({
                "priority": "MEDIUM",
                "category": "Material Substitution",
                "recommendation": f"'{top_mat['material']}' is the highest-emitting material at {top_mat['co2e_kg']:.0f} kg CO2e. Evaluate recycled or low-carbon variants to reduce embedded emissions."
            })

        # Top supplier emitter
        if top_suppliers:
            top_sup = top_suppliers[0]
            recs.append({
                "priority": "MEDIUM",
                "category": "Supplier Engagement",
                "recommendation": f"'{top_sup['supplier']}' is the largest contributor at {top_sup['co2e_kg']:.0f} kg CO2e. Request their CDP disclosure and evaluate alternative suppliers with lower emission intensities."
            })

        # CBAM cost reduction
        if total_cbam > 0:
            recs.append({
                "priority": "HIGH",
                "category": "CBAM Cost Mitigation",
                "recommendation": f"Total CBAM exposure is EUR {total_cbam:.2f}. Prioritize near-shoring or sourcing from EU-based suppliers who operate under ETS and may have free allocations."
            })

        # Manual review flagged rows
        manual_review_count = len(df[df["calculation_status"] != "Calculated"]) if "calculation_status" in df.columns else 0
        if manual_review_count > 0:
            recs.append({
                "priority": "CRITICAL",
                "category": "Data Quality",
                "recommendation": f"{manual_review_count} rows require manual auditor review due to low emission factor confidence (<95%). Assign factors manually to improve reporting accuracy."
            })

        return recs

    # ---------------------------------------------------------------
    # REPORT 1: CARBON REPORT PDF
    # ---------------------------------------------------------------
    def _generate_carbon_report_pdf(self, upload_dir: str, sections: Dict) -> str:
        """Generates comprehensive Carbon Audit Report PDF with all 11 sections."""
        path = os.path.join(upload_dir, "carbon_report.pdf")
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        exec_sum = sections["executive_summary"]
        doc_sum = sections["document_summary"]
        emission = sections["emission_summary"]
        cbam = sections["cbam_cost"]

        # --- Cover Page ---
        pdf.add_page()
        pdf.set_font("helvetica", "B", 22)
        pdf.cell(0, 20, text="CarbonLedger", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, text="Carbon Audit Report", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("helvetica", size=10)
        pdf.cell(0, 8, text=f"Report ID: {sections['report_id']}", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.cell(0, 8, text=f"Generated: {sections['timestamp']}", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.cell(0, 8, text=f"Upload Session: {sections['upload_id']}", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(10)

        # --- 1. Executive Summary ---
        self._pdf_section_header(pdf, "1. Executive Summary")
        self._pdf_kv(pdf, "Total Rows Processed", str(exec_sum["total_rows_processed"]))
        self._pdf_kv(pdf, "Total CO2e", f"{exec_sum['total_co2e_tonnes']} tonnes ({exec_sum['total_co2e_kg']} kg)")
        self._pdf_kv(pdf, "Total CBAM Cost", f"EUR {exec_sum['total_cbam_cost_eur']}")
        self._pdf_kv(pdf, "Carbon Price", f"EUR {exec_sum['carbon_price_eur_per_ton']}/t")
        self._pdf_kv(pdf, "Overall Confidence", f"{exec_sum['overall_confidence_pct']}%")
        self._pdf_kv(pdf, "Unique Materials", str(exec_sum["materials_count"]))
        self._pdf_kv(pdf, "Unique Suppliers", str(exec_sum["suppliers_count"]))
        self._pdf_kv(pdf, "Rows Calculated", str(exec_sum["rows_calculated"]))
        self._pdf_kv(pdf, "Rows Manual Review", str(exec_sum["rows_manual_review"]))
        pdf.ln(4)

        # --- 2. Document Summary ---
        self._pdf_section_header(pdf, "2. Document Summary")
        self._pdf_kv(pdf, "Documents Processed", str(doc_sum["documents_processed"]))
        self._pdf_kv(pdf, "Rows Extracted", str(doc_sum["rows_extracted"]))
        self._pdf_kv(pdf, "Rows Validated", str(doc_sum["rows_validated"]))
        self._pdf_kv(pdf, "OCR Confidence", f"{doc_sum['ocr_confidence_pct']}%")
        self._pdf_kv(pdf, "Material Match Rate", f"{doc_sum['material_match_pct']}%")
        self._pdf_kv(pdf, "Factor Match Rate", f"{doc_sum['factor_match_pct']}%")
        pdf.ln(4)

        # --- 3. Materials ---
        self._pdf_section_header(pdf, "3. Materials Summary")
        for mat in sections["materials"]:
            pdf.set_font("helvetica", size=9)
            pdf.cell(0, 6, text=f"  {mat['material']}: {mat['co2e_kg']:.2f} kg CO2e | Qty: {mat['quantity']} | CBAM: EUR {mat['cbam_cost_eur']:.2f} | Rows: {mat['count']}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # --- 4. Emission Summary ---
        self._pdf_section_header(pdf, "4. Emission Summary")
        self._pdf_kv(pdf, "Total CO2e", f"{emission['total_co2e_kg']} kg")
        self._pdf_kv(pdf, "Scope 1", f"{emission['scope_1_co2e_kg']} kg ({emission['scope_1_pct']}%)")
        self._pdf_kv(pdf, "Scope 2", f"{emission['scope_2_co2e_kg']} kg ({emission['scope_2_pct']}%)")
        self._pdf_kv(pdf, "Scope 3", f"{emission['scope_3_co2e_kg']} kg ({emission['scope_3_pct']}%)")
        pdf.ln(4)

        # --- 5. Scope 1 ---
        self._pdf_scope_section(pdf, "5. Scope 1 (Direct Emissions)", sections["scope_1"])

        # --- 6. Scope 2 ---
        self._pdf_scope_section(pdf, "6. Scope 2 (Indirect - Electricity)", sections["scope_2"])

        # --- 7. Scope 3 ---
        self._pdf_scope_section(pdf, "7. Scope 3 (Supply Chain)", sections["scope_3"])

        # --- 8. CBAM Cost ---
        self._pdf_section_header(pdf, "8. CBAM Cost Analysis")
        self._pdf_kv(pdf, "Carbon Price", f"EUR {cbam['carbon_price_eur_per_ton']}/t")
        self._pdf_kv(pdf, "Embedded CO2e", f"{cbam['total_embedded_co2e_tonnes']} tonnes")
        self._pdf_kv(pdf, "Total CBAM Cost", f"EUR {cbam['total_cbam_cost_eur']}")
        pdf.set_font("helvetica", "I", 9)
        pdf.cell(0, 6, text=f"  Formula: {cbam['formula']}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # --- 9. Top Emitters ---
        self._pdf_section_header(pdf, "9. Top Emitters")
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(0, 6, text="  By Material:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", size=9)
        for idx, m in enumerate(sections["top_emitters"]["by_material"][:5], 1):
            pdf.cell(0, 5, text=f"    {idx}. {m['material']}: {m['co2e_kg']:.2f} kg CO2e", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(0, 6, text="  By Supplier:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", size=9)
        for idx, s in enumerate(sections["top_emitters"]["by_supplier"][:5], 1):
            pdf.cell(0, 5, text=f"    {idx}. {s['supplier']}: {s['co2e_kg']:.2f} kg CO2e", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # --- 10. Recommendations ---
        self._pdf_section_header(pdf, "10. Recommendations")
        for rec in sections["recommendations"]:
            pdf.set_font("helvetica", "B", 9)
            pdf.cell(0, 6, text=f"  [{rec['priority']}] {rec['category']}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", size=8)
            # Truncate long recommendation text for PDF
            rec_text = rec["recommendation"]
            if len(rec_text) > 180:
                rec_text = rec_text[:177] + "..."
            pdf.cell(0, 5, text=f"    {rec_text}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # --- 11. Audit Trail ---
        self._pdf_section_header(pdf, "11. Audit Trail")
        pdf.set_font("helvetica", size=8)
        pdf.cell(0, 5, text=f"  Report ID: {sections['report_id']}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, text=f"  Timestamp: {sections['timestamp']}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, text=f"  OCR Confidence: {sections['validation_scores'].get('ocr_confidence_pct', 0)}%", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, text=f"  Factor Match: {sections['validation_scores'].get('factor_match_pct', 0)}%", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, text=f"  Overall Confidence: {sections['validation_scores'].get('overall_confidence_pct', 0)}%", new_x="LMARGIN", new_y="NEXT")

        pdf.output(path)
        return path

    # ---------------------------------------------------------------
    # REPORT 2: CBAM REPORT EXCEL
    # ---------------------------------------------------------------
    def _generate_cbam_report_excel(self, upload_dir: str, df: pd.DataFrame, sections: Dict) -> str:
        """Generates multi-sheet CBAM Report Excel with all 11 sections."""
        path = os.path.join(upload_dir, "cbam_report.xlsx")

        # Row-level columns for the CBAM detail sheet
        cbam_cols = ["material", "supplier", "quantity", "unit", "country",
                     "factor_id", "emission_factor", "formula", "scope",
                     "co2_kg", "ch4_kg", "n2o_kg", "co2e_kg", "cbam_cost_eur",
                     "calculation_status", "extraction_confidence",
                     "report_id", "report_timestamp"]
        available_cols = [c for c in cbam_cols if c in df.columns]
        df_cbam = df[available_cols].copy()
        df_cbam["embedded_co2e_tonnes"] = df_cbam["co2e_kg"] / 1000.0
        df_cbam["carbon_price_eur_per_ton"] = sections["carbon_price"]

        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            # Sheet 1: Executive Summary
            pd.DataFrame([sections["executive_summary"]]).T.reset_index().rename(
                columns={"index": "Metric", 0: "Value"}).to_excel(writer, sheet_name="Executive Summary", index=False)

            # Sheet 2: Document Summary
            pd.DataFrame([sections["document_summary"]]).T.reset_index().rename(
                columns={"index": "Metric", 0: "Value"}).to_excel(writer, sheet_name="Document Summary", index=False)

            # Sheet 3: Materials
            if sections["materials"]:
                pd.DataFrame(sections["materials"]).to_excel(writer, sheet_name="Materials", index=False)

            # Sheet 4: Emission Summary
            pd.DataFrame([sections["emission_summary"]]).T.reset_index().rename(
                columns={"index": "Metric", 0: "Value"}).to_excel(writer, sheet_name="Emission Summary", index=False)

            # Sheet 5: Scope 1
            if sections["scope_1"]["records"]:
                pd.DataFrame(sections["scope_1"]["records"]).to_excel(writer, sheet_name="Scope 1", index=False)

            # Sheet 6: Scope 2
            if sections["scope_2"]["records"]:
                pd.DataFrame(sections["scope_2"]["records"]).to_excel(writer, sheet_name="Scope 2", index=False)

            # Sheet 7: Scope 3
            if sections["scope_3"]["records"]:
                pd.DataFrame(sections["scope_3"]["records"]).to_excel(writer, sheet_name="Scope 3", index=False)

            # Sheet 8: CBAM Cost Detail
            df_cbam.to_excel(writer, sheet_name="CBAM Cost", index=False)

            # Sheet 9: Top Emitters
            top_mat_df = pd.DataFrame(sections["top_emitters"]["by_material"])
            top_sup_df = pd.DataFrame(sections["top_emitters"]["by_supplier"])
            if not top_mat_df.empty:
                top_mat_df.to_excel(writer, sheet_name="Top Emitters - Materials", index=False)
            if not top_sup_df.empty:
                top_sup_df.to_excel(writer, sheet_name="Top Emitters - Suppliers", index=False)

            # Sheet 10: Recommendations
            if sections["recommendations"]:
                pd.DataFrame(sections["recommendations"]).to_excel(writer, sheet_name="Recommendations", index=False)

            # Sheet 11: Audit Trail
            audit_df = pd.DataFrame([{
                "report_id": sections["report_id"],
                "timestamp": sections["timestamp"],
                "upload_id": sections["upload_id"],
                **sections["validation_scores"]
            }])
            audit_df.to_excel(writer, sheet_name="Audit Trail", index=False)

            # Sheet 12: Manual Corrections
            all_corrections = []
            for _, row in df.iterrows():
                row_corrs = row.get("manual_corrections", [])
                if isinstance(row_corrs, list):
                    for corr in row_corrs:
                        all_corrections.append({
                            "Row ID": int(row.get("id", 0)),
                            "PO Number": row.get("po_number", ""),
                            "Material": row.get("material", ""),
                            "Field": corr.get("field", ""),
                            "Original OCR Value": corr.get("original_ocr_value", ""),
                            "Approved Value": corr.get("approved_value", ""),
                            "Correction Reason": corr.get("correction_reason", ""),
                            "Correction Timestamp": corr.get("timestamp", ""),
                            "User": corr.get("user", "")
                        })
            if all_corrections:
                pd.DataFrame(all_corrections).to_excel(writer, sheet_name="Manual Corrections", index=False)

        return path

    # ---------------------------------------------------------------
    # REPORT 3: CARBON INVENTORY EXCEL
    # ---------------------------------------------------------------
    def _generate_inventory_excel(self, upload_dir: str, df: pd.DataFrame, sections: Dict) -> str:
        """Generates multi-sheet Carbon Inventory workbook with full row detail."""
        path = os.path.join(upload_dir, "inventory.xlsx")

        # Full row-level inventory columns (every row includes Factor ID, Formula, Confidence, Timestamp, Report ID)
        inv_cols = ["id", "po_number", "supplier", "material", "matched_material",
                    "quantity", "unit", "cost", "delivery_date",
                    "facility", "country", "scope",
                    "factor_id", "factor_source", "emission_factor", "formula",
                    "co2_kg", "ch4_kg", "n2o_kg", "co2e_kg", "cbam_cost_eur",
                    "calculation_status", "extraction_confidence", "ocr_confidence",
                    "report_id", "report_timestamp"]
        available = [c for c in inv_cols if c in df.columns]

        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            # Sheet 1: Executive Summary
            pd.DataFrame([sections["executive_summary"]]).T.reset_index().rename(
                columns={"index": "Metric", 0: "Value"}).to_excel(writer, sheet_name="Executive Summary", index=False)

            # Sheet 2: Document Summary
            pd.DataFrame([sections["document_summary"]]).T.reset_index().rename(
                columns={"index": "Metric", 0: "Value"}).to_excel(writer, sheet_name="Document Summary", index=False)

            # Sheet 3: Full Inventory (all rows with Factor ID, Formula, Confidence, Timestamp, Report ID)
            df[available].to_excel(writer, sheet_name="Carbon Inventory", index=False)

            # Sheet 4: Materials
            if sections["materials"]:
                pd.DataFrame(sections["materials"]).to_excel(writer, sheet_name="Materials", index=False)

            # Sheet 5: Emission Summary
            pd.DataFrame([sections["emission_summary"]]).T.reset_index().rename(
                columns={"index": "Metric", 0: "Value"}).to_excel(writer, sheet_name="Emission Summary", index=False)

            # Sheet 6: Scope 1
            if sections["scope_1"]["records"]:
                pd.DataFrame(sections["scope_1"]["records"]).to_excel(writer, sheet_name="Scope 1", index=False)

            # Sheet 7: Scope 2
            if sections["scope_2"]["records"]:
                pd.DataFrame(sections["scope_2"]["records"]).to_excel(writer, sheet_name="Scope 2", index=False)

            # Sheet 8: Scope 3
            if sections["scope_3"]["records"]:
                pd.DataFrame(sections["scope_3"]["records"]).to_excel(writer, sheet_name="Scope 3", index=False)

            # Sheet 9: CBAM Cost
            pd.DataFrame([sections["cbam_cost"]]).T.reset_index().rename(
                columns={"index": "Metric", 0: "Value"}).to_excel(writer, sheet_name="CBAM Cost", index=False)

            # Sheet 10: Top Emitters
            top_mat_df = pd.DataFrame(sections["top_emitters"]["by_material"])
            if not top_mat_df.empty:
                top_mat_df.to_excel(writer, sheet_name="Top Emitters", index=False)

            # Sheet 11: Recommendations
            if sections["recommendations"]:
                pd.DataFrame(sections["recommendations"]).to_excel(writer, sheet_name="Recommendations", index=False)

            # Sheet 12: Manual Corrections
            all_corrections = []
            for _, row in df.iterrows():
                row_corrs = row.get("manual_corrections", [])
                if isinstance(row_corrs, list):
                    for corr in row_corrs:
                        all_corrections.append({
                            "Row ID": int(row.get("id", 0)),
                            "PO Number": row.get("po_number", ""),
                            "Material": row.get("material", ""),
                            "Field": corr.get("field", ""),
                            "Original OCR Value": corr.get("original_ocr_value", ""),
                            "Approved Value": corr.get("approved_value", ""),
                            "Correction Reason": corr.get("correction_reason", ""),
                            "Correction Timestamp": corr.get("timestamp", ""),
                            "User": corr.get("user", "")
                        })
            if all_corrections:
                pd.DataFrame(all_corrections).to_excel(writer, sheet_name="Manual Corrections", index=False)

        return path

    # ---------------------------------------------------------------
    # REPORT 4: AUDIT TRAIL JSON
    # ---------------------------------------------------------------
    def _generate_audit_json(self, upload_dir: str, df: pd.DataFrame, sections: Dict,
                             audit_rows: List[Dict]) -> str:
        """Generates comprehensive Audit Trail JSON with all 11 sections and verifiable SHA-256 cryptographic hash chaining."""
        import hashlib
        path = os.path.join(upload_dir, "audit.json")

        # Build row-level audit entries (each row has Factor ID, Formula, Confidence, Timestamp, Report ID)
        row_audit = []
        for _, row in df.iterrows():
            row_audit.append({
                "row_id": int(row.get("id", 0)),
                "material": row.get("material", ""),
                "supplier": row.get("supplier", ""),
                "quantity": float(row.get("quantity", 0)),
                "unit": row.get("unit", ""),
                "scope": row.get("scope", ""),
                "factor_id": row.get("factor_id", "N/A"),
                "factor_source": row.get("factor_source", "N/A"),
                "emission_factor": float(row.get("emission_factor", 0)),
                "formula": row.get("formula", "N/A"),
                "confidence": float(row.get("extraction_confidence", 0)),
                "co2e_kg": float(row.get("co2e_kg", 0)),
                "cbam_cost_eur": float(row.get("cbam_cost_eur", 0)),
                "calculation_status": row.get("calculation_status", ""),
                "calculation_trace": row.get("calculation_trace", []),
                "timestamp": sections["timestamp"],
                "report_id": sections["report_id"],
            })

        # Calculate genuine cryptographic SHA-256 hash chain
        genesis_hash = hashlib.sha256(f"GENESIS_BLOCK_{sections['upload_id']}_{sections['timestamp']}".encode('utf-8')).hexdigest()
        prev_hash = genesis_hash
        hash_chained_audit = []
        
        for idx, item in enumerate(row_audit):
            item_raw = json.dumps(item, sort_keys=True, default=str)
            curr_hash = hashlib.sha256(f"{prev_hash}|{item['timestamp']}|{item_raw}".encode('utf-8')).hexdigest()
            item_with_hash = dict(item)
            item_with_hash["block_index"] = idx + 1
            item_with_hash["previous_hash"] = prev_hash
            item_with_hash["entry_hash"] = curr_hash
            hash_chained_audit.append(item_with_hash)
            prev_hash = curr_hash

        audit_package = {
            "report_id": sections["report_id"],
            "generated_at": sections["timestamp"],
            "upload_id": sections["upload_id"],
            "cryptographic_verification": {
                "hash_algorithm": "SHA-256",
                "genesis_block_hash": genesis_hash,
                "latest_chain_hash": prev_hash,
                "total_verified_blocks": len(hash_chained_audit),
                "tamper_evident": True
            },
            "sections": {
                "1_executive_summary": sections["executive_summary"],
                "2_document_summary": sections["document_summary"],
                "3_materials": sections["materials"],
                "4_emission_summary": sections["emission_summary"],
                "5_scope_1": {
                    "total_kg": sections["scope_1"]["total_kg"],
                    "rows_count": sections["scope_1"]["rows_count"],
                },
                "6_scope_2": {
                    "total_kg": sections["scope_2"]["total_kg"],
                    "rows_count": sections["scope_2"]["rows_count"],
                },
                "7_scope_3": {
                    "total_kg": sections["scope_3"]["total_kg"],
                    "rows_count": sections["scope_3"]["rows_count"],
                },
                "8_cbam_cost": sections["cbam_cost"],
                "9_top_emitters": sections["top_emitters"],
                "10_recommendations": sections["recommendations"],
                "11_audit_trail": {
                    "validation_scores": sections["validation_scores"],
                    "row_level_audit": hash_chained_audit,
                    "pipeline_audit_rows": audit_rows,
                    "manual_corrections": [
                        {
                            "row_id": int(row.get("id", 0)),
                            "po_number": row.get("po_number", ""),
                            "material": row.get("material", ""),
                            "field": corr.get("field", ""),
                            "original_ocr_value": corr.get("original_ocr_value", ""),
                            "approved_value": corr.get("approved_value", ""),
                            "correction_reason": corr.get("correction_reason", ""),
                            "timestamp": corr.get("timestamp", ""),
                            "user": corr.get("user", "")
                        }
                        for _, row in df.iterrows()
                        for corr in row.get("manual_corrections", [])
                        if isinstance(row.get("manual_corrections"), list)
                    ]
                }
            }
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(audit_package, f, indent=2, default=str)

        return path

    # ---------------------------------------------------------------
    # REPORT 5: EXECUTIVE ESG REPORT PDF
    # ---------------------------------------------------------------
    def _generate_executive_esg_pdf(self, upload_dir: str, sections: Dict) -> str:
        """Generates Executive ESG Report PDF with all 11 sections (board-level summary)."""
        path = os.path.join(upload_dir, "executive_esg_report.pdf")
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        exec_sum = sections["executive_summary"]
        emission = sections["emission_summary"]
        cbam = sections["cbam_cost"]

        # --- Cover ---
        pdf.add_page()
        pdf.set_font("helvetica", "B", 22)
        pdf.cell(0, 20, text="CarbonLedger", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, text="Executive ESG & Carbon Accounting Report", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("helvetica", size=10)
        pdf.cell(0, 8, text=f"Report ID: {sections['report_id']}", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.cell(0, 8, text=f"Generated: {sections['timestamp']}", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(10)

        # --- 1. Executive Summary ---
        self._pdf_section_header(pdf, "1. Executive Summary")
        self._pdf_kv(pdf, "Total Carbon Footprint", f"{exec_sum['total_co2e_tonnes']} tonnes CO2e")
        self._pdf_kv(pdf, "Total CBAM Exposure", f"EUR {exec_sum['total_cbam_cost_eur']}")
        self._pdf_kv(pdf, "Data Fidelity", f"{exec_sum['overall_confidence_pct']}%")
        self._pdf_kv(pdf, "Records Processed", str(exec_sum["total_rows_processed"]))
        pdf.ln(4)

        # --- 2. Document Summary ---
        self._pdf_section_header(pdf, "2. Document Processing Summary")
        doc_sum = sections["document_summary"]
        self._pdf_kv(pdf, "Documents", str(doc_sum["documents_processed"]))
        self._pdf_kv(pdf, "OCR Confidence", f"{doc_sum['ocr_confidence_pct']}%")
        self._pdf_kv(pdf, "Factor Match", f"{doc_sum['factor_match_pct']}%")
        pdf.ln(4)

        # --- 3. Materials ---
        self._pdf_section_header(pdf, "3. Materials Overview")
        for mat in sections["materials"][:8]:
            pdf.set_font("helvetica", size=9)
            pdf.cell(0, 5, text=f"  {mat['material']}: {mat['co2e_kg']:.1f} kg CO2e ({mat['count']} rows)", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # --- 4. Emission Summary ---
        self._pdf_section_header(pdf, "4. Emission Summary")
        self._pdf_kv(pdf, "Scope 1 (Direct)", f"{emission['scope_1_co2e_kg']} kg ({emission['scope_1_pct']}%)")
        self._pdf_kv(pdf, "Scope 2 (Electricity)", f"{emission['scope_2_co2e_kg']} kg ({emission['scope_2_pct']}%)")
        self._pdf_kv(pdf, "Scope 3 (Supply Chain)", f"{emission['scope_3_co2e_kg']} kg ({emission['scope_3_pct']}%)")
        pdf.ln(4)

        # --- 5-7. Scope Details (condensed) ---
        for scope_num, scope_key, label in [(5, "scope_1", "Scope 1"), (6, "scope_2", "Scope 2"), (7, "scope_3", "Scope 3")]:
            self._pdf_section_header(pdf, f"{scope_num}. {label} Detail")
            scope_data = sections[scope_key]
            self._pdf_kv(pdf, "Total", f"{scope_data['total_kg']} kg CO2e")
            self._pdf_kv(pdf, "Rows", str(scope_data['rows_count']))
            pdf.ln(2)

        # --- 8. CBAM Cost ---
        self._pdf_section_header(pdf, "8. CBAM Financial Exposure")
        self._pdf_kv(pdf, "Carbon Price", f"EUR {cbam['carbon_price_eur_per_ton']}/t")
        self._pdf_kv(pdf, "Embedded Carbon", f"{cbam['total_embedded_co2e_tonnes']} tonnes")
        self._pdf_kv(pdf, "CBAM Levy", f"EUR {cbam['total_cbam_cost_eur']}")
        pdf.ln(4)

        # --- 9. Top Emitters ---
        self._pdf_section_header(pdf, "9. Top Emitters")
        for idx, m in enumerate(sections["top_emitters"]["by_material"][:3], 1):
            pdf.set_font("helvetica", size=9)
            pdf.cell(0, 5, text=f"  Material #{idx}: {m['material']} ({m['co2e_kg']:.0f} kg)", new_x="LMARGIN", new_y="NEXT")
        for idx, s in enumerate(sections["top_emitters"]["by_supplier"][:3], 1):
            pdf.set_font("helvetica", size=9)
            pdf.cell(0, 5, text=f"  Supplier #{idx}: {s['supplier']} ({s['co2e_kg']:.0f} kg)", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # --- 10. Recommendations ---
        self._pdf_section_header(pdf, "10. Strategic Recommendations")
        for rec in sections["recommendations"]:
            pdf.set_font("helvetica", "B", 9)
            pdf.cell(0, 6, text=f"  [{rec['priority']}] {rec['category']}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("helvetica", size=8)
            rec_text = rec["recommendation"]
            if len(rec_text) > 180:
                rec_text = rec_text[:177] + "..."
            pdf.cell(0, 5, text=f"    {rec_text}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # --- 11. Audit Trail ---
        self._pdf_section_header(pdf, "11. Audit Trail")
        pdf.set_font("helvetica", size=8)
        pdf.cell(0, 5, text=f"  Report ID: {sections['report_id']}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, text=f"  Generated: {sections['timestamp']}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 5, text=f"  Overall Confidence: {sections['validation_scores'].get('overall_confidence_pct', 0)}%", new_x="LMARGIN", new_y="NEXT")

        pdf.output(path)
        return path

    # ---------------------------------------------------------------
    # PDF HELPERS
    # ---------------------------------------------------------------
    def _pdf_section_header(self, pdf: FPDF, title: str):
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, text=title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", size=9)

    def _pdf_kv(self, pdf: FPDF, key: str, value: str):
        pdf.cell(0, 6, text=f"  {key}: {value}", new_x="LMARGIN", new_y="NEXT")

    def _pdf_scope_section(self, pdf: FPDF, title: str, scope_data: Dict):
        self._pdf_section_header(pdf, title)
        self._pdf_kv(pdf, "Total", f"{scope_data['total_kg']} kg CO2e")
        self._pdf_kv(pdf, "Rows", str(scope_data['rows_count']))
        records = scope_data.get("records", [])
        for r in records[:15]:  # Cap at 15 rows per scope in PDF
            pdf.set_font("helvetica", size=8)
            line = f"    {r.get('material', 'N/A')} | {r.get('supplier', 'N/A')} | {r.get('quantity', 0)} {r.get('unit', '')} | Factor: {r.get('factor_id', 'N/A')} | CO2e: {r.get('co2e_kg', 0):.2f} kg | Status: {r.get('calculation_status', '')}"
            if len(line) > 180:
                line = line[:177] + "..."
            pdf.cell(0, 5, text=line, new_x="LMARGIN", new_y="NEXT")
        if len(records) > 15:
            pdf.set_font("helvetica", "I", 8)
            pdf.cell(0, 5, text=f"    ... and {len(records) - 15} more rows (see Excel for full detail)", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
