from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinLengthValidator
from django.utils.timezone import now
from django.core.mail import send_mail
import random
import string
from datetime import date, datetime, time
import re
from django.db.models import F

def validate_phone_number(value):
    if not re.match(r'^\+?1?\d{9,15}$', value):
        raise ValidationError('Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.')

def validate_password_complexity(value):
    if len(value) < 8:
        raise ValidationError('Password must be at least 8 characters long.')
    if not any(char.isdigit() for char in value):
        raise ValidationError('Password must contain at least one digit.')
    if not any(char.isupper() for char in value):
        raise ValidationError('Password must contain at least one uppercase letter.')

def validate_rpc_number(value):
    if not re.match(r'^RPC-\d{6}$', value):
        raise ValidationError('RPC number must be in the format RPC-XXXXXX where X is a digit.')

def validate_future_date(value):
    if value < date.today():
        raise ValidationError('Date cannot be in the past.')

def validate_business_hours(value):
    if not (time(9, 0) <= value.time() <= time(17, 0)):
        raise ValidationError('Booking time must be between 9:00 AM and 5:00 PM.')

class Instructor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, validators=[MinLengthValidator(2)])
    photo = models.ImageField(upload_to='instructors/')
    rpc_number = models.CharField(max_length=50, validators=[validate_rpc_number])
    experience = models.TextField(validators=[MinLengthValidator(50)])
    issued_date = models.DateField()
    phone_number = models.CharField(max_length=15, validators=[validate_phone_number])
    email = models.EmailField(unique=True, null=True, blank=True)
    username = models.CharField(max_length=100, unique=True, null=True, blank=True)
    password = models.CharField(max_length=100, null=True, blank=True, validators=[validate_password_complexity])

    def clean(self):
        super().clean()
        if self.issued_date and self.issued_date > date.today():
            raise ValidationError({'issued_date': 'Issued date cannot be in the future.'})

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.full_clean()  # Run all validators
        if not self.pk:  # Only for new instances
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=12))
            
            if not self.email:
                self.email = f"{self.name.lower().replace(' ', '.')}@example.com"
            
            if not self.username:
                base_username = self.name.lower().replace(' ', '_')
                username = base_username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}_{counter}"
                    counter += 1
                self.username = username

            user = User.objects.create_user(
                username=self.username,
                email=self.email,
                password=temp_password
            )
            self.user = user
            self.password = temp_password
            
            try:
                send_mail(
                    'Your Instructor Account Credentials',
                    f'''Hello {self.name},
                    
                    Your instructor account has been created. Here are your login credentials:
                    Username: {self.username}
                    Password: {temp_password}
                    
                    Please change your password after first login.
                    ''',
                    'from@yourdomain.com',
                    [self.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Failed to send email: {e}")
        
        super().save(*args, **kwargs)

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    ar_model = models.FileField(upload_to='ar_models/', null=True, blank=True, help_text='3D model file for AR try-on')
    ar_thumbnail = models.ImageField(upload_to='ar_thumbnails/', null=True, blank=True)
    supports_ar = models.BooleanField(default=False)
    ar_instructions = models.TextField(blank=True, help_text='Instructions for using AR try-on')

    def __str__(self):
        return self.name

class ComparisonList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user'], name='unique_comparison_list_per_user')
        ]

    def __str__(self):
        return f"Comparison List - {self.user.username}"

class BookingSlot(models.Model):
    instructor = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    date = models.DateField(validators=[validate_future_date])
    time = models.TimeField(validators=[validate_business_hours])
    is_booked = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["date", "time"], name="unique_slot_per_datetime")
        ]

    def clean(self):
        super().clean()
        # Check if slot is at least 24 hours in advance
        booking_datetime = datetime.combine(self.date, self.time)
        if booking_datetime < datetime.now() + F Expression('INTERVAL 1 DAY'):
            raise ValidationError('Booking must be made at least 24 hours in advance.')

    def save(self, *args, **kwargs):
        self.full_clean()
        if BookingSlot.objects.filter(date=self.date, time=self.time).exists() and not self.pk:
            raise ValidationError("A slot with this date and time already exists.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} {self.time} ({'Booked' if self.is_booked else 'Available'})"

class UserBooking(models.Model):
    name = models.CharField(max_length=100, validators=[MinLengthValidator(2)])
    email = models.EmailField()
    address = models.TextField(validators=[MinLengthValidator(10)])
    phone_number = models.CharField(max_length=15, validators=[validate_phone_number])
    drone_details = models.TextField(validators=[MinLengthValidator(50)])
    slot = models.OneToOneField(BookingSlot, on_delete=models.CASCADE)
    slot_date = models.DateField(editable=False)
    created_at = models.DateTimeField(default=now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["email", "phone_number", "slot_date"],
                name="unique_booking_per_day_per_user",
            )
        ]

    def clean(self):
        super().clean()
        if self.slot.is_booked:
            raise ValidationError({'slot': 'This slot is already booked.'})
        
        # Check if user has exceeded daily booking limit
        today_bookings = UserBooking.objects.filter(
            email=self.email,
            slot_date=self.slot.date
        ).count()
        if today_bookings >= 2:  # Maximum 2 bookings per day
            raise ValidationError('Maximum booking limit per day exceeded.')

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.slot_date:
            self.slot_date = self.slot.date
        super().save(*args, **kwargs)
        self.slot.is_booked = True
        self.slot.save()
