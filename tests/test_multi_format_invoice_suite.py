"""
Multi-Format Invoice Extraction & Bulk Calculation Engine Test Suite
===================================================================
Tests layout invariance, multi-format parsing (Formats A-J),
asynchronous bulk processing, real-time timer calculations,
and mathematical carbon calculation parity.
"""

import os
import json
import pytest
import tempfile
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

from pipeline.extraction.field_mapper import FieldMapper
from services.document_ai_service import DocumentAIService
from services.universal_upload_service import UniversalUploadService
from services.bulk_upload_service import BulkUploadService
from api.database import get_db_connection, init_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Ensure database schema and factor tables are initialized."""
    init_db()


@pytest.fixture
def doc_ai():
    return DocumentAIService()


@pytest.fixture
def calc_service():
    return UniversalUploadService()


@pytest.fixture
def bulk_service():
    return BulkUploadService()


class TestFieldMapperRobustness:
    """Tests semantic header mapping across reordered, aliased, and multilingual column names."""

    def test_synonym_recognition_formats_a_b_c(self):
        # Material synonyms
        assert FieldMapper.map_header("Material Description") == "material"
        assert FieldMapper.map_header("Item / Product Name") == "material"
        assert FieldMapper.map_header("Commodity") == "material"
        assert FieldMapper.map_header("Goods Description") == "material"
        assert FieldMapper.map_header("Description") == "material"

        # Quantity synonyms
        assert FieldMapper.map_header("Qty") == "quantity"
        assert FieldMapper.map_header("Amount Qty") == "quantity"
        assert FieldMapper.map_header("Volume") == "quantity"
        assert FieldMapper.map_header("Weight") == "weight"
        assert FieldMapper.map_header("Net Weight") == "weight"
        assert FieldMapper.map_header("Billed Quantity") == "quantity"

        # Unit synonyms
        assert FieldMapper.map_header("UOM") == "unit"
        assert FieldMapper.map_header("Unit of Measure") == "unit"
        assert FieldMapper.map_header("Measure") == "unit"
        assert FieldMapper.map_header("Units") == "unit"

        # Cost synonyms
        assert FieldMapper.map_header("Rate") in ["unit_rate", "cost"]
        assert FieldMapper.map_header("Unit Price") in ["unit_rate", "cost"]
        assert FieldMapper.map_header("Taxable Value") in ["total_amount", "cost"]
        assert FieldMapper.map_header("Line Total") in ["total_amount", "cost"]
        assert FieldMapper.map_header("Total Amount") in ["total_amount", "cost"]

        # Transport synonyms
        assert FieldMapper.map_header("Shipment Distance") == "distance"
        assert FieldMapper.map_header("Dispatch Location") == "origin"
        assert FieldMapper.map_header("Delivery Location") == "destination"
        assert FieldMapper.map_header("Mode of Transport") == "transport_mode"


class TestMultiFormatExtractionFormats:
    """Tests Formats A through J extraction and normalization."""

    def test_format_a_traditional_table(self, doc_ai, calc_service):
        """Format A: Standard Table (Material | Supplier | Qty | Unit | Total)"""
        text = """
        TAX INVOICE
        Invoice No: INV-2026-001
        Supplier: Acme Steel Ltd
        
        Item Description | Supplier | Quantity | Unit | Total Cost
        Structural Steel Beams | Acme Steel Ltd | 15000 | kg | $30,000.00
        Portland Cement | UltraCem Corp | 25000 | kg | $12,500.00
        """
        records = doc_ai.extract_from_text(text, filename="format_a_invoice.pdf")
        assert len(records) >= 2
        
        calc_res = calc_service.calculate_and_save(records, upload_id="test-fmt-a")
        summary = calc_res["summary"]
        assert summary["rows_calculated"] >= 1
        assert summary["total_co2e_kg"] > 0
        assert summary["scope_3_co2e_kg"] > 0

    def test_format_b_reordered_columns(self, doc_ai, calc_service):
        """Format B: Reordered Columns (Qty | Unit | Material | Unit Price | Total | Supplier)"""
        text = """
        COMMERCIAL INVOICE
        Qty | Unit | Material Description | Unit Price | Total | Supplier
        15000 | kg | Structural Steel Beams | $2.00 | $30000 | Acme Steel Ltd
        25000 | kg | Portland Cement | $0.50 | $12500 | UltraCem Corp
        """
        records = doc_ai.extract_from_text(text, filename="format_b_invoice.pdf")
        assert len(records) >= 2
        
        materials = [r.get("activity", {}).get("material") or r.get("material") for r in records]
        assert any("Steel" in m for m in materials if m)
        assert any("Cement" in m for m in materials if m)

    def test_layout_invariance_format_a_vs_format_b(self, doc_ai, calc_service):
        """Format A and Format B with identical activity must produce identical kg CO2e."""
        text_a = """
        INVOICE FORMAT A
        Description | Quantity | Unit
        Hot Rolled Steel Sheet | 10000 | kg
        Virgin Aluminium Ingot | 5000 | kg
        """
        text_b = """
        INVOICE FORMAT B (REORDERED)
        Quantity | Unit | Commodity Item
        10000 | kg | Hot Rolled Steel Sheet
        5000 | kg | Virgin Aluminium Ingot
        """
        records_a = doc_ai.extract_from_text(text_a, filename="invoice_a.pdf")
        records_b = doc_ai.extract_from_text(text_b, filename="invoice_b.pdf")

        calc_a = calc_service.calculate_and_save(records_a, upload_id="inv-a-test")
        calc_b = calc_service.calculate_and_save(records_b, upload_id="inv-b-test")

        co2e_a = calc_a["summary"]["total_co2e_kg"]
        co2e_b = calc_b["summary"]["total_co2e_kg"]

        assert co2e_a > 0
        assert co2e_b > 0
        assert pytest.approx(co2e_a, rel=1e-3) == co2e_b

    def test_format_c_alternate_headers(self, doc_ai, calc_service):
        """Format C: Alternate Headers (Product / Commodity, Volume / UOM, Weight, Taxable Value)"""
        text = """
        PURCHASE BILL
        Commodity / Goods | Volume / Measure | UOM | Taxable Value
        Copper Cathodes | 2500 | kg | $22,500
        HDPE Polymers | 8000 | kg | $9,600
        """
        records = doc_ai.extract_from_text(text, filename="format_c.pdf")
        assert len(records) >= 2
        calc_res = calc_service.calculate_and_save(records, upload_id="fmt-c-test")
        assert calc_res["summary"]["rows_calculated"] >= 1
        assert calc_res["summary"]["total_co2e_kg"] > 0

    def test_format_d_multipage_invoice(self, doc_ai, calc_service):
        """Format D: Multi-page invoice with repeated headers and running line numbers."""
        text = """
        --- PAGE 1 ---
        INVOICE #99881 - BATCH 1
        Item No | Description | Qty | UOM
        1 | Galvanized Steel Coil | 12000 | kg
        2 | Aluminium Extrusion | 4000 | kg
        
        --- PAGE 2 ---
        INVOICE #99881 - BATCH 2 (CONTINUED)
        Item No | Description | Qty | UOM
        3 | Flat Glass Float | 3000 | kg
        4 | Synthetic Rubber EPDM | 1500 | kg
        """
        records = doc_ai.extract_from_text(text, filename="multipage.pdf")
        assert len(records) >= 4
        calc_res = calc_service.calculate_and_save(records, upload_id="fmt-d-test")
        assert calc_res["summary"]["rows_calculated"] >= 1
        assert calc_res["summary"]["total_co2e_kg"] > 0

    def test_format_e_key_value_non_table(self, doc_ai, calc_service):
        """Format E: Non-table key-value plain text layout."""
        text = """
        PROCUREMENT STATEMENT
        Vendor: Global Metals Inc
        
        Item: Reinforcing Steel Rebar
        Quantity: 20000 kg
        Total: $16,000 USD
        
        Item: Ready-Mix Concrete C25/30
        Quantity: 15000 kg
        Total: $4,500 USD
        """
        records = doc_ai.extract_from_text(text, filename="format_e_text.pdf")
        assert len(records) >= 2
        calc_res = calc_service.calculate_and_save(records, upload_id="fmt-e-test")
        assert calc_res["summary"]["rows_calculated"] >= 1
        assert calc_res["summary"]["total_co2e_kg"] > 0

    def test_format_f_scanned_ocr_tokens(self, doc_ai, calc_service):
        """Format F: Simulated OCR token output with spacing variations."""
        text = """
        INVOICE [OCR SCANNED]
        Line | Item_Desc | Qty_Billed | Units
        01 | Stainless  Steel  Sheet 304 | 5000 | kg
        02 | Polypropylene  Granules | 3500 | kg
        """
        records = doc_ai.extract_from_text(text, filename="format_f_ocr.pdf")
        assert len(records) >= 2
        calc_res = calc_service.calculate_and_save(records, upload_id="fmt-f-test")
        assert calc_res["summary"]["rows_calculated"] >= 1
        assert calc_res["summary"]["total_co2e_kg"] > 0

    def test_format_g_single_material_invoice(self, doc_ai, calc_service):
        """Format G: Single material invoice."""
        text = """
        INVOICE
        Supplier: Apex Steel
        Item: Structural Steel
        Quantity: 50000 kg
        Amount: $10,000
        """
        records = doc_ai.extract_from_text(text, filename="single_item.pdf")
        assert len(records) == 1
        calc_res = calc_service.calculate_and_save(records, upload_id="fmt-g-test")
        assert calc_res["summary"]["rows_calculated"] >= 1
        assert calc_res["summary"]["total_co2e_kg"] > 0

    def test_format_h_fifty_plus_materials(self, doc_ai, calc_service):
        """Format H: 50+ line items invoice."""
        lines = ["Item | Description | Quantity | Unit | Cost"]
        materials = [
            "Hot Rolled Steel", "Cold Rolled Steel", "Aluminium Ingot", "Copper Wire",
            "Polyethylene HDPE", "Polypropylene PP", "Flat Glass", "Portland Cement",
            "Ready Mix Concrete", "Structural Steel", "Stainless Steel", "Cast Iron"
        ]
        for i in range(1, 55):
            mat = materials[i % len(materials)]
            lines.append(f"{i} | {mat} | {1000 + i * 50} | kg | ${500 + i * 20}")
        
        full_text = "\n".join(lines)
        records = doc_ai.extract_from_text(full_text, filename="fifty_plus.pdf")
        assert len(records) >= 50
        calc_res = calc_service.calculate_and_save(records, upload_id="fmt-h-test")
        assert calc_res["summary"]["rows_calculated"] >= 20
        assert calc_res["summary"]["total_co2e_kg"] > 0

    def test_format_i_transport_freight_line_item(self, doc_ai, calc_service):
        """Format I: Logistics / Transport invoice line item."""
        text = """
        FREIGHT INVOICE
        Origin: Frankfurt
        Destination: Rotterdam
        Transport Mode: Road Freight Truck
        Distance: 450 km
        Weight: 20000 kg
        """
        records = doc_ai.extract_from_text(text, filename="freight_inv.pdf")
        assert len(records) >= 1
        calc_res = calc_service.calculate_and_save(records, upload_id="fmt-i-test")
        assert calc_res["summary"]["rows_calculated"] >= 1
        assert calc_res["summary"]["scope_3_co2e_kg"] > 0

    def test_format_j_international_supplier_currencies(self, doc_ai, calc_service):
        """Format J: Multi-currency and international suppliers."""
        text = """
        INTERNATIONAL INVOICE
        Description | Qty | Unit | Supplier | Currency | Price
        Aluminium Ingot | 8000 | kg | Nippon Metals Co (Japan) | JPY | ¥2,400,000
        Hot Rolled Steel | 12000 | kg | Tata Steel (India) | INR | ₹650,000
        Copper Wire | 4000 | kg | Norsk Hydro (EU) | EUR | €8,800
        """
        records = doc_ai.extract_from_text(text, filename="intl_invoice.pdf")
        assert len(records) >= 3
        calc_res = calc_service.calculate_and_save(records, upload_id="fmt-j-test")
        assert calc_res["summary"]["rows_calculated"] >= 1
        assert calc_res["summary"]["total_co2e_kg"] > 0


class TestBulkUploadEngine:
    """Tests asynchronous batch creation, live timer math, polling, and partial calculation resilience."""

    def test_bulk_batch_lifecycle_and_timers(self, bulk_service):
        # Create 3 invoice files
        files_data = []
        for i in range(1, 4):
            content = f"INVOICE {i}\nDescription | Quantity | Unit\nStructural Steel | {5000 * i} | kg\n"
            files_data.append((f"invoice_batch_{i}.txt", content.encode("utf-8")))

        user_id = 1
        start_res = bulk_service.start_bulk_upload(files_data, user_id=user_id)
        batch_id = start_res["batch_id"]
        assert batch_id is not None
        assert start_res["total_files"] == 3

        # Wait for background thread completion (or max 15s)
        for _ in range(60):
            status_data = bulk_service.get_batch_status(batch_id, user_id=user_id)
            assert status_data is not None
            assert "elapsed_seconds" in status_data
            assert "progress_pct" in status_data
            if status_data["status"] in ["COMPLETED", "COMPLETED_WITH_REVIEW"]:
                break
            time.sleep(0.25)

        final_status = bulk_service.get_batch_status(batch_id, user_id=user_id)
        assert final_status["status"] in ["COMPLETED", "COMPLETED_WITH_REVIEW"]
        assert final_status["completed_count"] == 3
        assert final_status["processed_documents"] == 3
        assert final_status["progress_pct"] == 100
        assert len(final_status["jobs"]) == 3
        assert all(j["status"] == "COMPLETED" for j in final_status["jobs"])
        assert all(j["total_co2e_kg"] > 0 for j in final_status["jobs"])

    def test_bulk_error_resilience(self, bulk_service):
        """A corrupted/empty document on job 2 does not stop or fail job 3."""
        files_data = [
            ("valid_invoice_1.txt", b"INVOICE 1\nDescription | Quantity | Unit\nStructural Steel | 10000 | kg"),
            ("corrupt_empty.txt", b"NOT AN INVOICE JUNK TEXT EMPTY DATA"),
            ("valid_invoice_2.txt", b"INVOICE 2\nDescription | Quantity | Unit\nStructural Steel | 20000 | kg"),
        ]

        user_id = 1
        start_res = bulk_service.start_bulk_upload(files_data, user_id=user_id)
        batch_id = start_res["batch_id"]

        for _ in range(60):
            status_data = bulk_service.get_batch_status(batch_id, user_id=user_id)
            if status_data and status_data["status"] in ["COMPLETED", "COMPLETED_WITH_REVIEW", "FAILED"]:
                break
            time.sleep(0.25)

        final_status = bulk_service.get_batch_status(batch_id, user_id=user_id)
        assert final_status["total_documents"] == 3
        assert (final_status["completed_count"] + final_status["review_count"]) == 2
        assert final_status["failed_count"] == 1
        assert final_status["status"] == "COMPLETED_WITH_REVIEW"

        # Check per-job results
        jobs = {j["filename"]: j for j in final_status["jobs"]}
        assert jobs["valid_invoice_1.txt"]["status"] in ["COMPLETED", "REVIEW_REQUIRED"]
        assert jobs["valid_invoice_1.txt"]["total_kg_co2e"] > 0
        assert jobs["corrupt_empty.txt"]["status"] == "FAILED"
        assert jobs["valid_invoice_2.txt"]["status"] in ["COMPLETED", "REVIEW_REQUIRED"]
        assert jobs["valid_invoice_2.txt"]["total_kg_co2e"] > 0
