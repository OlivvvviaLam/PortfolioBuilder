"""
Options Chain Analyst

This module analyzes options data including:
- Call Options Chain
- Put Options Chain
- Implied Volatility Analysis
- Open Interest and Volume Analysis
- Put/Call Ratios
"""

import os
import json
import pandas as pd
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any


class OptionAnalyst:
    """Analyzes options chain data using AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Option Analyst
        
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
        Load all options data for a given ticker
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            data_dir: Path to the data directory containing ticker folders
            
        Returns:
            Dictionary containing all loaded options data
        """
        ticker_path = Path(data_dir) / ticker
        
        if not ticker_path.exists():
            raise ValueError(f"Data directory for {ticker} not found at {ticker_path}")
        
        data = {
            'ticker': ticker,
            'data_path': str(ticker_path),
            'expiries': {}
        }
        
        # Find all Finviz option chain files
        call_files = sorted(ticker_path.glob("finviz_OptionChainCall_*.csv"))
        put_files = sorted(ticker_path.glob("finviz_OptionChainPut_*.csv"))
        
        # Extract expiry dates from filenames
        expiries = set()
        for f in call_files:
            # Extract date from filename like finviz_OptionChainCall_2026-01-09.csv
            expiry = f.stem.replace("finviz_OptionChainCall_", "")
            expiries.add(expiry)
        
        # Load options for each expiry
        for expiry in sorted(expiries):
            call_path = ticker_path / f"finviz_OptionChainCall_{expiry}.csv"
            put_path = ticker_path / f"finviz_OptionChainPut_{expiry}.csv"
            
            expiry_data = {'expiry': expiry}
            
            # Load call options
            if call_path.exists():
                df = pd.read_csv(call_path)
                # Normalize column names (Finviz uses different naming)
                df = self._normalize_columns(df)
                expiry_data['call_options_df'] = df
                expiry_data['call_options'] = df.to_dict('records')
            
            # Load put options
            if put_path.exists():
                df = pd.read_csv(put_path)
                # Normalize column names
                df = self._normalize_columns(df)
                expiry_data['put_options_df'] = df
                expiry_data['put_options'] = df.to_dict('records')
            
            data['expiries'][expiry] = expiry_data
        
        # If no Finviz data found, try legacy yfinance format
        if not data['expiries']:
            call_options_path = ticker_path / "yfinance_OptionChainCall.csv"
            put_options_path = ticker_path / "yfinance_OptionChainPut.csv"
            
            if call_options_path.exists() or put_options_path.exists():
                expiry_data = {'expiry': 'unknown'}
                
                if call_options_path.exists():
                    df = pd.read_csv(call_options_path, index_col=0)
                    df = self._normalize_columns(df)
                    expiry_data['call_options_df'] = df
                    expiry_data['call_options'] = df.to_dict('records')
                
                if put_options_path.exists():
                    df = pd.read_csv(put_options_path, index_col=0)
                    df = self._normalize_columns(df)
                    expiry_data['put_options_df'] = df
                    expiry_data['put_options'] = df.to_dict('records')
                
                data['expiries']['unknown'] = expiry_data
        
        # Load Ticker Info for current price context
        ticker_info_path = ticker_path / "yfinance_TickerInfo.json"
        if ticker_info_path.exists():
            with open(ticker_info_path, 'r') as f:
                ticker_info = json.load(f)
                data['current_price'] = ticker_info.get('currentPrice', ticker_info.get('regularMarketPrice', 'N/A'))
        
        return data
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize column names from different data sources
        
        Args:
            df: DataFrame with option chain data
            
        Returns:
            DataFrame with normalized column names
        """
        # Mapping from various formats to standardized names
        column_mapping = {
            'Strike': 'strike',
            'OpenInt': 'openInterest',
            'IV': 'impliedVolatility',
            'Bid': 'bid',
            'Ask': 'ask',
            'Last': 'last',
            'Change': 'change',
            'Delta': 'delta',
            'Gamma': 'gamma',
            'Theta': 'theta',
            'Vega': 'vega',
            'Rho': 'rho'
        }
        
        # Rename columns if they exist
        df = df.rename(columns=column_mapping)
        
        return df
    
    def calculate_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate key options metrics for all expiries
        
        Args:
            data: Dictionary containing loaded options data
            
        Returns:
            Dictionary of calculated metrics by expiry
        """
        all_metrics = {}
        
        if 'expiries' in data:
            for expiry, expiry_data in data['expiries'].items():
                metrics = {'expiry': expiry}
                
                if 'call_options_df' in expiry_data and 'put_options_df' in expiry_data:
                    call_df = expiry_data['call_options_df']
                    put_df = expiry_data['put_options_df']
                    
                    # Total open interest
                    metrics['total_call_oi'] = call_df['openInterest'].sum()
                    metrics['total_put_oi'] = put_df['openInterest'].sum()
                    
                    # Put/Call ratios
                    if metrics['total_call_oi'] > 0:
                        metrics['put_call_oi_ratio'] = metrics['total_put_oi'] / metrics['total_call_oi']
                    
                    # Max open interest strikes
                    if len(call_df[call_df['openInterest'] > 0]) > 0:
                        metrics['max_call_oi_strike'] = call_df.loc[call_df['openInterest'].idxmax(), 'strike']
                    if len(put_df[put_df['openInterest'] > 0]) > 0:
                        metrics['max_put_oi_strike'] = put_df.loc[put_df['openInterest'].idxmax(), 'strike']
                    
                    # Implied volatility stats
                    call_iv_valid = call_df[call_df['impliedVolatility'] > 0.01]['impliedVolatility']
                    put_iv_valid = put_df[put_df['impliedVolatility'] > 0.01]['impliedVolatility']
                    
                    if len(call_iv_valid) > 0:
                        metrics['avg_call_iv'] = call_iv_valid.mean()
                    if len(put_iv_valid) > 0:
                        metrics['avg_put_iv'] = put_iv_valid.mean()
                    
                    # Max pain calculation (simplified - strike with max total OI)
                    call_oi_by_strike = call_df.groupby('strike')['openInterest'].sum()
                    put_oi_by_strike = put_df.groupby('strike')['openInterest'].sum()
                    total_oi_by_strike = call_oi_by_strike.add(put_oi_by_strike, fill_value=0)
                    if len(total_oi_by_strike) > 0:
                        metrics['max_pain_strike'] = total_oi_by_strike.idxmax()
                
                all_metrics[expiry] = metrics
        
        return all_metrics
    
    def format_data_for_prompt(self, data: Dict[str, Any]) -> str:
        """
        Format loaded options data into a readable string for the AI prompt
        
        Args:
            data: Dictionary containing all loaded options data
            
        Returns:
            Formatted string representation of the data
        """
        sections = []
        ticker = data['ticker']
        
        sections.append(f"# Options Chain Analysis Data for {ticker}\n")
        
        # Current Price Context
        if 'current_price' in data:
            sections.append(f"**Current Stock Price:** ${data['current_price']}\n")
        
        # Calculate and display metrics for all expiries
        all_metrics = self.calculate_metrics(data)
        
        # Display data for each expiry
        if 'expiries' in data:
            sections.append(f"**Available Expiries:** {len(data['expiries'])}")
            sections.append(f"**Expiry Dates:** {', '.join(sorted(data['expiries'].keys()))}\n")
            
            for expiry in sorted(data['expiries'].keys()):
                expiry_data = data['expiries'][expiry]
                metrics = all_metrics.get(expiry, {})
                
                sections.append("=" * 80)
                sections.append(f"## Expiry: {expiry}")
                sections.append("=" * 80)
                sections.append("")
                
                # Options Flow Metrics Summary for this expiry
                sections.append("### Options Flow Metrics Summary")

                if 'total_call_oi' in metrics:
                    sections.append(f"\n**Total Call Open Interest:** {metrics['total_call_oi']:,.0f}")
                    sections.append(f"**Total Put Open Interest:** {metrics['total_put_oi']:,.0f}")
                if 'put_call_oi_ratio' in metrics:
                    sections.append(f"**Put/Call OI Ratio:** {metrics['put_call_oi_ratio']:.3f}")
                
                if 'max_pain_strike' in metrics:
                    sections.append(f"\n**Estimated Max Pain Strike:** ${metrics['max_pain_strike']:.2f}")
                
                if 'avg_call_iv' in metrics:
                    sections.append(f"\n**Average Call IV:** {metrics['avg_call_iv']:.2%}")
                if 'avg_put_iv' in metrics:
                    sections.append(f"**Average Put IV:** {metrics['avg_put_iv']:.2%}")
                
                sections.append("")
                
                # Call Options Chain
                if 'call_options_df' in expiry_data:
                    sections.append("### Call Options Chain")
                    call_df = expiry_data['call_options_df']
                    
                    # Show strikes with significant activity
                    significant_calls = call_df[(call_df['openInterest'] > 0)].copy()
                    
                    if len(significant_calls) > 0:
                        sections.append(f"**Total Strikes with Activity:** {len(significant_calls)}\n")
                        sections.append("**Strikes with Significant Activity (OI > 0):**")
                        sections.append(significant_calls.to_string())
                    else:
                        sections.append("No significant activity found in call options.")
                    
                    sections.append("")
                
                # Put Options Chain
                if 'put_options_df' in expiry_data:
                    sections.append("### Put Options Chain")
                    put_df = expiry_data['put_options_df']
                    
                    # Show strikes with significant activity
                    significant_puts = put_df[(put_df['openInterest'] > 0)].copy()
                    
                    if len(significant_puts) > 0:
                        sections.append(f"**Total Strikes with Activity:** {len(significant_puts)}\n")
                        sections.append("**Strikes with Significant Activity (OI > 0):**")
                        sections.append(significant_puts.to_string())
                    else:
                        sections.append("No significant activity found in put options.")
                    
                    sections.append("")
                
                # Key Strikes Analysis
                if metrics:
                    sections.append("### Key Strike Levels")
                    if 'max_call_oi_strike' in metrics:
                        sections.append(f"**Highest Call Open Interest Strike:** ${metrics['max_call_oi_strike']:.2f}")
                    if 'max_put_oi_strike' in metrics:
                        sections.append(f"**Highest Put Open Interest Strike:** ${metrics['max_put_oi_strike']:.2f}")
                    sections.append("")
        
        return "\n".join(sections)
    
    def analyze(self, ticker: str, data_dir: str) -> str:
        """
        Perform options chain analysis on a given ticker
        
        Args:
            ticker: Stock ticker symbol
            data_dir: Path to the data directory
            
        Returns:
            Comprehensive options analysis report
        """
        # Load data
        print(f"Loading options data for {ticker}...")
        data = self.load_data(ticker, data_dir)
        
        # Format data for prompt
        formatted_data = self.format_data_for_prompt(data)
        
        # Prepare the prompt
        current_date = datetime.now().strftime("%B %d, %Y")
        
        system_message = (
            "You are a financial analyst specializing in options trading and derivatives analysis. "
            "Your task is to analyze options chain data to identify market sentiment, key support/resistance levels, "
            "unusual options activity, and potential trading opportunities. Provide detailed analysis with actionable insights. "
            "Consider implied volatility patterns, put/call ratios, open interest concentrations, and volume patterns. "
            "Identify potential hedging activity, directional bets, and market maker positioning. "
            "Do not simply describe the data - provide deep analysis of implications for price action and trader positioning. "
            "Make sure to append a Markdown table at the end summarizing key findings, strike levels, and sentiment indicators."
        )
        
        user_message = (
            f"Current Date: {current_date}\n"
            f"Company Ticker: {ticker}\n\n"
            f"Please analyze the following options chain data for MULTIPLE EXPIRY DATES:\n\n"
            f"{formatted_data}\n\n"
            f"Provide a comprehensive options analysis report that includes:\n"
            f"1. Options Flow Overview (volume, open interest, put/call ratios for each expiry)\n"
            f"2. Market Sentiment Analysis (bullish/bearish signals from options activity across expiries)\n"
            f"3. Key Strike Levels Analysis (support/resistance, max pain for each expiry)\n"
            f"4. Implied Volatility Analysis (IV patterns and term structure across expiries)\n"
            f"5. Unusual Options Activity (significant positions, large orders by expiry)\n"
            f"6. Institutional Positioning Insights (hedging vs. directional bets, calendar spreads)\n"
            f"7. Term Structure Analysis (how sentiment differs between near-term and longer-term expiries)\n"
            f"8. Potential Price Targets and Key Levels to Watch\n"
            f"9. Trading Implications and Strategy Considerations (including multi-leg strategies)\n"
            f"10. Summary table with key metrics, strike levels, and sentiment signals for each expiry\n"
        )
        
        # Call OpenRouter API
        print(f"Analyzing options for {ticker} using AI...")
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
        Analyze ticker options and save the report to a file
        
        Args:
            ticker: Stock ticker symbol
            data_dir: Path to the data directory
            output_dir: Directory to save the report. If None, saves in data/output/{timestamp}/analyst/option
            
        Returns:
            Path to the saved report file
        """
        # Perform analysis
        report = self.analyze(ticker, data_dir)
        
        # Determine output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_dir is None:
            # Save in data/output/{timestamp}/analyst/option/
            base_path = Path(data_dir).parent  # Go up from ticker folder to data/raw parent
            if base_path.name == 'raw':
                base_path = base_path.parent  # Go up one more level to data/
            output_dir = base_path / "output" / timestamp / "analyst" / "option"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save report
        output_file = output_dir / f"{ticker}_option_analysis_{timestamp}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Options Chain Analysis Report: {ticker}\n")
            f.write(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n")
            f.write("---\n\n")
            f.write(report)
        
        print(f"Report saved to: {output_file}")
        return str(output_file)


def main():
    """Example usage of the Option Analyst"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze options chain data for a stock ticker')
    parser.add_argument('ticker', type=str, help='Stock ticker symbol (e.g., AAPL)')
    parser.add_argument('--data-dir', type=str, required=True, help='Path to data directory')
    parser.add_argument('--api-key', type=str, help='OpenRouter API key (or set OPENROUTER_API_KEY env var)')
    parser.add_argument('--output-dir', type=str, help='Directory to save report (default: data/output/{timestamp}/analyst/option)')
    
    args = parser.parse_args()
    
    # Initialize analyst
    analyst = OptionAnalyst(api_key=args.api_key)
    
    # Analyze and save report
    report_path = analyst.analyze_and_save(
        ticker=args.ticker,
        data_dir=args.data_dir,
        output_dir=args.output_dir
    )
    
    print(f"\n✓ Options analysis complete!")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()

