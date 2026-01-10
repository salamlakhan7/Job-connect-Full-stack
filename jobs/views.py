from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile
from .forms import JobForm
from django.contrib.auth.decorators import login_required
from .decorators import seeker_required, employer_required  # ✅ Add this line
from django.contrib.auth import authenticate, login
from django.shortcuts import  get_object_or_404
from .forms import ProfileForm, SkillForm, EducationForm, ExperienceForm, SocialLinkForm
from django.contrib.auth import logout
import os
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.files.uploadedfile import UploadedFile

from .models import UserProfile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Job, Application, UserProfile  # update import as needed
from django.contrib.auth.decorators import login_required

from .models import Job, Application, UserProfile, SavedJob

# Create your views here.


def landing(request):
    categories = [
        "IT & Software", "Marketing", "Finance",
        "Sales", "Remote Jobs", "Part-time Jobs"
    ]
    featured_jobs = range(6)      # To render 6 job cards
    testimonials = range(3)       # To render 3 testimonial cards

    return render(request, "landing.html", {
        "categories": categories,
        "featured_jobs": featured_jobs,
        "testimonials": testimonials,
    })
    
    
    
def choose_role(request):
    return render(request, 'choose_role.html')
    


@login_required
def redirect_dashboard(request):
    profile = UserProfile.objects.get(user=request.user)

    if profile.role == 'seeker':
        return redirect('seeker_dashboard')
    elif profile.role == 'employer':
        return redirect('employer_dashboard')
    else:
        return redirect('home')  # fallback

# @login_required
# @seeker_required
# def seeker_dashboard(request):
#     return render(request, 'seeker_dashboard.html')

@login_required
@seeker_required
def seeker_dashboard(request):
    user = request.user

    # Get seeker profile
    try:
        seeker_profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        messages.error(request, "Seeker profile not found.")
        return redirect('home')

    # Jobs the seeker has applied to
    applied_jobs = Application.objects.filter(applicant=seeker_profile).count()

    # Saved jobs (if you want, for now = 0)
    # saved_jobs = 0
    saved_jobs = SavedJob.objects.filter(user_profile=seeker_profile).count()

    # Interviews scheduled (no field yet)
    interviews = 0

    # Recommended Jobs (for now show all active jobs)
    recommended_jobs = Job.objects.all().order_by('-created_at')

    context = {
        "applied_jobs": applied_jobs,
        "saved_jobs": saved_jobs,
        "interviews": interviews,
        "recommended_jobs": recommended_jobs,
    }

    return render(request, "seeker_dashboard.html", context)


def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    return render(request, 'job_detail.html', {'job': job})


from .models import Job, Application

@login_required
@seeker_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    seeker_profile = request.user.userprofile

    # Prevent duplicate applications
    if Application.objects.filter(job=job, applicant=seeker_profile).exists():
        messages.warning(request, "You have already applied for this job.")
        return redirect('job_detail', job_id=job.id)

    if request.method == "POST":
        resume = request.FILES.get('resume')
        cover_letter = request.POST.get('cover_letter', '')

        Application.objects.create(
            job=job,
            applicant=seeker_profile,
            resume=resume,
            cover_letter=cover_letter
        )

        messages.success(request, "Your application has been submitted successfully!")
        return redirect('seeker_dashboard')

    return render(request, "apply_job.html", {"job": job})


# @login_required
# @employer_required
# def employer_dashboard(request):
#     return render(request, 'employer_dashboard.html')

@login_required
def employer_dashboard(request):
    user = request.user

    # Get employer UserProfile
    try:
        employer_profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        messages.error(request, "Employer profile not found.")
        return redirect('home')

    # Fetch ALL jobs created by this employer
    jobs = Job.objects.filter(employer=user).order_by('-created_at')

    # Active job posts (for now: all)
    active_jobs_count = jobs.count()

    # Total applications across all jobs posted by this employer
    applications_count = Application.objects.filter(job__in=jobs).count()

    # Pending reviews logic (example: no status field in your model)
    pending_reviews = applications_count  # OR assign 0 if you want
    
    context = {
        "jobs": jobs,
        "active_jobs_count": active_jobs_count,
        "applications_count": applications_count,
        "pending_reviews": pending_reviews,
    }

    return render(request, "employer_dashboard.html", context)



@login_required
def dashboard_redirect(request):
    profile = getattr(request.user, 'userprofile', None)

    if profile:
        if profile.role == 'seeker':
            return redirect('seeker_dashboard')
        elif profile.role == 'employer':
            return redirect('employer_dashboard')

    messages.warning(request, "User role not defined.")
    return redirect('home')

def register_seeker(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Password check
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('register_seeker')

        # Email check
        if User.objects.filter(username=email).exists():
            messages.error(request, "Email is already registered!")
            return redirect('register_seeker')

        # Create user with email as username
        user = User.objects.create_user(
            username=email,        # ✅ Correct
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Assign job seeker role
        UserProfile.objects.create(user=user, role='seeker')

        messages.success(request, "Registered successfully! Please log in.")
        return redirect('login')

    return render(request, 'register_seeker.html')

def register_employer(request):
    if request.method == "POST":
        company_name = request.POST.get('company_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # ✅ Check password match
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('register_employer')

        # ✅ Check duplicate email
        if User.objects.filter(username=email).exists():
            messages.error(request, "Email is already registered!")
            return redirect('register_employer')

        # ✅ Create user
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=company_name  # or store company name separately if needed
        )

        # ✅ Assign Role: Employer
        UserProfile.objects.create(user=user, role='employer')

        messages.success(request, "Employer account created successfully! Please log in.")
        return redirect('login')

    return render(request, 'register_employer.html')

def categories(request):
    return render(request, 'categories.html')

def jobs_list(request):
    return render(request, 'samplejobs.html')

def how_it_works(request):
    return render(request, 'howitworks.html')

def contact(request):
    return render(request, 'contact.html')

def about(request):
    return render(request, 'about.html')

def custom_login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)

            # ✅ Get user's role from UserProfile
            profile = UserProfile.objects.get(user=user)

            # ✅ Redirect based on role
            if profile.role == 'seeker':
                return redirect('seeker_dashboard')
            elif profile.role == 'employer':
                return redirect('employer_dashboard')
            else:
                messages.error(request, "Invalid role assigned.")
                return redirect('home')

        else:
            messages.error(request, "Invalid email or password.")
            return redirect('login')

    return render(request, 'registration/login.html')



ALLOWED_RESUME_EXT = {'.pdf', '.docx'}


def _is_allowed_resume(filename: str) -> bool:
    _, ext = os.path.splitext(filename.lower())
    return ext in ALLOWED_RESUME_EXT


@login_required
@seeker_required
def seeker_profile(request):
    """
    GET: render seeker_profile.html with current profile
    POST: handle resume upload (form with file input 'resume')
    """
    # get or create profile (ensure role = 'seeker' if you want enforce)
    profile, created = UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'seeker'})

    # Handle resume upload from the simple form (multipart/form-data)
    if request.method == 'POST':
        # Expecting file input named 'resume'
        uploaded: UploadedFile = request.FILES.get('resume')
        if not uploaded:
            # No file provided; redirect back with a message (you can set messages if desired)
            return redirect('seeker_profile')

        # Basic validation: extension
        if not _is_allowed_resume(uploaded.name):
            # Optionally add a message for the user or return a bad request
            return HttpResponseBadRequest("Invalid file type. Only PDF or DOCX allowed.")

        # Save file to the resume field (Django handles storage to MEDIA_ROOT)
        profile.resume = uploaded
        profile.save()
        # Redirect back so user sees the updated resume link
        return redirect('seeker_profile')

    # GET (or other non-POST) – render page
    context = {
        'profile': profile,
        # convenient fields (template expects user.userprofile.* and user.*)
    }
    return render(request, 'seeker_profile.html', context)


@csrf_exempt  # AJAX POST from fetch; we still require authentication, so check request.user below
@login_required
@seeker_required
def update_seeker_profile(request):
    """
    AJAX endpoint for modal-based updates.
    Expects JSON body: { "name": "Full Name", "tags": "tag1 | tag2", "location": "City, Country" }
    Responds with JSON {"status":"success"} (or error).
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'method_not_allowed'}, status=405)

    # parse JSON
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'status': 'invalid_json'}, status=400)

    user = request.user
    profile = getattr(user, 'userprofile', None)
    if profile is None:
        # if for some reason profile is missing, create it with role seeker
        profile = UserProfile.objects.create(user=user, role='seeker')

    # Update name
    full_name = payload.get('name', '').strip()
    if full_name:
        # split into first / last (simple heuristic)
        if ' ' in full_name:
            first, rest = full_name.split(' ', 1)
            user.first_name = first
            user.last_name = rest
        else:
            user.first_name = full_name
            user.last_name = ''
        user.save()

    # Update tags and location on profile
    tags = payload.get('tags')
    if tags is not None:
        # normalize whitespace around separators (optional)
        profile.tags = tags.strip()

    location = payload.get('location')
    if location is not None:
        profile.location = location.strip()

    # Save profile changes
    profile.save()

    # Return success and optionally the updated fields
    return JsonResponse({
        'status': 'success',
        'name': f"{user.first_name} {user.last_name}".strip(),
        'tags': profile.tags,
        'location': profile.location,
    })

    return render(request, 'seeker_profile.html', context)

def custom_logout(request):
    logout(request)
    return redirect('home')

from .forms import JobForm
from .forms import JobForm
from .models import Interview


# EMPLOYER JOB MANAGEMENT VIEWS
from django.shortcuts import render, redirect, get_object_or_404
from .models import Job
from django.contrib import messages


# -----------------------
# EMPLOYER: LIST ALL JOBS
# -----------------------
@login_required
@employer_required
def employer_jobs(request):
    profile = get_object_or_404(UserProfile, user=request.user, role="employer")
    jobs = Job.objects.filter(employer=request.user)
    return render(request, "employer/employer_jobs.html", {"jobs": jobs})


@employer_required
@login_required
def post_job(request):
    if request.method == "POST":
        company_name = request.POST.get("company_name")
        title = request.POST.get("title")
        location = request.POST.get("location")
        description = request.POST.get("description")

        Job.objects.create(
            employer=request.user,
            employer_profile=UserProfile.objects.get(user=request.user),
            company_name=company_name,
            title=title,
            location=location,
            description=description
        )

        messages.success(request, "Job posted successfully!")
        return redirect("post_job")

    return render(request, "employer/post_job.html")



@employer_required
@login_required
def edit_job(request, job_id):
    profile = get_object_or_404(UserProfile, user=request.user, role="employer")
    job = get_object_or_404(Job, id=job_id, employer=request.user)

    if request.method == "POST":
        job.title = request.POST.get("title")
        job.description = request.POST.get("description")
        job.location = request.POST.get("location")
        # job.salary = request.POST.get("salary")
        job.save()

        messages.success(request, "Job updated successfully!")
        return redirect("employer_jobs")

    return render(request, "employer/edit_job.html", {"job": job})



@employer_required
# -----------------------
# EMPLOYER: DELETE JOB khan
# -----------------------
@login_required
def delete_job(request, job_id):
    profile = get_object_or_404(UserProfile, user=request.user, role="employer")
    job = get_object_or_404(Job, id=job_id, employer=request.user)

    if request.method == "POST":
        job.delete()
        messages.success(request, "Job deleted successfully!")
        return redirect("employer_jobs")

    return render(request, "employer/delete_job_confirm.html", {"job": job})


# -----------------------
# EMPLOYER: VIEW APPLICANTS
# -----------------------
@login_required
@employer_required  # keep your decorator
def view_applicants(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    # ensure current user owns this job
    if job.employer != request.user:
        messages.error(request, "Not authorized.")
        return redirect('employer_dashboard')

    applicants = Application.objects.filter(job=job).select_related('applicant__user').order_by('-applied_at')
    return render(request, 'view_applicants.html', {
        'job': job,
        'applicants': applicants
    })

@login_required
@employer_required
def update_application_status(request, job_id, app_id):
    job = get_object_or_404(Job, id=job_id)
    if job.employer != request.user:
        messages.error(request, "Not authorized.")
        return redirect('employer_dashboard')

    app = get_object_or_404(Application, id=app_id, job=job)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Application.STATUS_CHOICES):
            app.status = new_status
            app.save()
            messages.success(request, "Status updated.")
    return redirect('view_applicants', job_id=job.id)


@login_required
def save_job(request, job_id):
    seeker = getattr(request.user, 'userprofile', None)
    if not seeker:
        messages.error(request, "Please complete profile.")
        return redirect('job_detail', job_id=job_id)
    job = get_object_or_404(Job, id=job_id)
    SavedJob.objects.get_or_create(user_profile=seeker, job=job)
    messages.success(request, "Job saved.")
    return redirect('job_detail', job_id=job_id)

@login_required
def unsave_job(request, job_id):
    seeker = getattr(request.user, 'userprofile', None)
    job = get_object_or_404(Job, id=job_id)
    SavedJob.objects.filter(user_profile=seeker, job=job).delete()
    messages.success(request, "Job removed from saved.")
    return redirect('seeker_saved_jobs')

@login_required
def seeker_saved_jobs(request):
    seeker = getattr(request.user, 'userprofile', None)
    saved = SavedJob.objects.filter(user_profile=seeker).select_related('job').order_by('-saved_at')
    return render(request, 'seeker/saved_jobs.html', {'saved': saved})


def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    saved_jobs_ids = []
    if request.user.is_authenticated:
        seeker = getattr(request.user, 'userprofile', None)
        if seeker:
            saved_jobs_ids = list(SavedJob.objects.filter(user_profile=seeker).values_list('job_id', flat=True))
    return render(request, 'job_detail.html', {'job': job, 'saved_jobs_ids': saved_jobs_ids})


from django.db.models import Q
def job_search(request):
    q = request.GET.get('q','').strip()
    location = request.GET.get('location','').strip()

    jobs = Job.objects.all().order_by('-created_at')

    if q:
        jobs = jobs.filter(Q(title__icontains=q) | Q(description__icontains=q))

    if location:
        jobs = jobs.filter(location__icontains=location)

    from django.core.paginator import Paginator
    paginator = Paginator(jobs, 10)
    page = request.GET.get('page', 1)
    jobs_page = paginator.get_page(page)

    return render(request, 'search_results.html',
                  {'jobs': jobs_page, 'q': q, 'location': location})




from django.shortcuts import render, redirect, get_object_or_404
from .models import Job, SavedJob

from .models import Job, SavedJob, UserProfile

def save_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    user_profile = get_object_or_404(UserProfile, user=request.user)

    SavedJob.objects.get_or_create(
        user_profile=user_profile,
        job=job
    )

    return redirect(request.META.get('HTTP_REFERER', '/'))


def unsave_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    user_profile = get_object_or_404(UserProfile, user=request.user)

    SavedJob.objects.filter(
        user_profile=user_profile,
        job=job
    ).delete()

    return redirect(request.META.get('HTTP_REFERER', '/'))



def saved_jobs(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)

    saved = SavedJob.objects.filter(
        user_profile=user_profile
    ).select_related('job')

    return render(request, 'seeker/saved_jobs.html', {'saved': saved})



@login_required
def seeker_applied_jobs(request):
    seeker_profile = getattr(request.user, 'userprofile', None)
    if not seeker_profile:
        messages.error(request, "Profile not found.")
        return redirect('home')
    applications = Application.objects.filter(applicant=seeker_profile).select_related('job').order_by('-applied_at')
    return render(request, 'seeker/applied_jobs.html', {'applications': applications})


@login_required
@seeker_required
def all_jobs(request):
    jobs = Job.objects.all().order_by('-created_at')   # latest first
    return render(request, "seeker/all_jobs.html", {"jobs": jobs})

@login_required
@employer_required
def update_application_status(request, job_id, app_id):
    job = get_object_or_404(Job, id=job_id)

    # Ensure employer owns the job
    if job.employer != request.user:
        messages.error(request, "Not authorized.")
        return redirect('employer_dashboard')

    app = get_object_or_404(Application, id=app_id, job=job)

    if request.method == 'POST':
        new_status = request.POST.get('status')

        if new_status in dict(Application.STATUS_CHOICES):
            app.status = new_status
            app.save()
            messages.success(request, "Application status updated.")

    return redirect('view_applicants', job_id=job.id)


@login_required
@employer_required
def schedule_interview(request, app_id):
    application = get_object_or_404(Application, id=app_id)

    # Ensure employer owns this job
    if application.job.employer != request.user:
        messages.error(request, "Not authorized.")
        return redirect('employer_dashboard')

    # Prevent duplicate interviews (since OneToOne)
    if hasattr(application, "interview"):
        messages.error(request, "Interview already scheduled for this application.")
        return redirect('view_applicants', job_id=application.job.id)

    if request.method == "POST":
        Interview.objects.create(
            application=application,
            employer=request.user,                           # NEW
            date=request.POST.get("date"),
            meeting_link=request.POST.get("meeting_link", ""),  # NEW
            notes=request.POST.get("notes", "")
        )

        # Update application status
        application.status = "interview"
        application.save()

        messages.success(request, "Interview scheduled successfully!")
        return redirect('view_applicants', job_id=application.job.id)

    return render(request, "employer/schedule_interview.html", {
        "application": application
    })

# def chat_view(request, applicant_id):
#         return render(request, 'employer/chat_room.html', {
#         "applicant_id": applicant_id
#     })
        
@login_required
@seeker_required
def my_applications(request):
    seeker_profile = UserProfile.objects.get(user=request.user)
    applications = Application.objects.filter(applicant=seeker_profile).select_related('job').order_by('-applied_at')

    return render(request, "seeker/seeker_applications.html", {
        "applications": applications
    })

from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
import os

@login_required
@require_POST
def chat_upload(request):
    """
    Save uploaded file and return JSON:
    { file_url: '/media/...', file_path: 'chat/<conv>/filename', content_type, size, name }
    """
    f = request.FILES.get('file')
    if not f:
        return HttpResponseBadRequest("No file uploaded.")

    # optional: limit file size
    max_mb = 25
    if f.size > max_mb * 1024 * 1024:
        return HttpResponseBadRequest("File too large")

    # Save under media/chat/temp/<user> or accept conversation_id
    conv = request.POST.get('conversation_id')
    if conv:
        folder = f'chat/{conv}'
    else:
        folder = f'chat/temp/{request.user.id}'

    filename = default_storage.save(os.path.join(folder, f.name), f)
    file_url = default_storage.url(filename)   # usually /media/...
    return JsonResponse({
        "file_url": file_url,
        "file_path": filename,  # relative storage path
        "content_type": f.content_type,
        "size": f.size,
        "name": f.name
    })


from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import ChatRoom, ChatMessage
from django.contrib import messages
from django.shortcuts import redirect



@login_required
@login_required
def chat_list_view(request):
    # Find the most recent conversation
    latest_room = ChatRoom.objects.filter(
        Q(employer=request.user) | Q(seeker=request.user)
    ).order_by('-created_at').first()

    if latest_room:
        return redirect('chat_room', conversation_id=latest_room.id)

    # If no conversations, show empty list (we can reuse the same template or a specific one)
    # For now, let's just render the 'chat_list.html' which we will update to look like an empty state
    return render(request, 'employer/chat_list.html', {
        'conversations': [] 
    })

# @login_required
# def chat_room_view(request, conversation_id):
#     convo = get_object_or_404(Conversation, id=conversation_id)
#     # permission check
#     if not Participant.objects.filter(conversation=convo, user=request.user).exists():
#         messages.error(request, "You are not part of this conversation.")
#         return redirect('chat_list')

#     # other participant
#     other_participant = convo.participants.exclude(user=request.user).first()
#     other_user = other_participant.user if other_participant else request.user

#     # fetch last 100 messages
#     messages_qs = convo.messages.select_related('sender').prefetch_related('attachments').order_by('created_at')[:500]

#     return render(request, 'chat_room.html', {
#         'conversation': convo,
#         'other_user': other_user,
#         'messages': messages_qs,
#         'ws_url': f"/ws/chat/{convo.id}/",
#         'meeting_link': '',  # optional: populate if you have Interview.meeting_link
#     })

@login_required
@login_required
def chat_room_view(request, conversation_id):
    room = get_object_or_404(ChatRoom, id=conversation_id)

    if request.user not in [room.employer, room.seeker]:
        messages.error(request, "You are not allowed here.")
        return redirect('chat_list')
    
         #important 
        # 🔑 Decide base template by role
    profile = request.user.userprofile
    if profile.role == "employer":
        base_template = "employer_base.html"
    else:
        base_template = "base.html"
       #important 
       
    # Fetch all conversations for the sidebar
    rooms = ChatRoom.objects.filter(
        Q(employer=request.user) | Q(seeker=request.user)
    ).order_by('-created_at')

    conversations = []
    for r in rooms:
        last_msg = r.messages.order_by('-created_at').first()
        other = r.seeker if r.employer == request.user else r.employer
        conversations.append({
            'id': r.id,
            'title': other.first_name if other.first_name else other.username, # Use first name
            'other_user': other,
            'last_message_preview': last_msg.content[:50] if last_msg else '',
            'last_message_time': last_msg.created_at if last_msg else r.created_at,
            'is_active': (r.id == room.id)
        })

    chat_messages = room.messages.select_related('sender').prefetch_related('attachments').order_by('created_at')
    other_user = room.seeker if room.employer == request.user else room.employer

    return render(request, 'employer/chat_room.html', {
        'base_template': base_template,   # ✅ IMPORTANT
        'conversations': conversations,
        'conversation': room,
        'chat_history': chat_messages,  # This matches the template variable
        'other_user': other_user,
        'ws_url': f"/ws/chat/{room.id}/",
        'meeting_link': '',
    })

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Application, ChatRoom

# @login_required
# def start_chat(request, application_id):
#     application = get_object_or_404(Application, id=application_id)

#     # Employer (Job owner)
#     employer = application.job.employer   # User

#     # Job Seeker (UserProfile → User)
#     seeker = application.applicant.user   # ✅ FIX

#     # Create or get chat room per job + seeker
#     room, created = ChatRoom.objects.get_or_create(
#         job=application.job,
#         applicant=application.applicant,
#         defaults={
#             'name': f"{seeker.username} - {application.job.title}"
#         }
#     )

#     # Add participants (ManyToMany User)
#     room.participants.add(employer, seeker)

#     return redirect('chat_room', conversation_id=room.id)


@login_required
def chat_start_view(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    employer = application.job.employer
    seeker = application.applicant.user
    
    if request.user not in [employer, seeker]:
        return redirect('chat_list')

    chat_room, created = ChatRoom.objects.get_or_create(employer=employer, seeker=seeker)
    return redirect('chat_room', conversation_id=chat_room.id)

@login_required
def start_chat_from_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    employer = job.employer
    seeker = request.user 
    
    # If user is the employer themselves, redirect to their dashboard
    if seeker == employer:
        messages.warning(request, "You cannot chat with yourself.")
        return redirect('job_detail', job_id=job.id)

    # Ensure profile role
    profile = getattr(seeker, 'userprofile', None)
    if profile and profile.role == 'employer':
         # If an employer views another's job, treated as just user? 
         # Or prevent? Let's allow for now as "user".
         pass

    # Create/Get room
    chat_room, created = ChatRoom.objects.get_or_create(employer=employer, seeker=seeker)
    return redirect('chat_room', conversation_id=chat_room.id)
    seeker = application.applicant.user           # User

    # Safety check: only employer or seeker can open chat
    if request.user not in [employer, seeker]:
        return redirect('chat_list')

    # Create or get chat room
    chat_room, created = ChatRoom.objects.get_or_create(
        employer=employer,
        seeker=seeker
    )

    return redirect('chat_room', conversation_id=chat_room.id)