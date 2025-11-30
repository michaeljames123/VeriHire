# import pandas as pd
# import re
# from sklearn.utils import resample

# # -------------------------------
# # 1️⃣ Load datasets
# # -------------------------------
# data1 = pd.read_csv("datasets/ph_jobs2_with_estimated_salaries.csv")
# data2 = pd.read_csv("datasets/fake_job_postings_with_salaries.csv")
# data3 = pd.read_csv("datasets/fraudulent_job_postings.csv")

# # Standardize column names
# for df in [data1, data2, data3]:
#     df.columns = df.columns.str.lower()

# # Ensure "fraudulent" column exists
# for df in [data1, data2, data3]:
#     if "fraudulent" not in df.columns:
#         raise ValueError("Each dataset must have a 'fraudulent' column")

# # -------------------------------
# # 2️⃣ Helper: combine text fields
# # -------------------------------
# def combine_text_fields(row, fields):
#     parts = []
#     for f in fields:
#         if f in row and pd.notna(row[f]):
#             parts.append(str(row[f]))
#     return " ".join(parts)

# # -------------------------------
# # 3️⃣ Process datasets
# # -------------------------------
# # Dataset 1
# data1["text"] = data1.apply(
#     lambda r: combine_text_fields(
#         r, ["title", "company_profile", "location", "salary", "salary_estimated"]
#     ),
#     axis=1
# )
# data1_clean = data1[["text", "fraudulent"]]

# # Dataset 2 & 3
# common_fields = [
#     "title",
#     "company_profile",
#     "description",
#     "requirements",
#     "benefits",
#     "salary_range",
#     "salary_range_filled",
#     "location",
#     "department",
# ]

# data2["text"] = data2.apply(lambda r: combine_text_fields(r, common_fields), axis=1)
# data3["text"] = data3.apply(lambda r: combine_text_fields(r, common_fields), axis=1)

# data2_clean = data2[["text", "fraudulent"]]
# data3_clean = data3[["text", "fraudulent"]]

# # -------------------------------
# # 4️⃣ Merge all datasets
# # -------------------------------
# combined = pd.concat([data1_clean, data2_clean, data3_clean], ignore_index=True)

# # -------------------------------
# # 5️⃣ Clean text
# # -------------------------------
# def clean_text(text):
#     text = re.sub(r"<.*?>", " ", str(text))        # remove HTML tags
#     text = re.sub(r"http\S+", " ", text)          # remove URLs
#     text = re.sub(r"[^a-zA-Z0-9₱$ ]", " ", text) # keep letters, numbers, currency symbols
#     text = re.sub(r"\s+", " ", text)             # collapse whitespace
#     return text.strip().lower()

# combined["text"] = combined["text"].apply(clean_text)

# # Remove empty text
# combined = combined[combined["text"].str.strip() != ""]

# # -------------------------------
# # 6️⃣ Balance dataset
# # -------------------------------
# fraud = combined[combined.fraudulent == 1]
# real = combined[combined.fraudulent == 0]

# minority_size = min(len(fraud), len(real))

# fraud_balanced = resample(fraud, replace=False, n_samples=minority_size, random_state=42)
# real_balanced = resample(real, replace=False, n_samples=minority_size, random_state=42)

# balanced_data = pd.concat([fraud_balanced, real_balanced]).sample(frac=1, random_state=42).reset_index(drop=True)

# # -------------------------------
# # 7️⃣ Save in desired order: fraudulent, text
# # -------------------------------
# balanced_data = balanced_data[["fraudulent", "text"]]  # fraudulent first
# balanced_data.to_csv("datasets/clean_fakejobs_final.csv", index=False)
# print(f"✅ Clean & balanced dataset saved: {len(balanced_data)} rows, columns: {list(balanced_data.columns)}")


import pandas as pd
import csv
import re

# -----------------------------------------------------------
# Load datasets
# -----------------------------------------------------------
phobs = pd.read_csv("datasets/philippines_fake_job_dataset.csv")
fake_jobs = pd.read_csv("datasets/fake_job_postings_with_salaries.csv")
fraud_jobs = pd.read_csv("datasets/fraudulent_job_postings.csv")


# -----------------------------------------------------------
# Text Cleaning Function
# -----------------------------------------------------------
def clean_raw_text(text):
    if pd.isna(text):
        return ""
    text = str(text)

    # Remove HTML tags
    text = re.sub(r"<.*?>", " ", text)

    # Remove URLs
    text = re.sub(r"http\S+|www\.\S+", " ", text)

    # Remove special characters
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)

    # Lowercase
    text = text.lower()

    # Collapse extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


# -----------------------------------------------------------
# Fields to combine (generic for all datasets)
# -----------------------------------------------------------
FIELDS_TO_MERGE = [
    "title",
    "location",
    "department",
    "salary_range_filled",
    "company_profile",
    "description",
    "requirements",
    "benefits",
    "required_experience",
    "industry",
    "function",
    "employment_type"
]


def build_text(row):
    parts = []
    for field in FIELDS_TO_MERGE:
        if field in row:
            parts.append(clean_raw_text(row[field]))
    return " ".join([p for p in parts if p])


# -----------------------------------------------------------
# Process each dataset
# -----------------------------------------------------------
def process_dataset(df):
    cleaned = pd.DataFrame()
    cleaned["fraudulent"] = df["fraudulent"]
    cleaned["text"] = df.apply(build_text, axis=1)
    return cleaned


phobs_clean = process_dataset(phobs)
fake_clean = process_dataset(fake_jobs)
fraud_clean = process_dataset(fraud_jobs)

# -----------------------------------------------------------
# Combine All
# -----------------------------------------------------------
combined = pd.concat([phobs_clean, fake_clean, fraud_clean], ignore_index=True)

# Drop empty text rows
combined = combined[combined["text"].str.strip() != ""]


# -----------------------------------------------------------
# Balance dataset 50/50
# -----------------------------------------------------------
fraud = combined[combined["fraudulent"] == 1]
non_fraud = combined[combined["fraudulent"] == 0].sample(n=len(fraud), random_state=42)

balanced = pd.concat([fraud, non_fraud]).sample(frac=1, random_state=42).reset_index(drop=True)


balanced = balanced.sort_values(by="fraudulent", ascending=True).reset_index(drop=True)
balanced["job_id"] = balanced.index + 1

balanced = balanced[["job_id", "fraudulent", "text"]]
# -----------------------------------------------------------
# Save Final Output
# -----------------------------------------------------------
balanced.to_csv(
    "cleaned_jobs_balanced.csv",
    index=False,
    quoting=csv.QUOTE_NONNUMERIC
)

print("Cleaning complete → cleaned_jobs_balanced.csv")
