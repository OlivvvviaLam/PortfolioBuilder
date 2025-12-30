# In run.py or a separate script
from src.collectors.run import collect_all_data, collect_global_news
from datetime import datetime

tickers = ["AAPL", "MSFT", "GOOGL", "TSLA"]

# Generate a single timestamp for the entire run (date only)
run_timestamp = datetime.now().strftime("%Y%m%d")
print(f"Starting collection run with date: {run_timestamp}\n")

# Collect global news once per date (before ticker-specific data)
news_file, _, news_skipped = collect_global_news(timestamp=run_timestamp)

for ticker in tickers:
    print(f"Processing {ticker}...")
    output_dir, _, skipped = collect_all_data(ticker, timestamp=run_timestamp)
    if skipped:
        print(f"Skipped {ticker} (already exists) -> {output_dir}\n")
    else:
        print(f"Completed {ticker} -> {output_dir}\n")

print(f"\n✓ All tickers collected under date: {run_timestamp}")
print(f"  Global News: {'Skipped (already exists)' if news_skipped else 'Collected'}")
if news_file:
    print(f"    File: {news_file}")