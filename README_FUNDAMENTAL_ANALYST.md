# Fundamental & Financial Statement Analyst

A Python-based fundamental analysis tool that leverages AI to analyze financial data and generate comprehensive reports for stock trading decisions.

## Overview

The Fundamental Analyst uses OpenRouter API with the `xiaomi/mimo-v2-flash:free` model to analyze:

- **Key Financial Statistics** from Finviz and Yahoo Finance
- **Company Information** (Business Summary, Sector, Industry)
- **Historical Valuation Metrics** (P/E, P/B, Market Cap trends)
- **Financial Statements**:
  - Balance Sheet
  - Income Statement
  - Cash Flow Statement

## Features

✅ Loads and processes multiple data sources automatically  
✅ Formats financial data into AI-readable format  
✅ Generates comprehensive analysis reports with actionable insights  
✅ Supports single ticker and batch analysis  
✅ Saves reports in Markdown format for easy reading  

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up OpenRouter API Key:**

Get your free API key from [OpenRouter](https://openrouter.ai/)

**Windows PowerShell:**
```powershell
$env:OPENROUTER_API_KEY='your-api-key-here'
```

**Windows CMD:**
```cmd
set OPENROUTER_API_KEY=your-api-key-here
```

**Linux/Mac:**
```bash
export OPENROUTER_API_KEY='your-api-key-here'
```

## Usage

### Option 1: Command Line Interface

Analyze a single ticker:

```bash
python -m src.analyst.fundamental AAPL --data-dir data/raw/20251230_100857
```

With custom output directory:

```bash
python -m src.analyst.fundamental AAPL --data-dir data/raw/20251230_100857 --output-dir reports/fundamental
```

### Option 2: Using the Example Script

```bash
python example_fundamental_analysis.py
```

Edit `TICKER` and `DATA_DIR` in the script to analyze different stocks.

### Option 3: Batch Analysis

Analyze multiple tickers at once:

```bash
python analyze_batch.py
```

Edit the `TICKERS` list in `analyze_batch.py` to customize which stocks to analyze.

### Option 4: Python API

```python
from src.analyst.fundamental import FundamentalAnalyst

# Initialize
analyst = FundamentalAnalyst(api_key='your-api-key')

# Analyze single ticker
report = analyst.analyze(
    ticker='AAPL',
    data_dir='data/raw/20251230_100857'
)

print(report)

# Or analyze and save to file
report_path = analyst.analyze_and_save(
    ticker='AAPL',
    data_dir='data/raw/20251230_100857',
    output_dir='reports/fundamental'
)
```

## Data Structure

The analyst expects data to be organized as follows:

```
data/raw/YYYYMMDD_HHMMSS/
  ├── AAPL/
  │   ├── finviz_KeyFinanceStat_finviz.csv
  │   ├── yfinance_TickerInfo.json
  │   ├── yfinance_KeyFinanceStat_yfiance.csv
  │   ├── yfinance_HistoricalStat.csv
  │   ├── yfinance_FinancialReport_Balance_Sheet.csv
  │   ├── yfinance_FinancialReport_Income_Statement.csv
  │   └── yfinance_FinancialReport_Cash_Flow.csv
  ├── GOOGL/
  ├── MSFT/
  └── TSLA/
```

## Report Contents

Each generated report includes:

1. **Company Overview** - Business model, sector, and industry analysis
2. **Financial Health Analysis** - Balance sheet strength and liquidity
3. **Profitability Analysis** - Revenue, margins, and earnings trends
4. **Cash Flow Analysis** - Operating, investing, and financing activities
5. **Valuation Metrics** - P/E, P/B, and other valuation indicators
6. **Key Strengths and Weaknesses** - Competitive advantages and risks
7. **Investment Considerations** - Trading recommendations and insights
8. **Summary Table** - Quick reference of key metrics

## API Configuration

**Model:** `xiaomi/mimo-v2-flash:free`  
**Provider:** OpenRouter  
**Endpoint:** `https://openrouter.ai/api/v1/chat/completions`  

The model is configured to provide detailed, fine-grained analysis rather than generic statements.

## Troubleshooting

### Error: "OpenRouter API key must be provided"
- Make sure you've set the `OPENROUTER_API_KEY` environment variable
- Or pass the API key directly when initializing: `FundamentalAnalyst(api_key='your-key')`

### Error: "Data directory for TICKER not found"
- Verify the data directory path is correct
- Ensure the ticker folder exists in the data directory
- Check that required CSV/JSON files are present

### API Request Timeout
- The default timeout is 120 seconds
- Some complex analyses may take longer
- Check your internet connection

## Examples

### Example 1: Quick Analysis

```python
from src.analyst.fundamental import FundamentalAnalyst

analyst = FundamentalAnalyst()
report = analyst.analyze('AAPL', 'data/raw/20251230_100857')
print(report)
```

### Example 2: Analyze Multiple Companies

```python
from src.analyst.fundamental import FundamentalAnalyst

analyst = FundamentalAnalyst()
tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']

for ticker in tickers:
    try:
        analyst.analyze_and_save(
            ticker=ticker,
            data_dir='data/raw/20251230_100857',
            output_dir='reports/fundamental'
        )
        print(f"✓ {ticker} complete")
    except Exception as e:
        print(f"✗ {ticker} failed: {e}")
```

## License

This tool is part of the Portfolio Builder project.

## Contributing

To add more data sources or customize the analysis:

1. Edit the `load_data()` method to load additional data files
2. Update `format_data_for_prompt()` to include the new data in the AI prompt
3. Adjust the system/user messages in `analyze()` to guide the AI analysis

## Notes

- The free tier of the OpenRouter API may have rate limits
- Analysis quality depends on the completeness of input data
- Reports are generated in Markdown format for easy reading and sharing
- All financial data should be up-to-date for accurate analysis

