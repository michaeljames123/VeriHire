import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# Load dataset
# data = pd.read_csv('clean_fakejobs.csv')
data = pd.read_csv('cleaned_jobs_balanced.csv')

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    data.text, data.fraudulent, test_size=0.3, random_state=42
)

# Create and fit vectorizer
vect = CountVectorizer()
vect.fit(X_train)

# Transform train and test sets
X_train_dtm = vect.transform(X_train)
X_test_dtm = vect.transform(X_test)

# Train model
rf = RandomForestClassifier(random_state=42)
clf = rf.fit(X_train_dtm, y_train)

# Evaluate (optional)
y_pred = clf.predict(X_test_dtm)
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

# Save BOTH model and vectorizer
with open('verihire_model.pkl', 'wb') as model_file:
    pickle.dump(clf, model_file)

with open('verihire_vectorizer.pkl', 'wb') as vect_file:
    pickle.dump(vect, vect_file)

print("Model and vectorizer saved!")
