# Generated by Django 4.1.7 on 2023-12-17 17:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0022_agencyjobdetails_job_type_jobdetails_job_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agencyjobdetails',
            name='status',
            field=models.CharField(default='open', max_length=10),
        ),
        migrations.AlterField(
            model_name='jobdetails',
            name='status',
            field=models.CharField(default='open', max_length=10),
        ),
    ]
