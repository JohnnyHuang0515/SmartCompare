# run.py

from src.api.app import app

if __name__ == '__main__':
    # 這裡的配置會覆蓋 app.py 中 if __name__ == '__main__': 的配置
    # 但為了簡潔，您可以選擇只在 app.py 中設定這些。
    app.run(debug=True, host='0.0.0.0', port=5000)