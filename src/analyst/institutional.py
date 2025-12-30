"""
Institutional & Insider Activity Analyst

This module analyzes ownership and insider trading data including:
- Holding Breakdown (composition of holdings)
- Major Institutional Holders
- Major Mutual Fund Holders
- Insider Purchase Activity
"""

import os
import json
import pandas as pd
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any


class InstitutionalAnalyst:
    """Analyzes institutional ownership and insider trading data using AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Institutional Analyst
        
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
        Load all institutional and insider data for a given ticker
        
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
        
        # Load Holding Breakdown
        holding_breakdown_path = ticker_path / "yfinance_HoldingBreakdown.csv"
        if holding_breakdown_path.exists():
            df = pd.read_csv(holding_breakdown_path, index_col=0)
            data['holding_breakdown'] = df.to_dict()
        
        # Load Major Institutional Holders
        institutional_holders_path = ticker_path / "yfinance_MajorInstitutionalHolders.csv"
        if institutional_holders_path.exists():
            df = pd.read_csv(institutional_holders_path)
            data['institutional_holders'] = df.to_dict('records')
        
        # Load Major Mutual Fund Holders
        mutual_fund_holders_path = ticker_path / "yfinance_MajorMutualFundHolders.csv"
        if mutual_fund_holders_path.exists():
            df = pd.read_csv(mutual_fund_holders_path)
            data['mutual_fund_holders'] = df.to_dict('records')
        
        # Load Insider Purchase Activity
        insider_purchase_path = ticker_path / "yfinance_InsiderPurchase.csv"
        if insider_purchase_path.exists():
            df = pd.read_csv(insider_purchase_path)
            data['insider_purchases'] = df.to_dict('records')
        
        return data
    
    def format_data_for_prompt(self, data: Dict[str, Any]) -> str:
        """
        Format loaded data into a readable string for the AI prompt
        
        Args:
            data: Dictionary containing all loaded institutional data
            
        Returns:
            Formatted string representation of the data
        """
        sections = []
        ticker = data['ticker']
        
        sections.append(f"# Institutional & Insider Activity Data for {ticker}\n")
        
        # Holding Breakdown
        if 'holding_breakdown' in data:
            sections.append("## Holding Breakdown")
            sections.append("*Composition of holdings by category*\n")
            df = pd.DataFrame(data['holding_breakdown'])
            sections.append(df.to_string())
            sections.append("")
        
        # Major Institutional Holders
        if 'institutional_holders' in data:
            sections.append("## Major Institutional Holders")
            sections.append("*Top institutional investors and their holdings*\n")
            df = pd.DataFrame(data['institutional_holders'])
            if not df.empty:
                sections.append(df.to_string(index=False))
            else:
                sections.append("No institutional holder data available.")
            sections.append("")
        
        # Major Mutual Fund Holders
        if 'mutual_fund_holders' in data:
            sections.append("## Major Mutual Fund Holders")
            sections.append("*Top mutual funds holding this stock*\n")
            df = pd.DataFrame(data['mutual_fund_holders'])
            if not df.empty:
                sections.append(df.to_string(index=False))
            else:
                sections.append("No mutual fund holder data available.")
            sections.append("")
        
        # Insider Purchase Activity
        if 'insider_purchases' in data:
            sections.append("## Insider Purchase Activity")
            sections.append("*Recent insider buying and selling transactions*\n")
            df = pd.DataFrame(data['insider_purchases'])
            if not df.empty:
                sections.append(df.to_string(index=False))
            else:
                sections.append("No insider purchase data available.")
            sections.append("")
        
        return "\n".join(sections)
    
    def analyze(self, ticker: str, data_dir: str) -> str:
        """
        Perform institutional and insider activity analysis on a given ticker
        
        Args:
            ticker: Stock ticker symbol
            data_dir: Path to the data directory
            
        Returns:
            Comprehensive analysis report
        """
        # Load data
        print(f"Loading institutional data for {ticker}...")
        data = self.load_data(ticker, data_dir)
        
        # Format data for prompt
        formatted_data = self.format_data_for_prompt(data)
        
        # Prepare the prompt
        current_date = datetime.now().strftime("%B %d, %Y")
        
        system_message = (
            "You are a financial analyst specializing in institutional ownership and insider trading analysis. "
            "Your task is to analyze institutional holdings, mutual fund positions, and insider trading activity "
            "to provide insights into smart money movements and potential market signals. "
            "Provide detailed analysis of ownership concentration, institutional sentiment, and insider confidence. "
            "Do not simply state that the trends are mixed, provide detailed and fine-grained analysis and insights "
            "that may help traders understand institutional behavior and insider sentiment. "
            "Make sure to append a Markdown table at the end of the report to organize key points in the report, "
            "organized and easy to read."
        )
        
        user_message = (
            f"Current Date: {current_date}\n"
            f"Company Ticker: {ticker}\n\n"
            f"Please analyze the following institutional and insider activity data:\n\n"
            f"{formatted_data}\n\n"
            f"Provide a comprehensive institutional analysis report that includes:\n"
            f"1. Ownership Structure Overview (from Holding Breakdown)\n"
            f"2. Major Institutional Holders Analysis\n"
            f"   - Who are the largest institutional investors?\n"
            f"   - What percentage of shares do they control?\n"
            f"   - Are there any notable changes in positions?\n"
            f"3. Mutual Fund Holdings Analysis\n"
            f"   - Which mutual funds have significant positions?\n"
            f"   - What does this tell us about the stock's appeal to retail-focused funds?\n"
            f"4. Insider Trading Activity Analysis\n"
            f"   - Recent insider purchases and sales\n"
            f"   - Insider sentiment (bullish/bearish signals)\n"
            f"   - Significance of insider transactions\n"
            f"5. Institutional Ownership Concentration\n"
            f"   - Is ownership concentrated or diversified?\n"
            f"   - Implications for stock volatility and liquidity\n"
            f"6. Smart Money Signals\n"
            f"   - What do institutional moves suggest about future prospects?\n"
            f"   - Alignment or divergence between institutions and insiders\n"
            f"7. Key Takeaways and Trading Implications\n"
            f"8. Summary table with key institutional metrics and insights\n"
        )
        
        # Call OpenRouter API
        print(f"Analyzing {ticker} institutional data using AI...")
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
            output_dir: Directory to save the report. If None, saves in data/output/{timestamp}/analyst/institutional
            
        Returns:
            Path to the saved report file
        """
        # Perform analysis
        report = self.analyze(ticker, data_dir)
        
        # Determine output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_dir is None:
            # Save in data/output/{timestamp}/analyst/institutional/
            base_path = Path(data_dir).parent  # Go up from ticker folder to data/raw parent
            if base_path.name == 'raw':
                base_path = base_path.parent  # Go up one more level to data/
            output_dir = base_path / "output" / timestamp / "analyst" / "institutional"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save report
        output_file = output_dir / f"{ticker}_institutional_analysis_{timestamp}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Institutional & Insider Activity Analysis Report: {ticker}\n")
            f.write(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n")
            f.write("---\n\n")
            f.write(report)
        
        print(f"Report saved to: {output_file}")
        return str(output_file)


def main():
    """Example usage of the Institutional Analyst"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze institutional and insider data for a stock ticker')
    parser.add_argument('ticker', type=str, help='Stock ticker symbol (e.g., AAPL)')
    parser.add_argument('--data-dir', type=str, required=True, help='Path to data directory')
    parser.add_argument('--api-key', type=str, help='OpenRouter API key (or set OPENROUTER_API_KEY env var)')
    parser.add_argument('--output-dir', type=str, help='Directory to save report (default: ticker data directory)')
    
    args = parser.parse_args()
    
    # Initialize analyst
    analyst = InstitutionalAnalyst(api_key=args.api_key)
    
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

