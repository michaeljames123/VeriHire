import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from .preprocessing import clean_text
from .features import extract_features

def create_dataset(df):
    # Clean text
    text_data = df['text'].apply(clean_text)
    # Extract numeric features
    feature_data = df.apply(extract_features, axis=1).apply(pd.Series)
    # Combine
    X = pd.concat([text_data, feature_data], axis=1)
    y = df['fraudulent']
    return X, y

def build_pipeline():
    numeric_features = ['salary_min', 'salary_max', 'high_salary', 
                        'exp_edu_mismatch', 'num_benefits', 
                        'contact_info', 'id_request']
    preprocessor = ColumnTransformer([
        ('tfidf', TfidfVectorizer(ngram_range=(1,2), stop_words='english', min_df=3), 'text'),
        ('num', StandardScaler(), numeric_features)
    ])

    pipeline = Pipeline([
        ('pre', preprocessor),
        ('clf', LogisticRegression(max_iter=500, class_weight='balanced'))
    ])
    return pipeline
