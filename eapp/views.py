from datetime import date
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from .models import Customer
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, login
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib import messages
from .models import *
from .forms import AddressForm
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.views import View
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from django.core.paginator import Paginator
from django.contrib import messages
from django.shortcuts import redirect, render
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.db.models import Q
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.contrib import messages
def index(request):
    products = Product.objects.all()
    return render(request, 'index.html', {'products': products})


def customer_dashboard(request):
    return render(request, 'customer/customer_dashboard.html')



def register(request):
    if request.method == 'POST':
        full_name = request.POST.get('full-name')
        email = request.POST.get('your-email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')
        phone_number = request.POST.get('phone-number')

        # Check if passwords match
        if password != confirm_password:
            messages.error(request, 'Passwords Do Not Match!')
            return render(request, 'customer/register.html')

        # Check password strength using Django's built-in validators
        try:
            validate_password(password)
        except ValidationError as e:
            messages.error(request, ', '.join(e.messages))
            return render(request, 'customer/register.html')
        
                # Validate phone number
        if not phone_number.isnumeric() or len(phone_number) < 10 or len(phone_number) > 12:
            messages.error(request, 'Phone number must be between 10 and 12 digits and contain only numbers.')
            return render(request, 'customer/register.html')

        # Create user
        try:
            user = User.objects.create_user(username=email, email=email, password=password)
        except:
            messages.error(request, 'Email already exists!')
            return render(request, 'customer/register.html')

        # Create customer
        customer = Customer.objects.create(user=user, customer_name=full_name, email=email, contact_number=phone_number)
        
        # Authenticate and login user
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Your Account Has Been Registered Successfully!')
            return redirect('index')
        else:
            messages.error(request, 'Failed to login user.')
            return render(request, 'customer/register.html')

    return render(request, 'customer/register.html')



# def login_view(request):
#     if request.method == 'POST':
#         email = request.POST.get('email')
#         password = request.POST.get('password')
        
#         user = authenticate(request, username=email, password=password)
        
#         if user is not None:
#             login(request, user)
#             messages.success(request, 'You have successfully logged in!')
            
#             # Redirect based on user role
#             try:
#                 customer = user.customer
#                 return redirect('index')  # Redirect customer to index page
#             except Customer.DoesNotExist:
#                 try:
#                     seller = user.seller
#                     return redirect('seller_purchase_orders')  # Redirect seller to seller dashboard
#                 except Seller.DoesNotExist:
#                     messages.error(request, 'You are not authorized to access this page.')
#                     return redirect('login')  # Redirect to login page if no associated role found

#         else:
#             messages.error(request, 'Invalid email or password. Please try again.')
#             return render(request, 'customer/login.html')  # Change 'login.html' to your login template path
#     return render(request, 'customer/login.html')  # Change 'login.html' to your login template path



def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'You have successfully logged in!')
            
            # Redirect based on user role
            try:
                customer = user.customer
                return redirect('index')
            except Customer.DoesNotExist:
                try:
                    seller = user.seller
                    return redirect('seller_purchase_orders')
                except Seller.DoesNotExist:
                    try:
                        instructor = user.instructor
                        return redirect('instructor_dashboard')  # New redirect for instructors
                    except Instructor.DoesNotExist:
                        messages.error(request, 'You are not authorized to access this page.')
                        return redirect('login')

        else:
            messages.error(request, 'Invalid email or password. Please try again.')
            return render(request, 'customer/login.html')
    return render(request, 'customer/login.html')

def user_logout(request):
    logout(request)
    return redirect('index') 


@login_required
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        user = request.user  # Assuming the user is already logged in

        if user.check_password(old_password):
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password changed successfully.")
                return redirect('login')
            else:
                messages.error(request, "New passwords do not match.")
        else:
            messages.error(request, "Old password is incorrect.")

    return render(request, 'customer/change_password.html')


class CustomTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            str(user.pk) + user.password + str(timestamp)
        )



def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = CustomTokenGenerator().make_token(user)
            reset_password_url = request.build_absolute_uri('/reset_password/{}/{}/'.format(uid, token))
            email_subject = 'Reset Your Password'

            # Render both HTML and plain text versions of the email
            email_body_html = render_to_string('customer/reset_password_email.html', {
                'reset_password_url': reset_password_url,
                'user': user,
            })
            email_body_text = "Click the following link to reset your password: {}".format(reset_password_url)

            # Create an EmailMultiAlternatives object to send both HTML and plain text versions
            email = EmailMultiAlternatives(
                email_subject,
                email_body_text,
                settings.EMAIL_HOST_USER,
                [email],
            )
            email.attach_alternative(email_body_html, 'text/html')  # Attach HTML version
            email.send(fail_silently=False)

            messages.success(request, 'An email has been sent to your email address with instructions on how to reset your password.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, "User with this email does not exist.")
    return render(request, 'customer/forgot_password.html')


def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and CustomTokenGenerator().check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password reset successfully. You can now login with your new password.")
                return redirect('login')
            else:
                messages.error(request, "Passwords do not match.")
        return render(request, 'customer/reset_password.html')
    else:
        messages.error(request, "Invalid reset link. Please try again or request a new reset link.")
        return redirect('login')


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Customer

@login_required
def edit_customer(request):
    # Retrieve the current logged-in user
    current_user = request.user
    # Check if the current user has a corresponding Customer instance
    try:
        customer = Customer.objects.get(user=current_user)
    except Customer.DoesNotExist:
        # Handle the case where the logged-in user does not have a corresponding Customer instance
        return HttpResponse("You are not associated with any customer profile.")

    if request.method == 'POST':
        # Update customer details with the data from the form
        customer.customer_name = request.POST['full-name']
        customer.email = request.POST['your-email']
        customer.contact_number = request.POST['phone-number']
        customer.save()

        # Update associated user's email
        current_user.email = request.POST['your-email']
        current_user.username = request.POST['your-email']
        current_user.save()

        # Redirect to the customer detail page after editing
        return redirect('index')

    # If it's a GET request, display the edit form with existing customer details
    return render(request, 'customer/edit_customer.html', {'customer': customer})


    

@login_required
def address_list(request):
    addresses = Address.objects.filter(customer=request.user.customer)
    return render(request, 'customer/address_list.html', {'addresses': addresses})

@login_required
def address_create(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.customer = request.user.customer
            address.save()
            return redirect('address_list')
    else:
        form = AddressForm()
    return render(request, 'customer/address_form.html', {'form': form})

@login_required
def address_edit(request, pk):
    address = get_object_or_404(Address, pk=pk, customer=request.user.customer)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            return redirect('address_list')
    else:
        form = AddressForm(instance=address)
    return render(request, 'customer/address_form.html', {'form': form})

@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, customer=request.user.customer)
    if request.method == 'POST':
        address.delete()
        return redirect('address_list')
    return render(request, 'customer/address_confirm_delete.html', {'address': address})

def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    return render(request, 'product-details.html', {'product': product})

@login_required
def cart(request):
    customer = request.user.customer
    cart_items = Cart.objects.filter(customer=customer)
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'cart.html', context)

@login_required
def add_to_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = request.POST.get('quantity')
        if product_id and quantity:
            try:
                product = Product.objects.get(pk=product_id)
                customer = request.user.customer
                cart_item, created = Cart.objects.get_or_create(customer=customer, product=product)
                cart_item.quantity += int(quantity)
                if cart_item.quantity <= product.quantity_in_stock:
                    cart_item.save()
                    messages.success(request, f'{quantity} item(s) added to cart.')
                else:
                    messages.error(request, 'Requested quantity exceeds available stock.')
            except Product.DoesNotExist:
                messages.error(request, 'Product does not exist.')
        else:
            messages.error(request, 'Invalid request.')
    return redirect('cart')

@login_required
def delete_item_in_cart(request, id):
    customer = request.user.customer
    product = get_object_or_404(Product, id=id)
    cart_item = Cart.objects.get(customer=customer, product=product)
    cart_item.delete()
    return redirect('cart')


@login_required
def increase_quantity(request, cart_item_id):
    cart_item = Cart.objects.get(pk=cart_item_id)
    if cart_item.quantity < cart_item.product.quantity_in_stock:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('cart')

@login_required
def decrease_quantity(request, cart_item_id):
    cart_item = Cart.objects.get(pk=cart_item_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')


@login_required
def checkout(request):
    customer = request.user.customer
    cart_items = Cart.objects.filter(customer=customer)
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    
    if total_price == 0:
        return redirect('order_list')  # Redirect to order details with a placeholder order id
    
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        if not address_id:
            messages.error(request, "Please select or add an address to checkout.")
            return redirect('checkout')
        address = Address.objects.get(id=address_id)
        order = Order.objects.create(customer=customer, address=address)
        for item in cart_items:
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)
            # Reduce the quantity of the product in stock
            item.product.quantity_in_stock -= item.quantity
            item.product.save()
            item.delete()
        
        # Send confirmation email to customer
        email_subject = 'Order Confirmation'
        email_body_html = render_to_string('order_confirmation_email.html', {'order': order})
        email_body_text = "Thank you for your order. Your order ID is {}. We will process it shortly.".format(order.id)
        email = EmailMultiAlternatives(
            email_subject,
            email_body_text,
            settings.EMAIL_HOST_USER,
            [customer.email],
        )
        email.attach_alternative(email_body_html, 'text/html')
        email.send()
        
        # Generate PDF bill
        pdf_template = get_template('bill_template.html')
        html = pdf_template.render({'order': order})
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'filename="bill.pdf"'
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response
        
        return redirect('order_detail', order.id)
    else:
        addresses = Address.objects.filter(customer=customer)
        context = {
            'cart_items': cart_items,
            'total_price': total_price,
            'addresses': addresses,
        }
        return render(request, 'checkouts.html', context)


@login_required
def order_list(request):
    customer = request.user.customer
    orders = Order.objects.filter(customer=customer).order_by('-order_date', '-id')
    context = {
        'orders': orders,
    }
    return render(request, 'order_list.html', context)

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if order.customer != request.user.customer:
        return HttpResponseNotFound("Order not found.")
    context = {
        'order': order,
    }
    return render(request, 'order_detail.html', context)


def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.prefetch_related('subcategory_set').all()
    
    # Filter products by price if price parameters are provided
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    
    if min_price and max_price:
        products = products.filter(price__gte=min_price, price__lte=max_price)
    elif min_price:
        products = products.filter(price__gte=min_price)
    elif max_price:
        products = products.filter(price__lte=max_price)
    
    return render(request, 'product_list.html', {'products': products, 'categories': categories})



def search_results(request):
    query = request.GET.get('q')
    products = Product.objects.filter(name__icontains=query) | \
               Product.objects.filter(subcategory__subcategory_name__icontains=query) | \
               Product.objects.filter(subcategory__parent_category__category_name__icontains=query)
    return render(request, 'search_results.html', {'products': products, 'query': query})

def category_products(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    products = Product.objects.filter(subcategory__parent_category=category)
    return render(request, 'category_products.html', {'category': category, 'products': products})

def subcategory_products(request, subcategory_id):
    subcategory = get_object_or_404(Subcategory, pk=subcategory_id)
    products = Product.objects.filter(subcategory=subcategory)
    return render(request, 'subcategory_products.html', {'subcategory': subcategory, 'products': products})




class CreatePurchaseOrderView(View):
    def get(self, request):
        sellers = Seller.objects.all()
        products = Product.objects.none()  # Initially empty

        if 'seller' in request.GET:
            seller_id = request.GET.get('seller')
            if seller_id:
                products = Product.objects.filter(seller_id=seller_id)
        
        context = {
            'sellers': sellers,
            'products': products,
        }
        return render(request, 'create_purchase_order.html', context)
    
    def post(self, request):
        seller_id = request.POST.get('seller')
        total_amount = request.POST.get('total_amount')

        # Get the selected seller
        selected_seller = Seller.objects.get(id=seller_id)

        # Create the PurchaseOrder object with the selected seller
        purchase_order = PurchaseOrder.objects.create(
            TotalAmount=total_amount,
            PurchaseOrderDate=date.today(),
            Seller=selected_seller,  # Assign the Seller object, not just the ID
        )

        # Save purchase order items
        for i in range(len(request.POST.getlist('product'))):
            product_id = request.POST.getlist('product')[i]
            product = Product.objects.get(id=product_id)
            quantity = request.POST.getlist('quantity')[i]
            purchase_unit_price = Product.objects.get(id=product_id).cost
            
            PurchaseOrderItem.objects.create(
                Product=product,
                Quantity=quantity,
                PurchaseUnitPrice=purchase_unit_price,
                PurchaseOrder=purchase_order,
            )

        return redirect('/admin/eapp/purchaseorder/')  # Redirect to a success page
    
@login_required    
def seller_purchase_orders(request):
    # Assuming you have a way to identify the current seller, e.g., request.user.seller
    seller = request.user.seller
    username = seller.name
    purchase_orders = PurchaseOrder.objects.filter(Seller=seller)
    return render(request, 'seller_purchase_orders.html', {'purchase_orders': purchase_orders, 'username': username})

@login_required
def seller_purchase_orders_history(request):
    # Assuming you have a way to identify the current seller, e.g., request.user.seller
    seller = request.user.seller
    username = seller.name
    purchase_orders = PurchaseOrder.objects.filter(Seller=seller)
    return render(request, 'history.html', {'purchase_orders': purchase_orders, 'username': username})

from django.db import transaction

@login_required
@transaction.atomic
def purchase_order_details(request, purchase_order_id):
    purchase_order = get_object_or_404(PurchaseOrder, id=purchase_order_id)
    order_items = PurchaseOrderItem.objects.filter(PurchaseOrder=purchase_order)
    
    if request.method == 'POST':
        # Handle form submission to update delivery date and status
        delivery_date = request.POST.get('delivery_date')
        status = request.POST.get('status')
        
        # Check if the delivery date is provided
        if not delivery_date:
            messages.error(request, "Expected delivery date is required.")
            return render(request, 'purchase_order_details.html', {
                'purchase_order': purchase_order,
                'order_items': order_items,
            })
        
        # Update purchase order with new delivery date and status
        purchase_order.ExpectedDeliveryDate = delivery_date
        purchase_order.Status = status
        purchase_order.save()

        # Update product quantity if status is "Delivered"
        if status == 'Delivered':
            for item in order_items:
                item.Product.quantity_in_stock += item.Quantity
                item.Product.save()
        
        return redirect('seller_purchase_orders')

    return render(request, 'purchase_order_details.html', {'purchase_order': purchase_order, 'order_items': order_items})

@login_required
def reject_purchase_order(request, purchase_order_id):
    if request.method == 'GET':
        seller_message = request.GET.get('seller_message', '')  # Get seller message from the query parameters
        purchase_order = get_object_or_404(PurchaseOrder, id=purchase_order_id)  # Get the purchase order object

        # Update purchase order status and seller message
        purchase_order.Status = 'Rejected'
        purchase_order.seller_message = seller_message
        purchase_order.save()

        return redirect('seller_purchase_orders')  # Redirect to seller purchase orders page
    
from django.core.mail import send_mail

def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        # Update order status to 'Cancelled'
        order.status = 'Cancelled'
        order.save()
        
        # Increase the product quantity back in stock
        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            product = item.product
            product.quantity_in_stock += item.quantity
            product.save()
        
        # Send confirmation email
        send_mail(
            'Order Cancelled',
            f'Your order #{order_id} has been cancelled.',
            settings.DEFAULT_FROM_EMAIL,
            [order.customer.email]
        )
        
        messages.success(request, 'Order cancelled successfully.')
        return redirect('order_detail', order_id=order.id)
    
 


























from django.shortcuts import render
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from .models import Instructor, BookingSlot, UserBooking

@login_required
def instructor_details(request):
    instructor = Instructor.objects.first()
    return render(request, 'instructor_details.html', {'instructor': instructor})

# def slot_booking(request):
#     if request.method == 'POST':
#         name = request.POST['name']
#         email = request.POST['email']
#         address = request.POST['address']
#         phone_number = request.POST['phone_number']
#         drone_details = request.POST['drone_details']
#         date = request.POST['date']
#         time = request.POST['time']

#         # Find the specific slot
#         slot = BookingSlot.objects.filter(date=date, time=time, is_booked=False).first()
#         if not slot:
#             return HttpResponse('The selected slot is already booked or unavailable.')

#         # Create booking and mark slot as booked
#         booking = UserBooking.objects.create(
#             name=name, email=email, address=address,
#             phone_number=phone_number, drone_details=drone_details, slot=slot
#         )
#         slot.is_booked = True
#         slot.save()

#         send_mail(
#             'Booking Confirmation',
#             f'Thank you for booking! Your slot on {slot.date} at {slot.time} is confirmed.',
#             'noreply@example.com',
#             [email]
#         )
#         # return redirect('payment_page')
#         return redirect('payment', booking_id=booking.id)


#     slots = BookingSlot.objects.filter(is_booked=False)
#     return render(request, 'slot_booking.html', {'slots': slots})




from django.http import JsonResponse

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.mail import send_mail
from .models import BookingSlot, UserBooking

def slot_booking(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        address = request.POST['address']
        phone_number = request.POST['phone_number']
        drone_details = request.POST['drone_details']
        date = request.POST['date']
        time = request.POST['time']

        # Check if the user has already booked a slot on the selected date
        existing_booking = UserBooking.objects.filter(
            email=email,
            phone_number=phone_number,
            slot__date=date
        ).first()
        if existing_booking:
            return HttpResponse('You can only book one slot per day.', status=400)

        # Find the specific slot
        slot = BookingSlot.objects.filter(date=date, time=time, is_booked=False).first()
        if not slot:
            return HttpResponse('The selected slot is already booked or unavailable.', status=400)

        # Create a booking and set the slot_date field to the slot's date
        booking = UserBooking.objects.create(
            name=name, email=email, address=address,
            phone_number=phone_number, drone_details=drone_details, slot=slot,
            slot_date=slot.date  # Ensure the slot_date is set
        )

        # Redirect to the payment page with the booking ID
        return redirect('payment', booking_id=booking.id)

    slots = BookingSlot.objects.all()
    return render(request, 'slot_booking.html', {'slots': slots})




from django.shortcuts import get_object_or_404

def payment_page(request, booking_id):
    booking = get_object_or_404(UserBooking, id=booking_id)

    if request.method == 'POST':
        # Simulate payment success
        booking.slot.is_booked = True
        booking.slot.save()

        send_mail(
            'Booking Confirmation',
            f'Thank you for your payment! Your slot on {booking.slot.date} at {booking.slot.time} is confirmed.',
            'noreply@example.com',
            [booking.email]
        )
        return HttpResponse('''
       <html>
    <head>
        <style>
            /* Reset and Universal Styles */
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Poppins', Arial, sans-serif;
                background: linear-gradient(135deg, #e0f7fa, #c8e6c9);
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                color: #333;
            }

            .container {
                background: #ffffff;
                padding: 50px 40px;
                border-radius: 15px;
                box-shadow: 0 15px 30px rgba(0, 0, 0, 0.15);
                text-align: center;
                max-width: 450px;
                width: 90%;
                animation: fadeIn 1s ease-in-out;
                border: 1px solid rgba(0, 0, 0, 0.05);
            }

            h1 {
                font-size: 2.8rem;
                color: #2ecc71;
                margin-bottom: 20px;
                font-weight: 700;
                text-shadow: 1px 2px 3px rgba(46, 204, 113, 0.5);
            }

            p {
                font-size: 1.2rem;
                color: #555;
                line-height: 1.6;
                margin-top: 15px;
                font-weight: 400;
            }

            .button {
                display: inline-block;
                margin-top: 20px;
                padding: 12px 25px;
                font-size: 1rem;
                font-weight: 600;
                color: #fff;
                background: linear-gradient(135deg, #4caf50, #388e3c);
                border: none;
                border-radius: 25px;
                cursor: pointer;
                box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
                text-decoration: none;
                transition: all 0.3s ease;
            }

            .button:hover {
                background: linear-gradient(135deg, #66bb6a, #43a047);
                box-shadow: 0 12px 20px rgba(0, 0, 0, 0.2);
                transform: translateY(-3px);
            }

            /* Fade-in Animation */
            @keyframes fadeIn {
                from {
                    opacity: 0;
                    transform: translateY(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            /* Responsive Design */
            @media (max-width: 600px) {
                h1 {
                    font-size: 2.2rem;
                }

                p {
                    font-size: 1rem;
                }

                .button {
                    font-size: 0.9rem;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Payment Successful!</h1>
            <p>Your slot is confirmed. Thank you for choosing our service!</p>
            <a href="/" class="button">Back to Home</a>
        </div>
    </body>
</html>


    ''')

    return render(request, 'payment_page.html', {'booking': booking})


@login_required
def view_bookings(request):
    bookings = UserBooking.objects.select_related('slot').all()
    return render(request, 'view_bookings.html', {'bookings': bookings})



from django.http import JsonResponse
from .models import BookingSlot

def available_times(request):
    date = request.GET.get('date')
    if not date:
        return JsonResponse({'error': 'Date is required'}, status=400)

    # Get available times for the selected date
    available_slots = BookingSlot.objects.filter(date=date, is_booked=False)
    booked_slots = BookingSlot.objects.filter(date=date, is_booked=True)

    available_times = [slot.time.strftime('%H:%M') for slot in available_slots]
    booked_times = [slot.time.strftime('%H:%M') for slot in booked_slots]

    return JsonResponse({'times': available_times, 'bookedSlots': booked_times})



def confirm_payment(request):
    # Your function logic here
    pass



def get_booked_slots(request):
    date = request.GET.get('date')
    if not date:
        return JsonResponse({'error': 'Date is required'}, status=400)

    slots = BookingSlot.objects.filter(date=date)
    data = [
        {'time': slot.time.strftime('%H:%M'), 'is_booked': slot.is_booked}
        for slot in slots
    ]
    return JsonResponse({'slots': data})








from django.shortcuts import render
from django.http import JsonResponse
import google.generativeai as genai
import re

# Configure API key
api_key = "AIzaSyBvgdIgptWKRrICvcbmp5uSfmxDN974rkQ"
genai.configure(api_key=api_key)

# Initialize the model
model = genai.GenerativeModel('gemini-1.5-flash')

def clean_response(text):
    """
    Cleans the AI response by:
    - Removing timestamps, sender names, and asterisks.
    - Preserving line breaks and adding spacing.
    """
    # Remove timestamps (e.g., "9:52:07 PM")
    text = re.sub(r"\d{1,2}:\d{2}:\d{2} [APap][Mm]", "", text)

    # Remove role identifiers like "You", "AI Assistant", etc.
    text = re.sub(r"^(AI|You|User|Assistant)\s*[\n]?", "", text, flags=re.MULTILINE)

    # Remove asterisks (*) but replace them with proper bullet points
    text = text.replace("*", "-")  

    # Add space after punctuation if missing
    text = re.sub(r"(?<=[.,!?])(?=[^\s])", " ", text)

    # Remove excessive newlines and spaces
    text = re.sub(r"\n{2,}", "\n\n", text)  # Preserve paragraph breaks
    text = text.strip()

    return text

def generate_text(request):
    if request.method == 'POST':
        user_input = request.POST.get('input_text', '')
        if user_input:
            try:
                # Generate response from the model
                response = model.generate_content(user_input)
                
                # Extract text properly
                if hasattr(response, 'text') and response.text:
                    generated_text = clean_response(response.text)
                elif hasattr(response, 'candidates'):
                    generated_text = "\n\n".join(
                        clean_response(part.text) for part in response.candidates[0].content.parts if hasattr(part, 'text')
                    )
                else:
                    generated_text = "No structured response found."

                # Return formatted response
                return JsonResponse({'generated_text': generated_text})

            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        else:
            return JsonResponse({'error': 'No input text provided'}, status=400)
    
    return render(request, 'generate_text.html')



















from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import BookingSlot, UserBooking
from django.contrib import messages

@login_required
def instructor_dashboard(request):
    # Ensure the user is an instructor
    if not hasattr(request.user, 'instructor'):
        return redirect('/')  # Redirect if not an instructor

    instructor = request.user.instructor

    # Fetch all bookings and slots
    bookings = UserBooking.objects.select_related('slot').filter(slot__date__gte='today')
    slots = BookingSlot.objects.filter(is_booked=False).order_by('date', 'time')

    if request.method == 'POST':
        # Add a new slot
        date = request.POST['date']
        time = request.POST['time']

        # Ensure no duplicate slots
        if BookingSlot.objects.filter(date=date, time=time).exists():
            messages.error(request, 'A slot with this date and time already exists.')
        else:
            BookingSlot.objects.create(date=date, time=time)
            messages.success(request, 'Slot added successfully!')

    return render(request, 'instructor_dashboard.html', {
        'instructor': instructor,
        'bookings': bookings,
        'slots': slots
    })






# from django.shortcuts import render, redirect
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from .models import UserBooking, BookingSlot, Instructor
# from django.utils import timezone
# from datetime import datetime
# from django.core.exceptions import ValidationError

# @login_required
# def instructor_dashboard(request):
#     bookings = UserBooking.objects.all().order_by('-created_at')
#     slots = BookingSlot.objects.all().order_by('date', 'time')
#     instructors = Instructor.objects.all()
    
#     if request.method == 'POST':
#         try:
#             date_str = request.POST.get('date')
#             time_str = request.POST.get('time')
#             instructor_id = request.POST.get('instructor')
            
#             # Convert string date to date object
#             date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
#             # Convert string time to time object
#             time_obj = datetime.strptime(time_str, '%H:%M').time()
            
#             # Get instructor
#             instructor = Instructor.objects.get(id=instructor_id)
            
#             # Check if the slot already exists
#             if BookingSlot.objects.filter(date=date_obj, time=time_obj, instructor=instructor).exists():
#                 messages.error(request, 'A slot with this date and time already exists for this instructor.')
#                 return redirect('instructor_dashboard')
            
#             # Create new booking slot
#             slot = BookingSlot(
#                 instructor=instructor,
#                 date=date_obj,
#                 time=time_obj,
#                 is_booked=False
#             )
#             slot.full_clean()  # Validate the model
#             slot.save()
            
#             messages.success(request, 'Slot added successfully!')
#             return redirect('instructor_dashboard')
            
#         except Instructor.DoesNotExist:
#             messages.error(request, "Please select a valid instructor.")
#         except ValidationError as e:
#             messages.error(request, f"Validation error: {str(e)}")
#         except Exception as e:
#             print(f"Error creating slot: {str(e)}")  # For debugging
#             messages.error(request, f"Error creating slot: {str(e)}")
    
#     context = {
#         'bookings': bookings,
#         'slots': slots,
#         'instructors': instructors,
#         'today': timezone.now().date(),
#     }
#     return render(request, 'instructor/dashboard.html', context)



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserBooking, BookingSlot, Instructor
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.db.models import Count
from django.core.paginator import Paginator

@login_required
# def instructor_dashboard(request):
#     # Get filter parameters
#     date_filter = request.GET.get('date')
#     status_filter = request.GET.get('status')
#     instructor_filter = request.GET.get('instructor_filter')
#     search_query = request.GET.get('search')

#     # Base querysets
#     bookings = UserBooking.objects.all().order_by('-created_at')
#     slots = BookingSlot.objects.all().order_by('date', 'time')
#     instructors = Instructor.objects.all()

#     # Apply filters
#     if date_filter:
#         bookings = bookings.filter(slot__date=date_filter)
#         slots = slots.filter(date=date_filter)
    
#     if status_filter:
#         slots = slots.filter(is_booked=(status_filter == 'booked'))
    
#     if instructor_filter:
#         slots = slots.filter(instructor_id=instructor_filter)
    
#     if search_query:
#         bookings = bookings.filter(
#             name__icontains=search_query) | bookings.filter(
#             email__icontains=search_query) | bookings.filter(
#             phone_number__icontains=search_query)

#     # Statistics
#     total_bookings = bookings.count()
#     available_slots = slots.filter(is_booked=False).count()
#     today_bookings = bookings.filter(slot__date=timezone.now().date()).count()
    
#     # Pagination
#     page = request.GET.get('page', 1)
#     bookings_paginator = Paginator(bookings, 10)
#     bookings_page = bookings_paginator.get_page(page)

#     if request.method == 'POST':
#         action = request.POST.get('action')
        
#         if action == 'add_slot':
#             try:
#                 date_str = request.POST.get('date')
#                 time_str = request.POST.get('time')
#                 instructor_id = request.POST.get('instructor')
              
                
#                 date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
#                 time_obj = datetime.strptime(time_str, '%H:%M').time()
#                 instructor = Instructor.objects.get(id=instructor_id)
                
#                 slot = BookingSlot(
#                     instructor=instructor,
#                     date=date_obj,
#                     time=time_obj,
#                     is_booked=False,
                    
#                 )
#                 slot.full_clean()
#                 slot.save()
#                 messages.success(request, 'Slot added successfully!')
                
#             except Exception as e:
#                 messages.error(request, f"Error creating slot: {str(e)}")
        
#         elif action == 'delete_slot':
#             slot_id = request.POST.get('slot_id')
#             try:
#                 slot = BookingSlot.objects.get(id=slot_id)
#                 slot.delete()
#                 messages.success(request, 'Slot deleted successfully!')
#             except Exception as e:
#                 messages.error(request, f"Error deleting slot: {str(e)}")
        
#         elif action == 'cancel_booking':
#             booking_id = request.POST.get('booking_id')
#             try:
#                 booking = UserBooking.objects.get(id=booking_id)
#                 booking.slot.is_booked = False
#                 booking.slot.save()
#                 booking.delete()
#                 messages.success(request, 'Booking cancelled successfully!')
#             except Exception as e:
#                 messages.error(request, f"Error cancelling booking: {str(e)}")
        
#         return redirect('instructor_dashboard')

#     context = {
#         'bookings': bookings_page,
#         'slots': slots,
#         'instructors': instructors,
#         'today': timezone.now().date(),
#         'total_bookings': total_bookings,
#         'available_slots': available_slots,
#         'today_bookings': today_bookings,
#         'selected_date': date_filter,
#         'selected_status': status_filter,
#         'selected_instructor': instructor_filter,
#         'search_query': search_query,
#     }
#     return render(request, 'instructor/dashboard.html', context)

# views.py





def instructor_dashboard(request):
    delete_expired_slots()
    # Check if user is an instructor
    if not hasattr(request.user, 'instructor'):
        messages.error(request, 'You are not authorized to access this page.')
        return redirect('login')

    # Get the logged-in instructor
    instructor = request.user.instructor
    instructor_filter = request.GET.get('instructor_filter')
    # Get filter parameters
    date_filter = request.GET.get('date')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')
    # Get current date and time for filtering
    current_date = timezone.now().date()
    current_time = timezone.now().time()
    # Base querysets - filtered for the logged-in instructor only
    slots = BookingSlot.objects.filter(instructor=instructor).order_by('date', 'time')
    bookings = UserBooking.objects.filter(slot__instructor=instructor).order_by('-created_at')

    # Apply filters
    if date_filter:
        bookings = bookings.filter(slot__date=date_filter)
        slots = slots.filter(date=date_filter)
    
    if status_filter:
        slots = slots.filter(is_booked=(status_filter == 'booked'))
    
    if search_query:
        bookings = bookings.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )

    if instructor_filter:
           slots = slots.filter(instructor_id=instructor_filter)
    

    # Statistics for the logged-in instructor
    total_bookings = bookings.count()
    available_slots = slots.filter(is_booked=False).count()
    today_bookings = bookings.filter(slot__date=timezone.now().date()).count()
    
    # Pagination
    page = request.GET.get('page', 1)
    bookings_paginator = Paginator(bookings, 10)
    bookings_page = bookings_paginator.get_page(page)

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_slot':
            try:
                date_str = request.POST.get('date')
                time_str = request.POST.get('time')
                instructor_id = request.POST.get('instructor')
                
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                time_obj = datetime.strptime(time_str, '%H:%M').time()
                instructor = Instructor.objects.get(id=instructor_id)
                
                slot = BookingSlot(
                    instructor=instructor,  # Use logged-in instructor
                    date=date_obj,
                    time=time_obj,
                    is_booked=False
                )
                slot.full_clean()
                slot.save()
                messages.success(request, 'Slot added successfully!')
                
            except Exception as e:
                messages.error(request, f"Error creating slot: {str(e)}")
        
        elif action == 'delete_slot':
            slot_id = request.POST.get('slot_id')
            try:
                # Ensure instructor can only delete their own slots
                slot = BookingSlot.objects.get(id=slot_id, instructor=instructor)
                slot.delete()
                messages.success(request, 'Slot deleted successfully!')
            except BookingSlot.DoesNotExist:
                messages.error(request, "You can only delete your own slots.")
            except Exception as e:
                messages.error(request, f"Error deleting slot: {str(e)}")
        
        # In your views.py file


        elif action == 'cancel_booking':
            booking_id = request.POST.get('booking_id')
            try:
                booking = UserBooking.objects.get(
                    id=booking_id,
                    slot__instructor=instructor
                )
                
                # Store booking details
                student_email = booking.email
                booking_date = booking.slot.date.strftime('%B %d, %Y')  # Format: March 6, 2025
                booking_time = booking.slot.time.strftime('%I:%M %p')   # Format: 09:30 AM
                student_name = booking.name
                
                # Cancel the booking
                booking.slot.is_booked = False
                booking.slot.save()
                booking.delete()
                
                # HTML Email Template
                html_message = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Booking Cancellation</title>
                    <style>
                        body {{
                            font-family: 'Arial', sans-serif;
                            line-height: 1.6;
                            color: #333333;
                            margin: 0;
                            padding: 0;
                        }}
                        .email-container {{
                            max-width: 600px;
                            margin: 0 auto;
                            padding: 20px;
                        }}
                        .header {{
                            background-color: #f8f9fa;
                            padding: 20px;
                            text-align: center;
                            border-radius: 5px 5px 0 0;
                        }}
                        .content {{
                            background-color: #ffffff;
                            padding: 30px;
                            border-radius: 0 0 5px 5px;
                            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                        }}
                        .booking-details {{
                            background-color: #f8f9fa;
                            padding: 15px;
                            margin: 20px 0;
                            border-radius: 5px;
                        }}
                        .important-note {{
                            background-color: #fff3cd;
                            color: #856404;
                            padding: 15px;
                            margin: 20px 0;
                            border-radius: 5px;
                        }}
                        .footer {{
                            text-align: center;
                            margin-top: 20px;
                            padding-top: 20px;
                            border-top: 1px solid #eeeeee;
                            color: #666666;
                        }}
                        .btn {{
                            display: inline-block;
                            padding: 10px 20px;
                            background-color: #007bff;
                            color: #ffffff;
                            text-decoration: none;
                            border-radius: 5px;
                            margin-top: 15px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="email-container">
                        <div class="header">
                            <h2 style="color: #dc3545; margin: 0;">Booking Cancellation Notice</h2>
                        </div>
                        
                        <div class="content">
                            <p>Dear {student_name},</p>
                            
                            <p>We regret to inform you that your booking has been cancelled due to unavoidable circumstances.</p>
                            
                            <div class="booking-details">
                                <h3 style="margin-top: 0;">Booking Details:</h3>
                                <p><strong>Date:</strong> {booking_date}</p>
                                <p><strong>Time:</strong> {booking_time}</p>
                            </div>
                            
                            <div class="important-note">
                                <p><strong>Important:</strong> Your payment will be automatically refunded within 3 business days.</p>
                            </div>
                            
                            <p>We understand this may cause inconvenience and we sincerely apologize. You can book another available slot using the button below.</p>
                            
                            <div style="text-align: center;">
                                <a href="{settings.SITE_URL}/booking" class="btn">Book New Slot</a>
                            </div>
                            
                            <div class="footer">
                                <p>If you have any questions or concerns, please don't hesitate to contact our support team.</p>
                                <p style="margin-bottom: 0;">Best regards,<br>The Booking Team</p>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                # Plain text version of the email for clients that don't support HTML
                plain_message = strip_tags(html_message)
                
                try:
                    send_mail(
                        subject='Your Booking Has Been Cancelled',
                        message=plain_message,
                        html_message=html_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[student_email],
                        fail_silently=False,
                    )
                except Exception as email_error:
                    messages.warning(request, f'Booking cancelled but failed to send email notification: {str(email_error)}')
                else:
                    messages.success(request, 'Booking cancelled successfully and notification email sent!')
            except UserBooking.DoesNotExist:
                messages.error(request, "You can only cancel bookings for your slots.")
            except Exception as e:
                messages.error(request, f"Error cancelling booking: {str(e)}")
        
        return redirect('instructor_dashboard')

    # Get all instructors
    # instructors = Instructor.objects.all()
    instructors = Instructor.objects.filter(id=instructor.id)

    context = {
        'bookings': bookings_page,
        'slots': slots,
        'instructor': instructor,
        'instructors': instructors,  # Add this line
        'today': timezone.now().date(),
        'total_bookings': total_bookings,
        'available_slots': available_slots,
        'today_bookings': today_bookings,
        'selected_date': date_filter,
        'selected_status': status_filter,
        'search_query': search_query,
}
    return render(request, 'instructor/dashboard.html', context)



@login_required
def export_bookings(request):
    import csv
    from django.http import HttpResponse
    from django.utils import timezone
    
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="bookings.csv"'},
    )
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Time', 'Student Name', 'Email', 'Phone', 'Drone Details', 'Status', 'Instructor'])
    
    bookings = UserBooking.objects.all().order_by('-created_at')
    for booking in bookings:
        writer.writerow([
            booking.slot.date,
            booking.slot.time,
            booking.name,
            booking.email,
            booking.phone_number,
            booking.drone_details,
            'Booked' if booking.slot.is_booked else 'Available',
            booking.slot.instructor.name
        ])
    
    return response


from django.shortcuts import render
from .models import Instructor

def instructor_details(request):
    instructors = Instructor.objects.all()
    return render(request, 'instructor_details.html', {'instructors': instructors})





from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse

class InstructorCreateView(CreateView):
    model = Instructor
    template_name = 'instructor_form.html'
    success_url = reverse_lazy('instructor_list')
    fields = ['name', 'photo', 'rpc_number', 'experience', 'issued_date', 
              'phone_number', 'email', 'username', 'password']

    def form_invalid(self, form):
        if self.request.is_ajax():
            return JsonResponse(form.errors, status=400)
        return super().form_invalid(form)
    


def delete_expired_slots():
    """Delete all booking slots that have passed their date"""
    current_date = timezone.now().date()
    current_time = timezone.now().time()
    
    # Delete slots from past dates
    BookingSlot.objects.filter(date__lt=current_date).delete()
    
    # Delete slots from current date but with passed time
    BookingSlot.objects.filter(
        date=current_date,
        time__lt=current_time
    ).delete()





# def get_booked_slots(request):
#     date = request.GET.get('date')
#     instructor_id = request.GET.get('instructor_id')
    
#     if not date or not instructor_id:
#         return JsonResponse({'error': 'Date and instructor ID are required'}, status=400)
    
#     try:
#         date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        
#         # Filter slots by both date and instructor
#         slots = BookingSlot.objects.filter(
#             date=date_obj,
#             instructor_id=instructor_id
#         ).order_by('time')
        
#         slots_data = []
#         for slot in slots:
#             slots_data.append({
#                 'time': slot.time.strftime('%H:%M'),
#                 'is_booked': slot.is_booked,
#                 'instructor_id': slot.instructor_id,
#                 'instructor_name': slot.instructor.name
#             })
        
#         return JsonResponse({'slots': slots_data})
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=400)


def get_booked_slots(request):
    date = request.GET.get('date')
    instructor_id = request.GET.get('instructor_id')
    
    if not date or not instructor_id:
        return JsonResponse({'error': 'Date and instructor ID are required'}, status=400)
    
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Filter slots by both date and instructor
        slots = BookingSlot.objects.filter(
            date=date_obj,
            instructor_id=instructor_id  # This ensures we only get slots for the selected instructor
        ).order_by('time')
        
        slots_data = []
        for slot in slots:
            slots_data.append({
                'time': slot.time.strftime('%H:%M'),
                'is_booked': slot.is_booked,
                'instructor_id': slot.instructor_id,
                'instructor_name': slot.instructor.name
            })
        
        return JsonResponse({'slots': slots_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def booking_view(request):
    # Get the instructor_id from URL parameter
    selected_instructor_id = request.GET.get('instructor')
    
    if selected_instructor_id:
        # Only get the selected instructor
        instructors = Instructor.objects.filter(id=selected_instructor_id)
    else:
        instructors = Instructor.objects.none()
    
    context = {
        'instructors': instructors,
        'selected_instructor_id': selected_instructor_id
    }
    return render(request, 'slot_booking.html', context)




# views.py

from django.shortcuts import render
from django.http import JsonResponse, HttpResponseNotFound
from django.views.decorators.http import require_http_methods
from .models import (
    Address, Customer, Seller, Category, Subcategory, Product, Cart, Order,
    OrderItem, PurchaseOrder, PurchaseOrderItem, POMessage, Instructor,
    BookingSlot, UserBooking
)

# Mapping of model names to model classes
MODEL_MAPPING = {
    'address': Address,
    'customer': Customer,
    'seller': Seller,
    'category': Category,
    'subcategory': Subcategory,
    'product': Product,
    'cart': Cart,
    'order': Order,
    'orderitem': OrderItem,
    'purchaseorder': PurchaseOrder,
    'purchaseorderitem': PurchaseOrderItem,
    'pomessage': POMessage,
    'instructor': Instructor,
    'bookingslot': BookingSlot,
    'userbooking': UserBooking,
}

@require_http_methods(["GET"])
def query_tool(request, model_name):
    """
    A generic query view that allows filtering on any model.
    URL example: /query/product/?price=19.99&city=NewYork
    """
    model = MODEL_MAPPING.get(model_name.lower())
    if not model:
        return HttpResponseNotFound("Model not found.")

    # Start with all objects for the given model and apply filters from GET parameters.
    queryset = model.objects.all()
    filter_kwargs = {}
    for key, value in request.GET.items():
        filter_kwargs[key] = value
    queryset = queryset.filter(**filter_kwargs)

    # Return results as JSON.
    data = list(queryset.values())
    return JsonResponse(data, safe=False)

def query_tool_page(request):
    """
    Renders the HTML page for the generic query tool.
    """
    return render(request, "query_tool.html")




from django.shortcuts import render
from django.db.models import Count
from .models import Order

from django.shortcuts import render
from django.db.models import Count
from collections import defaultdict
from .models import Order






# from django.shortcuts import render
# from django.db.models import Count
# from collections import defaultdict
# from .models import Order

# def order_dashboard(request):
#     # 1. Order status bar chart data
#     orders_by_status = Order.objects.values('status').annotate(count=Count('id')).order_by('status')
#     statuses = [entry['status'] for entry in orders_by_status]
#     counts = [entry['count'] for entry in orders_by_status]

#     # 2. Total revenue calculation
#     # Convert each total_price (Decimal) to float to avoid mixing types
#     total_revenue = sum(float(order.total_price()) for order in Order.objects.all())
    
#     # 3. Sales analysis: group orders by day and sum their total price
#     sales_by_day = defaultdict(float)
#     orders = Order.objects.all()
#     for order in orders:
#         day = order.order_date.date()
#         sales_by_day[day] += float(order.total_price())  # Cast Decimal to float here
#     sorted_days = sorted(sales_by_day.keys())
#     sales_dates = [day.strftime('%Y-%m-%d') for day in sorted_days]
#     sales_values = [sales_by_day[day] for day in sorted_days]
    
#     # 4. Refund analysis: count refunded vs non-refunded orders
#     refunded_count = Order.objects.filter(status='Refunded').count()
#     non_refunded_count = Order.objects.exclude(status='Refunded').count()
#     refund_labels = ['Refunded', 'Non-Refunded']
#     refund_counts = [refunded_count, non_refunded_count]
    
#     context = {
#         'statuses': statuses,
#         'counts': counts,
#         'total_revenue': total_revenue,
#         'sales_dates': sales_dates,
#         'sales_values': sales_values,
#         'refund_labels': refund_labels,
#         'refund_counts': refund_counts,
#     }
#     return render(request, 'dashboard.html', context)

# from django.db.models import Count, Sum, F, Case, When, Value, CharField, Avg
# from django.db.models.functions import TruncMonth
# from collections import defaultdict
# from django.shortcuts import render
# from django.utils import timezone
# from datetime import timedelta

# def order_dashboard(request):
#     # Key Metrics
#     total_orders = Order.objects.count()
#     total_revenue = sum(float(order.total_price()) for order in Order.objects.all())
#     avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
#     active_products = Product.objects.filter(quantity_in_stock__gt=0).count()

#     # 1. Order Status Distribution
#     orders_by_status = Order.objects.values('status').annotate(count=Count('id')).order_by('status')
#     statuses = [entry['status'] for entry in orders_by_status]
#     status_counts = [entry['count'] for entry in orders_by_status]

#     # 2. Sales Trend
#     sales_by_day = defaultdict(float)
#     orders = Order.objects.all()
#     for order in orders:
#         day = order.order_date.date()
#         sales_by_day[day] += float(order.total_price())
#     sorted_days = sorted(sales_by_day.keys())
#     sales_dates = [day.strftime('%Y-%m-%d') for day in sorted_days]
#     sales_values = [sales_by_day[day] for day in sorted_days]

#     # 3. Refund Analysis
#     refunded_count = Order.objects.filter(status='Refunded').count()
#     non_refunded_count = Order.objects.exclude(status='Refunded').count()
#     refund_labels = ['Refunded', 'Non-Refunded']
#     refund_counts = [refunded_count, non_refunded_count]

#     # 4. Product Performance
#     top_products = OrderItem.objects.values(
#         'product__name'
#     ).annotate(
#         total_sold=Sum('quantity'),
#         revenue=Sum(F('quantity') * F('product__price'))
#     ).order_by('-revenue')[:5]
    
#     product_names = [item['product__name'] for item in top_products]
#     product_quantities = [item['total_sold'] for item in top_products]
#     product_revenues = [float(item['revenue']) for item in top_products]

#     # 5. Category Distribution
#     category_data = OrderItem.objects.values(
#         'product__subcategory__parent_category__category_name'
#     ).annotate(
#         total_revenue=Sum(F('quantity') * F('product__price'))
#     ).order_by('-total_revenue')
    
#     category_names = [item['product__subcategory__parent_category__category_name'] for item in category_data]
#     category_revenues = [float(item['total_revenue']) for item in category_data]

#     # 6. Inventory Status
#     inventory_status = Product.objects.annotate(
#         status=Case(
#             When(quantity_in_stock=0, then=Value('Out of Stock')),
#             When(quantity_in_stock__lte=F('reorder_level'), then=Value('Low Stock')),
#             default=Value('Healthy'),
#             output_field=CharField(),
#         )
#     ).values('status').annotate(count=Count('id'))
    
#     inventory_labels = [item['status'] for item in inventory_status]
#     inventory_counts = [item['count'] for item in inventory_status]

#     # 7. Customer Analysis
#     top_customers = Order.objects.values(
#         'customer__customer_name'
#     ).annotate(
#         order_count=Count('id'),
#         total_spent=Sum('orderitem__quantity' * F('orderitem__product__price'))
#     ).order_by('-total_spent')[:5]
    
#     customer_names = [item['customer__customer_name'] for item in top_customers]
#     customer_orders = [item['order_count'] for item in top_customers]
#     customer_spending = [float(item['total_spent']) for item in top_customers]

#     context = {
#         # Key Metrics
#         'total_orders': total_orders,
#         'total_revenue': total_revenue,
#         'avg_order_value': avg_order_value,
#         'active_products': active_products,
        
#         # Chart Data
#         'statuses': statuses,
#         'status_counts': status_counts,
#         'sales_dates': sales_dates,
#         'sales_values': sales_values,
#         'refund_labels': refund_labels,
#         'refund_counts': refund_counts,
#         'product_names': product_names,
#         'product_quantities': product_quantities,
#         'product_revenues': product_revenues,
#         'category_names': category_names,
#         'category_revenues': category_revenues,
#         'inventory_labels': inventory_labels,
#         'inventory_counts': inventory_counts,
#         'customer_names': customer_names,
#         'customer_orders': customer_orders,
#         'customer_spending': customer_spending,
#     }
    
#     return render(request, 'dashboard.html', context)
from django.db.models import Count, Sum, F, Case, When, Value, CharField, Avg
from django.db.models import Count, Sum, F, Case, When, Value, CharField, DecimalField
from collections import defaultdict
from django.shortcuts import render
from django.db.models.functions import Cast

def order_dashboard(request):
    # Key Metrics
    total_orders = Order.objects.count()
    total_revenue = sum(float(order.total_price()) for order in Order.objects.all())
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    active_products = Product.objects.filter(quantity_in_stock__gt=0).count()

    # 1. Order Status Distribution
    orders_by_status = Order.objects.values('status').annotate(count=Count('id')).order_by('status')
    statuses = [entry['status'] for entry in orders_by_status]
    status_counts = [entry['count'] for entry in orders_by_status]

    # 2. Sales Trend
    sales_by_day = defaultdict(float)
    orders = Order.objects.all()
    for order in orders:
        day = order.order_date.date()
        sales_by_day[day] += float(order.total_price())
    sorted_days = sorted(sales_by_day.keys())
    sales_dates = [day.strftime('%Y-%m-%d') for day in sorted_days]
    sales_values = [sales_by_day[day] for day in sorted_days]

    # 3. Refund Analysis
    refunded_count = Order.objects.filter(status='Refunded').count()
    non_refunded_count = Order.objects.exclude(status='Refunded').count()
    refund_labels = ['Refunded', 'Non-Refunded']
    refund_counts = [refunded_count, non_refunded_count]

    # 4. Product Performance
    top_products = OrderItem.objects.values(
        'product__name'
    ).annotate(
        total_sold=Sum('quantity'),
        revenue=Sum(F('quantity') * Cast('product__price', DecimalField()))
    ).order_by('-revenue')[:5]
    
    product_names = [item['product__name'] for item in top_products]
    product_quantities = [item['total_sold'] for item in top_products]
    product_revenues = [float(item['revenue']) for item in top_products]

    # 5. Category Distribution
    category_data = OrderItem.objects.values(
        'product__subcategory__parent_category__category_name'
    ).annotate(
        total_revenue=Sum(F('quantity') * Cast('product__price', DecimalField()))
    ).order_by('-total_revenue')
    
    category_names = [item['product__subcategory__parent_category__category_name'] for item in category_data]
    category_revenues = [float(item['total_revenue']) for item in category_data]

    # 6. Inventory Status
    inventory_status = Product.objects.annotate(
        status=Case(
            When(quantity_in_stock=0, then=Value('Out of Stock')),
            When(quantity_in_stock__lte=F('reorder_level'), then=Value('Low Stock')),
            default=Value('Healthy'),
            output_field=CharField(),
        )
    ).values('status').annotate(count=Count('id'))
    
    inventory_labels = [item['status'] for item in inventory_status]
    inventory_counts = [item['count'] for item in inventory_status]

    # 7. Customer Analysis
    top_customers = Order.objects.values(
        'customer__customer_name'
    ).annotate(
        order_count=Count('id'),
        total_spent=Sum(
            F('orderitem__quantity') * Cast('orderitem__product__price', DecimalField())
        )
    ).order_by('-total_spent')[:5]
    
    customer_names = [item['customer__customer_name'] for item in top_customers]
    customer_orders = [item['order_count'] for item in top_customers]
    customer_spending = [float(item['total_spent']) for item in top_customers]

    context = {
        # Key Metrics
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
        'active_products': active_products,
        
        # Chart Data
        'statuses': statuses,
        'status_counts': status_counts,
        'sales_dates': sales_dates,
        'sales_values': sales_values,
        'refund_labels': refund_labels,
        'refund_counts': refund_counts,
        'product_names': product_names,
        'product_quantities': product_quantities,
        'product_revenues': product_revenues,
        'category_names': category_names,
        'category_revenues': category_revenues,
        'inventory_labels': inventory_labels,
        'inventory_counts': inventory_counts,
        'customer_names': customer_names,
        'customer_orders': customer_orders,
        'customer_spending': customer_spending,
    }
    
    return render(request, 'dashboard.html', context)






































from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .chatbot import EnhancedEcommerceBot

chatbot = EnhancedEcommerceBot()

def chat_view(request):
    return render(request, 'chat.html')

@csrf_exempt
def chatbot_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            user_id = request.session.get('user_id', 'anonymous')
            
            response = chatbot.process_message(message, user_id)
            
            return JsonResponse({
                'status': 'success',
                'response': response
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)






















from django.shortcuts import render
from django.http import JsonResponse
import google.generativeai as genai
import os
from django.db.models import Avg, Count, F, Q, Max, Min, Sum
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import datetime, timedelta

# Import your models
from .models import (
    Category, Subcategory, Product, Cart, Order, OrderItem,
    Instructor, BookingSlot, UserBooking, Customer, Seller,
    PurchaseOrder, PurchaseOrderItem
)

def chatbot(request):
    """View for displaying and handling the chatbot interface"""
    if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        user_message = request.POST.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'error': 'Please enter a message'})
        
        try:
            # Get user session info if available for personalization
            user_id = request.session.get('user_id')
            user_type = request.session.get('user_type')
            
            # Prepare chatbot response using Gemini API
            response_data = generate_chatbot_response(user_message, user_id, user_type)
            
            if isinstance(response_data, dict):
                return JsonResponse(response_data)
            else:
                return JsonResponse({'response': response_data})
        except Exception as e:
            print(f"Chatbot error: {str(e)}")  # Add logging for debugging
            return JsonResponse({'error': f"Error processing your request: {str(e)}"})
    
    # For GET requests, render the chatbot interface
    context = {
        'initial_message': "Hello! I'm your drone training assistant. How can I help you today?"
    }
    return render(request, 'chatbot.html', context)

def generate_chatbot_response(user_message, user_id=None, user_type=None):
    """Generate response using Gemini API enriched with database lookups"""
    # Check if API key exists
    api_key = "AIzaSyBvgdIgptWKRrICvcbmp5uSfmxDN974rkQ"
    if not api_key:
        return {'response': "ERROR: Gemini API key not found. Please set the GEMINI_API_KEY environment variable."}
    
    # Configure Gemini API
    genai.configure(api_key=api_key)
    
    # Define generation config for model
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    
    # Initialize context information
    db_context = ""
    personalized_context = ""
    query_type = "general"
    
    # Personalize if user is logged in
    if user_id and user_type == 'customer':
        try:
            customer = Customer.objects.get(id=user_id)
            personalized_context = f"Customer: {customer.customer_name}\n"
            
            # Check if user is asking about orders
            if any(word in user_message.lower() for word in ['my order', 'my orders', 'order status']):
                orders = Order.objects.filter(customer=customer).order_by('-order_date')
                if orders.exists():
                    personalized_context += "\nOrder History:\n"
                    for i, order in enumerate(orders[:5], 1):  # Show last 5 orders
                        personalized_context += f"\nOrder #{order.id} - {order.order_date.strftime('%Y-%m-%d')}\n"
                        personalized_context += f"Status: {order.status}\n"
                        personalized_context += f"Total: ₹{order.total_price()}\n"
                        personalized_context += "Products:\n"
                        
                        for order_item in order.orderitem_set.all():
                            personalized_context += f"- {order_item.quantity}x {order_item.product.name} (₹{order_item.product.price} each)\n"
                        
                        # Add a view link for the order
                        personalized_context += f"[View Order Details: <a href='/orders/{order.id}/'>Order #{order.id}</a>]\n"
                        
                        if i < min(5, orders.count()):
                            personalized_context += "----------\n"
                    
                    # Add link to view all orders
                    if orders.count() > 5:
                        personalized_context += f"\n[View all {orders.count()} orders: <a href='/my-orders/'>My Orders</a>]\n"
                else:
                    personalized_context += "\nYou don't have any orders yet.\n"
                    personalized_context += "[Start shopping: <a href='/products/'>Shop Now</a>]\n"
            
            # Check if user is asking about bookings
            elif any(word in user_message.lower() for word in ['appointment', 'booking', 'instructor', 'schedule', 'lesson']):
                bookings = UserBooking.objects.filter(email=customer.email).order_by('slot__date')
                if bookings.exists():
                    personalized_context += "\nYour Booking Information:\n"
                    
                    # Show upcoming bookings first
                    upcoming = bookings.filter(slot_date_gte=timezone.now().date())
                    if upcoming.exists():
                        personalized_context += "\n--- Upcoming Bookings ---\n"
                        for booking in upcoming:
                            personalized_context += f"\nBooking on {booking.slot.date}\n"
                            personalized_context += f"Time: {booking.slot.time}\n"
                            personalized_context += f"Instructor: {booking.slot.instructor.name}\n"
                            personalized_context += f"[Booking Details: <a href='/my-bookings/{booking.id}/'>View Details</a>]\n"
                    
                    # Add link to manage bookings
                    personalized_context += f"\n[Manage your bookings: <a href='/my-bookings/'>My Bookings</a>]\n"
                else:
                    personalized_context += "\nYou don't have any bookings scheduled.\n"
                    personalized_context += "[Book a lesson: <a href='/book-instructor/'>Book Now</a>]\n"
                
            # Check if user has items in cart
            cart_items = Cart.objects.filter(customer=customer)
            if cart_items.exists():
                personalized_context += "\nYou have items in your cart:\n"
                total = 0
                for item in cart_items:
                    personalized_context += f"- {item.quantity}x {item.product.name} (₹{item.product.price} each)\n"
                    total += item.sub_total()
                personalized_context += f"\nCart total: ₹{total}\n"
                personalized_context += "[View Cart: <a href='/cart/'>Go to Cart</a>]\n"
                
        except Exception as e:
            print(f"Error getting personalization data: {str(e)}")
    
    # Classify the query type
    user_message_lower = user_message.lower()
    
    # Define common keywords for different query types
    product_terms = ['drone', 'product', 'buy', 'purchase', 'price', 'stock', 'category']
    instructor_terms = ['instructor', 'teacher', 'trainer', 'lesson', 'training', 'experience', 'qualification']
    booking_terms = ['book', 'booking', 'slot', 'schedule', 'appointment', 'time', 'date', 'availability']
    order_terms = ['order', 'purchase', 'delivery', 'status', 'track', 'shipping']
    
    # Determine query type
    if any(term in user_message_lower for term in product_terms):
        query_type = "product_info"
    elif any(term in user_message_lower for term in instructor_terms):
        query_type = "instructor_info"
    elif any(term in user_message_lower for term in booking_terms):
        query_type = "booking_info"
    elif any(term in user_message_lower for term in order_terms):
        query_type = "order_info"
    
    # Handle product-related queries
    if query_type == "product_info":
        # Check for category mentions
        categories = Category.objects.all()
        mentioned_category = None
        for category in categories:
            if category.category_name.lower() in user_message_lower:
                mentioned_category = category
                break
        
        # Check for product name mentions
        products = Product.objects.all()
        mentioned_product = None
        for product in products:
            if product.name.lower() in user_message_lower:
                mentioned_product = product
                break
        
        # Provide context based on what was found
        if mentioned_product:
            db_context += f"Product Information: {mentioned_product.name}\n"
            db_context += f"Price: ₹{mentioned_product.price}\n"
            db_context += f"Description: {mentioned_product.description}\n"
            db_context += f"In Stock: {mentioned_product.quantity_in_stock} units\n"
            db_context += f"Category: {mentioned_product.subcategory.parent_category.category_name} > {mentioned_product.subcategory.subcategory_name}\n"
            db_context += f"[View Product: <a href='/products/{mentioned_product.id}/'>Click here</a>]\n"
        
        elif mentioned_category:
            # Get subcategories and products in this category
            subcategories = Subcategory.objects.filter(parent_category=mentioned_category)
            
            db_context += f"Category: {mentioned_category.category_name}\n"
            db_context += f"[Browse Category: <a href='/category/{mentioned_category.id}/'>View All Products</a>]\n\n"
            
            db_context += "Subcategories:\n"
            for subcategory in subcategories[:5]:
                db_context += f"- {subcategory.subcategory_name} [<a href='/subcategories/{subcategory.id}/'>Browse</a>]\n"
            
            # Get top products in this category
            top_products = Product.objects.filter(subcategory__parent_category=mentioned_category).order_by('-quantity_in_stock')[:5]
            
            if top_products:
                db_context += "\nPopular products in this category:\n"
                for product in top_products:
                    db_context += f"- {product.name}: ₹{product.price} [<a href='/product/<int:product_id>/'>View</a>]\n"
        
        else:
            # General product information
            top_products = Product.objects.all().order_by('-quantity_in_stock')[:5]
            db_context += "Here are our top drone products:\n\n"
            
            for product in top_products:
                db_context += f"- {product.name}: ₹{product.price}\n"
                db_context += f"  Category: {product.subcategory.parent_category.category_name} > {product.subcategory.subcategory_name}\n"
                db_context += f"  [View Details: <a href='/product/{product.id}/'>Product Link</a>]\n\n"
            
            db_context += "[Browse All Products: <a href='/product_list/'>View All Products</a>]"
    
    # Handle instructor-related queries
    elif query_type == "instructor_info":
        instructors = Instructor.objects.all().order_by('name')
        
        # Check for specific instructor mentions
        mentioned_instructor = None
        for instructor in instructors:
            if instructor.name.lower() in user_message_lower:
                mentioned_instructor = instructor
                break
        
        if mentioned_instructor:
            db_context += f"Instructor: {mentioned_instructor.name}\n"
            db_context += f"Experience: {mentioned_instructor.experience[:100]}...\n"
            db_context += f"RPC Number: {mentioned_instructor.rpc_number}\n"
            db_context += f"Issued Date: {mentioned_instructor.issued_date}\n"
            db_context += f"[View Profile: <a href='/instructors/{mentioned_instructor.id}/'>Click here</a>]\n"
            
            # Check available slots for this instructor
            available_slots = BookingSlot.objects.filter(
                instructor=mentioned_instructor,
                date__gte=timezone.now().date(),
                is_booked=False
            ).order_by('date', 'time')[:5]
            
            if available_slots:
                db_context += "\nUpcoming available slots:\n"
                for slot in available_slots:
                    db_context += f"- {slot.date} at {slot.time}\n"
                
                db_context += f"\n[Book a session: <a href='/book-instructor/{mentioned_instructor.id}/'>Book Now</a>]"
            else:
                db_context += "\nNo available slots at the moment. Check back later or contact us for custom scheduling."
        
        else:
            db_context += "Our qualified drone instructors:\n\n"
            for instructor in instructors[:5]:
                db_context += f"- {instructor.name}: {instructor.experience[:50]}...\n"
                # db_context += f"  [View Profile: <a href='/instructor/{instructor.id}/'>Instructor Details</a>]\n\n"
            
            db_context += "[View All Instructors: <a href='/instructor/'>Browse Instructors</a>]\n"
    
    # Handle booking-related queries
    elif query_type == "booking_info":
        # Get available slots
        available_slots = BookingSlot.objects.filter(
            date__gte=timezone.now().date(),
            is_booked=False
        ).order_by('date', 'time')[:10]
        
        db_context += "Booking Information:\n\n"
        db_context += "To book a drone training session, you need to:\n"
        db_context += "1. Select an instructor from our qualified team\n"
        db_context += "2. Choose an available time slot that works for you\n"
        db_context += "3. Complete the booking form with your details and drone specifications\n\n"
        
        if available_slots:
            db_context += "Here are some upcoming available slots:\n"
            for slot in available_slots:
                db_context += f"- {slot.date} at {slot.time} with {slot.instructor.name}\n"
            
            db_context += "\n[Book a training session: <a href='/book-instructor/'>Book Now</a>]\n"
        else:
            db_context += "Currently all slots are booked. Please check back soon for new availability.\n"
            db_context += "[Contact us for custom scheduling: <a href='/contact/'>Contact Us</a>]"
    
    # Handle order-related queries
    elif query_type == "order_info":
        db_context += "Order Information:\n\n"
        db_context += "After placing an order on our website:\n"
        db_context += "1. You'll receive an order confirmation email with your order details\n"
        db_context += "2. Your order status will update as it progresses (Processing, Shipped, Delivered)\n"
        db_context += "3. You can track your order status in your account dashboard\n\n"
        
        db_context += "For order tracking or issues, you can:\n"
        db_context += "- Check your order status: [<a href='/my-orders/'>My Orders</a>]\n"
        db_context += "- Contact customer support: [<a href='/contact/'>Contact Us</a>]\n"
        db_context += "- View shipping policies: [<a href='/shipping-policy/'>Shipping Policy</a>]\n"
    
    # System instruction for the AI
    system_instruction = """
    You are a helpful drone training e-commerce assistant. You help customers find information about drone products,
    instructors, booking training sessions, and managing orders.
    
    Key information:
    - We sell drone products and offer professional drone training
    - Our instructors are certified with RPC (Remote Pilot Certificate) credentials
    - Customers can book one-on-one training sessions with our instructors
    - We offer various drone categories and models for different skill levels and purposes
    
    Always be helpful, concise, and informative. If you don't know something, suggest that the customer contact customer service.
    
    IMPORTANT: When providing links, maintain the HTML <a> tag format exactly as provided in the context. Do not modify URLs.
    
    When customers ask about specific products, instructors, or bookings, emphasize the relevant information and include the
    provided links to direct them to the appropriate pages on our website.
    """
    
    # Create Gemini model
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
        system_instruction=system_instruction
    )
    
    # Prepare context with database info if available
    context_for_model = ""
    if personalized_context:
        context_for_model += f"Customer information:\n{personalized_context}\n\n"
    
    if db_context:
        context_for_model += f"Information from our database that might help answer the query:\n{db_context}\n\n"
    
    # Complete prompt with user question
    prompt = f"{context_for_model}User query: {user_message}\n\n"
    prompt += "Please provide a helpful response based on the available information."
    
    try:
        # Generate response from Gemini
        response = model.generate_content(prompt)
        
        # Track metrics for monitoring
        response_metadata = {
            'response': response.text,
            'db_data_used': bool(db_context),
            'query_type': query_type, 
            'personalized': bool(personalized_context)
        }
        
        return response_metadata
    except Exception as e:
        print(f"Gemini API error: {str(e)}")
        # Provide a fallback response if API fails
        fallback_responses = {
            "product_info": "I can help you find the perfect drone for your needs. However, I'm having trouble accessing our product database right now. Please try again in a few moments or browse our collection online.",
            "instructor_info": "Our certified drone instructors are available for training sessions. While I can't access their details right now, you can check our 'Instructors' page to find one that matches your needs.",
            "booking_info": "We offer personalized drone training sessions with qualified instructors. I'm having trouble accessing booking availability at the moment. Please visit our 'Book Instructor' page to see current availability.",
            "order_info": "I can help track your orders and provide shipping information. I'm having difficulty accessing our systems right now. Please try again later or check your Order History page directly.",
            "general": "I'm sorry, I'm having trouble connecting to my knowledge base right now. Please try again later or contact our customer service for immediate assistance."
        }
        
        return {
            'response': fallback_responses.get(query_type, fallback_responses["general"]),
            'db_data_used': bool(db_context),
            'error': str(e)
        }

@login_required
def add_to_wishlist(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        if not product_id:
            messages.error(request, 'Invalid request. Product ID is required.')
            return redirect('index')
            
        try:
            product = Product.objects.get(id=product_id)
            customer = request.user.customer
            
            # Check if item already exists in wishlist
            wishlist_item, created = Wishlist.objects.get_or_create(
                customer=customer,
                product=product
            )
            
            if created:
                messages.success(request, f'{product.name} has been added to your wishlist.')
            else:
                messages.info(request, f'{product.name} is already in your wishlist.')
                
        except Product.DoesNotExist:
            messages.error(request, 'Product not found.')
        except Exception as e:
            messages.error(request, 'An error occurred while adding to wishlist.')
            
    return redirect('index')

@login_required
def remove_from_wishlist(request, product_id):
    try:
        customer = request.user.customer
        wishlist_item = Wishlist.objects.get(customer=customer, product_id=product_id)
        product_name = wishlist_item.product.name
        wishlist_item.delete()
        messages.success(request, f'{product_name} has been removed from your wishlist.')
    except Wishlist.DoesNotExist:
        messages.error(request, 'Item not found in wishlist.')
    except Exception as e:
        messages.error(request, 'An error occurred while removing from wishlist.')
    
    return redirect('view_wishlist')

@login_required
def view_wishlist(request):
    try:
        customer = request.user.customer
        wishlist_items = Wishlist.objects.filter(customer=customer).select_related('product')
        context = {
            'wishlist_items': wishlist_items
        }
        return render(request, 'customer/wishlist.html', context)
    except Exception as e:
        messages.error(request, 'An error occurred while loading your wishlist.')
        return redirect('index')
    

@login_required
def index(request):
    products = Product.objects.all()
    cart_items_count = Cart.objects.filter(customer=request.user.customer).count()  # Count items in the cart
    return render(request, 'index.html', {'products': products, 'cart_items_count': cart_items_count})


@login_required
def add_to_comparison(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        if not product_id:
            messages.error(request, 'Product ID is required')
            return redirect('product_list')
            
        try:
            product = Product.objects.get(id=product_id)
            comparison_list, created = ComparisonList.objects.get_or_create(user=request.user)
            
            # Limit to 4 products maximum
            if comparison_list.products.count() >= 4:
                messages.warning(request, 'You can compare up to 4 products at a time')
                return redirect('product_list')
                
            comparison_list.products.add(product)
            messages.success(request, f'{product.name} added to comparison')
            
        except Product.DoesNotExist:
            messages.error(request, 'Product not found')
        except Exception as e:
            messages.error(request, str(e))
            
    return redirect('product_list')

@login_required
def remove_from_comparison(request, product_id):
    try:
        comparison_list = ComparisonList.objects.get(user=request.user)
        product = Product.objects.get(id=product_id)
        comparison_list.products.remove(product)
        messages.success(request, f'{product.name} removed from comparison')
    except (ComparisonList.DoesNotExist, Product.DoesNotExist):
        messages.error(request, 'Product or comparison list not found')
    return redirect('view_comparison')

@login_required
@login_required
def view_comparison(request):
    comparison_list, created = ComparisonList.objects.get_or_create(user=request.user)
    products = comparison_list.products.all()
    
    # Get all unique specification keys across products
    spec_keys = set()
    for product in products:
        if hasattr(product, 'specifications'):
            spec_keys.update(product.specifications.keys())
    
    context = {
        'products': products,
        'spec_keys': sorted(spec_keys)
    }
    return render(request, 'customer/comparison.html', context)