DEFAULT_SCORE = 0


def clamp_score(value, default=DEFAULT_SCORE) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError):
        return default

    return max(0, min(100, score))


def normalize_career_analysis_payload(payload: dict) -> dict:
    if not isinstance(payload, dict):
        payload = {}

    return {
        'resume_quality': payload.get('resume_quality') or {},
        'ats_analysis': payload.get('ats_analysis') or {},
        'strongest_skills': payload.get('strongest_skills') or [],
        'missing_skills': payload.get('missing_skills') or [],
        'weak_sections': payload.get('weak_sections') or [],
        'improvement_suggestions': payload.get('improvement_suggestions') or [],
        'career_paths': payload.get('career_paths') or [],
        'role_readiness': payload.get('role_readiness') or [],
        'ai_explanation': payload.get('ai_explanation') or '',
        'next_actions': payload.get('next_actions') or [],
    }
