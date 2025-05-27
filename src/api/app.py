# src/api/app.py

from flask import Flask, request, jsonify, render_template
import os # <--- 導入 os 模組
from src.scraper.momo_scraper import MomoScraper
from src.scraper.pchome_scraper import PChomeScraper
from src.database import db_connector
import threading
from datetime import datetime, timedelta

# 獲取當前文件 (app.py) 的絕對路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
# 專案根目錄，假設 app.py 在 src/api/ 下
# 往上兩層就是專案根目錄 (src 的上一層)
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

# 創建 Flask 應用實例時，明確指定模板和靜態檔案的路徑
app = Flask(
    __name__,
    template_folder=os.path.join(project_root, 'templates'), # <--- 指向專案根目錄下的 templates
    static_folder=os.path.join(project_root, 'static')       # <--- 指向專案根目錄下的 static
)

# 配置：定義資料過期時間 (例如：1小時)
DATA_FRESHNESS_HOURS = 1

# 根路由：處理根路徑 '/' 的請求，渲染 index.html
@app.route('/', methods=['GET'])
def index():
    """渲染前端的 index.html 頁面"""
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search_products():
    # ... (這個函數的內容保持不變，與您之前修改的一樣) ...
    keyword = request.args.get('keyword')
    if not keyword:
        return jsonify({"error": "Missing 'keyword' parameter"}), 400

    print(f"Received search request for keyword: {keyword}")

    db_results = db_connector.get_comparison_data(keyword)

    has_fresh_data = False
    if db_results:
        for product_group in db_results:
            for platform_info in product_group['platforms']:
                # 確保 last_updated 是字串，並且能被正確解析
                if isinstance(platform_info['last_updated'], str):
                    last_updated_str = platform_info['last_updated']
                elif isinstance(platform_info['last_updated'], datetime):
                    last_updated_str = platform_info['last_updated'].strftime('%Y-%m-%d %H:%M:%S')
                else:
                    continue # 如果格式不對，跳過這個平台信息

                try:
                    last_updated_dt = datetime.strptime(last_updated_str, '%Y-%m-%d %H:%M:%S')
                    if datetime.now() - last_updated_dt < timedelta(hours=DATA_FRESHNESS_HOURS):
                        has_fresh_data = True
                        break
                except ValueError:
                    print(f"Warning: Could not parse datetime string '{last_updated_str}' for platform '{platform_info.get('platform')}'")
                    continue
            if has_fresh_data:
                break

    if has_fresh_data:
        print(f"Found fresh data for '{keyword}' in database. Returning DB results.")
        return jsonify(db_results)
    else:
        print(f"No fresh data for '{keyword}' in database. Initiating scraping...")
        all_scraped_results = []
        errors = []

        def run_scraper(scraper_class, results_list, errors_list):
            scraper_instance = None
            try:
                scraper_instance = scraper_class()
                platform_results = scraper_instance.search_product(keyword)
                results_list.extend(platform_results)
            except Exception as e:
                errors_list.append(f"Error scraping {scraper_class.__name__}: {e}")
                print(f"Error scraping {scraper_class.__name__}: {e}")
            finally:
                if scraper_instance:
                    scraper_instance.close_driver()

        threads = []
        scrapers_to_run = [MomoScraper, PChomeScraper]

        for scraper_class in scrapers_to_run:
            thread = threading.Thread(target=run_scraper, args=(scraper_class, all_scraped_results, errors))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        if all_scraped_results:
            print(f"Scraped {len(all_scraped_results)} items. Saving to database...")
            db_connector.save_product_data(all_scraped_results)

            final_results = db_connector.get_comparison_data(keyword)
            print("Returning latest data from database after scraping.")
            return jsonify(final_results)
        else:
            print(f"No results scraped for '{keyword}'. Returning existing DB results or empty list.")
            return jsonify(db_results if db_results else [])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)