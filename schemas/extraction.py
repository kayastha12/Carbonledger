from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class FieldSource(BaseModel):
    type: str  # REAL_DOCUMENT, PDF_EMBEDDED_TEXT, REAL_OCR, NOT_FOUND, ANNOTATION, MOCK, GROUND_TRUTH
    method: Optional[str] = None
    page: Optional[int] = None
    bbox: Optional[List[float]] = None
    raw_text: Optional[str] = None
    confidence: float = 0.0

class ExtractedField(BaseModel):
    value: Any
    original_value: Optional[str] = None
    normalized_value: Optional[Any] = None
    confidence: float
    source: FieldSource
    status: str = "extracted" # extracted, conflict, not_found

class MaterialData(BaseModel):
    original: str
    normalized: str
    category: str
    confidence: float

class QuantityData(BaseModel):
    value: float
    unit: str

class WeightData(BaseModel):
    value: float
    unit: str

class EnergyData(BaseModel):
    type: str
    quantity: QuantityData

class FuelData(BaseModel):
    type: str
    quantity: QuantityData

class TransportData(BaseModel):
    mode: str
    origin: Optional[str] = None
    destination: Optional[str] = None
    distance: Optional[QuantityData] = None

class SupplierData(BaseModel):
    name: str
    country: Optional[str] = None

class LocationData(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    country_of_origin: Optional[str] = None
    country_of_destination: Optional[str] = None

class FinancialData(BaseModel):
    currency: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total_amount: Optional[float] = None

class ExtractionWarning(BaseModel):
    field: str
    message: str
    severity: str = "warning"

class ProcessingMetadata(BaseModel):
    mode: str = "REAL"
    ocr_engine: str = "unknown"
    used_mock: bool = False
    used_annotation: bool = False
    used_ground_truth: bool = False

class ExtractionResult(BaseModel):
    document_id: str
    document_type: str
    metadata: Dict[str, Optional[ExtractedField]] = {}
    supplier: Optional[SupplierData] = None
    customer: Optional[Dict[str, Any]] = None
    items: Optional[List[Dict[str, Any]]] = None
    transport: Optional[TransportData] = None
    energy: Optional[EnergyData] = None
    fuel: Optional[FuelData] = None
    financial: Optional[FinancialData] = None
    warnings: List[ExtractionWarning] = []
    status: str = "success"
    requires_review: bool = False
    processing: Optional[ProcessingMetadata] = None


class CompanyRecord(BaseModel):
    name: Optional[str] = None
    company_id: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    facility: Optional[str] = None


class SupplierRecord(BaseModel):
    name: Optional[str] = None
    supplier_id: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None


class ActivityRecord(BaseModel):
    activity_type: Optional[str] = None
    scope: Optional[str] = None
    category: Optional[str] = None
    material: Optional[str] = None
    product: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    fuel_type: Optional[str] = None
    energy_type: Optional[str] = None
    distance: Optional[float] = None
    distance_unit: Optional[str] = None
    weight: Optional[float] = None
    weight_unit: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    transport_mode: Optional[str] = None
    consumption: Optional[float] = None
    consumption_unit: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    country: Optional[str] = None
    state: Optional[str] = None
    grid_region: Optional[str] = None


class FinancialRecord(BaseModel):
    amount: Optional[float] = None
    currency: Optional[str] = None


class EmissionFactorRecord(BaseModel):
    factor_required: bool = True
    factor_source: Optional[str] = None
    factor_value: Optional[float] = None
    factor_unit: Optional[str] = None


class CarbonCalculationRecord(BaseModel):
    calculation_ready: bool = False
    missing_fields: List[str] = []


class ConfidenceRecord(BaseModel):
    overall: float = 0.0
    level: str = "LOW"


class ValidationRecord(BaseModel):
    status: str = "UNKNOWN"
    anomalies: List[Dict[str, Any]] = []


class CbamRecord(BaseModel):
    cn_code: Optional[str] = None
    hs_code: Optional[str] = None
    hsn_code: Optional[str] = None
    commodity_code: Optional[str] = None
    product_description: Optional[str] = None
    material: Optional[str] = None
    product_category: Optional[str] = None
    country_of_origin: Optional[str] = None
    country_of_production: Optional[str] = None
    country_of_dispatch: Optional[str] = None
    country_of_destination: Optional[str] = None
    export_country: Optional[str] = None
    import_country: Optional[str] = None
    supplier: Optional[str] = None
    producer: Optional[str] = None
    installation: Optional[str] = None
    production_facility: Optional[str] = None
    net_mass: Optional[float] = None
    gross_mass: Optional[float] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    direct_emissions: Optional[float] = None
    indirect_emissions: Optional[float] = None
    embedded_emissions: Optional[float] = None
    specific_embedded_emissions: Optional[float] = None
    total_embedded_emissions: Optional[float] = None
    co2: Optional[float] = None
    co2e: Optional[float] = None
    ghg: Optional[float] = None
    emission_factor: Optional[float] = None
    emission_factor_source: Optional[str] = None
    production_route: Optional[str] = None
    manufacturing_process: Optional[str] = None
    process_type: Optional[str] = None
    precursor_material: Optional[str] = None
    precursor_quantity: Optional[float] = None
    electricity_consumed: Optional[float] = None
    electricity_source: Optional[str] = None
    electricity_mix: Optional[str] = None
    grid_factor: Optional[float] = None
    renewable_electricity: Optional[float] = None
    supplier_declared_emissions: Optional[float] = None
    methodology: Optional[str] = None
    reporting_period: Optional[str] = None
    verification_status: Optional[str] = None
    verification_body: Optional[str] = None
    calculation_method: Optional[str] = None
    cbam_ready: bool = False
    missing_fields: List[str] = []
    cbam_completeness: float = 0.0


class CarbonActivityRecord(BaseModel):
    document_id: str
    company: CompanyRecord
    supplier: SupplierRecord
    activity: ActivityRecord
    financial: FinancialRecord
    emission_factor: EmissionFactorRecord = Field(default_factory=EmissionFactorRecord)
    carbon_calculation: CarbonCalculationRecord
    provenance: Dict[str, Any] = {}
    confidence: ConfidenceRecord
    validation: ValidationRecord
    cbam: CbamRecord = Field(default_factory=CbamRecord)
    unit_normalization_audit: Dict[str, Any] = {}

