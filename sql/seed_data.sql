-- Seed data for online_shopping_db
-- Run after full_schema.sql

USE online_shopping_db;

-- Categories (id will auto-generate if not already present)
INSERT INTO Category (category_name, description) VALUES
 ('Electronics','Electronic devices')
,('Clothing','Fashion')
,('Books','Books')
,('Home & Kitchen','Home appliances')
,('Sports','Sports equipment')
ON DUPLICATE KEY UPDATE description=VALUES(description);

-- Customers (using plain passwords for demo)
INSERT INTO Customer (name, email, phone, password, city, state, pin, address)
VALUES
 ('Alice', 'alice@example.com', '9000000001', 'alice123', 'Mumbai', 'MH', '400001', 'Colaba, Mumbai'),
 ('Bob',   'bob@example.com',   '9000000002', 'bob123',   'Bengaluru', 'KA', '560001', 'MG Road, Bengaluru')
ON DUPLICATE KEY UPDATE phone=VALUES(phone);

-- Products (image_url stores only filename; files expected in DBMS/PICTURES)
-- Ensure files exist in: c:/Users/shukl/OneDrive/Desktop/DBMS/PICTURES/
INSERT INTO Product (name, description, price, stock_quantity, category_id, image_url)
VALUES
 ('Samsung Galaxy S24', 'Smartphone', 79999.00, 50, (SELECT category_id FROM Category WHERE category_name='Electronics'), 'phone.jpg'),
 ('Sony WH-1000XM5', 'Headphones', 29999.00, 100, (SELECT category_id FROM Category WHERE category_name='Electronics'), 'hearphone.jpg'),
 ('Levi Jeans', 'Denim', 2999.00, 200, (SELECT category_id FROM Category WHERE category_name='Clothing'), 'JEANS.jpg'),
 ('Nike Shoes', 'Running', 5999.00, 150, (SELECT category_id FROM Category WHERE category_name='Sports'), 'nike.jpg'),
 ('The Alchemist', 'Novel', 399.00, 300, (SELECT category_id FROM Category WHERE category_name='Books'), 'book.jpg'),
 ('Mixer', 'Grinder', 3999.00, 80, (SELECT category_id FROM Category WHERE category_name='Home & Kitchen'), 'mixer.jpg'),
 ('Yoga Mat', 'Mat', 1299.00, 120, (SELECT category_id FROM Category WHERE category_name='Sports'), 'yogamat.jpg'),
 ('Formal Shirt', 'Shirt', 1499.00, 180, (SELECT category_id FROM Category WHERE category_name='Clothing'), 'formal.jpg'),
 ('Harry Potter', 'Series', 3999.00, 50, (SELECT category_id FROM Category WHERE category_name='Books'), 'harry.jpg'),
 ('Smart Watch', 'Watch', 4999.00, 90, (SELECT category_id FROM Category WHERE category_name='Electronics'), 'smartwatch.jpg');

-- Wishlist for Alice
INSERT IGNORE INTO Wishlist (customer_id, product_id)
SELECT c.customer_id, p.product_id FROM Customer c, Product p
WHERE c.email='alice@example.com' AND p.name IN ('Samsung Galaxy S24','The Alchemist');

-- A few reviews

-- Samsung Galaxy S24 by Alice
SET @pid := (SELECT product_id FROM Product WHERE name='Samsung Galaxy S24' LIMIT 1);
SET @cid := (SELECT customer_id FROM Customer WHERE email='alice@example.com' LIMIT 1);
INSERT INTO Review (product_id, customer_id, rating, comment)
VALUES (@pid, @cid, 5, 'Excellent product!');

SET @pid := (SELECT product_id FROM Product WHERE name='Sony WH-1000XM5' LIMIT 1);
SET @cid := (SELECT customer_id FROM Customer WHERE email='alice@example.com' LIMIT 1);
INSERT INTO Review (product_id, customer_id, rating, comment)
VALUES (@pid, @cid, 4, 'Great noise cancellation.');

-- Create an active cart for Alice with a couple items
INSERT INTO Cart (customer_id, status) SELECT customer_id, 'active' FROM Customer WHERE email='alice@example.com'
ON DUPLICATE KEY UPDATE updated_date=CURRENT_TIMESTAMP;

-- Find Alice's active cart id
SET @alice_id = (SELECT customer_id FROM Customer WHERE email='alice@example.com');
SET @cart_id = (SELECT cart_id FROM Cart WHERE customer_id=@alice_id AND status='active' ORDER BY created_date DESC LIMIT 1);

-- Add items to her cart (INSERT IGNORE to avoid duplicates if re-run)
INSERT IGNORE INTO Cart_Item (cart_id, product_id, quantity)
SELECT @cart_id, p.product_id, 1 FROM Product p WHERE p.name='Samsung Galaxy S24';
INSERT IGNORE INTO Cart_Item (cart_id, product_id, quantity)
SELECT @cart_id, p.product_id, 2 FROM Product p WHERE p.name='The Alchemist';

-- Create a completed order for Bob to have some sales data
SET @bob_id = (SELECT customer_id FROM Customer WHERE email='bob@example.com');
INSERT INTO Orders (customer_id, total_amount, status, shipping_address, payment_method, transaction_status)
VALUES (@bob_id, 9998.00, 'delivered', 'MG Road, Bengaluru', 'UPI', 'success');
SET @order_id = LAST_INSERT_ID();

-- Order items (prices as of now; you can also select p.price at runtime)
INSERT INTO Order_Item (order_id, product_id, quantity, price_at_purchase, subtotal)
SELECT @order_id, p.product_id, 1, p.price, p.price FROM Product p WHERE p.name='Sony WH-1000XM5';
INSERT INTO Order_Item (order_id, product_id, quantity, price_at_purchase, subtotal)
SELECT @order_id, p.product_id, 2, p.price, p.price*2 FROM Product p WHERE p.name='Formal Shirt';

INSERT INTO Payment (order_id, payment_method, transaction_status)
VALUES (@order_id, 'UPI', 'success');

SELECT DISTINCT p.product_id, p.name
FROM `Orders` o
JOIN Order_Item oi ON o.order_id = oi.order_id
JOIN Product p ON oi.product_id = p.product_id
LEFT JOIN Review r
  ON r.product_id = p.product_id
 AND r.customer_id = o.customer_id
WHERE o.customer_id = 1
  AND o.status = 'delivered'
  AND r.review_id IS NULL
ORDER BY p.name;



-- Normalize image_url values to filenames only (safe to re-run)
UPDATE Product SET image_url = TRIM(REPLACE(image_url, '\\', '/'));
UPDATE Product SET image_url = SUBSTRING_INDEX(image_url, '/', -1);
