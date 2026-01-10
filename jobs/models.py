from django.db import models
from django.contrib.auth.models import User
# from .model_chatroom import ChatRoom, ChatMessage, ChatAttachment



@property
def profile_picture_url(self):
    if self.profile_picture and hasattr(self.profile_picture, 'url'):
        return self.profile_picture.url
    return '/static/Abimg.png'


# jobs/models.py or accounts/models.py

# class UserProfile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     location = models.CharField(max_length=255, blank=True, null=True)
#     tags = models.CharField(max_length=255, blank=True, null=True)

#     def __str__(self):
#         return self.user.username



class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('seeker', 'Job Seeker'),
        ('employer', 'Employer'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=100, blank=True)
    dob = models.DateField(null=True, blank=True)
    summary = models.TextField(blank=True)
    professional_title = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    tags = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


# class UserProfile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     phone = models.CharField(max_length=15, blank=True)
#     location = models.CharField(max_length=100, blank=True)
#     dob = models.DateField(null=True, blank=True)
#     summary = models.TextField(blank=True)
#     professional_title = models.CharField(max_length=100, blank=True)
#     profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
#     resume = models.FileField(upload_to='resumes/', blank=True, null=True)

#     def __str__(self):
#         return self.user.username
    
    
class Education(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='educations')
    degree = models.CharField(max_length=100)
    institution = models.CharField(max_length=150)
    start_year = models.IntegerField()
    end_year = models.IntegerField(blank=True, null=True)
    grade = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.degree} at {self.institution}"


class Experience(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='experiences')
    job_title = models.CharField(max_length=100)
    company_name = models.CharField(max_length=150)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.job_title} at {self.company_name}"


class Skill(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=50)
    proficiency_level = models.CharField(
        max_length=20,
        choices=[
            ('Beginner', 'Beginner'),
            ('Intermediate', 'Intermediate'),
            ('Advanced', 'Advanced'),
            ('Expert', 'Expert')
        ]
    )

    def __str__(self):
        return f"{self.name} ({self.proficiency_level})"


class SocialLink(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='social_links')
    platform = models.CharField(max_length=50, choices=[
        ('LinkedIn', 'LinkedIn'),
        ('GitHub', 'GitHub'),
        ('Portfolio', 'Portfolio'),
        ('Twitter', 'Twitter')
    ])
    url = models.URLField()

    def __str__(self):
        return f"{self.platform} - {self.user_profile.user.username}"


class Job(models.Model):
    employer = models.ForeignKey(User, on_delete=models.CASCADE)
    employer_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, null=True, blank=True)
    company_name = models.CharField(max_length=255, default="")   # <-- Add this
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=150)
    # salary = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# class Application(models.Model):
#     job = models.ForeignKey(Job, on_delete=models.CASCADE)
#     applicant = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
#     resume = models.FileField(upload_to='applications/', null=True, blank=True)
#     cover_letter = models.TextField(blank=True)
#     applied_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.applicant.user.username} → {self.job.title}"


# from django.db import models
# from django.contrib.auth.models import User

# existing UserProfile, Job, Application here...
# Add status choices for Application (if not present) and SavedJob:

class Application(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('interview', 'Interview Scheduled'),
        ('hired', 'Hired'),
    ]
    job = models.ForeignKey('Job', on_delete=models.CASCADE)
    applicant = models.ForeignKey('UserProfile', on_delete=models.CASCADE)
    resume = models.FileField(upload_to='applications/', null=True, blank=True)
    cover_letter = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.applicant.user.username} → {self.job.title}"
    

class SavedJob(models.Model):
    user_profile = models.ForeignKey('UserProfile', on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey('Job', on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_profile', 'job')

    def __str__(self):
        return f"{self.user_profile.user.username} saved {self.job.title}"

# class Message(models.Model):
#     sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
#     receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
#     message = models.TextField()
#     timestamp = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.sender.username} → {self.receiver.username}"


# class Interview(models.Model):
#     application = models.OneToOneField(Application, on_delete=models.CASCADE)
#     date = models.DateTimeField()
#     notes = models.TextField(blank=True)

#     def __str__(self):
#         return f"Interview for {self.application.applicant.user.username}"

class Interview(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    employer = models.ForeignKey(User, on_delete=models.CASCADE)
    scheduled_date = models.DateTimeField()
    location = models.CharField(max_length=255)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interview for {self.application.user.username} on {self.scheduled_date}"




# class ChatRoom(models.Model):
#     # a room for two users (employer & seeker) or group
#     name = models.CharField(max_length=100, unique=True)
#     created_at = models.DateTimeField(auto_now_add=True)
    
# class ChatRoom(models.Model):
#     job = models.ForeignKey(Job, on_delete=models.CASCADE)
#     applicant = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
#     participants = models.ManyToManyField(User)
#     name = models.CharField(max_length=255)
#     created_at = models.DateTimeField(auto_now_add=True)


# class ChatMessage(models.Model):
#     room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
#     sender = models.ForeignKey(User, on_delete=models.CASCADE)
#     text = models.TextField(blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)


# class ChatRoom(models.Model):
#     employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='employer_chatrooms')
#     seeker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seeker_chatrooms')
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('employer', 'seeker')

# =========================
# CHAT MODELS
# =========================

class ChatRoom(models.Model):
    employer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='employer_chatrooms'
    )
    seeker = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='seeker_chatrooms'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employer', 'seeker')

    def __str__(self):
        return f"{self.employer.username} ↔ {self.seeker.username}"

# class ChatMessage(models.Model):
class ChatMessage(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
    ]

    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_messages'
    )
    content = models.TextField(blank=True)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='text')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"


class ChatAttachment(models.Model):
    message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='chat_files/')
    content_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name
