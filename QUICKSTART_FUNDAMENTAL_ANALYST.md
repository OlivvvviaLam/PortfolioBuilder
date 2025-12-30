# Quick Start Guide - Fundamental Analyst

Get started with fundamental analysis in 3 simple steps!

## Step 1: Setup (One-time)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Get OpenRouter API Key
1. Visit [https://openrouter.ai/](https://openrouter.ai/)
2. Sign up for a free account
3. Get your API key from the dashboard

### Set Environment Variable

**Windows PowerShell:**
```powershell
$env:OPENROUTER_API_KEY='sk-or-v1-...'
```

**Windows CMD:**
```cmd
set OPENROUTER_API_KEY=sk-or-v1-...
```

**Linux/Mac:**
```bash
export OPENROUTER_API_KEY='sk-or-v1-...'
```

## Step 2: Test Your Setup

Run the test script to verify data loading works:

```bash
python test_fundamental_analyst.py
```

You should see output like:
```
✓ Data loaded for AAPL
  - Loaded datasets: finviz_key_stats, ticker_info, yfinance_key_stats, ...
```

## Step 3: Run Your First Analysis

### Option A: Single Stock Analysis

```bash
python example_fundamental_analysis.py
```

This will analyze AAPL by default. Edit the script to change the ticker.

### Option B: Command Line

```bash
python -m src.analyst.fundamental AAPL --data-dir data/raw/20251230_100857
```

### Option C: Batch Analysis (Multiple Stocks)

```bash
python analyze_batch.py
```

This analyzes AAPL, GOOGL, MSFT, and TSLA by default.

## What You'll Get

After running the analysis, you'll get a comprehensive Markdown report with:

- 📊 Company overview and business model
- 💰 Financial health analysis
- 📈 Profitability trends
- 💵 Cash flow analysis
- 🎯 Valuation metrics
- ⚡ Key strengths and weaknesses
- 💡 Investment considerations
- 📋 Summary table with key insights

## Example Output Location

Reports are saved to:
```
data/raw/20251230_100857/AAPL/AAPL_fundamental_analysis_20251230_143052.md
```

Or if you specify an output directory:
```
reports/fundamental/AAPL_fundamental_analysis_20251230_143052.md
```

## Troubleshooting

### "OPENROUTER_API_KEY environment variable not set"
- Make sure you've set the environment variable in your current terminal session
- The variable only persists in the current session - you'll need to set it again if you open a new terminal

### "Data directory for AAPL not found"
- Check that your data directory path is correct
- Verify the ticker folder exists: `data/raw/20251230_100857/AAPL/`
- Make sure the required CSV and JSON files are present

### API Timeout or Rate Limit
- The free tier may have rate limits
- Wait a few minutes between requests
- Consider upgrading to a paid plan for higher limits

## Next Steps

1. **Customize the analysis prompt** - Edit `src/analyst/fundamental.py` to modify the system message
2. **Add more data sources** - Extend the `load_data()` method to include additional files
3. **Automate reports** - Set up a scheduled task to run analysis regularly
4. **Compare multiple stocks** - Use batch analysis to compare fundamentals across your portfolio

## Tips

💡 **Save your API key permanently** (Windows):
```powershell
[System.Environment]::SetEnvironmentVariable('OPENROUTER_API_KEY', 'sk-or-v1-...', 'User')
```

💡 **Run analysis for a specific date folder**:
```bash
python -m src.analyst.fundamental AAPL --data-dir data/raw/20251230_100857
```

💡 **Organize reports by date**:
```bash
python -m src.analyst.fundamental AAPL --data-dir data/raw/20251230_100857 --output-dir reports/20251230
```

## Need Help?

- Check `README_FUNDAMENTAL_ANALYST.md` for detailed documentation
- Review the example scripts for usage patterns
- Run `test_fundamental_analyst.py` to verify your setup

Happy analyzing! 📊

