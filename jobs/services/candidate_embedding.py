import hashlib
import json
import logging

from jobs.models import CandidateEmbedding

from .embedding_client import generate_embedding, get_embedding_model_name
from .vector_store import CANDIDATE_COLLECTION, upsert_embedding

logger = logging.getLogger(__name__)


def _safe_error_message(exc: Exception) -> str:
    return f"Candidate embedding failed: {exc.__class__.__name__}"


def _stable_json(data) -> str:
    return json.dumps(data or {}, ensure_ascii=True, sort_keys=True)


def build_candidate_embedding_text(resume_analysis, career_analysis=None) -> str:
    parsed_resume = resume_analysis.parsed_data or {}
    career_data = career_analysis.analysis_data if career_analysis else {}

    sections = [
        "Candidate Profile",
        f"Resume Summary: {parsed_resume.get('summary', '')}",
        f"Skills: {_stable_json(parsed_resume.get('skills'))}",
        f"Technical Skills: {_stable_json(parsed_resume.get('technical_skills'))}",
        f"Soft Skills: {_stable_json(parsed_resume.get('soft_skills'))}",
        f"Education: {_stable_json(parsed_resume.get('education'))}",
        f"Experience: {_stable_json(parsed_resume.get('experience'))}",
        f"Projects: {_stable_json(parsed_resume.get('projects'))}",
        f"Certifications: {_stable_json(parsed_resume.get('certifications'))}",
        f"Languages: {_stable_json(parsed_resume.get('languages'))}",
        f"Years of Experience: {parsed_resume.get('years_of_experience', '')}",
        f"Career Strong Skills: {_stable_json(career_data.get('strongest_skills'))}",
        f"Career Paths: {_stable_json(career_data.get('career_paths'))}",
        f"Role Readiness: {_stable_json(career_data.get('role_readiness'))}",
        f"Missing Skills: {_stable_json(career_data.get('missing_skills'))}",
    ]
    return "\n".join(section for section in sections if section.strip())


def candidate_embedding_hash(resume_analysis, career_analysis=None) -> str:
    payload = {
        'resume_analysis_id': resume_analysis.id,
        'resume_updated_at': resume_analysis.updated_at.isoformat() if resume_analysis.updated_at else '',
        'parsed_data': resume_analysis.parsed_data,
        'career_analysis_id': career_analysis.id if career_analysis else None,
        'career_updated_at': career_analysis.updated_at.isoformat() if career_analysis and career_analysis.updated_at else '',
        'career_data': career_analysis.analysis_data if career_analysis else {},
        'embedding_model': get_embedding_model_name(),
    }
    return hashlib.sha256(_stable_json(payload).encode('utf-8')).hexdigest()


def generate_candidate_embedding(user_profile):
    resume_analysis = getattr(user_profile, 'resume_analysis', None)
    if resume_analysis is None or resume_analysis.status != 'completed':
        return None

    career_analysis = getattr(resume_analysis, 'career_analysis', None)
    if career_analysis is not None and career_analysis.status != 'completed':
        career_analysis = None

    metadata, _ = CandidateEmbedding.objects.get_or_create(user_profile=user_profile)
    embedding_hash = candidate_embedding_hash(resume_analysis, career_analysis)
    embedding_model = get_embedding_model_name()

    if (
        metadata.embedding_status == 'completed'
        and metadata.embedding_hash == embedding_hash
        and metadata.embedding_model == embedding_model
    ):
        return metadata

    metadata.resume_analysis = resume_analysis
    metadata.career_analysis = career_analysis
    metadata.embedding_status = 'pending'
    metadata.embedding_hash = embedding_hash
    metadata.embedding_model = embedding_model
    metadata.error_message = ''
    metadata.save(update_fields=[
        'resume_analysis',
        'career_analysis',
        'embedding_status',
        'embedding_hash',
        'embedding_model',
        'error_message',
        'updated_at',
    ])

    try:
        text = build_candidate_embedding_text(resume_analysis, career_analysis)
        embedding = generate_embedding(text)
        upsert_embedding(
            CANDIDATE_COLLECTION,
            f"candidate_{user_profile.id}",
            embedding,
            {
                'user_profile_id': user_profile.id,
                'resume_analysis_id': resume_analysis.id,
                'career_analysis_id': career_analysis.id if career_analysis else '',
                'embedding_hash': embedding_hash,
                'embedding_model': embedding_model,
            },
        )
    except Exception as exc:
        logger.exception("Candidate embedding generation failed for user_profile_id=%s", user_profile.id)
        metadata.embedding_status = 'failed'
        metadata.error_message = _safe_error_message(exc)
        metadata.save(update_fields=['embedding_status', 'error_message', 'updated_at'])
        return metadata

    metadata.embedding_status = 'completed'
    metadata.error_message = ''
    metadata.save(update_fields=['embedding_status', 'error_message', 'updated_at'])
    return metadata
