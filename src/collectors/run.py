import json
import shutil
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Union
from _yfinance import YFinanceCollector
from finviz import FinvizCollector


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


def collect_all_data(ticker: str, output_base_dir: str = "data/processed") -> str:
    """
    Collect data from both YFinance and Finviz collectors and save to a single directory.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        output_base_dir: Base directory for output
        
    Returns:
        Path to the output directory
    """
    print(f"\n{'='*60}")
    print(f"Starting data collection for {ticker}")
    print(f"{'='*60}\n")
    
    # Create timestamped output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(output_base_dir) / f"{ticker}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Output directory: {output_dir}\n")
    
    # Initialize collectors
    print("Initializing collectors...")
    yf_collector = YFinanceCollector(ticker)
    fv_collector = FinvizCollector(ticker, rps=3.0)
    
    # Track all saved files
    saved_files = []
    
    # Collect YFinance data
    print("\n[1/2] Collecting YFinance data...")
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
            elif result.get("status") == "empty":
                print(f"    ○ {key} (empty)")
                
    except Exception as e:
        print(f"✗ Error collecting YFinance data: {e}")
        import traceback
        traceback.print_exc()
    
    # Collect Finviz data
    print("\n[2/2] Collecting Finviz data...")
    try:
        fv_data = fv_collector.get_all_data()
        print(f"✓ Finviz data collected: {len(fv_data)} data points")
        
        print("  Saving Finviz data...")
        for key, value in fv_data.items():
            result = save_data_item(value, key, output_dir, prefix="finviz_")
            saved_files.append(result)
            if result.get("status") == "saved":
                print(f"    ✓ {key} ({result['type']})")
            elif result.get("status") == "copied":
                print(f"    ✓ {key} (File copied)")
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
    print(f"  Total files saved: {len([f for f in saved_files if f.get('status') in ['saved', 'copied']])}")
    print(f"  Summary file: {summary_path}")
    print(f"{'='*60}\n")
    
    return str(output_dir)


def main():
    """Main execution function."""
    # Example usage - change ticker as needed
    ticker = "AAPL"  # You can change this to any ticker
    
    # Uncomment to prompt for ticker input:
    # ticker = input("Enter ticker symbol (e.g., AAPL): ").strip().upper()
    # if not ticker:
    #     ticker = "AAPL"
    #     print(f"No ticker provided, using default: {ticker}")
    
    try:
        output_dir = collect_all_data(ticker)
        print(f"Success! Check the output directory: {output_dir}")
    except Exception as e:
        print(f"\n✗ Error during data collection: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

