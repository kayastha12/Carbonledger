from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

# --- Classification Models ---

class PageClassification(BaseModel):
    page: int
    document_type: str
    confidence: float

class ClassificationResult(BaseModel):
    document_type: str
    confidence: float
    method: str
    scores: Dict[str, float]
    requires_review: bool
    pages: Optional[List[PageClassification]] = None
    overall_document_type: Optional[str] = None
    overall_confidence: Optional[float] = None

# --- Layout & Table Models ---

class LayoutElement(BaseModel):
    type: str  # HEADER, FOOTER, TITLE, KEY_VALUE, TABLE, TOTAL, NOTE, UNKNOWN
    text: str
    bbox: List[float] = Field(..., description="[x0, y0, x1, y1]")
    page: int
    confidence: float = 1.0

class KeyValueBlock(BaseModel):
    type: str = "KEY_VALUE"
    key: str
    value: str
    key_bbox: List[float]
    value_bbox: List[float]
    bbox: List[float]
    page: int
    confidence: float = 1.0

class TableCell(BaseModel):
    text: str
    bbox: List[float]

class TableRow(BaseModel):
    cells: List[TableCell]

class TableHeader(BaseModel):
    text: str
    bbox: List[float]

class Table(BaseModel):
    type: str = "TABLE"
    table_id: str
    bbox: List[float]
    headers: List[TableHeader]
    rows: List[TableRow]
    page: int

class PageLayout(BaseModel):
    page: int
    elements: List[LayoutElement] = []
    key_values: List[KeyValueBlock] = []
    tables: List[Table] = []

class LayoutResult(BaseModel):
    document_id: str
    pages: List[PageLayout] = []
