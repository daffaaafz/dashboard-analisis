# 📊 Interactive Sales Analytics Dashboard

A dynamic and interactive web dashboard built with **Streamlit**, **Python**, and **SQLite (In-Memory)** to analyze sales data in real-time.

![Streamlit Status](https://img.shields.io/badge/Streamlit-Cloud-FF4B4B?logo=streamlit)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)
![Database](https://img.shields.io/badge/SQLite-In--Memory-003B57?logo=sqlite)

---

## 🌟 Key Features
- **Dynamic City Filter**: Instantly update metrics, tables, and charts based on selected city/region.
- **Automated SQL Analysis**: Utilizes SQL queries (`GROUP BY`, `SUM`, `ORDER BY`, `LIMIT`) for real-time metric computation.
- **Core Business Metrics**:
  - Total Revenue & Total Volume (Cups Sold)
  - Best-Selling Product (🏆)
  - Top Performing Month (📈)
  - Average Order Value (AOV)
- **Data Export**: Allows users to download filtered transaction reports directly into Excel (`.xlsx`).
- **Flexible Data Ingestion**: Supports custom Excel file uploads with automatic column whitespace cleaning.

---

## 🛠️ Tech Stack & Libraries
- **Frontend & App Framework**: [Streamlit](https://streamlit.io/)
- **Data Processing**: `pandas`, `openpyxl`
- **Database Logic**: `sqlite3` (In-Memory SQL)
- **Version Control & Deployment**: GitHub, Streamlit Cloud

---

## 📂 Project Structure
```text
├── app.py              # Main Streamlit application script
├── requirements.txt    # Python dependencies for Streamlit Cloud
└── README.md           # Project documentation