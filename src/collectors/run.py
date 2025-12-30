import json
import shutil
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Union
from src.collectors._yfinance import YFinanceCollector
from src.collectors.finviz import FinvizCollector
from src.collectors.technical_indicator import TechnicalIndicator


def sanitize_filename(name: str) -> str:
    """Convert a key name to a safe filename."""
    # Replace special characters with underscores
    safe_name = name.replace("/", "_").replace("\\", "_").replace(" ", "_")
    safe_name = "".join(c if c.isalnum() or c in "_-" else "_" for c in safe_name)
    return safe_name


def save_data_item(data: Any, name: str, output_dir: Path, prefix: str = "") -> Dict[str, str]:
    """
    Save a single data item to the appropriate format.
    
    Args:
        data: The data to save (DataFrame, dict, list, or string)
        name: The name/key of this data item
        output_dir: Directory to save the file
        prefix: Optional prefix for the filename (e.g., 'yfinance_' or 'finviz_')
    
    Returns:
        Dictionary with info about what was saved
    """
    safe_name = sanitize_filename(name)
    filename_base = f"{prefix}{safe_name}" if prefix else safe_name
    
    # Handle DataFrames - save as CSV
    if isinstance(data, pd.DataFrame):
        if data.empty:
            return {"type": "DataFrame", "status": "empty", "name": name}
        
        csv_path = output_dir / f"{filename_base}.csv"
        data.to_csv(csv_path, index=True)
        return {
            "type": "DataFrame",
            "status": "saved",
            "name": name,
            "file": str(csv_path),
            "rows": len(data),
            "columns": len(data.columns)
        }
    
    # Handle dictionaries
    elif isinstance(data, dict):
        # Check if it's a dictionary of DataFrames (like FinancialReport)
        if all(isinstance(v, pd.DataFrame) for v in data.values()):
            saved_items = {}
            for sub_key, sub_df in data.items():
                if not sub_df.empty:
                    sub_safe_name = sanitize_filename(sub_key)
                    csv_path = output_dir / f"{filename_base}_{sub_safe_name}.csv"
                    sub_df.to_csv(csv_path, index=True)
                    saved_items[sub_key] = str(csv_path)
            
            return {
                "type": "Dict[DataFrame]",
                "status": "saved",
                "name": name,
                "files": saved_items
            }
        
        # Regular dictionary - save as JSON
        else:
            json_path = output_dir / f"{filename_base}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            return {
                "type": "Dict",
                "status": "saved",
                "name": name,
                "file": str(json_path)
            }
    
    # Handle lists - save as JSON
    elif isinstance(data, list):
        json_path = output_dir / f"{filename_base}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return {
            "type": "List",
            "status": "saved",
            "name": name,
            "file": str(json_path),
            "items": len(data)
        }
    
    # Handle string paths (like image paths)
    elif isinstance(data, str):
        # Check if it's a file path that exists
        source_path = Path(data)
        if source_path.exists() and source_path.is_file():
            # Copy the file to output directory
            dest_path = output_dir / source_path.name
            
            # Check if source and destination are the same (resolve to absolute paths)
            if source_path.resolve() == dest_path.resolve():
                # File is already in the correct location, no need to copy
                return {
                    "type": "File",
                    "status": "already_exists",
                    "name": name,
                    "file": str(dest_path)
                }
            
            shutil.copy2(source_path, dest_path)
            return {
                "type": "File",
                "status": "copied",
                "name": name,
                "source": str(source_path),
                "destination": str(dest_path)
            }
        else:
            # Just a string value, save as text
            txt_path = output_dir / f"{filename_base}.txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(data)
            return {
                "type": "String",
                "status": "saved",
                "name": name,
                "file": str(txt_path)
            }
    
    else:
        return {"type": type(data).__name__, "status": "unsupported", "name": name}


def collect_all_data(ticker: str, output_base_dir: str = "data/raw", timestamp: str = None) -> str:
    """
    Collect data from both YFinance and Finviz collectors and save to a single directory.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        output_base_dir: Base directory for output
        timestamp: Optional timestamp string. If not provided, a new one will be generated.
                   Pass the same timestamp to collect multiple tickers in the same run.
        
    Returns:
        Path to the output directory
    """
    print(f"\n{'='*60}")
    print(f"Starting data collection for {ticker}")
    print(f"{'='*60}\n")
    
    # Create timestamped output directory: data/raw/{timestamp}/{ticker}/
    # Use provided timestamp or generate a new one
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(output_base_dir) / timestamp / ticker
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Output directory: {output_dir}\n")
    
    # Initialize collectors
    print("Initializing collectors...")
    yf_collector = YFinanceCollector(ticker)
    fv_collector = FinvizCollector(ticker, rps=3.0)
    
    # Track all saved files
    saved_files = []
    
    # Collect YFinance data
    print("\n[1/3] Collecting YFinance data...")
    try:
        yf_data = yf_collector.get_all_data()
        print(f"✓ YFinance data collected: {len(yf_data)} data points")
        
        print("  Saving YFinance data...")
        for key, value in yf_data.items():
            result = save_data_item(value, key, output_dir, prefix="yfinance_")
            saved_files.append(result)
            if result.get("status") == "saved":
                print(f"    ✓ {key} ({result['type']})")
            elif result.get("status") == "copied":
                print(f"    ✓ {key} (File copied)")
            elif result.get("status") == "already_exists":
                print(f"    ✓ {key} (File already in place)")
            elif result.get("status") == "empty":
                print(f"    ○ {key} (empty)")
                
    except Exception as e:
        print(f"✗ Error collecting YFinance data: {e}")
        import traceback
        traceback.print_exc()
    
    # Process technical indicators
    print("\n[2/3] Processing Technical Indicators...")
    try:
        ti = TechnicalIndicator()
        
        # Define paths to historical data files
        daily_path = output_dir / "yfinance_History1mo_d.csv"
        weekly_path = output_dir / "yfinance_History6m_1wk.csv"
        monthly_path = output_dir / "yfinance_History2y_1mo.csv"
        
        # Process daily indicators if file exists
        if daily_path.exists():
            print("  Processing daily indicators (1mo)...")
            df_daily = pd.read_csv(daily_path)
            df_daily_res = ti.calculate_1mo_daily(df_daily)
            
            output_daily = output_dir / "yfinance_History1mo_d_indicators.csv"
            df_daily_res.to_csv(output_daily, index=False)
            saved_files.append({
                "type": "DataFrame",
                "status": "saved",
                "name": "History1mo_d_indicators",
                "file": str(output_daily),
                "rows": len(df_daily_res),
                "columns": len(df_daily_res.columns)
            })
            print(f"    ✓ Daily indicators saved")
            
            # Generate 3 daily charts
            print(f"    Generating daily charts...")
            chart_daily_price = output_dir / "yfinance_History1mo_d_price_overlays.png"
            ti.plot_price_overlays(df_daily_res, chart_daily_price, title=f"{ticker} - Daily")
            saved_files.append({
                "type": "File",
                "status": "saved",
                "name": "History1mo_d_price_overlays",
                "file": str(chart_daily_price)
            })
            
            chart_daily_momentum = output_dir / "yfinance_History1mo_d_momentum.png"
            ti.plot_momentum_indicators(df_daily_res, chart_daily_momentum, title=f"{ticker} - Daily")
            saved_files.append({
                "type": "File",
                "status": "saved",
                "name": "History1mo_d_momentum",
                "file": str(chart_daily_momentum)
            })
            
            chart_daily_volume = output_dir / "yfinance_History1mo_d_volume.png"
            ti.plot_volume_indicators(df_daily_res, chart_daily_volume, title=f"{ticker} - Daily")
            saved_files.append({
                "type": "File",
                "status": "saved",
                "name": "History1mo_d_volume",
                "file": str(chart_daily_volume)
            })
            print(f"    ✓ Daily charts generated (3 files)")
        
        # Process weekly indicators if file exists
        if weekly_path.exists():
            print("  Processing weekly indicators (6m)...")
            df_weekly = pd.read_csv(weekly_path)
            df_weekly_res = ti.calculate_6m_weekly(df_weekly)
            
            output_weekly = output_dir / "yfinance_History6m_1wk_indicators.csv"
            df_weekly_res.to_csv(output_weekly, index=False)
            saved_files.append({
                "type": "DataFrame",
                "status": "saved",
                "name": "History6m_1wk_indicators",
                "file": str(output_weekly),
                "rows": len(df_weekly_res),
                "columns": len(df_weekly_res.columns)
            })
            print(f"    ✓ Weekly indicators saved")
            
            # Generate 3 weekly charts
            print(f"    Generating weekly charts...")
            chart_weekly_price = output_dir / "yfinance_History6m_1wk_price_overlays.png"
            ti.plot_price_overlays(df_weekly_res, chart_weekly_price, title=f"{ticker} - Weekly")
            saved_files.append({
                "type": "File",
                "status": "saved",
                "name": "History6m_1wk_price_overlays",
                "file": str(chart_weekly_price)
            })
            
            chart_weekly_momentum = output_dir / "yfinance_History6m_1wk_momentum.png"
            ti.plot_momentum_indicators(df_weekly_res, chart_weekly_momentum, title=f"{ticker} - Weekly")
            saved_files.append({
                "type": "File",
                "status": "saved",
                "name": "History6m_1wk_momentum",
                "file": str(chart_weekly_momentum)
            })
            
            chart_weekly_volume = output_dir / "yfinance_History6m_1wk_volume.png"
            ti.plot_volume_indicators(df_weekly_res, chart_weekly_volume, title=f"{ticker} - Weekly")
            saved_files.append({
                "type": "File",
                "status": "saved",
                "name": "History6m_1wk_volume",
                "file": str(chart_weekly_volume)
            })
            print(f"    ✓ Weekly charts generated (3 files)")
        
        # Process monthly indicators if file exists
        if monthly_path.exists():
            print("  Processing monthly indicators (2y)...")
            df_monthly = pd.read_csv(monthly_path)
            df_monthly_res = ti.calculate_2y_monthly(df_monthly)
            
            output_monthly = output_dir / "yfinance_History2y_1mo_indicators.csv"
            df_monthly_res.to_csv(output_monthly, index=False)
            saved_files.append({
                "type": "DataFrame",
                "status": "saved",
                "name": "History2y_1mo_indicators",
                "file": str(output_monthly),
                "rows": len(df_monthly_res),
                "columns": len(df_monthly_res.columns)
            })
            print(f"    ✓ Monthly indicators saved")
            
            # Generate 3 monthly charts
            print(f"    Generating monthly charts...")
            chart_monthly_price = output_dir / "yfinance_History2y_1mo_price_overlays.png"
            ti.plot_price_overlays(df_monthly_res, chart_monthly_price, title=f"{ticker} - Monthly")
            saved_files.append({
                "type": "File",
                "status": "saved",
                "name": "History2y_1mo_price_overlays",
                "file": str(chart_monthly_price)
            })
            
            chart_monthly_momentum = output_dir / "yfinance_History2y_1mo_momentum.png"
            ti.plot_momentum_indicators(df_monthly_res, chart_monthly_momentum, title=f"{ticker} - Monthly")
            saved_files.append({
                "type": "File",
                "status": "saved",
                "name": "History2y_1mo_momentum",
                "file": str(chart_monthly_momentum)
            })
            
            chart_monthly_volume = output_dir / "yfinance_History2y_1mo_volume.png"
            ti.plot_volume_indicators(df_monthly_res, chart_monthly_volume, title=f"{ticker} - Monthly")
            saved_files.append({
                "type": "File",
                "status": "saved",
                "name": "History2y_1mo_volume",
                "file": str(chart_monthly_volume)
            })
            print(f"    ✓ Monthly charts generated (3 files)")
        
        print(f"✓ Technical indicators processing complete")
        
    except Exception as e:
        print(f"✗ Error processing technical indicators: {e}")
        import traceback
        traceback.print_exc()
    
    # Collect Finviz data
    print("\n[3/3] Collecting Finviz data...")
    try:
        # Pass output_dir to save charts in the data directory instead of "charts"
        fv_data = fv_collector.get_all_data(chart_output_dir=str(output_dir))
        print(f"✓ Finviz data collected: {len(fv_data)} data points")
        
        print("  Saving Finviz data...")
        for key, value in fv_data.items():
            result = save_data_item(value, key, output_dir, prefix="finviz_")
            saved_files.append(result)
            if result.get("status") == "saved":
                print(f"    ✓ {key} ({result['type']})")
            elif result.get("status") == "copied":
                print(f"    ✓ {key} (File copied)")
            elif result.get("status") == "already_exists":
                print(f"    ✓ {key} (File already in place)")
            elif result.get("status") == "empty":
                print(f"    ○ {key} (empty)")
                
    except Exception as e:
        print(f"✗ Error collecting Finviz data: {e}")
        import traceback
        traceback.print_exc()
    
    # Save metadata and summary
    metadata = {
        "ticker": ticker,
        "collection_time": datetime.now().isoformat(),
        "timestamp": timestamp,
        "collectors": ["YFinance", "Finviz"],
        "output_directory": str(output_dir),
        "saved_files": saved_files
    }
    
    summary_path = output_dir / "_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"✓ Data collection complete!")
    print(f"  Output directory: {output_dir}")
    print(f"  Total files saved: {len([f for f in saved_files if f.get('status') in ['saved', 'copied', 'already_exists']])}")
    print(f"  Summary file: {summary_path}")
    print(f"{'='*60}\n")
    
    return str(output_dir), timestamp


def main():
    """Main execution function."""
    # Example usage - collect data for multiple tickers in a single run
    # All tickers will share the same timestamp
    tickers = ["AAPL"]  # You can add multiple tickers, e.g., ["AAPL", "MSFT", "GOOGL"]
    
    # Uncomment to prompt for ticker input:
    # ticker_input = input("Enter ticker symbols separated by commas (e.g., AAPL,MSFT): ").strip().upper()
    # if ticker_input:
    #     tickers = [t.strip() for t in ticker_input.split(",")]
    # else:
    #     print(f"No tickers provided, using default: {tickers}")
    
    try:
        # Generate a single timestamp for the entire run
        run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"\n{'='*60}")
        print(f"Starting data collection run")
        print(f"Timestamp: {run_timestamp}")
        print(f"Tickers: {', '.join(tickers)}")
        print(f"{'='*60}")
        
        output_dirs = []
        for ticker in tickers:
            output_dir, _ = collect_all_data(ticker, timestamp=run_timestamp)
            output_dirs.append(output_dir)
        
        print(f"\n{'='*60}")
        print(f"✓ All data collection complete!")
        print(f"  Collected {len(tickers)} ticker(s)")
        print(f"  Shared timestamp: {run_timestamp}")
        print(f"  Output directories:")
        for output_dir in output_dirs:
            print(f"    - {output_dir}")
        print(f"{'='*60}\n")
    except Exception as e:
        print(f"\n✗ Error during data collection: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

