from django.contrib import admin
from .models import Medicine, Shop, MedicineStock, MedicineSale, StockAlert

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('primary_id', 'name', 'generic_name', 'category', 'manufacturer')
    search_fields = ('name', 'generic_name', 'primary_id')
    list_filter = ('category', 'manufacturer')

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'contact_number', 'license_number')
    search_fields = ('name', 'location', 'license_number')

@admin.register(MedicineStock)
class MedicineStockAdmin(admin.ModelAdmin):
    list_display = ('medicine', 'shop', 'batch_number', 'quantity', 'price', 'expiry_date')
    list_filter = ('shop', 'medicine__category')
    search_fields = ('medicine__name', 'batch_number')
    date_hierarchy = 'expiry_date'

@admin.register(MedicineSale)
class MedicineSaleAdmin(admin.ModelAdmin):
    list_display = ('medicine', 'shop', 'quantity', 'total_amount', 'payment_method', 'date')
    list_filter = ('shop', 'payment_method', 'date')
    search_fields = ('medicine__name', 'customer_name', 'customer_phone')
    date_hierarchy = 'date'

@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ('medicine_stock', 'alert_type', 'created_at', 'resolved')
    list_filter = ('alert_type', 'resolved')
    search_fields = ('medicine_stock__medicine__name', 'message')
    date_hierarchy = 'created_at' 