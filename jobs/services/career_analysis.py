import logging

from django.utils import timezone

from jobs.models import CareerAnalysis

from .career_prompts import (
    CAREER_ANALYSIS_PROMPT_VERSION,
    CAREER_ANALYSIS_SYSTEM_PROMPT,
    build_career_analysis_prompt,
)
from .career_scoring import clamp_score, normalize_career_analysis_payload
from .candidate_embedding import generate_candidate_embedding
from .groq_client import complete_json_with_groq

logger = logging.getLogger(__name__)


class CareerAnalysisError(Exception):
    """Raised when career analysis cannot be generated."""


def _safe_error_message(exc: Exception) -> str:
    return f"Career analysis failed: {exc.__class__.__name__}"


def analyze_career_from_resume_analysis(resume_analysis) -> CareerAnalysis:
    career_analysis, _ = CareerAnalysis.objects.get_or_create(
        resume_analysis=resume_analysis
    )
    career_analysis.status = 'pending'
    career_analysis.overall_score = 0
    career_analysis.ats_score = 0
    career_analysis.readiness_score = 0
    career_analysis.analysis_data = {}
    career_analysis.error_message = ''
    career_analysis.model_name = ''
    career_analysis.prompt_version = CAREER_ANALYSIS_PROMPT_VERSION
    career_analysis.analyzed_at = None
    career_analysis.save(update_fields=[
        'status',
        'overall_score',
        'ats_score',
        'readiness_score',
        'analysis_data',
        'error_message',
        'model_name',
        'prompt_version',
        'analyzed_at',
        'updated_at',
    ])

    try:
        if resume_analysis.status != 'completed':
            raise CareerAnalysisError("Resume analysis is not completed.")

        payload, model_name = complete_json_with_groq(
            CAREER_ANALYSIS_SYSTEM_PROMPT,
            build_career_analysis_prompt(resume_analysis),
        )
        normalized_payload = normalize_career_analysis_payload(payload)
    except Exception as exc:
        logger.exception(
            "Career analysis failed for resume_analysis_id=%s",
            resume_analysis.id,
        )
        career_analysis.status = 'failed'
        career_analysis.error_message = _safe_error_message(exc)
        career_analysis.save(update_fields=['status', 'error_message', 'updated_at'])
        return career_analysis

    career_analysis.overall_score = clamp_score(payload.get('overall_score'))
    career_analysis.ats_score = clamp_score(payload.get('ats_score'))
    career_analysis.readiness_score = clamp_score(payload.get('readiness_score'))
    career_analysis.analysis_data = normalized_payload
    career_analysis.model_name = model_name
    career_analysis.status = 'completed'
    career_analysis.analyzed_at = timezone.now()
    career_analysis.save(update_fields=[
        'overall_score',
        'ats_score',
        'readiness_score',
        'analysis_data',
        'model_name',
        'status',
        'analyzed_at',
        'updated_at',
    ])
    generate_candidate_embedding(resume_analysis.user_profile)
    return career_analysis
