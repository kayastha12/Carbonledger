import random
import logging

logger = logging.getLogger("ERPConnectors")

class ERPConnectorService:
    def __init__(self, workflow_pipeline=None):
        self.pipeline = workflow_pipeline

    def sync_sap_s4hana(self, connection_params):
        logger.info("Initializing SAP S/4HANA OData OConnection...")
        # Simulate scheduled batch pull
        records = [
            "=== CarbonLedger ERP Document === | Document Type: Invoice | Reference Number: SAP-INV-101 | Date: 2026-07-01 | Company ID: 10 | Supplier ID: 231 | Total Value: 45000.0 | Language: English |",
            "=== CarbonLedger ERP Document === | Document Type: Purchase Order | Reference Number: SAP-PO-882 | Date: 2026-07-02 | Company ID: 10 | Supplier ID: 940 | Total Value: 125000.0 | Language: English |"
        ]
        sync_results = []
        for r in records:
            if self.pipeline:
                res = self.pipeline.run_document_audit_pipeline(r)
                sync_results.append(res)
        logger.info(f"SAP S/4HANA sync completed. Synced {len(sync_results)} transactions.")
        return sync_results

    def sync_oracle_erp(self, api_endpoint, token):
        logger.info("Connecting to Oracle Integration Cloud REST endpoints...")
        record = "=== CarbonLedger ERP Document === | Document Type: Packing List | Reference Number: ORCL-FREIGHT-99 | Date: 2026-07-05 | Company ID: 12 | Supplier ID: 412 | Total Value: 8500.0 | Language: English |"
        if self.pipeline:
            res = self.pipeline.run_document_audit_pipeline(record)
            return [res]
        return []

    def sync_ms_dynamics(self, client_id, client_secret):
        logger.info("Connecting to Microsoft Dynamics 365 Dataverse API...")
        record = "=== CarbonLedger ERP Document === | Document Type: Electricity Bill | Reference Number: DYN-UTIL-8812 | Date: 2026-07-06 | Company ID: 15 | Supplier ID: 101 | Total Value: 4320.12 | Language: German |"
        if self.pipeline:
            res = self.pipeline.run_document_audit_pipeline(record)
            return [res]
        return []

    def sync_odoo(self, db_name, user, password):
        logger.info("Connecting to Odoo XML-RPC / JSON-RPC server...")
        record = "=== CarbonLedger ERP Document === | Document Type: Water Bill | Reference Number: ODOO-UTIL-9021 | Date: 2026-07-07 | Company ID: 22 | Supplier ID: 881 | Total Value: 812.90 | Language: French |"
        if self.pipeline:
            res = self.pipeline.run_document_audit_pipeline(record)
            return [res]
        return []

    def sync_zoho_books(self, org_id, authtoken):
        logger.info("Ingesting records from Zoho Books OAuth API...")
        record = "=== CarbonLedger ERP Document === | Document Type: Invoice | Reference Number: ZOHO-INV-3012 | Date: 2026-07-08 | Company ID: 26 | Supplier ID: 301 | Total Value: 24500.00 | Language: English |"
        if self.pipeline:
            res = self.pipeline.run_document_audit_pipeline(record)
            return [res]
        return []

    def ingest_webhook_payload(self, source_system, payload):
        """
        Ingest webhook payloads dynamically and audit them via multi-agent nodes.
        """
        logger.info(f"Ingesting webhook payload from {source_system}...")
        
        # Convert JSON keys to normalized format
        doc_type = payload.get("document_type", "Invoice")
        ref_num = payload.get("reference_number", f"WEB-{random.randint(1000,9999)}")
        date = payload.get("date", "2026-07-01")
        company = payload.get("company_id", "1")
        supplier = payload.get("supplier_id", "1")
        val = payload.get("total_value", "1000")
        lang = payload.get("language", "English")
        
        normalized_ocr = (
            f"=== CarbonLedger ERP Document === | Document Type: {doc_type} | "
            f"Reference Number: {ref_num} | Date: {date} | Company ID: {company} | "
            f"Supplier ID: {supplier} | Total Value: {val} | Language: {lang} |"
        )
        
        if self.pipeline:
            res = self.pipeline.run_document_audit_pipeline(normalized_ocr)
            return {"status": "success", "audit_result": res}
        return {"status": "success", "raw_ingested": normalized_ocr}

if __name__ == "__main__":
    from models.document_classifier import DocumentClassifier
    from models.ner_extractor import NERExtractor
    from services.matching_service import MatchingService
    from services.calculation_engine import CalculationEngine
    from services.recommendation_engine import RecommendationEngine
    from services.autonomous_agents import AutonomousWorkflow

    cls_model = DocumentClassifier()
    ner_model = NERExtractor()
    match_service = MatchingService()
    calc_engine = CalculationEngine()
    rec_engine = RecommendationEngine()
    
    wf = AutonomousWorkflow(cls_model, ner_model, match_service, calc_engine, rec_engine)
    connector = ERPConnectorService(wf)
    
    # Test webhook
    payload = {"document_type": "Invoice", "total_value": 500, "company_id": "4", "supplier_id": "87"}
    res = connector.ingest_webhook_payload("QuickBooks", payload)
    print("Webhook Ingestion Result:", res["status"])
