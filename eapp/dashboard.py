from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
import plotly.graph_objects as go
import plotly.express as px
from .models import (
    Order, Product, Category, Customer, 
    PurchaseOrder, Instructor, BookingSlot, UserBooking
)

def get_order_status_chart():
    # Order Status Distribution
    status_data = Order.objects.values('status').annotate(count=Count('id'))
    fig = go.Figure(data=[
        go.Pie(
            labels=[item['status'] for item in status_data],
            values=[item['count'] for item in status_data],
            hole=.3
        )
    ])
    fig.update_layout(title='Order Status Distribution')
    return fig.to_html()

def get_sales_trend():
    # Daily sales trend for the last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_sales = Order.objects.filter(
        order_date__gte=thirty_days_ago
    ).values('order_date__date').annotate(
        total_sales=Sum('orderitem__product__price')
    ).order_by('order_date__date')

    fig = go.Figure(data=[
        go.Line(
            x=[item['order_date__date'] for item in daily_sales],
            y=[float(item['total_sales']) for item in daily_sales]
        )
    ])
    fig.update_layout(title='Sales Trend (Last 30 Days)')
    return fig.to_html()

def get_category_distribution():
    # Product distribution by category
    category_data = Category.objects.annotate(
        product_count=Count('subcategory__product')
    )
    
    fig = go.Figure(data=[
        go.Bar(
            x=[cat.category_name for cat in category_data],
            y=[cat.product_count for cat in category_data]
        )
    ])
    fig.update_layout(title='Products by Category')
    return fig.to_html()

def get_inventory_status():
    # Products with low inventory
    low_stock = Product.objects.filter(
        quantity_in_stock__lt=models.F('reorder_level')
    ).values('name', 'quantity_in_stock', 'reorder_level')
    
    fig = go.Figure(data=[
        go.Bar(
            name='Current Stock',
            x=[item['name'] for item in low_stock],
            y=[item['quantity_in_stock'] for item in low_stock]
        ),
        go.Bar(
            name='Reorder Level',
            x=[item['name'] for item in low_stock],
            y=[item['reorder_level'] for item in low_stock]
        )
    ])
    fig.update_layout(
        title='Low Stock Products',
        barmode='group'
    )
    return fig.to_html()

def get_instructor_bookings():
    # Booking statistics by instructor
    instructor_stats = Instructor.objects.annotate(
        total_slots=Count('bookingslot'),
        booked_slots=Count('bookingslot', filter=models.Q(bookingslot__is_booked=True))
    )
    
    fig = go.Figure(data=[
        go.Bar(
            name='Available Slots',
            x=[inst.name for inst in instructor_stats],
            y=[(inst.total_slots - inst.booked_slots) for inst in instructor_stats]
        ),
        go.Bar(
            name='Booked Slots',
            x=[inst.name for inst in instructor_stats],
            y=[inst.booked_slots for inst in instructor_stats]
        )
    ])
    fig.update_layout(
        title='Instructor Booking Statistics',
        barmode='stack'
    )
    return fig.to_html()