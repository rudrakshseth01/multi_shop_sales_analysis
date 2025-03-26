from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Medicines
    path('medicines/', views.medicine_list, name='medicine_list'),
    path('medicines/<str:primary_id>/', views.medicine_detail, name='medicine_detail'),
    path('medicines/<str:primary_id>/edit/', views.medicine_edit, name='medicine_edit'),
    path('medicines/<str:primary_id>/delete/', views.medicine_delete, name='medicine_delete'),
    path('medicines/add/', views.medicine_add, name='medicine_add'),
    
    # Shops
    path('shops/', views.shop_list, name='shop_list'),
    path('shops/<int:shop_id>/', views.shop_detail, name='shop_detail'),
    path('shops/<int:shop_id>/add-stock/', views.add_stock, name='add_stock'),
    path('shops/<int:shop_id>/edit-stock/<int:stock_id>/', views.edit_stock, name='edit_stock'),
    path('shops/add/', views.shop_add, name='shop_add'),
    path('shops/<int:shop_id>/edit/', views.shop_edit, name='shop_edit'),
    
    # Alerts
    path('alerts/', views.stock_alerts, name='stock_alerts'),
    path('alerts/<int:alert_id>/resolve/', views.resolve_alert, name='resolve_alert'),
    
    # Sales Analysis
    path('sales/analysis/', views.sales_analysis, name='sales_analysis'),
    
    # add sales
    path('sales/add/', views.sales_add, name='sales_add'),
    path('sales/', views.sales_list, name='sales_list'),
    
    # API endpoints
    path('api/medicine/<str:primary_id>/sales/', views.medicine_sales_chart, name='medicine_sales_chart'),
    path('api/shop/<int:shop_id>/sales/', views.shop_sales_chart, name='shop_sales_chart'),
] 