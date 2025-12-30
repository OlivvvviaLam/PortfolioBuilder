"""
Example: How to use the Fundamental Analyst

This script demonstrates how to use the FundamentalAnalyst class to analyze
financial data for a given ticker.
"""

import os
from src.analyst.fundamental import FundamentalAnalyst

# Configuration
TICKER = "AAPL"  # Change this to analyze different stocks
DATA_DIR = "data/raw/20251230_100857"  # Path to your data directory
API_KEY = os.environ.get('OPENROUTER_API_KEY')  # Get API key from environment

def main():
    """Run fundamental analysis on a ticker"""
    
    print("=" * 60)
    print("Fundamental Analysis Example")
    print("=" * 60)
    
    # Check if API key is set
    if not API_KEY:
        print("\n⚠️  Warning: OPENROUTER_API_KEY environment variable not set")
        print("Please set it using:")
        print("  Windows PowerShell: $env:OPENROUTER_API_KEY='your-api-key-here'")
        print("  Windows CMD: set OPENROUTER_API_KEY=your-api-key-here")
        print("  Linux/Mac: export OPENROUTER_API_KEY='your-api-key-here'")
        return
    
    try:
        # Initialize the analyst
        print(f"\nInitializing Fundamental Analyst...")
        analyst = FundamentalAnalyst(api_key=API_KEY)
        
        # Analyze and save report
        print(f"Analyzing {TICKER}...\n")
        report_path = analyst.analyze_and_save(
            ticker=TICKER,
            data_dir=DATA_DIR
        )
        
        print("\n" + "=" * 60)
        print("✓ Analysis Complete!")
        print("=" * 60)
        print(f"Report saved to: {report_path}")
        
        # Read and display first few lines of the report
        print("\nPreview of the report:")
        print("-" * 60)
        with open(report_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:20]
            print(''.join(lines))
            if len(lines) >= 20:
                print("\n... (see full report in file)")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: Data not found - {e}")
        print(f"Make sure the data directory exists: {DATA_DIR}/{TICKER}")
    except ValueError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

