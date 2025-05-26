import os, json
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

my_options = webdriver.ChromeOptions()
# my_options.add_argument("--headless")               #不開啟實體瀏覽器背景執行
my_options.add_argument("--start-maximized")         #最大化視窗
my_options.add_argument("--incognito")               #開啟無痕模式
my_options.add_argument("--disable-popup-blocking") #禁用彈出攔截
my_options.add_argument("--disable-notifications")  #取消通知
my_options.add_argument("--lang=zh-TW")  #設定為正體中文
my_options.add_experimental_option("excludeSwitches", ["enable-automation"])
my_options.add_experimental_option('useAutomationExtension', False)
my_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options = my_options)

folderPath = 'shopee_product'
if not os.path.exists(folderPath):
    os.makedirs(folderPath)

listData = []

def visit():
    driver.get("https://shopee.tw/")
    sleep(2)

def search(keyword: str):
    txt_input = driver.find_element(
        By.CSS_SELECTOR,
        "shopee-searchbar-input__input"
    )
    txt_input.send_keys({keyword})
    sleep(1)
    txt_input.submit()
    sleep(1)

def filterFunc():
    try:
        # 等待篩選元素出現
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 "#hot"
                 )
            )
        )

        # 按下篩選元素
        driver.find_element(
            By.CSS_SELECTOR,
            "#hot"
        ).click()

        # 等待一下
        sleep(2)

    except TimeoutException:
        print("等待逾時")

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
        "li.c-listInfoGrid__item.c-listInfoGrid__item--gridCardGray5.is-bottomLine"
    )
    for elm in elements:
        img_src = elm.find_element(
            By.CSS_SELECTOR,
            "div.c-prodInfoV2__img > img"
        ).get_attribute("src")
        print(img_src)
        a_title = elm.find_element(
            By.CSS_SELECTOR,
            "div.c-prodInfoV2__title"
        ).text
        print(a_title)
        l = elm.find_element(
            By.CSS_SELECTOR,
            "a.c-prodInfoV2__link.gtmClickV2"
        )
        link = l.get_attribute("href")
        print(link)
        price = elm.find_element(
            By.CSS_SELECTOR,
            "div.c-prodInfoV2__priceValue.c-prodInfoV2__priceValue--m"
        ).text
        print(price)
        listData.append({
            "title": a_title,
            "price": price,
            "link": link,
            "img": img_src
        })
def saveJson():
    with open(f"{folderPath}/pchome.json", "w", encoding='utf-8') as file:
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