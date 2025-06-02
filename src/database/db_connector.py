# src/database/db_connector.py

import pymysql
from pymysql.cursors import DictCursor
from datetime import datetime, timedelta
from configparser import ConfigParser, NoOptionError
import os
import decimal

# --- 配置資料庫連接參數 ---
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = os.path.abspath(os.path.join(current_script_dir, '..', '..'))
config_path = os.path.join(project_root_dir, 'config.ini')

config = ConfigParser()
DB_CONFIG = {}
DB_NAME = '' # 將資料庫名稱獨立出來，方便初始化時使用

if not os.path.exists(config_path):
    print(f"Error: config.ini not found at {config_path}. Cannot proceed without database configuration.")
    raise FileNotFoundError(f"Missing config.ini at {config_path}. Please place it in the project root directory.")
else:
    config.read(config_path)

    if not config.has_section("DB_CONFIG"):
        print(
            f"Error: Section [DB_CONFIG] not found in {config_path}. Please ensure it contains database connection details.")
        raise ValueError(f"Missing [DB_CONFIG] section in {config_path}.")

    required_db_keys = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    for key in required_db_keys:
        try:
            DB_CONFIG[key.lower()] = config.get("DB_CONFIG", key)
        except NoOptionError:
            print(f"Error: Missing option '{key}' in section 'DB_CONFIG' in {config_path}.")
            raise
    DB_NAME = DB_CONFIG['db_name'] # 從 config.ini 獲取資料庫名稱

# --- 資料庫連接函數 ---
def get_db_connection(target_db_name=None):
    """
    獲取資料庫連接。
    target_db_name:
        - 如果為 None (預設)，則使用 DB_CONFIG['db_name'] 連接。
        - 如果為字符串 (例如 'mysql' 或具體資料庫名)，則連接到該名稱的資料庫。
        - **請注意：不建議傳遞空字串 ''，如果需要無資料庫連接，請直接傳遞 None。**
    """
    db_to_connect = target_db_name if target_db_name is not None else DB_CONFIG['db_name']

    try:
        conn = pymysql.connect(
            host=DB_CONFIG['db_host'],
            user=DB_CONFIG['db_user'],
            password=DB_CONFIG['db_password'],
            database=db_to_connect, # 將 None 傳遞給 database 參數表示不指定數據庫
            charset='utf8mb4',
            cursorclass=DictCursor
        )
        return conn
    except pymysql.Error as e:
        print(f"Error connecting to MySQL database: {e}")
        raise

def initialize_database():
    """
    第一次運行時自動創建資料庫和表格。
    """
    conn = None
    try:
        # 第一次連接時，嘗試連接到 MySQL 伺服器的 'mysql' 系統資料庫。
        # 這是最穩健的選擇，因為這個資料庫通常都存在。
        conn = get_db_connection(target_db_name='mysql')

        if not conn:
            print("無法連接到 MySQL 伺服器，請檢查配置和伺服器狀態。")
            return

        with conn.cursor() as cursor:
            # 1. 創建目標資料庫 (如果不存在)
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            print(f"資料庫 '{DB_NAME}' 已創建或已存在。")

            # 2. 使用新創建的資料庫
            cursor.execute(f"USE {DB_NAME};")

            # 3. 讀取並執行 schema.sql 中的表格創建語句
            schema_sql_path = os.path.join(project_root_dir, 'src', 'database', 'schema.sql')
            if not os.path.exists(schema_sql_path):
                print(f"錯誤：找不到 schema.sql 文件在 {schema_sql_path}")
                return

            with open(schema_sql_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()

            # 分割 SQL 語句並執行 (移除 CREATE DATABASE 和 USE database 語句，因為已經處理)
            statements = [s.strip() for s in sql_script.split(';') if s.strip() and not s.strip().upper().startswith(('CREATE DATABASE', 'USE '))]

            for statement in statements:
                try:
                    cursor.execute(statement)
                    # print(f"已執行 SQL 語句: {statement[:50]}...") # 調試時可開啟
                except pymysql.Error as e:
                    # 針對已存在的物件 (如表、索引) 錯誤，給出警告而不是中止
                    # 常見錯誤碼：1050 (Table already exists), 1061 (Duplicate key name), 1062 (Duplicate entry for key)
                    if e.args[0] in [1050, 1061, 1062] or "already exists" in str(e) or "Duplicate" in str(e) or "PRIMARY" in str(e) or "FOREIGN KEY" in str(e):
                        print(f"警告: 執行 SQL 語句時發生已知錯誤 (可能已存在): {statement[:50]}... - {e}")
                    else:
                        print(f"執行 SQL 語句時發生錯誤: {statement[:50]}... - {e}")
                        raise # 重新拋出其他嚴重的錯誤

            conn.commit()
            print("資料庫結構初始化完成。")

    except pymysql.Error as e:
        print(f"資料庫初始化失敗: {e}")
        if "Access denied for user" in str(e):
            print("請檢查您的 MySQL 用戶名和密碼是否正確，以及該用戶是否有足夠權限在 MySQL 伺服器上創建資料庫。")
        elif "Can't connect to MySQL server" in str(e):
            print("請確認 MySQL 伺服器是否正在運行且監聽正確的端口。")
        else:
            print(f"其他資料庫錯誤: {e}")
    except Exception as e:
        print(f"初始化過程中發生未知錯誤: {e}")
    finally:
        if conn:
            conn.close()

# --- 數據處理函數 (save_product_data, get_products_with_prices_by_keyword, get_comparison_data, _calculate_summary 保持不變) ---
# ... (這裡放置您之前給出的 save_product_data, get_products_with_prices_by_keyword 等函數)

def save_product_data(products_data: list[dict]):
    """
    保存或更新產品數據到資料庫。
    會檢查產品是否存在，如果存在則更新價格並設定 is_available。
    如果產品不存在，則插入新產品及其價格。
    使用 INSERT ... ON DUPLICATE KEY UPDATE 語句來處理重複鍵衝突。
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            for product_info in products_data:
                product_name = product_info['name']
                platform = product_info['platform']
                price = product_info['price']
                product_url = product_info['url']
                image_url = product_info.get('image', None)
                brand = product_info.get('brand', None)
                is_available = product_info.get('is_available', True)

                # 1. 查找或創建產品
                cursor.execute(
                    "SELECT id FROM products WHERE name = %s AND (brand = %s OR (brand IS NULL AND %s IS NULL))",
                    (product_name, brand, brand)
                )
                product_id_result = cursor.fetchone()

                product_id = None
                if product_id_result:
                    product_id = product_id_result['id']
                    # 更新產品的 updated_at 和 image_url (如果新的更好)
                    cursor.execute(
                        "UPDATE products SET image_url = COALESCE(%s, image_url), updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                        (image_url, product_id)
                    )
                else:
                    # 插入新產品
                    cursor.execute(
                        "INSERT INTO products (name, image_url, brand) VALUES (%s, %s, %s)",
                        (product_name, image_url, brand)
                    )
                    product_id = cursor.lastrowid # 獲取新插入的產品ID

                # 2. 使用 INSERT ... ON DUPLICATE KEY UPDATE 處理價格資訊
                # 如果 (product_id, platform, product_url) 組合已存在，則更新價格和可用性
                # 否則，插入新記錄
                cursor.execute(
                    """
                    INSERT INTO prices (product_id, platform, price, product_url, is_available)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        price = VALUES(price),
                        is_available = VALUES(is_available),
                        last_updated = CURRENT_TIMESTAMP;
                    """,
                    (product_id, platform, price, product_url, is_available)
                )
            conn.commit()
            print(f"Successfully saved/updated {len(products_data)} product entries.")
    except pymysql.Error as e:
        print(f"Database error during save_product_data: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def get_products_with_prices_by_keyword(keyword: str, freshness_hours: int = 24) -> dict:
    """
    根據關鍵字查詢資料庫中在 freshness_hours 內更新的商品數據。
    返回包含分組產品和統計信息的字典。
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 查詢符合關鍵字且在 freshness_hours 內更新的產品及其價格
            # 這裡需要 JOIN 兩個表
            query = """
            SELECT
                p.id AS product_id,
                p.name AS product_name,
                p.image_url,
                p.brand,
                pr.platform,
                pr.price,
                pr.product_url,
                pr.is_available,
                pr.last_updated
            FROM
                products p
            JOIN
                prices pr ON p.id = pr.product_id
            WHERE
                p.name LIKE %s
                AND pr.last_updated >= NOW() - INTERVAL %s HOUR
            ORDER BY
                p.name, pr.platform, pr.price;
            """
            cursor.execute(query, (f"%{keyword}%", freshness_hours))
            raw_results = cursor.fetchall()

            if not raw_results:
                return {"grouped_products": [], "summary": {"total_products": 0, "avg_savings": 0, "best_platform": "N/A"}}

            # 將扁平化的結果分組
            grouped_products = {}
            for row in raw_results:
                product_id = row['product_id']
                if product_id not in grouped_products:
                    grouped_products[product_id] = {
                        "id": product_id,
                        "name": row['product_name'],
                        "image": row['image_url'],
                        "brand": row['brand'],
                        "prices": [],
                        "lowest_price": float('inf'),
                        "highest_price": 0.0,
                        "min_price_platform": None
                    }

                price_entry = {
                    "platform": row['platform'],
                    "price": float(row['price']), # 轉換為浮點數
                    "url": row['product_url'],
                    "is_available": bool(row['is_available']),
                    "last_updated": row['last_updated'].isoformat() # 轉換為 ISO 格式字串
                }
                grouped_products[product_id]["prices"].append(price_entry)

                # 更新最低/最高價格
                if price_entry["is_available"] and price_entry["price"] < grouped_products[product_id]["lowest_price"]:
                    grouped_products[product_id]["lowest_price"] = price_entry["price"]
                    grouped_products[product_id]["min_price_platform"] = price_entry["platform"]
                if price_entry["is_available"] and price_entry["price"] > grouped_products[product_id]["highest_price"]:
                    grouped_products[product_id]["highest_price"] = price_entry["price"]


            final_grouped_products_list = list(grouped_products.values())

            # 對每個產品組內的價格進行排序 (最低價優先)
            for product_group in final_grouped_products_list:
                # 確保只有可用的價格才參與最低價排序，不可用的價格排在後面
                product_group["prices"].sort(key=lambda x: (not x["is_available"], x["price"]))

            # 計算總結統計
            summary = _calculate_summary(final_grouped_products_list)

            return {
                "grouped_products": final_grouped_products_list,
                "summary": summary
            }

    except pymysql.Error as e:
        print(f"Database error in get_products_with_prices_by_keyword: {e}")
        return {"grouped_products": [], "summary": {"total_products": 0, "avg_savings": 0, "best_platform": "N/A"}, "errors": [f"Database error: {e}"]}
    finally:
        if conn:
            conn.close()

def get_comparison_data(keyword: str) -> dict:
    """
    獲取所有與關鍵字相關的產品及其價格，不論新鮮度。
    主要用於當新鮮數據不足或爬蟲後獲取最新全量數據。
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 查詢所有符合關鍵字的產品及其所有價格
            query = """
            SELECT
                p.id AS product_id,
                p.name AS product_name,
                p.image_url,
                p.brand,
                pr.platform,
                pr.price,
                pr.product_url,
                pr.is_available,
                pr.last_updated
            FROM
                products p
            JOIN
                prices pr ON p.id = pr.product_id
            WHERE
                p.name LIKE %s
            ORDER BY
                p.name, pr.platform, pr.price;
            """
            cursor.execute(query, (f"%{keyword}%",))
            raw_results = cursor.fetchall()

            if not raw_results:
                return {"grouped_products": [], "summary": {"total_products": 0, "avg_savings": 0, "best_platform": "N/A"}}

            grouped_products = {}
            for row in raw_results:
                product_id = row['product_id']
                if product_id not in grouped_products:
                    grouped_products[product_id] = {
                        "id": product_id,
                        "name": row['product_name'],
                        "image": row['image_url'],
                        "brand": row['brand'],
                        "prices": [],
                        "lowest_price": float('inf'),
                        "highest_price": 0.0,
                        "min_price_platform": None
                    }

                price_entry = {
                    "platform": row['platform'],
                    "price": float(row['price']),
                    "url": row['product_url'],
                    "is_available": bool(row['is_available']),
                    "last_updated": row['last_updated'].isoformat()
                }
                grouped_products[product_id]["prices"].append(price_entry)

                # 更新最低/最高價格 (只考慮有庫存的價格)
                if price_entry["is_available"] and price_entry["price"] < grouped_products[product_id]["lowest_price"]:
                    grouped_products[product_id]["lowest_price"] = price_entry["price"]
                    grouped_products[product_id]["min_price_platform"] = price_entry["platform"]
                if price_entry["is_available"] and price_entry["price"] > grouped_products[product_id]["highest_price"]:
                    grouped_products[product_id]["highest_price"] = price_entry["price"]

            final_grouped_products_list = list(grouped_products.values())

            # 對每個產品組內的價格進行排序 (最低價優先)
            for product_group in final_grouped_products_list:
                # 確保只有可用的價格才參與最低價排序，不可用的價格排在後面
                product_group["prices"].sort(key=lambda x: (not x["is_available"], x["price"]))

            # 計算總結統計
            summary = _calculate_summary(final_grouped_products_list)

            return {
                "grouped_products": final_grouped_products_list,
                "summary": summary
            }

    except pymysql.Error as e:
        print(f"Database error in get_comparison_data: {e}")
        return {"grouped_products": [], "summary": {"total_products": 0, "avg_savings": 0, "best_platform": "N/A"}, "errors": [f"Database error: {e}"]}
    finally:
        if conn:
            conn.close()

def _calculate_summary(final_grouped_products_list: list) -> dict:
    """計算產品總結統計數據"""
    total_products_found = len(final_grouped_products_list)
    avg_savings = 0.0
    best_platform = "N/A"

    if total_products_found > 0:
        total_price_difference = 0
        total_items_for_avg = 0
        platform_lowest_count = {}

        for product_group in final_grouped_products_list:
            # 確保 product_group["prices"] 中有可用的價格
            available_prices = [p['price'] for p in product_group["prices"] if p['is_available']]

            if len(available_prices) > 1:
                min_price = min(available_prices)
                max_price = max(available_prices)

                total_price_difference += (max_price - min_price)
                total_items_for_avg += 1

            # 統計最佳平台
            if product_group["min_price_platform"]: # 確保有找到最低價的平台
                platform_lowest_count[product_group["min_price_platform"]] = platform_lowest_count.get(product_group["min_price_platform"], 0) + 1

        if total_items_for_avg > 0:
            avg_savings = total_price_difference / total_items_for_avg

        if platform_lowest_count:
            best_platform = max(platform_lowest_count, key=platform_lowest_count.get)

    return {
        "total_products": total_products_found,
        "avg_savings": float(f"{avg_savings:.2f}"), # 四捨五入到小數點後兩位
        "best_platform": best_platform
    }

# --- 測試區塊 ---
if __name__ == '__main__':
    initialize_database() # 在測試前先初始化資料庫

    # --- 您的測試數據 (來自之前的對話) ---
    test_products_to_save = [
        {
            'name': '測試商品A',
            'brand': 'TestBrand',
            'price': 1000.0,
            'url': 'http://test.com/a',
            'image': 'http://test.com/a.jpg',
            'platform': 'TestPlatform1',
            'is_available': True
        },
        {
            'name': '測試商品A',
            'brand': 'TestBrand',
            'price': 980.0,
            'url': 'http://test.com/b',
            'image': 'http://test.com/a.jpg',
            'platform': 'TestPlatform2',
            'is_available': True
        },
        {
            'name': '測試商品B',
            'brand': None, # 品牌可為 None
            'price': 1200.0,
            'url': 'http://test.com/c',
            'image': 'http://test.com/c.jpg',
            'platform': 'TestPlatform1',
            'is_available': False
        },
        {
            'name': '測試商品A', # 測試更新當天價格
            'brand': 'TestBrand',
            'price': 950.0,
            'url': 'http://test.com/a', # 這裡應該是 http://test.com/a 而不是 a_updated，因為是更新
            'image': 'http://test.com/a.jpg',
            'platform': 'TestPlatform1',
            'is_available': True
        }
    ]
    print("Saving test products...")
    save_product_data(test_products_to_save)
    print("Done saving.")

    print("\nQuerying '測試商品' (freshness_hours=1)...\n")
    comparison_results = get_products_with_prices_by_keyword("測試商品", 1)
    if comparison_results['grouped_products']:
        print(f"Found {len(comparison_results['grouped_products'])} fresh results:")
        for item in comparison_results['grouped_products']:
            print(item)
        print("Summary:", comparison_results['summary'])
    else:
        print("No fresh results found.")

    print("\nQuerying '測試商品' (get_comparison_data, all data)...\n")
    all_comparison_results = get_comparison_data("測試商品")
    if all_comparison_results['grouped_products']:
        print(f"Found {len(all_comparison_results['grouped_products'])} all results:")
        for item in all_comparison_results['grouped_products']:
            print(item)
        print("Summary:", all_comparison_results['summary'])
    else:
        print("No results found in general.")