import pandas as pd
import pickle
import re
from flask import Flask, render_template, request, flash, jsonify
import scraper
from urllib.parse import urlparse
import nltk
from nltk.corpus import words
from nltk import pos_tag

JOB_SITES = [
    "jobstreet.com", "linkedin.com", "indeed.com",
    "glassdoor.com", "kalibrr.com", "monster.com",
    "joblum.com", "jobs180.com", "jobbank.gc.ca",
    "ziprecruiter.com", "careerbuilder.com"
]




# Ensure required NLTK resources exist
def ensure_nltk():
    needed = [
        "words",
        "punkt",
        "averaged_perceptron_tagger_eng"
    ]

    for pkg in needed:
        try:
            nltk.data.find(pkg)
        except LookupError:
            nltk.download(pkg)

ensure_nltk()

# Now load dictionary
english_dict = set(words.words())


def is_meaningful(text):
    text = text.strip()
    words_list = text.split()

    # --------------------------------
    # 1. Basic length + word count
    # --------------------------------
    if len(text) < 30:
        return False
    if len(words_list) < 6:
        return False

    # --------------------------------
    # 2. English ratio (must contain real words)
    # --------------------------------
    real_words = sum(1 for w in words_list if w.lower() in english_dict)
    english_ratio = real_words / len(words_list)

    # Require at least 20% real English words
    if english_ratio < 0.20:
        return False

    # --------------------------------
    # 3. Detect nonsense or keyboard smash
    # --------------------------------
    nonsense = 0
    for w in words_list:
        # repeated pattern like "asdasd", "qweqwe"
        if re.search(r"([a-z]{2,})\1", w.lower()):
            nonsense += 1

        # low letter variety like "aaaaaa", "asddddd"
        if len(set(w.lower())) <= 2 and len(w) >= 5:
            nonsense += 1

        # random mix like "a3s2d1"
        if re.fullmatch(r"[a-z0-9]{5,}", w.lower()):
            if not w.lower() in english_dict:
                nonsense += 1

    if nonsense / len(words_list) > 0.30:
        return False

    # --------------------------------
    # 4. Variety check (avoid "word word word word")
    # --------------------------------
    unique_ratio = len(set(words_list)) / len(words_list)
    if unique_ratio < 0.40:  # at least 40% unique
        return False

    # --------------------------------
    # 5. POS Tagging (must contain noun + verb)
    # --------------------------------
    pos_tags = pos_tag(words_list)

    noun_count = sum(1 for w, t in pos_tags if t.startswith("NN"))
    verb_count = sum(1 for w, t in pos_tags if t.startswith("VB"))

    # Require structure: at least 2 nouns and 1 verb
    if noun_count < 2:
        return False
    if verb_count < 1:
        return False

    return True


# ----------------------------------------------------
# CLEAN TEXT (same as train.py)
# ----------------------------------------------------
def clean_text(text):
    text = text.lower()
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\s₱\-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# ----------------------------------------------------
# MATCH TRAIN.PY EXACTLY
# ----------------------------------------------------
def extract_features(df):
    df['salary_high'] = df['text'].str.contains(
        r"₱?\s?(?:1[5-9]0{4}|[2-9]\d{5,})",
        regex=True
    ).astype(int)

    df['contact_email'] = df['text'].str.contains(
        r'@gmail\.com|@yahoo\.com|@hotmail\.com',
        regex=True
    ).astype(int)

    df['contact_phone'] = df['text'].str.contains(
        r"\b\d{10,11}\b"
    ).astype(int)

    df['id_request'] = df['text'].str.contains(
        r"(?:valid id|government id|govt id|send id|upload id|passport|sss|philhealth|nbi|tin)",
        flags=re.IGNORECASE,
        regex=True
    ).astype(int)

    df['benefit_count'] = df['text'].str.count(
        r"(benefit|insurance|allowance|support|bonus|stipend)",
        flags=re.IGNORECASE
    )

    df['exp_required'] = pd.to_numeric(
        df['text'].str.extract(r"(\d+)\s*[-+]?\s*\d*\s*year", expand=False).fillna(0)
    ).astype(int)

    df['edu_mismatch'] = (
        ((df['exp_required'] <= 1) & df['text'].str.contains("degree required", regex=True)) |
        ((df['exp_required'] >= 5) & df['text'].str.contains(r"no degree|required|no experience", regex=True))
    ).astype(int)

    df['word_count'] = df['text'].apply(lambda x: len(str(x).split()))
    df['text_length'] = df['text'].apply(lambda x: len(str(x)))
    df['uppercase_rate'] = df['text'].apply(
        lambda x: (sum(1 for c in x if c.isupper()) / len(x)) if len(x) else 0
    )

    return df


# ----------------------------------------------------
# FLASK APP
# ----------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = "secret"

# ✅ Load ML pipeline
model_pipeline = pickle.load(open("models/verihire_model5.pkl", "rb"))

@app.route("/")
def home():
    return render_template("index.html")

# -----------------------------
# Scraper API (independent)
# -----------------------------
@app.route("/scrape", methods=["POST"])
def scrape_job():
    data = request.get_json()
    job_url = data.get("url")

    if not job_url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        job_data = scraper.scrape_job_post(job_url)
        if not job_data:
            return jsonify({"error": "Failed to scrape job details"}), 500
        return jsonify(job_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def is_job_site(url):
    try:
        domain = urlparse(url).netloc.lower()
        return any(job_site in domain for job_site in JOB_SITES)
    except:
        return False


# -----------------------------
# Manual input route (unchanged, with debug)
# -----------------------------
@app.route("/submit", methods=["POST"])
def submit():
    url = request.form.get("url", "").strip()
    scraped_text = ""
    scraped_success = False

    if url:
        try:
            scraped = scraper.scrape_job_post(url)
            if scraped:
                scraped_text = " ".join(str(v) for v in scraped.values())
                scraped_success = True
        except Exception as e:
            print("SCRAPE BLOCKED:", e)

        # --- Fallback if scraping FAILS ---
        if not scraped_success:
            if is_job_site(url):
                # Real job website → Legit
                flash("LIKELY REAL JOB")
                return render_template("index.html")
            else:
                # Not a job website → Fraud
                # flash("HIGH RISK — This link is NOT a job posting website")
                flash("FRAUDULENT JOB")
                return render_template("index.html")

        raw_text = scraped_text


    else:
        # --- 2. Manual Input Mode ---
        raw_text = " ".join([
            request.form.get("title", ""),
            request.form.get("location", ""),
            request.form.get("salary", ""),
            request.form.get("department", ""),
            request.form.get("profile", ""),
            request.form.get("req", ""),
            request.form.get("ben", ""),
            request.form.get("emptype", ""),
            request.form.get("exp", ""),
            request.form.get("edu", ""),
            request.form.get("indu", ""),
            request.form.get("func", ""),
            request.form.get("des", "")
        ]).strip()

    if not raw_text:
        flash("Auto Identifier.")
        return render_template("index.html")

    # -------------------------
    # Meaningfulness Filter
    # -------------------------
    if not is_meaningful(raw_text):

        # If user submitted a URL:
        if url:
            # URL from non-job website → Fraud
            if not is_job_site(url):
                flash("FRAUDULENT JOB")
                return render_template("index.html")

            # URL from known job website but empty text → Likely real
            flash("LIKELY REAL JOB — Legit site but no readable content extracted.")
            return render_template("index.html")

        # Manual input case → invalid
        flash("Input text is too short, repetitive, or not meaningful enough to analyze.")
        return render_template("index.html")

        


    clean_txt = clean_text(raw_text)
    input_df = pd.DataFrame([{"text": clean_txt}])
    input_df = extract_features(input_df)

    pred_prob = model_pipeline.predict_proba(input_df)[0][1]
    pred_label = model_pipeline.predict(input_df)[0]

    # -------------------------
    # DEBUG PRINTS
    # -------------------------
    print("\n--- DEBUG ---")
    print("Clean text:", clean_txt[:200])
    print("Features:", input_df.to_dict(orient="records")[0])
    print("Probability:", pred_prob)
    print("--------------\n")
    # -------------------------

    if pred_prob > 0.70:
        final = "FRAUDULENT JOB"
    elif pred_prob > 0.40:
        final = "SUSPICIOUS"
    else:
        final = "LIKELY REAL JOB"


    flash(final)
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
