# Class Diagram

```
+---------------------+        +---------------------+        +---------------------+
|      Medicine       |        |        Shop         |        |    MedicineStock    |
+---------------------+        +---------------------+        +---------------------+
| -primary_id: String |        | -id: Integer        |<-------| -id: Integer        |
| -name: String       |        | -name: String       |        | -medicine: Medicine |
| -generic_name: String|<------| -location: String   |        | -shop: Shop         |
| -category: String   |        | -contact_number: String|     | -batch_number: String|
| -manufacturer: String|       | -license_number: String|     | -quantity: Integer  |
| -description: Text  |        | -opening_time: Time |        | -expiry_date: Date  |
| -side_effects: Text |        | -closing_time: Time |        | -purchase_price: Decimal|
+---------------------+        +---------------------+        | -selling_price: Decimal|
| +add()              |        | +add()              |        | -last_restocked: DateTime|
| +update()           |        | +update()           |        +---------------------+
| +delete()           |        | +delete()           |        | +add()              |
| +get_stocks()       |        | +get_medicines()    |        | +update()           |
+---------------------+        +---------------------+        | +delete()           |
         ^                              ^                     | +check_expiry()     |
         |                              |                     | +check_low_stock()  |
         |                              |                     +---------------------+
         |                              |                              ^
         |                              |                              |
+---------------------+        +---------------------+                  |
|    MedicineSale     |        |     StockAlert     |                  |
+---------------------+        +---------------------+                  |
| -id: Integer        |        | -id: Integer        |<-----------------+
| -medicine: Medicine |        | -stock: MedicineStock|
| -shop: Shop         |        | -alert_type: String |
| -quantity: Integer  |        | -message: String    |
| -unit_price: Decimal|        | -date_created: DateTime|
| -total_amount: Decimal|      | -resolved: Boolean  |
| -date: DateTime     |        | -resolved_date: DateTime|
| -payment_method: String|     +---------------------+
| -customer_name: String|      | +resolve()          |
| -customer_phone: String|     | +is_active()        |
+---------------------+        +---------------------+
| +add()              |
| +update()           |                +---------------------+
| +delete()           |                |   TransactionLog   |
| +get_receipt()      |                +---------------------+
+---------------------+                | -id: Integer        |
                                      | -action_type: String |
                                      | -description: String |
                                      | -timestamp: DateTime |
                                      | -user: String        |
                                      +---------------------+
                                      | +add()              |
                                      | +get_logs_by_date() |
                                      | +get_logs_by_user() |
                                      +---------------------+
```

## Relationships Explanation

1. **Medicine to MedicineStock**: One-to-Many
   - One medicine can have multiple stock entries (different batches, shops, etc.)

2. **Shop to MedicineStock**: One-to-Many
   - One shop can have multiple medicine stocks

3. **Medicine to MedicineSale**: One-to-Many
   - One medicine can be sold multiple times

4. **Shop to MedicineSale**: One-to-Many
   - One shop can have multiple sales

5. **MedicineStock to StockAlert**: One-to-Many
   - One stock entry can have multiple alerts (low stock, expiring, expired)

## Methods Detail

### Medicine
- **add()**: Create a new medicine record
- **update()**: Update medicine details
- **delete()**: Delete a medicine from the system
- **get_stocks()**: Get all stock entries for this medicine

### Shop
- **add()**: Create a new shop record
- **update()**: Update shop details
- **delete()**: Delete a shop from the system
- **get_medicines()**: Get all medicines available in this shop

### MedicineStock
- **add()**: Add new stock entry
- **update()**: Update stock details
- **delete()**: Delete a stock entry
- **check_expiry()**: Check if stock is expiring soon or expired
- **check_low_stock()**: Check if quantity is below threshold

### MedicineSale
- **add()**: Record a new sale
- **update()**: Update sale details
- **delete()**: Delete a sale record
- **get_receipt()**: Generate receipt for this sale

### StockAlert
- **resolve()**: Mark alert as resolved
- **is_active()**: Check if alert is still active

### TransactionLog
- **add()**: Create a new log entry
- **get_logs_by_date()**: Filter logs by date range
- **get_logs_by_user()**: Filter logs by user 