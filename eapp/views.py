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

# Configure API key
api_key = "AIzaSyBvgdIgptWKRrICvcbmp5uSfmxDN974rkQ"
genai.configure(api_key=api_key)

# Initialize the model
model = genai.GenerativeModel('gemini-1.5-flash')

def generate_text(request):
    if request.method == 'POST':
        user_input = request.POST.get('input_text', '')
        if user_input:
            try:
                # Call generate_content
                response = model.generate_content(user_input)
                # Access the text directly if it's an attribute
                generated_text = response.text if hasattr(response, 'text') else 'No text found'
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
        
        elif action == 'cancel_booking':
            booking_id = request.POST.get('booking_id')
            try:
                # Ensure instructor can only cancel bookings for their slots
                booking = UserBooking.objects.get(
                    id=booking_id,
                    slot__instructor=instructor
                )
                booking.slot.is_booked = False
                booking.slot.save()
                booking.delete()
                messages.success(request, 'Booking cancelled successfully!')
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