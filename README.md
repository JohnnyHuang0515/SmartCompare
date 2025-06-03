# SmartCompare: E-commerce Product Price Comparison Tool

##  Project Overview

**SmartCompare** is a web application designed to help users compare product prices across major Taiwanese e-commerce platforms: **momo**, **PChome**, and **Coupang**.  
It features a **Flask** backend, **web scraping modules** for real-time data fetching, and a **MySQL** database for efficient product data storage.

> The app prioritizes recently scraped data from the database and triggers live scraping only when data is outdated or unavailable.

---

##  Features

-  **Product Search** — Search for items using keywords.
-  **Real-Time Scraping** — Fetches up-to-date prices from momo, PChome, and Coupang.
-  **Database Integration** — Avoids redundant scraping by storing and retrieving data efficiently.
-  **Data Freshness** — Falls back to scraping if data is older than 1 hour (configurable).
-  **Price Comparison** — Displays multi-platform prices and highlights the lowest.
-  **Data Summary** — Shows total products, potential savings, and the platform with the most deals.
-  **Auto DB Initialization** — Automatically sets up the database and tables on first launch.

---

##  Project Structure

```
SmartCompare/
├── config.ini               # MySQL and other configurations
├── run.py                   # App entry point
├── .gitignore               # Ignored files
├── README.md                # This documentation file
├── requirements.txt         # Python dependencies

├── src/                     # Core source code
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── app.py           # Flask app routes and logic
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db_connector.py  # DB connection & operations
│   │   └── schema.sql       # DB schema (CREATE TABLE only)
│   └── scraper/
│       ├── __init__.py
│       ├── base_scraper.py
│       ├── momo_scraper.py
│       ├── pchome_scraper.py
│       └── coupang_scraper.py

├── static/                  # Static frontend assets
│   ├── css/style.css
│   └── js/main.js

└── templates/
    └── index.html           # Main HTML template
```

---

##  Setup & Installation

###  Prerequisites

Make sure the following are installed:

- Python 3.8+
- MySQL Server (Community Edition)
- MySQL Client (e.g., MySQL Workbench or CLI)
- Google Chrome (required by Selenium)

---

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd SmartCompare
```

---

### 2. Set Up Virtual Environment (Recommended)

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> If `requirements.txt` is missing, install manually and run:  
> `pip freeze > requirements.txt`

Core libraries:

- `Flask`
- `pymysql`
- `selenium`
- `webdriver_manager`

---

### 4. Configure MySQL

#### a. `config.ini` File

Create a `config.ini` in the project root with:

```ini
[DB_CONFIG]
DB_HOST=localhost
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=smartcompare_db
```

Replace the values accordingly. Ensure `DB_USER` has **privileges to create/manage tables**.

#### b. Verify `schema.sql`

Make sure `src/database/schema.sql` contains **only CREATE TABLE statements**, no `CREATE DATABASE` or `USE`.

Example:

```sql
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    image_url VARCHAR(1000),
    brand VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS prices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    product_url VARCHAR(255) NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id),
    UNIQUE KEY (product_id, platform, product_url)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### c. Grant MySQL Privileges (If Needed)

```sql
GRANT ALL PRIVILEGES ON smartcompare_db.* TO 'your_mysql_username'@'localhost';
FLUSH PRIVILEGES;
```

> Even if the DB doesn't exist yet, this ensures access when it’s auto-created.

---

### 5. Ensure `__init__.py` Exists

Check or create empty `__init__.py` files in:

- `src/`
- `src/api/`
- `src/database/`
- `src/scraper/`

---

### 6. Chrome WebDriver for Selenium

Make sure `webdriver_manager` is installed so it auto-handles ChromeDriver versioning.

---

### 7. (Optional) Clean Existing Database

If you've run the app before and want a clean slate:

```sql
DROP DATABASE IF EXISTS smartcompare_db;
```

---

##  Running the Application

Activate your virtual environment:

```bash
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

Navigate to project root and run:

```bash
python run.py
```

The app will initialize the DB and start a Flask dev server (usually at http://127.0.0.1:5000/).

---

##  Usage

1. Open browser at `http://127.0.0.1:5000/`
2. Search for a product keyword
3. App checks for recent database results
4. If none found or data is stale, live scraping is triggered
5. Results display once complete

---
