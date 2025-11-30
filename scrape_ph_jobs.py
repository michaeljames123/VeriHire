import requests
import csv
import json
import os
import time
from datetime import datetime

API_KEY = "00f5aefc77msh5c87b78de1f4da9p1b2a6bjsn0614af9e35a0"
BASE_URL = "https://jsearch.p.rapidapi.com/search"

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
}

CHECKPOINT_FILE = "checkpoint.json"
CSV_FILE = "scrape_ph_jobs3.csv"
BACKUP_FOLDER = "backups"

PH_CITIES = [
    "Manila", "Quezon City", "Cebu", "Davao", "Makati", 
    "Taguig", "Pasig", "Caloocan", "Mandaluyong", "Baguio"
]

# Create backups folder if not exists
os.makedirs(BACKUP_FOLDER, exist_ok=True)


def save_checkpoint(city, page, keyword):
    """Save progress to checkpoint file."""
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({"last_city": city, "last_page": page, "keyword": keyword}, f)


def load_checkpoint():
    """Load checkpoint file if exists."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {"last_city": None, "last_page": 0, "keyword": ""}


def append_to_csv(jobs, file_path):
    """Append job entries to CSV."""
    file_exists = os.path.isfile(file_path)
    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "company_profile", "location", "link", "source", "salary", "fraudulent"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(jobs)


def create_backup(page):
    """Create a backup copy of the CSV every 50 pages."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{BACKUP_FOLDER}/backup_page_{page}_{timestamp}.csv"
    if os.path.exists(CSV_FILE):
        os.system(f"cp '{CSV_FILE}' '{backup_name}'")
        print(f" Backup created: {backup_name}")


def scrape_ph_jobs(keyword="", pages=3):
    checkpoint = load_checkpoint()
    start_city_index = 0

    # Resume from last city if checkpoint exists
    if checkpoint["last_city"]:
        try:
            start_city_index = PH_CITIES.index(checkpoint["last_city"])
        except ValueError:
            start_city_index = 0

    for city in PH_CITIES[start_city_index:]:
        print(f"\nStarting scraping for city: {city}")
        start_page = 1
        if checkpoint["last_city"] == city:
            start_page = checkpoint["last_page"] + 1

        for page in range(start_page, pages + 1):
            query = f"{keyword} {city}" if keyword else city
            print(f" Scraping JSearch page {page} for '{query}'...")
            params = {
                "query": query,
                "page": str(page),
                "num_pages": "1"
            }

            try:
                r = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=20)
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                print(f"[ERROR] Failed on page {page}: {e}")
                time.sleep(5)
                continue

            if "data" not in data or not data["data"]:
                print(" No data found on this page")
                save_checkpoint(city, page, keyword)
                break  # Stop current city if no more results

            jobs = []
            for job in data["data"]:

                salary = ""

                if job.get("job_salary"):
                    salary = job.get("job_salary")

                elif job.get("estimated_salary_min") or job.get("estimated_salary_max"):
                    currency = job.get("job_salary_currency", "")
                    salary = f"{currency} {job.get('estimated_salary_min', '')} - {job.get('estimated_salary_max', '')}".strip(" -")

                elif job.get("job_salary_currency") and job.get("job_salary_period"):
                    salary = f"{job.get('job_salary_currency')} ({job.get('job_salary_period')})"

                salary = salary.strip()

                print("Salary: ", salary)

                jobs.append({
                    "title": job.get("job_title", ""),
                    "company_profile": job.get("employer_name", ""),
                    "location": job.get("job_city", ""),
                    "link": job.get("job_apply_link", ""),
                    "source": job.get("job_publisher", ""),
                    "salary": salary,
                    "fraudulent": 0
                })

            append_to_csv(jobs, CSV_FILE)
            print(f" Saved {len(jobs)} jobs from page {page}")

            # Save checkpoint every page
            save_checkpoint(city, page, keyword)

            # Create backup every 10 pages
            if page % 10 == 0:
                create_backup(page)

            time.sleep(2)  # small delay to avoid hitting API rate limits

    print("\nScraping complete!")
    print(f"Data saved to {CSV_FILE}")


if __name__ == "__main__":
    kw = input("Enter keyword (optional, press enter to skip): ").strip()
    scrape_ph_jobs(keyword=kw, pages=40)
