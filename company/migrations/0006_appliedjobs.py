# Generated by Django 4.1.7 on 2023-11-26 17:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0005_userdetails'),
    ]

    operations = [
        migrations.CreateModel(
            name='AppliedJobs',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('experience', models.CharField(default='fresher', max_length=500)),
                ('qualification', models.CharField(default='BE', max_length=400)),
                ('skills', models.CharField(default='HTML', max_length=600)),
                ('city', models.CharField(default='Hubli', max_length=500)),
                ('expected_salary', models.CharField(max_length=300)),
                ('resume', models.FileField(upload_to='applied_resume/')),
                ('applied_date', models.DateField(default=django.utils.timezone.now)),
                ('job_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='company.jobdetails')),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
