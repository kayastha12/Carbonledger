from pipeline.normalization import NormalizationEngine

class EntityNormalizer:
    def __init__(self):
        self.engine = NormalizationEngine()

    def normalize_material(self, text: str) -> dict:
        res = self.engine.normalize_material(text)
        return {
            "original": res["original_value"],
            "normalized": res["normalized_value"] or text,
            "category": res["category"] or "Other",
            "confidence": res["confidence"],
            "requires_review": res["requires_review"]
        }

    def normalize_fuel(self, text: str) -> dict:
        res = self.engine.normalize_fuel(text)
        return {
            "original": res["original_value"],
            "normalized": res["normalized_value"] or text,
            "category": res["category"] or "Other",
            "confidence": res["confidence"],
            "requires_review": res["requires_review"]
        }

    def normalize_transport(self, text: str) -> str:
        res = self.engine.normalize_transport(text)
        return res["normalized_value"] or "Unknown"

    def normalize_unit(self, text: str) -> str:
        return self.engine.normalize_unit(text) or text

    def normalize_value(self, text: str) -> tuple:
        val, unit, audit = self.engine.normalize_value(text)
        return val, unit
