import abc # 導入抽象基底類別模組
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class BaseScraper(abc.ABC):
    """
    所有電商爬蟲的抽象基底類別。
    定義了所有具體爬蟲必須實現的方法。
    """

    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.driver = None # Selenium driver instance

        # 設定 ChromeOptions
        self.chrome_options = webdriver.ChromeOptions()
        # self.chrome_options.add_argument("--headless") # 不開啟實體瀏覽器背景執行，除錯時建議關閉
        self.chrome_options.add_argument("--start-maximized") # 最大化視窗
        self.chrome_options.add_argument("--incognito") # 開啟無痕模式
        self.chrome_options.add_argument("--disable-popup-blocking") # 禁用彈出攔截
        self.chrome_options.add_argument("--disable-notifications") # 取消通知
        self.chrome_options.add_argument("--lang=zh-TW") # 設定為正體中文
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    def _initialize_driver(self):
        """初始化 Selenium WebDriver"""
        if self.driver is None:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.chrome_options)

    @abc.abstractmethod
    def search_product(self, keyword: str) -> list[dict]:
        """
        抽象方法：根據關鍵字搜尋商品。
        所有繼承此基底類別的子類別都必須實作此方法。

        Args:
            keyword (str): 要搜尋的商品關鍵字。

        Returns:
            list[dict]: 包含多個商品資訊的列表，每個商品是一個字典。
                        字典應包含 'name', 'price', 'url', 'image', 'platform' 等標準鍵。
        """
        pass # 抽象方法沒有具體實現

    def close_driver(self):
        """關閉 WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None # 重置 driver 實例