# 💰 FinTrack - Your All-in-One Indian Portfolio Manager

FinTrack is a comprehensive portfolio management tool designed for the modern Indian investor. It allows users to track both their mutual fund and stock investments in a single, intuitive dashboard, providing powerful analytics and future projections to enable smarter financial decisions.

This project moves beyond simple tracking to offer advanced, actionable insights, including true annualized returns (XIRR), portfolio-level analysis, and performance comparisons against market benchmarks.

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/your-username/fintrack)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

---
## 📖 Table of Contents

- [About The Project](#about-the-project)
- [Key Features](#key-features)
- [Built With](#built-with)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Future Roadmap](#future-roadmap)
- [License](#license)
- [Contact](#contact)

---

## 🧐 About The Project

For many Indian investors, tracking a portfolio spread across different mutual funds and stocks is a fragmented and tedious process, often involving complex spreadsheets or juggling multiple brokerage apps. FinTrack solves this by providing a unified platform to consolidate, track, and analyze all your investments.

The application allows users to manually add their holdings, fetches live market data, and calculates a suite of performance metrics that are often unavailable on basic platforms. The core mission is to provide retail investors with the analytical tools they need to understand the true performance of their portfolio, assess their risk, and project future growth towards their financial goals.

<br>

**[ADD A SCREENSHOT OR GIF OF YOUR FINAL DEPLOYED DASHBOARD HERE]**

<br>

---
## ✨ Key Features

- **Unified Portfolio:** Track both **Indian Mutual Funds** and **NSE-listed Stocks** in one place.
- **Live Data Integration:** Fetches the latest NAV for mutual funds (via `mftool`) and live prices for stocks (via `yfinance`).
- **Multi-Asset Entry:** A dynamic interface to add multiple investments to a single portfolio.
- **Comprehensive Individual Analysis:** For each asset, the app calculates:
    - Current Value, Total Profit/Loss, and Absolute Returns.
    - **Compound Annual Growth Rate (CAGR)** to measure true performance.
- **Powerful Aggregate Portfolio Analysis:**
    - Calculates total portfolio value and P&L.
    - Determines the true, time-weighted annualized return of the entire portfolio using **XIRR**.
- **Future Value Projections:** Simulates the potential future growth of your investments based on historical performance data.
- **Benchmark Comparison:** Compares your portfolio's performance against standard market indices like the Nifty 50.

---
## 🛠️ Built With

This project is built with a focus on rapid development, robust data analysis, and a clean user interface.

* **Core Framework:** [Streamlit](https://streamlit.io/)
* **Data Analysis & Calculation:** [Python](https://www.python.org/), [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
* **Financial Data Sources:**
    * [mftool](https://pypi.org/project/mftool/) for Indian Mutual Fund NAV data.
    * [yfinance](https://pypi.org/project/yfinance/) for Indian stock market data.
* **Data Visualization:** [Plotly](https://plotly.com/python/)

---
## 🚀 Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

Make sure you have Python 3.8+ and pip installed on your system.

### Installation

1.  **Clone the repository:**
    ```sh
    git clone [https://github.com/your-username/fintrack.git](https://github.com/your-username/fintrack.git)
    cd fintrack
    ```
2.  **Install the required packages:**
    ```sh
    pip install -r requirements.txt
    ```
3.  **Run the application:**
    ```sh
    streamlit run main.py
    ```
    The application should now be running in your web browser.

---
## 📁 Project Structure

The project is organized into a modular structure for scalability and maintainability.
.
├── 📜 main.py             # The main Streamlit application file (UI)
├── 📜 data_fetcher.py      # Module for fetching all external financial data (NAV & stock prices)
├── 📜 portfolio_analyzer.py # The core logic engine for all financial calculations
├── 📜 requirements.txt     # A list of all necessary Python packages
└── 📜 README.md            # This file

---
## 🛣️ Future Roadmap

This project is designed to be scalable. Future enhancements planned include:
- [ ] **User Authentication:** Adding user accounts to securely save portfolios.
- [ ] **Database Integration:** Using a database like Firebase/Firestore to persist user data.
- [ ] **Automated CAS Import:** Allowing users to upload their Consolidated Account Statement (CAS) PDF for automatic portfolio import.
- [ ] **Advanced Risk Analytics:** Implementing metrics like portfolio volatility and the Sharpe Ratio.

---
## 📄 License

This project is distributed under the MIT License.

---
## 📧 Contact
Project Link: 