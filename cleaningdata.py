import pandas as pd
import re

# Load raw dataset
df = pd.read_csv("fake_job_postings.csv")

# Keep only useful columns
cols_to_use = [
    "job_id", "title", "company_profile", "description",
    "requirements", "benefits", "fraudulent"
]
df = df[cols_to_use]

# Combine text columns into one
df["text"] = (
    df["title"].fillna('') + ' ' +
    df["company_profile"].fillna('') + ' ' +
    df["description"].fillna('') + ' ' +
    df["requirements"].fillna('') + ' ' +
    df["benefits"].fillna('')
)

# Clean the text
def clean_text(text):
    text = text.lower()
    text = re.sub(r'http\S+', '', text)        # remove URLs
    text = re.sub(r'[^a-z\s]', '', text)       # keep only letters
    text = re.sub(r'\s+', ' ', text).strip()   # remove extra spaces
    return text

df["text"] = df["text"].apply(clean_text)

# Keep only final useful columns
clean_df = df[["job_id", "fraudulent", "text"]]

# Drop empty text rows
clean_df = clean_df[clean_df["text"].str.strip() != ""]

# Save to new file
clean_df.to_csv("clean_fakejobs.csv", index=False)

print("✅ Clean dataset saved as 'clean_fakejobs.csv'")
