# In run.py or a separate script
from src.collectors.run import collect_all_data
from datetime import datetime

tickers = ["AAPL", "MSFT", "GOOGL", "TSLA"]

# Generate a single timestamp for the entire run
run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
print(f"Starting collection run with timestamp: {run_timestamp}\n")

for ticker in tickers:
    print(f"Processing {ticker}...")
    output_dir, _ = collect_all_data(ticker, timestamp=run_timestamp)
    print(f"Completed {ticker} -> {output_dir}\n")

print(f"\n✓ All tickers collected under timestamp: {run_timestamp}")