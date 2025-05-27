-- src/database/schema.sql

-- 創建資料庫 (如果不存在)
CREATE DATABASE IF NOT EXISTS smartcompare_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用資料庫
USE smartcompare_db;

-- 商品表
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(500) NOT NULL, -- 商品名稱可能很長
    image_url VARCHAR(1000),    -- 圖片連結可能很長
    brand VARCHAR(255),
    -- 其他通用商品屬性，例如分類ID、描述等 (未來可擴充)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 價格表 (記錄每個商品在不同平台的價格歷史)
CREATE TABLE IF NOT EXISTS prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,       -- 外鍵，指向 products 表
    platform VARCHAR(50) NOT NULL, -- 電商平台名稱 (例如 'PChome', 'momo')
    price DECIMAL(10, 2) NOT NULL, -- 商品價格
    product_url VARCHAR(1000) NOT NULL, -- 該平台上的商品連結
    is_available BOOLEAN DEFAULT TRUE, -- 是否有庫存
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 價格更新時間
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE, -- 當商品被刪除時，其價格記錄也一併刪除
    UNIQUE (product_id, platform, last_updated) -- 確保同一商品在同一時間點同一平台只有一條價格記錄 (可調整為每天只記錄一次)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 索引 (為了查詢效能)
CREATE INDEX idx_products_name ON products(name(255)); -- 對商品名稱建立索引，加速搜尋
CREATE INDEX idx_prices_product_id ON prices(product_id);
CREATE INDEX idx_prices_platform ON prices(platform);