import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# === API CONFIG ===
API_KEY = "184f4c4f08msh441d5b23ae4f96dp12bbfajsn6da52acc1a09"
BASE_URL = "https://jsearch.p.rapidapi.com/search"

HEADERS_API = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
}


# === HELPER FUNCTIONS ===
def extract_domain(url: str) -> str:
    """Extract domain from URL (e.g., linkedin.com, indeed.com)."""
    match = re.search(r"https?://(www\.)?([^/]+)/", url)
    return match.group(2) if match else None


def extract_education(text: str) -> str:
    """Extract education level from text."""
    if not text:
        return ""
    education_keywords = {
        r"\bbachelor'?s?\b": "Bachelor's degree",
        r"\bbs\b": "Bachelor's degree",
        r"\bba\b": "Bachelor's degree",
        r"\bmaster'?s?\b": "Master's degree",
        r"\bmba\b": "MBA",
        r"\bph\.?d\b": "PhD",
        r"\bdoctorate\b": "Doctorate",
        r"\bgraduate\b": "Graduate degree",
        r"\bassociate\b": "Associate degree",
        r"\bcollege diploma\b": "College diploma",
        r"\bhigh school\b": "High School diploma",
    }
    for pattern, label in education_keywords.items():
        if re.search(pattern, text, re.IGNORECASE):
            return label
    if re.search(r"\bdegree\b", text, re.IGNORECASE):
        return "Degree mentioned"
    return ""


def extract_years_of_experience(text: str) -> str:
    """Extract years of experience from text."""
    if not text:
        return ""
    matches = re.findall(r"(\d+)\+?\s*(?:years?|yrs?)", text, re.IGNORECASE)
    if matches:
        return ", ".join(f"{m}+ years" for m in matches)
    return ""


def normalize_employment_type(text: str) -> str:
    """Normalize employment type labels."""
    if not text:
        return ""
    text = text.lower()
    if "full" in text:
        return "Full-time"
    if "part" in text:
        return "Part-time"
    if "contract" in text:
        return "Contract"
    if "temporary" in text or "temp" in text:
        return "Temporary"
    return "Other"


def normalize_experience_level(text: str) -> str:
    """Normalize experience level labels."""
    if not text:
        return ""
    text = text.lower()
    if "intern" in text:
        return "Internship"
    if "entry" in text:
        return "Entry Level"
    if "associate" in text:
        return "Associate"
    if "mid" in text or "senior" in text:
        return "Mid-Senior-Level"
    if "executive" in text:
        return "Executive"
    if "director" in text:
        return "Director"
    if "not applicable" in text:
        return "Not applicable"
    return ""


def clean_benefits(values) -> list:
    """Remove salary or currency items from benefits list."""
    if not values:
        return []
    clean_list = []
    for v in values:
        if re.search(r"[\$₱€]\s?\d", v) or re.search(r"\d+\s*(k|K|,)", v):
            continue
        clean_list.append(v)
    return clean_list


# === API SCRAPER ===
def get_jobs(query: str, site: str, pages: int = 1):
    """
    Fetch job postings from JSearch API.
    query: job keyword/title
    site: source domain (e.g. linkedin.com)
    pages: number of pages to fetch
    """
    all_jobs = []
    for page in range(1, pages + 1):
        querystring = {
            "query": query,
            "page": str(page),
            "num_pages": "1",
            "site": site
        }
        response = requests.get(BASE_URL, headers=HEADERS_API, params=querystring)
        data = response.json()

        if "data" in data:
            all_jobs.extend(data["data"])
        else:
            print(f"[WARN] No data found for {site} page {page}")

    return all_jobs


def format_job(job: dict) -> dict:
    """Normalize API job data to the unified schema."""
    desc = job.get("job_description", "") or ""
    requirements = ""

    if "job_highlights" in job and job["job_highlights"]:
        highlights = job["job_highlights"]
        if "Qualifications" in highlights:
            requirements = "; ".join(highlights["Qualifications"])

    combined_text = f"{requirements}\n{desc}"

    return {
        "Job Title": job.get("job_title", ""),
        "Location": job.get("job_city", ""),
        "Department": job.get("job_category", ""),
        "Benefits": clean_benefits(job.get("job_benefits", []) or []),
        "Employment Type": normalize_employment_type(job.get("job_employment_type", "")),
        "Required Experience": extract_years_of_experience(combined_text),
        "Required Education": extract_education(combined_text),
        "Industry": job.get("job_industry", ""),
        "Function": job.get("job_publisher", ""),
        "Company Profile": job.get("employer_name", ""),
        "Requirements": requirements,
        "Description": desc[:5000],
    }


# === HTML FALLBACK SCRAPER ===
def scrape_job_post(url: str) -> dict:
    """Fallback scraper using BeautifulSoup for unsupported sites."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
        "DNT": "1",  # Do Not Track header for realism
    }

    try:
        print(f"[DEBUG] Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=20)
    except Exception as e:
        print("[ERROR] Request failed:", e)
        return None

    # 🔹 Handle 403 or other errors gracefully
    if response.status_code == 403:
        print(f"[ERROR] 403 Forbidden — the site blocked our scraper for {url}")
        print("[INFO] Retrying with alternate headers...")
        # Try again with even more realistic headers
        headers_alt = headers.copy()
        headers_alt["User-Agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"
        )
        response = requests.get(url, headers=headers_alt, timeout=20)

    if response.status_code != 200:
        print(f"[ERROR] {response.status_code} when fetching {url}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    domain = urlparse(url).netloc.lower()

    if "linkedin.com" in domain:
        return scrape_linkedin_job(soup)
    elif "indeed" in domain:
        return scrape_indeed_job(soup)
    elif "glassdoor" in domain:
        return scrape_glassdoor_job(soup)
    elif "onlinejobs.ph" in domain:
        return scrape_onlinejobsph_job(soup)
    else:
        return scrape_generic_job(soup)


def scrape_onlinejobsph_job(soup):
    """Custom parser for onlinejobs.ph job posts."""
    title = soup.find("h1")
    title = title.get_text(strip=True) if title else ""

    company = ""
    comp_el = soup.find("div", class_="ojd-company-name")
    if comp_el:
        company = comp_el.get_text(strip=True)

    location = ""
    loc_el = soup.find("div", string=re.compile("Location", re.IGNORECASE))
    if loc_el:
        next_el = loc_el.find_next("div")
        location = next_el.get_text(strip=True) if next_el else ""

    description = ""
    desc_el = soup.find("div", class_="ojd-job-description")
    if desc_el:
        description = desc_el.get_text(" ", strip=True)

    text = soup.get_text(" ", strip=True)

    return {
        "Job Title": title,
        "Location": location,
        "Department": "",
        "Benefits": "",
        "Employment Type": "",
        "Required Experience": extract_years_of_experience(text),
        "Required Education": extract_education(text),
        "Industry": "",
        "Function": "",
        "Company Profile": company,
        "Requirements": extract_years_of_experience(text),
        "Description": description or text[:5000],
    }


def scrape_linkedin_job(soup):
    title = soup.find("h1")
    title = title.get_text(strip=True) if title else ""
    company = soup.find("a", {"class": "topcard__org-name-link"})
    company = company.get_text(strip=True) if company else ""
    location = soup.find("span", {"class": "topcard__flavor topcard__flavor--bullet"})
    location = location.get_text(strip=True) if location else ""
    description = soup.find("div", {"class": "show-more-less-html__markup"})
    description = description.get_text(" ", strip=True) if description else ""

    return {
        "Job Title": title,
        "Location": location,
        "Department": "",
        "Benefits": "",
        "Employment Type": "",
        "Required Experience": extract_years_of_experience(description),
        "Required Education": extract_education(description),
        "Industry": "",
        "Function": "",
        "Company Profile": company,
        "Requirements": extract_years_of_experience(description),
        "Description": description,
    }


def scrape_indeed_job(soup):
    title = soup.find("h1")
    title = title.get_text(strip=True) if title else ""
    company = soup.find("div", {"data-company-name": True})
    company = company.get_text(strip=True) if company else ""
    location = soup.find("div", {"data-testid": "job-location"})
    location = location.get_text(strip=True) if location else ""
    description = soup.find("div", {"id": "jobDescriptionText"})
    description = description.get_text(" ", strip=True) if description else ""

    return {
        "Job Title": title,
        "Location": location,
        "Department": "",
        "Benefits": "",
        "Employment Type": "",
        "Required Experience": extract_years_of_experience(description),
        "Required Education": extract_education(description),
        "Industry": "",
        "Function": "",
        "Company Profile": company,
        "Requirements": extract_years_of_experience(description),
        "Description": description,
    }


def scrape_glassdoor_job(soup):
    title = soup.find("div", {"data-test": "jobTitle"})
    title = title.get_text(strip=True) if title else ""
    company = soup.find("div", {"data-test": "employerName"})
    company = company.get_text(strip=True) if company else ""
    location = soup.find("div", {"data-test": "location"})
    location = location.get_text(strip=True) if location else ""
    description = soup.find("div", {"class": "jobDescriptionContent"})
    description = description.get_text(" ", strip=True) if description else ""

    return {
        "Job Title": title,
        "Location": location,
        "Department": "",
        "Benefits": "",
        "Employment Type": "",
        "Required Experience": extract_years_of_experience(description),
        "Required Education": extract_education(description),
        "Industry": "",
        "Function": "",
        "Company Profile": company,
        "Requirements": extract_years_of_experience(description),
        "Description": description,
    }


def scrape_generic_job(soup):
    text = soup.get_text(" ", strip=True)
    title = soup.find(["h1", "h2"])
    title = title.get_text(strip=True) if title else ""

    company = ""
    match = re.search(r"(?:Company|Organization)[:\-]\s*(.+)", text, re.IGNORECASE)
    if match:
        company = match.group(1).split("\n")[0].strip()

    location = ""
    match = re.search(r"(?:Location)[:\-]\s*(.+)", text, re.IGNORECASE)
    if match:
        location = match.group(1).split("\n")[0].strip()

    return {
        "Job Title": title,
        "Location": location,
        "Department": "",
        "Benefits": "",
        "Employment Type": "",
        "Required Experience": extract_years_of_experience(text),
        "Required Education": extract_education(text),
        "Industry": "",
        "Function": "",
        "Company Profile": company,
        "Requirements": extract_years_of_experience(text),
        "Description": text[:5000],
    }


# === UNIVERSAL HANDLER ===
def universal_scrape(url: str, query: str = "") -> dict:
    """
    Try JSearch API first, fallback to HTML scraper if needed.
    """
    domain = extract_domain(url)
    if not domain:
        print("[WARN] Could not extract domain; falling back to HTML scraping.")
        return scrape_job_post(url)

    try:
        jobs = get_jobs(query=query or "Job", site=domain)
        if jobs:
            return format_job(jobs[0])
    except Exception as e:
        print("[WARN] API failed, falling back:", e)

    return scrape_job_post(url)


# === DEMO ===
if __name__ == "__main__":
    url = input("Enter job post URL: ")
    data = universal_scrape(url)
    if not data:
        print("Failed to scrape job data.")
    else:
        print("\n--- Job Information ---")
        for k, v in data.items():
            print(f"{k}: {v}")
