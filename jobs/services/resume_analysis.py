import logging

from django.utils import timezone

from jobs.models import ResumeAnalysis

from .groq_client import analyze_resume_with_groq
from .resume_parser import extract_text_from_resume

logger = logging.getLogger(__name__)


def analyze_uploaded_resume(user_profile) -> ResumeAnalysis:
    analysis, _ = ResumeAnalysis.objects.get_or_create(user_profile=user_profile)
    analysis.resume_file = user_profile.resume
    analysis.status = 'pending'
    analysis.error_message = ''
    analysis.parsed_data = {}
    analysis.extracted_text = ''
    analysis.model_name = ''
    analysis.analyzed_at = None
    analysis.save(update_fields=[
        'resume_file',
        'status',
        'error_message',
        'parsed_data',
        'extracted_text',
        'model_name',
        'analyzed_at',
        'updated_at',
    ])

    try:
        extracted_text = extract_text_from_resume(user_profile.resume)
        parsed_data, model_name = analyze_resume_with_groq(extracted_text)
    except Exception as exc:
        logger.exception(
            "Resume AI analysis failed for user_profile_id=%s",
            user_profile.id,
        )
        analysis.status = 'failed'
        analysis.error_message = str(exc)
        analysis.save(update_fields=['status', 'error_message', 'updated_at'])
        return analysis

    analysis.extracted_text = extracted_text
    analysis.parsed_data = parsed_data
    analysis.model_name = model_name
    analysis.status = 'completed'
    analysis.analyzed_at = timezone.now()
    analysis.save(update_fields=[
        'extracted_text',
        'parsed_data',
        'model_name',
        'status',
        'analyzed_at',
        'updated_at',
    ])
    return analysis
