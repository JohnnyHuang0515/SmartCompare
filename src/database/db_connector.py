# src/database/db_connector.py

import pymysql
from pymysql.cursors import DictCursor
from datetime import datetime, timedelta
from configparser import ConfigParser
import os

# --- 配置資料庫連接參數 ---
# 獲取當前文件 (db_connector.py) 的絕對路徑
current_script_dir = os.path.dirname(os.path.abspath(__file__))
# 專案根目錄，假設 db_connector.py 在 src/database/ 下
# 往上兩層就是專案根目錄 (src 的上一層)
project_root_dir = os.path.abspath(os.path.join(current_script_dir, '..', '..'))
config_path = os.path.join(project_root_dir, 'config.ini')  # config.ini 應該在專案根目錄

config = ConfigParser()
# 檢查 config.ini 是否存在。如果不存在，直接報錯。
if not os.path.exists(config_path):
    print(f"Error: config.ini not found at {config_path}. Cannot proceed without database configuration.")
    raise FileNotFoundError(f"Missing config.ini at {config_path}. Please place it in the project root directory.")
else:
    config.read(config_path)  # 使用絕對路徑讀取 config.ini

    # 檢查 'DB_CONFIG' 區塊是否存在
    if not config.has_section("DB_CONFIG"):
        print(f"Error: Section [DB_CONFIG] not found in {config_path}. Cannot proceed without database configuration.")
        raise ValueError(
            f"Missing [DB_CONFIG] section in {config_path}. Please ensure your config.ini has this section.")

    DB_CONFIG = {
        'host': config.get("DB_CONFIG", "host"),
        'user': config.get("DB_CONFIG", "user"),
        'password': config.get("DB_CONFIG", "password"),
        'db': config.get("DB_CONFIG", "db"),
        'charset': config.get("DB_CONFIG", "charset"),
        'cursorclass': DictCursor  # 直接使用類別，不需要引號
    }


def get_db_connection():
    """建立並返回一個資料庫連接"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except pymysql.Error as e:
        print(f"Error connecting to MySQL: {e}")  # 這裡會打印錯誤訊息
        return None
    except Exception as e:  # 捕獲其他潛在錯誤
        print(f"An unexpected error occurred during database connection: {e}")
        return None


def save_product_data(product_list: list[dict]):
    """
    將爬取到的商品資料存入資料庫。
    會檢查商品是否已存在，若存在則更新 prices 表，否則新增 products 和 prices 表。
    目標：每個商品在每個平台只保留一條最新的價格記錄。
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

                if not (name and platform and url and price is not None):
                    print(f"Skipping incomplete product data: {product_data}")
                    continue

                # 1. 檢查 products 表中是否已存在該商品
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
                    cursor.execute(sql_insert_product, (name, image, None))
                    product_id = cursor.lastrowid  # 獲取新插入的商品ID

                # 2. 插入或更新價格到 prices 表
                # 不再檢查日期，直接檢查 product_id 和 platform 是否存在
                sql_check_price_exists = """
                 SELECT id FROM prices
                 WHERE product_id = %s AND platform = %s
                 """
                cursor.execute(sql_check_price_exists, (product_id, platform))
                price_record = cursor.fetchone()  # 不再叫 price_record_today

                if price_record:
                    # 如果記錄存在，則更新價格
                    sql_update_price = """
                     UPDATE prices
                     SET price = %s, product_url = %s, is_available = %s, last_updated = CURRENT_TIMESTAMP
                     WHERE id = %s
                     """
                    cursor.execute(sql_update_price, (price, url, is_available, price_record['id']))
                else:
                    # 否則插入新的價格記錄
                    sql_insert_price = """
                     INSERT INTO prices (product_id, platform, price, product_url, is_available)
                     VALUES (%s, %s, %s, %s, %s)
                     """
                    cursor.execute(sql_insert_price, (product_id, platform, price, url, is_available))

            connection.commit()  # 提交所有更改
            print(f"Successfully saved {len(product_list)} product data to DB (updated/inserted).")
    except pymysql.Error as e:
        connection.rollback()  # 出錯時回滾
        print(f"Database error during save_product_data: {e}")
    except Exception as e:
        connection.rollback()
        print(f"An unexpected error occurred during save_product_data: {e}")
    finally:
        if connection:
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
            # 修正 SQL 查詢以獲取每個商品在每個平台的最新價格
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
            JOIN (
                SELECT
                    product_id,
                    platform,
                    price,
                    product_url,
                    is_available,
                    last_updated,
                    ROW_NUMBER() OVER (PARTITION BY product_id, platform ORDER BY last_updated DESC) AS rn
                FROM
                    prices
            ) AS pr ON p.id = pr.product_id
            WHERE
                p.name LIKE %s AND pr.rn = 1
            ORDER BY
                p.name, pr.platform, pr.last_updated DESC;
            """
            cursor.execute(sql_query, (f"%{keyword}%",))
            raw_results = cursor.fetchall()

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

                platform_info = {
                    'platform': row['platform'],
                    'price': float(row['price']),  # 確保為浮點數
                    'url': row['product_url'],
                    'is_available': row['is_available'],
                    'last_updated': row['last_updated'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(row['last_updated'],
                                                                                                    datetime) else str(
                        row['last_updated'])
                }
                grouped_products[product_id]['platforms'].append(platform_info)

                if platform_info['price'] < grouped_products[product_id]['min_price']:
                    grouped_products[product_id]['min_price'] = platform_info['price']

            results = sorted(list(grouped_products.values()), key=lambda x: x['min_price'])

    except pymysql.Error as e:
        print(f"Database error during get_comparison_data: {e}")
    except Exception as e:  # 捕獲其他潛在錯誤
        print(f"An unexpected error occurred during get_comparison_data: {e}")
    finally:
        if connection:
            connection.close()
    return results


# --- 測試區塊 (僅供測試 db_connector 功能，不在生產環境運行) ---
if __name__ == '__main__':
    # 在運行這個測試之前，請確保您的 config.ini 位於專案根目錄 (SmartCompare/)
    # 並且其中的數據庫憑證是正確的。
    test_products_to_save = [
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
        },
        {
            'name': '測試商品A',  # 測試更新當天價格
            'price': 950.0,
            'url': 'http://test.com/a_updated',
            'image': 'http://test.com/a.jpg',
            'platform': 'TestPlatform1',
            'is_available': True
        }
    ]
    print("Saving test products...")
    save_product_data(test_products_to_save)
    print("Done saving.")

    print("\nQuerying '測試商品'...")
    comparison_results = get_comparison_data("測試商品")
    if comparison_results:
        for prod in comparison_results:
            print(f"商品名稱: {prod['name']}, 最低價格: {prod['min_price']}")
            for p_info in prod['platforms']:
                print(
                    f"  - 平台: {p_info['platform']}, 價格: {p_info['price']}, 連結: {p_info['url']}, 更新時間: {p_info['last_updated']}")
    else:
        print("未找到 '測試商品' 的任何結果。")