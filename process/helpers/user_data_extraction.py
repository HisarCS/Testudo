# helpers/user_data_extraction.py
import spacy
import re
import json
from typing import List, Dict, Any

nlp = spacy.load("en_core_web_sm")

def extract_all_info(text: str) -> List[Dict[str, Any]]:
    """
    Extract category-value pairs from text, including general user info (name, age, etc.)
    and dynamic favorite declarations. If no regex patterns match, fallback to a simple 
    spaCy-based verb/adjective detector for sentences that start with "I".
    """
    pairs = []
    boundary = r"(?=\s*(?:,|\.|!|\?|\band\b)|$)"
    
    patterns = [
        # -- General User Info Patterns --
        # Name
        (r"my name is\s+([a-zA-Z\s]+?)" + boundary, "name", "{value}"),
        (r"i go by\s+([a-zA-Z\s]+?)" + boundary, "name", "{value}"),

        # Age
        (r"i am\s+(\d{1,3})\s*years? old" + boundary, "age", "{value}"),
        (r"i'm\s+(\d{1,3})" + boundary, "age", "{value}"),
        (r"my age is\s+(\d{1,3})" + boundary, "age", "{value}"),

        # Gender
        (r"i am\s+(male|female|non[-\s]?binary|other)" + boundary, "gender", "{value}"),
        (r"my gender is\s+(male|female|non[-\s]?binary|other)" + boundary, "gender", "{value}"),

        # Location / Origin
        (r"i live in\s+([a-zA-Z\s]+?)" + boundary, "location", "{value}"),
        (r"my city is\s+([a-zA-Z\s]+?)" + boundary, "location", "{value}"),
        (r"i come from\s+([a-zA-Z\s]+?)" + boundary, "origin", "{value}"),
        (r"i'm from\s+([a-zA-Z\s]+?)" + boundary, "origin", "{value}"),
        (r"i moved to\s+([a-zA-Z\s]+?)" + boundary, "moved_to", "{value}"),

        # Relationship Status
        (r"i am\s+(single|married|divorced|engaged|in a relationship)" + boundary, "relationship_status", "{value}"),
        
        # Social Media
        (r"my instagram is\s+(@[\w\d]+)" + boundary, "instagram", "{value}"),
        (r"my twitter is\s+(@[\w\d]+)" + boundary, "twitter", "{value}"),
        (r"my linkedin is\s+([a-zA-Z0-9_\-]+)" + boundary, "linkedin", "{value}"),
        
        # Contact Information
        (r"my email is\s+([\w\.-]+@[\w\.-]+\.\w+)" + boundary, "email", "{value}"),
        (r"you can reach me at\s+([\d\+\-\s]+)" + boundary, "phone", "{value}"),

        # Hobbies and Interests
        (r"i like\s+([a-zA-Z\s,]+?)" + boundary, "likes", "{value}"),
        (r"i love\s+([a-zA-Z\s,]+?)" + boundary, "loves", "{value}"),
        (r"my hobbies include\s+([a-zA-Z\s,]+?)" + boundary, "hobbies", "{value}"),

        # More Personal Preferences
        (r"i prefer\s+([a-zA-Z\s]+?)" + boundary, "preference", "{value}"),
        (r"my favorite music genre is\s+([a-zA-Z\s]+?)" + boundary, "favorite_music", "{value}"),
        
        # Health Conditions
        (r"i have\s+([a-zA-Z\s]+?)" + boundary, "health_condition", "{value}"),
        
        # -- Dynamic Favorites Patterns --
        (r"my favorite (\w+) is ([\w\s]+?)(?=[,.!?]|$)", "favorite_{category}", "{value}"),
        (r"my favourite (\w+) is ([\w\s]+?)(?=[,.!?]|$)", "favorite_{category}", "{value}"),
        
        (r"my (\w+) is ([\w\s]+?)(?=[,.!?]|$)", "{category}", "{value}"),
        (r"my (\w+) are ([\w\s]+?)(?=[,.!?]|$)", "{category}", "{value}"),
        
        (r"I (\w+) in ([\w\s]+?)(?=[,.!?]|$)", "{category}", "{value}"),
        (r"I (\w+) at ([\w\s]+?)(?=[,.!?]|$)", "{category}", "{value}"),
        (r"I (\w+) from ([\w\s]+?)(?=[,.!?]|$)", "{category}", "{value}"),
        (r"I (\w+) as ([\w\s]+?)(?=[,.!?]|$)", "{category}", "{value}"),
        (r"I (\w+) to ([\w\s]+?)(?=[,.!?]|$)", "{category}", "{value}"),
        
        (r"i'm\s+([a-zA-Z\s]+?)" + boundary, "current_user_adj", "{value}"),
        (r"i am\s+([a-zA-Z\s]+?)" + boundary, "current_user_adj", "{value}"),
        (r"i was\s+([a-zA-Z\s]+?)" + boundary, "past_user_adj", "{value}"),
        (r"we were\s+([a-zA-Z\s]+?)" + boundary, "users_adj", "{value}"),
        
        (r"he is\s+([a-zA-Z\s]+?)" + boundary, "other_current_user_adj", "{value}"),
        (r"he was\s+([a-zA-Z\s]+?)" + boundary, "other_past_user_adj", "{value}"),
        (r"she is\s+([a-zA-Z\s]+?)" + boundary, "other_current_user_adj", "{value}"),
        (r"she was\s+([a-zA-Z\s]+?)" + boundary, "other_past_user_adj", "{value}"),
        (r"they were\s+([a-zA-Z\s]+?)" + boundary, "they_user_adj", "{value}"),
    ]
    
    extracted_pairs = []

    # Regex-based extraction
    for pattern, category_template, value_template in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            if "{category}" in category_template:
                dynamic_category = match.group(1).strip().replace(" ", "_")
                value = match.group(2).strip()
                category = category_template.replace("{category}", dynamic_category)
            else:
                value = match.group(1).strip()
                category = category_template
            extracted_pairs.append((category, value))

    # If nothing was extracted, try spaCy fallback
    if not extracted_pairs:
        doc = nlp(text.lower().strip())

        if text.lower().startswith("i") or text.lower().startswith("i'm"):
            for token in doc:
                if token.pos_ == "VERB" and token.dep_ == "ROOT":
                    dobj = [child.text for child in token.children if child.dep_ in ["dobj", "attr", "acomp", "pobj"]]
                    if dobj:
                        extracted_pairs.append((token.lemma_ + "s", " ".join(dobj)))

            if not extracted_pairs:
                for token in doc:
                    if token.dep_ == "ROOT" and token.lemma_.lower() in ["be"] and token.pos_ in ["AUX", "VERB"]:
                        adj_kids = [child.text for child in token.children if child.pos_ == "ADJ"]
                        for adj in adj_kids:
                            extracted_pairs.append(("current_user_adj", adj))

    return extracted_pairs
