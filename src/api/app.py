# src/api/app.py

from flask import Flask, request, jsonify, render_template
import os
from src.scraper.momo_scraper import MomoScraper
from src.scraper.pchome_scraper import PChomeScraper
from src.scraper.coupang_scraper import CoupangScraper
from src.database import db_connector # 確保這裡導入了 db_connector
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
    template_folder=os.path.join(project_root, 'templates'),
    static_folder=os.path.join(project_root, 'static')
)

# 配置：定義資料過期時間 (例如：1小時)
DATA_FRESHNESS_HOURS = 1

# 根路由：處理根路徑 '/' 的請求，渲染 index.html
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return jsonify({"error": "Keyword is required"}), 400

    db_results = db_connector.get_products_with_prices_by_keyword(keyword, DATA_FRESHNESS_HOURS)

    if db_results and db_results['grouped_products']: # 檢查 'grouped_products' 是否有內容
        print(f"Found fresh results for '{keyword}' in database. Returning from DB.")
        return jsonify(db_results)
    else:
        print(f"No fresh results for '{keyword}' in database or no results found. Starting scraping...")
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
        scrapers_to_run = [MomoScraper, PChomeScraper, CoupangScraper]

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
            # 如果爬蟲也沒有結果，但資料庫有舊資料，仍然返回舊資料 (因為 get_comparison_data 總是返回所有)
            return jsonify(db_connector.get_comparison_data(keyword) if db_connector.get_comparison_data(keyword)['grouped_products'] else {"grouped_products": [], "summary": {"total_products": 0, "avg_savings": 0, "best_platform": "N/A"}, "errors": errors})


if __name__ == '__main__':
    # 在應用啟動時調用資料庫初始化函數
    db_connector.initialize_database()
    app.run(debug=True)