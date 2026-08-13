from services.emission_factor_service import EmissionFactorService, EmissionFactorMatch

class MaterialMatchingService:
    """
    Service for mapping raw material descriptions to standardized emission factors
    via the centralized EmissionFactorService singleton.
    """
    def __init__(self, factor_service: EmissionFactorService = None):
        self.factor_service = factor_service or EmissionFactorService.get_instance()

    def match_material(self, material: str, scope: str, unit: str, region: str) -> EmissionFactorMatch:
        """
        Runs multi-tiered semantic matching to find the best-matched factor.
        """
        return self.factor_service.get_factor(material, scope=scope, unit=unit, region=region)
