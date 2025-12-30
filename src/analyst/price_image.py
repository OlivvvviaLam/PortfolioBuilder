"""
Price Chart Image Analyst

This module analyzes price chart images including:
- Daily and Weekly price charts
- 2-month daily technical indicator charts (momentum, price overlays, volume)
- 1-year weekly and 4-year monthly technical charts
"""

import os
import base64
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


class PriceImageAnalyst:
    """Analyzes price chart images using AI vision models"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Price Image Analyst
        
        Args:
            api_key: OpenRouter API key. If None, will try to get from environment variable OPENROUTER_API_KEY
        """
        self.api_key = api_key or os.environ.get('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OpenRouter API key must be provided or set in OPENROUTER_API_KEY environment variable")
        
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "google/gemini-3-flash-preview"
        
    def encode_image(self, image_path: str) -> str:
        """
        Encode an image file to base64
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded string of the image
        """
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def find_chart_images(self, ticker: str, data_dir: str) -> dict:
        """
        Find all chart images for a given ticker
        
        Args:
            ticker: Stock ticker symbol (e.g., 'GOOGL')
            data_dir: Path to the data directory containing ticker folders
            
        Returns:
            Dictionary containing paths to all chart images organized by type
        """
        ticker_path = Path(data_dir) / ticker
        
        if not ticker_path.exists():
            raise ValueError(f"Data directory for {ticker} not found at {ticker_path}")
        
        images = {
            'basic': [],
            'short_term': [],
            'long_term': []
        }
        
        # Basic charts (daily and weekly)
        daily_chart = ticker_path / f"{ticker}_daily.png"
        weekly_chart = ticker_path / f"{ticker}_weekly.png"
        
        if daily_chart.exists():
            images['basic'].append(str(daily_chart))
        if weekly_chart.exists():
            images['basic'].append(str(weekly_chart))
        
        # Short-term charts (2 months daily)
        short_term_patterns = [
            'yfinance_History2mo_d_momentum.png',
            'yfinance_History2mo_d_price_overlays.png',
            'yfinance_History2mo_d_volume.png'
        ]
        
        for pattern in short_term_patterns:
            chart_path = ticker_path / pattern
            if chart_path.exists():
                images['short_term'].append(str(chart_path))
        
        # Long-term charts (1 year weekly and 4 year monthly)
        long_term_patterns = [
            'yfinance_History1y_1wk_momentum.png',
            'yfinance_History1y_1wk_price_overlays.png',
            'yfinance_History1y_1wk_volume.png',
            'yfinance_History4y_1mo_momentum.png',
            'yfinance_History4y_1mo_price_overlays.png',
            'yfinance_History4y_1mo_volume.png'
        ]
        
        for pattern in long_term_patterns:
            chart_path = ticker_path / pattern
            if chart_path.exists():
                images['long_term'].append(str(chart_path))
        
        return images
    
    def analyze_images(self, image_paths: List[str], analysis_type: str, ticker: str) -> str:
        """
        Analyze a set of chart images
        
        Args:
            image_paths: List of paths to image files
            analysis_type: Type of analysis ('basic', 'short_term', 'long_term')
            ticker: Stock ticker symbol
            
        Returns:
            Analysis report from the AI
        """
        if not image_paths:
            return f"No images found for {analysis_type} analysis."
        
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Prepare system messages based on analysis type
        if analysis_type == 'basic':
            system_message = (
                "You are an expert technical analyst specializing in price chart analysis. "
                "Analyze the provided daily and weekly price charts to identify key price levels, "
                "trends, patterns, and potential support/resistance zones. "
                "Provide detailed insights that can help traders make informed decisions. "
                "Include a summary table at the end with key observations."
            )
            user_prompt = (
                f"Current Date: {current_date}\n"
                f"Company Ticker: {ticker}\n\n"
                f"Please analyze the following daily and weekly price charts:\n\n"
                f"Provide a comprehensive technical analysis including:\n"
                f"1. Overall trend direction (short-term and medium-term)\n"
                f"2. Key support and resistance levels\n"
                f"3. Chart patterns (if any)\n"
                f"4. Moving averages and their significance\n"
                f"5. Volume analysis\n"
                f"6. Trading recommendations based on the charts\n"
                f"7. Summary table with key price levels and observations\n"
            )
        elif analysis_type == 'short_term':
            system_message = (
                "You are an expert technical analyst specializing in short-term trading analysis. "
                "Analyze the provided 2-month daily charts showing momentum indicators, price overlays, and volume. "
                "Focus on recent price action, momentum shifts, and short-term trading opportunities. "
                "Provide detailed and actionable insights for short-term traders. "
                "Include a summary table at the end with key indicators and signals."
            )
            user_prompt = (
                f"Current Date: {current_date}\n"
                f"Company Ticker: {ticker}\n\n"
                f"Please analyze the following 2-month daily technical indicator charts:\n\n"
                f"Provide a comprehensive short-term technical analysis including:\n"
                f"1. Momentum indicators analysis (RSI, MACD, etc.)\n"
                f"2. Price overlays and moving averages\n"
                f"3. Volume patterns and anomalies\n"
                f"4. Short-term trend strength and direction\n"
                f"5. Overbought/oversold conditions\n"
                f"6. Entry and exit signals for short-term trades\n"
                f"7. Risk levels and stop-loss suggestions\n"
                f"8. Summary table with key indicators and their current signals\n"
            )
        else:  # long_term
            system_message = (
                "You are an expert technical analyst specializing in long-term trend analysis. "
                "Analyze the provided 1-year weekly and 4-year monthly charts showing momentum, price overlays, and volume. "
                "Focus on major trends, long-term patterns, and structural changes in price behavior. "
                "Provide comprehensive insights for long-term investors and position traders. "
                "Include a summary table at the end with key long-term trends and levels."
            )
            user_prompt = (
                f"Current Date: {current_date}\n"
                f"Company Ticker: {ticker}\n\n"
                f"Please analyze the following 1-year weekly and 4-year monthly technical charts:\n\n"
                f"Provide a comprehensive long-term technical analysis including:\n"
                f"1. Major trend analysis (primary and secondary trends)\n"
                f"2. Long-term support and resistance zones\n"
                f"3. Chart patterns on different timeframes\n"
                f"4. Long-term momentum and trend strength\n"
                f"5. Volume trends and their significance\n"
                f"6. Structural changes in price behavior\n"
                f"7. Long-term investment outlook\n"
                f"8. Summary table with key long-term trends and price levels\n"
            )
        
        # Encode all images
        print(f"Encoding {len(image_paths)} images for {analysis_type} analysis...")
        image_contents = []
        
        for img_path in image_paths:
            try:
                encoded_image = self.encode_image(img_path)
                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{encoded_image}"
                    }
                })
                print(f"  ✓ Encoded: {Path(img_path).name}")
            except Exception as e:
                print(f"  ✗ Error encoding {img_path}: {str(e)}")
        
        if not image_contents:
            return f"Failed to encode any images for {analysis_type} analysis."
        
        # Prepare the API request
        print(f"Analyzing {ticker} using AI ({analysis_type})...")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Build the user message content with images
        user_content = [
            {"type": "text", "text": user_prompt}
        ]
        user_content.extend(image_contents)
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": user_content
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
            raise Exception(f"Error calling OpenRouter API for {analysis_type}: {str(e)}")
    
    def analyze_and_save(self, ticker: str, data_dir: str, output_dir: Optional[str] = None) -> List[str]:
        """
        Analyze all chart images for a ticker and save reports
        
        Args:
            ticker: Stock ticker symbol
            data_dir: Path to the data directory
            output_dir: Directory to save the reports. If None, saves in data/output/{timestamp}/analyst/price_image
            
        Returns:
            List of paths to the saved report files
        """
        print(f"\n{'='*60}")
        print(f"Starting Price Chart Image Analysis for {ticker}")
        print(f"{'='*60}\n")
        
        # Find all chart images
        print("Finding chart images...")
        images = self.find_chart_images(ticker, data_dir)
        
        print(f"Found {len(images['basic'])} basic charts")
        print(f"Found {len(images['short_term'])} short-term charts")
        print(f"Found {len(images['long_term'])} long-term charts\n")
        
        # Determine output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_dir is None:
            # Save in data/output/{timestamp}/analyst/price_image/
            base_path = Path(data_dir).parent  # Go up from ticker folder to data/raw parent
            if base_path.name == 'raw':
                base_path = base_path.parent  # Go up one more level to data/
            output_dir = base_path / "output" / timestamp / "analyst" / "price_image"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_reports = []
        
        # Analysis 1: Basic charts (daily and weekly)
        print(f"\n{'='*60}")
        print("Analysis 1/3: Basic Price Charts (Daily & Weekly)")
        print(f"{'='*60}\n")
        
        if images['basic']:
            report1 = self.analyze_images(images['basic'], 'basic', ticker)
            output_file1 = output_dir / f"{ticker}_price_basic_analysis_{timestamp}.md"
            
            with open(output_file1, 'w', encoding='utf-8') as f:
                f.write(f"# Price Chart Analysis (Basic): {ticker}\n")
                f.write(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n")
                f.write(f"Charts Analyzed: Daily and Weekly Price Charts\n\n")
                f.write("---\n\n")
                f.write(report1)
            
            print(f"✓ Report 1 saved to: {output_file1}")
            saved_reports.append(str(output_file1))
        else:
            print("⚠ No basic charts found, skipping analysis 1")
        
        # Analysis 2: Short-term charts (2 months daily)
        print(f"\n{'='*60}")
        print("Analysis 2/3: Short-Term Charts (2-Month Daily)")
        print(f"{'='*60}\n")
        
        if images['short_term']:
            report2 = self.analyze_images(images['short_term'], 'short_term', ticker)
            output_file2 = output_dir / f"{ticker}_price_shortterm_analysis_{timestamp}.md"
            
            with open(output_file2, 'w', encoding='utf-8') as f:
                f.write(f"# Price Chart Analysis (Short-Term): {ticker}\n")
                f.write(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n")
                f.write(f"Charts Analyzed: 2-Month Daily Technical Indicators\n\n")
                f.write("---\n\n")
                f.write(report2)
            
            print(f"✓ Report 2 saved to: {output_file2}")
            saved_reports.append(str(output_file2))
        else:
            print("⚠ No short-term charts found, skipping analysis 2")
        
        # Analysis 3: Long-term charts (1 year weekly + 4 year monthly)
        print(f"\n{'='*60}")
        print("Analysis 3/3: Long-Term Charts (1-Year Weekly & 4-Year Monthly)")
        print(f"{'='*60}\n")
        
        if images['long_term']:
            report3 = self.analyze_images(images['long_term'], 'long_term', ticker)
            output_file3 = output_dir / f"{ticker}_price_longterm_analysis_{timestamp}.md"
            
            with open(output_file3, 'w', encoding='utf-8') as f:
                f.write(f"# Price Chart Analysis (Long-Term): {ticker}\n")
                f.write(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n")
                f.write(f"Charts Analyzed: 1-Year Weekly & 4-Year Monthly Technical Indicators\n\n")
                f.write("---\n\n")
                f.write(report3)
            
            print(f"✓ Report 3 saved to: {output_file3}")
            saved_reports.append(str(output_file3))
        else:
            print("⚠ No long-term charts found, skipping analysis 3")
        
        print(f"\n{'='*60}")
        print(f"Price Chart Image Analysis Complete!")
        print(f"Total Reports Generated: {len(saved_reports)}")
        print(f"{'='*60}\n")
        
        return saved_reports


def main():
    """Example usage of the Price Image Analyst"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze price chart images for a stock ticker')
    parser.add_argument('ticker', type=str, help='Stock ticker symbol (e.g., GOOGL)')
    parser.add_argument('--data-dir', type=str, required=True, help='Path to data directory')
    parser.add_argument('--api-key', type=str, help='OpenRouter API key (or set OPENROUTER_API_KEY env var)')
    parser.add_argument('--output-dir', type=str, help='Directory to save reports (default: auto-generated)')
    
    args = parser.parse_args()
    
    # Initialize analyst
    analyst = PriceImageAnalyst(api_key=args.api_key)
    
    # Analyze and save reports
    report_paths = analyst.analyze_and_save(
        ticker=args.ticker,
        data_dir=args.data_dir,
        output_dir=args.output_dir
    )
    
    print(f"\n✓ All analyses complete!")
    print(f"Reports generated:")
    for i, path in enumerate(report_paths, 1):
        print(f"  {i}. {path}")


if __name__ == "__main__":
    main()

