import hashlib
import logging
import re

from jobs.models import JobEmbedding

from .embedding_client import generate_embedding, get_embedding_model_name
from .vector_store import JOB_COLLECTION, get_embedding, upsert_embedding

logger = logging.getLogger(__name__)

COMMON_SKILL_TERMS = [
    'python', 'django', 'flask', 'fastapi', 'javascript', 'react', 'node',
    'html', 'css', 'tailwind', 'sql', 'postgresql', 'mysql', 'sqlite',
    'rest api', 'api', 'git', 'docker', 'aws', 'azure', 'linux',
    'machine learning', 'data analysis', 'communication', 'leadership',
]


def _safe_error_message(exc: Exception) -> str:
    return f"Job embedding failed: {exc.__class__.__name__}"


def derive_required_skills(job) -> list[str]:
    text = f"{job.title} {job.description}".lower()
    found = []
    for skill in COMMON_SKILL_TERMS:
        if re.search(rf"(?<!\w){re.escape(skill)}(?!\w)", text):
            found.append(skill)
    return found


def build_job_embedding_text(job) -> str:
    skills = ", ".join(derive_required_skills(job))
    sections = [
        "Job Posting",
        f"Title: {job.title or ''}",
        f"Company: {job.company_name or ''}",
        f"Location: {job.location or ''}",
        f"Description: {job.description or ''}",
        f"Derived Required Skills: {skills}",
    ]
    return "\n".join(section for section in sections if section.strip())


def job_embedding_hash(job) -> str:
    payload = "\n".join([
        job.title or '',
        job.description or '',
        job.company_name or '',
        job.location or '',
        get_embedding_model_name(),
    ])
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def _job_vector_id(job) -> str:
    return f"job_{job.id}"


def _job_vector_exists(job) -> bool:
    try:
        return bool(get_embedding(JOB_COLLECTION, _job_vector_id(job)))
    except Exception:
        logger.exception(
            "Unable to verify job vector in ChromaDB. job_id=%s vector_id=%s",
            job.id,
            _job_vector_id(job),
        )
        return False


def generate_job_embedding(job):
    metadata, _ = JobEmbedding.objects.get_or_create(job=job)
    embedding_hash = job_embedding_hash(job)
    embedding_model = get_embedding_model_name()

    if (
        metadata.embedding_status == 'completed'
        and metadata.embedding_hash == embedding_hash
        and metadata.embedding_model == embedding_model
    ):
        if _job_vector_exists(job):
            return metadata
        logger.warning(
            "Job embedding metadata is completed but ChromaDB vector is missing; regenerating. job_id=%s vector_id=%s",
            job.id,
            _job_vector_id(job),
        )

    metadata.embedding_status = 'pending'
    metadata.embedding_hash = embedding_hash
    metadata.embedding_model = embedding_model
    metadata.error_message = ''
    metadata.save(update_fields=[
        'embedding_status',
        'embedding_hash',
        'embedding_model',
        'error_message',
        'updated_at',
    ])

    try:
        text = build_job_embedding_text(job)
        embedding = generate_embedding(text)
        upsert_embedding(
            JOB_COLLECTION,
            _job_vector_id(job),
            embedding,
            {
                'job_id': job.id,
                'embedding_hash': embedding_hash,
                'embedding_model': embedding_model,
            },
        )
    except Exception as exc:
        logger.exception("Job embedding generation failed for job_id=%s", job.id)
        metadata.embedding_status = 'failed'
        metadata.error_message = _safe_error_message(exc)
        metadata.save(update_fields=['embedding_status', 'error_message', 'updated_at'])
        return metadata

    metadata.embedding_status = 'completed'
    metadata.error_message = ''
    metadata.save(update_fields=['embedding_status', 'error_message', 'updated_at'])
    return metadata
