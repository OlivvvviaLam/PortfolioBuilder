"""
Fundamental and Financial Statement Analyst

This module analyzes financial data including:
- Key Financial Statistics (finviz & yfinance)
- Ticker Information (Business Summary, Sector, Industry)
- Historical Statistics (P/E, P/B, etc.)
- Financial Reports (Balance Sheet, Income Statement, Cash Flow)
"""

import os
import json
import pandas as pd
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any


class FundamentalAnalyst:
    """Analyzes fundamental and financial statement data using AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Fundamental Analyst
        
        Args:
            api_key: OpenRouter API key. If None, will try to get from environment variable OPENROUTER_API_KEY
        """
        self.api_key = api_key or os.environ.get('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OpenRouter API key must be provided or set in OPENROUTER_API_KEY environment variable")
        
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "xiaomi/mimo-v2-flash:free"
        
    def load_data(self, ticker: str, data_dir: str) -> Dict[str, Any]:
        """
        Load all fundamental data for a given ticker
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            data_dir: Path to the data directory containing ticker folders
            
        Returns:
            Dictionary containing all loaded data
        """
        ticker_path = Path(data_dir) / ticker
        
        if not ticker_path.exists():
            raise ValueError(f"Data directory for {ticker} not found at {ticker_path}")
        
        data = {
            'ticker': ticker,
            'data_path': str(ticker_path)
        }
        
        # Load Finviz Key Financial Stats
        finviz_stats_path = ticker_path / "finviz_KeyFinanceStat_finviz.csv"
        if finviz_stats_path.exists():
            df = pd.read_csv(finviz_stats_path, index_col=0)
            data['finviz_key_stats'] = df.to_dict()
        
        # Load Ticker Info (Business Summary, Sector, Industry)
        ticker_info_path = ticker_path / "yfinance_TickerInfo.json"
        if ticker_info_path.exists():
            with open(ticker_info_path, 'r') as f:
                data['ticker_info'] = json.load(f)
        
        # Load yfinance Key Financial Stats
        yf_stats_path = ticker_path / "yfinance_KeyFinanceStat_yfiance.csv"
        if yf_stats_path.exists():
            df = pd.read_csv(yf_stats_path, index_col=0)
            data['yfinance_key_stats'] = df.to_dict()
        
        # Load Historical Statistics
        hist_stats_path = ticker_path / "yfinance_HistoricalStat.csv"
        if hist_stats_path.exists():
            df = pd.read_csv(hist_stats_path, index_col=0)
            data['historical_stats'] = df.to_dict()
        
        # Load Financial Reports
        balance_sheet_path = ticker_path / "yfinance_FinancialReport_Balance_Sheet.csv"
        if balance_sheet_path.exists():
            df = pd.read_csv(balance_sheet_path, index_col=0)
            data['balance_sheet'] = df.to_dict()
        
        income_statement_path = ticker_path / "yfinance_FinancialReport_Income_Statement.csv"
        if income_statement_path.exists():
            df = pd.read_csv(income_statement_path, index_col=0)
            data['income_statement'] = df.to_dict()
        
        cash_flow_path = ticker_path / "yfinance_FinancialReport_Cash_Flow.csv"
        if cash_flow_path.exists():
            df = pd.read_csv(cash_flow_path, index_col=0)
            data['cash_flow'] = df.to_dict()
        
        return data
    
    def format_data_for_prompt(self, data: Dict[str, Any]) -> str:
        """
        Format loaded data into a readable string for the AI prompt
        
        Args:
            data: Dictionary containing all loaded financial data
            
        Returns:
            Formatted string representation of the data
        """
        sections = []
        ticker = data['ticker']
        
        sections.append(f"# Fundamental Analysis Data for {ticker}\n")
        
        # Company Information
        if 'ticker_info' in data:
            sections.append("## Company Information")
            info = data['ticker_info']
            sections.append(f"**Sector:** {info.get('sector', 'N/A')}")
            sections.append(f"**Industry:** {info.get('industry', 'N/A')}")
            sections.append(f"\n**Business Summary:**\n{info.get('longBusinessSummary', 'N/A')}\n")
        
        # Key Financial Statistics from Finviz
        if 'finviz_key_stats' in data:
            sections.append("## Key Financial Statistics (Finviz)")
            df = pd.DataFrame(data['finviz_key_stats'])
            sections.append(df.to_string())
            sections.append("")
        
        # Key Financial Statistics from yfinance
        if 'yfinance_key_stats' in data:
            sections.append("## Key Financial Statistics (Yahoo Finance)")
            df = pd.DataFrame(data['yfinance_key_stats'])
            sections.append(df.to_string())
            sections.append("")
        
        # Historical Statistics
        if 'historical_stats' in data:
            sections.append("## Historical Valuation Metrics")
            df = pd.DataFrame(data['historical_stats'])
            sections.append(df.to_string())
            sections.append("")
        
        # Balance Sheet
        if 'balance_sheet' in data:
            sections.append("## Balance Sheet (Annual)")
            df = pd.DataFrame(data['balance_sheet'])
            # Show only the most recent 3 years for brevity
            if len(df.columns) > 3:
                df = df.iloc[:, :3]
            sections.append(df.to_string())
            sections.append("")
        
        # Income Statement
        if 'income_statement' in data:
            sections.append("## Income Statement (Annual)")
            df = pd.DataFrame(data['income_statement'])
            # Show only the most recent 3 years for brevity
            if len(df.columns) > 3:
                df = df.iloc[:, :3]
            sections.append(df.to_string())
            sections.append("")
        
        # Cash Flow Statement
        if 'cash_flow' in data:
            sections.append("## Cash Flow Statement (Annual)")
            df = pd.DataFrame(data['cash_flow'])
            # Show only the most recent 3 years for brevity
            if len(df.columns) > 3:
                df = df.iloc[:, :3]
            sections.append(df.to_string())
            sections.append("")
        
        return "\n".join(sections)
    
    def analyze(self, ticker: str, data_dir: str) -> str:
        """
        Perform fundamental analysis on a given ticker
        
        Args:
            ticker: Stock ticker symbol
            data_dir: Path to the data directory
            
        Returns:
            Comprehensive analysis report
        """
        # Load data
        print(f"Loading data for {ticker}...")
        data = self.load_data(ticker, data_dir)
        
        # Format data for prompt
        formatted_data = self.format_data_for_prompt(data)
        
        # Prepare the prompt
        current_date = datetime.now().strftime("%B %d, %Y")
        
        system_message = (
            "You are a researcher tasked with analyzing fundamental information over the past week about a company. "
            "Please write a comprehensive report of the company's fundamental information such as financial documents, "
            "company profile, basic company financials, and company financial history to gain a full view of the company's "
            "fundamental information to inform traders. Make sure to include as much detail as possible. "
            "Do not simply state the trends are mixed, provide detailed and fine-grained analysis and insights that may help traders make decisions. "
            "Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."
        )
        
        user_message = (
            f"Current Date: {current_date}\n"
            f"Company Ticker: {ticker}\n\n"
            f"Please analyze the following fundamental and financial data:\n\n"
            f"{formatted_data}\n\n"
            f"Provide a comprehensive fundamental analysis report that includes:\n"
            f"1. Company Overview and Business Model\n"
            f"2. Financial Health Analysis (Balance Sheet)\n"
            f"3. Profitability Analysis (Income Statement)\n"
            f"4. Cash Flow Analysis\n"
            f"5. Valuation Metrics and Trends\n"
            f"6. Key Strengths and Weaknesses\n"
            f"7. Investment Considerations\n"
            f"8. Summary table with key metrics and insights\n"
        )
        
        # Call OpenRouter API
        print(f"Analyzing {ticker} using AI...")
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
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            analysis_report = result['choices'][0]['message']['content']
            
            return analysis_report
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling OpenRouter API: {str(e)}")
    
    def analyze_and_save(self, ticker: str, data_dir: str, output_dir: Optional[str] = None) -> str:
        """
        Analyze a ticker and save the report to a file
        
        Args:
            ticker: Stock ticker symbol
            data_dir: Path to the data directory
            output_dir: Directory to save the report. If None, saves in data/output/{timestamp}/analyst/fundamental
            
        Returns:
            Path to the saved report file
        """
        # Perform analysis
        report = self.analyze(ticker, data_dir)
        
        # Determine output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_dir is None:
            # Save in data/output/{timestamp}/analyst/fundamental/
            base_path = Path(data_dir).parent  # Go up from ticker folder to data/raw parent
            if base_path.name == 'raw':
                base_path = base_path.parent  # Go up one more level to data/
            output_dir = base_path / "output" / timestamp / "analyst" / "fundamental"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save report
        output_file = output_dir / f"{ticker}_fundamental_analysis_{timestamp}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Fundamental Analysis Report: {ticker}\n")
            f.write(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n")
            f.write("---\n\n")
            f.write(report)
        
        print(f"Report saved to: {output_file}")
        return str(output_file)


def main():
    """Example usage of the Fundamental Analyst"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze fundamental data for a stock ticker')
    parser.add_argument('ticker', type=str, help='Stock ticker symbol (e.g., AAPL)')
    parser.add_argument('--data-dir', type=str, required=True, help='Path to data directory')
    parser.add_argument('--api-key', type=str, help='OpenRouter API key (or set OPENROUTER_API_KEY env var)')
    parser.add_argument('--output-dir', type=str, help='Directory to save report (default: ticker data directory)')
    
    args = parser.parse_args()
    
    # Initialize analyst
    analyst = FundamentalAnalyst(api_key=args.api_key)
    
    # Analyze and save report
    report_path = analyst.analyze_and_save(
        ticker=args.ticker,
        data_dir=args.data_dir,
        output_dir=args.output_dir
    )
    
    print(f"\n✓ Analysis complete!")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()

