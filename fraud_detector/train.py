import pandas as pd
import numpy as np
import re
import pickle

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.metrics import classification_report

# -----------------------------
# TEXT CLEANING
# -----------------------------
def clean_text(text):
    text = text.lower()
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# -----------------------------
# FEATURE ENGINEERING
# -----------------------------
def extract_features(df):
    # Salary flags
    df['salary_high'] = df['text'].str.contains(r'[\$₱]\s?(\d{6,})', regex=True).astype(int)

    # Contact info flags
    df['contact_email'] = df['text'].str.contains(r'\b@gmail\.com|\byahoo\.com|\bhotmail\.com', regex=True).astype(int)
    df['contact_phone'] = df['text'].str.contains(r'\b\d{10,11}\b').astype(int)
    df['id_request'] = df['text'].str.contains(r'valid id|gov.t id|government id|send id|upload id', regex=True).astype(int)

    # Benefit count (scammers copy-paste long lists)
    df['benefit_count'] = df['text'].str.count(r'benefit|insurance|allowance|support')

    # Experience vs education mismatch
    df['exp_required'] = df['text'].str.extract(r'(\d+)\+?\s+year', expand=False).fillna(0).astype(int)
    df['edu_mismatch'] = ((df['exp_required'] > 5) & (df['text'].str.contains("no degree|no experience", regex=True))).astype(int)

    # Length of posting
    df['word_count'] = df['text'].apply(lambda x: len(x.split()))

    return df


# -----------------------------
# LOAD DATA
# -----------------------------
print("Loading dataset...")
df = pd.read_csv("../cleaned_jobs_balanced.csv")   # <-- Change to your dataset name
df['text'] = df['text'].astype(str).apply(clean_text)

# Extract engineered features
df = extract_features(df)

# Columns
text_col = 'text'
numeric_cols = ['salary_high', 'contact_email', 'contact_phone',
                'id_request', 'benefit_count', 'exp_required',
                'edu_mismatch', 'word_count']

y = df['fraudulent']
X = df[[text_col] + numeric_cols]

# -----------------------------
# TRANSFORMER
# -----------------------------
preprocessor = ColumnTransformer(
    transformers=[
        ('tfidf', TfidfVectorizer(min_df=3, ngram_range=(1, 2)), 'text'),
        ('scaler', StandardScaler(), numeric_cols)
    ]
)

# -----------------------------
# FINAL PIPELINE
# -----------------------------
model_pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('clf', LogisticRegression(max_iter=300))
])

# -----------------------------
# TRAIN / TEST SPLIT
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("Training model...")
model_pipeline.fit(X_train, y_train)

# -----------------------------
# EVALUATION
# -----------------------------
y_pred = model_pipeline.predict(X_test)
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# -----------------------------
# SAVE PIPELINE
# -----------------------------
pickle.dump(model_pipeline, open("verihire_model5.pkl", "wb"))
print("\nModel saved to models/verihire_model.pkl")
