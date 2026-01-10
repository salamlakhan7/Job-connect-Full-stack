from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def redirect_logout(request):
    return redirect('logout')

urlpatterns = [
    path('', views.landing, name='home'),
    path('RegistrationOptions/', views.choose_role, name='choose_role'),
    path('register/seeker/login', views.register_seeker, name='register_seeker'),
    path('register/employer/', views.register_employer, name='register_employer'),
    
        # New pages
    path('categories/', views.categories, name='categories'),
    path('samplejobs/', views.jobs_list, name='jobs'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    
    #Job Seeker
    path('dashboard/', views.redirect_dashboard, name='dashboard'),
    path('seeker_profile/', views.seeker_profile, name='seeker_profile'),
    
    #job Seeker profile
    path('seeker/profile/', views.seeker_profile, name='seeker_profile'),
    path('seeker/profile/update/', views.update_seeker_profile, name='update_seeker_profile'),
    
    # Role Dashboards
    path('accounts/logout/', redirect_logout), 
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    
    path('seeker/dashboard/', views.seeker_dashboard, name='seeker_dashboard'),
    path('employer/dashboard/', views.employer_dashboard, name='employer_dashboard'),
    
    path('redirect_dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    
    # Employer Section
    path('employer/dashboard/', views.employer_dashboard, name='employer_dashboard'),
 
    # Employer Job Management key urls
    path("employer/jobs/", views.employer_jobs, name="employer_jobs"),
    path("employer/job/post/", views.post_job, name="post_job"),
    path("employer/job/<int:job_id>/edit/", views.edit_job, name="edit_job"),
    path("employer/job/<int:job_id>/delete/", views.delete_job, name="delete_job"),
    path("employer/job/<int:job_id>/applicants/", views.view_applicants, name="view_applicants"),
    
    #seeker logic urls
    path('job/<int:job_id>/', views.job_detail, name='job_detail'),
    path('job/<int:job_id>/apply/', views.apply_job, name='apply_job'),
    path('seeker/applied/', views.seeker_applied_jobs, name='seeker_applied'),
    
    path('employer/job/<int:job_id>/applicant/<int:app_id>/status/',views.update_application_status, name='update_application_status'),
    path("application/<int:app_id>/interview/", views.schedule_interview, name="schedule_interview"),
    
    # path('chat/<int:applicant_id>/', views.chat_view, name='chat'),
    
    
    path('job/<int:job_id>/save/', views.save_job, name='save_job'),
    path('job/<int:job_id>/unsave/', views.unsave_job, name='unsave_job'),
    path('seeker/saved/', views.seeker_saved_jobs, name='seeker_saved_jobs'),
    
    path('jobs/search/', views.job_search, name='job_search'),
    
    path('search/', views.job_search, name='job_search'),
    path('job/<int:job_id>/', views.job_detail, name='job_detail'),

   path('save-job/<int:job_id>/', views.save_job, name='save_job'),
   path('unsave-job/<int:job_id>/', views.unsave_job, name='unsave_job'),
   path('saved-jobs/', views.saved_jobs, name='saved_jobs'),
   
   
  path('jobs/all/', views.all_jobs, name="all_jobs"),
  path('seeker/applications/', views.my_applications, name='my_applications'),
  
  path('chat/', views.chat_list_view, name='chat_list'),
  path('chat/start/<int:application_id>/', views.chat_start_view, name='chat_start'),
  path('chat/job/<int:job_id>/', views.start_chat_from_job, name='start_chat_from_job'),  # New
  path('chat/upload/', views.chat_upload, name='chat_upload'),
  path('chat/<int:conversation_id>/', views.chat_room_view, name='chat_room'),


]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)