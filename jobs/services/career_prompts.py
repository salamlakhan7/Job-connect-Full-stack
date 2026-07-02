import json

CAREER_ANALYSIS_PROMPT_VERSION = 'career-analysis-v1'

CAREER_ANALYSIS_SYSTEM_PROMPT = """
You are a career analysis engine for a hiring platform.
Return only valid JSON. Do not include markdown, comments, or prose.
Base conclusions only on the provided resume analysis data.
Do not invent employers, degrees, certifications, or private facts.
"""


def build_career_analysis_prompt(resume_analysis) -> str:
    resume_payload = {
        'parsed_resume': resume_analysis.parsed_data,
        'extracted_resume_text': resume_analysis.extracted_text,
    }

    return f"""
Analyze this candidate resume and return a single JSON object with this exact shape:

{{
  "overall_score": 0,
  "ats_score": 0,
  "readiness_score": 0,
  "resume_quality": {{
    "summary": "",
    "strengths": [],
    "issues": []
  }},
  "ats_analysis": {{
    "summary": "",
    "formatting_risks": [],
    "keyword_gaps": [],
    "section_warnings": []
  }},
  "strongest_skills": [],
  "missing_skills": [
    {{
      "skill": "",
      "reason": "",
      "priority": "high"
    }}
  ],
  "weak_sections": [
    {{
      "section": "",
      "issue": "",
      "recommendation": ""
    }}
  ],
  "improvement_suggestions": [
    {{
      "title": "",
      "detail": "",
      "impact": "high"
    }}
  ],
  "career_paths": [
    {{
      "title": "",
      "fit": "strong",
      "reason": ""
    }}
  ],
  "role_readiness": [
    {{
      "role": "",
      "readiness": "ready_now",
      "reason": ""
    }}
  ],
  "ai_explanation": "",
  "next_actions": []
}}

Scoring rules:
- Scores must be integers from 0 to 100.
- Overall score measures resume strength.
- ATS score measures parsing and recruiter-screening friendliness.
- Readiness score measures current readiness for realistic entry-level or experienced roles.
- Explain conclusions with concise evidence from the resume, but do not quote long resume passages.

Resume analysis data:
{json.dumps(resume_payload, ensure_ascii=True)}
"""
