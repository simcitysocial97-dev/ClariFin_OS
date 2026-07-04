"""
Base Extractor Interface
========================
Defines the protocol and data structures for PDF statement extraction.

All extractors (Legacy, Docling, future implementations) must conform
to the ExtractorProtocol interface and return ExtractedStatement objects.
"""

from typing import Dict, List, Optional, Protocol, Any
from dataclasses import dataclass, field


@dataclass
class ExtractedStatement:
    """
    Standardized output structure for all extractors.
    
    This dataclass ensures all extractors return data in a consistent
    format that can be processed by the staging and validation pipeline.
    """
    bank: str
    """Detected bank name (e.g., 'HDFC Bank', 'ICICI Bank')."""
    
    pages: List[int]
    """List of page numbers that contained transaction data."""
    
    opening_balance: Optional[float]
    """Opening balance in rupees (positive = debit balance, negative = credit)."""
    
    closing_balance: Optional[float]
    """Closing balance in rupees (positive = debit balance, negative = credit)."""
    
    normalized_rows: List[Dict[str, Any]]
    """List of normalized transaction rows. Each row should have:
    - date: str (original date string)
    - date_iso: str (ISO format YYYY-MM-DD)
    - description: str
    - debit_paise: int (0 if credit)
    - credit_paise: int (0 if debit)
    - balance_paise: Optional[int] (running balance if available)
    - raw: Dict (original row data for debugging)
    """
    
    raw_json: Dict[str, Any] = field(default_factory=dict)
    """Original extraction output for debugging and forensic analysis."""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional extraction metadata:
    - extractor: str ('legacy', 'docling')
    - strategy: str (extraction strategy used)
    - processing_time_ms: int
    - warnings: List[str]
    """
    
    def to_staging_format(self) -> Dict[str, Any]:
        """Convert to format expected by staging database."""
        return {
            'bank': self.bank,
            'pages': self.pages,
            'opening_balance_paise': int(self.opening_balance * 100) if self.opening_balance else None,
            'closing_balance_paise': int(self.closing_balance * 100) if self.closing_balance else None,
            'transactions': self.normalized_rows,
            'extractor': self.metadata.get('extractor', 'unknown'),
            'strategy': self.metadata.get('strategy'),
        }


class ExtractorProtocol(Protocol):
    """
    Protocol defining the extractor interface.
    
    All extractors must implement this interface to be used by the
    extraction factory and the imports router.
    """
    
    def extract(self, pdf_path: str) -> ExtractedStatement:
        """
        Extract transactions and metadata from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file to extract from.
            
        Returns:
            ExtractedStatement containing all extracted data.
            
        Raises:
            RuntimeError: If the extractor is not properly configured
                         (e.g., docling not installed when using DoclingExtractor).
            ExtractionError: If extraction fails due to PDF format issues.
        """
        ...
    
    @property
    def name(self) -> str:
        """Return the extractor name for logging and debugging."""
        ...


class ExtractionError(Exception):
    """Raised when PDF extraction fails."""
    pass
