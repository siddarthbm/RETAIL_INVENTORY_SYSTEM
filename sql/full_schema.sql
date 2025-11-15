-- Full schema for online_shopping_db
-- Run in MySQL Workbench or CLI
-- Example CLI: mysql -u root -p < c:/Users/shukl/OneDrive/Desktop/DBMS/sql/full_schema.sql

-- Safe defaults
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- Create DB
CREATE DATABASE IF NOT EXISTS online_shopping_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE online_shopping_db;



-- Core tables
CREATE TABLE Customer (
  customer_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  phone VARCHAR(20) UNIQUE,
  password VARCHAR(255) NOT NULL,
  city VARCHAR(100),
  state VARCHAR(100),
  pin VARCHAR(10),
  address TEXT,
  registration_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE Category (
  category_id INT AUTO_INCREMENT PRIMARY KEY,
  category_name VARCHAR(100) NOT NULL UNIQUE,
  description VARCHAR(255),
  created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE Product (
  product_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NOT NULL,
  description TEXT,
  price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
  stock_quantity INT NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
  category_id INT,
  image_url VARCHAR(500),
  average_rating DECIMAL(3,2) DEFAULT 0.00,
  created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_product_category FOREIGN KEY (category_id) REFERENCES Category(category_id) ON DELETE SET NULL ON UPDATE CASCADE,
  INDEX idx_product_category (category_id),
  INDEX idx_product_name (name)
) ENGINE=InnoDB;

CREATE TABLE Wishlist (
  customer_id INT NOT NULL,
  product_id INT NOT NULL,
  added_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (customer_id, product_id),
  CONSTRAINT fk_wishlist_customer FOREIGN KEY (customer_id) REFERENCES Customer(customer_id) ON DELETE CASCADE,
  CONSTRAINT fk_wishlist_product FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE Review (
  review_id INT AUTO_INCREMENT PRIMARY KEY,
  product_id INT NOT NULL,
  customer_id INT NOT NULL,
  rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment TEXT,
  review_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_review_product FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE CASCADE,
  CONSTRAINT fk_review_customer FOREIGN KEY (customer_id) REFERENCES Customer(customer_id) ON DELETE CASCADE,
  INDEX idx_review_product (product_id),
  INDEX idx_review_customer (customer_id)
) ENGINE=InnoDB;

CREATE TABLE Cart (
  cart_id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  status ENUM('active','completed') NOT NULL DEFAULT 'active',
  created_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_date TIMESTAMP NULL DEFAULT NULL,
  CONSTRAINT fk_cart_customer FOREIGN KEY (customer_id) REFERENCES Customer(customer_id) ON DELETE CASCADE,
  INDEX idx_cart_customer_status (customer_id, status)
) ENGINE=InnoDB;

CREATE TABLE Cart_Item (
  cart_item_id INT AUTO_INCREMENT PRIMARY KEY,
  cart_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT NOT NULL CHECK (quantity > 0),
  CONSTRAINT fk_ci_cart FOREIGN KEY (cart_id) REFERENCES Cart(cart_id) ON DELETE CASCADE,
  CONSTRAINT fk_ci_product FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE CASCADE,
  UNIQUE KEY uq_cart_product (cart_id, product_id)
) ENGINE=InnoDB;

CREATE TABLE Orders (
  order_id INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT NOT NULL,
  order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  total_amount DECIMAL(10,2) NOT NULL CHECK (total_amount >= 0),
  status ENUM('pending','processing','shipped','delivered','cancelled') NOT NULL DEFAULT 'pending',
  shipping_address TEXT,
  payment_method VARCHAR(50),
  transaction_status VARCHAR(50) DEFAULT 'processing',
  delivery_date TIMESTAMP NULL DEFAULT NULL,
  CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES Customer(customer_id) ON DELETE CASCADE,
  INDEX idx_orders_customer_date (customer_id, order_date)
) ENGINE=InnoDB;

CREATE TABLE Order_Item (
  order_item_id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  product_id INT NOT NULL,
  quantity INT NOT NULL CHECK (quantity > 0),
  price_at_purchase DECIMAL(10,2) NOT NULL CHECK (price_at_purchase >= 0),
  subtotal DECIMAL(10,2) NOT NULL CHECK (subtotal >= 0),
  CONSTRAINT fk_oi_order FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE,
  CONSTRAINT fk_oi_product FOREIGN KEY (product_id) REFERENCES Product(product_id) ON DELETE RESTRICT,
  INDEX idx_oi_order (order_id)
) ENGINE=InnoDB;

CREATE TABLE Payment (
  payment_id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  payment_method VARCHAR(50) NOT NULL,
  transaction_status VARCHAR(50) NOT NULL,
  transaction_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_payment_order FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE,
  INDEX idx_payment_order (order_id)
) ENGINE=InnoDB;

SET FOREIGN_KEY_CHECKS = 1;

-- Triggers
DELIMITER $$

-- Keep Cart.updated_date fresh on item changes
CREATE TRIGGER trg_cart_item_ai AFTER INSERT ON Cart_Item
FOR EACH ROW
BEGIN
  UPDATE Cart SET updated_date = CURRENT_TIMESTAMP WHERE cart_id = NEW.cart_id;
END $$

CREATE TRIGGER trg_cart_item_au AFTER UPDATE ON Cart_Item
FOR EACH ROW
BEGIN
  UPDATE Cart SET updated_date = CURRENT_TIMESTAMP WHERE cart_id = NEW.cart_id;
END $$

CREATE TRIGGER trg_cart_item_ad AFTER DELETE ON Cart_Item
FOR EACH ROW
BEGIN
  UPDATE Cart SET updated_date = CURRENT_TIMESTAMP WHERE cart_id = OLD.cart_id;
END $$

-- Maintain Product.average_rating when reviews change
CREATE TRIGGER trg_review_ai AFTER INSERT ON Review
FOR EACH ROW
BEGIN
  UPDATE Product p
  SET p.average_rating = (
    SELECT COALESCE(AVG(r.rating),0)
    FROM Review r WHERE r.product_id = NEW.product_id
  )
  WHERE p.product_id = NEW.product_id;
END $$

CREATE TRIGGER trg_review_au AFTER UPDATE ON Review
FOR EACH ROW
BEGIN
  UPDATE Product p
  SET p.average_rating = (
    SELECT COALESCE(AVG(r.rating),0)
    FROM Review r WHERE r.product_id = NEW.product_id
  )
  WHERE p.product_id = NEW.product_id;
END $$

CREATE TRIGGER trg_review_ad AFTER DELETE ON Review
FOR EACH ROW
BEGIN
  UPDATE Product p
  SET p.average_rating = (
    SELECT COALESCE(AVG(r.rating),0)
    FROM Review r WHERE r.product_id = OLD.product_id
  )
  WHERE p.product_id = OLD.product_id;
END $$

-- Prevent negative stock on Product updates
CREATE TRIGGER trg_product_no_negative BEFORE UPDATE ON Product
FOR EACH ROW
BEGIN
  IF NEW.stock_quantity < 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Stock cannot be negative';
  END IF;
END $$

-- Functions
-- Total spending function
DELIMITER $$

CREATE FUNCTION get_customer_total_spending(p_customer_id INT)
RETURNS DECIMAL(12,2)
DETERMINISTIC
BEGIN
  DECLARE v_total DECIMAL(12,2);

  SELECT COALESCE(SUM(total_amount), 0)
  INTO v_total
  FROM Orders
  WHERE customer_id = p_customer_id
    AND status <> 'cancelled';

  RETURN v_total;
END$$

DELIMITER ;

-- Procedures
-- Search products with optional filters
DELIMITER $$

CREATE PROCEDURE search_products(
  IN p_name_like VARCHAR(255),
  IN p_category_id INT,
  IN p_min_price DECIMAL(10,2),
  IN p_max_price DECIMAL(10,2)
)
BEGIN
  SELECT 
    p.product_id,
    p.name,
    p.description,
    p.price,
    p.stock_quantity,
    p.category_id,
    p.image_url,
    p.average_rating
  FROM Product p
  WHERE (p_name_like IS NULL OR p.name LIKE p_name_like)
    AND (p_category_id IS NULL OR p.category_id = p_category_id)
    AND (p_min_price IS NULL OR p.price >= p_min_price)
    AND (p_max_price IS NULL OR p.price <= p_max_price)
  ORDER BY p.product_id DESC;
END $$

-- Add to cart (validates stock)
CREATE PROCEDURE add_to_cart(IN p_customer_id INT, IN p_product_id INT, IN p_quantity INT)
BEGIN
  DECLARE v_cart_id INT;
  DECLARE v_stock INT;

  SELECT stock_quantity INTO v_stock FROM Product WHERE product_id = p_product_id;
  IF v_stock IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Product not found';
  ELSEIF v_stock < p_quantity THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient stock available';
  END IF;

  SELECT cart_id INTO v_cart_id FROM Cart WHERE customer_id = p_customer_id AND status = 'active' LIMIT 1;
  IF v_cart_id IS NULL THEN
    INSERT INTO Cart (customer_id, status, created_date) VALUES (p_customer_id, 'active', CURRENT_TIMESTAMP);
    SET v_cart_id = LAST_INSERT_ID();
  END IF;

  IF EXISTS (SELECT 1 FROM Cart_Item WHERE cart_id = v_cart_id AND product_id = p_product_id) THEN
    UPDATE Cart_Item SET quantity = quantity + p_quantity WHERE cart_id = v_cart_id AND product_id = p_product_id;
  ELSE
    INSERT INTO Cart_Item (cart_id, product_id, quantity) VALUES (v_cart_id, p_product_id, p_quantity);
  END IF;

  UPDATE Cart SET updated_date = CURRENT_TIMESTAMP WHERE cart_id = v_cart_id;

  SELECT 'Item added to cart successfully' AS message;
END $$
DELIMITER ;

-- Place order (transactional)

DELIMITER $$
CREATE PROCEDURE place_order(IN p_user_id INT, IN p_shipping_address TEXT, IN p_payment_method VARCHAR(50))
BEGIN
  DECLARE v_cart_id INT;
  DECLARE v_order_id INT;
  DECLARE v_total_amount DECIMAL(10,2);

  START TRANSACTION;
  -- get active cart
  SELECT cart_id INTO v_cart_id FROM Cart WHERE customer_id = p_user_id AND status = 'active' LIMIT 1 FOR UPDATE;
  IF v_cart_id IS NULL THEN
    ROLLBACK; SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No active cart found for customer';
  END IF;

  -- compute total
  SELECT COALESCE(SUM(ci.quantity * p.price), 0) INTO v_total_amount
  FROM Cart_Item ci JOIN Product p ON ci.product_id = p.product_id
  WHERE ci.cart_id = v_cart_id;
  IF v_total_amount = 0 THEN
    ROLLBACK; SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cart is empty';
  END IF;

  -- lock products to validate stock
  SELECT 1 FROM Cart_Item ci JOIN Product p ON ci.product_id = p.product_id WHERE ci.cart_id = v_cart_id FOR UPDATE;
  IF EXISTS (
    SELECT 1 FROM Cart_Item ci JOIN Product p ON ci.product_id = p.product_id
    WHERE ci.cart_id = v_cart_id AND ci.quantity > p.stock_quantity
  ) THEN
    ROLLBACK; SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'One or more items exceed stock';
  END IF;

  INSERT INTO Orders (customer_id, order_date, total_amount, status, shipping_address, payment_method, transaction_status)
  VALUES (p_user_id, CURRENT_TIMESTAMP, v_total_amount, 'pending', p_shipping_address, p_payment_method, 'processing');
  SET v_order_id = LAST_INSERT_ID();

  INSERT INTO Order_Item (order_id, product_id, quantity, price_at_purchase, subtotal)
  SELECT v_order_id, ci.product_id, ci.quantity, p.price, (ci.quantity * p.price)
  FROM Cart_Item ci JOIN Product p ON ci.product_id = p.product_id
  WHERE ci.cart_id = v_cart_id;

  -- decrement stock
  UPDATE Product p
  JOIN (
    SELECT ci.product_id, SUM(ci.quantity) AS qty FROM Cart_Item ci WHERE ci.cart_id = v_cart_id GROUP BY ci.product_id
  ) x ON x.product_id = p.product_id
  SET p.stock_quantity = p.stock_quantity - x.qty;

  -- clear cart
  DELETE FROM Cart_Item WHERE cart_id = v_cart_id;
  UPDATE Cart SET status = 'completed', updated_date = CURRENT_TIMESTAMP WHERE cart_id = v_cart_id;

  -- create payment row (placeholder status)
  INSERT INTO Payment (order_id, payment_method, transaction_status)
  VALUES (v_order_id, p_payment_method, 'processing');

  COMMIT;

  SELECT v_order_id AS order_id, v_total_amount AS total_amount;
END $$

-- Update order status
CREATE PROCEDURE update_order_status(IN p_order_id INT, IN p_new_status VARCHAR(20))
BEGIN
  UPDATE Orders SET status = p_new_status,
                    delivery_date = CASE WHEN p_new_status = 'delivered' THEN CURRENT_TIMESTAMP ELSE delivery_date END
  WHERE order_id = p_order_id;
  SELECT ROW_COUNT() AS affected_rows;
END $$

-- Get orders for a customer
CREATE PROCEDURE get_customer_orders(IN p_customer_id INT)
BEGIN
  SELECT o.order_id, o.order_date, o.total_amount, o.status, o.shipping_address,
         o.payment_method, o.transaction_status, o.delivery_date
  FROM Orders o
  WHERE o.customer_id = p_customer_id
  ORDER BY o.order_date DESC;
END $$

-- Generate sales report for date range
CREATE PROCEDURE generate_sales_report(IN p_start_date DATE, IN p_end_date DATE)
BEGIN
  SELECT DATE(o.order_date) AS order_date,
         SUM(o.total_amount) AS total_revenue,
         COUNT(*) AS total_orders,
         COUNT(DISTINCT o.customer_id) AS unique_customers
  FROM Orders o
  WHERE DATE(o.order_date) BETWEEN p_start_date AND p_end_date
    AND o.status <> 'cancelled'
  GROUP BY DATE(o.order_date)
  ORDER BY order_date;
END $$

-- Trending products by quantity sold in last N days
CREATE PROCEDURE get_trending_products(IN p_limit INT)
BEGIN
  SELECT p.product_id, p.name, COALESCE(SUM(oi.quantity),0) AS total_quantity_sold
  FROM Product p
  LEFT JOIN Order_Item oi ON oi.product_id = p.product_id
  LEFT JOIN Orders o ON o.order_id = oi.order_id AND o.order_date >= (CURRENT_TIMESTAMP - INTERVAL 30 DAY)
  GROUP BY p.product_id, p.name
  ORDER BY total_quantity_sold DESC, p.product_id DESC
  LIMIT p_limit;
END $$

DELIMITER ;

-- Seed minimal categories (optional)
INSERT INTO Category (category_name, description)
VALUES ('Electronics','Electronic devices')
ON DUPLICATE KEY UPDATE description=VALUES(description);
INSERT INTO Category (category_name, description)
VALUES ('Clothing','Fashion')
ON DUPLICATE KEY UPDATE description=VALUES(description);
INSERT INTO Category (category_name, description)
VALUES ('Books','Books')
ON DUPLICATE KEY UPDATE description=VALUES(description);
INSERT INTO Category (category_name, description)
VALUES ('Home & Kitchen','Home appliances')
ON DUPLICATE KEY UPDATE description=VALUES(description);
INSERT INTO Category (category_name, description)
VALUES ('Sports','Sports equipment')
ON DUPLICATE KEY UPDATE description=VALUES(description);
