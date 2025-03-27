# Pharmacy Analysis and Inventory Management System

## Project Overview

This application is a comprehensive pharmacy inventory and sales management system designed to help pharmacies track medicine inventory, manage sales, analyze business performance, and optimize stock levels across multiple shops. The system provides real-time analytics, stock alerts, and detailed reports to facilitate data-driven decision making.

## System Architecture

The application is built using the Django web framework with a SQLite database. The architecture follows the Model-View-Template (MVT) pattern:

- **Models**: Define the database structure and business logic
- **Views**: Handle HTTP requests, process data, and render templates
- **Templates**: Provide the user interface 
- **Static Files**: Contain CSS, JavaScript, and images for the frontend

## Key Features

### 1. Inventory Management
- Track medicine details (name, generic name, category, manufacturer, etc.)
- Manage medicine stock across multiple shops
- Monitor expiry dates and batch numbers
- Add new medicines and update existing inventory

### 2. Sales Management
- Record sales transactions with customer information
- Process different payment methods
- Track sales by shop, medicine, and time period
- Record and manage purchase transactions

### 3. Shop Management
- Maintain multiple shop locations
- Track shop-specific inventory
- Analyze performance by shop

### 4. Analytics & Reports
- Sales trends analysis (daily, weekly, monthly)
- Shop performance comparison
- Top-selling medicines
- Revenue metrics and forecasting
- Stock aging analysis
- Customer loyalty analytics

### 5. Alerts System
- Low stock alerts
- Expiring medicine alerts
- Expired medicine alerts
- Alert resolution tracking

### 6. Transaction Logging
- Comprehensive activity logging
- Audit trail of all system actions

## Database Models

### Medicine
- Primary fields: primary_id, name, generic_name, category, manufacturer, description, side_effects
- Tracks basic information about medicines

### Shop
- Primary fields: name, location, contact_number, license_number, opening_time, closing_time
- Manages pharmacy shop locations

### MedicineStock
- Primary fields: medicine, shop, batch_number, quantity, expiry_date, purchase_price, selling_price, last_restocked
- Tracks inventory levels at each shop

### MedicineSale
- Primary fields: medicine, shop, quantity, unit_price, total_amount, date, payment_method, customer_name, customer_phone
- Records sales transactions

### StockAlert
- Primary fields: stock, alert_type, message, date_created, resolved, resolved_date
- Manages alerts for low stock, expiring medicines, etc.

### TransactionLog
- Primary fields: action_type, description, timestamp, user
- Logs all system activities

## Views/Controllers

### Dashboard
- `dashboard`: Main system overview with key metrics

### Medicine Management
- `medicine_list`: Display all medicines
- `medicine_detail`: Show detailed medicine information
- `medicine_add`: Add new medicine
- `medicine_edit`: Update medicine details
- `medicine_delete`: Remove medicine from system

### Shop Management
- `shop_list`: Display all shops
- `shop_detail`: Show detailed shop information
- `shop_add`: Add new shop
- `shop_edit`: Update shop details
- `add_stock`: Add stock to a shop

### Sales Management
- `sales_add`: Record new sales
- `sales_list`: View all sales transactions
- `make_purchase`: Process purchases and update stock

### Alerts
- `stock_alerts`: View all current alerts
- `resolve_alert`: Mark an alert as resolved

### Analytics
- `sales_analysis`: Comprehensive sales analytics
- `medicine_sales_chart`: API for medicine sales visualization
- `shop_sales_chart`: API for shop sales visualization

### System
- `transaction_logs`: View system activity logs

## User Interface

The system features a modern, responsive UI with:

1. **Navigation**
   - Left sidebar for main navigation
   - Quick access to key functions from dashboard
   - Contextual submenus

2. **Dashboard**
   - Key performance indicators
   - Recent activities
   - Alert notifications
   - Quick access buttons

3. **List Views**
   - Sortable and filterable tables
   - Pagination for large datasets
   - Export functionality

4. **Detail Views**
   - Comprehensive information displays
   - Tabbed interfaces for complex data
   - Charts and visualizations

5. **Forms**
   - Validated input forms
   - Dynamic fields with AJAX support
   - Intuitive error messaging

## API Endpoints

The system provides internal API endpoints for AJAX functionality:

- `/api/medicine/<primary_id>/sales/`: Get sales data for specific medicine
- `/api/shop/<shop_id>/sales/`: Get sales data for specific shop

## Data Flow

### Inventory Flow
1. Medicines are added to the system
2. Stock is added to specific shops through purchases
3. System monitors stock levels and generates alerts
4. Stock is reduced through sales transactions

### Sales Flow
1. Sales are recorded through the sales form
2. Inventory is automatically updated
3. Transaction is logged
4. Analytics are recalculated

### Alert Flow
1. System checks for alert conditions (low stock, expiry)
2. Alerts are generated and displayed
3. Users resolve alerts by taking appropriate action
4. Resolved alerts are archived

## Security Measures

- Django's built-in security features
- CSRF protection
- Form validation
- User authentication and authorization

## Deployment Considerations

- Django production settings
- Database migration management
- Static files collection
- Logging configuration

## Future Enhancements

Potential areas for system expansion:

1. Advanced forecasting with machine learning
2. Mobile application for on-the-go management
3. Customer relationship management (CRM) integration
4. Supplier management and automated ordering
5. Prescription management
6. Integration with point-of-sale systems
7. Barcode/QR code scanning for inventory management

---

*Documentation created for Pharmacy Analysis and Inventory Management System, 2024* 