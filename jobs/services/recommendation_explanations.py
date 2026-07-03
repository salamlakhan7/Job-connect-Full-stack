from .job_embedding import derive_required_skills


def normalize_skill(value) -> str:
    return str(value or '').strip().lower()


def candidate_skill_set(resume_analysis, career_analysis=None) -> set[str]:
    parsed = resume_analysis.parsed_data or {}
    career_data = career_analysis.analysis_data if career_analysis else {}
    skills = set()

    for key in ('skills', 'technical_skills', 'soft_skills'):
        for skill in parsed.get(key) or []:
            if isinstance(skill, dict):
                skill = skill.get('name') or skill.get('skill')
            normalized = normalize_skill(skill)
            if normalized:
                skills.add(normalized)

    for skill in career_data.get('strongest_skills') or []:
        normalized = normalize_skill(skill)
        if normalized:
            skills.add(normalized)

    return skills


def skill_overlap_score(candidate_skills: set[str], job_skills: list[str]) -> tuple[int, list[str], list[str]]:
    normalized_job_skills = [normalize_skill(skill) for skill in job_skills if normalize_skill(skill)]
    if not normalized_job_skills:
        return 50, [], []

    matched = sorted(skill for skill in normalized_job_skills if skill in candidate_skills)
    missing = sorted(skill for skill in normalized_job_skills if skill not in candidate_skills)
    score = round((len(matched) / len(normalized_job_skills)) * 100)
    return score, matched, missing


def confidence_from_score(final_score: int) -> str:
    if final_score >= 75:
        return 'high'
    if final_score >= 55:
        return 'medium'
    return 'low'


def next_steps_for_missing_skills(missing_skills: list[str]) -> list[str]:
    if not missing_skills:
        return ["Review the job details and apply if the role fits your goals."]
    return [
        f"Strengthen or add evidence for {skill} before applying."
        for skill in missing_skills[:3]
    ]


def build_explanation_data(job, matched_skills, missing_skills, score_breakdown, confidence):
    if matched_skills:
        summary = f"This role matches your profile through {', '.join(matched_skills[:3])}."
    else:
        summary = "This role is semantically related to your profile, but explicit skill overlap is limited."

    return {
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'score_breakdown': score_breakdown,
        'confidence': confidence,
        'summary': summary,
        'next_steps': next_steps_for_missing_skills(missing_skills),
    }
