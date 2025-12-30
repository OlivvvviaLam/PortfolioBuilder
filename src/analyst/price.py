"""
Price Analysis Integrator

This module integrates:
- Price chart image analysis reports (from price_image.py)
- Historical price and technical indicator data from CSV files
- Combines visual chart analysis with numerical technical indicators
"""

import os
import pandas as pd
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List


class PriceAnalyst:
    """Integrates price chart analysis with technical indicator data"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Price Analyst
        
        Args:
            api_key: OpenRouter API key. If None, will try to get from environment variable OPENROUTER_API_KEY
        """
        self.api_key = api_key or os.environ.get('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OpenRouter API key must be provided or set in OPENROUTER_API_KEY environment variable")
        
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "xiaomi/mimo-v2-flash:free"
        
    def find_price_image_reports(self, ticker: str, base_output_dir: str) -> Dict[str, Optional[str]]:
        """
        Find the most recent price image analysis reports
        
        Args:
            ticker: Stock ticker symbol
            base_output_dir: Base output directory (e.g., data/output)
            
        Returns:
            Dictionary with paths to basic, short-term, and long-term reports
        """
        base_path = Path(base_output_dir)
        reports = {
            'basic': None,
            'short_term': None,
            'long_term': None
        }
        
        if not base_path.exists():
            return reports
        
        # Find the most recent timestamp directory with price_image reports
        price_image_dirs = sorted(base_path.glob("*/analyst/price_image"), reverse=True)
        
        for price_image_dir in price_image_dirs:
            # Look for the three report types
            basic_reports = list(price_image_dir.glob(f"{ticker}_price_basic_analysis_*.md"))
            short_reports = list(price_image_dir.glob(f"{ticker}_price_shortterm_analysis_*.md"))
            long_reports = list(price_image_dir.glob(f"{ticker}_price_longterm_analysis_*.md"))
            
            if basic_reports and reports['basic'] is None:
                reports['basic'] = str(basic_reports[0])
            if short_reports and reports['short_term'] is None:
                reports['short_term'] = str(short_reports[0])
            if long_reports and reports['long_term'] is None:
                reports['long_term'] = str(long_reports[0])
            
            # If we found all three, we're done
            if all(reports.values()):
                break
        
        return reports
    
    def load_indicator_data(self, ticker: str, data_dir: str) -> Dict[str, Any]:
        """
        Load technical indicator CSV files
        
        Args:
            ticker: Stock ticker symbol
            data_dir: Path to the data directory containing ticker folders
            
        Returns:
            Dictionary containing dataframes for each timeframe
        """
        ticker_path = Path(data_dir) / ticker
        
        if not ticker_path.exists():
            raise ValueError(f"Data directory for {ticker} not found at {ticker_path}")
        
        data = {
            'ticker': ticker,
            'data_path': str(ticker_path)
        }
        
        # Load 1-year weekly indicators
        weekly_path = ticker_path / "yfinance_History1y_1wk_indicators.csv"
        if weekly_path.exists():
            df = pd.read_csv(weekly_path)
            data['weekly_indicators'] = df
        
        # Load 2-month daily indicators
        daily_path = ticker_path / "yfinance_History2mo_d_indicators.csv"
        if daily_path.exists():
            df = pd.read_csv(daily_path)
            data['daily_indicators'] = df
        
        # Load 4-year monthly indicators
        monthly_path = ticker_path / "yfinance_History4y_1mo_indicators.csv"
        if monthly_path.exists():
            df = pd.read_csv(monthly_path)
            data['monthly_indicators'] = df
        
        return data
    
    def format_indicator_summary(self, df: pd.DataFrame, timeframe: str, num_recent: int = 10) -> str:
        """
        Format indicator data into a summary string
        
        Args:
            df: DataFrame with indicator data
            timeframe: Description of the timeframe (e.g., "1-Year Weekly")
            num_recent: Number of recent rows to include
            
        Returns:
            Formatted string summary
        """
        if df is None or df.empty:
            return f"No {timeframe} data available.\n"
        
        # Get the most recent rows
        recent_df = df.tail(num_recent)
        
        # Select key columns if they exist
        key_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 
                      'SMA_10', 'SMA_20', 'EMA_10', 'EMA_20',
                      'RSI_14', 'MACD', 'MACD_Signal', 'MACD_Hist',
                      'BB_Upper', 'BB_Middle', 'BB_Lower', 'ATR_14']
        
        available_columns = [col for col in key_columns if col in recent_df.columns]
        
        if available_columns:
            summary_df = recent_df[available_columns]
        else:
            # If key columns don't exist, use first 10 columns
            summary_df = recent_df.iloc[:, :min(10, len(recent_df.columns))]
        
        output = f"### {timeframe} Indicators (Most Recent {len(recent_df)} periods)\n\n"
        output += summary_df.to_string(index=False)
        output += "\n\n"
        
        # Add current values summary
        if len(df) > 0:
            latest = df.iloc[-1]
            output += f"**Latest Values ({timeframe}):**\n"
            output += f"- Date: {latest.get('Date', 'N/A')}\n"
            output += f"- Close: {latest.get('Close', 'N/A')}\n"
            output += f"- RSI(14): {latest.get('RSI_14', 'N/A')}\n"
            output += f"- MACD: {latest.get('MACD', 'N/A')}\n"
            output += f"- MACD Signal: {latest.get('MACD_Signal', 'N/A')}\n"
            output += f"- Volume: {latest.get('Volume', 'N/A')}\n"
            output += "\n"
        
        return output
    
    def load_reports(self, report_paths: Dict[str, Optional[str]]) -> Dict[str, str]:
        """
        Load the content of price image analysis reports
        
        Args:
            report_paths: Dictionary with paths to reports
            
        Returns:
            Dictionary with report contents
        """
        reports = {}
        
        for report_type, path in report_paths.items():
            if path and Path(path).exists():
                with open(path, 'r', encoding='utf-8') as f:
                    reports[report_type] = f.read()
            else:
                reports[report_type] = f"No {report_type} report available."
        
        return reports
    
    def analyze(self, ticker: str, data_dir: str, output_base_dir: Optional[str] = None) -> str:
        """
        Perform integrated price analysis
        
        Args:
            ticker: Stock ticker symbol
            data_dir: Path to the data directory
            output_base_dir: Base output directory where price_image reports are stored
            
        Returns:
            Comprehensive integrated analysis report
        """
        print(f"Loading data for {ticker}...")
        
        # Determine output base directory
        if output_base_dir is None:
            base_path = Path(data_dir).parent
            if base_path.name == 'raw':
                base_path = base_path.parent
            output_base_dir = base_path / "output"
        
        # Load price image analysis reports
        print("Finding price image analysis reports...")
        report_paths = self.find_price_image_reports(ticker, str(output_base_dir))
        reports = self.load_reports(report_paths)
        
        print(f"  Basic report: {'✓' if reports.get('basic') != 'No basic report available.' else '✗'}")
        print(f"  Short-term report: {'✓' if reports.get('short_term') != 'No short_term report available.' else '✗'}")
        print(f"  Long-term report: {'✓' if reports.get('long_term') != 'No long_term report available.' else '✗'}")
        
        # Load indicator data
        print("\nLoading technical indicator data...")
        indicator_data = self.load_indicator_data(ticker, data_dir)
        
        # Format the data for the prompt
        formatted_data = self.format_data_for_prompt(ticker, reports, indicator_data)
        
        # Prepare the prompt
        current_date = datetime.now().strftime("%B %d, %Y")
        
        system_message = (
            "You are an expert technical analyst tasked with creating a comprehensive price analysis report. "
            "You have been provided with:\n"
            "1. AI-generated chart image analysis reports (basic, short-term, and long-term)\n"
            "2. Numerical technical indicator data from CSV files across multiple timeframes\n\n"
            "Your task is to synthesize these data sources into a unified, comprehensive analysis that:\n"
            "- Validates chart analysis insights with numerical indicator data\n"
            "- Identifies convergence or divergence between visual patterns and technical indicators\n"
            "- Provides actionable trading insights backed by both visual and numerical evidence\n"
            "- Highlights key price levels, trends, and momentum indicators\n"
            "- Offers clear trading recommendations with risk management guidelines\n\n"
            "Make sure to include as much detail as possible and provide a summary table at the end "
            "with key findings organized by timeframe (short-term, medium-term, long-term)."
        )
        
        user_message = (
            f"Current Date: {current_date}\n"
            f"Company Ticker: {ticker}\n\n"
            f"{formatted_data}\n\n"
            f"Please provide a comprehensive integrated price analysis that includes:\n"
            f"1. Executive Summary\n"
            f"2. Multi-Timeframe Trend Analysis\n"
            f"3. Technical Indicator Analysis (RSI, MACD, Moving Averages, etc.)\n"
            f"4. Support and Resistance Levels\n"
            f"5. Volume Analysis\n"
            f"6. Momentum and Volatility Assessment\n"
            f"7. Trading Opportunities and Risk Management\n"
            f"8. Short-term, Medium-term, and Long-term Outlook\n"
            f"9. Summary Table with Key Insights by Timeframe\n"
        )
        
        # Call OpenRouter API
        print(f"\nAnalyzing {ticker} using AI...")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=180
            )
            response.raise_for_status()
            
            result = response.json()
            analysis_report = result['choices'][0]['message']['content']
            
            return analysis_report
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling OpenRouter API: {str(e)}")
    
    def format_data_for_prompt(self, ticker: str, reports: Dict[str, str], 
                               indicator_data: Dict[str, Any]) -> str:
        """
        Format all data sources into a comprehensive prompt
        
        Args:
            ticker: Stock ticker symbol
            reports: Dictionary of report contents
            indicator_data: Dictionary of indicator dataframes
            
        Returns:
            Formatted string for the AI prompt
        """
        sections = []
        
        sections.append(f"# Integrated Price Analysis Data for {ticker}\n")
        
        # Section 1: Chart Image Analysis Reports
        sections.append("## Part 1: Chart Image Analysis Reports\n")
        
        if reports.get('basic'):
            sections.append("### Basic Chart Analysis (Daily & Weekly)\n")
            # Extract just the analysis content, skip the header
            basic_content = reports['basic'].split('---\n\n', 1)[-1] if '---\n\n' in reports['basic'] else reports['basic']
            sections.append(basic_content[:2000] + "...\n" if len(basic_content) > 2000 else basic_content)
            sections.append("")
        
        if reports.get('short_term'):
            sections.append("### Short-Term Chart Analysis (2-Month Daily)\n")
            short_content = reports['short_term'].split('---\n\n', 1)[-1] if '---\n\n' in reports['short_term'] else reports['short_term']
            sections.append(short_content[:2000] + "...\n" if len(short_content) > 2000 else short_content)
            sections.append("")
        
        if reports.get('long_term'):
            sections.append("### Long-Term Chart Analysis (1-Year Weekly & 4-Year Monthly)\n")
            long_content = reports['long_term'].split('---\n\n', 1)[-1] if '---\n\n' in reports['long_term'] else reports['long_term']
            sections.append(long_content[:2000] + "...\n" if len(long_content) > 2000 else long_content)
            sections.append("")
        
        # Section 2: Technical Indicator Data
        sections.append("## Part 2: Technical Indicator Data\n")
        
        if 'daily_indicators' in indicator_data:
            sections.append(self.format_indicator_summary(
                indicator_data['daily_indicators'], 
                "2-Month Daily",
                num_recent=10
            ))
        
        if 'weekly_indicators' in indicator_data:
            sections.append(self.format_indicator_summary(
                indicator_data['weekly_indicators'], 
                "1-Year Weekly",
                num_recent=10
            ))
        
        if 'monthly_indicators' in indicator_data:
            sections.append(self.format_indicator_summary(
                indicator_data['monthly_indicators'], 
                "4-Year Monthly",
                num_recent=12
            ))
        
        return "\n".join(sections)
    
    def analyze_and_save(self, ticker: str, data_dir: str, 
                        output_dir: Optional[str] = None,
                        output_base_dir: Optional[str] = None) -> str:
        """
        Analyze a ticker and save the integrated report
        
        Args:
            ticker: Stock ticker symbol
            data_dir: Path to the data directory
            output_dir: Directory to save the report. If None, saves in data/output/{timestamp}/analyst/price
            output_base_dir: Base output directory where price_image reports are stored
            
        Returns:
            Path to the saved report file
        """
        print(f"\n{'='*60}")
        print(f"Integrated Price Analysis for {ticker}")
        print(f"{'='*60}\n")
        
        # Perform analysis
        report = self.analyze(ticker, data_dir, output_base_dir)
        
        # Determine output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_dir is None:
            # Save in data/output/{timestamp}/analyst/price/
            base_path = Path(data_dir).parent
            if base_path.name == 'raw':
                base_path = base_path.parent
            output_dir = base_path / "output" / timestamp / "analyst" / "price"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save report
        output_file = output_dir / f"{ticker}_integrated_price_analysis_{timestamp}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Integrated Price Analysis Report: {ticker}\n")
            f.write(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n")
            f.write(f"Analysis Type: Chart Analysis + Technical Indicators\n\n")
            f.write("---\n\n")
            f.write(report)
        
        print(f"\n{'='*60}")
        print(f"✓ Report saved to: {output_file}")
        print(f"{'='*60}\n")
        
        return str(output_file)


def main():
    """Example usage of the Price Analyst"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Perform integrated price analysis for a stock ticker')
    parser.add_argument('ticker', type=str, help='Stock ticker symbol (e.g., GOOGL)')
    parser.add_argument('--data-dir', type=str, required=True, help='Path to data directory')
    parser.add_argument('--api-key', type=str, help='OpenRouter API key (or set OPENROUTER_API_KEY env var)')
    parser.add_argument('--output-dir', type=str, help='Directory to save report (default: auto-generated)')
    parser.add_argument('--output-base-dir', type=str, help='Base directory where price_image reports are stored')
    
    args = parser.parse_args()
    
    # Initialize analyst
    analyst = PriceAnalyst(api_key=args.api_key)
    
    # Analyze and save report
    report_path = analyst.analyze_and_save(
        ticker=args.ticker,
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        output_base_dir=args.output_base_dir
    )
    
    print(f"\n✓ Integrated analysis complete!")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()

