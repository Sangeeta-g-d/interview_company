# Generated by Django 4.1.7 on 2023-12-06 05:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0019_rename_application_id_agencyscheduleinterview_a_application_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='agencyappliedjobs',
            old_name='job_id',
            new_name='a_job_id',
        ),
    ]
