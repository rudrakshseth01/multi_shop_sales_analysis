import django_filters
from .models import Medicine, MedicineStock, MedicineSale, Shop

class MedicineFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        label='Medicine Name'
    )
    generic_name = django_filters.CharFilter(
        field_name='generic_name',
        lookup_expr='icontains',
        label='Generic Name'
    )
    manufacturer = django_filters.CharFilter(
        field_name='manufacturer',
        lookup_expr='icontains',
        label='Manufacturer'
    )
    category = django_filters.ChoiceFilter(
        choices=Medicine.CATEGORY_CHOICES,
        label='Category'
    )

    class Meta:
        model = Medicine
        fields = ['name', 'generic_name', 'manufacturer', 'category']

class StockFilter(django_filters.FilterSet):
    medicine_name = django_filters.CharFilter(
        field_name='medicine__name',
        lookup_expr='icontains',
        label='Medicine Name'
    )
    quantity_lt = django_filters.NumberFilter(
        field_name='quantity',
        lookup_expr='lt',
        label='Quantity less than'
    )
    quantity_gt = django_filters.NumberFilter(
        field_name='quantity',
        lookup_expr='gt',
        label='Quantity greater than'
    )
    expiry_before = django_filters.DateFilter(
        field_name='expiry_date',
        lookup_expr='lt',
        label='Expires before'
    )
    expiry_after = django_filters.DateFilter(
        field_name='expiry_date',
        lookup_expr='gt',
        label='Expires after'
    )

    class Meta:
        model = MedicineStock
        fields = ['medicine_name', 'quantity_lt', 'quantity_gt', 'expiry_before', 'expiry_after']

class SaleFilter(django_filters.FilterSet):
    medicine_name = django_filters.CharFilter(
        field_name='medicine__name',
        lookup_expr='icontains',
        label='Medicine Name'
    )
    date_after = django_filters.DateFilter(
        field_name='date',
        lookup_expr='gt',
        label='After'
    )
    date_before = django_filters.DateFilter(
        field_name='date',
        lookup_expr='lt',
        label='Before'
    )
    payment_method = django_filters.ChoiceFilter(
        choices=MedicineSale.PAYMENT_CHOICES,
        label='Payment Method'
    )

    class Meta:
        model = MedicineSale
        fields = ['medicine_name', 'date_after', 'date_before', 'payment_method']

class ShopFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains',
        label='Shop Name'
    )
    location = django_filters.CharFilter(
        field_name='location',
        lookup_expr='icontains',
        label='Location'
    )

    class Meta:
        model = Shop
        fields = ['name', 'location']