import datetime
import random
import string
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinLengthValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from jsonschema import ValidationError
from datetime import datetime, timedelta


from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MinLengthValidator
from django.utils.timezone import now
from django.core.mail import send_mail
from django.core.exceptions import ValidationError  # Changed from jsonschema import
import random
import string
from datetime import date, datetime, time
import re

class Address(models.Model):
    recepient_name = models.CharField(max_length=100, null=True)
    recepient_contact = models.CharField(max_length=12, null=True, validators=[MinLengthValidator(10)])
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.address_line1}, {self.address_line2}, {self.city}, {self.state} - {self.postal_code}"    

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    customer_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=12, blank=True, null=True, validators=[MinLengthValidator(10)])
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=50, default='customer')

    def __str__(self):
        return self.customer_name
   
    

class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_no = models.CharField(max_length=12, unique=True, validators=[MinLengthValidator(10)])
    address = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name

class Category(models.Model):
    category_name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.category_name

class Subcategory(models.Model):
    subcategory_name = models.CharField(max_length=100)
    parent_category = models.ForeignKey(Category, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.subcategory_name

class Product(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    cost = models.DecimalField(max_digits=6, decimal_places=2, default = 100)
    image_1 = models.ImageField(upload_to='product_images/')
    image_2 = models.ImageField(upload_to='product_images/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='product_images/', blank=True, null=True)
    image_4 = models.ImageField(upload_to='product_images/', blank=True, null=True)
    quantity_in_stock = models.PositiveIntegerField(default=0)
    sku = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
            # Check if the quantity has gone below the reorder level
        if self.quantity_in_stock < self.reorder_level:
            # Create a new PurchaseOrder
            purchase_order = PurchaseOrder.objects.create(
                TotalAmount=self.cost * self.sku,
                PurchaseOrderDate=timezone.now().date(),  # Using Django's timezone utility
                Status='Not Initiated',
                Seller=self.seller,
            )

            # Create a new PurchaseOrderItem
            PurchaseOrderItem.objects.create(
                Quantity=self.sku,
                Product=self,
                PurchaseOrder=purchase_order,
                PurchaseUnitPrice=self.cost,
            )

            # Send a message to the admin
            POMessage.objects.create(
                product=self,
                quantity=self.sku,
                purchase_order=purchase_order,
            )

        super().save(*args, **kwargs)
       
        





class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)

    def sub_total(self):
        return int(self.product.price) * int(self.quantity)

    def __str__(self):
        return f"Cart - Customer: {self.customer.customer_name} - Product: {self.product.name} - Qty: {self.quantity}"
    
    
class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped/Dispatched', 'Shipped/Dispatched'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Refunded', 'Refunded'),
        ('Returned', 'Returned'),
        ('On Hold', 'On Hold'),
        ('Backordered', 'Backordered'),
        ('Partially Shipped', 'Partially Shipped'),
        ('Awaiting Payment', 'Awaiting Payment'),
        ('Awaiting Fulfillment', 'Awaiting Fulfillment'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    order_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def total_price(self):
        return sum(item.total_price() for item in self.orderitem_set.all())

    def __str__(self):
        return f"Order - Customer: {self.customer.customer_name} - Status: {self.status}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def total_price(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"Order Item - Order: {self.order.id} - Product: {self.product.name} - Qty: {self.quantity}"


# Define the PurchaseOrder model
class PurchaseOrder(models.Model):
    TotalAmount = models.DecimalField(max_digits=20, decimal_places=2)
    PurchaseOrderDate = models.DateField()
    Status = models.CharField(max_length=250, blank=True)
    ExpectedDeliveryDate = models.DateField(blank=True, null=True)
    Seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    seller_message = models.TextField(blank=True)
    
    def __str__(self):
        return f"Purchase Order {self.id}"
    
from decimal import Decimal    

class PurchaseOrderItem(models.Model):
    Quantity = models.IntegerField()
    Product = models.ForeignKey(Product, on_delete=models.CASCADE)
    PurchaseOrder = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    PurchaseUnitPrice = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    TotalAmount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Calculate total amount before saving
        if self.Quantity is not None and self.PurchaseUnitPrice is not None:
            self.TotalAmount = Decimal(self.Quantity) * self.PurchaseUnitPrice
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Purchase Order Item {self.id}"
    


class POMessage(models.Model):
    purchase_order = models.OneToOneField(PurchaseOrder, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"Admin Message for {self.product.name} - Quantity: {self.quantity} - Purchase Order: {self.purchase_order.id}"

    def save(self, *args, **kwargs):
        # Calculate the total amount when the message is saved
        self.total_amount = self.quantity * self.product.cost
        super().save(*args, **kwargs)

    
    
@receiver(post_save, sender=POMessage)
def update_purchase_order_status(sender, instance, **kwargs):
    # If the admin confirms the message, update the status of the PurchaseOrder
    if instance.confirmed:
        instance.purchase_order.Status = 'Initiated'
        instance.purchase_order.TotalAmount = instance.quantity * instance.product.cost
        instance.purchase_order.save()

        # Update the quantity in the PurchaseOrderItem
        purchase_order_item = PurchaseOrderItem.objects.get(PurchaseOrder=instance.purchase_order, Product=instance.product)
        purchase_order_item.Quantity = instance.quantity
        purchase_order_item.TotalAmount = instance.quantity * instance.product.cost
        purchase_order_item.save()







from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MinLengthValidator
from django.utils.timezone import now
from django.core.mail import send_mail
import random
import string
from datetime import date, datetime, time
import re

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
    # Create time objects for comparison
    opening_time = time(9, 0)
    closing_time = time(17, 0)
    # Compare the time values directly
    if not (opening_time <= value <= closing_time):
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
    # password = models.CharField(max_length=100, null=True, blank=True, validators=[validate_password_complexity])

    class Meta:
        verbose_name = 'Instructor'
        verbose_name_plural = 'Instructors'

    def clean(self):
        errors = {}
        try:
            super().clean()
        except ValidationError as e:
            errors.update(e.message_dict)

        if self.issued_date and self.issued_date > date.today():
            errors['issued_date'] = ['Issued date cannot be in the future.']

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        try:
            self.full_clean()
        except ValidationError as e:
            # Convert validation errors to JSON-serializable format
            error_dict = {}
            for field, errors in e.message_dict.items():
                error_dict[field] = list(errors)
            raise ValidationError(error_dict)

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
        if booking_datetime < datetime.now() + timedelta(hours=1):
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
    
