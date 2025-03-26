from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Count, Avg, F, Q, Window, Case, When,Max,ExpressionWrapper,DurationField
from django.db.models.functions import TruncMonth, ExtractHour, ExtractWeek, ExtractYear,ExtractDay
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import Medicine, Shop, MedicineStock, MedicineSale, StockAlert
import logging
from django.views.decorators.http import require_POST
from .filters import MedicineFilter, StockFilter, SaleFilter, ShopFilter
from django.db.models import Q
from django_filters.views import FilterView
from django.shortcuts import get_object_or_404
from django.contrib import messages
from .filters import SaleFilter

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Medicine, Shop, MedicineStock, MedicineSale

logger = logging.getLogger('inventory')

def dashboard(request):
    try:
        # Basic statistics
        total_sales = MedicineSale.objects.aggregate(
            total=Sum('total_amount'))['total'] or 0
        total_stock_value = MedicineStock.objects.aggregate(
            total=Sum(F('quantity') * F('price')))['total'] or 0
        
        # Low stock and expiry alerts
        low_stock_count = MedicineStock.objects.filter(
            quantity__lte=F('reorder_level')).count()
        expiring_soon = MedicineStock.objects.filter(
            expiry_date__lte=timezone.now().date() + timedelta(days=30),
            expiry_date__gt=timezone.now().date()
        ).count()

        # Get top selling medicines with shop information
        sales_by_medicine = MedicineSale.objects.values(
            'medicine_id'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_sales=Sum('total_amount')
        ).order_by('-total_quantity')[:5]

        # Get medicine details and their shops
        top_medicines = []
        for sale in sales_by_medicine:
            medicine = Medicine.objects.get(primary_id=sale['medicine_id'])
            shops = Shop.objects.filter(
                medicinestock__medicine=medicine
            ).distinct().values_list('name', flat=True)
            
            top_medicines.append({
                'primary_id': medicine.primary_id,
                'name': medicine.name,
                'total_quantity': sale['total_quantity'],
                'total_sales': sale['total_sales'],
                'shops': list(shops)
            })

        context = {
            'total_sales': total_sales,
            'total_stock_value': total_stock_value,
            'low_stock_count': low_stock_count,
            'expiring_soon': expiring_soon,
            'top_medicines': top_medicines,
        }
        return render(request, 'inventory/dashboard.html', context)
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        messages.error(request, "Error loading dashboard")
        return render(request, 'inventory/dashboard.html', {})

def medicine_list(request):
    medicines = Medicine.objects.all()
    medicine_filter = MedicineFilter(request.GET, queryset=medicines)
    
    # Additional search functionality
    search_query = request.GET.get('search')
    if search_query:
        medicine_filter.qs = medicine_filter.qs.filter(
            Q(name__icontains=search_query) |
            Q(generic_name__icontains=search_query) |
            Q(manufacturer__icontains=search_query)
        )
    
    context = {
        'filter': medicine_filter,
        'medicines': medicine_filter.qs
    }
    return render(request, 'inventory/medicines/list.html', context)

def medicine_detail(request, primary_id):
    medicine = get_object_or_404(Medicine, primary_id=primary_id)
    stocks = MedicineStock.objects.filter(medicine=medicine)
    sales = MedicineSale.objects.filter(medicine=medicine)
    
    # Calculate total sales for percentage calculation
    total_sales = sales.aggregate(
        total_quantity=Sum('quantity')
    )
    
    # Stock analysis by shop
    shop_stats = []
    for stock in stocks:
        shop_sales = sales.filter(shop=stock.shop)
        shop_stats.append({
            'shop_name': stock.shop.name,
            'current_stock': stock.quantity,
            'total_sales': shop_sales.aggregate(Sum('quantity'))['quantity__sum'] or 0,
            'revenue': shop_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        })
    
    context = {
        'medicine': medicine,
        'stocks': stocks,
        'shop_stats': shop_stats,
        'total_sales': total_sales,
    }
    return render(request, 'inventory/medicines/detail.html', context)

def shop_list(request):
    shops = Shop.objects.all()
    shop_filter = ShopFilter(request.GET, queryset=shops)
    
    search_query = request.GET.get('search')
    if search_query:
        shop_filter.qs = shop_filter.qs.filter(
            Q(name__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    context = {
        'filter': shop_filter,
        'shops': shop_filter.qs
    }
    return render(request, 'inventory/shops/list.html', context)

def shop_detail(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    
    # Get stocks with medicine information
    stocks = MedicineStock.objects.filter(shop=shop).select_related('medicine')
    
    # Get sales information
    sales = MedicineSale.objects.filter(shop=shop).select_related('medicine')
    
    # Calculate total revenue
    total_revenue = sales.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Get monthly sales count
    monthly_sales_count = sales.filter(
        date__month=timezone.now().month
    ).count()
    
    # Get recent sales
    recent_sales = sales.order_by('-date')[:10]
    
    # Get top selling medicines in this shop
    top_medicines = sales.values(
        'medicine__name',
        'medicine__primary_id'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_sales=Sum('total_amount')
    ).order_by('-total_quantity')[:5]
    
    # Low stock alerts
    low_stock_items = stocks.filter(quantity__lte=F('reorder_level'))
    
    context = {
        'shop': shop,
        'stocks': stocks,
        'total_revenue': total_revenue,
        'monthly_sales_count': monthly_sales_count,
        'top_medicines': top_medicines,
        'low_stock_items': low_stock_items,
        'recent_sales': recent_sales,
    }
    return render(request, 'inventory/shops/detail.html', context)

def stock_alerts(request):
    # Get all active alerts
    low_stock_alerts = StockAlert.objects.filter(
        alert_type='low_stock',
        resolved=False
    ).select_related('medicine_stock', 'medicine_stock__medicine', 'medicine_stock__shop')
    
    expiring_alerts = StockAlert.objects.filter(
        alert_type='expiring',
        resolved=False
    ).select_related('medicine_stock', 'medicine_stock__medicine', 'medicine_stock__shop')
    
    expired_alerts = StockAlert.objects.filter(
        alert_type='expired',
        resolved=False
    ).select_related('medicine_stock', 'medicine_stock__medicine', 'medicine_stock__shop')
    
    search_query = request.GET.get('search')
    if search_query:
        low_stock_alerts = low_stock_alerts.filter(
            Q(medicine_stock__medicine__name__icontains=search_query) |
            Q(medicine_stock__shop__name__icontains=search_query)
        )
    
    context = {
        'low_stock_alerts': low_stock_alerts,
        'expiring_alerts': expiring_alerts,
        'expired_alerts': expired_alerts,
    }
    return render(request, 'inventory/alerts.html', context)

# add sales sales_add

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Medicine, Shop, MedicineStock, MedicineSale

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Medicine, Shop, MedicineStock, MedicineSale

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Medicine, Shop, MedicineStock, MedicineSale


def sales_add(request):
    if request.method == "POST":
        try:
            # Extract data from the form
            medicine_id = request.POST.get('medicine_id')
            shop_id = request.POST.get('shop_id')
            quantity = int(request.POST.get('quantity'))
            payment_method = request.POST.get('payment_method')
            customer_name = request.POST.get('customer_name', '')
            customer_phone = request.POST.get('customer_phone', '')

            # Fetch related objects
            medicine = get_object_or_404(Medicine, primary_id=medicine_id)
            shop = get_object_or_404(Shop, id=shop_id)
            
            # Fetch the MedicineStock object
            stocks = MedicineStock.objects.filter(medicine=medicine, shop=shop)
            if stocks.count() > 1:
                messages.error(request, "Multiple stock records found for the selected medicine and shop. Please resolve duplicates.")
                return redirect('sales_add')
            
            stock = stocks.first()
            if not stock:
                messages.error(request, "Stock not found for the selected medicine and shop.")
                return redirect('sales_add')

            # Validate stock availability
            if stock.quantity < quantity:
                messages.error(request, "Insufficient stock for this sale.")
                return redirect('sales_add')

            # Calculate total amount
            total_amount = quantity * stock.price

            # Create the sale record
            MedicineSale.objects.create(
                medicine=medicine,
                shop=shop,
                stock=stock,
                quantity=quantity,
                unit_price=stock.price,
                total_amount=total_amount,
                payment_method=payment_method,
                customer_name=customer_name,
                customer_phone=customer_phone,
            )

            # Update stock quantity
            stock.quantity -= quantity
            stock.save()

            # Fetch recent sales for the modal
            recent_sales = MedicineSale.objects.filter(shop=shop).order_by('-date')[:10]
            sales_data = [{
                'medicine': sale.medicine.name,
                'shop': sale.shop.name,
                'quantity': sale.quantity,
                'total': float(sale.total_amount),
                'customer': sale.customer_name or 'N/A',
                'payment_method': sale.get_payment_method_display(),
                'timestamp': sale.date.strftime("%d %b %Y %H:%M")
            } for sale in recent_sales]

            # Return JSON response for AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'sales': sales_data
                })

            messages.success(request, "Sale added successfully.")
            return redirect('sales_list')

        except Exception as e:
            messages.error(request, f"Error adding sale: {str(e)}")
            return redirect('sales_add')

    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            recent_sales = MedicineSale.objects.all().order_by('-date')[:10]
            sales_data = [{
                'medicine': sale.medicine.name,
                'shop': sale.shop.name,
                'quantity': sale.quantity,
                'total': float(sale.total_amount),
                'customer': sale.customer_name or 'N/A',
                'payment_method': sale.get_payment_method_display(),
                'timestamp': sale.date.strftime("%d %b %Y %H:%M")
            } for sale in recent_sales]
            
            return JsonResponse({
                'success': True,
                'sales': sales_data
            })
        
        # Regular GET request (render form)
        medicines = Medicine.objects.all()
        shops = Shop.objects.all()
        context = {
            'medicines': medicines,
            'shops': shops,
        }
        return render(request, 'inventory/record_sale.html', context)
# def sales_add(request):
#     try:
#         sales = Shop.objects.create(
            
#             # name=request.POST['name'],
#             # location=request.POST['location'],
#             # contact_number=request.POST['contact_number'],
#             # license_number=request.POST['license_number'],
#             # opening_time='09:00:00',  # Default opening time
#             # closing_time='21:00:00'   # Default closing time
#         )
#         messages.success(request, f"Shop '{sales.name}' added successfully")
#     except Exception as e:
#         messages.error(request, f"Error adding sales: {str(e)}")
#     # return redirect('shop_list')
#     return render(request, 'inventory/sales/add.html')

# 
# 
# 
def sales_list(request):
    sales = MedicineSale.objects.all()
    sales_filter = SaleFilter(request.GET, queryset=sales)

    context = {
        'filter': sales_filter,
        'sales': sales_filter.qs
    }
    return render(request, 'inventory/sales/list.html', context)
    
def sales_analysis(request):
    # Base Metrics
    total_sales = MedicineSale.objects.aggregate(
        total_amount=Sum('total_amount'),
        total_quantity=Sum('quantity')
    )
    
    avg_transaction = total_sales['total_amount'] / MedicineSale.objects.count() if MedicineSale.objects.count() > 0 else 0

    # Weekly Trends (SQLite compatible)
    weekly_trends = MedicineSale.objects.annotate(
        week=ExtractWeek('date'),
        year=ExtractYear('date')
    ).values('year', 'week').annotate(
        total_sales=Sum('total_amount')
    ).order_by('-year', '-week')[:12]

    # Calculate 3-week moving average in Python
    sales_values = [w['total_sales'] or 0 for w in weekly_trends]
    moving_avg = []
    for i in range(len(sales_values)):
        if i < 2:  # First two weeks don't have enough data
            moving_avg.append(None)
        else:
            avg = sum(sales_values[i-2:i+1]) / 3
            moving_avg.append(round(avg, 2))

    # Stock Aging Analysis (Corrected)
    stock_aging = MedicineStock.objects.annotate(
        duration=ExpressionWrapper(
            timezone.now() - F('last_restocked'),
            output_field=DurationField()
        ),
        days_in_stock=ExtractDay('duration')
    ).values('medicine__name').annotate(
        avg_days=Avg('days_in_stock')
    ).order_by('-avg_days')[:10]

    # Customer Loyalty Metrics
    loyal_customers = MedicineSale.objects.exclude(customer_phone='').values(
        'customer_phone', 'customer_name'
    ).annotate(
        total_spent=Sum('total_amount'),
        visit_count=Count('id'),
        last_visit=Max('date')
    ).order_by('-total_spent')[:10]

    context = {
        'total_sales': {
            'total_amount': total_sales.get('total_amount', 0) or 0,
            'total_quantity': total_sales.get('total_quantity', 0) or 0,
            'avg_transaction': avg_transaction
        },
        'payment_stats': MedicineSale.objects.values('payment_method').annotate(
            count=Count('id'),
            total=Sum('total_amount')
        ),
        'top_medicines': MedicineSale.objects.values(
            'medicine__name', 'medicine__primary_id'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_amount=Sum('total_amount')
        ).order_by('-total_quantity')[:10],
        'shop_analysis': Shop.objects.annotate(
            total_sales=Sum('medicinesale__total_amount'),
            total_quantity=Sum('medicinesale__quantity'),
            unique_medicines=Count('medicinestock__medicine', distinct=True)
        ),
        'medicine_by_shop': MedicineSale.objects.values(
            'medicine__name', 'shop__name'
        ).annotate(
            total_quantity=Sum('quantity'),
            total_amount=Sum('total_amount')
        ).order_by('shop__name', '-total_quantity'),
        'weekly_trends': zip(weekly_trends, moving_avg),
        'stock_aging': stock_aging,
        'loyal_customers': loyal_customers
    }
    return render(request, 'inventory/sales/analysis.html', context)

# API endpoints for AJAX calls
def medicine_sales_chart(request, primary_id):
    medicine = get_object_or_404(Medicine, primary_id=primary_id)
    sales_data = MedicineSale.objects.filter(
        medicine=medicine
    ).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('total_amount'),
        quantity=Sum('quantity')
    ).order_by('month')
    
    return JsonResponse({
        'labels': [item['month'].strftime('%B %Y') for item in sales_data],
        'amounts': [float(item['total']) for item in sales_data],
        'quantities': [item['quantity'] for item in sales_data]
    })

def shop_sales_chart(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    sales_data = MedicineSale.objects.filter(
        shop=shop
    ).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('total_amount')
    ).order_by('month')
    
    return JsonResponse({
        'labels': [item['month'].strftime('%B %Y') for item in sales_data],
        'data': [float(item['total']) for item in sales_data]
    }) 

@require_POST
def medicine_edit(request, primary_id):
    medicine = get_object_or_404(Medicine, primary_id=primary_id)
    # Add form handling logic here
    messages.success(request, f"{medicine.name} updated successfully")
    return redirect('medicine_detail', primary_id=primary_id)

@require_POST
def medicine_delete(request, primary_id):
    medicine = get_object_or_404(Medicine, primary_id=primary_id)
    name = medicine.name
    medicine.delete()
    messages.success(request, f"{name} deleted successfully")
    return redirect('medicine_list') 

@require_POST
def add_stock(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    # Add stock logic here
    messages.success(request, "Stock added successfully")
    return redirect('shop_detail', shop_id=shop_id)

@require_POST
def edit_stock(request, shop_id, stock_id):
    stock = get_object_or_404(MedicineStock, id=stock_id, shop_id=shop_id)
    # Edit stock logic here
    messages.success(request, "Stock updated successfully")
    return redirect('shop_detail', shop_id=shop_id) 

@require_POST
def medicine_add(request):
    try:
        medicine = Medicine.objects.create(
            primary_id=request.POST['primary_id'],
            name=request.POST['name'],
            generic_name=request.POST['generic_name'],
            category=request.POST['category'],
            manufacturer=request.POST['manufacturer'],
            description=request.POST.get('description', ''),
            side_effects=request.POST.get('side_effects', '')
        )
        messages.success(request, f"Medicine '{medicine.name}' added successfully")
    except Exception as e:
        messages.error(request, f"Error adding medicine: {str(e)}")
    return redirect('medicine_list')

@require_POST
def shop_add(request):
    try:
        shop = Shop.objects.create(
            name=request.POST['name'],
            location=request.POST['location'],
            contact_number=request.POST['contact_number'],
            license_number=request.POST['license_number'],
            opening_time='09:00:00',  # Default opening time
            closing_time='21:00:00'   # Default closing time
        )
        messages.success(request, f"Shop '{shop.name}' added successfully")
    except Exception as e:
        messages.error(request, f"Error adding shop: {str(e)}")
    return redirect('shop_list')

@require_POST
def shop_edit(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    try:
        shop.name = request.POST['name']
        shop.location = request.POST['location']
        shop.contact_number = request.POST['contact_number']
        shop.license_number = request.POST['license_number']
        shop.save()
        messages.success(request, f"Shop '{shop.name}' updated successfully")
    except Exception as e:
        messages.error(request, f"Error updating shop: {str(e)}")
    return redirect('shop_list') 

@require_POST
def resolve_alert(request, alert_id):
    alert = get_object_or_404(StockAlert, id=alert_id)
    alert.resolved = True
    alert.resolved_at = timezone.now()
    alert.save()
    messages.success(request, "Alert marked as resolved")
    return redirect('stock_alerts') 