from django.db.models import Exists, OuterRef, Q

from .models import Application, ChatRoom


CHAT_ALLOWED_STATUSES = frozenset({
    'shortlisted',
    'interview',
    'hired',
})


def is_chat_status_allowed(status):
    return status in CHAT_ALLOWED_STATUSES


def can_chat_for_application(application, user=None):
    if not is_chat_status_allowed(application.status):
        return False

    if user is None:
        return True

    return user.id in {
        application.job.employer_id,
        application.applicant.user_id,
    }


def eligible_application_exists(employer, seeker, job=None):
    applications = Application.objects.filter(
        job__employer=employer,
        applicant__user=seeker,
        status__in=CHAT_ALLOWED_STATUSES,
    )
    if job is not None:
        applications = applications.filter(job=job)
    return applications.exists()


def can_access_chat_room(user, room):
    if not user.is_authenticated:
        return False
    if user.id not in {room.employer_id, room.seeker_id}:
        return False
    return eligible_application_exists(room.employer, room.seeker)


def accessible_chat_rooms(user):
    if not user.is_authenticated:
        return ChatRoom.objects.none()

    eligible_application = Application.objects.filter(
        job__employer_id=OuterRef('employer_id'),
        applicant__user_id=OuterRef('seeker_id'),
        status__in=CHAT_ALLOWED_STATUSES,
    )
    return ChatRoom.objects.filter(
        Q(employer=user) | Q(seeker=user)
    ).annotate(
        chat_is_eligible=Exists(eligible_application)
    ).filter(chat_is_eligible=True)
