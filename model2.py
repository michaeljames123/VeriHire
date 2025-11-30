import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

# Load dataset
df = pd.read_csv("cleaned_jobs_balanced.csv")

# Split train/test
X_train, X_test, y_train, y_test = train_test_split(
    df['text'], df['fraudulent'], test_size=0.2, random_state=42
)

# TF-IDF Vectorizer
vectorizer = TfidfVectorizer(
    min_df=3,
    ngram_range=(1,2),
    stop_words='english',
    sublinear_tf=True
)

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# Logistic Regression
model = LogisticRegression(max_iter=500, class_weight='balanced', n_jobs=-1)
model.fit(X_train_vec, y_train)

# Evaluate
pred = model.predict(X_test_vec)
print("Accuracy:", accuracy_score(y_test, pred))
print(classification_report(y_test, pred))

# Save model & vectorizer
pickle.dump(model, open("models/verihire_model4.pkl","wb"))
pickle.dump(vectorizer, open("models/verihire_vectorizer4.pkl","wb"))
print("✅ Model & vectorizer saved!")
