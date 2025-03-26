from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Count, Avg, F, Q, Window, Case, When,Max,ExpressionWrapper,DurationField
from django.db.models.functions import TruncMonth, ExtractHour, ExtractWeek, ExtractYear,ExtractDay
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal

from .models import Medicine, Shop, MedicineStock, MedicineSale, StockAlert, TransactionLog
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
            expiry_date__lte=timezone.now().date() + timedelta(days=20),
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
    # Get all active alerts from StockAlert model
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
    
    # Direct database checks for conditions that should trigger alerts
    # This will catch any stocks that should have alerts but don't
    
    # 1. Check for low stock items without alerts
    low_stock_items = MedicineStock.objects.filter(
        quantity__lte=F('reorder_level')
    ).exclude(
        id__in=low_stock_alerts.values('medicine_stock_id')
    )
    
    # Create missing low stock alerts
    for stock in low_stock_items:
        StockAlert.objects.get_or_create(
            medicine_stock=stock,
            alert_type='low_stock',
            resolved=False,
            defaults={
                'message': f"Low stock alert for {stock.medicine.name} at {stock.shop.name}. Current quantity: {stock.quantity}"
            }
        )
    
    # 2. Check for expiring items without alerts
    thirty_days_from_now = timezone.now().date() + timedelta(days=30)
    expiring_items = MedicineStock.objects.filter(
        expiry_date__lte=thirty_days_from_now,
        expiry_date__gt=timezone.now().date()
    ).exclude(
        id__in=expiring_alerts.values('medicine_stock_id')
    )
    
    # Create missing expiring alerts
    for stock in expiring_items:
        StockAlert.objects.get_or_create(
            medicine_stock=stock,
            alert_type='expiring',
            resolved=False,
            defaults={
                'message': f"Stock expiring soon for {stock.medicine.name} at {stock.shop.name}. Expires on: {stock.expiry_date}"
            }
        )
    
    # 3. Check for expired items without alerts
    expired_items = MedicineStock.objects.filter(
        expiry_date__lte=timezone.now().date()
    ).exclude(
        id__in=expired_alerts.values('medicine_stock_id')
    )
    
    # Create missing expired alerts
    for stock in expired_items:
        StockAlert.objects.get_or_create(
            medicine_stock=stock,
            alert_type='expired',
            resolved=False,
            defaults={
                'message': f"Stock expired for {stock.medicine.name} at {stock.shop.name}. Expired on: {stock.expiry_date}"
            }
        )
    
    # Refresh the alert queries to include newly created alerts
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
        expiring_alerts = expiring_alerts.filter(
            Q(medicine_stock__medicine__name__icontains=search_query) |
            Q(medicine_stock__shop__name__icontains=search_query)
        )
        expired_alerts = expired_alerts.filter(
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
            sale = MedicineSale.objects.create(
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

            # Update stock quantity and properly save to trigger alerts
            stock.quantity -= quantity
            stock.save()  # This will trigger check_and_create_alerts()
            
            # Log the transaction
            TransactionLog.objects.create(
                action_type='sale',
                description=f"Sale of {quantity} units of {medicine.name} at {shop.name}",
                medicine=medicine,
                shop=shop,
                quantity=quantity,
                amount=total_amount
            )

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
    # Date range selection (default to last 30 days if not specified)
    end_date = timezone.now().date()
    start_date = request.GET.get('start_date', None)
    end_date_param = request.GET.get('end_date', None)
    
    if start_date and end_date_param:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
        except ValueError:
            start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(days=30)
    
    # Get sales within date range
    sales_query = MedicineSale.objects.filter(
        date__date__gte=start_date,
        date__date__lte=end_date
    )
    
    # Base Metrics
    total_sales = sales_query.aggregate(
        total_amount=Sum('total_amount'),
        total_quantity=Sum('quantity'),
        total_transactions=Count('id')
    )
    
    avg_transaction = total_sales['total_amount'] / total_sales['total_transactions'] if total_sales['total_transactions'] > 0 else 0

    # Weekly Trends (SQLite compatible)
    weekly_trends = sales_query.annotate(
        week=ExtractWeek('date'),
        year=ExtractYear('date')
    ).values('year', 'week').annotate(
        total_sales=Sum('total_amount')
    ).order_by('year', 'week')
    
    # Calculate 3-week moving average
    sales_values = [w['total_sales'] or 0 for w in weekly_trends]
    moving_avg = []
    for i in range(len(sales_values)):
        if i < 2:  # First two weeks don't have enough data
            moving_avg.append(None)
        else:
            avg = sum(sales_values[i-2:i+1]) / 3
            moving_avg.append(round(avg, 2))

    # Shop Performance Analysis with improved metrics
    all_shops = Shop.objects.all()
    
    # Get performance for each shop within date range
    shop_performance = []
    total_amount = total_sales['total_amount'] or Decimal('0.0')
    total_quantity = total_sales['total_quantity'] or 0
    
    for shop in all_shops:
        # Current period metrics
        current_metrics = sales_query.filter(shop=shop).aggregate(
            sales_amount=Sum('total_amount') or Decimal('0.0'),
            sales_quantity=Sum('quantity') or 0,
            transaction_count=Count('id'),
            avg_transaction=Avg('total_amount'),
            unique_customers=Count('customer_phone', distinct=True, filter=~Q(customer_phone='')),
            unique_medicines=Count('medicine', distinct=True)
        )
        
        # Previous period metrics (for trend comparison)
        previous_start = start_date - timedelta(days=(end_date - start_date).days)
        previous_end = start_date - timedelta(days=1)
        
        previous_metrics = MedicineSale.objects.filter(
            shop=shop,
            date__date__gte=previous_start,
            date__date__lte=previous_end
        ).aggregate(
            sales_amount=Sum('total_amount') or Decimal('0.0')
        )
        
        # Calculate trend (percentage change)
        prev_amount = previous_metrics['sales_amount'] or Decimal('0.0')
        current_amount = current_metrics['sales_amount'] or Decimal('0.0')
        
        if prev_amount > 0:
            trend_pct = ((current_amount - prev_amount) / prev_amount) * 100
        else:
            trend_pct = 100 if current_amount > 0 else 0
        
        # Calculate market share
        market_share = (current_amount / total_amount * 100) if total_amount > 0 else 0
        
        # Calculate sales per day
        days_in_period = (end_date - start_date).days + 1
        sales_per_day = current_amount / days_in_period if days_in_period > 0 else 0
        
        # Calculate revenue per medicine
        rev_per_medicine = current_amount / current_metrics['unique_medicines'] if current_metrics['unique_medicines'] > 0 else 0
        
        # Monthly sales trend
        monthly_trend = sales_query.filter(shop=shop).annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Sum('total_amount')
        ).order_by('month')
        
        shop_performance.append({
            'id': shop.id,
            'name': shop.name,
            'location': shop.location,
            'sales_amount': current_amount,
            'sales_quantity': current_metrics['sales_quantity'] or 0,
            'transaction_count': current_metrics['transaction_count'] or 0,
            'unique_medicines': current_metrics['unique_medicines'] or 0,
            'unique_customers': current_metrics['unique_customers'] or 0,
            'market_share': round(market_share, 2),
            'sales_per_day': round(sales_per_day, 2),
            'revenue_per_medicine': round(rev_per_medicine, 2),
            'trend_pct': round(trend_pct, 2),
            'monthly_trend': list(monthly_trend),
            'avg_transaction': current_metrics['avg_transaction'] or 0
        })
    
    # Sort shop performance by sales amount (descending)
    shop_performance.sort(key=lambda x: x['sales_amount'], reverse=True)
    
    # Top selling medicines with shop breakdown
    top_medicines = sales_query.values(
        'medicine__name', 'medicine__primary_id'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_amount=Sum('total_amount')
    ).order_by('-total_amount')[:10]
    
    # Medicine performance by shop (improved sorting)
    medicine_by_shop = sales_query.values(
        'medicine__name', 'shop__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_amount=Sum('total_amount')
    ).order_by('-total_amount')  # Sort by revenue (better for analysis)
    
    # Stock Aging Analysis
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
    loyal_customers = sales_query.exclude(customer_phone='').values(
        'customer_phone', 'customer_name'
    ).annotate(
        total_spent=Sum('total_amount'),
        visit_count=Count('id'),
        last_visit=Max('date')
    ).order_by('-total_spent')[:10]

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': {
            'total_amount': total_sales.get('total_amount', 0) or 0,
            'total_quantity': total_sales.get('total_quantity', 0) or 0,
            'total_transactions': total_sales.get('total_transactions', 0) or 0,
            'avg_transaction': avg_transaction
        },
        'payment_stats': sales_query.values('payment_method').annotate(
            count=Count('id'),
            total=Sum('total_amount')
        ),
        'top_medicines': top_medicines,
        'shop_performance': shop_performance,
        'medicine_by_shop': medicine_by_shop,
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
    try:
        old_name = medicine.name
        
        # Update medicine fields here
        medicine.name = request.POST.get('name', medicine.name)
        medicine.generic_name = request.POST.get('generic_name', medicine.generic_name)
        medicine.manufacturer = request.POST.get('manufacturer', medicine.manufacturer)
        medicine.category = request.POST.get('category', medicine.category)
        medicine.description = request.POST.get('description', medicine.description)
        medicine.side_effects = request.POST.get('side_effects', medicine.side_effects)
        medicine.save()
        
        # Log the medicine edit
        TransactionLog.objects.create(
            action_type='medicine_edit',
            description=f"Updated medicine details from '{old_name}' to '{medicine.name}'",
            medicine=medicine
        )
        
        messages.success(request, f"{medicine.name} updated successfully")
    except Exception as e:
        messages.error(request, f"Error updating medicine: {str(e)}")
    return redirect('medicine_detail', primary_id=primary_id)

@require_POST
def medicine_delete(request, primary_id):
    medicine = get_object_or_404(Medicine, primary_id=primary_id)
    name = medicine.name
    try:
        # Log the medicine deletion before deleting the object
        TransactionLog.objects.create(
            action_type='medicine_delete',
            description=f"Deleted medicine: {name} (ID: {primary_id})"
            # Note: we can't link to the medicine as it will be deleted
        )
        
        medicine.delete()
        messages.success(request, f"{name} deleted successfully")
    except Exception as e:
        messages.error(request, f"Error deleting medicine: {str(e)}")
    return redirect('medicine_list')

@require_POST
def add_stock(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    try:
        # Get the stock object if it's a restock
        stock_id = request.POST.get('stock_id')
        if stock_id:
            stock = get_object_or_404(MedicineStock, id=stock_id, shop=shop)
            quantity = int(request.POST.get('quantity', 0))
            if quantity > 0:
                old_quantity = stock.quantity
                stock.quantity += quantity
                stock.last_restocked = timezone.now()
                stock.save()  # This will trigger alert checks
                
                # Log the stock addition
                TransactionLog.objects.create(
                    action_type='stock_add',
                    description=f"Added {quantity} units to {stock.medicine.name} stock at {shop.name}. New total: {stock.quantity}",
                    medicine=stock.medicine,
                    shop=shop,
                    quantity=quantity
                )
        else:
            # Handle adding new stock
            # ... existing logic
            pass
        
        # Check if we need to refresh alerts (from the alert page)
        if request.POST.get('refresh_alerts') == 'true':
            return redirect('stock_alerts')
            
        messages.success(request, "Stock added successfully")
        return redirect('shop_detail', shop_id=shop_id)
    except Exception as e:
        messages.error(request, f"Error adding stock: {str(e)}")
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
        
        # Log the medicine addition
        TransactionLog.objects.create(
            action_type='medicine_add',
            description=f"Added new medicine: {medicine.name} (ID: {medicine.primary_id})",
            medicine=medicine
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
        
        # Log the shop addition
        TransactionLog.objects.create(
            action_type='shop_add',
            description=f"Added new shop: {shop.name} at {shop.location}",
            shop=shop
        )
        
        messages.success(request, f"Shop '{shop.name}' added successfully")
    except Exception as e:
        messages.error(request, f"Error adding shop: {str(e)}")
    return redirect('shop_list')

@require_POST
def shop_edit(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    try:
        old_name = shop.name
        old_location = shop.location
        
        shop.name = request.POST['name']
        shop.location = request.POST['location']
        shop.contact_number = request.POST['contact_number']
        shop.license_number = request.POST['license_number']
        shop.save()
        
        # Log the shop edit
        TransactionLog.objects.create(
            action_type='shop_edit',
            description=f"Updated shop details from '{old_name} at {old_location}' to '{shop.name} at {shop.location}'",
            shop=shop
        )
        
        messages.success(request, f"Shop '{shop.name}' updated successfully")
    except Exception as e:
        messages.error(request, f"Error updating shop: {str(e)}")
    return redirect('shop_list') 

@require_POST
def resolve_alert(request, alert_id):
    alert = get_object_or_404(StockAlert, id=alert_id)
    stock = alert.medicine_stock
    
    # Check if the underlying condition is actually fixed
    if alert.alert_type == 'low_stock' and stock.quantity <= stock.reorder_level:
        messages.warning(request, f"Cannot resolve low stock alert - {stock.medicine.name} is still below reorder level. Please restock first.")
        return redirect('stock_alerts')
    
    elif alert.alert_type == 'expiring' and 0 < (stock.expiry_date - timezone.now().date()).days <= 30:
        # For expiring items, we allow resolution even if the condition persists
        # since this might be accepted by the pharmacy
        pass
    
    elif alert.alert_type == 'expired' and stock.expiry_date <= timezone.now().date():
        # For expired items, ensure stock is zero or update the user
        if stock.quantity > 0:
            messages.warning(request, f"Warning: Resolving expired stock alert for {stock.medicine.name} with remaining quantity. Please dispose of expired stock.")
    
    # Mark the alert as resolved
    alert.resolved = True
    alert.resolved_at = timezone.now()
    alert.save()
    
    # Log the alert resolution
    TransactionLog.objects.create(
        action_type='alert_resolved',
        description=f"Resolved {alert.get_alert_type_display()} alert for {stock.medicine.name} at {stock.shop.name}",
        medicine=stock.medicine,
        shop=stock.shop
    )
    
    messages.success(request, "Alert marked as resolved")
    return redirect('stock_alerts')

def make_purchase(request):
    """
    View for making purchases (adding stock with different purchase rates) by shop
    """
    # Get all shops and medicines for the form
    shops = Shop.objects.all().order_by('name')
    medicines = Medicine.objects.all().order_by('name')
    
    context = {
        'shops': shops,
        'medicines': medicines,
        'today': timezone.now(),
    }
    
    if request.method == 'POST':
        try:
            # Get form data
            shop_id = request.POST.get('shop_id')
            purchase_date = request.POST.get('purchase_date') or timezone.now().date()
            
            # Get arrays of medicine data
            medicine_ids = request.POST.getlist('medicine_id[]')
            quantities = request.POST.getlist('quantity[]')
            purchase_prices = request.POST.getlist('purchase_price[]')
            selling_prices = request.POST.getlist('selling_price[]')
            batch_numbers = request.POST.getlist('batch_number[]')
            expiry_dates = request.POST.getlist('expiry_date[]')
            
            if not shop_id:
                messages.error(request, "Please select a shop")
                return redirect('make_purchase')
            
            shop = Shop.objects.get(id=shop_id)
            
            # Process each medicine entry
            for i in range(len(medicine_ids)):
                medicine_id = medicine_ids[i]
                quantity = int(quantities[i])
                purchase_price = Decimal(purchase_prices[i])
                selling_price = Decimal(selling_prices[i])
                batch_number = batch_numbers[i]
                
                # Convert expiry_date string to date object
                expiry_date_str = expiry_dates[i]
                try:
                    expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                except ValueError:
                    messages.error(request, f"Invalid expiry date format for medicine at row {i+1}")
                    return redirect('make_purchase')
                
                # Check if this is a new medicine to add
                if medicine_id == 'new':
                    # Get new medicine data
                    new_med_id = request.POST.get(f'new_med_id_{i}')
                    new_med_name = request.POST.get(f'new_med_name_{i}')
                    new_med_generic = request.POST.get(f'new_med_generic_{i}')
                    new_med_category = request.POST.get(f'new_med_category_{i}')
                    new_med_manufacturer = request.POST.get(f'new_med_manufacturer_{i}')
                    
                    # Create new medicine
                    medicine = Medicine.objects.create(
                        primary_id=new_med_id,
                        name=new_med_name,
                        generic_name=new_med_generic,
                        category=new_med_category,
                        manufacturer=new_med_manufacturer
                    )
                    messages.success(request, f"Added new medicine: {new_med_name}")
                    
                    # Log new medicine addition
                    TransactionLog.objects.create(
                        action_type='medicine_add',
                        description=f"Added new medicine: {new_med_name} (ID: {new_med_id})",
                        medicine=medicine
                    )
                else:
                    # Get existing medicine
                    medicine = Medicine.objects.get(primary_id=medicine_id)
                
                # Check if stock for this batch already exists
                stock, created = MedicineStock.objects.get_or_create(
                    medicine=medicine,
                    shop=shop,
                    batch_number=batch_number,
                    defaults={
                        'expiry_date': expiry_date,
                        'quantity': quantity,
                        'purchase_price': purchase_price,
                        'price': selling_price,
                    }
                )
                
                # If stock already exists, update it
                if not created:
                    old_quantity = stock.quantity
                    stock.purchase_price = purchase_price
                    stock.price = selling_price
                    stock.expiry_date = expiry_date
                    stock.quantity += quantity
                    stock.save()
                    
                    # Log stock update
                    TransactionLog.objects.create(
                        action_type='stock_update',
                        description=f"Updated stock of {medicine.name} at {shop.name}. Added {quantity} units to existing {old_quantity} units.",
                        medicine=medicine,
                        shop=shop,
                        quantity=quantity,
                        amount=purchase_price * quantity
                    )
                else:
                    # Log new stock addition
                    TransactionLog.objects.create(
                        action_type='purchase',
                        description=f"Purchased {quantity} units of {medicine.name} for {shop.name}. Batch: {batch_number}, Expiry: {expiry_date}",
                        medicine=medicine,
                        shop=shop,
                        quantity=quantity,
                        amount=purchase_price * quantity
                    )
                
            messages.success(request, "Purchase completed successfully")
            return redirect('make_purchase')
            
        except Shop.DoesNotExist:
            messages.error(request, "Shop not found")
        except Medicine.DoesNotExist:
            messages.error(request, "Medicine not found")
        except Exception as e:
            messages.error(request, f"Error processing purchase: {str(e)}")
    
    return render(request, 'inventory/purchase/make_purchase.html', context) 

def transaction_logs(request):
    """
    View to display all transaction logs with filtering options
    """
    logs = TransactionLog.objects.all()
    
    # Filter by action type if specified
    action_type = request.GET.get('action_type')
    if action_type:
        logs = logs.filter(action_type=action_type)
    
    # Filter by date range if specified
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            # Add a day to end_date to include the entire day
            end_date = end_date + timedelta(days=1)
            logs = logs.filter(created_at__gte=start_date, created_at__lt=end_date)
        except ValueError:
            messages.error(request, "Invalid date format. Please use YYYY-MM-DD format.")
    
    # Filter by shop if specified
    shop_id = request.GET.get('shop_id')
    if shop_id:
        logs = logs.filter(shop_id=shop_id)
    
    # Filter by medicine if specified
    medicine_id = request.GET.get('medicine_id')
    if medicine_id:
        logs = logs.filter(medicine_id=medicine_id)
    
    # Get all action types for the filter dropdown
    action_types = [choice[0] for choice in TransactionLog.ACTION_TYPES]
    
    # Get all shops and medicines for filter dropdowns
    shops = Shop.objects.all()
    medicines = Medicine.objects.all()
    
    context = {
        'logs': logs,
        'action_types': action_types,
        'shops': shops,
        'medicines': medicines,
    }
    
    return render(request, 'inventory/logs.html', context) 