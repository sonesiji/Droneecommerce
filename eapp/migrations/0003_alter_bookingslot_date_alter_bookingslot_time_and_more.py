# Generated by Django 4.2.5 on 2025-01-27 17:15

import django.core.validators
from django.db import migrations, models
import eapp.models


class Migration(migrations.Migration):

    dependencies = [
        ('eapp', '0002_instructor_email_instructor_password_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookingslot',
            name='date',
            field=models.DateField(validators=[eapp.models.validate_future_date]),
        ),
        migrations.AlterField(
            model_name='bookingslot',
            name='time',
            field=models.TimeField(validators=[eapp.models.validate_business_hours]),
        ),
        migrations.AlterField(
            model_name='instructor',
            name='experience',
            field=models.TextField(validators=[django.core.validators.MinLengthValidator(50)]),
        ),
        migrations.AlterField(
            model_name='instructor',
            name='name',
            field=models.CharField(max_length=100, validators=[django.core.validators.MinLengthValidator(2)]),
        ),
        migrations.AlterField(
            model_name='instructor',
            name='password',
            field=models.CharField(blank=True, max_length=100, null=True, validators=[eapp.models.validate_password_complexity]),
        ),
        migrations.AlterField(
            model_name='instructor',
            name='phone_number',
            field=models.CharField(max_length=15, validators=[eapp.models.validate_phone_number]),
        ),
        migrations.AlterField(
            model_name='instructor',
            name='rpc_number',
            field=models.CharField(max_length=50, validators=[eapp.models.validate_rpc_number]),
        ),
        migrations.AlterField(
            model_name='userbooking',
            name='address',
            field=models.TextField(validators=[django.core.validators.MinLengthValidator(10)]),
        ),
        migrations.AlterField(
            model_name='userbooking',
            name='drone_details',
            field=models.TextField(validators=[django.core.validators.MinLengthValidator(50)]),
        ),
        migrations.AlterField(
            model_name='userbooking',
            name='name',
            field=models.CharField(max_length=100, validators=[django.core.validators.MinLengthValidator(2)]),
        ),
        migrations.AlterField(
            model_name='userbooking',
            name='phone_number',
            field=models.CharField(max_length=15, validators=[eapp.models.validate_phone_number]),
        ),
    ]
