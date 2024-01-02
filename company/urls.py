from django.urls import path,include
from . import views
from django.contrib import admin

urlpatterns = [

    path('',views.index,name='index'),
    path('demo',views.demo,name='demo'),
    path('job_list/<str:department>',views.job_list,name='job_list'),
    path('location_related_jobs/<str:location>',views.location_related_jobs,name='location_related_jobs'),
    path('user_job_list/<str:department>',views.user_job_list,name='user_job_list'),
    path('registration',views.registration,name='registration'),
    path('companies',views.companies,name='companies'),
    path('all_companies',views.all_companies,name='all_companies'),
    path('all_jobs',views.all_jobs,name='all_jobs'),
    path('saved_jobs',views.saved_jobs,name='saved_jobs'),
    path('company/<int:id>',views.company,name='company'),
    path('single_job/<int:job_id>/<int:u_id>',views.single_job,name='single_job'),
    path('user_single_job/<int:job_id>/<int:u_id>',views.user_single_job,name='user_single_job'),
    path('search_results',views.search_results,name='search_results'),
    path('autocomplete-job-title/', views.autocomplete_job_title_suggestions, name='autocomplete_job_title'),
    path('autocomplete-location-title/', views.autocomplete_location_suggestions, name='autocomplete_location_title'),
    path('user_search_results',views.user_search_results,name='user_search_results'),
    path('work_mode/<str:selected_work_mode>/', views.work_mode, name='work_mode'),
    path('user_work_mode/<str:selected_work_mode>/', views.user_work_mode, name='user_work_mode'),
    path('login',views.login1,name='login1'),
    path('add_company_details',views.add_company_details,name='add_company_details'),
    path('user_login',views.user_login,name='user_login'),
    path('company_dashboard',views.company_dashboard,name='company_dashboard'),
    path('job_vacancy',views.job_vacancy,name='job_vacancy'),
    path('add_job',views.add_job,name='add_job'),
    path('user_registration',views.user_registration,name='user_registration'),
    path('user_details',views.user_details,name='user_details'),
    path('user_dashboard',views.user_dashboard1,name='user_dashboard'),
    path('delete_jobs/<int:pk>/', views.delete_jobs, name='delete_jobs'),
    path('jobs',views.jobs,name="jobs"),
    path('profile',views.profile,name="profile"),
    path('job_description/<int:job_id>/<int:u_id>',views.job_description,name="job_description"),
    path('application/<int:job_id>/<int:u_id>',views.application,name="application"),
    path('save_job/<int:job_id>/<int:u_id>/',views.save_job,name="save_job"),
    path('remove_job/<int:job_id>/<int:u_id>/',views.remove_job,name="remove_job"),
    path('job_applications',views.job_applications,name="job_applications"),
    path('application_status',views.application_status,name="application_status"),
    path('selected',views.selected,name="selected"),
    path('pending',views.pending,name="pending"),
    path('refresh_data',views.refresh_data,name="refresh_data"),
    path('delete_application/<int:pk>',views.delete_application,name="delete_application"),
    path('schedule_interview1/<int:id>/', views.schedule_interview1, name='schedule_interview1'),
    path('agency_dashboard',views.agency_dashboard,name="agency_dashboard"),
    path('company_details',views.company_details,name="company_details"),
    path('Add_company',views.Add_company,name="Add_company"),
    path('delete_operator/<int:id>',views.delete_operator,name="delete_operator"),
    path('agency_job/<int:id>',views.agency_job,name="agency_job"),
    path('agency_job_details',views.agency_job_details,name="agency_job_details"),
    path('agency_job_applications',views.agency_job_applications,name="agency_job_applications"),
    path('agency_selected',views.agency_selected,name="agency_selected"),
    path('agency_schedule_interview/<int:id>/',views.agency_schedule_interview,name="agency_schedule_interview"),
    path('api/get-interviews/', views.get_interviews, name='get_interviews'),
    path('api/get-company-interviews/', views.get_company_interviews, name='get_company_interviews'),
    path('company_profile',views.company_profile,name="company_profile"),
    path('edit_company_profile',views.edit_company_profile,name="edit_company_profile"),
    path('edit_user_profile',views.edit_user_profile,name="edit_user_profile"),
    path('user_logout', views.user_logout, name='user_logout'),
    path('logout', views.company_logout, name='company_logout'),
    path('agency_logout', views.agency_logout, name='agency_logout'),
    path('search_trend/<str:keyword>/', views.search_trend, name='search_trend'),
]
