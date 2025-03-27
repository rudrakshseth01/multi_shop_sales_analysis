# Use Case Diagram

```
+------------------------------------------------------+
|               Pharmacy Management System             |
+------------------------------------------------------+
|                                                      |
|  +-------------+       +----------------------+      |
|  |             |------>| Login to System      |      |
|  |             |       +----------------------+      |
|  |             |                                     |
|  |             |       +----------------------+      |
|  |             |------>| Manage Medicines     |      |
|  |             |       |  - Add Medicine      |      |
|  |             |       |  - Edit Medicine     |      |
|  | Pharmacist/ |       |  - Delete Medicine   |      |
|  | Manager     |       |  - View Medicine     |      |
|  |             |       +----------------------+      |
|  |             |                                     |
|  |             |       +----------------------+      |
|  |             |------>| Manage Shops         |      |
|  |             |       |  - Add Shop          |      |
|  |             |       |  - Edit Shop         |      |
|  |             |       |  - View Shop Details |      |
|  +-------------+       +----------------------+      |
|        |                                             |
|        |               +----------------------+      |
|        |-------------- | Manage Inventory     |      |
|        |               |  - Add Stock         |      |
|        |               |  - Edit Stock        |      |
|        |               |  - View Stock Levels |      |
|        |               +----------------------+      |
|        |                                             |
|        |               +----------------------+      |
|        |-------------- | Record Sales         |      |
|        |               |  - Add Sale          |      |
|        |               |  - View Sales        |      |
|        |               +----------------------+      |
|        |                                             |
|        |               +----------------------+      |
|        |-------------- | Make Purchases      |      |
|        |               |  - Add Purchase     |      |
|        |               +----------------------+      |
|        |                                             |
|        |               +----------------------+      |
|        |-------------- | View Analytics       |      |
|        |               |  - Sales Analysis    |      |
|        |               |  - Inventory Analysis|      |
|        |               |  - Shop Performance  |      |
|        |               +----------------------+      |
|        |                                             |
|        |               +----------------------+      |
|        |-------------- | Manage Alerts        |      |
|        |               |  - View Alerts       |      |
|        |               |  - Resolve Alerts    |      |
|        |               +----------------------+      |
|        |                                             |
|        |               +----------------------+      |
|        +-------------- | View Logs           |      |
|                        +----------------------+      |
|                                                      |
+------------------------------------------------------+
```

## Use Case Descriptions

### 1. Login to System
- **Actor**: Pharmacist/Manager
- **Description**: Authenticate user with username and password
- **Preconditions**: User has valid credentials
- **Basic Flow**:
  1. User enters username and password
  2. System validates credentials
  3. System grants access to dashboard
- **Alternate Flow**: Invalid credentials error message

### 2. Manage Medicines
- **Actor**: Pharmacist/Manager
- **Description**: CRUD operations for medicines
- **Preconditions**: User is logged in
- **Basic Flow**:
  1. User selects medicine management option
  2. System displays list of medicines
  3. User performs desired operation (add/edit/delete/view)
  4. System updates database and confirms action

### 3. Manage Shops
- **Actor**: Pharmacist/Manager
- **Description**: CRUD operations for pharmacy shops
- **Preconditions**: User is logged in
- **Basic Flow**:
  1. User selects shop management option
  2. System displays list of shops
  3. User performs desired operation (add/edit/view)
  4. System updates database and confirms action

### 4. Manage Inventory
- **Actor**: Pharmacist/Manager
- **Description**: Manage medicine stock levels across shops
- **Preconditions**: User is logged in, medicines and shops exist
- **Basic Flow**:
  1. User selects inventory management option
  2. User selects shop
  3. System displays current inventory for selected shop
  4. User adds/edits stock entries
  5. System updates database and confirms action

### 5. Record Sales
- **Actor**: Pharmacist/Manager
- **Description**: Record medicine sales with customer information
- **Preconditions**: User is logged in, medicines and shops exist with stock
- **Basic Flow**:
  1. User selects record sale option
  2. User selects shop, medicine, quantity, payment method
  3. User enters customer information (optional)
  4. System calculates total and updates stock
  5. System records sale and generates receipt

### 6. Make Purchases
- **Actor**: Pharmacist/Manager
- **Description**: Record medicine purchases to update inventory
- **Preconditions**: User is logged in, medicines and shops exist
- **Basic Flow**:
  1. User selects make purchase option
  2. User selects shop and medicines
  3. User enters purchase details (quantity, price, batch, expiry)
  4. System updates inventory
  5. System records purchase transaction

### 7. View Analytics
- **Actor**: Pharmacist/Manager
- **Description**: Access sales and inventory analytics
- **Preconditions**: User is logged in, sales and inventory data exists
- **Basic Flow**:
  1. User selects analytics option
  2. User selects analysis type and parameters (date range, shop)
  3. System generates and displays reports and visualizations

### 8. Manage Alerts
- **Actor**: Pharmacist/Manager
- **Description**: View and resolve inventory alerts
- **Preconditions**: User is logged in
- **Basic Flow**:
  1. User selects alerts option
  2. System displays active alerts (low stock, expiring, expired)
  3. User takes action to resolve alerts
  4. System updates alert status

### 9. View Logs
- **Actor**: Pharmacist/Manager
- **Description**: View system activity logs
- **Preconditions**: User is logged in
- **Basic Flow**:
  1. User selects logs option
  2. System displays transaction logs
  3. User can filter logs by date, action type, etc. 