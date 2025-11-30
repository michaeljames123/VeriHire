from playwright.sync_api import sync_playwright

def scrape_jobs():
    file_path = "/home/raffy17/programtest/verihire/VeriHire/templates/fake_job_generator2.html"
    file_uri = f"file://{file_path}"
    print(f"Opening local file: {file_uri}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(file_uri, wait_until="domcontentloaded")

        # Example selector logic
        job_elements = page.query_selector_all(".job-card")

        jobs = []
        for job in job_elements:
            title = job.query_selector(".job-title").inner_text() if job.query_selector(".job-title") else "N/A"
            company = job.query_selector(".company").inner_text() if job.query_selector(".company") else "N/A"
            details = job.query_selector(".details").inner_text() if job.query_selector(".details") else "N/A"
            jobs.append({"title": title, "company": company, "details": details})

        browser.close()
        return jobs


if __name__ == "__main__":
    jobs = scrape_jobs()
    for j in jobs:
        print(j)
