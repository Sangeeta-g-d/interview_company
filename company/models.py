from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from django.core.validators import MaxValueValidator
from datetime import datetime

# Create your models here.
class NewUser(AbstractUser):
    user_type = models.CharField(max_length=100, default='job seeker')
    phone_no = models.CharField(max_length=100, default='9999999999')
    country = models.CharField(max_length=300, default='India')
    state = models.CharField(max_length=300, default='Karnataka')
    address = models.CharField(max_length=100, default='abc')
    city = models.CharField(max_length=100, default='hubli')
    about = models.CharField(max_length=1000, default='about')
    profile = models.ImageField(upload_to='uploaded_images/',default="profile")
    status = models.BooleanField(default=0)
    

class CompanyDetails(models.Model):
    companyOrAgency_id=models.ForeignKey('NewUser', on_delete=models.CASCADE)
    tag_line = models.CharField(max_length=700, default='tagline')
    company_type = models.CharField(max_length=100, default='startup')
    company_service_sector = models.CharField(max_length=1000, default='IT Services')
    why_us = models.CharField(max_length=2000, default='abcd')
    founded_year = models.PositiveIntegerField(
        validators=[MaxValueValidator(datetime.now().year)]  # Maximum year as current year
    )
    head_branch = models.CharField(max_length=500,default='hubli')
    milestone = models.CharField(max_length=4000,default='none')
    linkedin_url = models.URLField(max_length=500,default='https://example.com')
    instagram_url = models.URLField(max_length=500,default='https://example.com')
    facebook = models.URLField(max_length=500,default='https://example.com')
    webiste = models.URLField(max_length=500,default='https://example.com')
    Key_highlights = models.CharField(max_length=2000, default='highlights')
    cover_image = models.ImageField(upload_to='company_images/',default="cover_image")
    other_image1 = models.ImageField(upload_to='company_images/',default='img1')
    other_image2 = models.ImageField(upload_to='company_images/',default='img2')
    

class Agency_Company(models.Model):
    agency_id=models.ForeignKey('NewUser', on_delete=models.CASCADE)
    company_name= models.CharField(max_length=100, default='company')
    contact_person_name= models.CharField(max_length=100, default='name')
    c_p_email=models.EmailField()
    c_p_phone_no= models.CharField(max_length=100, default='9999999999')
    company_email=models.EmailField()
    c_p_designation= models.CharField(max_length=300, default='xyz')
    city = models.CharField(max_length=100, default='hubli')
    profile = models.ImageField(upload_to='uploaded_images/',default="profile")
    state = models.CharField(max_length=100, default='karnataka')
    country = models.CharField(max_length=100, default='India')
    pin_code=models.CharField(max_length=100, default='zip')
    about = models.CharField(max_length=1000, default='about')
    hired=models.IntegerField( default='0')
    status = models.CharField(max_length=1000, default='open')
    c_email = models.EmailField(default='xyz@gmail.com')


class AgencyJobDetails(models.Model):
    company_id = models.ForeignKey('Agency_Company', on_delete=models.CASCADE)
    agency_id = models.ForeignKey('NewUser',on_delete=models.CASCADE,default=9)
    designation = models.CharField(max_length=300,default='data analyst')
    job_description = models.CharField(max_length=1000,default='abc')
    department = models.CharField(max_length=300,default='sales')
    location = models.CharField(max_length=300,default='hubli')
    work_mode = models.CharField(max_length=100,default='work from office')
    no_of_vacancy = models.CharField(max_length=100,default='2')
    mandatory_skills = models.CharField(max_length=500,default='HTML')
    optional_skills = models.CharField(max_length=500,default='C')
    experience = models.CharField(max_length=200,default='fresher')
    salary = models.CharField(max_length=400,default='3LPA')
    qualification = models.CharField(max_length=300,default='BCA')
    created_on = models.DateField(auto_now_add = True)
    status = models.CharField(max_length=10, default='open')
    job_type = models.CharField(max_length=100, default='Full time')
    country = models.CharField(max_length=300, default='India')
    state = models.CharField(max_length=300, default='Karnataka')


class JobDetails(models.Model):
    company_id = models.ForeignKey('NewUser', on_delete=models.CASCADE)
    designation = models.CharField(max_length=300,default='data analyst')
    job_description = models.CharField(max_length=1000,default='abc')
    department = models.CharField(max_length=300,default='sales')
    location = models.CharField(max_length=300,default='hubli')
    work_mode = models.CharField(max_length=100,default='work from office')
    no_of_vacancy = models.CharField(max_length=100,default='2')
    mandatory_skills = models.CharField(max_length=500,default='HTML')
    optional_skills = models.CharField(max_length=500,default='C')
    experience = models.CharField(max_length=200,default='fresher')
    salary = models.CharField(max_length=400,default='3LPA')
    qualification = models.CharField(max_length=300,default='BCA')
    created_on = models.DateField(auto_now_add = True)
    status = models.CharField(max_length=10, default='open')
    job_type = models.CharField(max_length=100, default='Full time')
    country = models.CharField(max_length=300, default='India')
    state = models.CharField(max_length=300, default='Karnataka')


class UserDetails(models.Model):
    user_id = models.ForeignKey('NewUser', on_delete=models.CASCADE)
    qualification = models.CharField(max_length=300,default='BCA')
    experience = models.CharField(max_length=300,default='fresher')
    skills = models.CharField(max_length=400,default='html')
    DOB = models.CharField(max_length=100)
    about = models.CharField(max_length=1000,default='Passionate professional dedicated to driving innovation and fostering growth through collaboration and strategic expertise.')


class AppliedJobs(models.Model):
    user_id = models.ForeignKey('NewUser',on_delete=models.CASCADE)
    job_id = models.ForeignKey('JobDetails',on_delete=models.CASCADE)
    experience = models.CharField(max_length=500,default='fresher')
    qualification = models.CharField(max_length=400,default='BE')
    skills = models.CharField(max_length=600,default='HTML')
    city = models.CharField(max_length=500,default='Hubli')
    expected_salary = models.CharField(max_length=300)
    resume = models.FileField(upload_to='applied_resume/')
    applied_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=200,default='Pending')


class AgencyAppliedJobs(models.Model):
    user_id = models.ForeignKey('NewUser',on_delete=models.CASCADE)
    job_id = models.ForeignKey('AgencyJobDetails',on_delete=models.CASCADE)
    experience = models.CharField(max_length=500,default='fresher')
    qualification = models.CharField(max_length=400,default='BE')
    skills = models.CharField(max_length=600,default='HTML')
    city = models.CharField(max_length=500,default='Hubli')
    expected_salary = models.CharField(max_length=300)
    resume = models.FileField(upload_to='applied_resume/')
    applied_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=200,default='Pending')



class ApplicationStatus(models.Model):
    user_id = models.ForeignKey('NewUser',on_delete=models.CASCADE)
    application_id = models.ForeignKey('AppliedJobs',on_delete=models.CASCADE)
    status = models.CharField(max_length=500,default='rejected')

class AgencyApplicationStatus(models.Model):
    user_id = models.ForeignKey('NewUser',on_delete=models.CASCADE)
    application_id = models.ForeignKey('AgencyAppliedJobs',on_delete=models.CASCADE)
    status = models.CharField(max_length=500,default='rejected')

class ScheduleInterview(models.Model):
    companyIdOrAgencyId =  models.ForeignKey('NewUser',on_delete=models.CASCADE)
    application_id = models.ForeignKey('AppliedJobs',on_delete=models.CASCADE)
    interview_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.DurationField()
    mode_of_interview= models.CharField(max_length=500,default='IN_office')

class AgencyScheduleInterview(models.Model):
    companyIdOrAgencyId =  models.ForeignKey('NewUser',on_delete=models.CASCADE)
    application_id = models.ForeignKey('AgencyAppliedJobs',on_delete=models.CASCADE,default=1)
    interview_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.DurationField()
    mode_of_interview= models.CharField(max_length=500,default='IN_office')
    confirm = models.CharField(max_length=100,default='confirm')


class AgencyJobSaved(models.Model):
    user_id=models.ForeignKey('NewUser',on_delete=models.CASCADE,related_name='userId')
    companyIdOrAgencyId=models.ForeignKey('NewUser',on_delete=models.CASCADE,related_name='agencyId')
    applied_date = models.DateField(default=timezone.now)
    job_id = models.ForeignKey('AgencyJobDetails',on_delete=models.CASCADE,default=1)

class CompanyJobSaved(models.Model):
    user_id=models.ForeignKey('NewUser',on_delete=models.CASCADE,related_name='UserId')
    companyIdOrAgencyId=models.ForeignKey('NewUser',on_delete=models.CASCADE,related_name='companyId')
    applied_date = models.DateField(default=timezone.now)
    job_id = models.ForeignKey('JobDetails',on_delete=models.CASCADE,default=1)
