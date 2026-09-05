import abc
from schemas.extraction import ExtractionResult
from schemas.document import ClassificationResult, LayoutResult

class BaseExtractor(abc.ABC):
    @abc.abstractmethod
    def extract(
        self,
        document: dict,
        classification: ClassificationResult,
        layout: LayoutResult
    ) -> ExtractionResult:
        """
        Abstract method to extract structured CarbonLedger activity data
        from parsed document text, classification results, and layout elements.
        """
        pass
