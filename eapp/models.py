import datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinLengthValidator
from django.db.models.signals import post_save
from django.dispatch import receiver

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
                PurchaseOrderDate=datetime.date.today(),
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
from django.core.validators import RegexValidator








from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import path
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.utils.timezone import now
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

# Models
from django.db import models
from django.utils.timezone import now

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.timezone import now


from django.db import models
from django.core.exceptions import ValidationError
from django.utils.timezone import now


class Instructor(models.Model):
    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='instructors/')
    rpc_number = models.CharField(max_length=50)
    experience = models.TextField()
    issued_date = models.DateField()
    phone_number = models.CharField(max_length=15)

    def __str__(self):
        return self.name
from django.contrib.auth.models import User




class BookingSlot(models.Model):
    date = models.DateField()
    time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["date", "time"], name="unique_slot_per_datetime")
        ]

    def save(self, *args, **kwargs):
        # Ensure the admin cannot create duplicate slots for the same date and time
        if BookingSlot.objects.filter(date=self.date, time=self.time).exists() and not self.pk:
            raise ValidationError("A slot with this date and time already exists.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} {self.time} ({'Booked' if self.is_booked else 'Available'})"



class UserBooking(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.TextField()
    phone_number = models.CharField(max_length=15)
    drone_details = models.TextField()
    slot = models.OneToOneField(BookingSlot, on_delete=models.CASCADE)
    slot_date = models.DateField(editable=False)  # New field to store slot date
    created_at = models.DateTimeField(default=now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["email", "phone_number", "slot_date"],
                name="unique_booking_per_day_per_user",
            )
        ]

    def save(self, *args, **kwargs):
        if self.slot.is_booked:
            raise ValidationError("This slot is already booked.")
        super().save(*args, **kwargs)
        # Mark the slot as booked after saving
        self.slot.is_booked = True
        self.slot.save()

    def __str__(self):
        return f"Booking for {self.name} on {self.slot.date} {self.slot.time}"