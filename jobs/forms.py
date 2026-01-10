from django import forms
from .models import UserProfile, Skill, Education, Experience, SocialLink

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'location', 'dob', 'summary', 'professional_title', 'profile_picture', 'resume']


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['name', 'proficiency_level']


class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['degree', 'institution', 'start_year', 'end_year', 'grade']


class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ['job_title', 'company_name', 'start_date', 'end_date', 'description']


class SocialLinkForm(forms.ModelForm):
    class Meta:
        model = SocialLink
        fields = ['platform', 'url']

from .models import Job

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description', 'location']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full border px-3 py-2 rounded'}),
            'description': forms.Textarea(attrs={'class': 'w-full border px-3 py-2 rounded'}),
            'location': forms.TextInput(attrs={'class': 'w-full border px-3 py-2 rounded'}),
        }