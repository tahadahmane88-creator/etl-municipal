# 📊 Suq Khamis Dadès - Municipal Budget ETL & Dashboard

An ETL (Extract, Transform, Load) project that converts municipal budget data for Suq Khamis Dadès (Excel files) into a MySQL database, with an interactive Power BI dashboard for visualization.

## 🎯 Overview

This project performs:
- **Extract**: Reads yearly Excel budget execution reports (2024 and 2025)
- **Transform**: Cleans the data, removes empty rows, totals, and signature lines, and converts financial values into numeric format
- **Load**: Loads the cleaned data into a MySQL database

## 📁 Project Structure

```
├── etl_municipal.py                          # Main ETL script
├── بيان-تنفيذ-ميزانية-سوق-الخميس-دادس2024.xlsx
├── بيان تنفيذ ميزانية سوق الخميس دادس2025.xlsx
├── screenshots/                              # Power BI dashboard screenshots
└── README.md
```

## 🗃️ Tables Created in MySQL

| Table | Content |
|---|---|
| `municipal_revenues` | Revenue / income sources |
| `municipal_operating_expenses` | Operating expenses |
| `municipal_capital_expenses` | Capital / equipment expenses |

## 🚀 How to Run

### Requirements

```bash
pip install pandas sqlalchemy mysql-connector-python openpyxl
```

### Setup

1. Make sure a MySQL database is ready
2. Update the connection settings in `etl_municipal.py`:

```python
my_mysql_config = {
    "host": "localhost",
    "port": "3306",
    "user": "root",
    "password": "",
    "database": "suq_khamis_db"
}
```

3. Place the Excel files in the same folder as the script

### Run

```bash
python etl_municipal.py
```

## 📈 Power BI Dashboard

![Dashboard 2024](screenshots/Screenshot%202024.png)
![Dashboard 2025](screenshots/Screenshot%202025.png)

The dashboard displays:
- Total revenue collected
- Total operating expenses
- Total capital expenses
- Budget surplus or deficit
- Revenue breakdown by funding source
- Operating expenses breakdown by main category
- Capital expenses breakdown by investment type

## 🛠️ Tech Stack

- **Python** (pandas, SQLAlchemy)
- **MySQL**
- **Power BI**

## ⚠️ Note

This project aims to automate the processing of municipal budget data for Suq Khamis Dadès for transparency and analysis purposes.
