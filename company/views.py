from django.shortcuts import render,redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse,HttpResponseRedirect,HttpResponseForbidden,HttpResponseBadRequest
from django.template import loader
from .models import NewUser, JobDetails, UserDetails, AppliedJobs, CompanyDetails,ApplicationStatus, ScheduleInterview, Agency_Company,AgencyJobDetails,AgencyAppliedJobs,AgencyApplicationStatus
from .models import AgencyScheduleInterview, AgencyJobSaved, CompanyJobSaved
from rest_framework import generics
from rest_framework.views import APIView
from django.contrib.auth import authenticate,login,logout
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from datetime import date
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from rest_framework.authtoken.models import Token
from django.utils import timezone
from django.core.mail import send_mail
from django.db.models import F
from datetime import datetime, timedelta
from django.conf import settings
import smtplib
from django.views.decorators.csrf import csrf_exempt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.core.mail import send_mail
from django.db.models import Q
from django.core.serializers import serialize
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from random import shuffle
from itertools import chain
from random import sample
from django.core.serializers import deserialize
from django.db.models import Count
from collections import defaultdict
from urllib.parse import unquote
from operator import attrgetter

def demo(request):
    return render(request,'components.html')


def admin_db(request):
    i = request.user.id
    obj = NewUser.objects.get(id=i)
    today_date = date.today()
    
    data = NewUser.objects.filter(Q(user_type='Company') | Q(user_type='Agency'))
    context = {
        'obj':obj,
        'today_date':today_date,
        'data':data,
    }
    print(data)
    return render(request,'admin_db.html',context)

def update_status(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(NewUser, id=user_id)
        print("userrrrrrr",user)
        
        # Assuming 'status' is a BooleanField in your model
        user.status = True
        user.save()
        
        return JsonResponse({'message': 'Status updated successfully!'})
    return JsonResponse({}, status=400)

def index(request):
    recent_agency_jobs = AgencyJobDetails.objects.all().order_by('-created_on')[:5]
    recent_jobs = JobDetails.objects.all().order_by('-created_on')[:5]

    # Combine the querysets and shuffle the combined queryset
    combined_jobs = list(chain(recent_agency_jobs, recent_jobs))
    random.shuffle(combined_jobs)

    # Sort combined_jobs by the latest job posted (created_on) in descending order
    combined_jobs = sorted(combined_jobs, key=attrgetter('created_on'), reverse=True)

    for x in combined_jobs:
        if hasattr(x, 'company_id') and hasattr(x.company_id, 'first_name'):
            days_since_posted = (timezone.now().date() - x.created_on).days
            x.days_since_posted = days_since_posted
        elif hasattr(x, 'company_id') and hasattr(x.company_id, 'company_name'):
            days_since_posted = (timezone.now().date() - x.created_on).days
            x.days_since_posted = days_since_posted

    unique_departments_agency = AgencyJobDetails.objects.values_list('department', flat=True).distinct()
    unique_departments_job = JobDetails.objects.values_list('department', flat=True).distinct()
    all_unique_departments = list(set(chain(unique_departments_agency, unique_departments_job)))

    open_status_count_job = (
        JobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_status_count_agency = (
        AgencyJobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_jobs_count = defaultdict(int)
    for item in open_status_count_job:
        open_jobs_count[item['department']] += item['open_count']

    for item in open_status_count_agency:
        open_jobs_count[item['department']] += item['open_count']

    department_open_counts = [
        (department, open_jobs_count.get(department, 0)) for department in all_unique_departments
    ]

    hiring_partners = NewUser.objects.filter(Q(user_type='Company') | Q(user_type='Agency'))
    for x in hiring_partners:
        print(x)

    context = {
        'shuffled_jobs': combined_jobs,
        'all_unique_departments': all_unique_departments,
        'department_open_counts': department_open_counts,
        'hiring_partners':hiring_partners
    }

    return render(request, 'index.html', context)


from datetime import datetime, timedelta
from itertools import chain

def job_list(request, department):
    print(department)
    decoded_department = unquote(department)
    print("!!!!!!!!!!",decoded_department)
    job_details = JobDetails.objects.filter(department=decoded_department, status='open')
    print("##########",job_details)
    agency_job_details = AgencyJobDetails.objects.filter(department=decoded_department, status='open')
    print("##########",agency_job_details)
    all_jobs = list(chain(job_details, agency_job_details))
    for job in all_jobs:
        today = datetime.now().date()  # Define 'today' here for each iteration
        days_posted_ago = (today - job.created_on).days
        job.days_posted_ago = days_posted_ago

    # Sort the combined queryset based on days posted (latest at the top)
    all_jobs = sorted(all_jobs, key=lambda x: x.created_on, reverse=True)

    unique_departments_agency = AgencyJobDetails.objects.values_list('department', flat=True).distinct()
    unique_departments_job = JobDetails.objects.values_list('department', flat=True).distinct()
    all_unique_departments = list(set(chain(unique_departments_agency, unique_departments_job)))

    open_status_count_job = (
        JobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_status_count_agency = (
        AgencyJobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_jobs_count = defaultdict(int)
    for item in open_status_count_job:
        open_jobs_count[item['department']] += item['open_count']

    for item in open_status_count_agency:
        open_jobs_count[item['department']] += item['open_count']

    department_open_counts = [
        (department, open_jobs_count.get(department, 0)) for department in all_unique_departments
    ]

    work_modes = AgencyJobDetails.objects.values_list('work_mode', flat=True).distinct()

    job_details_count = JobDetails.objects.values('location').annotate(job_count=Count('location'))

# Count jobs in each unique location from AgencyJobDetails
    agency_job_details_count = AgencyJobDetails.objects.values('location').annotate(job_count=Count('location'))

# Combine the counts
    combined_counts = {}

    for job_detail in job_details_count:
        combined_counts[job_detail['location']] = combined_counts.get(job_detail['location'], 0) + job_detail['job_count']

    for agency_job_detail in agency_job_details_count:
        combined_counts[agency_job_detail['location']] = combined_counts.get(agency_job_detail['location'], 0) + agency_job_detail['job_count']

    context = {
        'all_jobs': all_jobs,
        'selected_department': decoded_department,
        'department_open_counts':department_open_counts,
        'work_modes':work_modes,
        'combined_counts':combined_counts
    }

    return render(request, 'job_list.html', context)

def location_related_jobs(request, location):
    decoded_department = unquote(location)
    print("!!!!!!!!!!",decoded_department)
    job_details = JobDetails.objects.filter(location=decoded_department, status='open')
    print("##########",job_details)
    agency_job_details = AgencyJobDetails.objects.filter(location=decoded_department, status='open')
    print("##########",agency_job_details)
    all_jobs = list(chain(job_details, agency_job_details))
    for job in all_jobs:
        today = datetime.now().date()  # Define 'today' here for each iteration
        days_posted_ago = (today - job.created_on).days
        job.days_posted_ago = days_posted_ago

    # Sort the combined queryset based on days posted (latest at the top)
    all_jobs = sorted(all_jobs, key=lambda x: x.created_on, reverse=True)

    unique_departments_agency = AgencyJobDetails.objects.values_list('department', flat=True).distinct()
    unique_departments_job = JobDetails.objects.values_list('department', flat=True).distinct()
    all_unique_departments = list(set(chain(unique_departments_agency, unique_departments_job)))

    open_status_count_job = (
        JobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_status_count_agency = (
        AgencyJobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_jobs_count = defaultdict(int)
    for item in open_status_count_job:
        open_jobs_count[item['department']] += item['open_count']

    for item in open_status_count_agency:
        open_jobs_count[item['department']] += item['open_count']

    department_open_counts = [
        (department, open_jobs_count.get(department, 0)) for department in all_unique_departments
    ]

    work_modes = AgencyJobDetails.objects.values_list('work_mode', flat=True).distinct()

    job_details_count = JobDetails.objects.values('location').annotate(job_count=Count('location'))

# Count jobs in each unique location from AgencyJobDetails
    agency_job_details_count = AgencyJobDetails.objects.values('location').annotate(job_count=Count('location'))

# Combine the counts
    combined_counts = {}

    for job_detail in job_details_count:
        combined_counts[job_detail['location']] = combined_counts.get(job_detail['location'], 0) + job_detail['job_count']

    for agency_job_detail in agency_job_details_count:
        combined_counts[agency_job_detail['location']] = combined_counts.get(agency_job_detail['location'], 0) + agency_job_detail['job_count']

    context = {
        'all_jobs': all_jobs,
        'selected_department': decoded_department,
        'department_open_counts':department_open_counts,
        'work_modes':work_modes,
        'combined_counts':combined_counts,
    }

    return render(request, 'location_related_jobs.html', context)

def user_location_related(request, location):
    decoded_department = unquote(location)
    print("!!!!!!!!!!",decoded_department)
    job_details = JobDetails.objects.filter(location=decoded_department, status='open')
    print("##########",job_details)
    agency_job_details = AgencyJobDetails.objects.filter(location=decoded_department, status='open')
    print("##########",agency_job_details)
    all_jobs = list(chain(job_details, agency_job_details))
    for job in all_jobs:
        today = datetime.now().date()  # Define 'today' here for each iteration
        days_posted_ago = (today - job.created_on).days
        job.days_posted_ago = days_posted_ago

    # Sort the combined queryset based on days posted (latest at the top)
    all_jobs = sorted(all_jobs, key=lambda x: x.created_on, reverse=True)

    unique_departments_agency = AgencyJobDetails.objects.values_list('department', flat=True).distinct()
    unique_departments_job = JobDetails.objects.values_list('department', flat=True).distinct()
    all_unique_departments = list(set(chain(unique_departments_agency, unique_departments_job)))

    open_status_count_job = (
        JobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_status_count_agency = (
        AgencyJobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_jobs_count = defaultdict(int)
    for item in open_status_count_job:
        open_jobs_count[item['department']] += item['open_count']

    for item in open_status_count_agency:
        open_jobs_count[item['department']] += item['open_count']

    department_open_counts = [
        (department, open_jobs_count.get(department, 0)) for department in all_unique_departments
    ]

    work_modes = AgencyJobDetails.objects.values_list('work_mode', flat=True).distinct()

    job_details_count = JobDetails.objects.values('location').annotate(job_count=Count('location'))

# Count jobs in each unique location from AgencyJobDetails
    agency_job_details_count = AgencyJobDetails.objects.values('location').annotate(job_count=Count('location'))

# Combine the counts
    combined_counts = {}

    for job_detail in job_details_count:
        combined_counts[job_detail['location']] = combined_counts.get(job_detail['location'], 0) + job_detail['job_count']

    for agency_job_detail in agency_job_details_count:
        combined_counts[agency_job_detail['location']] = combined_counts.get(agency_job_detail['location'], 0) + agency_job_detail['job_count']

    context = {
        'all_jobs': all_jobs,
        'selected_department': decoded_department,
        'department_open_counts':department_open_counts,
        'work_modes':work_modes,
        'combined_counts':combined_counts,
    }

    return render(request, 'user_location_related.html', context)


def user_job_list(request, department):
    decoded_department = unquote(department)
    print("!!!!!!!!!!",decoded_department)
    job_details = JobDetails.objects.filter(department=decoded_department, status='open')
    print("##########",job_details)
    agency_job_details = AgencyJobDetails.objects.filter(department=decoded_department, status='open')
    print("##########",agency_job_details)
    all_jobs = list(chain(job_details, agency_job_details))

    saved_agency_jobs_ids = AgencyJobSaved.objects.filter(user_id=request.user.id).values_list('job_id_id', flat=True)
    saved_company_jobs_ids = CompanyJobSaved.objects.filter(user_id=request.user.id).values_list('job_id_id', flat=True)
    saved_job_ids = list(saved_agency_jobs_ids) + list(saved_company_jobs_ids)
    print("^^^^^^^^^^^^^^^",saved_job_ids)

    for job in all_jobs:
        today = datetime.now().date()  # Define 'today' here for each iteration
        days_posted_ago = (today - job.created_on).days
        job.days_posted_ago = days_posted_ago
        job.is_saved = job.id in saved_job_ids

    # Sort the combined queryset based on days posted (latest at the top)
    all_jobs = sorted(all_jobs, key=lambda x: x.created_on, reverse=True)
    # Fetch saved job IDs for the current user from both models

    unique_departments_agency = AgencyJobDetails.objects.values_list('department', flat=True).distinct()
    unique_departments_job = JobDetails.objects.values_list('department', flat=True).distinct()
    all_unique_departments = list(set(chain(unique_departments_agency, unique_departments_job)))

    open_status_count_job = (
        JobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_status_count_agency = (
        AgencyJobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_jobs_count = defaultdict(int)
    for item in open_status_count_job:
        open_jobs_count[item['department']] += item['open_count']

    for item in open_status_count_agency:
        open_jobs_count[item['department']] += item['open_count']

    department_open_counts = [
        (department, open_jobs_count.get(department, 0)) for department in all_unique_departments
    ]

    work_modes = AgencyJobDetails.objects.values_list('work_mode', flat=True).distinct()

    job_details_count = JobDetails.objects.values('location').annotate(job_count=Count('location'))

# Count jobs in each unique location from AgencyJobDetails
    agency_job_details_count = AgencyJobDetails.objects.values('location').annotate(job_count=Count('location'))

# Combine the counts
    combined_counts = {}

    for job_detail in job_details_count:
        combined_counts[job_detail['location']] = combined_counts.get(job_detail['location'], 0) + job_detail['job_count']

    for agency_job_detail in agency_job_details_count:
        combined_counts[agency_job_detail['location']] = combined_counts.get(agency_job_detail['location'], 0) + agency_job_detail['job_count']

    

    context = {
        'all_jobs': all_jobs,
        'selected_department': decoded_department,
        'department_open_counts':department_open_counts,
        'work_modes':work_modes,
        'combined_counts':combined_counts
    }

    return render(request, 'user_job_list.html', context)

def search_results(request):
    keyword = request.GET.get('keyword')
    job_title = request.GET.get('job_title')
    location = request.GET.get('location')
    job_type = request.GET.get('type')

    combined_results = []

    if keyword:
        agency_job_results = AgencyJobDetails.objects.filter(
            Q(designation__icontains=keyword) |
            Q(job_description__icontains=keyword) |
            Q(department__icontains=keyword) |
            Q(location__icontains=keyword) |
            Q(mandatory_skills__icontains=keyword) |
            Q(optional_skills__icontains=keyword) |
            Q(experience__icontains=keyword) |
            Q(salary__icontains=keyword) |
            Q(qualification__icontains=keyword)
        )

        job_results = JobDetails.objects.filter(
            Q(designation__icontains=keyword) |
            Q(job_description__icontains=keyword) |
            Q(department__icontains=keyword) |
            Q(location__icontains=keyword) |
            Q(mandatory_skills__icontains=keyword) |
            Q(optional_skills__icontains=keyword) |
            Q(experience__icontains=keyword) |
            Q(salary__icontains=keyword) |
            Q(qualification__icontains=keyword)
        )

        # Combine both querysets into a single result set
        combined_results = list(chain(agency_job_results, job_results))

    elif job_title:
        # Search by job title in the designation column
        combined_results = list(chain(
            AgencyJobDetails.objects.filter(designation__icontains=job_title),
            JobDetails.objects.filter(designation__icontains=job_title)
        ))

    elif location:
        # Search by location in the location column
        combined_results = list(chain(
            AgencyJobDetails.objects.filter(location__icontains=location),
            JobDetails.objects.filter(location__icontains=location)
        ))

    elif job_type:
        # Search by job type in the type column
        agency_job_results = AgencyJobDetails.objects.filter(job_type=job_type)
        job_results = JobDetails.objects.filter(job_type=job_type)
        combined_results = list(chain(agency_job_results, job_results))

    for job in combined_results:
        # Assuming 'posted_on' is the field in your models storing the posting date
        days_since_posted = (datetime.now().date() - job.created_on).days
        job.days_since_posted = days_since_posted


    unique_departments_agency = AgencyJobDetails.objects.values_list('department', flat=True).distinct()
    unique_departments_job = JobDetails.objects.values_list('department', flat=True).distinct()
    all_unique_departments = list(set(chain(unique_departments_agency, unique_departments_job)))

    open_status_count_job = (
        JobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_status_count_agency = (
        AgencyJobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_jobs_count = defaultdict(int)
    for item in open_status_count_job:
        open_jobs_count[item['department']] += item['open_count']

    for item in open_status_count_agency:
        open_jobs_count[item['department']] += item['open_count']

    department_open_counts = [
        (department, open_jobs_count.get(department, 0)) for department in all_unique_departments
    ]
    job_details_count = JobDetails.objects.values('location').annotate(job_count=Count('location'))

# Count jobs in each unique location from AgencyJobDetails
    agency_job_details_count = AgencyJobDetails.objects.values('location').annotate(job_count=Count('location'))

# Combine the counts
    combined_counts = {}

    for job_detail in job_details_count:
        combined_counts[job_detail['location']] = combined_counts.get(job_detail['location'], 0) + job_detail['job_count']

    for agency_job_detail in agency_job_details_count:
        combined_counts[agency_job_detail['location']] = combined_counts.get(agency_job_detail['location'], 0) + agency_job_detail['job_count']

# Print or use the job counts in each unique location as needed
    print(combined_counts)
    context = {
        'combined_results': combined_results,
        'keyword': keyword,
        'job_title': job_title,
        'location': location,
        'job_type': job_type,
        'department_open_counts':department_open_counts,
        'combined_counts':combined_counts,
    }

    return render(request, 'search_results.html', context)

def autocomplete_job_title_suggestions(request):
    keyword = request.GET.get('keyword')
    suggestions = set()  # Using a set to maintain unique values

    if keyword:
        agency_job_results = AgencyJobDetails.objects.filter(
            designation__icontains=keyword
        ).values_list('designation', flat=True)[:10]  # Limit suggestions to 10

        job_results = JobDetails.objects.filter(
            designation__icontains=keyword
        ).values_list('designation', flat=True)[:10]  # Limit suggestions to 10

        suggestions.update(agency_job_results)
        suggestions.update(job_results)

    return JsonResponse({'suggestions': list(suggestions)})


def autocomplete_location_suggestions(request):
    keyword = request.GET.get('keyword')
    print(keyword)
    suggestions = set()  # Using a set to maintain unique values

    if keyword:
        agency_location_results = AgencyJobDetails.objects.filter(
            designation__icontains=keyword
        ).values_list('location', flat=True)[:10]  # Limit suggestions to 10

        location_results = JobDetails.objects.filter(
            designation__icontains=keyword
        ).values_list('location', flat=True)[:10]  # Limit suggestions to 10

        suggestions.update(agency_location_results)
        suggestions.update(location_results)
    

    return JsonResponse({'suggestions': list(suggestions)})


def user_search_results(request):
    keyword = request.GET.get('keyword')
    job_title = request.GET.get('job_title')
    location = request.GET.get('location')
    job_type = request.GET.get('type')

    combined_results = []

    if keyword:
        agency_job_results = AgencyJobDetails.objects.filter(
            Q(designation__icontains=keyword) |
            Q(job_description__icontains=keyword) |
            Q(department__icontains=keyword) |
            Q(location__icontains=keyword) |
            Q(mandatory_skills__icontains=keyword) |
            Q(optional_skills__icontains=keyword) |
            Q(experience__icontains=keyword) |
            Q(salary__icontains=keyword) |
            Q(qualification__icontains=keyword)
        )

        job_results = JobDetails.objects.filter(
            Q(designation__icontains=keyword) |
            Q(job_description__icontains=keyword) |
            Q(department__icontains=keyword) |
            Q(location__icontains=keyword) |
            Q(mandatory_skills__icontains=keyword) |
            Q(optional_skills__icontains=keyword) |
            Q(experience__icontains=keyword) |
            Q(salary__icontains=keyword) |
            Q(qualification__icontains=keyword)
        )

        # Combine both querysets into a single result set
        combined_results = list(chain(agency_job_results, job_results))
        combined_data.sort(key=lambda x: x.created_on, reverse=True)


    elif job_title:
        # Search by job title in the designation column
        combined_results = list(chain(
            AgencyJobDetails.objects.filter(designation__icontains=job_title),
            JobDetails.objects.filter(designation__icontains=job_title)
        ))

    elif location:
        # Search by location in the location column
        combined_results = list(chain(
            AgencyJobDetails.objects.filter(location__icontains=location),
            JobDetails.objects.filter(location__icontains=location)
        ))

    elif job_type:
        # Search by job type in the type column
        agency_job_results = AgencyJobDetails.objects.filter(job_type=job_type)
        job_results = JobDetails.objects.filter(job_type=job_type)
        combined_results = list(chain(agency_job_results, job_results))

    # Fetch saved job IDs for the current user from both models
    saved_agency_jobs_ids = AgencyJobSaved.objects.filter(user_id=request.user.id).values_list('job_id_id', flat=True)
    saved_company_jobs_ids = CompanyJobSaved.objects.filter(user_id=request.user.id).values_list('job_id_id', flat=True)
    saved_job_ids = list(saved_agency_jobs_ids) + list(saved_company_jobs_ids)
    print("^^^^^^^^^^^^^^^",saved_job_ids)

    for job in combined_results:
        # Assuming 'posted_on' is the field in your models storing the posting date
        days_since_posted = (datetime.now().date() - job.created_on).days
        job.days_since_posted = days_since_posted
        job.is_saved = job.id in saved_job_ids


    unique_departments_agency = AgencyJobDetails.objects.values_list('department', flat=True).distinct()
    unique_departments_job = JobDetails.objects.values_list('department', flat=True).distinct()
    all_unique_departments = list(set(chain(unique_departments_agency, unique_departments_job)))

    open_status_count_job = (
        JobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_status_count_agency = (
        AgencyJobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_jobs_count = defaultdict(int)
    for item in open_status_count_job:
        open_jobs_count[item['department']] += item['open_count']

    for item in open_status_count_agency:
        open_jobs_count[item['department']] += item['open_count']

    department_open_counts = [
        (department, open_jobs_count.get(department, 0)) for department in all_unique_departments
    ]

    job_details_count = JobDetails.objects.values('location').annotate(job_count=Count('location'))

# Count jobs in each unique location from AgencyJobDetails
    agency_job_details_count = AgencyJobDetails.objects.values('location').annotate(job_count=Count('location'))

# Combine the counts
    combined_counts = {}

    for job_detail in job_details_count:
        combined_counts[job_detail['location']] = combined_counts.get(job_detail['location'], 0) + job_detail['job_count']

    for agency_job_detail in agency_job_details_count:
        combined_counts[agency_job_detail['location']] = combined_counts.get(agency_job_detail['location'], 0) + agency_job_detail['job_count']

    context = {
        'combined_results': combined_results,
        'keyword': keyword,
        'job_title': job_title,
        'location': location,
        'job_type': job_type,
        'department_open_counts':department_open_counts,
        'combined_counts':combined_counts
    }

    return render(request, 'user_search_results.html', context)



def work_mode(request, selected_work_mode):
    print("!!!!!!!",selected_work_mode)
    selected_work_mode = selected_work_mode.replace('_', ' ')

    # Fetch jobs from AgencyJobDetails for the selected work_mode
    agency_jobs = AgencyJobDetails.objects.filter(work_mode=selected_work_mode)
    print("agency_job",agency_jobs)
    # Fetch jobs from JobDetails for the selected work_mode
    jobs = JobDetails.objects.filter(work_mode=selected_work_mode)
    print("company_job",jobs)
    # Combine both sets of jobs
    combined_jobs = list(agency_jobs) + list(jobs)
    combined_jobs.sort(key=lambda x: x.created_on, reverse=True)
    print("**********",combined_jobs)

    unique_departments_agency = AgencyJobDetails.objects.values_list('department', flat=True).distinct()
    unique_departments_job = JobDetails.objects.values_list('department', flat=True).distinct()
    all_unique_departments = list(set(chain(unique_departments_agency, unique_departments_job)))

    open_status_count_job = (
        JobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_status_count_agency = (
        AgencyJobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_jobs_count = defaultdict(int)
    for item in open_status_count_job:
        open_jobs_count[item['department']] += item['open_count']

    for item in open_status_count_agency:
        open_jobs_count[item['department']] += item['open_count']

    department_open_counts = [
        (department, open_jobs_count.get(department, 0)) for department in all_unique_departments
    ]
    for job in combined_jobs:
        today = datetime.now().date()  # Define 'today' here for each iteration
        days_posted_ago = (today - job.created_on).days
        job.days_posted_ago = days_posted_ago
    job_details_count = JobDetails.objects.values('location').annotate(job_count=Count('location'))

# Count jobs in each unique location from AgencyJobDetails
    agency_job_details_count = AgencyJobDetails.objects.values('location').annotate(job_count=Count('location'))

# Combine the counts
    combined_counts = {}

    for job_detail in job_details_count:
        combined_counts[job_detail['location']] = combined_counts.get(job_detail['location'], 0) + job_detail['job_count']

    for agency_job_detail in agency_job_details_count:
        combined_counts[agency_job_detail['location']] = combined_counts.get(agency_job_detail['location'], 0) + agency_job_detail['job_count']


    context = {
        'selected_work_mode': selected_work_mode,
        'jobs': combined_jobs,
        'department_open_counts':department_open_counts,
        'selected_work_mode':selected_work_mode,
        'combined_counts':combined_counts
    }

    return render(request, 'work_mode.html', context)


def user_work_mode(request, selected_work_mode):
    print("!!!!!!!",selected_work_mode)
    selected_work_mode = selected_work_mode.replace('_', ' ')

    # Fetch jobs from AgencyJobDetails for the selected work_mode
    agency_jobs = AgencyJobDetails.objects.filter(work_mode=selected_work_mode)
    print("agency_job",agency_jobs)
    # Fetch jobs from JobDetails for the selected work_mode
    jobs = JobDetails.objects.filter(work_mode=selected_work_mode)
    print("company_job",jobs)
    # Combine both sets of jobs
    combined_jobs = list(agency_jobs) + list(jobs)
    combined_jobs.sort(key=lambda x: x.created_on, reverse=True)
    print("**********",combined_jobs)

    saved_agency_jobs_ids = AgencyJobSaved.objects.filter(user_id=request.user.id).values_list('job_id_id', flat=True)
    saved_company_jobs_ids = CompanyJobSaved.objects.filter(user_id=request.user.id).values_list('job_id_id', flat=True)
    saved_job_ids = list(saved_agency_jobs_ids) + list(saved_company_jobs_ids)
    print("^^^^^^^^^^^^^^^",saved_job_ids)


    unique_departments_agency = AgencyJobDetails.objects.values_list('department', flat=True).distinct()
    unique_departments_job = JobDetails.objects.values_list('department', flat=True).distinct()
    all_unique_departments = list(set(chain(unique_departments_agency, unique_departments_job)))

    open_status_count_job = (
        JobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_status_count_agency = (
        AgencyJobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_jobs_count = defaultdict(int)
    for item in open_status_count_job:
        open_jobs_count[item['department']] += item['open_count']

    for item in open_status_count_agency:
        open_jobs_count[item['department']] += item['open_count']

    department_open_counts = [
        (department, open_jobs_count.get(department, 0)) for department in all_unique_departments
    ]
    for job in combined_jobs:
        today = datetime.now().date()  # Define 'today' here for each iteration
        days_posted_ago = (today - job.created_on).days
        job.days_posted_ago = days_posted_ago
        job.is_saved = job.id in saved_job_ids

    job_details_count = JobDetails.objects.values('location').annotate(job_count=Count('location'))

# Count jobs in each unique location from AgencyJobDetails
    agency_job_details_count = AgencyJobDetails.objects.values('location').annotate(job_count=Count('location'))

# Combine the counts
    combined_counts = {}

    for job_detail in job_details_count:
        combined_counts[job_detail['location']] = combined_counts.get(job_detail['location'], 0) + job_detail['job_count']

    for agency_job_detail in agency_job_details_count:
        combined_counts[agency_job_detail['location']] = combined_counts.get(agency_job_detail['location'], 0) + agency_job_detail['job_count']


    context = {
        'selected_work_mode': selected_work_mode,
        'jobs': combined_jobs,
        'department_open_counts':department_open_counts,
        'selected_work_mode':selected_work_mode,
        'combined_counts':combined_counts,
    }

    return render(request, 'user_work_mode.html', context)





def user_single_job(request,job_id,u_id):
    job = AgencyJobDetails.objects.select_related('company_id').filter(id=job_id, status="open").first()
    details = NewUser.objects.filter(user_type="Agency",id=u_id)
    print("@@@@@@@@@@@@@@@@@@@@",details)
    if details:
        print("HIiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii")
    else:
        job = JobDetails.objects.select_related('company_id').filter(id=job_id, status="open").first()
        print("**********************",job.designation)
    context = {
        'job_id':job_id,
        'job': job,
        'u_id':u_id

    }
    return render(request, 'user_single_job.html',context)

def companies(request):
    hiring_partners = NewUser.objects.filter(Q(user_type='Company') | Q(user_type='Agency'))
    context = {
    'hiring_partners':hiring_partners
    }
    return render(request,'companies.html',context)

def all_companies(request):
    hiring_partners = NewUser.objects.filter(Q(user_type='Company') | Q(user_type='Agency'))
    context = {
    'hiring_partners':hiring_partners
    }
    return render(request,'all_companies.html',context)

# Company or Agency registration
def registration(request):
    if request.method == 'POST':
        company_name = request.POST.get('company_name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        password1 = request.POST.get('password1')
        email = request.POST.get('email')
        email_password = request.POST.get('email_password')
        contact_no = request.POST.get('contact_no')
        user_type = request.POST.get('user_type')
        country = request.POST.get('country')
        state = request.POST.get('state')
        address = request.POST.get('address')
        city = request.POST.get('city')
        company_logo = request.FILES.get('company_logo')
        print("!!!!!!!!!",company_logo)
        about = request.POST.get('about')
        passw = make_password(password)
        user = NewUser.objects.create(first_name=company_name,username=username,password=passw,
        email=email,phone_no=contact_no,user_type=user_type, country=country,state=state,address=address,city=city,
        profile=company_logo,about=about)
        return redirect('login1')
    return render(request,'registration.html')

# login
def login1(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        print(username)
        password = request.POST.get('password')
        print(password)
        user = authenticate(request, username=username, password=password)
        print("!!!!!!!!!!!!!!!!",user)
        if user is not None and user.user_type == 'Company' and user.status == True:
            login(request, user)
            i = request.user.id
            print("companyyy idddd",i)
            return redirect('company_dashboard')
        elif user is not None and user.user_type == 'Agency' and user.status == True:
            login(request, user)
            i = request.user.id
            print("agencyyyy idddd",i)
            return redirect('agency_dashboard')
        else:
            messages.error(request,"Sorry unable to login please try after sometime")
            print("credentials are wrong")
           

    return render(request, 'login1.html')

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            print(request.user)
            
            return redirect('/admin_db')
        else:
            messages.error(request,'Wrong Credentials')
            return redirect('/admin_login')
    return render(request,'admin_login.html')



def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        print(username)
        password = request.POST.get('password')
        print(password)
        user = authenticate(request, username=username, password=password)
        print("!!!!!!!!!!!!!!!!",user)
        if user is not None and user.user_type == 'job seeker':
            login(request, user)
            i = request.user.id
            print("agencyyyy idddd",i)
            obj = UserDetails.objects.filter(user_id_id=i).first()
            print("!!!!!!!!!",obj)
            if obj is None:
                return redirect('user_details')
            else:

                return redirect('user_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'user_login.html')
    return render(request, 'user_login.html', {'messages': messages.get_messages(request)})


# company Dashboard
def company_dashboard(request):
    i = request.user.id
    obj = NewUser.objects.get(id=i)
    today_date = date.today()

    user_id = ScheduleInterview.objects.select_related('application_id','companyIdOrAgencyId').filter(companyIdOrAgencyId_id = i)
    print(user_id)
    for x in user_id:
        u = x.application_id.job_id
        print("****************************",u)

    user_id_data = serialize('json', user_id)
    obj = NewUser.objects.get(id=i)
    data=ScheduleInterview.objects.filter(companyIdOrAgencyId_id=i)

    context = {'today_date':today_date,'data':data,'obj':obj,'user_id':user_id,'user_id_data': user_id_data,}
    return render(request,'company_dashboard.html',context)

@require_GET
def get_company_interviews(request):
    id = request.user.id
    clicked_date = request.GET.get('date')
    print("**************8",clicked_date) # Retrieve the clicked date from the request
    user_id = ScheduleInterview.objects.filter(interview_date=clicked_date,companyIdOrAgencyId_id=id)
    print("!!!!!!!!!!!!!",user_id)
    interview_data = list(user_id.values('interview_date', 'companyIdOrAgencyId_id__first_name', 'application_id__job_id__designation', 'application_id__user_id__email', 'start_time', 'end_time', 'mode_of_interview'))
    print("++++++++++++",interview_data)
    return JsonResponse(interview_data, safe=False)


def company_profile(request):
    i = request.user.id
    obj = NewUser.objects.get(id=i)
    today_date = date.today()
    jobs = JobDetails.objects.filter(company_id_id = i).count()
    print("!!!!!",jobs)
    context = {'obj':obj,'today_date':today_date,'jobs':jobs}
    return render(request,'company_profile.html',context)

def edit_company_profile(request):
    i = request.user.id
    obj = NewUser.objects.get(id=i)
    today_date = date.today()
    context = {'obj':obj,'today_date':today_date}
    return render(request,'edit_company_profile.html',context)

# JobDetails
def job_vacancy(request):
    success_message = request.GET.get('success_message')
    i = request.user.id
    obj = NewUser.objects.get(id=i)
    today_date = date.today()


    search_query = request.GET.get('search_query', '')

    data = JobDetails.objects.filter(company_id_id=i)

    if search_query:
        # Perform case-insensitive search for string fields
        data = data.filter(
            Q(designation__icontains=search_query) |
            Q(department__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(mandatory_skills__icontains=search_query) |
            Q(optional_skills__icontains=search_query) |
            Q(qualification__icontains=search_query) |
            Q(no_of_vacancy__icontains=search_query)
        )

        # Handle case-insensitive search for numeric fields by converting them to strings
        data = data.filter(
            Q(experience__icontains=str(search_query)) |
            Q(salary__icontains=str(search_query))
        )

    context = {'obj':obj,'today_date':today_date,'data':data,'success_message':success_message}

    return render(request,'job_vacancy.html',context)


def refresh_data(request):
    i = request.user.id
    obj = NewUser.objects.get(id=i)
    today_date = date.today()

    # Fetch all data without any filters
    all_data = JobDetails.objects.filter(company_id_id=i)

    context = {'obj': obj, 'today_date': today_date, 'data': all_data}

    return render(request, 'job_vacancy.html', context)

# add Job vacancy
def add_job(request):
    i = request.user.id
    obj = NewUser.objects.get(id=i)
    today_date = date.today()
    context = {'obj':obj,'today_date':today_date}
    if request.method == 'POST':
        designation = request.POST.get('designation')
        department = request.POST.get('department')
        location = request.POST.get('location')
        work_mode = request.POST.get('work_mode')
        no_of_vacancy = request.POST.get('no_of_vacancy')
        mandatory_skills = request.POST.get('mandatory_skills')
        optional_skills = request.POST.get('optional_skills')
        experience = request.POST.get('experience')
        qualification = request.POST.get('qualification')
        salary = request.POST.get('salary')
        status = request.POST.get('status')
        description = request.POST.get('description')
        state = request.POST.get('state')
        country = request.POST.get('country')
        obj = JobDetails.objects.create(company_id_id=i,designation=designation,department=department,location=location,work_mode=work_mode,
        no_of_vacancy=no_of_vacancy,mandatory_skills=mandatory_skills,optional_skills=optional_skills,
        qualification=qualification,experience=experience,
        salary=salary,job_description=description)

        print(obj)
        return redirect(reverse('job_vacancy') + '?success_message=1')

    return render(request,'add_job.html',context)

def add_company_details(request):
    i = request.user.id
    obj = NewUser.objects.get(id=i)
    today_date = date.today()
    context = {'obj':obj,'today_date':today_date}
    if request.method == 'POST':
        tag_line = request.POST.get('tag_line')
        company_type = request.POST.get('company_type')
        service_sector = request.POST.get('service_sector')
        founded_year = request.POST.get('founded_year')
        head_branch = request.POST.get('head_branch')
        linkedin = request.POST.get('linkedin')
        instagram = request.POST.get('instagram')
        facebook = request.POST.get('facebook')
        website = request.POST.get('website')
        highlights = request.POST.get('highlights')
        why_us = request.POST.get('why_us')
        milestone = request.POST.get('milestone')
        img1 = request.FILES.get('img1')
        img2 = request.FILES.get('img2')
        cover_image = request.FILES.get('cover_image')

        obj = CompanyDetails.objects.create(companyOrAgency_id_id=i,tag_line=tag_line,company_type=company_type,company_service_sector=service_sector,founded_year=founded_year,
        head_branch=head_branch,linkedin_url=linkedin,instagram_url=instagram,
        facebook=facebook,webiste=website,
        Key_highlights=highlights,why_us=why_us,
        milestone=milestone,
        other_image1=img1,
        other_image2=img2,cover_image=cover_image)

        print(obj)

    return render(request,'add_company_details.html',context)


def delete_jobs(request, pk):
    application = get_object_or_404(JobDetails, pk=pk)
    if request.method == 'POST':
        application.delete()
        return redirect('job_vacancy')


def user_registration(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        password1 = request.POST.get('password1')
        email = request.POST.get('email')
        phone_no = request.POST.get('phone_no')
        address = request.POST.get('address')
        city = request.POST.get('city')
        profile = request.FILES.get('profile')
        if password != password1:
            context = {
                'registration_error': 'Passwords do not match',
                # Include other context data needed for rendering the form again
            }
            return render(request, 'user_registration.html', context)

        passw = make_password(password)
        user = NewUser.objects.create(first_name=first_name,last_name=last_name,username=username,password=passw,
        email=email,phone_no=phone_no,address=address,city=city,profile=profile)

        context = {'registration_successful': True}
        return render(request, 'user_registration.html', context)
    return render(request,'user_registration.html')


def user_details(request):
    id = request.user.id
    if request.method == 'POST':

        qualification = request.POST.get('qualification')
        experience = request.POST.get('experience')
        dob = request.POST.get('dob')
        skills = request.POST.get('skills')
        obj = UserDetails.objects.create(user_id_id=id,qualification=qualification,experience=experience,DOB=dob,
        skills=skills)
        return redirect('user_dashboard')
    return render(request,'user_details.html')


def user_dashboard1(request):
    id = request.user.id
    obj = NewUser.objects.get(id=id)
    today_date = date.today()
    print("profileeee",obj.profile)
    # Get user details
    user_details = UserDetails.objects.get(user_id_id=id)

    # Extract user skills
    user_skills = set(user_details.skills.lower().split(','))  # Assuming skills are comma-separated

    # Get all job details from JobDetails model
    all_jobs = JobDetails.objects.all().select_related('company_id').filter(status="open")

    recommended_jobs_job_details = []

    # Compare user skills with job required skills in JobDetails model
    for job in all_jobs:
        job_required_skills = set(job.mandatory_skills.lower().split(','))
        common_skills = user_skills.intersection(job_required_skills)
        if common_skills:
            recommended_jobs_job_details.append(job)

    # Get all job details from AgencyJobDetails model
    all_agency_jobs = AgencyJobDetails.objects.all().select_related('company_id').filter(status="open")

    recommended_jobs_agency_details = []

    # Compare user skills with job required skills in AgencyJobDetails model
    for agency_job in all_agency_jobs:
        agency_job_required_skills = set(agency_job.mandatory_skills.lower().split(','))
        common_skills = user_skills.intersection(agency_job_required_skills)
        if common_skills:
            recommended_jobs_agency_details.append(agency_job)

    # Combine recommendations from both models into a single list
    combined_recommended_jobs = list(chain(recommended_jobs_job_details, recommended_jobs_agency_details))
    combined_recommended_jobs.sort(key=lambda x: x.created_on, reverse=True)
    r_jobs = len(combined_recommended_jobs)
    print("**********",r_jobs)

    # Fetch saved job IDs for the current user from both models
    saved_agency_jobs_ids = AgencyJobSaved.objects.filter(user_id=request.user.id).values_list('job_id_id', flat=True)
    saved_company_jobs_ids = CompanyJobSaved.objects.filter(user_id=request.user.id).values_list('job_id_id', flat=True)
    saved_job_ids = list(saved_agency_jobs_ids) + list(saved_company_jobs_ids)

    for x in combined_recommended_jobs:
        print(x)
        days_since_posted = (timezone.now().date() - x.created_on).days
        x.days_since_posted = days_since_posted
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",x.days_since_posted)
        x.is_saved = x.id in saved_job_ids



    # Merge the saved job IDs from both models


    unique_departments_agency = AgencyJobDetails.objects.values_list('department', flat=True).distinct()
    unique_departments_job = JobDetails.objects.values_list('department', flat=True).distinct()
    all_unique_departments = list(set(chain(unique_departments_agency, unique_departments_job)))

    open_status_count_job = (
        JobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_status_count_agency = (
        AgencyJobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_jobs_count = defaultdict(int)
    for item in open_status_count_job:
        open_jobs_count[item['department']] += item['open_count']

    for item in open_status_count_agency:
        open_jobs_count[item['department']] += item['open_count']

    department_open_counts = [
        (department, open_jobs_count.get(department, 0)) for department in all_unique_departments
    ]

    job_details_count = JobDetails.objects.values('location').annotate(job_count=Count('location'))

# Count jobs in each unique location from AgencyJobDetails
    agency_job_details_count = AgencyJobDetails.objects.values('location').annotate(job_count=Count('location'))

# Combine the counts
    combined_counts = {}

    for job_detail in job_details_count:
        combined_counts[job_detail['location']] = combined_counts.get(job_detail['location'], 0) + job_detail['job_count']

    for agency_job_detail in agency_job_details_count:
        combined_counts[agency_job_detail['location']] = combined_counts.get(agency_job_detail['location'], 0) + agency_job_detail['job_count']

    context = {'obj':obj,'today_date':today_date,'combined_recommended_jobs':combined_recommended_jobs
    ,'department_open_counts':department_open_counts,
    'combined_counts':combined_counts
    }
    return render(request,'user_dashboard1.html',context)


def application_status(request):
    id = request.user.id
    obj = NewUser.objects.get(id=id)
    today_date = date.today()
    applied_jobs = AppliedJobs.objects.select_related('job_id').filter(user_id_id=id)
    agency_applied_job = AgencyAppliedJobs.objects.select_related('job_id').filter(user_id_id=id)
    combined_jobs = list(applied_jobs) + list(agency_applied_job)
    combined_jobs.sort(key=lambda x: x.applied_date, reverse=True)
    for x in combined_jobs:
        print(x)
    context = {'obj':obj,'today_date':today_date,'combined_jobs':combined_jobs}
    return render(request,'application_status.html',context)

from itertools import chain
import random

def jobs(request):
    id = request.user.id
    obj = NewUser.objects.get(id=id)
    today_date = date.today()

    data = JobDetails.objects.all().select_related('company_id').filter(status="open")
    print(data)
    data1 = AgencyJobDetails.objects.all().select_related('company_id').filter(status="open")
    print(data1)
    combined_data = list(chain(data, data1))
    print("^^^^^^^^^^^^^^^^^^^^^^^^^^",combined_data)
# Shuffle the combined list
    random.shuffle(combined_data)

    # Sort the combined list based on 'created_on' attribute to display recent jobs first
    combined_data.sort(key=lambda x: x.created_on, reverse=True)


# Display the jumbled results
    for item in combined_data:
        print(item)

    # Fetch saved job IDs for the current user from both models
    saved_agency_jobs_ids = AgencyJobSaved.objects.filter(user_id=request.user.id).values_list('job_id_id', flat=True)
    saved_company_jobs_ids = CompanyJobSaved.objects.filter(user_id=request.user.id).values_list('job_id_id', flat=True)
    saved_job_ids = list(saved_agency_jobs_ids) + list(saved_company_jobs_ids)
    print("^^^^^^^^^^^^^^^",saved_job_ids)

    for x in combined_data:
        if hasattr(x, 'company_id') and hasattr(x.company_id, 'first_name'):

            days_since_posted = (timezone.now().date() - x.created_on).days
            x.days_since_posted = days_since_posted
            x.is_saved = x.id in saved_job_ids
        elif hasattr(x, 'company_id') and hasattr(x.company_id, 'company_name'):

            days_since_posted = (timezone.now().date() - x.created_on).days
            x.days_since_posted = days_since_posted
            x.is_saved = x.id in saved_job_ids
    else:
        # Handle cases where the attribute doesn't exist for the object
        print("Attribute doesn't exist for this object")


        days_since_posted = (timezone.now().date() - x.created_on).days
        x.days_since_posted = days_since_posted
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",x.days_since_posted)
        x.is_saved = x.id in saved_job_ids





    unique_departments_agency = AgencyJobDetails.objects.values_list('department', flat=True).distinct()
    unique_departments_job = JobDetails.objects.values_list('department', flat=True).distinct()
    all_unique_departments = list(set(chain(unique_departments_agency, unique_departments_job)))

    open_status_count_job = (
        JobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_status_count_agency = (
        AgencyJobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_jobs_count = defaultdict(int)
    for item in open_status_count_job:
        open_jobs_count[item['department']] += item['open_count']

    for item in open_status_count_agency:
        open_jobs_count[item['department']] += item['open_count']

    department_open_counts = [
        (department, open_jobs_count.get(department, 0)) for department in all_unique_departments
    ]
    job_details_count = JobDetails.objects.values('location').annotate(job_count=Count('location'))

# Count jobs in each unique location from AgencyJobDetails
    agency_job_details_count = AgencyJobDetails.objects.values('location').annotate(job_count=Count('location'))

# Combine the counts
    combined_counts = {}

    for job_detail in job_details_count:
        combined_counts[job_detail['location']] = combined_counts.get(job_detail['location'], 0) + job_detail['job_count']

    for agency_job_detail in agency_job_details_count:
        combined_counts[agency_job_detail['location']] = combined_counts.get(agency_job_detail['location'], 0) + agency_job_detail['job_count']

    context = {'obj':obj,'today_date':today_date,'data':data,'combined_data':combined_data,
    'department_open_counts':department_open_counts,
    'combined_counts':combined_counts}
    return render(request,'jobs.html',context)


def all_jobs(request):

    data = JobDetails.objects.all().select_related('company_id').filter(status="open")
    print(data)
    data1 = AgencyJobDetails.objects.all().select_related('company_id').filter(status="open")
    print(data1)
    combined_data = list(chain(data, data1))
    print("^^^^^^^^^^^^^^^^^^^^^^^^^^",combined_data)
# Shuffle the combined list
    random.shuffle(combined_data)

    # Sort the combined list based on 'created_on' attribute to display recent jobs first
    combined_data.sort(key=lambda x: x.created_on, reverse=True)


# Display the jumbled results
    for item in combined_data:
        print(item)


    for x in combined_data:
        if hasattr(x, 'company_id') and hasattr(x.company_id, 'first_name'):

            days_since_posted = (timezone.now().date() - x.created_on).days
            x.days_since_posted = days_since_posted
        elif hasattr(x, 'company_id') and hasattr(x.company_id, 'company_name'):

            days_since_posted = (timezone.now().date() - x.created_on).days
            x.days_since_posted = days_since_posted
    else:
        # Handle cases where the attribute doesn't exist for the object
        print("Attribute doesn't exist for this object")


        days_since_posted = (timezone.now().date() - x.created_on).days
        x.days_since_posted = days_since_posted

    unique_departments_agency = AgencyJobDetails.objects.values_list('department', flat=True).distinct()
    unique_departments_job = JobDetails.objects.values_list('department', flat=True).distinct()
    all_unique_departments = list(set(chain(unique_departments_agency, unique_departments_job)))

    open_status_count_job = (
        JobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_status_count_agency = (
        AgencyJobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_jobs_count = defaultdict(int)
    for item in open_status_count_job:
        open_jobs_count[item['department']] += item['open_count']

    for item in open_status_count_agency:
        open_jobs_count[item['department']] += item['open_count']

    department_open_counts = [
        (department, open_jobs_count.get(department, 0)) for department in all_unique_departments
    ]

    job_details_count = JobDetails.objects.values('location').annotate(job_count=Count('location'))

# Count jobs in each unique location from AgencyJobDetails
    agency_job_details_count = AgencyJobDetails.objects.values('location').annotate(job_count=Count('location'))

# Combine the counts
    combined_counts = {}

    for job_detail in job_details_count:
        combined_counts[job_detail['location']] = combined_counts.get(job_detail['location'], 0) + job_detail['job_count']

    for agency_job_detail in agency_job_details_count:
        combined_counts[agency_job_detail['location']] = combined_counts.get(agency_job_detail['location'], 0) + agency_job_detail['job_count']
        
    context = {'data':data,'combined_data':combined_data,
    'department_open_counts':department_open_counts,'combined_counts':combined_counts}
    return render(request,'all_jobs.html',context)


def job_description(request, job_id,u_id):
    id = request.user.id
    obj = NewUser.objects.get(id=id)
    today_date = date.today()
    # Check if the job is from a direct company
    # Check if the job is from a direct company
    i = u_id
    print("userrrrrrrrrr id",i)
    job = AgencyJobDetails.objects.select_related('company_id').filter(id=job_id, status="open").first()
    details = NewUser.objects.filter(user_type="Agency",id=u_id)
    print("@@@@@@@@@@@@@@@@@@@@",details)
    if details:
        print("HIiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii")
    else:
        job = JobDetails.objects.select_related('company_id').filter(id=job_id, status="open").first()
        print("**********************",job.designation)
    context = {
        'obj': obj,
        'today_date': today_date,
        'job': job,
        'i':i
    }
    return render(request, 'job_description.html', context)


def application(request,job_id,u_id):
    id = request.user.id
    obj = NewUser.objects.get(id=id)
    today_date = date.today()
    #print("1111111111111111111111111111")
    if request.method == 'POST':
        #print("hiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii")
        skills = request.POST.get('skills')
        qualification = request.POST.get('qualification')
        experience = request.POST.get('experience')
        expected_salary = request.POST.get('expected_salary')
        resume = request.FILES.get('resume')
        city = request.POST.get('city')
        details = NewUser.objects.filter(user_type='Agency',id=u_id)
        if details:
            application = AgencyAppliedJobs.objects.create(user_id_id=id,job_id_id=job_id,skills=skills,
            qualification=qualification,experience=experience,expected_salary=expected_salary,
            city=city,resume=resume)
            #messages.success(request, 'Your application has been submitted successfully!')
            return redirect('/jobs')
        else:
            application = AppliedJobs.objects.create(user_id_id=id,job_id_id=job_id,skills=skills,
            qualification=qualification,experience=experience,expected_salary=expected_salary,
            city=city,resume=resume)
            #messages.success(request, 'Your application has been submitted successfully!')
        #print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",application)
        #messages.success(request, "Application sent successfully")
        messages.success(request, 'Your application has been submitted successfully!')
        return redirect('user_single_job', job_id=job_id, u_id=u_id)
    
    messages.error(request, 'There was an error processing your application.')
    return redirect('user_single_job', job_id=job_id, u_id=u_id)

from django.urls import reverse
def profile(request):
    success_message = request.GET.get('success_message')
    id = request.user.id
    obj = NewUser.objects.get(id=id)
    today_date = date.today()
    print("%%%%%%%%%%%%%",obj.profile)
    data = UserDetails.objects.get(user_id=id)
    if request.method == 'POST':
        obj.first_name = request.POST.get('first_name')
        obj.last_name = request.POST.get('last_name')
        obj.email = request.POST.get('email')
        obj.city = request.POST.get('city')
        obj.country = request.POST.get('country')
        obj.profile = request.FILES.get('profile')
        data.qualification = request.POST.get('qualification')
        data.experience = request.POST.get('experience')
        data.skills = request.POST.get('skills')
        obj.save()
        data.save()
    applied_jobs = AppliedJobs.objects.select_related('job_id').filter(user_id_id=id)
    agency_applied_job = AgencyAppliedJobs.objects.select_related('job_id').filter(user_id_id=id)
    combined_jobs = list(applied_jobs) + list(agency_applied_job)
    combined_jobs.sort(key=lambda x: x.applied_date, reverse=True)
    no = len(combined_jobs)
    context = {'obj':obj,'today_date':today_date,'data':data,'success_message':success_message,'no':no}
    return render(request,'profile.html',context)

def edit_user_profile(request):
    id = request.user.id
    obj = NewUser.objects.get(id=id)
    today_date = date.today()
    data = UserDetails.objects.get(user_id=id)
    if request.method == 'POST':

        obj.first_name = request.POST.get('first_name')
        obj.last_name = request.POST.get('last_name')
        obj.phone_no = request.POST.get('phone_no')
        obj.email = request.POST.get('email')
        data.experience = request.POST.get('experience')
        data.qualification = request.POST.get('qualification')

        # Save changes
        obj.save()
        data.save()
        return redirect(reverse('profile') + '?success_message=1')  # Use the URL name ('profile') here

    context = {'obj':obj,'today_date':today_date,'data':data}
    return render(request,'edit_user_profile.html',context)

def user_logout(request):
    logout(request)
    # Redirect to a specific page after logout (optional)
    return redirect('/')

def company_logout(request):
    logout(request)
    # Redirect to a specific page after logout (optional)
    return redirect('/')

def agency_logout(request):
    logout(request)
    # Redirect to a specific page after logout (optional)
    return redirect('/')

def job_applications(request):
    logged_in_company_id = request.user.id
    obj = NewUser.objects.get(id=logged_in_company_id)
    today_date = date.today()

    job = AppliedJobs.objects.select_related('job_id', 'user_id').filter(job_id_id__company_id_id=logged_in_company_id)
    designations = AppliedJobs.objects.filter(job_id__company_id_id=logged_in_company_id).values_list('job_id__designation', flat=True).distinct()
    qualifications = AppliedJobs.objects.filter(job_id__company_id_id=logged_in_company_id).values_list('qualification', flat=True).distinct()

    context = {'obj': obj, 'today_date': today_date,'designations':designations,'qualifications':qualifications}
    if request.method == 'POST':
        for x in job:
            application_id = x.pk
            status = request.POST.get(f'status_{application_id}')

            if status:
                job_application = AppliedJobs.objects.get(pk=application_id)
                job = job_application.job_id
                application_id = job_application.id
                u = job_application.user_id_id
                des = job_application.job_id.designation
                company_name = job_application.job_id.company_id.first_name
                company_email = job_application.job_id.company_id.email

    # Check if a record with the same user_id already exists
                existing_status_record = ApplicationStatus.objects.filter(user_id_id=u, application_id_id=application_id).first()

                if existing_status_record:
        # Update the existing record
                    existing_status_record.status = status.lower()
                    existing_status_record.save()

                else:
        # Create a new record
                    obj = ApplicationStatus.objects.create(
                    user_id_id=u,
                    application_id_id=application_id,
                    status=status.lower()  # Ensure lowercase for comparison
                    )
                job_application.status = status
                job_application.save()
                user_email = job_application.user_id.email
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!",user_email)
                smtp_server = settings.EMAIL_HOST
                smtp_port = settings.EMAIL_PORT
                sender_email = settings.EMAIL_HOST_USER
                sender_password = settings.EMAIL_HOST_PASSWORD
                to_email = user_email
                if status.lower() == 'selected':
                     subject = f'Congratulations! You have been selected for the position of {des}'
                     body = f"""Congratulations! This email is to inform you that you have been selected for the position of {des} at {company_name}.qualifications stood out among the candidates, and we believe you will make a valuable contribution to our team. \nThank You\n Best Regards \n{company_name}"""
                     msg = MIMEMultipart()
                     msg['From'] = settings.EMAIL_HOST_USER
                     msg['To'] = user_email
                     msg['Subject'] = subject
                     msg.attach(MIMEText(body, 'plain'))
                     # Start the SMTP server connection
                     with smtplib.SMTP(smtp_server, smtp_port) as server:
                         server.starttls()  # Enable TLS
                         server.login(sender_email, sender_password)  # Log in to your Gmail account
                         server.sendmail(sender_email, to_email, msg.as_string())
                         recipient_email = [user_email]  # Send the email

                         send_mail(subject, body,sender_email, recipient_email)
                         messages.success(request, "Selected mail is sent successful")
                         return redirect('/job_applications')

                elif status.lower() == 'rejected':
                     subject = 'Better luck next time!'
                     body = f"""We regret to inform you that after careful consideration, you have not been selected for the position of {des} at {company_name}.\nWe encourage you to continue your job search and wish you success in your career endeavors.\n
Thank you for your interest in {company_name}.\nBest Regards\n{company_name} """

                     msg = MIMEMultipart()
                     msg['From'] = settings.EMAIL_HOST_USER
                     msg['To'] = user_email
                     msg['Subject'] = subject
                     msg.attach(MIMEText(body, 'plain'))
                     # Start the SMTP server connection
                     with smtplib.SMTP(smtp_server, smtp_port) as server:
                         server.starttls()  # Enable TLS
                         server.login(sender_email, sender_password)  # Log in to your Gmail account
                         server.sendmail(sender_email, to_email, msg.as_string())
                         recipient_email = [user_email]  # Send the email
                         send_mail(subject, body,sender_email, recipient_email)
                         messages.success(request, "Selected mail is sent successful")
                         return redirect('/job_applications')



        # After handling POST data, redirect to avoid resubmission on refresh
        return redirect('job_applications')  # Adjust the URL name if needed

    # This part will execute if it's a GET request or after the POST handling
    context['job'] = job
    return render(request, 'job_applications.html', context)


def agency_job_applications(request):
    agency_id = request.user.id
    obj = NewUser.objects.get(id=agency_id)
    today_date = date.today()
    context = {'obj': obj, 'today_date': today_date}
    job = AgencyAppliedJobs.objects.select_related('job_id','user_id').filter(job_id_id__company_id_id__agency_id_id = agency_id)
    agency_email=request.user.email
    print("88888",agency_email)
    for x in job:
        user_email=x.user_id.email
        print("99999",user_email)
    if request.method == 'POST':
        for x in job:
            application_id = x.pk
            status = request.POST.get(f'status_{application_id}')

            if status:
                job_application = AgencyAppliedJobs.objects.get(pk=application_id)
                job = job_application.job_id
                application_id = job_application.id
                u = job_application.user_id_id
                des = job_application.job_id.designation
                company_name = job_application.job_id.company_id.company_name
                company_email = job_application.job_id.company_id.company_email

    # Check if a record with the same user_id already exists
                existing_status_record = AgencyApplicationStatus.objects.filter(user_id_id=u, application_id_id=application_id).first()

                if existing_status_record:
        # Update the existing record
                    existing_status_record.status = status.lower()
                    existing_status_record.save()
                else:
        # Create a new record
                    obj = AgencyApplicationStatus.objects.create(
                    user_id_id=u,
                    application_id_id=application_id,
                    status=status.lower()  # Ensure lowercase for comparison
                    )
                job_application.status = status
                job_application.save()
                user_email = job_application.user_id.email
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!",user_email)
                smtp_server = settings.EMAIL_HOST
                smtp_port = settings.EMAIL_PORT
                sender_email = settings.EMAIL_HOST_USER
                sender_password = settings.EMAIL_HOST_PASSWORD
                to_email = user_email
                if status.lower() == 'selected':
                     subject = f'Congratulations! You have been selected for the position of {des}'
                     body = f"""Congratulations! This email is to inform you that you have been selected for the position of {des} at {company_name}.qualifications stood out among the candidates, and we believe you will make a valuable contribution to our team. \nThank You\n Best Regards \n{company_name}"""
                     msg = MIMEMultipart()
                     msg['From'] = settings.EMAIL_HOST_USER
                     msg['To'] = user_email
                     msg['Subject'] = subject
                     msg.attach(MIMEText(body, 'plain'))
                     # Start the SMTP server connection
                     with smtplib.SMTP(smtp_server, smtp_port) as server:
                         server.starttls()  # Enable TLS
                         server.login(sender_email, sender_password)  # Log in to your Gmail account
                         server.sendmail(sender_email, to_email, msg.as_string())
                         recipient_email = [user_email]  # Send the email
                         send_mail(subject, body,sender_email, recipient_email)
                         messages.success(request, "Selected mail is sent successful")
                         return redirect('/agency_job_applications')

                elif status.lower() == 'rejected':
                     subject = 'Better luck next time!'
                     body = f"""We regret to inform you that after careful consideration, you have not been selected for the position of {des} at {company_name}.\nWe encourage you to continue your job search and wish you success in your career endeavors.\n
                          Thank you for your interest in {company_name}.\nBest Regards\n{company_name} """

                     msg = MIMEMultipart()
                     msg['From'] = settings.EMAIL_HOST_USER
                     msg['To'] = user_email
                     msg['Subject'] = subject
                     msg.attach(MIMEText(body, 'plain'))
                     # Start the SMTP server connection
                     with smtplib.SMTP(smtp_server, smtp_port) as server:
                         server.starttls()  # Enable TLS
                         server.login(sender_email, sender_password)  # Log in to your Gmail account
                         server.sendmail(sender_email, to_email, msg.as_string())
                         recipient_email = [user_email]  # Send the email
                         send_mail(subject, body,sender_email, recipient_email)
                         messages.success(request, "Rejected mail is sent successful")
                         return redirect('/agency_job_applications')
                         # After handling POST data, redirect to avoid resubmission on refresh
        return redirect('agency_job_applications')  # Adjust the URL name if needed
    context['job'] = job
    return render(request, 'agency_job_applications.html', context)




def delete_application(request, pk):
    application = get_object_or_404(AppliedJobs, pk=pk)
    if request.method == 'POST':
        application.delete()
        # Redirect to the page where the table is displayed
        return redirect('job_applications')


def selected(request):
    logged_in_company_id=request.user.id
    i = request.user.id
    obj = NewUser.objects.get(id=i)
    today_date = date.today()

    data = ApplicationStatus.objects.select_related('application_id','user_id').filter(application_id_id__job_id_id__company_id_id=logged_in_company_id,status = 'selected')


    context={'data':data,'obj':obj,'today_date':today_date}
    return render(request,'selected.html',context)


def pending(request):
    logged_in_company_id=request.user.id
    data = ApplicationStatus.objects.select_related('application_id','user_id').filter(application_id_id__job_id_id__company_id_id=logged_in_company_id,status = 'pending')

    context={'data':data}
    return render(request,'pending.html',context)

def schedule_interview1(request, id):
    id = id
    print()
    company_id=request.user.id
    print("hiiiiiiiii")
    print("!!!!!!!",id)
    obj = AppliedJobs.objects.select_related('job_id','user_id').get(id=id)
    user_email = obj.user_id.email
    to_email = user_email
    print("emaillllllllllllllllllllll",user_email)
    print("%%%%",obj)
    smtp_server = settings.EMAIL_HOST
    smtp_port = settings.EMAIL_PORT
    sender_email = settings.EMAIL_HOST_USER
    sender_password = settings.EMAIL_HOST_PASSWORD


    if request.method == 'POST':
        interview_date = request.POST.get('interview_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        start_time1 = datetime.strptime(start_time, '%H:%M')
        end_time1 = datetime.strptime(end_time, '%H:%M')
        duration= end_time1-start_time1
        hours, remainder = divmod(duration.seconds, 3600)
        minutes = remainder // 60
        duration_str = f"{hours} hours, {minutes} minutes"
        print("####",duration_str)
        mode_of_interview = request.POST.get('mode_of_interview')
        interviews_on_date = ScheduleInterview.objects.filter(interview_date=interview_date,company_id=company_id)
        total_duration = timedelta()
        for interview in interviews_on_date:
            total_duration += interview.duration

        overlapping_interviews = ScheduleInterview.objects.filter(
        interview_date=interview_date,
        start_time__lt=end_time,
        end_time__gt=start_time,
        )
        print("ooooooooooooooooooooooooooooooooooooooooooooo",overlapping_interviews)
        if overlapping_interviews.exists():
            messages.error(request, "Selected time overlaps")
            return redirect('/selected')

        total_duration += duration
        if total_duration.total_seconds() > 8 * 3600:  # 8 hours in seconds
            messages.error(request, "Selected date is packed")
            return redirect('/selected')


               # Check if the record already exists
        existing_schedule = ScheduleInterview.objects.filter(application_id_id=id)


        if existing_schedule.exists():
            # Update the existing record
            existing_schedule.update(
                interview_date=interview_date,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                mode_of_interview=mode_of_interview
            )
            subject = f'rescheduled Interview'
            body = f"""Your interview has been rescheduled"""
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_HOST_USER
            msg['To'] = user_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            # Start the SMTP server connection
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # Enable TLS
                server.login(sender_email, sender_password)  # Log in to your Gmail account
                server.sendmail(sender_email, to_email, msg.as_string())
                recipient_email = [user_email]  # Send the email
                send_mail(subject, body,sender_email, recipient_email)
                messages.success(request, "Rescheduled Interview. Mail sent successfully")
                return redirect('/selected')

        else:
            # Create a new record
            ScheduleInterview.objects.create(
                company_id_id=company_id,
                application_id_id=id,
                interview_date=interview_date,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                mode_of_interview=mode_of_interview
            )
            subject = f'Interview has been scheduled'
            body = f"""Your interview has been rescheduled"""
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_HOST_USER
            msg['To'] = user_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            # Start the SMTP server connection
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # Enable TLS
                server.login(sender_email, sender_password)  # Log in to your Gmail account
                server.sendmail(sender_email, to_email, msg.as_string())
                recipient_email = [user_email]  # Send the email
                send_mail(subject, body,sender_email, recipient_email)
                messages.success(request, "Interview scheduled. Mail sent successfully")
                return redirect('/selected')
        return redirect('selected')


def agency_dashboard(request):
    today_date = date.today()
    i = request.user.id
    print(i)
    user_id = AgencyScheduleInterview.objects.select_related('application_id','companyIdOrAgencyId').filter(companyIdOrAgencyId_id = i)
    for x in user_id:
        u = x.application_id.job_id
        print("****************************",u)

    user_id_data = serialize('json', user_id)
    obj = NewUser.objects.get(id=i)
    data=AgencyScheduleInterview.objects.filter(companyIdOrAgencyId_id=i)
    context = {'today_date':today_date,'obj':obj,'data':data,'user_id':user_id,'user_id_data': user_id_data,}
    return render(request,'agency_dashboard.html',context)

@require_GET
def get_interviews(request):
    clicked_date = request.GET.get('date')  # Retrieve the clicked date from the request
    user_id = AgencyScheduleInterview.objects.filter(interview_date=clicked_date)
    interview_data = list(user_id.values('interview_date', 'application_id__job_id__company_id__company_name', 'application_id__job_id__designation', 'application_id__user_id__email', 'start_time', 'end_time', 'mode_of_interview'))
    return JsonResponse(interview_data, safe=False)

def company_details(request):
    success_message = request.GET.get('success_message')
    if request.method == 'POST':
        # Assuming your form contains the fields 'id' and 'status'
        company_id = request.POST.get('id')
        new_status = request.POST.get('status')

        # Update the status in the Agency_Company model
        try:
            company = Agency_Company.objects.get(id=company_id)
            company.status = new_status
            company.save()
            return HttpResponse(status=204)  # Indicates successful AJAX request
        except Agency_Company.DoesNotExist:
            return HttpResponse(status=404)  # Company not found
    else:
        today_date = date.today()
        i = request.user.id
        obj = NewUser.objects.get(id=i)
        data = Agency_Company.objects.filter(agency_id_id=i,status='open')

        context = {'data': data, 'today_date': today_date, 'obj': obj,'success_message':success_message}
        return render(request, 'company_details.html', context)


def Add_company(request):
    today_date = date.today()
    i=request.user.id
    obj = NewUser.objects.get(id=i)
    context={'today_date':today_date,'obj':obj}
    if request.method == 'POST':
        c_name = request.POST.get('c_name')
        c_p_email = request.POST.get('c_p_email')
        c_p_name = request.POST.get('c_p_name')
        c_email = request.POST.get('c_email')
        c_p_phone_no = request.POST.get('c_p_phone_no')
        c_p_designation = request.POST.get('c_p_designation')
        state = request.POST.get('state')
        city = request.POST.get('city')
        country = request.POST.get('country')
        zip_code = request.POST.get('zip_code')
        about = request.POST.get('about')
        p = request.FILES.get('profile')
        user = Agency_Company.objects.create(agency_id_id=i,company_name=c_name,contact_person_name=c_p_name,c_p_email=c_p_email,
        company_email=c_email,c_p_phone_no=c_p_phone_no,c_p_designation=c_p_designation,state=state,city=city,profile=p,country=country,
        pin_code=zip_code,about=about,c_email=c_email)

        return redirect(reverse('company_details') + '?success_message=1')
    return render(request,'add_company.html',context)


def delete_operator(request, id):
    application = get_object_or_404(Agency_Company, id=id)
    if request.method == 'POST':
        application.delete()
        return redirect('company_details')


def agency_job(request,id):
    i=id
    today_date = date.today()
    it = request.user.id
    obj = NewUser.objects.get(id=it)
    context = {'obj':obj,'today_date':today_date}
    if request.method == 'POST':
        designation = request.POST.get('designation')
        department = request.POST.get('department')
        location = request.POST.get('location')
        work_mode = request.POST.get('work_mode')
        no_of_vacancy = request.POST.get('no_of_vacancy')
        mandatory_skills = request.POST.get('mandatory_skills')
        optional_skills = request.POST.get('optional_skills')
        experience = request.POST.get('experience')
        qualification = request.POST.get('qualification')
        salary = request.POST.get('salary')
        status = request.POST.get('status')
        description = request.POST.get('description')

        obj = AgencyJobDetails.objects.create(company_id_id=i,designation=designation,department=department,location=location,work_mode=work_mode,
        no_of_vacancy=no_of_vacancy,mandatory_skills=mandatory_skills,optional_skills=optional_skills,
        qualification=qualification,experience=experience,
        salary=salary,job_description=description)

        print(obj)
        return redirect(reverse('agency_job_details') + '?success_message=1')

    return render(request,'agency_job.html',context)


def agency_job_details(request):
    success_message = request.GET.get('success_message')
    i = request.user.id
    obj = NewUser.objects.get(id=i)
    today_date = date.today()

    data = AgencyJobDetails.objects.select_related('company_id').filter(company_id_id__agency_id_id = i)
    for x in data:
        cn = x.company_id.company_name
        print("!!!!!!!!!",cn)


    context = {'obj':obj,'today_date':today_date,'data':data,'success_message':success_message}

    return render(request,'agency_job_details.html',context)


def agency_selected(request):
    id=request.user.id
    obj = NewUser.objects.get(id=id)
    today_date = date.today()
    data = AgencyApplicationStatus.objects.select_related('application_id__job_id').filter(application_id_id__job_id_id__company_id_id__agency_id_id = id,status='selected')
    context={'data':data,'obj':obj,'today_date':today_date}
    return render(request,'agency_selected.html',context)


def agency_schedule_interview(request, id):
    id = id
    agency_id=request.user.id
    print("hiiiiiiiii")
    print("!!!!!!!",id)
    obj = AgencyAppliedJobs.objects.select_related('user_id').get(id=id)
    print("%%%%",obj)
    job_id=obj.job_id_id
    data1=AgencyJobDetails.objects.select_related('company_id').get(id=job_id)
    des=data1.designation
    company_name = data1.company_id.company_name
    company_c_p_email = data1.company_id.c_p_email
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&",company_c_p_email)
    print("$$$$",des)
    print("userrrrrrrrrrrrrr mail",obj.user_id.email)
    to_email = obj.user_id.email
    user_email = to_email
    user_email1 = company_c_p_email
    to_email1 = company_c_p_email
    smtp_server = settings.EMAIL_HOST
    smtp_port = settings.EMAIL_PORT
    sender_email = settings.EMAIL_HOST_USER
    sender_password = settings.EMAIL_HOST_PASSWORD
    if request.method == 'POST':
        interview_date = request.POST.get('interview_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        start_time1 = datetime.strptime(start_time, '%H:%M')
        end_time1 = datetime.strptime(end_time, '%H:%M')
        duration= end_time1-start_time1
        hours, remainder = divmod(duration.seconds, 3600)
        minutes = remainder // 60
        duration_str = f"{hours} hours, {minutes} minutes"
        print("####",duration_str)
        mode_of_interview = request.POST.get('mode_of_interview')
        interviews_on_date = AgencyScheduleInterview.objects.filter(interview_date=interview_date,agency_id=agency_id)
        total_duration = timedelta()
        for interview in interviews_on_date:
            total_duration += interview.duration

        overlapping_interviews = AgencyScheduleInterview.objects.filter(
        interview_date=interview_date,
        start_time__lt=end_time,
        end_time__gt=start_time,
        )
        if overlapping_interviews.exists():
            messages.error(request, "Selected time overlaps")
            return redirect('/agency_selected')

        total_duration += duration
        if total_duration.total_seconds() > 8 * 3600:
            messages.error(request, "selected date is already packed")
            return redirect('/agency_selected')  # 8 hours in seconds


               # Check if the record already exists
        existing_schedule = AgencyScheduleInterview.objects.filter(application_id_id=id)


        if existing_schedule.exists():
            # Update the existing record
            existing_schedule.update(
                interview_date=interview_date,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                mode_of_interview=mode_of_interview
            )
            subject = f'Revised Interview Date for {des} Interview'
            body = f"""Dear {obj.user_id.username} \nSending this mail to inform you about a change in the schedule for your upcoming interview for the {des} at {company_name}. After careful consideration, we have revised the interview timetable. Updated details as below\n
            Date : {interview_date}\nStart Time : {start_time}\nEnd Time : {start_time}\nMode : {mode_of_interview}\nThank You\n Warn Regards, \n{company_name}"""
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_HOST_USER
            msg['To'] = user_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            # Start the SMTP server connection
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # Enable TLS
                server.login(sender_email, sender_password)  # Log in to your Gmail account
                server.sendmail(sender_email, to_email, msg.as_string())
                recipient_email = [user_email]  # Send the email
                send_mail(subject, body,sender_email, recipient_email)


            subject = f'Revised Interview Date for recruiter'
            body = f"""Recruiter email rescheduled mail"""
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_HOST_USER
            msg['To'] = company_c_p_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            # Start the SMTP server connection
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # Enable TLS
                server.login(sender_email, sender_password)  # Log in to your Gmail account
                server.sendmail(sender_email, to_email1, msg.as_string())
                recipient_email = [user_email1]  # Send the email
                send_mail(subject, body,sender_email, recipient_email)
                messages.success(request, "Rescheduled Interview. Mail sent successfully")
                return redirect('/agency_selected')
        else:
            # Create a new record
            AgencyScheduleInterview.objects.create(
                agency_id_id=agency_id,
                application_id_id=id,
                interview_date=interview_date,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                mode_of_interview=mode_of_interview
            )
            subject = f'Interview Date for {des} Interview'
            body = f"""Dear {obj.user_id.username} \nSending this mail to inform you about a change in the schedule for your upcoming interview for the {des} at {company_name}. After careful consideration, we have revised the interview timetable. Updated details as below\n
            Date : {interview_date}\nStart Time : {start_time}\nEnd Time : {end_time}\nMode : {mode_of_interview}\nThank You\n Warn Regards, \n{company_name}"""
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_HOST_USER
            msg['To'] = user_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            # Start the SMTP server connection
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # Enable TLS
                server.login(sender_email, sender_password)  # Log in to your Gmail account
                server.sendmail(sender_email, to_email, msg.as_string())
                recipient_email = [user_email]  # Send the email
                send_mail(subject, body,sender_email, recipient_email)

            subject = f'Interview Date for recruiter'
            body = f"""Recruiter email rescheduled mail"""
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_HOST_USER
            msg['To'] = company_c_p_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            # Start the SMTP server connection
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # Enable TLS
                server.login(sender_email, sender_password)  # Log in to your Gmail account
                server.sendmail(sender_email, to_email1, msg.as_string())
                recipient_email = [user_email1]  # Send the email
                send_mail(subject, body,sender_email, recipient_email)
                messages.success(request, "scheduled Interview. Mail sent successfully")
                return redirect('/agency_selected')
        return redirect('agency_selected')
    context={'data1':data1}
    return render(request, 'agency_selected.html',context)

import json
@csrf_exempt
def save_job(request, job_id, u_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        job_id = data.get('job_id')
        u_id = data.get('u_id')

        # Fetch user and company/agency based on IDs (Replace this logic as per your actual implementation)
        user_id = request.user.id

        # Replace '1' with your logic to fetch the user
        # Replace this with your logic
        details = NewUser.objects.filter(user_type='Agency', id=u_id)

        if details.exists():
            saved_job = AgencyJobSaved.objects.create(
                user_id_id=user_id,
                companyIdOrAgencyId_id=u_id,
                job_id_id=job_id
            )
            return JsonResponse({'message': 'Job saved successfully'})
        else:
            saved_job = CompanyJobSaved.objects.create(
                user_id_id=user_id,
                companyIdOrAgencyId_id=u_id,
                job_id_id=job_id
            )
            return JsonResponse({'message': 'Job saved successfully'})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def remove_job(request, job_id, u_id):
    if request.method == 'POST':
        # Fetch user ID (You may have a different way of retrieving the user ID)
        user_id = request.user.id

        # Check if the job exists in the saved jobs of the user
        try:
            if AgencyJobSaved.objects.filter(user_id_id=user_id, companyIdOrAgencyId_id=u_id, job_id_id=job_id).exists():
                saved_job = AgencyJobSaved.objects.get(user_id_id=user_id, companyIdOrAgencyId_id=u_id, job_id_id=job_id)
                saved_job.delete()
                return JsonResponse({'message': 'Job removed successfully'})
            elif CompanyJobSaved.objects.filter(user_id_id=user_id, companyIdOrAgencyId_id=u_id, job_id_id=job_id).exists():
                saved_job = CompanyJobSaved.objects.get(user_id_id=user_id, companyIdOrAgencyId_id=u_id, job_id_id=job_id)
                saved_job.delete()
                return JsonResponse({'message': 'Job removed successfully'})
            else:
                return JsonResponse({'error': 'Job not found in saved jobs'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)

def company(request,id):
    print("iddddddddd",id)
    obj = NewUser.objects.get(id=id)
    info = CompanyDetails.objects.filter(companyOrAgency_id_id=id).first()
    c_img = info.cover_image
    print(info.other_image1)
    
    company_names = []
    company_jobs_dict = {}

    if obj.user_type == 'Company':
        # If the user is a company, retrieve jobs related to that company
        jobs = JobDetails.objects.filter(company_id_id=id)
        company_names = [obj.first_name]
        display_jobs = JobDetails.objects.filter(company_id_id=id)  # Assuming company_name exists in the NewUser model
        # Additional logic for companies if needed
    else:
        display_jobs = AgencyJobDetails.objects.filter(company_id_id=id)
        # If the user is not a company, assume it's an agency and retrieve jobs related to that agency
        # Fetch unique company names and associated job details for agencies
        companies_with_jobs = (
            
            AgencyJobDetails.objects.filter(agency_id_id=id)
            .values('company_id__company_name', 'designation', 'no_of_vacancy')
            .distinct()
        )

        for company in companies_with_jobs:
            company_name = company['company_id__company_name']
            job_details = {
                'designation': company['designation'],

                'no_of_vacancy': company['no_of_vacancy'],
                # Add other job details here
            }
            if company_name in company_jobs_dict:
                company_jobs_dict[company_name].append(job_details)
            else:
                company_jobs_dict[company_name] = [job_details]
            print(company_jobs_dict)

        company_names = list(company_jobs_dict.keys())
        for x in company_names:
            print(x)
        jobs = None  # No direct jobs to display for agencies

    
    context = {
        'jobs': jobs,
        'company_names': company_names,
        'company_jobs_dict': company_jobs_dict,
        'obj': obj,
        'info':info,
        'c_img':c_img,
        'display_jobs':display_jobs
        
    }
    return render(request,'company.html',context)

def company_info(request,id):
    print("iddddddddd",id)
    obj = NewUser.objects.get(id=id)
    info = CompanyDetails.objects.filter(companyOrAgency_id_id=id).first()
    c_img = info.cover_image
    print(info.other_image1)
    
    company_names = []
    company_jobs_dict = {}

    if obj.user_type == 'Company':
        # If the user is a company, retrieve jobs related to that company
        jobs = JobDetails.objects.filter(company_id_id=id)
        company_names = [obj.first_name]
        display_jobs = JobDetails.objects.filter(company_id_id=id)  # Assuming company_name exists in the NewUser model
        # Additional logic for companies if needed
    else:
        display_jobs = AgencyJobDetails.objects.filter(company_id_id=id)
        # If the user is not a company, assume it's an agency and retrieve jobs related to that agency
        # Fetch unique company names and associated job details for agencies
        companies_with_jobs = (
            
            AgencyJobDetails.objects.filter(agency_id_id=id)
            .values('company_id__company_name', 'designation', 'no_of_vacancy')
            .distinct()
        )

        for company in companies_with_jobs:
            company_name = company['company_id__company_name']
            job_details = {
                'designation': company['designation'],

                'no_of_vacancy': company['no_of_vacancy'],
                # Add other job details here
            }
            if company_name in company_jobs_dict:
                company_jobs_dict[company_name].append(job_details)
            else:
                company_jobs_dict[company_name] = [job_details]
            print(company_jobs_dict)

        company_names = list(company_jobs_dict.keys())
        for x in company_names:
            print(x)
        jobs = None  # No direct jobs to display for agencies

    
    context = {
        'jobs': jobs,
        'company_names': company_names,
        'company_jobs_dict': company_jobs_dict,
        'obj': obj,
        'info':info,
        'c_img':c_img,
        'display_jobs':display_jobs
        
    }
    return render(request,'company_info.html',context)

def saved_jobs1(request):
    user_id = request.user.id
    agency_jobs = AgencyJobSaved.objects.select_related('companyIdOrAgencyId','job_id').filter(user_id=user_id)

    # Fetch saved jobs from CompanyJobSaved model for the given user_id
    company_jobs = CompanyJobSaved.objects.filter(user_id=user_id)
    print("$$$$$$$$$$$",company_jobs)

    # Combine the job details from both models into a single variable
    all_saved_jobs = list(chain(agency_jobs, company_jobs))

    saved_agency_jobs_ids = AgencyJobSaved.objects.filter(user_id=request.user.id).values_list('job_id_id', flat=True)
    saved_company_jobs_ids = CompanyJobSaved.objects.filter(user_id=request.user.id).values_list('job_id_id', flat=True)
    saved_job_ids = list(saved_agency_jobs_ids) + list(saved_company_jobs_ids)
    print("^^^^^^^^^^^^^^^",saved_job_ids)

    for x in all_saved_jobs:
        print(x.job_id.company_id.profile)
        x.is_saved = x.id in saved_job_ids
    context = {
    'all_saved_jobs':all_saved_jobs,
    'combined_counts':combined_counts

    }

    return render(request,'saved_jobs.html',context)

def saved_jobs(request):
    id = request.user.id
    obj = NewUser.objects.get(id=id)
    today_date = date.today()
    print("profileeee",obj.profile)
    agency_jobs = AgencyJobSaved.objects.select_related('companyIdOrAgencyId','job_id').filter(user_id=id)

    # Fetch saved jobs from CompanyJobSaved model for the given user_id
    company_jobs = CompanyJobSaved.objects.select_related('companyIdOrAgencyId','job_id').filter(user_id=id)
    print("$$$$$$$$$$$",company_jobs)

    # Combine the job details from both models into a single variable
    all_saved_jobs = list(chain(agency_jobs, company_jobs))

    saved_agency_jobs_ids = AgencyJobSaved.objects.filter(user_id=request.user.id).values_list('job_id_id', flat=True)
    saved_company_jobs_ids = CompanyJobSaved.objects.filter(user_id=request.user.id).values_list('job_id_id', flat=True)
    saved_job_ids = list(saved_agency_jobs_ids) + list(saved_company_jobs_ids)

    for x in all_saved_jobs:
        print(x)
        days_since_posted = (timezone.now().date() - x.job_id.created_on).days
        x.days_since_posted = days_since_posted
        #print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",x.days_since_posted)
        x.is_saved = x.id in saved_job_ids




    # Merge the saved job IDs from both models
    saved_job_ids = list(saved_agency_jobs_ids) + list(saved_company_jobs_ids)

    unique_departments_agency = AgencyJobDetails.objects.values_list('department', flat=True).distinct()
    unique_departments_job = JobDetails.objects.values_list('department', flat=True).distinct()
    all_unique_departments = list(set(chain(unique_departments_agency, unique_departments_job)))

    open_status_count_job = (
        JobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_status_count_agency = (
        AgencyJobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_jobs_count = defaultdict(int)
    for item in open_status_count_job:
        open_jobs_count[item['department']] += item['open_count']

    for item in open_status_count_agency:
        open_jobs_count[item['department']] += item['open_count']

    department_open_counts = [
        (department, open_jobs_count.get(department, 0)) for department in all_unique_departments
    ]

    job_details_count = JobDetails.objects.values('location').annotate(job_count=Count('location'))

# Count jobs in each unique location from AgencyJobDetails
    agency_job_details_count = AgencyJobDetails.objects.values('location').annotate(job_count=Count('location'))

# Combine the counts
    combined_counts = {}

    for job_detail in job_details_count:
        combined_counts[job_detail['location']] = combined_counts.get(job_detail['location'], 0) + job_detail['job_count']

    for agency_job_detail in agency_job_details_count:
        combined_counts[agency_job_detail['location']] = combined_counts.get(agency_job_detail['location'], 0) + agency_job_detail['job_count']

    context = {'obj':obj,'today_date':today_date
    ,'department_open_counts':department_open_counts,'all_saved_jobs':all_saved_jobs}
    return render(request,'saved_jobs.html',context)


def search_trend(request, keyword):
    print(keyword)
    if keyword == 'freshers':
        job_details = JobDetails.objects.filter(
            Q(experience='Fresher') | Q(experience__startswith='0-'),
            status='open'
        )
        agency_job_details = AgencyJobDetails.objects.filter(
            Q(experience='Fresher') | Q(experience__startswith='0-'),
            status='open'
        )
    elif keyword == 'banking':
        job_details = JobDetails.objects.filter(
            Q(department='Finance and Accounting'),
            status='open'
        )
        agency_job_details = AgencyJobDetails.objects.filter(
            Q(department='Finance and Accounting'),
            status='open'
        )
    elif keyword == 'part-time':
        job_details = JobDetails.objects.filter(
            Q(job_type='Part time'),
            status='open'
        )
        agency_job_details = AgencyJobDetails.objects.filter(
            Q(job_type='Part time'),
            status='open'
        )
    else:
        job_details = JobDetails.objects.filter(
            Q(department='Research and Development') | Q(department='Information Technology (IT)') ,
            status='open'
        )
        agency_job_details = AgencyJobDetails.objects.filter(
             Q(department='Research and Development') | Q(department='Information Technology (IT)') ,
            status='open'
        )
    print("##########", job_details)
    #print("##########",agency_job_details)
    all_jobs = list(chain(job_details, agency_job_details))
    for job in all_jobs:
        today = datetime.now().date()  # Define 'today' here for each iteration
        days_posted_ago = (today - job.created_on).days
        job.days_posted_ago = days_posted_ago

    # Sort the combined queryset based on days posted (latest at the top)
    all_jobs = sorted(all_jobs, key=lambda x: x.created_on, reverse=True)
    #print("^^^^^^^^^^^^^",all_jobs)
    unique_departments_agency = AgencyJobDetails.objects.values_list('department', flat=True).distinct()
    unique_departments_job = JobDetails.objects.values_list('department', flat=True).distinct()
    all_unique_departments = list(set(chain(unique_departments_agency, unique_departments_job)))

    open_status_count_job = (
        JobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_status_count_agency = (
        AgencyJobDetails.objects.filter(status='open')
        .values('department')
        .annotate(open_count=Count('department'))
    )

    open_jobs_count = defaultdict(int)
    for item in open_status_count_job:
        open_jobs_count[item['department']] += item['open_count']

    for item in open_status_count_agency:
        open_jobs_count[item['department']] += item['open_count']

    department_open_counts = [
        (department, open_jobs_count.get(department, 0)) for department in all_unique_departments
    ]
    print("^^^^^^^^^^^^^^^^",department_open_counts)
    work_modes = AgencyJobDetails.objects.values_list('work_mode', flat=True).distinct()

    job_details_count = JobDetails.objects.values('location').annotate(job_count=Count('location'))

# Count jobs in each unique location from AgencyJobDetails
    agency_job_details_count = AgencyJobDetails.objects.values('location').annotate(job_count=Count('location'))

# Combine the counts
    combined_counts = {}

    for job_detail in job_details_count:
        combined_counts[job_detail['location']] = combined_counts.get(job_detail['location'], 0) + job_detail['job_count']

    for agency_job_detail in agency_job_details_count:
        combined_counts[agency_job_detail['location']] = combined_counts.get(agency_job_detail['location'], 0) + agency_job_detail['job_count']

    context = {
        'all_jobs': all_jobs,
        'department_open_counts':department_open_counts,
        'work_modes':work_modes,
        'combined_counts':combined_counts,'keyword':keyword,
    }
    return render(request,'search_trend.html', context)

def single_job(request,job_id,u_id):
    job = AgencyJobDetails.objects.select_related('company_id').filter(id=job_id, status="open").first()
    details = NewUser.objects.filter(user_type="Agency",id=u_id)
    print("@@@@@@@@@@@@@@@@@@@@",details)
    if details:
        print("HIiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii")
    else:
        job = JobDetails.objects.select_related('company_id').filter(id=job_id, status="open").first()
        print("**********************",job.designation)
    context = {

        'job': job,

    }
    return render(request, 'single_job.html',context)