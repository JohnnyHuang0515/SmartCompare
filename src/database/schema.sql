-- src/database/schema.sql

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
    product_id INT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    product_url VARCHAR(1000) NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    record_date DATE DEFAULT (CURRENT_DATE), -- ✅ 加這個，改成每天唯一
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE (product_id, platform, record_date)
);

 -- 對商品名稱建立索引，加速搜尋
CREATE INDEX idx_products_name ON products(name(255));
CREATE INDEX idx_prices_product_id ON prices(product_id);
CREATE INDEX idx_prices_platform ON prices(platform);