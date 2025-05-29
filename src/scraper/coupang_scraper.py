import os, json
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_scraper import BaseScraper # 導入 BaseScraper

class CoupangScraper(BaseScraper):
    def __init__(self):
        super().__init__("coupang") # 調用父類別的初始化方法，設定平台名稱
        # self.driver = None # 驅動器在父類別中初始化
        # self.folderPath = 'momo_product' # 儲存到 json 可改為在 api 端處理
        # if not os.path.exists(self.folderPath):
        #     os.makedirs(self.folderPath)
        # self.listData = [] # 儲存到 json 可改為直接返回

    def _visit(self):
        """訪問 Coupang 網站"""
        self._initialize_driver() # 確保驅動器已初始化
        self.driver.get("https://www.tw.coupang.com/")
        sleep(2)

    def _search_input(self, keyword: str):
        """在搜尋框輸入關鍵字並提交"""
        try:
            txt_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.header-searchForm.fw-relative.fw-flex-1 > input"))
            )
            txt_input.send_keys(keyword)
            sleep(1)
            txt_input.submit()
            sleep(2) # 等待搜尋結果頁面載入
        except TimeoutException:
            print("Coupang 搜尋框或提交按鈕等候逾時")
        except NoSuchElementException:
            print("Coupang 搜尋框或提交按鈕未找到")


    def _filter_popular(self):
        """點擊熱銷篩選"""
        try:
            WebDriverWait(self.driver,10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR,
                    "Sort_selected__SBbDW"
                     )
                )
            )
            self.driver.find_element(
                By.CSS_SELECTOR,
                "Sort_selected__SBbDW"
            ).click()
            sleep(2) # 等待篩選結果載入
        except TimeoutException:
            print("Coupang 熱銷篩選按鈕等候逾時")
        except NoSuchElementException:
            print("Coupang 熱銷篩選按鈕未找到")

    def _scroll(self, limit: int = 3):
        """滾動頁面載入更多內容"""
        inner_height = 0
        offset = 0
        count = 0
        while count <= limit:
            offset = self.driver.execute_script(
                'return document.documentElement.scrollHeight;'
            )
            self.driver.execute_script(f'''
                window.scrollTo({{
                    top: {offset},
                    behavior: 'smooth'
                }});
            ''')
            sleep(3)
            inner_height = self.driver.execute_script(
                'return document.documentElement.scrollHeight;'
            )
            if offset == inner_height:
                count += 1
            else: # 如果有新內容載入，重置計數
                count = 0

    def _parse(self) -> list[dict]:
        """解析頁面並提取商品資訊"""
        products = []
        try:
            # 確保商品元素已經載入
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.ProductUnit_productUnit__Qd6sv"))
            )
            elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                "li.ProductUnit_productUnit__Qd6sv"
            )
            for elm in elements:
                try:
                    # 使用 find_elements 而不是 find_element，處理可能沒有圖片的情況
                    img_elements = elm.find_elements(By.CSS_SELECTOR, "a > figure > img")
                    img_src = img_elements[0].get_attribute("src") if img_elements else "" # 如果沒有圖片，給空字串

                    a_title = elm.find_element(
                        By.CSS_SELECTOR,
                        "div.ProductUnit_productName__gre7e"
                    ).text

                    l = elm.find_element(
                        By.CSS_SELECTOR,
                        "li.ProductUnit_productUnit__Qd6sv > a"
                    )
                    link = l.get_attribute("href")

                    price_element = elm.find_element(
                        By.CSS_SELECTOR,
                        "div > strong.Price_priceValue__A4KOr"
                    ).text.replace(',', '').replace('$', '') # 移除價格中的逗號以便轉換為數字
                    price = float(price_element) # 轉換為浮點數

                    products.append({
                        "name": a_title,
                        "price": price,
                        "url": link,
                        "image": img_src,
                        "platform": self.platform_name,
                        "is_available": True # 預設有庫存，如果有明確的缺貨標示，需要額外判斷
                    })
                except NoSuchElementException as e:
                    print(f"解析 Coupang 單一商品時部分元素未找到: {e}")
                    continue # 跳過當前商品，繼續解析下一個
                except ValueError as e:
                    print(f"解析 Coupang 價格時出錯: {e}")
                    continue
        except TimeoutException:
            print("Coupang 商品列表載入逾時，可能沒有結果。")
        except Exception as e:
            print(f"Coupang 解析時發生未知錯誤: {e}")
        return products

    def search_product(self, keyword: str) -> list[dict]:
        """
        從 momo 搜尋商品並返回標準化結果。
        這是供外部調用的主要方法。
        """
        self._visit()
        self._search_input(keyword)
        self._filter_popular() # 可選，根據需求決定是否每次都篩選
        self._scroll() # 滾動頁面載入更多
        results = self._parse()
        self.close_driver() # 完成後關閉 driver
        return results

# --- 測試區塊 ---
if __name__ == '__main__':
    scraper = CoupangScraper()
    search_keyword = "耳機"
    results = scraper.search_product(search_keyword)

    if results:
        print(f"\n從 {scraper.platform_name} 找到 {len(results)} 項 '{search_keyword}' 的結果:")
        for i, item in enumerate(results[:5]): # 只印前5個
            print(f"--- 商品 {i+1} ---")
            print(f"名稱: {item['name']}")
            print(f"價格: {item['price']}")
            print(f"連結: {item['url']}")
            print(f"圖片: {item['image']}")
            print(f"平台: {item['platform']}")
            print(f"是否有庫存: {item['is_available']}")
            print("-" * 20)
    else:
        print(f"\n在 {scraper.platform_name} 未找到 '{search_keyword}' 的結果。")