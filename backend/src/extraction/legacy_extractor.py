"""
Legacy Extractor Wrapper
========================
Wraps the existing StatementExtractor and MetadataExtractor to conform
to the ExtractorProtocol interface.

This ensures backward compatibility while allowing the new extraction
framework to work with existing code.
"""

import time
from typing import Dict, List, Optional, Any

from .base_extractor import ExtractedStatement, ExtractionError

# Import existing extractors
import sys
from pathlib import Path

# Add parent src directory to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from statement_extractor import StatementExtractor, ExtractionError as LegacyExtractionError
from metadata_extractor import MetadataExtractor
from utils import parse_date_to_iso

# Import bank detector
from .bank_detector import detect_bank_from_pdf


class LegacyExtractor:
    """
    Wrapper around the existing Camelot-based extraction pipeline.
    
    This extractor uses the production-proven StatementExtractor for
    transaction extraction and MetadataExtractor for balance/metadata.
    """
    
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    @property
    def name(self) -> str:
        return "legacy"
    
    def extract(self, pdf_path: str) -> ExtractedStatement:
        """
        Extract statement using the legacy pipeline.
        
        Args:
            pdf_path: Path to the PDF file.
            
        Returns:
            ExtractedStatement with standardized structure.
            
        Raises:
            ExtractionError: If extraction fails.
        """
        start_time = time.time()
        warnings = []
        
        try:
            # Step 1: Detect bank from PDF text
            try:
                detected_bank = detect_bank_from_pdf(pdf_path, max_pages=3)
                bank = detected_bank if detected_bank else "Unknown"
            except Exception:
                bank = "Unknown"
            
            # Step 2: Extract metadata (bank, balances, etc.)
            metadata_extractor = MetadataExtractor(pdf_path, bank=bank)
            metadata = metadata_extractor.extract()
            
            # Use detected bank if metadata didn't find one
            if bank == "Unknown" and metadata.get('bank_name'):
                bank = metadata.get('bank_name')
            
            # Step 3: Extract transactions
            statement_extractor = StatementExtractor(pdf_path, debug=self.debug)
            tx_result = statement_extractor.extract()
            
            transactions = tx_result.get("transactions", [])
            
            # Step 4: Get opening/closing balances
            # Priority: metadata extractor values, then None
            opening_balance = metadata.get('opening_balance')
            closing_balance = metadata.get('total_amount_due')
            
            # Step 5: Normalize transactions to common format
            normalized_rows = self._normalize_transactions(transactions)
            
            # Step 6: Determine pages with transaction data
            pages = self._extract_pages(tx_result)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return ExtractedStatement(
                bank=bank,
                pages=pages,
                opening_balance=opening_balance,
                closing_balance=closing_balance,
                normalized_rows=normalized_rows,
                raw_json={
                    'metadata': metadata,
                    'transactions': tx_result,
                },
                metadata={
                    'extractor': 'legacy',
                    'strategy': tx_result.get('strategy'),
                    'extraction_method': tx_result.get('extraction_method'),
                    'transaction_count': len(transactions),
                    'processing_time_ms': processing_time_ms,
                    'warnings': warnings,
                }
            )
            
        except LegacyExtractionError as e:
            raise ExtractionError(f"Legacy extraction failed: {e}") from e
        except Exception as e:
            raise ExtractionError(f"Unexpected error in legacy extraction: {e}") from e
    
    def _normalize_transactions(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert legacy transaction format to standardized normalized rows.
        
        Legacy format: {date, description, amount, type, raw}
        Normalized format: {date, date_iso, description, debit_paise, credit_paise, balance_paise, raw}
        """
        normalized = []
        
        for txn in transactions:
            amount_str = txn.get('amount', '0')
            txn_type = txn.get('type', '').lower()
            
            # Parse amount
            try:
                # Remove commas and convert
                amount_clean = str(amount_str).replace(',', '').strip()
                amount_float = float(amount_clean) if amount_clean else 0.0
            except (ValueError, TypeError):
                amount_float = 0.0
            
            amount_paise = int(round(amount_float * 100))
            
            # Determine debit/credit
            debit_paise = amount_paise if txn_type == 'debit' else 0
            credit_paise = amount_paise if txn_type == 'credit' else 0
            
            # Handle negative amounts (credit balances)
            if amount_float < 0:
                # Negative amount in legacy format usually means credit
                if txn_type == 'debit':
                    debit_paise = 0
                    credit_paise = abs(amount_paise)
                elif txn_type == 'credit':
                    debit_paise = 0
                    credit_paise = abs(amount_paise)
            
            normalized.append({
                'date': txn.get('date', ''),
                'date_iso': parse_date_to_iso(txn.get('date', '')),
                'description': txn.get('description', ''),
                'debit_paise': debit_paise,
                'credit_paise': credit_paise,
                'balance_paise': None,  # Legacy extractor doesn't capture running balance
                'raw': txn.get('raw', {}),
            })
        
        return normalized
    
    def _extract_pages(self, tx_result: Dict[str, Any]) -> List[int]:
        """Extract page numbers from transaction result."""
        pages = []
        
        # Get selected page from result
        selected_page = tx_result.get('selected_page')
        if selected_page is not None:
            pages.append(selected_page)
        
        # If we have statement period info, we might have covered multiple pages
        # For now, we return the primary page where the main table was found
        if not pages:
            pages = [0]  # Default to first page
        
        return pages
