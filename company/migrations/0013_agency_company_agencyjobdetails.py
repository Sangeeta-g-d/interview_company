# Generated by Django 4.1.7 on 2023-12-02 10:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0012_scheduleinterview'),
    ]

    operations = [
        migrations.CreateModel(
            name='Agency_Company',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(default='company', max_length=100)),
                ('contact_person_name', models.CharField(default='name', max_length=100)),
                ('c_p_email', models.EmailField(max_length=254)),
                ('c_p_phone_no', models.CharField(default='9999999999', max_length=100)),
                ('company_email', models.EmailField(max_length=254)),
                ('c_p_designation', models.CharField(default='xyz', max_length=300)),
                ('city', models.CharField(default='hubli', max_length=100)),
                ('profile', models.ImageField(default='profile', upload_to='uploaded_images/')),
                ('state', models.CharField(default='karnataka', max_length=100)),
                ('country', models.CharField(default='India', max_length=100)),
                ('pin_code', models.CharField(default='zip', max_length=100)),
                ('about', models.CharField(default='about', max_length=1000)),
                ('hired', models.IntegerField(default='0')),
                ('status', models.CharField(default='open', max_length=1000)),
                ('agency_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='AgencyJobDetails',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('designation', models.CharField(default='data analyst', max_length=300)),
                ('job_description', models.CharField(default='abc', max_length=1000)),
                ('department', models.CharField(default='sales', max_length=300)),
                ('location', models.CharField(default='hubli', max_length=300)),
                ('work_mode', models.CharField(default='work from office', max_length=100)),
                ('no_of_vacancy', models.CharField(default='2', max_length=100)),
                ('mandatory_skills', models.CharField(default='HTML', max_length=500)),
                ('optional_skills', models.CharField(default='C', max_length=500)),
                ('experience', models.CharField(default='fresher', max_length=200)),
                ('salary', models.CharField(default='3LPA', max_length=400)),
                ('qualification', models.CharField(default='BCA', max_length=300)),
                ('created_on', models.DateField(auto_now_add=True)),
                ('status', models.BooleanField(default=1)),
                ('company_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='company.agency_company')),
            ],
        ),
    ]
