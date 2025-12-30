"""
Batch Fundamental Analysis

Analyze multiple tickers at once and generate reports for all of them.
"""

import os
from pathlib import Path
from src.analyst.fundamental import FundamentalAnalyst

# Configuration
TICKERS = ["AAPL", "GOOGL", "MSFT", "TSLA"]  # Add more tickers as needed
DATA_DIR = "data/raw/20251230_100857"
OUTPUT_DIR = "reports/fundamental"  # Where to save all reports
API_KEY = os.environ.get('OPENROUTER_API_KEY')


def main():
    """Analyze multiple tickers in batch"""
    
    print("=" * 70)
    print("Batch Fundamental Analysis")
    print("=" * 70)
    
    # Check if API key is set
    if not API_KEY:
        print("\n⚠️  Error: OPENROUTER_API_KEY environment variable not set")
        print("Please set it before running this script.")
        return
    
    # Create output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # Initialize analyst
    analyst = FundamentalAnalyst(api_key=API_KEY)
    
    # Track results
    successful = []
    failed = []
    
    # Analyze each ticker
    for i, ticker in enumerate(TICKERS, 1):
        print(f"\n[{i}/{len(TICKERS)}] Processing {ticker}...")
        print("-" * 70)
        
        try:
            report_path = analyst.analyze_and_save(
                ticker=ticker,
                data_dir=DATA_DIR,
                output_dir=OUTPUT_DIR
            )
            successful.append((ticker, report_path))
            print(f"✓ {ticker} analysis complete!")
            
        except Exception as e:
            failed.append((ticker, str(e)))
            print(f"✗ {ticker} analysis failed: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("Batch Analysis Summary")
    print("=" * 70)
    
    if successful:
        print(f"\n✓ Successfully analyzed {len(successful)} ticker(s):")
        for ticker, path in successful:
            print(f"  - {ticker}: {path}")
    
    if failed:
        print(f"\n✗ Failed to analyze {len(failed)} ticker(s):")
        for ticker, error in failed:
            print(f"  - {ticker}: {error}")
    
    print(f"\nAll reports saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

