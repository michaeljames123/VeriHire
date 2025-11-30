import re

def extract_features(job_data):
    """
    Extract numeric features from job posting
    """
    features = {}
    
    # Salary numeric check
    salary_text = job_data.get("Salary", "")
    salary_nums = [int(s.replace('₱','').replace(',','')) for s in re.findall(r'\d+', salary_text)]
    if salary_nums:
        features['salary_min'] = min(salary_nums)
        features['salary_max'] = max(salary_nums)
        features['high_salary'] = int(features['salary_max'] > 150000)
    else:
        features['salary_min'] = 0
        features['salary_max'] = 0
        features['high_salary'] = 0

    # Experience vs education
    exp_text = job_data.get("Required Experience", "")
    edu_text = job_data.get("Required Education", "").lower()
    features['exp_edu_mismatch'] = int(('0' in exp_text or 'entry' in exp_text.lower()) and 'phd' in edu_text)

    # Number of benefits
    benefits = job_data.get("Benefits", "")
    features['num_benefits'] = len(benefits.split(','))

    # Contact info and ID request
    text_combined = " ".join(job_data.values())
    features['contact_info'] = int(bool(re.search(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', text_combined)))
    features['id_request'] = int(bool(re.search(r'\b(id|passport|ssn|valid id|upload).{0,20}\b', text_combined, re.I)))

    return features
