from django.core.management.base import BaseCommand
from django.utils import timezone
from inventory.models import Medicine, Shop, MedicineStock, MedicineSale, StockAlert
from datetime import timedelta, datetime
import random
from django.db import transaction
from decimal import Decimal

class Command(BaseCommand):
    help = 'Initialize medical inventory data'

    def handle(self, *args, **kwargs):
        try:
            self.stdout.write('Clearing existing data...')
            StockAlert.objects.all().delete()
            MedicineSale.objects.all().delete()
            MedicineStock.objects.all().delete()
            Medicine.objects.all().delete()
            Shop.objects.all().delete()

            with transaction.atomic():
                self.stdout.write('Creating medicines...')
                # Real medicine data
                medicines_data = [
                    {
                        'id': 'MED001',
                        'name': 'Paracetamol 500mg',
                        'generic': 'Acetaminophen',
                        'category': 'tablet',
                        'manufacturer': 'GSK Pharmaceuticals',
                    },
                    {
                        'id': 'MED002',
                        'name': 'Amoxicillin 250mg',
                        'generic': 'Amoxicillin Trihydrate',
                        'category': 'tablet',
                        'manufacturer': 'Cipla Ltd',
                    },
                    {
                        'id': 'MED003',
                        'name': 'Azithromycin 500mg',
                        'generic': 'Azithromycin',
                        'category': 'tablet',
                        'manufacturer': 'Sun Pharma',
                    },
                    {
                        'id': 'MED004',
                        'name': 'Crocin Cold & Flu',
                        'generic': 'Paracetamol + Phenylephrine',
                        'category': 'tablet',
                        'manufacturer': 'GSK Pharmaceuticals',
                    },
                    {
                        'id': 'MED005',
                        'name': 'Benadryl Cough Syrup',
                        'generic': 'Diphenhydramine',
                        'category': 'syrup',
                        'manufacturer': 'Johnson & Johnson',
                    },
                    {
                        'id': 'MED006',
                        'name': 'Dolo 650mg',
                        'generic': 'Paracetamol',
                        'category': 'tablet',
                        'manufacturer': 'Micro Labs Ltd',
                    },
                    {
                        'id': 'MED007',
                        'name': 'Allegra 120mg',
                        'generic': 'Fexofenadine',
                        'category': 'tablet',
                        'manufacturer': 'Sanofi India',
                    },
                    {
                        'id': 'MED008',
                        'name': 'Augmentin 625 Duo',
                        'generic': 'Amoxicillin + Clavulanic Acid',
                        'category': 'tablet',
                        'manufacturer': 'GSK Pharmaceuticals',
                    },
                    {
                        'id': 'MED009',
                        'name': 'Zincovit',
                        'generic': 'Multivitamin + Zinc',
                        'category': 'tablet',
                        'manufacturer': 'Apex Laboratories',
                    },
                    {
                        'id': 'MED010',
                        'name': 'Ascoril LS Syrup',
                        'generic': 'Levosalbutamol + Ambroxol',
                        'category': 'syrup',
                        'manufacturer': 'Glenmark Pharmaceuticals',
                    }
                ]

                medicines = []
                for med_data in medicines_data:
                    medicine = Medicine.objects.create(
                        primary_id=med_data['id'],
                        name=med_data['name'],
                        generic_name=med_data['generic'],
                        category=med_data['category'],
                        manufacturer=med_data['manufacturer'],
                        description=f"Common {med_data['category']} form of {med_data['generic']}",
                        side_effects="Common side effects may include nausea, drowsiness. Consult doctor for complete information."
                    )
                    medicines.append(medicine)

                self.stdout.write('Creating shops...')
                # Real shop data
                shops_data = [
                    {
                        'name': 'LifeCare Pharmacy',
                        'location': '123 Main Street, City Center',
                        'contact': '+919876543210',
                        'license': 'LIC2023001',
                    },
                    {
                        'name': 'MedPlus Pharmacy',
                        'location': '45 Market Road, New Town',
                        'contact': '+919876543211',
                        'license': 'LIC2023002',
                    },
                    {
                        'name': 'Apollo Pharmacy',
                        'location': '78 Hospital Road, Health District',
                        'contact': '+919876543212',
                        'license': 'LIC2023003',
                    },
                    {
                        'name': 'Wellness Forever',
                        'location': '90 Colony Circle, Suburb Area',
                        'contact': '+919876543213',
                        'license': 'LIC2023004',
                    },
                    {
                        'name': 'Care & Cure Pharmacy',
                        'location': '34 Lake View Road, Residential Zone',
                        'contact': '+919876543214',
                        'license': 'LIC2023005',
                    }
                ]

                shops = []
                for shop_data in shops_data:
                    shop = Shop.objects.create(
                        name=shop_data['name'],
                        location=shop_data['location'],
                        contact_number=shop_data['contact'],
                        license_number=shop_data['license'],
                        opening_time='09:00:00',
                        closing_time='21:00:00'
                    )
                    shops.append(shop)

                self.stdout.write('Creating stocks...')
                stocks = []
                today = timezone.now().date()
                
                for medicine in medicines:
                    for shop in shops:
                        # Create normal stock (future expiry)
                        stock = MedicineStock.objects.create(
                            medicine=medicine,
                            shop=shop,
                            batch_number=f'B{random.randint(10000,99999)}',
                            quantity=random.randint(50, 200),
                            price=Decimal(random.uniform(10.0, 100.0)).quantize(Decimal('0.01')),
                            expiry_date=today + timedelta(days=random.randint(180, 365)),
                            reorder_level=30
                        )
                        stocks.append(stock)

                        # Create some low stock situations (20% chance)
                        if random.random() < 0.2:
                            stock = MedicineStock.objects.create(
                                medicine=medicine,
                                shop=shop,
                                batch_number=f'B{random.randint(10000,99999)}',
                                quantity=random.randint(5, 15),
                                price=Decimal(random.uniform(10.0, 100.0)).quantize(Decimal('0.01')),
                                expiry_date=today + timedelta(days=random.randint(180, 365)),
                                reorder_level=20
                            )
                            stocks.append(stock)

                        # Create some expiring soon stock (15% chance)
                        if random.random() < 0.15:
                            stock = MedicineStock.objects.create(
                                medicine=medicine,
                                shop=shop,
                                batch_number=f'B{random.randint(10000,99999)}',
                                quantity=random.randint(20, 50),
                                price=Decimal(random.uniform(10.0, 100.0)).quantize(Decimal('0.01')),
                                expiry_date=today + timedelta(days=random.randint(1, 30)),
                                reorder_level=20
                            )
                            stocks.append(stock)

                        # Create some expired stock (10% chance)
                        if random.random() < 0.1:
                            try:
                                stock = MedicineStock(
                                    medicine=medicine,
                                    shop=shop,
                                    batch_number=f'B{random.randint(10000,99999)}',
                                    quantity=random.randint(5, 15),
                                    price=Decimal(random.uniform(10.0, 100.0)).quantize(Decimal('0.01')),
                                    expiry_date=today - timedelta(days=random.randint(1, 30)),
                                    reorder_level=20
                                )
                                # Skip validation for expired stock during initialization
                                stock.save(force_insert=True)
                                stocks.append(stock)
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(f'Skipped creating expired stock: {str(e)}'))

                self.stdout.write('Creating sales...')
                # Create sales data with proper stock updates
                for _ in range(200):
                    stock = random.choice(stocks)
                    if stock.quantity > 0:
                        quantity = min(random.randint(1, 10), stock.quantity)
                        sale_date = timezone.now() - timedelta(days=random.randint(0, 30))
                        
                        try:
                            # Create sale
                            sale = MedicineSale.objects.create(
                                medicine=stock.medicine,
                                shop=stock.shop,
                                stock=stock,
                                quantity=quantity,
                                unit_price=stock.price,
                                total_amount=quantity * stock.price,
                                payment_method=random.choice(['cash', 'upi', 'card']),
                                customer_name=f"Customer {random.randint(1,100)}",
                                customer_phone=f"+91987{random.randint(1000000,9999999)}",
                                date=sale_date
                            )
                            
                            # Update stock quantity directly
                            stock.quantity = max(0, stock.quantity - quantity)
                            stock.save()
                            
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f'Skipped creating sale: {str(e)}'))

                # Create alerts for all stocks
                self.stdout.write('Creating alerts...')
                for stock in MedicineStock.objects.all():
                    stock.check_and_create_alerts()

                self.stdout.write(self.style.SUCCESS('Successfully initialized medical data'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error initializing data: {str(e)}'))
            raise 