import re

def clean_text(text):
    """
    Lowercase, remove punctuation, normalize whitespace
    """
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
