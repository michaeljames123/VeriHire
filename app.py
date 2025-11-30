import pandas as pd
import numpy as np
import pickle
from flask import Flask, render_template, request, flash, jsonify
import scraper  # ✅ import your universal scraper

app = Flask(__name__)
app.config['SECRET_KEY'] = "secret lol"

# ✅ Load ML model + vectorizer
model = pickle.load(open('models/verihire_model.pkl', 'rb'))
vectorizer = pickle.load(open('models/verihire_vectorizer.pkl', 'rb'))


@app.route("/")
def home():
    return render_template("index.html")


# ✅ API route for AJAX-based scraping
@app.route("/scrape", methods=["POST"])
def scrape_job():
    """
    Receives a job posting URL and scrapes job details.
    Example POST body: { "url": "https://www.linkedin.com/jobs/view/..." }
    """
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


@app.route("/submit", methods=["POST"])
def submit():
    """
    Handles two cases:
    1. User submits a job URL (auto-scrape)
    2. User manually fills out the job form
    """

    job_url = request.form.get("url", "").strip()

    # Case 1: URL provided → scrape automatically
    if job_url:
        print(f"\n[DEBUG] URL received: {job_url}")

        job_data = scraper.scrape_job_post(job_url)

        # ✅ Log raw data returned by scraper
        print("[DEBUG] Scraped job data:")
        print(job_data)

        if not job_data or not any(job_data.values()):
            print("[DEBUG] ❌ Scraper returned empty or invalid data.")
            flash("Could not scrape job details from the provided URL.")
            return render_template("index.html")

        # Merge all scraped fields
        input_text = " ".join([
            job_data.get("Job Title", ""),
            job_data.get("Company", ""),
            job_data.get("Location", ""),
            job_data.get("Department", ""),
            job_data.get("Company Profile", ""),
            job_data.get("Requirements", ""),
            job_data.get("Benefits", ""),
            job_data.get("Employment Type", ""),
            job_data.get("Required Experience", ""),
            job_data.get("Required Education", ""),
            job_data.get("Industry", ""),
            job_data.get("Function", ""),
            job_data.get("Description", "")
        ])

        # ✅ Log processed text preview
        print(f"[DEBUG] Combined input text (first 300 chars): {input_text[:300]!r}")

    # Case 2: Manual input
    else:
        input_text = " ".join([
            request.form.get("title", ""),
            request.form.get("location", ""),
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
        ])
        print("[DEBUG] Manual input mode.")
        print(f"[DEBUG] Combined input text (first 300 chars): {input_text[:300]!r}")

    # ✅ Clean + vectorize the text
    input_text = input_text.strip()
    if not input_text:
        print("[DEBUG] ❌ No text available for model prediction.")
        flash("Please provide job details or a valid URL.")
        return render_template("index.html")

    input_features = vectorizer.transform([input_text])

    # ✅ Predict
    prediction = model.predict(input_features)[0]
    print(f"[DEBUG] Prediction result: {prediction} -> {'FRAUDULENT' if prediction == 1 else 'REAL'}")

    flash("FRAUDULENT JOB" if prediction == 1 else "REAL JOB")
    return render_template("index.html")



if __name__ == "__main__":
    # ✅ Accessible on local network (e.g. mobile preview)
    app.run(debug=True, host="0.0.0.0", port=5000)