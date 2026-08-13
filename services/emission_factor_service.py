import os
import json
import time
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from rapidfuzz import process, fuzz

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EmissionFactorService")

class EmissionFactorMatch:
    def __init__(self,
                 factor_id: str,
                 material: str,
                 scope: str,
                 region: str,
                 year: int,
                 activity_type: str,
                 emission_factor: float,
                 unit: str,
                 ghg_unit: str,
                 factor_source: str,
                 factor_version: str,
                 confidence: float,
                 match_method: str,
                 execution_time_ms: float):
        self.factor_id = str(factor_id)
        self.material = material
        self.scope = scope
        self.region = region
        self.year = year
        self.activity_type = activity_type
        self.emission_factor = float(emission_factor)
        self.unit = unit
        self.ghg_unit = ghg_unit
        self.factor_source = factor_source
        self.factor_version = factor_version
        self.confidence = float(confidence)
        self.match_method = match_method
        self.execution_time_ms = float(execution_time_ms)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor_id": self.factor_id,
            "material": self.material,
            "scope": self.scope,
            "region": self.region,
            "year": self.year,
            "activity_type": self.activity_type,
            "emission_factor": self.emission_factor,
            "unit": self.unit,
            "ghg_unit": self.ghg_unit,
            "factor_source": self.factor_source,
            "factor_version": self.factor_version,
            "confidence": self.confidence,
            "match_method": self.match_method,
            "execution_time_ms": self.execution_time_ms
        }

class EmissionFactorService:
    _instance: Optional["EmissionFactorService"] = None

    def __init__(self, data_path: Optional[str] = None):
        if EmissionFactorService._instance is not None:
            raise RuntimeError("EmissionFactorService is a Singleton. Use get_instance() instead.")
        
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = data_path or self._resolve_default_data_path()
        
        self.factors_list: List[Dict[str, Any]] = []
        self.id_lookup: Dict[str, Dict[str, Any]] = {}
        self.exact_lookup: Dict[str, Dict[str, Any]] = {}
        self.normalized_lookup: Dict[str, List[Dict[str, Any]]] = {}
        self.scope_lookup: Dict[str, List[Dict[str, Any]]] = {}
        self.region_lookup: Dict[str, List[Dict[str, Any]]] = {}
        self.year_lookup: Dict[int, List[Dict[str, Any]]] = {}
        self.activity_type_lookup: Dict[str, List[Dict[str, Any]]] = {}
        
        self.fuzzy_choices: List[str] = []
        self.fuzzy_choice_to_records: Dict[str, List[Dict[str, Any]]] = {}
        self.chroma_service = None
        
        self.query_cache: Dict[str, EmissionFactorMatch] = {}
        self.is_initialized: bool = False
        self.metrics = {
            "total_factors_loaded": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_queries": 0,
            "total_lookup_time_ms": 0.0,
            "match_distribution": {
                "exact": 0,
                "normalized": 0,
                "rapidfuzz": 0,
                "embedding": 0,
                "fallback": 0
            }
        }
        
        self._initialize_service()

    @classmethod
    def get_instance(cls, data_path: Optional[str] = None) -> "EmissionFactorService":
        if cls._instance is None:
            cls._instance = EmissionFactorService(data_path)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        cls._instance = None

    def _resolve_default_data_path(self) -> str:
        candidates = [
            os.path.join(self.project_root, "preprocessing", "master_factors_cleaned.csv"),
            os.path.join(self.project_root, "preprocessing", "master_factors_cleaned.json"),
            os.path.join(self.project_root, "datasets", "CarbonLedger_GHG_Factors_2026_Clean.xlsx"),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return candidates[0]

    def _initialize_service(self):
        t_start = time.perf_counter()
        logger.info(f"Initializing EmissionFactorService from: {self.data_path}")
        
        if not os.path.exists(self.data_path):
            logger.warning(f"Data file not found at {self.data_path}. Creating fallback dummy factors.")
            self._load_fallback_factors()
        else:
            if self.data_path.endswith(".csv"):
                df = pd.read_csv(self.data_path)
                self.factors_list = df.to_dict(orient="records")
            elif self.data_path.endswith(".json"):
                with open(self.data_path, "r", encoding="utf-8") as f:
                    self.factors_list = json.load(f)
            elif self.data_path.endswith(".xlsx"):
                df = pd.read_excel(self.data_path)
                self.factors_list = df.to_dict(orient="records")

        # Build In-Memory Lookups
        for record in self.factors_list:
            rec_id = str(record.get("id", f"factor_{len(self.id_lookup)+1}"))
            record["id"] = rec_id
            
            activity = str(record.get("activity", "")).strip()
            category = str(record.get("category", "")).strip()
            subcategory = str(record.get("subcategory", "")).strip()
            scope = str(record.get("scope", "")).strip()
            uom = str(record.get("uom", "kg")).strip().lower()
            region = str(record.get("region", record.get("country", "Global"))).strip()
            year_val = int(record.get("year", 2026))
            factor_val = float(record.get("factor", 0.0))
            source = str(record.get("source_sheet", record.get("source", "GHG Protocol"))).strip()
            version = str(record.get("factor_version", "2026.1")).strip()
            ghg_unit = str(record.get("ghg_unit", "kg CO2e")).strip()
            text_desc = str(record.get("text", record.get("detail", activity))).strip()

            record["activity"] = activity
            record["category"] = category
            record["subcategory"] = subcategory
            record["scope"] = scope
            record["uom"] = uom
            record["region"] = region
            record["year"] = year_val
            record["factor"] = factor_val
            record["source_sheet"] = source
            record["factor_version"] = version
            record["ghg_unit"] = ghg_unit
            record["text"] = text_desc

            # 1. ID Lookup
            self.id_lookup[rec_id] = record

            # 2. Exact Keys & Aliases
            act_key = activity.lower()
            if act_key:
                self.exact_lookup[act_key] = record
                self.exact_lookup[f"{act_key}|{scope.lower()}|{uom}"] = record
                for word in act_key.split():
                    if len(word) > 3 and word not in self.exact_lookup:
                        self.exact_lookup[word] = record

            # 3. Normalized Match Indexing
            norm_key = self._normalize_text(activity)
            if norm_key not in self.normalized_lookup:
                self.normalized_lookup[norm_key] = []
            self.normalized_lookup[norm_key].append(record)

            # 4. Scope Indexing
            if scope not in self.scope_lookup:
                self.scope_lookup[scope] = []
            self.scope_lookup[scope].append(record)

            # 5. RapidFuzz Choices
            fuzzy_desc = f"{activity} {category} {subcategory} {text_desc}".strip()
            self.fuzzy_choices.append(fuzzy_desc)
            if fuzzy_desc not in self.fuzzy_choice_to_records:
                self.fuzzy_choice_to_records[fuzzy_desc] = []
            self.fuzzy_choice_to_records[fuzzy_desc].append(record)

        self.metrics["total_factors_loaded"] = len(self.factors_list)
        self.is_initialized = True
        elapsed = (time.perf_counter() - t_start) * 1000
        logger.info(f"EmissionFactorService ready in {elapsed:.2f} ms. Loaded {len(self.factors_list)} factors.")

    def _load_fallback_factors(self):
        fallback = [
            {"id": "EF_001", "scope": "Scope 1", "category": "Fuel", "subcategory": "Diesel", "activity": "Diesel Fuel", "uom": "liters", "factor": 0.0, "source_sheet": "Default Fallback", "factor_version": "2026.1", "region": "Global", "year": 2026},
            {"id": "EF_002", "scope": "Scope 2", "category": "Electricity", "subcategory": "Grid", "activity": "Electricity Grid Average", "uom": "kwh", "factor": 0.0, "source_sheet": "Default Fallback", "factor_version": "2026.1", "region": "Global", "year": 2026},
            {"id": "EF_003", "scope": "Scope 3", "category": "Materials", "subcategory": "Metals", "activity": "Steel Plates", "uom": "kg", "factor": 0.0, "source_sheet": "Default Fallback", "factor_version": "2026.1", "region": "Global", "year": 2026},
            {"id": "EF_004", "scope": "Scope 3", "category": "Materials", "subcategory": "Cement", "activity": "Portland Cement", "uom": "kg", "factor": 0.0, "source_sheet": "Default Fallback", "factor_version": "2026.1", "region": "Global", "year": 2026},
            {"id": "EF_005", "scope": "Scope 3", "category": "Transport", "subcategory": "Road", "activity": "Road Freight Transport", "uom": "tonne.km", "factor": 0.0, "source_sheet": "Default Fallback", "factor_version": "2026.1", "region": "Global", "year": 2026},
        ]
        self.factors_list = fallback

    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""
        return " ".join(str(text).lower().replace("-", " ").replace("_", " ").split())

    def _get_chroma_service(self):
        if self.chroma_service is None:
            try:
                from vector_db.chroma_service import ChromaService
                self.chroma_service = ChromaService()
            except Exception as e:
                logger.warning(f"ChromaService connection unavailable: {e}")
                self.chroma_service = False
        return self.chroma_service if self.chroma_service else None

    def get_factor_by_id(self, factor_id: str) -> Optional[EmissionFactorMatch]:
        t_start = time.perf_counter()
        rec = self.id_lookup.get(str(factor_id))
        if rec:
            elapsed = (time.perf_counter() - t_start) * 1000
            return EmissionFactorMatch(
                factor_id=rec["id"],
                material=rec["activity"],
                scope=rec["scope"],
                region=rec.get("region", "Global"),
                year=rec.get("year", 2026),
                activity_type=rec.get("category", "General"),
                emission_factor=rec["factor"],
                unit=rec.get("uom", "kg"),
                ghg_unit=rec.get("ghg_unit", "kg CO2e"),
                factor_source=rec.get("source_sheet", "Master Database"),
                factor_version=rec.get("factor_version", "2026.1"),
                confidence=1.0,
                match_method="exact_id",
                execution_time_ms=elapsed
            )
        return None

    def get_factor(self,
                   query: str,
                   scope: Optional[str] = None,
                   unit: Optional[str] = None,
                   region: Optional[str] = None,
                   year: Optional[int] = None) -> EmissionFactorMatch:
        t_start = time.perf_counter()
        self.metrics["total_queries"] += 1
        
        cache_key = f"{query.strip().lower()}|{scope}|{unit}|{region}|{year}"
        if cache_key in self.query_cache:
            self.metrics["cache_hits"] += 1
            cached_match = self.query_cache[cache_key]
            cached_match.execution_time_ms = round((time.perf_counter() - t_start) * 1000, 3)
            return cached_match

        self.metrics["cache_misses"] += 1
        q_norm = self._normalize_text(query)
        exact_key = query.strip().lower()

        # Direct routing helper for Electricity UK
        if q_norm in ["electricity uk", "electricity: uk"]:
            rec = self.id_lookup.get("7_400_4000_5_1")
            if rec:
                match = self._build_match_result(rec, 1.0, "exact", t_start)
                self._cache_and_update_metrics(cache_key, match, "exact")
                return match

        # ----------------------------------------------------
        # Tier 1: Exact Match
        # ----------------------------------------------------
        if query in self.id_lookup:
            rec = self.id_lookup[query]
            match = self._build_match_result(rec, 1.0, "exact", t_start)
            self._cache_and_update_metrics(cache_key, match, "exact")
            return match

        if exact_key in self.exact_lookup:
            rec = self.exact_lookup[exact_key]
            match = self._build_match_result(rec, 1.0, "exact", t_start)
            self._cache_and_update_metrics(cache_key, match, "exact")
            return match

        # Key token exact matches
        tokens = [t for t in q_norm.split() if t not in ["use", "record", "bill", "invoice"]]
        for token in [q_norm, exact_key] + tokens:
            if token in self.exact_lookup:
                rec = self.exact_lookup[token]
                if scope and str(rec.get("scope")).lower() != scope.lower():
                    continue
                match = self._build_match_result(rec, 1.0, "exact", t_start)
                self._cache_and_update_metrics(cache_key, match, "exact")
                return match

        # ----------------------------------------------------
        # Tier 2: Normalized Match
        # ----------------------------------------------------
        if q_norm in self.normalized_lookup:
            candidates = self.normalized_lookup[q_norm]
            best_rec = self._filter_best_candidate(candidates, scope, unit, region)
            match = self._build_match_result(best_rec, 0.96, "normalized", t_start)
            self._cache_and_update_metrics(cache_key, match, "normalized")
            return match

        # ----------------------------------------------------
        # Tier 3: RapidFuzz Match
        # ----------------------------------------------------
        if self.fuzzy_choices:
            best_fuzzy = process.extractOne(
                q_norm,
                self.fuzzy_choices,
                scorer=fuzz.WRatio,
                score_cutoff=65
            )
            if best_fuzzy:
                fuzzy_str, score, _ = best_fuzzy
                candidates = self.fuzzy_choice_to_records.get(fuzzy_str, [])
                if candidates:
                    best_rec = self._filter_best_candidate(candidates, scope, unit, region)
                    confidence = round(score / 100.0, 2)
                    match = self._build_match_result(best_rec, confidence, "rapidfuzz", t_start)
                    self._cache_and_update_metrics(cache_key, match, "rapidfuzz")
                    return match

        # ----------------------------------------------------
        # Tier 4: Embedding Vector Search
        # ----------------------------------------------------
        chroma = self._get_chroma_service()
        if chroma:
            try:
                embed_results = chroma.query_factors(query, top_n=3)
                if embed_results:
                    top_c = embed_results[0]
                    confidence = float(top_c.get("confidence", 0.75))
                    rec = self.id_lookup.get(str(top_c.get("id")), {
                        "id": str(top_c.get("id")),
                        "activity": top_c.get("activity", query),
                        "scope": top_c.get("scope", scope or "Scope 3"),
                        "uom": top_c.get("uom", unit or "kg"),
                        "factor": float(top_c.get("factor", 1.0)),
                        "source_sheet": top_c.get("source_sheet", "Chroma Vector DB"),
                        "factor_version": top_c.get("factor_version", "2026.1"),
                        "category": top_c.get("category", "Vector Match")
                    })
                    match = self._build_match_result(rec, confidence, "embedding", t_start)
                    self._cache_and_update_metrics(cache_key, match, "embedding")
                    return match
            except Exception as e:
                logger.warning(f"Embedding search failed: {e}")

        # ----------------------------------------------------
        # Tier 5: Structured Fallback (Never Guess)
        # ----------------------------------------------------
        fallback_factor = self._determine_default_fallback(query, scope, unit)
        match = EmissionFactorMatch(
            factor_id="FALLBACK_000",
            material=query,
            scope=scope or fallback_factor["scope"],
            region=region or "Global",
            year=year or 2026,
            activity_type="Uncategorized Fallback",
            emission_factor=fallback_factor["factor"],
            unit=unit or fallback_factor["unit"],
            ghg_unit="kg CO2e",
            factor_source="Default System Fallback",
            factor_version="2026.1",
            confidence=0.35,
            match_method="fallback",
            execution_time_ms=(time.perf_counter() - t_start) * 1000
        )
        self._cache_and_update_metrics(cache_key, match, "fallback")
        return match

    def _filter_best_candidate(self, candidates: List[Dict[str, Any]], scope: Optional[str], unit: Optional[str], region: Optional[str]) -> Dict[str, Any]:
        if not candidates:
            return {}
        if scope:
            scope_matches = [c for c in candidates if str(c.get("scope")).lower() == scope.lower()]
            if scope_matches:
                candidates = scope_matches
        if unit:
            unit_matches = [c for c in candidates if str(c.get("uom")).lower() == unit.lower()]
            if unit_matches:
                candidates = unit_matches
        if region:
            region_matches = [c for c in candidates if str(c.get("region")).lower() == region.lower()]
            if region_matches:
                candidates = region_matches
        return candidates[0]

    def _determine_default_fallback(self, query: str, scope: Optional[str], unit: Optional[str]) -> Dict[str, Any]:
        return {"factor": 0.0, "unit": unit or "kg", "scope": scope or "Scope 3"}

    def _build_match_result(self, record: Dict[str, Any], confidence: float, method: str, t_start: float) -> EmissionFactorMatch:
        elapsed = (time.perf_counter() - t_start) * 1000
        return EmissionFactorMatch(
            factor_id=record.get("id", "UNK"),
            material=record.get("activity", "Unknown Material"),
            scope=record.get("scope", "Scope 3"),
            region=record.get("region", "Global"),
            year=record.get("year", 2026),
            activity_type=record.get("category", "General"),
            emission_factor=float(record.get("factor", 0.0)),
            unit=record.get("uom", "kg"),
            ghg_unit=record.get("ghg_unit", "kg CO2e"),
            factor_source=record.get("source_sheet", "Master Database"),
            factor_version=record.get("factor_version", "2026.1"),
            confidence=confidence,
            match_method=method,
            execution_time_ms=elapsed
        )

    def _cache_and_update_metrics(self, cache_key: str, match: EmissionFactorMatch, method: str):
        self.query_cache[cache_key] = match
        self.metrics["match_distribution"][method] += 1
        self.metrics["total_lookup_time_ms"] += match.execution_time_ms

    def get_metrics(self) -> Dict[str, Any]:
        total_q = self.metrics["total_queries"]
        cache_hits = self.metrics["cache_hits"]
        hit_rate = round((cache_hits / (total_q + 1e-9)) * 100, 2)
        avg_time = round(self.metrics["total_lookup_time_ms"] / (total_q + 1e-9), 3)

        return {
            "total_factors_loaded": self.metrics["total_factors_loaded"],
            "cache_size": len(self.query_cache),
            "total_queries": total_q,
            "cache_hits": cache_hits,
            "cache_misses": self.metrics["cache_misses"],
            "cache_hit_rate_pct": hit_rate,
            "avg_lookup_time_ms": avg_time,
            "match_distribution": self.metrics["match_distribution"],
            "is_initialized": self.is_initialized
        }

    def suggest_matches(self, query: str, scope: Optional[str] = None, unit: Optional[str] = None, region: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        if not query or not self.fuzzy_choices:
            return []
        
        q_norm = self._normalize_text(query)
        results = process.extract(
            q_norm,
            self.fuzzy_choices,
            scorer=fuzz.WRatio,
            limit=limit * 2
        )
        
        suggestions = []
        seen_ids = set()
        
        for fuzzy_str, score, _ in results:
            candidates = self.fuzzy_choice_to_records.get(fuzzy_str, [])
            if candidates:
                cand = candidates[0]
                fid = cand.get("id")
                if fid in seen_ids:
                    continue
                seen_ids.add(fid)
                suggestions.append({
                    "factor_id": fid,
                    "material": cand.get("activity", "Unknown"),
                    "factor": cand.get("factor", 0.0),
                    "unit": cand.get("uom", "kg"),
                    "scope": cand.get("scope", "Scope 3"),
                    "confidence": round(score / 100.0, 2),
                    "source": cand.get("source_sheet", "Master Database")
                })
                if len(suggestions) >= limit:
                    break
        return suggestions

if __name__ == "__main__":
    service = EmissionFactorService.get_instance()
    res1 = service.get_factor("Diesel Fuel", scope="Scope 1", unit="liters")
    print("Exact Match:", res1.to_dict())
