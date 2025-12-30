"""
Test script for Fundamental Analyst

This script tests the fundamental analyst functionality without making API calls.
It verifies that data loading and formatting work correctly.
"""

from src.analyst.fundamental import FundamentalAnalyst
from pathlib import Path


def test_data_loading():
    """Test if data can be loaded correctly"""
    print("Testing data loading...")
    
    # Configuration
    ticker = "AAPL"
    data_dir = "data/raw/20251230_100857"
    
    # Check if data exists
    ticker_path = Path(data_dir) / ticker
    if not ticker_path.exists():
        print(f"❌ Test skipped: Data directory not found: {ticker_path}")
        return False
    
    try:
        # Initialize analyst (dummy API key for testing)
        analyst = FundamentalAnalyst(api_key="test-key")
        
        # Load data
        data = analyst.load_data(ticker, data_dir)
        
        # Verify data was loaded
        expected_keys = ['ticker', 'data_path']
        optional_keys = [
            'finviz_key_stats',
            'ticker_info',
            'yfinance_key_stats',
            'historical_stats',
            'balance_sheet',
            'income_statement',
            'cash_flow'
        ]
        
        # Check required keys
        for key in expected_keys:
            if key not in data:
                print(f"❌ Missing required key: {key}")
                return False
        
        # Report what was loaded
        print(f"✓ Data loaded for {ticker}")
        print(f"  - Data path: {data['data_path']}")
        
        loaded_data = []
        for key in optional_keys:
            if key in data:
                loaded_data.append(key)
        
        print(f"  - Loaded datasets: {', '.join(loaded_data)}")
        
        # Test data formatting
        print("\nTesting data formatting...")
        formatted_data = analyst.format_data_for_prompt(data)
        
        if not formatted_data or len(formatted_data) < 100:
            print("❌ Formatted data seems too short")
            return False
        
        print(f"✓ Data formatted successfully ({len(formatted_data)} characters)")
        
        # Show preview of formatted data
        print("\nPreview of formatted data (first 500 chars):")
        print("-" * 70)
        print(formatted_data[:500])
        print("...")
        print("-" * 70)
        
        return True
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_tickers():
    """Test data loading for all available tickers"""
    print("\nTesting all available tickers...")
    print("=" * 70)
    
    data_dir = "data/raw/20251230_100857"
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return
    
    # Find all ticker directories
    tickers = [d.name for d in data_path.iterdir() if d.is_dir()]
    
    if not tickers:
        print(f"❌ No ticker directories found in {data_dir}")
        return
    
    print(f"Found {len(tickers)} ticker(s): {', '.join(tickers)}\n")
    
    analyst = FundamentalAnalyst(api_key="test-key")
    
    results = {}
    for ticker in tickers:
        try:
            print(f"Testing {ticker}...", end=" ")
            data = analyst.load_data(ticker, data_dir)
            
            # Count loaded datasets
            dataset_count = sum(1 for key in [
                'finviz_key_stats', 'ticker_info', 'yfinance_key_stats',
                'historical_stats', 'balance_sheet', 'income_statement', 'cash_flow'
            ] if key in data)
            
            results[ticker] = f"✓ ({dataset_count} datasets)"
            print(results[ticker])
            
        except Exception as e:
            results[ticker] = f"✗ ({str(e)})"
            print(results[ticker])
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary:")
    for ticker, result in results.items():
        print(f"  {ticker}: {result}")


def main():
    """Run all tests"""
    print("=" * 70)
    print("Fundamental Analyst - Test Suite")
    print("=" * 70)
    print()
    
    # Test 1: Data loading for single ticker
    success = test_data_loading()
    
    if success:
        # Test 2: All tickers
        test_all_tickers()
    
    print("\n" + "=" * 70)
    print("Tests complete!")
    print("=" * 70)
    print("\nNote: These tests only verify data loading and formatting.")
    print("To test the full analysis with API calls, use example_fundamental_analysis.py")
    print("Make sure to set OPENROUTER_API_KEY environment variable first.")


if __name__ == "__main__":
    main()

