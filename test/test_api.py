import requests
import json

url = "https://www.jobstreet.com.ph/en/job-search/developer-jobs/1"
headers = {"User-Agent": "Mozilla/5.0"}

params = {
    "page": 1,
    "limit": 10,  # how many jobs per page
}

r = requests.get(url, headers=headers, params=params)

print(f"Status Code: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    print(json.dumps(data, indent=2)[:2000])  # print the first 2000 chars of JSON
else:
    print("⚠️ Failed to fetch API data")
