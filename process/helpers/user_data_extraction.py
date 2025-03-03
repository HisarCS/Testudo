# helpers/user_data_extraction.py
import spacy
import re
import json
from typing import List, Dict, Any

nlp = spacy.load("en_core_web_sm")

def extract_all_info(text: str) -> List[Dict[str, str]]:
    """
    Given some text, return a list of (category, value) dictionaries.
    """
    # [Your existing code – truncated for brevity]
    patterns = [
        # Examples: name, age, preferences, dynamic favorites, etc.
        (r"my name is\s+([a-zA-Z\s]+)", "name", "{value}"),
        # ...
    ]
    extracted_pairs = []
    
    # 1) Do regex-based extraction
    for pattern, category_template, value_template in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # handle dynamic categories, etc.
            # ...
            extracted_pairs.append({...})
    
    # 2) If none found, optionally do spaCy fallback
    # ...
    
    # Return as a list of dicts: [{"category": "name", "value": "Alice"}, ...]
    return [{"category": cat, "value": val} for (cat, val) in extracted_pairs]
