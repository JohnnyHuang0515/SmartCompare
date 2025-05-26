import os, json
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_scraper import BaseScraper # 導入 BaseScraper

class MomoScraper(BaseScraper):
    def __init__(self):
        super().__init__("momo") # 調用父類別的初始化方法，設定平台名稱
        # self.driver = None # 驅動器在父類別中初始化
        # self.folderPath = 'momo_product' # 儲存到 json 可改為在 api 端處理
        # if not os.path.exists(self.folderPath):
        #     os.makedirs(self.folderPath)
        # self.listData = [] # 儲存到 json 可改為直接返回

driver = webdriver.Chrome(options = my_options)

folderPath = 'momo_product'
if not os.path.exists(folderPath):
    os.makedirs(folderPath)

listData = []

def visit():
    driver.get("https://www.momoshop.com.tw/main/Main.jsp")
    sleep(2)

def search(keyword: str):
    txt_input = driver.find_element(
        By.CSS_SELECTOR,
        "#keyword"
    )
    txt_input.send_keys({keyword})
    driver.find_element(
        By.CSS_SELECTOR,
        "#topSchFrm > div > button"
    ).click()

def filterFunc():
    try:
        WebDriverWait(driver,10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                "#searchType > li.popularPrd"
                 )
            )
        )

        driver.find_element(
            By.CSS_SELECTOR,
            "#searchType > li.popularPrd"
        ).click()

        sleep(2)

    except TimeoutException:
        print("等候逾時")

def scroll():
    inner_height = 0
    offset = 0
    count = 0
    limit = 3
    while count <= limit:
        # 每次移動高度
        offset = driver.execute_script(
            'return document.documentElement.scrollHeight;'
        )
        driver.execute_script(f'''
            window.scrollTo({{
                top: {offset}, 
                behavior: 'smooth' 
            }});
        ''')
        sleep(3)
        inner_height = driver.execute_script(
            'return document.documentElement.scrollHeight;'
        )
        if offset == inner_height:
            count += 1

def parse():
    global listData
    listData.clear()
    elements = driver.find_elements(
        By.CSS_SELECTOR,
        "div.goodsUrl"
    )
    for elm in elements:
        img_src = elm.find_element(
            By.CSS_SELECTOR,
            "div.swiper-slide.swiper-slide-active > a > picture > img"
        ).get_attribute("src")
        print(img_src)
        a_title = elm.find_element(
            By.CSS_SELECTOR,
            "h3.prdName"
        ).text
        print(a_title)
        l = elm.find_element(
            By.CSS_SELECTOR,
            "a.goods-img-url"
        )
        link = l.get_attribute("href")
        print(link)
        price = elm.find_element(
            By.CSS_SELECTOR,
            "span.price > b"
        ).text
        print(f"${price}")
        listData.append({
            "title": a_title,
            "price": f"${price}",
            "link": link,
            "img": img_src
        })
def saveJson():
    with open(f"{folderPath}/momo.json", "w", encoding='utf-8') as file:
        file.write( json.dumps(listData, ensure_ascii=False, indent=4) )

def close():
    driver.quit()

if __name__ == '__main__':
    visit()
    search("電競鍵盤")
    filterFunc()
    scroll()
    parse()
    saveJson()
    close()