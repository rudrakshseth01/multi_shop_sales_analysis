from django.core.management.base import BaseCommand
from inventory.models import Shop, Item, Sale
from django.db import transaction
from django.utils import timezone
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Initialize dummy data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating dummy data...')
        
        with transaction.atomic():
            # Create shops
            shops = [
                Shop.objects.create(
                    name='Electronics Bazaar',
                    location='MG Road, Bangalore',
                    contact_number='9876543210'
                ),
                Shop.objects.create(
                    name='Fashion Hub',
                    location='Commercial Street',
                    contact_number='9876543211'
                ),
                Shop.objects.create(
                    name='Grocery Mart',
                    location='Indiranagar',
                    contact_number='9876543212'
                ),
                Shop.objects.create(
                    name='Home Store',
                    location='HSR Layout',
                    contact_number='9876543213'
                )
            ]

            # Create items
            categories = ['electronics', 'clothing', 'groceries', 'home']
            items_data = [
                # Electronics
                {'name': 'Laptop', 'price': 45000, 'category': 'electronics'},
                {'name': 'Smartphone', 'price': 15000, 'category': 'electronics'},
                {'name': 'Tablet', 'price': 20000, 'category': 'electronics'},
                # Clothing
                {'name': 'T-Shirt', 'price': 499, 'category': 'clothing'},
                {'name': 'Jeans', 'price': 999, 'category': 'clothing'},
                {'name': 'Dress', 'price': 1499, 'category': 'clothing'},
                # Groceries
                {'name': 'Rice (5kg)', 'price': 299, 'category': 'groceries'},
                {'name': 'Dal (1kg)', 'price': 120, 'category': 'groceries'},
                {'name': 'Oil (1L)', 'price': 180, 'category': 'groceries'},
                # Home
                {'name': 'Bedsheet', 'price': 699, 'category': 'home'},
                {'name': 'Pillow', 'price': 299, 'category': 'home'},
                {'name': 'Towel', 'price': 199, 'category': 'home'}
            ]

            items = []
            for shop in shops:
                for item_data in items_data:
                    if item_data['category'] == categories[shops.index(shop) % len(categories)]:
                        items.append(Item(
                            name=item_data['name'],
                            shop=shop,
                            category=item_data['category'],
                            price=item_data['price'],
                            quantity=random.randint(5, 100),
                            reorder_level=random.randint(5, 15)
                        ))
            
            Item.objects.bulk_create(items)

            # Create sales
            payment_methods = ['cash', 'upi', 'card']
            for _ in range(100):  # Create 100 sales records
                item = random.choice(items)
                sale_date = timezone.now() - timedelta(
                    days=random.randint(0, 30),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )
                
                Sale.objects.create(
                    item=item,
                    shop=item.shop,
                    quantity=random.randint(1, 5),
                    date=sale_date,
                    payment_method=random.choice(payment_methods)
                )

        self.stdout.write(self.style.SUCCESS('Successfully created dummy data')) 