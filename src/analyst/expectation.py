"""
Street Expectations & Revisions Analyst

This module analyzes street expectations and analyst revisions including:
- Updowngrade History (Previous 15 updowngrade events)
- Revenue Estimates (by quarter and year)
- Earning Estimates (by quarter and year)
- EPS Estimate History (by quarter)
- Growth Estimates
"""

import os
import json
import pandas as pd
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any


class ExpectationAnalyst:
    """Analyzes street expectations and analyst revision data using AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Expectation Analyst
        
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
        Load all street expectation data for a given ticker
        
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
        
        # Load Updowngrade History
        updowngrade_path = ticker_path / "yfinance_Updowngrade.csv"
        if updowngrade_path.exists():
            df = pd.read_csv(updowngrade_path)
            data['updowngrade'] = df.to_dict(orient='records')
        
        # Load Revenue Estimate
        revenue_estimate_path = ticker_path / "yfinance_RevenueEstimate.csv"
        if revenue_estimate_path.exists():
            df = pd.read_csv(revenue_estimate_path, index_col=0)
            data['revenue_estimate'] = df.to_dict()
        
        # Load Earning Estimate
        earning_estimate_path = ticker_path / "yfinance_EarningEstimate.csv"
        if earning_estimate_path.exists():
            df = pd.read_csv(earning_estimate_path, index_col=0)
            data['earning_estimate'] = df.to_dict()
        
        # Load EPS Estimate History
        eps_estimate_path = ticker_path / "yfinance_EPSEestimateHistory.csv"
        if eps_estimate_path.exists():
            df = pd.read_csv(eps_estimate_path, index_col=0)
            data['eps_estimate_history'] = df.to_dict()
        
        # Load Growth Estimate
        growth_estimate_path = ticker_path / "yfinance_GrowthEstimate.csv"
        if growth_estimate_path.exists():
            df = pd.read_csv(growth_estimate_path, index_col=0)
            data['growth_estimate'] = df.to_dict()
        
        return data
    
    def format_data_for_prompt(self, data: Dict[str, Any]) -> str:
        """
        Format loaded data into a readable string for the AI prompt
        
        Args:
            data: Dictionary containing all loaded expectation data
            
        Returns:
            Formatted string representation of the data
        """
        sections = []
        ticker = data['ticker']
        
        sections.append(f"# Street Expectations & Revisions Data for {ticker}\n")
        
        # Updowngrade History
        if 'updowngrade' in data:
            sections.append("## Analyst Upgrade/Downgrade History")
            sections.append("Recent analyst rating changes (most recent 15 events):\n")
            df = pd.DataFrame(data['updowngrade'])
            sections.append(df.to_string(index=False))
            sections.append("")
        
        # Revenue Estimate
        if 'revenue_estimate' in data:
            sections.append("## Revenue Estimates")
            sections.append("Analyst estimates for revenue by quarter and year:\n")
            df = pd.DataFrame(data['revenue_estimate'])
            sections.append(df.to_string())
            sections.append("")
        
        # Earning Estimate
        if 'earning_estimate' in data:
            sections.append("## Earnings Estimates")
            sections.append("Analyst estimates for earnings by quarter and year:\n")
            df = pd.DataFrame(data['earning_estimate'])
            sections.append(df.to_string())
            sections.append("")
        
        # EPS Estimate History
        if 'eps_estimate_history' in data:
            sections.append("## EPS Estimate History")
            sections.append("Historical EPS estimate revisions by quarter:\n")
            df = pd.DataFrame(data['eps_estimate_history'])
            sections.append(df.to_string())
            sections.append("")
        
        # Growth Estimate
        if 'growth_estimate' in data:
            sections.append("## Growth Estimates")
            sections.append("Analyst estimates for company growth:\n")
            df = pd.DataFrame(data['growth_estimate'])
            sections.append(df.to_string())
            sections.append("")
        
        return "\n".join(sections)
    
    def analyze(self, ticker: str, data_dir: str) -> str:
        """
        Perform street expectation analysis on a given ticker
        
        Args:
            ticker: Stock ticker symbol
            data_dir: Path to the data directory
            
        Returns:
            Comprehensive analysis report
        """
        # Load data
        print(f"Loading street expectation data for {ticker}...")
        data = self.load_data(ticker, data_dir)
        
        # Format data for prompt
        formatted_data = self.format_data_for_prompt(data)
        
        # Prepare the prompt
        current_date = datetime.now().strftime("%B %d, %Y")
        
        system_message = (
            "You are a financial analyst specializing in analyzing street expectations and analyst revisions for stocks. "
            "Your task is to provide comprehensive analysis of analyst ratings, estimates, and revisions to help traders "
            "understand the consensus view and any recent changes in sentiment. Focus on identifying trends in analyst "
            "upgrades/downgrades, estimate revisions, and growth expectations. Provide detailed insights that go beyond "
            "simply stating 'mixed signals' - identify specific patterns, notable changes, and what they might indicate "
            "about the company's prospects. Make sure to include as much detail as possible and append a Markdown table "
            "at the end to organize key points in an easy-to-read format."
        )
        
        user_message = (
            f"Current Date: {current_date}\n"
            f"Company Ticker: {ticker}\n\n"
            f"Please analyze the following street expectation and analyst revision data:\n\n"
            f"{formatted_data}\n\n"
            f"Provide a comprehensive street expectations analysis report that includes:\n"
            f"1. Analyst Rating Trends (upgrades/downgrades analysis)\n"
            f"2. Revenue Estimate Analysis (trends and consensus)\n"
            f"3. Earnings Estimate Analysis (EPS trends and revisions)\n"
            f"4. Growth Expectations (short-term and long-term)\n"
            f"5. Analyst Sentiment Changes (recent shifts in outlook)\n"
            f"6. Estimate Revision Trends (positive or negative momentum)\n"
            f"7. Key Takeaways for Traders\n"
            f"8. Summary table with key metrics and insights\n"
        )
        
        # Call OpenRouter API
        print(f"Analyzing {ticker} street expectations using AI...")
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
            output_dir: Directory to save the report. If None, saves in data/output/{timestamp}/analyst/expectation
            
        Returns:
            Path to the saved report file
        """
        # Perform analysis
        report = self.analyze(ticker, data_dir)
        
        # Determine output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_dir is None:
            # Save in data/output/{timestamp}/analyst/expectation/
            base_path = Path(data_dir).parent  # Go up from ticker folder to data/raw parent
            if base_path.name == 'raw':
                base_path = base_path.parent  # Go up one more level to data/
            output_dir = base_path / "output" / timestamp / "analyst" / "expectation"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save report
        output_file = output_dir / f"{ticker}_expectation_analysis_{timestamp}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Street Expectations & Revisions Analysis Report: {ticker}\n")
            f.write(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n")
            f.write("---\n\n")
            f.write(report)
        
        print(f"Report saved to: {output_file}")
        return str(output_file)


def main():
    """Example usage of the Expectation Analyst"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze street expectations and revisions for a stock ticker')
    parser.add_argument('ticker', type=str, help='Stock ticker symbol (e.g., AAPL)')
    parser.add_argument('--data-dir', type=str, required=True, help='Path to data directory')
    parser.add_argument('--api-key', type=str, help='OpenRouter API key (or set OPENROUTER_API_KEY env var)')
    parser.add_argument('--output-dir', type=str, help='Directory to save report (default: ticker data directory)')
    
    args = parser.parse_args()
    
    # Initialize analyst
    analyst = ExpectationAnalyst(api_key=args.api_key)
    
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

