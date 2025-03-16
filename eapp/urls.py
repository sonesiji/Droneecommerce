from django.urls import path
from . import views
from .views import query_tool
from .views import query_tool_page, query_tool
from .views import order_dashboard
from .views import (
    generate_text,
    instructor_details,
    slot_booking,
    payment_page,
    view_bookings,
    confirm_payment,  # Handle confirmation of payment
)

urlpatterns = [
    path('',views.index,name='index'),
    path('customer_dashboard/',views.customer_dashboard,name='customer_dashboard'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('change_password/', views.change_password, name='change_password'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('reset_password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
    path('logout/', views.user_logout, name='logout'),
    path('edit_customer/', views.edit_customer, name='edit_customer'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('address/', views.address_list, name='address_list'),
    path('address/add/', views.address_create, name='address_create'),
    path('address/edit/<int:pk>/', views.address_edit, name='address_edit'),
    path('address/delete/<int:pk>/', views.address_delete, name='address_delete'),
    path("cart/", views.cart, name="cart"),
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/increase/<int:cart_item_id>/', views.increase_quantity, name='increase_quantity'),
    path('cart/decrease/<int:cart_item_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('delete_item_in_cart/<int:id>/', views.delete_item_in_cart, name='delete_item_in_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order_list/', views.order_list, name='order_list'),
    path('order_detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('product_list',views.product_list,name='product_list'),
    path('search/', views.search_results, name='search_results'),
    path('category/<int:category_id>/', views.category_products, name='category_products'),
    path('subcategory/<int:subcategory_id>/', views.subcategory_products, name='subcategory_products'),
    path('create_purchase_order/', views.CreatePurchaseOrderView.as_view(), name='create_purchase_order'),
    path('seller', views.seller_purchase_orders, name='seller_purchase_orders'),
    path('seller/history', views.seller_purchase_orders_history, name='seller_purchase_orders_history'),
    path('seller/purchase_order/<int:purchase_order_id>/', views.purchase_order_details, name='purchase_order_details'),
    path('seller/purchase_order/<int:purchase_order_id>/reject/', views.reject_purchase_order, name='reject_purchase_order'),
    path('order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    # path('generate/', generate_text, name='generate_text'),
     path('generate_text/', views.generate_text, name='generate_text'),

    path('instructor/', instructor_details, name='instructor_details'),
    # path('', instructor_details, name='instructor_details'),  # Instructor details page
    path('book/', slot_booking, name='slot_booking'),  # Slot booking page
    path('payment/<int:booking_id>/', payment_page, name='payment'),  # Redirects to payment page with booking_id
    
  
    path('confirm-payment/<int:booking_id>/', views.confirm_payment, name='confirm_payment'),
   

    path('view-bookings/', view_bookings, name='view_bookings'),  # View user bookings page
    
    path('available-times/', views.available_times, name='available_times'),  # Get available times
    
      path('slot-booking/', views.slot_booking, name='slot_booking'),
    path('get-booked-slots/', views.get_booked_slots, name='get_booked_slots'),

    path('view-bookings/', views.view_bookings, name='view_bookings'),


path('instructor/dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
path('instructor/export-bookings/', views.export_bookings, name='export_bookings'),
path('query/', query_tool_page, name='query_tool_page'),
    # JSON endpoint to handle queries for specific models.
    path('query/<str:model_name>/', query_tool, name='query_tool'),
     path('dashboard/', order_dashboard, name='order_dashboard'),
      path('api/chatbot/', views.chatbot_message, name='chatbot_message'),

     path('chat/', views.chat_view, name='chat_view'), 



    
    
]
