-- Retail Inventory Management System Setup Script
-- Converted from Online Shopping System

-- Drop existing database if it exists
DROP DATABASE IF EXISTS retail_db;
CREATE DATABASE retail_db;
USE retail_db;

-- Categories Table (for product categorization)
CREATE TABLE Category (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products Table (main inventory table)
CREATE TABLE Product (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 0,
    min_stock_level INT DEFAULT 10,  -- Alert when stock is low
    category_id INT,
    sku VARCHAR(100) UNIQUE,  -- Stock Keeping Unit
    barcode VARCHAR(100),
    supplier VARCHAR(255),
    cost_price DECIMAL(10,2),  -- Purchase cost for profit calculation
    image_url VARCHAR(500),
    average_rating DECIMAL(3,2) DEFAULT 0.00,
    status ENUM('active', 'discontinued', 'out_of_stock') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES Category(category_id) ON DELETE SET NULL
);

-- Customers Table (for customer management)
CREATE TABLE Customer (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),
    password VARCHAR(255) NOT NULL,  -- Plain text as requested
    city VARCHAR(100),
    state VARCHAR(100),
    pin VARCHAR(10),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Suppliers Table (for supplier management)
CREATE TABLE Supplier (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    pin VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Purchase Orders Table (for stock procurement)
CREATE TABLE Purchase_Order (
    purchase_order_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT,
    order_date DATE NOT NULL,
    expected_delivery_date DATE,
    status ENUM('pending', 'received', 'cancelled') DEFAULT 'pending',
    total_amount DECIMAL(12,2),
    created_by INT,  -- Admin user who created the order
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id) ON DELETE SET NULL
);

-- Purchase Order Items Table
CREATE TABLE Purchase_Order_Item (
    purchase_order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    purchase_order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_cost DECIMAL(10,2) NOT NULL,
    total_cost DECIMAL(12,2) GENERATED ALWAYS AS (quantity * unit_cost) STORED,
    received_quantity INT DEFAULT 0,
    FOREIGN KEY (purchase_order_id) REFERENCES Purchase_Order(purchase_order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE RESTRICT
);

-- Orders Table (for sales)
CREATE TABLE Orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(12,2) NOT NULL,
    status ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
    payment_method VARCHAR(50),
    payment_status ENUM('pending', 'paid', 'refunded') DEFAULT 'pending',
    shipping_address TEXT,
    delivery_date TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id) ON DELETE SET NULL
);

-- Order Items Table
CREATE TABLE Order_Item (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price_at_purchase DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(12,2) GENERATED ALWAYS AS (quantity * price_at_purchase) STORED,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE RESTRICT
);

-- Inventory Transactions Table (for tracking stock movements)
CREATE TABLE Inventory_Transaction (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    transaction_type ENUM('purchase', 'sale', 'adjustment', 'return', 'damage') NOT NULL,
    quantity_change INT NOT NULL,  -- Positive for stock in, negative for stock out
    reference_id INT,  -- Order ID or Purchase Order ID
    reference_type ENUM('order', 'purchase_order', 'manual'),
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    created_by INT,  -- User who performed the transaction
    stock_before INT NOT NULL,
    stock_after INT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE CASCADE
);

-- Users Table (for staff/admin access)
CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,  -- Plain text as requested
    role ENUM('admin', 'manager', 'staff') NOT NULL DEFAULT 'staff',
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert Categories
INSERT INTO Category (category_name, description) VALUES
('Electronics', 'Electronic devices and accessories'),
('Clothing', 'Apparel and fashion items'),
('Books', 'Books and educational materials'),
('Home & Kitchen', 'Home appliances and kitchenware'),
('Sports', 'Sports equipment and accessories'),
('Toys', 'Children toys and games'),
('Office Supplies', 'Office and stationery items'),
('Health & Beauty', 'Personal care and health products');

-- Insert Sample Products
INSERT INTO Product (name, description, price, stock_quantity, category_id, sku, supplier, cost_price, min_stock_level) VALUES
('Laptop Pro 15"', 'High-performance laptop with 16GB RAM, 512GB SSD', 1200.00, 25, 1, 'LP-001', 'TechSupplier Inc.', 800.00, 5),
('Wireless Mouse', 'Ergonomic wireless mouse with USB receiver', 25.50, 100, 1, 'WM-002', 'TechSupplier Inc.', 15.00, 20),
('USB-C Cable', 'Type-C to Type-A charging cable, 2m length', 12.99, 150, 1, 'UC-003', 'CableMaster', 5.00, 30),
('Cotton T-Shirt', '100% cotton t-shirt, various colors', 15.00, 200, 2, 'CT-004', 'FashionHub', 8.00, 50),
('Denim Jeans', 'Classic fit denim jeans', 45.00, 80, 2, 'DJ-005', 'FashionHub', 25.00, 15),
('Winter Jacket', 'Warm winter jacket with hood', 89.99, 40, 2, 'WJ-006', 'FashionHub', 50.00, 10),
('Programming Book', 'Python Programming Guide', 35.00, 60, 3, 'PB-007', 'BookWorld', 20.00, 12),
('Notebook Set', 'Set of 5 notebooks, 200 pages each', 18.50, 120, 3, 'NS-008', 'BookWorld', 10.00, 25),
('Coffee Maker', 'Automatic drip coffee maker, 12 cups', 65.00, 30, 4, 'CM-009', 'HomeEssentials', 40.00, 8),
('Blender', 'High-speed blender with multiple settings', 45.99, 45, 4, 'BL-010', 'HomeEssentials', 28.00, 10),
('Tennis Racket', 'Professional tennis racket', 120.00, 20, 5, 'TR-011', 'SportsGear', 75.00, 5),
('Yoga Mat', 'Non-slip exercise yoga mat', 25.00, 75, 5, 'YM-012', 'SportsGear', 12.00, 15),
('Board Game', 'Strategy board game for 2-4 players', 35.99, 55, 6, 'BG-013', 'ToyLand', 20.00, 12),
('Puzzle Set', '1000-piece jigsaw puzzle', 15.99, 90, 6, 'PS-014', 'ToyLand', 8.00, 20),
('Pen Set', 'Set of 12 ballpoint pens', 8.99, 200, 7, 'PS-015', 'OfficePro', 4.00, 40),
('Stapler', 'Heavy-duty desktop stapler', 12.50, 85, 7, 'ST-016', 'OfficePro', 7.00, 18),
('Shampoo', 'Herbal shampoo 500ml', 8.99, 130, 8, 'SH-017', 'BeautyCare', 5.00, 25),
('Face Cream', 'Moisturizing face cream 100ml', 15.99, 70, 8, 'FC-018', 'BeautyCare', 9.00, 15);

-- Insert Sample Suppliers
INSERT INTO Supplier (name, contact_person, email, phone, city, state) VALUES
('TechSupplier Inc.', 'John Smith', 'john@techsupplier.com', '555-0101', 'New York', 'NY'),
('FashionHub', 'Sarah Johnson', 'sarah@fashionhub.com', '555-0102', 'Los Angeles', 'CA'),
('BookWorld', 'Michael Brown', 'michael@bookworld.com', '555-0103', 'Chicago', 'IL'),
('HomeEssentials', 'Emily Davis', 'emily@homeessentials.com', '555-0104', 'Houston', 'TX'),
('SportsGear', 'David Wilson', 'david@sportsgear.com', '555-0105', 'Phoenix', 'AZ'),
('ToyLand', 'Lisa Anderson', 'lisa@toyland.com', '555-0106', 'Philadelphia', 'PA'),
('OfficePro', 'Robert Taylor', 'robert@officepro.com', '555-0107', 'San Antonio', 'TX'),
('BeautyCare', 'Jennifer Martinez', 'jennifer@beautycare.com', '555-0108', 'San Diego', 'CA');

-- Insert Sample Customers
INSERT INTO Customer (name, email, phone, password, city, state, address) VALUES
('Alice Johnson', 'alice@email.com', '555-1001', 'customer123', 'Boston', 'MA', '123 Main St'),
('Bob Smith', 'bob@email.com', '555-1002', 'customer123', 'Seattle', 'WA', '456 Oak Ave'),
('Carol White', 'carol@email.com', '555-1003', 'customer123', 'Miami', 'FL', '789 Pine Rd'),
('David Brown', 'david@email.com', '555-1004', 'customer123', 'Denver', 'CO', '321 Elm St');

-- Insert Admin Users
INSERT INTO Users (username, password, role, name, email) VALUES
('admin', 'admin123', 'admin', 'System Administrator', 'admin@retail.com'),
('manager', 'manager123', 'manager', 'Store Manager', 'manager@retail.com'),
('staff', 'staff123', 'staff', 'Sales Staff', 'staff@retail.com');

-- Create Indexes for better performance
CREATE INDEX idx_product_category ON Product(category_id);
CREATE INDEX idx_product_sku ON Product(sku);
CREATE INDEX idx_product_status ON Product(status);
CREATE INDEX idx_customer_email ON Customer(email);
CREATE INDEX idx_orders_customer ON Orders(customer_id);
CREATE INDEX idx_orders_date ON Orders(order_date);
CREATE INDEX idx_order_items_order ON Order_Item(order_id);
CREATE INDEX idx_order_items_product ON Order_Item(product_id);
CREATE INDEX idx_inventory_product ON Inventory_Transaction(product_id);
CREATE INDEX idx_inventory_date ON Inventory_Transaction(transaction_date);

-- Create Views for common queries
CREATE VIEW ProductInventory AS
SELECT 
    p.product_id,
    p.name,
    p.description,
    p.price,
    p.stock_quantity,
    p.min_stock_level,
    p.sku,
    p.barcode,
    p.supplier,
    p.cost_price,
    (p.price - p.cost_price) as profit_margin,
    c.category_name,
    p.status,
    CASE 
        WHEN p.stock_quantity <= p.min_stock_level THEN 'Low Stock'
        WHEN p.stock_quantity = 0 THEN 'Out of Stock'
        ELSE 'In Stock'
    END as stock_status
FROM Product p
LEFT JOIN Category c ON p.category_id = c.category_id;

CREATE VIEW SalesSummary AS
SELECT 
    DATE(o.order_date) as sale_date,
    COUNT(o.order_id) as total_orders,
    SUM(o.total_amount) as total_revenue,
    AVG(o.total_amount) as average_order_value,
    COUNT(DISTINCT o.customer_id) as unique_customers
FROM Orders o
WHERE o.status != 'cancelled'
GROUP BY DATE(o.order_date);

-- Triggers
DELIMITER $$

-- Trigger to update product stock when order is placed
CREATE TRIGGER update_stock_on_sale
AFTER INSERT ON Order_Item
FOR EACH ROW
BEGIN
    UPDATE Product 
    SET stock_quantity = stock_quantity - NEW.quantity,
        updated_at = CURRENT_TIMESTAMP
    WHERE product_id = NEW.product_id;
    
    -- Record inventory transaction
    INSERT INTO Inventory_Transaction (
        product_id, transaction_type, quantity_change, 
        reference_id, reference_type, stock_before, stock_after
    )
    SELECT 
        NEW.product_id, 'sale', -NEW.quantity, 
        NEW.order_id, 'order', 
        stock_quantity + NEW.quantity, stock_quantity
    FROM Product 
    WHERE product_id = NEW.product_id;
END$$

-- Trigger to restore stock when order is cancelled
CREATE TRIGGER restore_stock_on_cancel
AFTER UPDATE ON Orders
FOR EACH ROW
BEGIN
    IF NEW.status = 'cancelled' AND OLD.status != 'cancelled' THEN
        -- Update stock for all items in the cancelled order
        UPDATE Product p
        JOIN Order_Item oi ON p.product_id = oi.product_id
        SET p.stock_quantity = p.stock_quantity + oi.quantity,
            p.updated_at = CURRENT_TIMESTAMP
        WHERE oi.order_id = NEW.order_id;
        
        -- Record inventory transactions for restored items
        INSERT INTO Inventory_Transaction (
            product_id, transaction_type, quantity_change,
            reference_id, reference_type, stock_before, stock_after
        )
        SELECT 
            oi.product_id, 'return', oi.quantity,
            NEW.order_id, 'order',
            p.stock_quantity - oi.quantity, p.stock_quantity
        FROM Order_Item oi
        JOIN Product p ON oi.product_id = p.product_id
        WHERE oi.order_id = NEW.order_id;
    END IF;
END$$

DELIMITER ;

-- Stored Procedures
DELIMITER $$

-- Add new product
CREATE PROCEDURE AddProduct(
    IN p_name VARCHAR(255),
    IN p_description TEXT,
    IN p_price DECIMAL(10,2),
    IN p_stock INT,
    IN p_category_id INT,
    IN p_sku VARCHAR(100),
    IN p_supplier VARCHAR(255),
    IN p_cost_price DECIMAL(10,2),
    IN p_min_stock INT,
    OUT p_product_id INT
)
BEGIN
    INSERT INTO Product (name, description, price, stock_quantity, category_id, sku, supplier, cost_price, min_stock_level)
    VALUES (p_name, p_description, p_price, p_stock, p_category_id, p_sku, p_supplier, p_cost_price, p_min_stock);
    
    SET p_product_id = LAST_INSERT_ID();
    
    SELECT 'Product added successfully' as message;
END$$

-- Update stock
CREATE PROCEDURE UpdateStock(
    IN p_product_id INT,
    IN p_quantity_change INT,
    IN p_transaction_type VARCHAR(20),
    IN p_notes TEXT,
    IN p_user_id INT,
    OUT p_new_stock INT
)
BEGIN
    DECLARE v_current_stock INT;
    
    SELECT stock_quantity INTO v_current_stock FROM Product WHERE product_id = p_product_id;
    
    UPDATE Product
    SET stock_quantity = stock_quantity + p_quantity_change,
        updated_at = CURRENT_TIMESTAMP
    WHERE product_id = p_product_id;
    
    SELECT stock_quantity INTO p_new_stock FROM Product WHERE product_id = p_product_id;
    
    -- Record inventory transaction
    INSERT INTO Inventory_Transaction (
        product_id, transaction_type, quantity_change,
        reference_type, notes, created_by,
        stock_before, stock_after
    )
    VALUES (
        p_product_id, p_transaction_type, p_quantity_change,
        'manual', p_notes, p_user_id,
        v_current_stock, p_new_stock
    );
    
    SELECT CONCAT('Stock updated. New quantity: ', p_new_stock) as message;
END$$

-- Get low stock products
CREATE PROCEDURE GetLowStockProducts()
BEGIN
    SELECT 
        p.product_id,
        p.name,
        p.stock_quantity,
        p.min_stock_level,
        c.category_name,
        (p.min_stock_level - p.stock_quantity) as needed_quantity
    FROM Product p
    JOIN Category c ON p.category_id = c.category_id
    WHERE p.stock_quantity <= p.min_stock_level
    ORDER BY (p.min_stock_level - p.stock_quantity) DESC;
END$$

-- Get sales report for date range
CREATE PROCEDURE GetSalesReport(
    IN p_start_date DATE,
    IN p_end_date DATE
)
BEGIN
    SELECT 
        DATE(o.order_date) as sale_date,
        COUNT(o.order_id) as total_orders,
        SUM(o.total_amount) as total_revenue,
        AVG(o.total_amount) as average_order_value,
        COUNT(DISTINCT o.customer_id) as unique_customers,
        SUM(CASE WHEN o.status = 'delivered' THEN 1 ELSE 0 END) as delivered_orders
    FROM Orders o
    WHERE DATE(o.order_date) BETWEEN p_start_date AND p_end_date
      AND o.status != 'cancelled'
    GROUP BY DATE(o.order_date)
    ORDER BY sale_date;
END$$

-- Get top selling products
CREATE PROCEDURE GetTopSellingProducts(IN p_limit INT)
BEGIN
    SELECT 
        p.product_id,
        p.name,
        c.category_name,
        SUM(oi.quantity) as total_sold,
        SUM(oi.subtotal) as total_revenue,
        COUNT(DISTINCT oi.order_id) as order_count
    FROM Product p
    JOIN Order_Item oi ON p.product_id = oi.product_id
    JOIN Orders o ON oi.order_id = o.order_id
    JOIN Category c ON p.category_id = c.category_id
    WHERE o.status != 'cancelled'
    GROUP BY p.product_id, p.name, c.category_name
    ORDER BY total_sold DESC
    LIMIT p_limit;
END$$

DELIMITER ;

-- Functions
DELIMITER $$

-- Calculate profit margin for a product
CREATE FUNCTION GetProfitMargin(p_product_id INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_price DECIMAL(10,2);
    DECLARE v_cost DECIMAL(10,2);
    
    SELECT price, cost_price INTO v_price, v_cost
    FROM Product WHERE product_id = p_product_id;
    
    RETURN IFNULL(v_price - v_cost, 0);
END$$

-- Get total stock value for category
CREATE FUNCTION GetCategoryStockValue(p_category_id INT)
RETURNS DECIMAL(15,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE total_value DECIMAL(15,2);
    
    SELECT SUM(stock_quantity * price)
    INTO total_value
    FROM Product
    WHERE category_id = p_category_id AND stock_quantity > 0;
    
    RETURN IFNULL(total_value, 0);
END$$

DELIMITER ;

-- Sample Data for Testing
-- Insert some sample orders
INSERT INTO Orders (customer_id, total_amount, status, payment_method, payment_status, shipping_address) VALUES
(1, 1275.50, 'delivered', 'credit_card', 'paid', '123 Main St, Boston, MA'),
(2, 89.99, 'processing', 'debit_card', 'paid', '456 Oak Ave, Seattle, WA'),
(3, 156.48, 'shipped', 'paypal', 'paid', '789 Pine Rd, Miami, FL');

-- Insert order items
INSERT INTO Order_Item (order_id, product_id, quantity, price_at_purchase) VALUES
(1, 1, 1, 1200.00),  -- Laptop
(1, 2, 3, 25.50),     -- Wireless Mouse
(2, 5, 2, 45.00),     -- Denim Jeans
(3, 9, 1, 65.00),     -- Coffee Maker
(3, 10, 2, 45.99);    -- Blender

-- Insert sample purchase order
INSERT INTO Purchase_Order (supplier_id, order_date, expected_delivery_date, status, total_amount) VALUES
(1, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 7 DAY), 'pending', 5000.00);

-- Insert purchase order items
INSERT INTO Purchase_Order_Item (purchase_order_id, product_id, quantity, unit_cost) VALUES
(1, 1, 5, 800.00),    -- 5 Laptops
(1, 2, 20, 15.00);    -- 20 Mice

-- Insert sample inventory transactions
INSERT INTO Inventory_Transaction (
    product_id, transaction_type, quantity_change, 
    reference_id, reference_type, stock_before, stock_after, notes
) VALUES
(1, 'purchase', 5, 1, 'purchase_order', 20, 25, 'Initial stock from supplier'),
(2, 'purchase', 20, 1, 'purchase_order', 80, 100, 'Initial stock from supplier'),
(1, 'sale', -1, 1, 'order', 25, 24, 'Sold to customer'),
(2, 'sale', -3, 1, 'order', 100, 97, 'Sold 3 units to customer');

SELECT 'Retail Inventory Management System setup completed successfully!' as status;
