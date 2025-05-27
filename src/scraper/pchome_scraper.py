import os, json
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_scraper import BaseScraper # 導入 BaseScraper

class PChomeScraper(BaseScraper):
    def __init__(self):
        super().__init__("PChome") # 調用父類別的初始化方法，設定平台名稱
        # self.driver 和 self.chrome_options 在父類別初始化

    def _visit(self):
        """訪問 PChome 網站"""
        self._initialize_driver() # 確保驅動器已初始化
        self.driver.get("https://24h.pchome.com.tw/")
        sleep(2)

    def _search_input(self, keyword: str):
        """在搜尋框輸入關鍵字並提交"""
        try:
            txt_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.c-search__input"))
            )
            txt_input.send_keys(keyword)
            sleep(1)
            txt_input.submit()
            sleep(2) # 等待搜尋結果頁面載入
        except TimeoutException:
            print("PChome 搜尋框等候逾時")
        except NoSuchElementException:
            print("PChome 搜尋框未找到")


    def _filter_hot(self):
        """點擊熱門篩選"""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "#hot")
                )
            )
            self.driver.find_element(
                By.CSS_SELECTOR,
                "#hot"
            ).click()
            sleep(2) # 等待篩選結果載入
        except TimeoutException:
            print("PChome 熱門篩選按鈕等候逾時")
        except NoSuchElementException:
            print("PChome 熱門篩選按鈕未找到")

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
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.c-listInfoGrid__item"))
            )
            elements = self.driver.find_elements(
                By.CSS_SELECTOR,
                "li.c-listInfoGrid__item.c-listInfoGrid__item--gridCardGray5.is-bottomLine"
            )
            for elm in elements:
                try:
                    img_src = elm.find_element(
                        By.CSS_SELECTOR,
                        "div.c-prodInfoV2__img > img"
                    ).get_attribute("src")

                    a_title = elm.find_element(
                        By.CSS_SELECTOR,
                        "div.c-prodInfoV2__title"
                    ).text

                    l = elm.find_element(
                        By.CSS_SELECTOR,
                        "a.c-prodInfoV2__link.gtmClickV2"
                    )
                    link = l.get_attribute("href")

                    price_text = elm.find_element(
                        By.CSS_SELECTOR,
                        "div.c-prodInfoV2__priceValue.c-prodInfoV2__priceValue--m"
                    ).text.replace('$', '').replace(',', '') # 移除貨幣符號和逗號
                    price = float(price_text)

                    # PChome通常有缺貨提示，需要判斷，這裡先簡單設為True
                    is_available = True
                    # 您可以根據實際頁面元素判斷是否有缺貨標籤，例如：
                    # if elm.find_elements(By.CSS_SELECTOR, ".sold-out-tag"):
                    #     is_available = False

                    products.append({
                        "name": a_title,
                        "price": price,
                        "url": link,
                        "image": img_src,
                        "platform": self.platform_name,
                        "is_available": is_available
                    })
                except NoSuchElementException as e:
                    print(f"解析 PChome 單一商品時部分元素未找到: {e}")
                    continue # 跳過當前商品，繼續解析下一個
                except ValueError as e:
                    print(f"解析 PChome 價格時出錯: {e}")
                    continue
        except TimeoutException:
            print("PChome 商品列表載入逾時，可能沒有結果。")
        except Exception as e:
            print(f"PChome 解析時發生未知錯誤: {e}")
        return products

    def search_product(self, keyword: str) -> list[dict]:
        """
        從 PChome 搜尋商品並返回標準化結果。
        這是供外部調用的主要方法。
        """
        self._visit()
        self._search_input(keyword)
        self._filter_hot() # 可選，根據需求決定是否每次都篩選
        self._scroll() # 滾動頁面載入更多
        results = self._parse()
        self.close_driver() # 完成後關閉 driver
        return results

# --- 測試區塊 ---
if __name__ == '__main__':
    scraper = PChomeScraper()
    search_keyword = "顯示器"
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