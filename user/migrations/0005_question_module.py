# Generated by Django 5.1.6 on 2025-03-07 17:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_student_login_time_student_test_end_time_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='module',
            field=models.CharField(blank=True, editable=False, max_length=50, null=True),
        ),
    ]
