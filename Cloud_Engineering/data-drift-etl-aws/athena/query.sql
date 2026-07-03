-- Sample SQL queries for analyzing product data

-- 1. View all products
SELECT * FROM "data_drift_db"."products" LIMIT 10;

-- 2. Top 10 most expensive products
SELECT title, brand, price, rating 
FROM "data_drift_db"."products" 
ORDER BY price DESC 
LIMIT 10;

-- 3. Products with highest rating
SELECT title, brand, rating, price 
FROM "data_drift_db"."products" 
ORDER BY rating DESC 
LIMIT 10;

-- 4. Count products by category
SELECT category, COUNT(*) as product_count 
FROM "data_drift_db"."products" 
GROUP BY category 
ORDER BY product_count DESC;

-- 5. Products with low stock (under 10)
SELECT title, brand, stock, price 
FROM "data_drift_db"."products" 
WHERE stock < 10 
ORDER BY stock ASC;

-- 6. Average price by category
SELECT category, 
       ROUND(AVG(price), 2) as avg_price,
       COUNT(*) as count,
       MIN(price) as min_price,
       MAX(price) as max_price
FROM "data_drift_db"."products" 
GROUP BY category 
ORDER BY avg_price DESC;

-- 7. Products with discounts over 15%
SELECT title, brand, price, discount_percentage, 
       ROUND(price * (1 - discount_percentage/100), 2) as discounted_price
FROM "data_drift_db"."products" 
WHERE discount_percentage > 15 
ORDER BY discount_percentage DESC;

-- 8. Brand performance summary
SELECT brand, 
       COUNT(*) as product_count,
       ROUND(AVG(rating), 2) as avg_rating,
       ROUND(AVG(price), 2) as avg_price,
       SUM(stock) as total_stock
FROM "data_drift_db"."products" 
WHERE brand != ''
GROUP BY brand 
HAVING COUNT(*) > 1
ORDER BY product_count DESC;

-- 9. Out of stock products
SELECT title, brand, stock, price 
FROM "data_drift_db"."products" 
WHERE stock = 0;

-- 10. Products with best value (high rating, low price)
SELECT title, brand, price, rating, 
       ROUND(rating / price, 4) as value_score
FROM "data_drift_db"."products" 
WHERE price > 0
ORDER BY value_score DESC 
LIMIT 10;