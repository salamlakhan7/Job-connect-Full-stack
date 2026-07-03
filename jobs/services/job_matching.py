import logging

from django.utils import timezone

from jobs.models import (
    Application,
    CandidateEmbedding,
    Job,
    JobRecommendation,
    JobRecommendationRun,
)

from .job_embedding import derive_required_skills
from .recommendation_explanations import (
    build_explanation_data,
    candidate_skill_set,
    confidence_from_score,
    skill_overlap_score,
)
from .vector_store import CANDIDATE_COLLECTION, JOB_COLLECTION, get_embedding, query_embeddings

logger = logging.getLogger(__name__)

SEMANTIC_WEIGHT = 0.45
SKILLS_WEIGHT = 0.30
READINESS_WEIGHT = 0.15
ATS_WEIGHT = 0.10


class JobMatchingError(Exception):
    """Raised when recommendations cannot be generated."""


def _safe_error_message(exc: Exception) -> str:
    return f"Job matching failed: {exc.__class__.__name__}"


def _clamp_score(value) -> int:
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, score))


def _semantic_score_from_distance(distance) -> int:
    try:
        distance = float(distance)
    except (TypeError, ValueError):
        return 0
    return _clamp_score((1 - distance) * 100)


def _final_score(semantic_score, skills_score, readiness_score, ats_score) -> int:
    return _clamp_score(
        semantic_score * SEMANTIC_WEIGHT
        + skills_score * SKILLS_WEIGHT
        + readiness_score * READINESS_WEIGHT
        + ats_score * ATS_WEIGHT
    )


def _latest_completed_candidate_embedding(user_profile):
    try:
        metadata = user_profile.candidate_embedding
    except CandidateEmbedding.DoesNotExist:
        return None

    if metadata.embedding_status != 'completed':
        return None
    return metadata


def latest_recommendation_run(user_profile):
    return (
        JobRecommendationRun.objects
        .filter(user_profile=user_profile)
        .order_by('-created_at')
        .first()
    )


def refresh_job_recommendations(user_profile, limit=10, query_limit=50):
    candidate_embedding = _latest_completed_candidate_embedding(user_profile)
    run = JobRecommendationRun.objects.create(
        user_profile=user_profile,
        candidate_embedding=candidate_embedding,
        status='pending',
        started_at=timezone.now(),
    )

    try:
        if candidate_embedding is None:
            raise JobMatchingError("Candidate embedding is not completed.")

        candidate_vector = get_embedding(CANDIDATE_COLLECTION, f"candidate_{user_profile.id}")
        if not candidate_vector:
            raise JobMatchingError("Candidate vector was not found.")

        query_embedding = candidate_vector.get('embeddings', [[]])[0]
        results = query_embeddings(JOB_COLLECTION, query_embedding, n_results=query_limit)
        ids = results.get('ids', [[]])[0]
        distances = results.get('distances', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]

        applied_job_ids = set(
            Application.objects
            .filter(applicant=user_profile)
            .values_list('job_id', flat=True)
        )

        resume_analysis = getattr(user_profile, 'resume_analysis', None)
        career_analysis = getattr(resume_analysis, 'career_analysis', None) if resume_analysis else None
        if career_analysis is not None and career_analysis.status != 'completed':
            career_analysis = None

        candidate_skills = candidate_skill_set(resume_analysis, career_analysis) if resume_analysis else set()
        readiness_score = career_analysis.readiness_score if career_analysis else 0
        ats_score = career_analysis.ats_score if career_analysis else 0

        recommendations = []
        for index, _ in enumerate(ids):
            metadata = metadatas[index] if index < len(metadatas) else {}
            job_id = metadata.get('job_id')
            try:
                job_id = int(job_id)
            except (TypeError, ValueError):
                job_id = None
            if not job_id or job_id in applied_job_ids:
                continue

            try:
                job = Job.objects.get(id=job_id)
            except Job.DoesNotExist:
                continue

            semantic_score = _semantic_score_from_distance(distances[index] if index < len(distances) else None)
            job_skills = derive_required_skills(job)
            skills_score, matched_skills, missing_skills = skill_overlap_score(candidate_skills, job_skills)
            final_score = _final_score(semantic_score, skills_score, readiness_score, ats_score)
            confidence = confidence_from_score(final_score)
            score_breakdown = {
                'semantic_score': semantic_score,
                'skills_score': skills_score,
                'readiness_score': _clamp_score(readiness_score),
                'ats_score': _clamp_score(ats_score),
            }
            explanation_data = build_explanation_data(
                job,
                matched_skills,
                missing_skills,
                score_breakdown,
                confidence,
            )
            recommendations.append({
                'job': job,
                'final_score': final_score,
                'semantic_score': semantic_score,
                'skills_score': skills_score,
                'readiness_score': _clamp_score(readiness_score),
                'ats_score': _clamp_score(ats_score),
                'confidence': confidence,
                'explanation_data': explanation_data,
            })

        recommendations.sort(key=lambda item: item['final_score'], reverse=True)
        selected = recommendations[:limit]

        for rank, item in enumerate(selected, start=1):
            JobRecommendation.objects.create(
                run=run,
                user_profile=user_profile,
                job=item['job'],
                rank=rank,
                final_score=item['final_score'],
                semantic_score=item['semantic_score'],
                skills_score=item['skills_score'],
                readiness_score=item['readiness_score'],
                ats_score=item['ats_score'],
                confidence=item['confidence'],
                explanation_data=item['explanation_data'],
            )

        run.status = 'completed'
        run.total_jobs_considered = len(recommendations)
        run.completed_at = timezone.now()
        run.error_message = ''
        run.save(update_fields=['status', 'total_jobs_considered', 'completed_at', 'error_message', 'updated_at'])
        return run
    except Exception as exc:
        logger.exception("Job recommendation refresh failed for user_profile_id=%s", user_profile.id)
        run.status = 'failed'
        run.completed_at = timezone.now()
        run.error_message = _safe_error_message(exc)
        run.save(update_fields=['status', 'completed_at', 'error_message', 'updated_at'])
        return run
