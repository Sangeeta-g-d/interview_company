# Generated by Django 4.2.6 on 2024-01-01 06:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0030_agencyjobdetails_country_agencyjobdetails_state_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='newuser',
            name='email_password',
        ),
    ]
