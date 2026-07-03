import json
import logging

from django.conf import settings

from .resume_prompts import RESUME_ANALYSIS_SYSTEM_PROMPT, build_resume_analysis_prompt

logger = logging.getLogger(__name__)


class GroqConfigurationError(Exception):
    """Raised when Groq is not configured."""


class GroqResponseError(Exception):
    """Raised when Groq returns unusable output."""


def _load_groq_client():
    api_key = getattr(settings, 'GROQ_API_KEY', '')
    if not api_key:
        raise GroqConfigurationError("GROQ_API_KEY is not configured.")

    try:
        from groq import Groq
    except ImportError as exc:
        raise GroqConfigurationError("The groq package is not installed.") from exc

    return Groq(api_key=api_key)


def _parse_json_response(content: str) -> dict:
    cleaned = content.strip()
    if cleaned.startswith('```'):
        cleaned = cleaned.strip('`')
        if cleaned.lower().startswith('json'):
            cleaned = cleaned[4:].strip()

    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.warning("Groq returned invalid JSON.")
        raise GroqResponseError("Groq returned invalid JSON.") from exc

    if not isinstance(payload, dict):
        raise GroqResponseError("Groq response must be a JSON object.")

    return payload


def analyze_resume_with_groq(resume_text: str) -> tuple[dict, str]:
    return complete_json_with_groq(
        RESUME_ANALYSIS_SYSTEM_PROMPT,
        build_resume_analysis_prompt(resume_text),
    )


def complete_json_with_groq(system_prompt: str, user_prompt: str) -> tuple[dict, str]:
    client = _load_groq_client()
    model = getattr(settings, 'GROQ_MODEL', 'llama-3.1-8b-instant')

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            temperature=0,
            response_format={'type': 'json_object'},
        )
    except Exception as exc:
        logger.exception("Groq JSON completion request failed.")
        raise GroqResponseError("Groq JSON completion request failed.") from exc

    content = response.choices[0].message.content if response.choices else ''
    if not content:
        raise GroqResponseError("Groq returned an empty response.")

    return _parse_json_response(content), model
