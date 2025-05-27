# src/database/db_connector.py

import pymysql
import json
from datetime import datetime

# 從配置檔讀取資料庫資訊 (如果還沒建立 config.ini，可以先硬編碼)
# 建議您創建一個 config.ini，並用 configparser 來讀取
# 這裡先寫死，方便您測試
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'P@ssw0rd', # <-- 請替換為您的 MySQL 密碼
    'db': 'smartcompare_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor # 讓查詢結果返回字典格式
}

def get_db_connection():
    """建立並返回一個資料庫連接"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except pymysql.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def save_product_data(product_list: list[dict]):
    """
    將爬取到的商品資料存入資料庫。
    會檢查商品是否已存在，若存在則更新 prices 表，否則新增 products 和 prices 表。
    """
    connection = get_db_connection()
    if not connection:
        return

    try:
        with connection.cursor() as cursor:
            for product_data in product_list:
                name = product_data.get('name')
                platform = product_data.get('platform')
                price = product_data.get('price')
                url = product_data.get('url')
                image = product_data.get('image')
                is_available = product_data.get('is_available', True)

                if not all([name, platform, price, url]):
                    print(f"Skipping incomplete product data: {product_data}")
                    continue

                # 1. 檢查 products 表中是否已存在該商品 (以名稱為主要判斷依據，實際應用可能需要更精確的匹配，如UPC/EAN)
                # 這裡使用名稱和平台作為簡單的去重方式，考慮到不同平台可能名稱稍有差異，未來可引入模糊匹配
                sql_select_product = "SELECT id FROM products WHERE name = %s LIMIT 1"
                cursor.execute(sql_select_product, (name,))
                result = cursor.fetchone()

                product_id = None
                if result:
                    product_id = result['id']
                else:
                    # 商品不存在，插入新商品到 products 表
                    sql_insert_product = """
                    INSERT INTO products (name, image_url, brand)
                    VALUES (%s, %s, %s)
                    """
                    # 品牌可以從商品名稱或描述中提取，這裡簡化為空
                    cursor.execute(sql_insert_product, (name, image, None))
                    product_id = cursor.lastrowid # 獲取新插入的商品ID

                # 2. 插入或更新價格到 prices 表
                # 檢查今天是否已經有該商品在該平台的價格記錄
                today = datetime.now().strftime('%Y-%m-%d')
                sql_check_price_today = """
                SELECT id FROM prices
                WHERE product_id = %s AND platform = %s
                AND DATE(last_updated) = %s
                """
                cursor.execute(sql_check_price_today, (product_id, platform, today))
                price_record_today = cursor.fetchone()

                if price_record_today:
                    # 如果今天已有記錄，則更新價格
                    sql_update_price = """
                    UPDATE prices
                    SET price = %s, product_url = %s, is_available = %s, last_updated = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """
                    cursor.execute(sql_update_price, (price, url, is_available, price_record_today['id']))
                else:
                    # 否則插入新的價格記錄
                    sql_insert_price = """
                    INSERT INTO prices (product_id, platform, price, product_url, is_available)
                    VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql_insert_price, (product_id, platform, price, url, is_available))

            connection.commit() # 提交所有更改
            print(f"Successfully saved {len(product_list)} product data to DB.")
    except pymysql.Error as e:
        connection.rollback() # 出錯時回滾
        print(f"Database error during save_product_data: {e}")
    finally:
        connection.close()

def get_comparison_data(keyword: str) -> list[dict]:
    """
    從資料庫查詢指定關鍵字的商品比價資訊。
    返回每個商品在不同平台上的最新價格。
    """
    connection = get_db_connection()
    if not connection:
        return []

    results = []
    try:
        with connection.cursor() as cursor:
            # 複雜查詢：查找包含關鍵字的商品，並獲取其在各平台的最新價格
            # 這裡需要一個更精確的查詢，以獲取每個商品的最新價格。
            # 一種方法是使用子查詢或JOIN來找到每個 product_id 和 platform 的最新 last_updated
            sql_query = """
            SELECT
                p.id AS product_id,
                p.name AS product_name,
                p.image_url,
                pr.platform,
                pr.price,
                pr.product_url,
                pr.is_available,
                pr.last_updated
            FROM
                products AS p
            JOIN
                prices AS pr ON p.id = pr.product_id
            WHERE
                p.name LIKE %s
            ORDER BY
                p.name, pr.platform, pr.last_updated DESC;
            """
            cursor.execute(sql_query, (f"%{keyword}%",))
            raw_results = cursor.fetchall()

            # 將原始結果組合成每個商品的多平台比價數據
            grouped_products = {}
            for row in raw_results:
                product_id = row['product_id']
                if product_id not in grouped_products:
                    grouped_products[product_id] = {
                        'id': product_id,
                        'name': row['product_name'],
                        'image': row['image_url'],
                        'platforms': [],
                        'min_price': float('inf')
                    }
                # 確保只取每個平台最新的一條價格記錄
                platform_exists = False
                for existing_platform in grouped_products[product_id]['platforms']:
                    if existing_platform['platform'] == row['platform']:
                        # 由於我們已經 ORDER BY DESC，第一個遇到的就是最新的
                        platform_exists = True
                        break
                if not platform_exists:
                    platform_info = {
                        'platform': row['platform'],
                        'price': float(row['price']), # 確保為浮點數
                        'url': row['product_url'],
                        'is_available': row['is_available'],
                        'last_updated': row['last_updated'].strftime('%Y-%m-%d %H:%M:%S')
                    }
                    grouped_products[product_id]['platforms'].append(platform_info)
                    if platform_info['price'] < grouped_products[product_id]['min_price']:
                        grouped_products[product_id]['min_price'] = platform_info['price']

            # 將字典轉換為列表，並按最低價格排序
            results = sorted(list(grouped_products.values()), key=lambda x: x['min_price'])

    except pymysql.Error as e:
        print(f"Database error during get_comparison_data: {e}")
    finally:
        connection.close()
    return results

# --- 測試區塊 ---
if __name__ == '__main__':
    # 這是一個測試 db_connector 功能的簡單範例
    # 您可以運行爬蟲先獲取一些數據，然後再調用這個測試
    test_products = [
        {
            'name': '測試商品A',
            'price': 999.0,
            'url': 'http://test.com/a',
            'image': 'http://test.com/a.jpg',
            'platform': 'TestPlatform1',
            'is_available': True
        },
        {
            'name': '測試商品A',
            'price': 980.0,
            'url': 'http://test.com/b',
            'image': 'http://test.com/a.jpg',
            'platform': 'TestPlatform2',
            'is_available': True
        },
        {
            'name': '測試商品B',
            'price': 1200.0,
            'url': 'http://test.com/c',
            'image': 'http://test.com/c.jpg',
            'platform': 'TestPlatform1',
            'is_available': False
        }
    ]
    print("Saving test products...")
    save_product_data(test_products)
    print("Done saving.")

    print("\nQuerying '測試商品'...")
    comparison_results = get_comparison_data("測試商品")
    for prod in comparison_results:
        print(f"商品名稱: {prod['name']}, 最低價格: {prod['min_price']}")
        for p_info in prod['platforms']:
            print(f"  - 平台: {p_info['platform']}, 價格: {p_info['price']}, 連結: {p_info['url']}")