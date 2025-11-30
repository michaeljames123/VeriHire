SUSPICIOUS_KEYWORDS = [
    "money transfer", "western union", "paypal", "id upload", "bank account", "personal info"
]

def suspicious_oov_check(input_text, vectorizer):
    """
    Compute OOV fraction and detect suspicious keywords
    """
    words = input_text.split()
    vector_vocab = set(vectorizer.get_feature_names_out())
    
    oov_count = sum(1 for w in words if w not in vector_vocab)
    oov_fraction = oov_count / len(words) if words else 0
    
    keyword_flag = any(k in input_text.lower() for k in SUSPICIOUS_KEYWORDS)
    
    return oov_fraction, keyword_flag
