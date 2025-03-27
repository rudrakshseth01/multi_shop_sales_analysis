# Entity Relationship Diagram (ERD)

```
+----------------+       +----------------+       +----------------+
|    MEDICINE    |       |      SHOP      |       | MEDICINE_STOCK |
+----------------+       +----------------+       +----------------+
| PK primary_id  |<------| PK id          |<------| PK id          |
| name           |       | name           |       | FK medicine_id |
| generic_name   |       | location       |       | FK shop_id     |
| category       |       | contact_number |       | batch_number   |
| manufacturer   |       | license_number |       | quantity       |
| description    |       | opening_time   |       | expiry_date    |
| side_effects   |       | closing_time   |       | purchase_price |
+----------------+       +----------------+       | selling_price  |
        ^                        ^                | last_restocked |
        |                        |                +----------------+
        |                        |                        |
        |                        |                        |
        |                        |                        v
+----------------+       +----------------+       +----------------+
| MEDICINE_SALE  |       |  STOCK_ALERT   |       |TRANSACTION_LOG |
+----------------+       +----------------+       +----------------+
| PK id          |       | PK id          |       | PK id          |
| FK medicine_id |       | FK stock_id    |       | action_type    |
| FK shop_id     |       | alert_type     |       | description    |
| quantity       |       | message        |       | timestamp      |
| unit_price     |       | date_created   |       | user           |
| total_amount   |       | resolved       |       +----------------+
| date           |       | resolved_date  |
| payment_method |       +----------------+
| customer_name  |
| customer_phone |
+----------------+
```

## Entity Descriptions

### MEDICINE
- **Primary Key**: primary_id (String)
- **Description**: Stores information about medicines available in the system.
- **Relationships**:
  - One-to-Many with MEDICINE_STOCK (One medicine can have multiple stock entries)
  - One-to-Many with MEDICINE_SALE (One medicine can be sold multiple times)

### SHOP
- **Primary Key**: id (Integer, auto-increment)
- **Description**: Stores information about pharmacy shops/branches.
- **Relationships**:
  - One-to-Many with MEDICINE_STOCK (One shop can have multiple medicine stocks)
  - One-to-Many with MEDICINE_SALE (One shop can have multiple sales)

### MEDICINE_STOCK
- **Primary Key**: id (Integer, auto-increment)
- **Foreign Keys**:
  - medicine_id (References MEDICINE.primary_id)
  - shop_id (References SHOP.id)
- **Description**: Maintains stock levels of medicines at each shop.
- **Relationships**:
  - Many-to-One with MEDICINE
  - Many-to-One with SHOP
  - One-to-Many with STOCK_ALERT (One stock entry can have multiple alerts)

### MEDICINE_SALE
- **Primary Key**: id (Integer, auto-increment)
- **Foreign Keys**:
  - medicine_id (References MEDICINE.primary_id)
  - shop_id (References SHOP.id)
- **Description**: Records sales transactions of medicines.
- **Relationships**:
  - Many-to-One with MEDICINE
  - Many-to-One with SHOP

### STOCK_ALERT
- **Primary Key**: id (Integer, auto-increment)
- **Foreign Keys**:
  - stock_id (References MEDICINE_STOCK.id)
- **Description**: Tracks alerts for stock issues (low stock, expiring, expired).
- **Relationships**:
  - Many-to-One with MEDICINE_STOCK

### TRANSACTION_LOG
- **Primary Key**: id (Integer, auto-increment)
- **Description**: Logs all system activities for audit purposes.
- **Relationships**: 
  - No direct foreign key relationships, but references various entities in description field

## Cardinality Relationships

1. **MEDICINE to MEDICINE_STOCK**: 1:N
   - One medicine can have many stock entries.

2. **SHOP to MEDICINE_STOCK**: 1:N
   - One shop can have many medicine stocks.

3. **MEDICINE to MEDICINE_SALE**: 1:N
   - One medicine can be sold many times.

4. **SHOP to MEDICINE_SALE**: 1:N
   - One shop can have many sales.

5. **MEDICINE_STOCK to STOCK_ALERT**: 1:N
   - One stock entry can have many alerts. 