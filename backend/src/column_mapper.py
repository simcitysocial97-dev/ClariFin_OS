"""
Map PDF column names to standard transaction fields.
Uses FUZZY MATCHING, not regex.
"""
from difflib import SequenceMatcher
from typing import Dict, Optional, List


class ColumnMapper:
    """Map various column names to standard fields"""
    
    # Standard field names we want to extract
    STANDARD_FIELDS = ['date', 'description', 'amount', 'debit', 'credit']
    
    # Known column name variations (lowercase)
    COLUMN_ALIASES = {
        'date': [
            'date', 'transaction date', 'txn date', 'posting date', 
            'trans date', 'value date', 'date of transaction'
        ],
        'description': [
            'description', 'particulars', 'narration', 'details', 
            'transaction details', 'transaction description', 'trans description',
            'description of transaction'
        ],
        'amount': [
            'amount', 'transaction amount', 'txn amount', 'amount (in rs.)',
            'amount(in rs.)', 'amount inr', 'total'
        ],
        'debit': [
            'debit', 'dr', 'withdrawal', 'debit amount', 'dr amount',
            'debits', 'dr.'
        ],
        'credit': [
            'credit', 'cr', 'deposit', 'credit amount', 'cr amount',
            'credits', 'cr.'
        ],
    }
    
    # Similarity threshold for fuzzy matching
    SIMILARITY_THRESHOLD = 0.7
    
    def map_columns(self, df_columns: List[str]) -> Dict[str, str]:
        """
        Map DataFrame columns to standard field names.
        Returns dict: {standard_field: actual_column_name}
        """
        mapping = {}
        
        for col in df_columns:
            col_lower = str(col).lower().strip()
            
            # Skip metadata columns
            if col.startswith('_'):
                continue
            
            # Find best match
            best_match = self._find_best_match(col_lower)
            if best_match:
                # Don't overwrite existing mappings
                if best_match not in mapping:
                    mapping[best_match] = col
        
        return mapping
    
    def _find_best_match(self, column_name: str) -> Optional[str]:
        """Find which standard field this column matches"""
        
        best_field = None
        best_score = 0
        
        for standard_field, aliases in self.COLUMN_ALIASES.items():
            for alias in aliases:
                score = self._similarity(column_name, alias)
                
                if score > best_score:
                    best_score = score
                    best_field = standard_field
        
        if best_score >= self.SIMILARITY_THRESHOLD:
            return best_field
        
        return None
    
    def _similarity(self, s1: str, s2: str) -> float:
        """
        Calculate similarity between two strings.
        Uses multiple matching strategies.
        """
        
        # Normalize
        s1 = s1.lower().strip()
        s2 = s2.lower().strip()
        
        # Exact match
        if s1 == s2:
            return 1.0
        
        # Contains match
        if s2 in s1 or s1 in s2:
            return 0.9
        
        # Fuzzy match using SequenceMatcher
        ratio = SequenceMatcher(None, s1, s2).ratio()
        
        # Also check similarity after removing common words
        s1_clean = self._remove_common_words(s1)
        s2_clean = self._remove_common_words(s2)
        
        if s1_clean and s2_clean:
            clean_ratio = SequenceMatcher(None, s1_clean, s2_clean).ratio()
            ratio = max(ratio, clean_ratio)
        
        return ratio
    
    def _remove_common_words(self, s: str) -> str:
        """Remove common words from string for better matching"""
        
        common_words = ['of', 'the', 'in', 'for', 'transaction', 'amount', 'rs', 'rs.']
        
        words = s.split()
        filtered = [w for w in words if w not in common_words]
        
        return ' '.join(filtered)
    
    def get_missing_fields(self, mapping: Dict[str, str]) -> List[str]:
        """Get list of standard fields not found in mapping"""
        
        return [f for f in self.STANDARD_FIELDS if f not in mapping]
    
    def has_required_fields(self, mapping: Dict[str, str]) -> bool:
        """Check if mapping has at least date and one amount field"""
        
        has_date = 'date' in mapping
        has_amount = any(f in mapping for f in ['amount', 'debit', 'credit'])
        
        return has_date and has_amount