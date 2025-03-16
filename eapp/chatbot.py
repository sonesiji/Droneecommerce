from django.db.models import Q
from datetime import datetime, timedelta
from .models import (
    Product, Order, Category, Subcategory, Customer, Seller, 
    BookingSlot, Instructor, Address, OrderItem, PurchaseOrder
)

class EnhancedEcommerceBot:
    def __init__(self):
        self.context = {}
        
    def process_message(self, message, user=None):
        message = message.lower().strip()
        
        # Comprehensive help and project information
        if any(word in message for word in ['hello', 'hi', 'hey', 'help', 'what can you do']):
            return self.get_help_message()
            
        # Project overview
        if any(phrase in message for phrase in ['about project', 'project details', 'what is this project']):
            return self.get_project_overview()
            
        # Detailed product information
        if 'product' in message:
            if 'all' in message or 'list' in message or 'show' in message:
                return self.get_all_products()
            if 'detail' in message:
                return self.get_product_details(message)
                
        # Category information
        if 'categor' in message:  # Will match category/categories
            return self.get_category_details()
            
        # Seller information
        if 'seller' in message:
            return self.get_seller_information()
            
        # Order related queries
        if 'order' in message:
            if user:
                return self.get_order_details(user)
            return "Please log in to access order information. Our ordering system allows customers to:\n" \
                   "- Place orders for multiple products\n" \
                   "- Track order status\n" \
                   "- View order history\n" \
                   "- Get delivery updates"
                   
        # Instructor and booking related queries
        if any(word in message for word in ['instructor', 'booking', 'slot', 'schedule']):
            return self.get_booking_information()
            
        # Purchase order information
        if 'purchase' in message:
            return self.get_purchase_order_info()
            
        return "I can help you with detailed information about:\n" \
               "1. Products and their details\n" \
               "2. Categories and subcategories\n" \
               "3. Order management\n" \
               "4. Booking system\n" \
               "5. Seller information\n" \
               "Please ask specific questions about any of these topics!"

    def get_help_message(self):
        return """Welcome to our E-commerce Assistant! 🛍️

I can provide detailed information about:

📦 Products:
- Complete product listings
- Price information
- Stock availability
- Product descriptions

🏷️ Categories:
- Main categories
- Subcategories
- Product classification

📋 Orders:
- Order tracking
- Order history
- Order status updates
- Delivery information

👨‍🏫 Booking System:
- Available instructors
- Booking slots
- Scheduling information
- Instructor qualifications

🏪 Sellers:
- Seller profiles
- Product offerings
- Contact information

How can I assist you today?"""

    def get_project_overview(self):
        return """This is a comprehensive E-commerce platform with the following key features:

1. Product Management System:
   - Multiple categories and subcategories
   - Detailed product information
   - Stock management
   - Price tracking

2. User Management:
   - Customer profiles
   - Seller accounts
   - Address management
   - Authentication system

3. Order Processing:
   - Shopping cart functionality
   - Order tracking
   - Multiple status updates
   - Delivery management

4. Booking System:
   - Instructor management
   - Slot booking
   - Schedule management
   - Availability tracking

5. Purchase Order System:
   - Automated reordering
   - Stock level monitoring
   - Supplier management
   - Order processing

Would you like detailed information about any specific feature?"""

    def get_all_products(self):
        products = Product.objects.all()
        if not products:
            return "Currently, there are no products in the database. The system supports:\n" \
                   "- Product name, description, and pricing\n" \
                   "- Multiple product images\n" \
                   "- Stock management\n" \
                   "- SKU tracking\n" \
                   "- Automatic reordering system"
        
        response = "Here are all our products:\n\n"
        for product in products:
            response += f"📦 {product.name}\n"
            response += f"   Price: ${product.price}\n"
            response += f"   Stock: {product.quantity_in_stock} units\n"
            response += f"   Seller: {product.seller.name}\n"
            response += f"   Category: {product.subcategory.parent_category.category_name}\n\n"
        return response

    def get_category_details(self):
        categories = Category.objects.all()
        if not categories:
            return "Our category system supports:\n" \
                   "- Main categories\n" \
                   "- Subcategories\n" \
                   "- Product classification\n" \
                   "- Category-based navigation"
        
        response = "📑 Product Categories and Subcategories:\n\n"
        for category in categories:
            response += f"🔹 {category.category_name}\n"
            subcategories = Subcategory.objects.filter(parent_category=category)
            for subcategory in subcategories:
                response += f"  ├─ {subcategory.subcategory_name}\n"
                products = Product.objects.filter(subcategory=subcategory)
                response += f"  │  ({products.count()} products)\n"
            response += "\n"
        return response

    def get_seller_information(self):
        sellers = Seller.objects.all()
        if not sellers:
            return "Our seller management system supports:\n" \
                   "- Seller profiles\n" \
                   "- Product management\n" \
                   "- Contact information\n" \
                   "- Order processing"
        
        response = "🏪 Registered Sellers:\n\n"
        for seller in sellers:
            response += f"👤 {seller.name}\n"
            products = Product.objects.filter(seller=seller)
            response += f"   Products: {products.count()}\n"
            response += f"   Contact: {seller.phone_no}\n"
            response += f"   Address: {seller.address}\n\n"
        return response

    def get_booking_information(self):
        instructors = Instructor.objects.all()
        if not instructors:
            return "Our booking system features:\n" \
                   "- Qualified instructors\n" \
                   "- Flexible scheduling\n" \
                   "- Real-time availability\n" \
                   "- Automated slot management"
        
        response = "👨‍🏫 Available Instructors and Slots:\n\n"
        for instructor in instructors:
            response += f"Instructor: {instructor.name}\n"
            response += f"Experience: {instructor.experience}\n"
            response += f"RPC Number: {instructor.rpc_number}\n"
            
            # Get available slots
            today = datetime.now().date()
            week_later = today + timedelta(days=7)
            slots = BookingSlot.objects.filter(
                instructor=instructor,
                date__range=[today, week_later],
                is_booked=False
            )
            
            if slots:
                response += "Available Slots:\n"
                for slot in slots:
                    response += f"- {slot.date} at {slot.time}\n"
            response += "\n"
        return response

    def get_purchase_order_info(self):
        return """Our Purchase Order System manages:

1. Automatic Reordering:
   - Stock level monitoring
   - Reorder point tracking
   - Supplier notification

2. Order Processing:
   - Purchase order creation
   - Quantity calculation
   - Cost management

3. Supplier Management:
   - Supplier profiles
   - Contact information
   - Order history

4. Stock Management:
   - Current stock levels
   - Reorder levels
   - SKU tracking

Would you like specific information about any of these features?"""
