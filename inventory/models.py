# from django.db import models
# from django.utils import timezone
# from django.core.validators import (
#     MinValueValidator, 
#     RegexValidator,
#     FileExtensionValidator
# )
# from django.db.models import Sum, F
# from django.core.exceptions import ValidationError
# from decimal import Decimal
# from django.db import transaction
# from django.db import models
# from django.core.validators import MinValueValidator
# from django.core.exceptions import ValidationError
# from django.utils import timezone
# from decimal import Decimal
# from .models import Medicine, Shop, StockAlert
# class Medicine(models.Model):
#     """
#     Model to store medicine information.
#     Primary key is a custom medicine ID (e.g., MED001) instead of auto-incrementing number.
#     """
#     CATEGORY_CHOICES = [
#         ('tablet', 'Tablet'),
#         ('syrup', 'Syrup'),
#         ('injection', 'Injection'),
#         ('cream', 'Cream'),
#         ('drops', 'Drops'),
#     ]

#     # Primary Fields
#     primary_id = models.CharField(
#         max_length=10, 
#         primary_key=True,
#         validators=[
#             RegexValidator(
#                 regex='^MED\d{3}$',
#                 message='Medicine ID must be in format MED001'
#             )
#         ]
#     )
#     name = models.CharField(max_length=100)
#     generic_name = models.CharField(max_length=100)
#     manufacturer = models.CharField(max_length=100)
#     category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
#     description = models.TextField(blank=True)
#     side_effects = models.TextField(blank=True)
    
#     # Metadata
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ['name']
#         indexes = [
#             models.Index(fields=['name']),
#             models.Index(fields=['manufacturer']),
#         ]

#     def __str__(self):
#         return self.name
    
#     def clean(self):
#         """Validate the medicine data"""
#         if not self.name:
#             raise ValidationError('Medicine name is required')
#         if not self.generic_name:
#             raise ValidationError('Generic name is required')
        
#         # Convert names to title case
#         self.name = self.name.title()
#         self.generic_name = self.generic_name.title()
    
#     @property
#     def total_stock(self):
#         """Calculate total stock across all shops"""
#         result = self.medicinestock_set.aggregate(total=Sum('quantity'))
#         return result['total'] or 0
    
#     @property
#     def total_sales(self):
#         """Calculate total sales across all shops"""
#         result = self.medicinesale_set.aggregate(total=Sum('quantity'))
#         return result['total'] or 0

# class Shop(models.Model):
#     """
#     Model to store pharmacy/shop information.
#     Each shop can have multiple medicine stocks.
#     """
#     name = models.CharField(max_length=100)
#     location = models.CharField(max_length=200)
#     contact_number = models.CharField(
#         max_length=15,
#         validators=[
#             RegexValidator(
#                 regex=r'^\+?1?\d{9,15}$',
#                 message='Phone number must be entered in format: +999999999'
#             )
#         ]
#     )
#     license_number = models.CharField(
#         max_length=50,
#         unique=True,
#         validators=[
#             RegexValidator(
#                 regex=r'^LIC\d{7}$',
#                 message='License number must be in format LIC0000000'
#             )
#         ]
#     )
#     opening_time = models.TimeField()
#     closing_time = models.TimeField()
#     opening_date = models.DateField(default=timezone.now)
    
#     class Meta:
#         ordering = ['name']
#         indexes = [
#             models.Index(fields=['name']),
#             models.Index(fields=['license_number']),
#         ]

#     def clean(self):
#         """Validate shop data"""
#         if self.opening_time >= self.closing_time:
#             raise ValidationError('Opening time must be before closing time')
        
#         # Convert name to title case
#         self.name = self.name.title()
    
#     @property
#     def total_revenue(self):
#         """Calculate total revenue from all sales"""
#         return self.medicinesale_set.aggregate(
#             total=Sum('total_amount')
#         )['total'] or Decimal('0.00')
    
#     @property
#     def low_stock_count(self):
#         """Count items with stock below reorder level"""
#         return self.medicinestock_set.filter(
#             quantity__lte=models.F('reorder_level')
#         ).count()

# from django.db import models
# from django.core.validators import MinValueValidator
# from django.core.exceptions import ValidationError
# from django.utils import timezone
# from decimal import Decimal
# from .models import Medicine, Shop, StockAlert

# class MedicineStock(models.Model):
#     """
#     Model to track medicine stock in each shop.
#     Links medicines to shops and tracks quantity, price, and expiry.
#     """
#     medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
#     shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
#     batch_number = models.CharField(max_length=50)
#     expiry_date = models.DateField()
#     quantity = models.IntegerField(validators=[MinValueValidator(0)])
#     price = models.DecimalField(
#         max_digits=10, 
#         decimal_places=2,
#         validators=[MinValueValidator(Decimal('0.01'))]
#     )
#     reorder_level = models.IntegerField(default=10)
#     last_restocked = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.medicine.name} at {self.shop.name} (Batch: {self.batch_number})"

#     @property
#     def total_value(self):
#         return self.quantity * self.price

#     @property
#     def is_expired(self):
#         return self.expiry_date <= timezone.now().date()

#     @property
#     def is_low_stock(self):
#         return self.quantity <= self.reorder_level

#     def clean(self):
#         """Validate stock data"""
#         if not self.pk and self.expiry_date <= timezone.now().date():
#             raise ValidationError('Expiry date must be in the future')
#         if self.quantity < 0:
#             raise ValidationError('Quantity cannot be negative')
#         if self.reorder_level < 0:
#             raise ValidationError('Reorder level cannot be negative')
#         if self.price <= 0:
#             raise ValidationError('Price must be greater than zero')

#     def save(self, *args, **kwargs):
#         self.clean()
#         super().save(*args, **kwargs)
#         self.check_and_create_alerts()

#     def check_and_create_alerts(self):
#         """Create alerts for low stock and expiry conditions"""
#         if self.is_low_stock:
#             StockAlert.objects.get_or_create(
#                 medicine_stock=self,
#                 alert_type='low_stock',
#                 resolved=False,
#                 defaults={
#                     'message': f"Low stock alert for {self.medicine.name} at {self.shop.name}. Current quantity: {self.quantity}"
#                 }
#             )

#         days_until_expiry = (self.expiry_date - timezone.now().date()).days
#         if 0 < days_until_expiry <= 30:
#             StockAlert.objects.get_or_create(
#                 medicine_stock=self,
#                 alert_type='expiring',
#                 resolved=False,
#                 defaults={
#                     'message': f"Stock expiring soon for {self.medicine.name} at {self.shop.name}. Expires on: {self.expiry_date}"
#                 }
#             )

#         if self.is_expired:
#             StockAlert.objects.get_or_create(
#                 medicine_stock=self,
#                 alert_type='expired',
#                 resolved=False,
#                 defaults={
#                     'message': f"Stock expired for {self.medicine.name} at {self.shop.name}. Expired on: {self.expiry_date}"
#                 }
#             )

#     def restock(self, quantity):
#         """Restock the medicine and update the last_restocked field"""
#         if quantity <= 0:
#             raise ValidationError('Restock quantity must be greater than zero')
#         self.quantity += quantity
#         self.last_restocked = timezone.now()
#         self.save()

#     def get_expiry_status(self):
#         """Get the expiry status of the stock"""
#         if self.is_expired:
#             return "Expired"
#         days_until_expiry = (self.expiry_date - timezone.now().date()).days
#         if days_until_expiry <= 30:
#             return f"Expiring in {days_until_expiry} days"
#         return "Not Expiring Soon"

#     def get_stock_status(self):
#         """Get the overall stock status"""
#         if self.quantity == 0:
#             return "Out of Stock"
#         elif self.is_low_stock:
#             return "Low Stock"
#         return "In Stock"

#     def get_absolute_url(self):
#         """Get the URL for the stock detail page"""
#         return reverse('medicine_stock_detail', args=[str(self.id)])

#     class Meta:
#         verbose_name = "Medicine Stock"
#         verbose_name_plural = "Medicine Stocks"
#         unique_together = ['medicine', 'shop', 'batch_number']
#         indexes = [
#             models.Index(fields=['medicine', 'shop']),
#             models.Index(fields=['expiry_date']),
#         ]

# # class MedicineStock(models.Model):
#     """
#     Model to track medicine stock in each shop.
#     Links medicines to shops and tracks quantity, price, and expiry.
#     """
#     medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
#     shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
#     batch_number = models.CharField(max_length=50)
#     expiry_date = models.DateField()
#     quantity = models.IntegerField(validators=[MinValueValidator(0)])
#     price = models.DecimalField(
#         max_digits=10, 
#         decimal_places=2,
#         validators=[MinValueValidator(Decimal('0.01'))]
#     )
#     reorder_level = models.IntegerField(default=10)
#     last_restocked = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         unique_together = ['medicine', 'shop', 'batch_number']
#         indexes = [
#             models.Index(fields=['medicine', 'shop']),
#             models.Index(fields=['expiry_date']),
#         ]
    
#     def clean(self):
#         """Validate stock data"""
#         # Only check expiry date for new stock
#         if not self.pk and self.expiry_date <= timezone.now().date():
#             raise ValidationError('Expiry date must be in the future')
#         if self.quantity < 0:
#             raise ValidationError('Quantity cannot be negative')
#         if self.reorder_level < 0:
#             raise ValidationError('Reorder level cannot be negative')
    
#     def save(self, *args, **kwargs):
#         self.clean()
#         super().save(*args, **kwargs)
#         self.check_and_create_alerts()
    
#     def check_and_create_alerts(self):
#         """Create alerts for low stock and expiry conditions"""
#         # Check for low stock
#         if self.quantity <= self.reorder_level:
#             StockAlert.objects.get_or_create(
#                 medicine_stock=self,
#                 alert_type='low_stock',
#                 resolved=False,
#                 defaults={
#                     'message': f"Low stock alert for {self.medicine.name} at {self.shop.name}. Current quantity: {self.quantity}"
#                 }
#             )
        
#         # Check for expiring stock (within 30 days)
#         days_until_expiry = (self.expiry_date - timezone.now().date()).days
#         if 0 < days_until_expiry <= 30:
#             StockAlert.objects.get_or_create(
#                 medicine_stock=self,
#                 alert_type='expiring',
#                 resolved=False,
#                 defaults={
#                     'message': f"Stock expiring soon for {self.medicine.name} at {self.shop.name}. Expires on: {self.expiry_date}"
#                 }
#             )
        
#         # Check for expired stock
#         if self.expiry_date <= timezone.now().date():
#             StockAlert.objects.get_or_create(
#                 medicine_stock=self,
#                 alert_type='expired',
#                 resolved=False,
#                 defaults={
#                     'message': f"Stock expired for {self.medicine.name} at {self.shop.name}. Expired on: {self.expiry_date}"
#                 }
#             )

# class MedicineSale(models.Model):
#     """
#     Model to track medicine sales.
#     Records each sale with quantity, price, and customer information.
#     """
#     PAYMENT_CHOICES = [
#         ('cash', 'Cash'),
#         ('upi', 'UPI'),
#         ('card', 'Card'),
#         ('insurance', 'Insurance'),
#     ]

#     medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
#     shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
#     stock = models.ForeignKey(MedicineStock, on_delete=models.CASCADE)
#     quantity = models.IntegerField(validators=[MinValueValidator(1)])
#     unit_price = models.DecimalField(max_digits=10, decimal_places=2)
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2)
#     payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
#     prescription = models.FileField(
#         upload_to='prescriptions/', 
#         null=True, 
#         blank=True,
#         validators=[
#             FileExtensionValidator(
#                 allowed_extensions=['pdf', 'jpg', 'jpeg', 'png']
#             )
#         ]
#     )
#     customer_name = models.CharField(max_length=100, blank=True)
#     customer_phone = models.CharField(
#         max_length=15,
#         blank=True,
#         validators=[
#             RegexValidator(
#                 regex=r'^\+?1?\d{9,15}$',
#                 message='Phone number must be entered in format: +999999999'
#             )
#         ]
#     )
#     date = models.DateTimeField(auto_now_add=True)
    
#     class Meta:
#         indexes = [
#             models.Index(fields=['medicine', 'shop']),
#             models.Index(fields=['date']),
#         ]

#     def clean(self):
#         """Validate sale data"""
#         if self.quantity > self.stock.quantity:
#             raise ValidationError(f"Not enough stock. Available: {self.stock.quantity}")
#         if self.stock.expiry_date <= timezone.now().date():
#             raise ValidationError("Cannot sell expired medicine")
#         if self.unit_price <= 0:
#             raise ValidationError("Unit price must be greater than zero")

#     def save(self, *args, **kwargs):
#         """Save sale and update stock"""
#         self.clean()
        
#         # Calculate total amount
#         self.unit_price = self.stock.price
#         self.total_amount = self.quantity * self.unit_price
        
#         # Update stock quantity in a transaction
#         with transaction.atomic():
#             stock = MedicineStock.objects.select_for_update().get(id=self.stock.id)
#             if stock.quantity < self.quantity:
#                 raise ValidationError("Stock quantity changed. Please try again.")
            
#             stock.quantity -= self.quantity
#             stock.save()
            
#             super().save(*args, **kwargs)

# class StockAlert(models.Model):
#     """
#     Model to track stock alerts for low quantity and expiry.
#     Helps manage inventory by providing timely notifications.
#     """
#     ALERT_TYPES = [
#         ('low_stock', 'Low Stock'),
#         ('expiring', 'Expiring Soon'),
#         ('expired', 'Expired'),
#     ]

#     medicine_stock = models.ForeignKey(MedicineStock, on_delete=models.CASCADE)
#     alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
#     message = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     resolved = models.BooleanField(default=False)
#     resolved_at = models.DateTimeField(null=True, blank=True)
    
#     class Meta:
#         ordering = ['-created_at']
#         indexes = [
#             models.Index(fields=['alert_type', 'resolved']),
#             models.Index(fields=['created_at']),
#         ]

#     def __str__(self):
#         return f"{self.alert_type} - {self.medicine_stock.medicine.name}"
    
#     def resolve(self):
#         """Mark alert as resolved"""
#         self.resolved = True
#         self.resolved_at = timezone.now()
#         self.save() 

from django.db import models
from django.utils import timezone
from django.core.validators import (
    MinValueValidator, 
    RegexValidator,
    FileExtensionValidator
)
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db import transaction
from django.urls import reverse
from sympy import Sum

from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.db.models import Sum
from decimal import Decimal

class Medicine(models.Model):
    """
    Model to store medicine information.
    Primary key is a custom medicine ID (e.g., MED001) instead of auto-incrementing number.
    """
    CATEGORY_CHOICES = [
        ('tablet', 'Tablet'),
        ('syrup', 'Syrup'),
        ('injection', 'Injection'),
        ('cream', 'Cream'),
        ('drops', 'Drops'),
    ]

    # Primary Fields
    primary_id = models.CharField(
        max_length=10, 
        primary_key=True,
        validators=[
            RegexValidator(
                regex=r'^MED\d{3}$',  # Use raw string for regex
                message='Medicine ID must be in format MED001'
            )
        ]
    )
    name = models.CharField(max_length=100)
    generic_name = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['manufacturer']),
        ]
        verbose_name = "Medicine"
        verbose_name_plural = "Medicines"

    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate the medicine data"""
        if not self.name:
            raise ValidationError('Medicine name is required')
        if not self.generic_name:
            raise ValidationError('Generic name is required')
        
        # Convert names to title case
        self.name = self.name.title()
        self.generic_name = self.generic_name.title()
    
    @property
    def total_stock(self):
        """Calculate total stock across all shops"""
        result = self.medicinestock_set.aggregate(total=Sum('quantity'))
        return result.get('total', 0)  # Return 0 if 'total' is None
    
    @property
    def total_sales(self):
        """Calculate total sales across all shops"""
        result = self.medicinesale_set.aggregate(total=Sum('quantity'))
        return result.get('total', 0)  # Return 0 if 'total' is None

class Shop(models.Model):
    """
    Model to store pharmacy/shop information.
    Each shop can have multiple medicine stocks.
    """
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    contact_number = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Phone number must be entered in format: +999999999'
            )
        ]
    )
    license_number = models.CharField(
        max_length=50,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^LIC\d{7}$',
                message='License number must be in format LIC0000000'
            )
        ]
    )
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    opening_date = models.DateField(default=timezone.now)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['license_number']),
        ]
        verbose_name = "Shop"
        verbose_name_plural = "Shops"

    def __str__(self):
        return self.name

    def clean(self):
        """Validate shop data"""
        if self.opening_time >= self.closing_time:
            raise ValidationError('Opening time must be before closing time')
        
        # Convert name to title case
        self.name = self.name.title()
    
    @property
    def total_revenue(self):
        """Calculate total revenue from all sales"""
        return self.medicinesale_set.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
    
    @property
    def low_stock_count(self):
        """Count items with stock below reorder level"""
        return self.medicinestock_set.filter(
            quantity__lte=models.F('reorder_level')
        ).count()


class MedicineStock(models.Model):
    """
    Model to track medicine stock in each shop.
    Links medicines to shops and tracks quantity, price, and expiry.
    """
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    batch_number = models.CharField(max_length=50)
    expiry_date = models.DateField()
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    reorder_level = models.IntegerField(default=10)
    last_restocked = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['medicine', 'shop', 'batch_number']
        indexes = [
            models.Index(fields=['medicine', 'shop']),
            models.Index(fields=['expiry_date']),
        ]
        verbose_name = "Medicine Stock"
        verbose_name_plural = "Medicine Stocks"

    def __str__(self):
        return f"{self.medicine.name} at {self.shop.name} (Batch: {self.batch_number})"

    def clean(self):
        """Validate stock data"""
        if not self.pk and self.expiry_date <= timezone.now().date():
            raise ValidationError('Expiry date must be in the future')
        if self.quantity < 0:
            raise ValidationError('Quantity cannot be negative')
        if self.reorder_level < 0:
            raise ValidationError('Reorder level cannot be negative')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        self.check_and_create_alerts()
    
    def check_and_create_alerts(self):
        """Create alerts for low stock and expiry conditions"""
        if self.quantity <= self.reorder_level:
            StockAlert.objects.get_or_create(
                medicine_stock=self,
                alert_type='low_stock',
                resolved=False,
                defaults={
                    'message': f"Low stock alert for {self.medicine.name} at {self.shop.name}. Current quantity: {self.quantity}"
                }
            )
        
        days_until_expiry = (self.expiry_date - timezone.now().date()).days
        if 0 < days_until_expiry <= 30:
            StockAlert.objects.get_or_create(
                medicine_stock=self,
                alert_type='expiring',
                resolved=False,
                defaults={
                    'message': f"Stock expiring soon for {self.medicine.name} at {self.shop.name}. Expires on: {self.expiry_date}"
                }
            )
        
        if self.expiry_date <= timezone.now().date():
            StockAlert.objects.get_or_create(
                medicine_stock=self,
                alert_type='expired',
                resolved=False,
                defaults={
                    'message': f"Stock expired for {self.medicine.name} at {self.shop.name}. Expired on: {self.expiry_date}"
                }
            )


class MedicineSale(models.Model):
    """
    Model to track medicine sales.
    Records each sale with quantity, price, and customer information.
    """
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('insurance', 'Insurance'),
    ]

    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    stock = models.ForeignKey(MedicineStock, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES)
    prescription = models.FileField(
        upload_to='prescriptions/', 
        null=True, 
        blank=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png']
            )
        ]
    )
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(
        max_length=15,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Phone number must be entered in format: +999999999'
            )
        ]
    )
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['medicine', 'shop']),
            models.Index(fields=['date']),
        ]
        verbose_name = "Medicine Sale"
        verbose_name_plural = "Medicine Sales"

    def clean(self):
        """Validate sale data"""
        if self.quantity > self.stock.quantity:
            raise ValidationError(f"Not enough stock. Available: {self.stock.quantity}")
        if self.stock.expiry_date <= timezone.now().date():
            raise ValidationError("Cannot sell expired medicine")
        if self.unit_price <= 0:
            raise ValidationError("Unit price must be greater than zero")

    def save(self, *args, **kwargs):
        """Save sale and update stock"""
        self.clean()
        
        # Calculate total amount
        self.unit_price = self.stock.price
        self.total_amount = self.quantity * self.unit_price
        
        # Update stock quantity in a transaction
        with transaction.atomic():
            stock = MedicineStock.objects.select_for_update().get(id=self.stock.id)
            if stock.quantity < self.quantity:
                raise ValidationError("Stock quantity changed. Please try again.")
            
            stock.quantity -= self.quantity
            stock.save()
            
            super().save(*args, **kwargs)


class StockAlert(models.Model):
    """
    Model to track stock alerts for low quantity and expiry.
    Helps manage inventory by providing timely notifications.
    """
    ALERT_TYPES = [
        ('low_stock', 'Low Stock'),
        ('expiring', 'Expiring Soon'),
        ('expired', 'Expired'),
    ]

    medicine_stock = models.ForeignKey(MedicineStock, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_type', 'resolved']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = "Stock Alert"
        verbose_name_plural = "Stock Alerts"

    def __str__(self):
        return f"{self.alert_type} - {self.medicine_stock.medicine.name}"
    
    def resolve(self):
        """Mark alert as resolved"""
        self.resolved = True
        self.resolved_at = timezone.now()
        self.save()