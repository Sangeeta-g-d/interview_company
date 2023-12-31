# Generated by Django 4.1.7 on 2023-12-04 10:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0017_agencyapplicationstatus'),
    ]

    operations = [
        migrations.CreateModel(
            name='AgencyScheduleInterview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interview_date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('duration', models.DurationField()),
                ('mode_of_interview', models.CharField(default='IN_office', max_length=500)),
                ('confirm', models.CharField(default='confirm', max_length=100)),
                ('agency_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('application_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='company.appliedjobs')),
            ],
        ),
    ]
