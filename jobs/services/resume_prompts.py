RESUME_ANALYSIS_SYSTEM_PROMPT = """
You extract structured candidate information from resume text.
Return only valid JSON. Do not include markdown, comments, or prose.
Use empty strings, empty arrays, or null values when information is missing.
"""


def build_resume_analysis_prompt(resume_text: str) -> str:
    return f"""
Extract the following fields from the resume text and return a single JSON object:

{{
  "full_name": "",
  "email": "",
  "phone": "",
  "location": "",
  "summary": "",
  "skills": [],
  "technical_skills": [],
  "soft_skills": [],
  "education": [
    {{
      "degree": "",
      "institution": "",
      "start_year": null,
      "end_year": null,
      "details": ""
    }}
  ],
  "experience": [
    {{
      "job_title": "",
      "company": "",
      "start_date": "",
      "end_date": "",
      "description": "",
      "technologies": []
    }}
  ],
  "projects": [
    {{
      "name": "",
      "description": "",
      "technologies": []
    }}
  ],
  "certifications": [],
  "languages": [],
  "years_of_experience": null
}}

Resume text:
{resume_text}
"""
