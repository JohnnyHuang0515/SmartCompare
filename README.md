# SmartCompare: E-commerce Product Price Comparison Tool

## Project Overview

SmartCompare is a web application designed to help users compare product prices across major Taiwanese e-commerce platforms: momo, PChome, and Coupang.
It is built with a Flask backend, web scraping modules for real-time data acquisition, and a MySQL database for efficient data storage and management.

The application prioritizes using recently cached data and initiates live scraping only when necessary.

## Features

* Product Search — Search for items using keywords.
* Real-Time Scraping — Retrieves current prices from momo, PChome, and Coupang.
* Database Integration — Stores and retrieves product data to minimize redundant scraping.
* Data Freshness — Falls back to live scraping if existing data is older than a configurable threshold (default: 1 hour).
* Price Comparison — Displays prices from multiple platforms and highlights the lowest.
* Data Summary — Provides a summary of results, including product count, potential savings, and best-priced platform.
* Automatic Database Initialization — Automatically creates the required database and tables upon first launch.

## Project Structure

```
SmartCompare/
├── config.ini               # Configuration file for MySQL and application settings
├── run.py                   # Main application entry point
├── .gitignore               # Git ignore rules
├── README.md                # Project documentation
├── requirements.txt         # Python dependencies
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── app.py           # Flask routes and handlers
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db_connector.py  # Handles DB connections and operations
│   │   └── schema.sql       # Table definitions
│   └── scraper/
│       ├── __init__.py
│       ├── base_scraper.py
│       ├── momo_scraper.py
│       ├── pchome_scraper.py
│       └── coupang_scraper.py
├── static/
│   ├── css/style.css
│   └── js/main.js
└── templates/
    └── index.html
```

## Setup and Installation

### Prerequisites

Ensure the following are installed:

* Python 3.8+
* MySQL Server
* MySQL Client (e.g., MySQL Workbench or terminal client)
* Google Chrome (required for Selenium)

### 1. Clone the Repository

```bash
git clone https://github.com/JohnnyHuang0515/SmartCompare.git
cd SmartCompare
```

### 2. Set Up Virtual Environment

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` is not available, manually install the following packages:

* Flask
* pymysql
* selenium
* webdriver\_manager

Then generate the file:

```bash
pip freeze > requirements.txt
```

### 4. Configure MySQL

#### a. Create config.ini

```ini
[DB_CONFIG]
DB_HOST=localhost
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=smartcompare_db
```

Replace with your MySQL credentials. Ensure the user has privileges to create and manage tables.

#### b. Validate schema.sql

Ensure that `src/database/schema.sql` contains only `CREATE TABLE` statements and does not include any `CREATE DATABASE` or `USE` commands.

#### c. Grant Database Privileges (if required)

```sql
GRANT ALL PRIVILEGES ON smartcompare_db.* TO 'your_mysql_username'@'localhost';
FLUSH PRIVILEGES;
```

## Running the Application

Activate your virtual environment:

```bash
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

From the project root directory, execute the following command:

```bash
python run.py
```

Initializes the database and starts the Flask development server (typically at [http://127.0.0.1:5000/](http://127.0.0.1:5000/)).

## Usage

1. Open [http://127.0.0.1:5000/](http://127.0.0.1:5000/) in a web browser.
2. Enter a product keyword and submit.
3. The application checks the database for existing results.
4. If data is outdated or missing, it automatically triggers real-time scraping.
5. Results are displayed and saved for future use.

## Summary

SmartCompare offers a streamlined and effective solution for comparing product prices across multiple e-commerce platforms.
