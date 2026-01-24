# 📊 Data Sources Server (MCP)

The **Data Sources Server** provides specialized connectors for fetching structured data from major financial, economic, and developmental databases. It centralizes the integration logic for various third-party APIs and provides data in a format ready for analysis.

## 🛠️ Tools

| Tool | Description |
|:-----|:------------|
| `yfinance_fetch` | Fetches historical price data, company info, and financial statements from Yahoo Finance. |
| `fred_fetch` | Retrieves economic series data from the Federal Reserve Economic Data (FRED) database. |
| `world_bank_fetch` | Fetches global development indicators (GDP, population, etc.) from the World Bank API. |
| `csv_fetch` | Generic tool to fetch and preview CSV data from any publicly accessible URL. |

## 🏗️ Implementation

The server utilizes specialized Python libraries for each source:
- `yfinance`: For financial data.
- `fredapi`: For economic indicators (requires `FRED_API_KEY`).
- `wbgapi`: For World Bank data.
- `pandas`: For generic CSV parsing and data manipulation.

## ⚙️ Configuration

Requires the following environment variables for full functionality:
- `FRED_API_KEY`: Required for using the `fred_fetch` tool.
