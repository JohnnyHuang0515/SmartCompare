import os
import sys

# 將專案根目錄添加到 Python 模組搜索路徑中
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 導入 Flask 應用實例和 db_connector
from src.api.app import app
from src.database import db_connector # 導入 db_connector 以便調用其初始化函數

if __name__ == '__main__':
    # 確保在 Flask 應用運行之前，資料庫被初始化
    print("正在初始化資料庫...")
    db_connector.initialize_database()
    print("資料庫初始化檢查完成。")

    # 運行 Flask 應用
    app.run(debug=True)