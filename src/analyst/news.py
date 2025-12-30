"""
News & Narrative / Catalyst Analyst

This module analyzes news and events data including:
- Global News Headlines (from Google News)
- Stock-Specific News (from yfinance)
- Upcoming Events (earnings, dividends, etc.)
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List


class NewsAnalyst:
    """Analyzes news, events, and narratives using AI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the News Analyst
        
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
        Load all news and event data for a given ticker
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            data_dir: Path to the data directory containing ticker folders
            
        Returns:
            Dictionary containing all loaded news data
        """
        data_path = Path(data_dir)
        ticker_path = data_path / ticker
        
        if not ticker_path.exists():
            raise ValueError(f"Data directory for {ticker} not found at {ticker_path}")
        
        data = {
            'ticker': ticker,
            'data_path': str(ticker_path),
            'collection_date': data_path.name if data_path.name.isdigit() else None
        }
        
        # Load Global News
        global_news_path = data_path / "global_news.json"
        if global_news_path.exists():
            with open(global_news_path, 'r', encoding='utf-8') as f:
                data['global_news'] = json.load(f)
        
        # Load Stock-Specific News
        stock_news_path = ticker_path / "yfinance_News.json"
        if stock_news_path.exists():
            with open(stock_news_path, 'r', encoding='utf-8') as f:
                data['stock_news'] = json.load(f)
        
        # Load Upcoming Events
        upcoming_events_path = ticker_path / "yfinance_UpcommingEvents.json"
        if upcoming_events_path.exists():
            with open(upcoming_events_path, 'r', encoding='utf-8') as f:
                data['upcoming_events'] = json.load(f)
        
        return data
    
    def format_data_for_prompt(self, data: Dict[str, Any]) -> str:
        """
        Format loaded news data into a readable string for the AI prompt
        
        Args:
            data: Dictionary containing all loaded news data
            
        Returns:
            Formatted string representation of the data
        """
        sections = []
        ticker = data['ticker']
        
        sections.append(f"# News & Events Analysis Data for {ticker}\n")
        
        # Upcoming Events
        if 'upcoming_events' in data:
            sections.append("## Upcoming Events & Catalysts")
            events = data['upcoming_events']
            
            if 'Earnings Date' in events:
                earnings_dates = events['Earnings Date']
                if isinstance(earnings_dates, list):
                    sections.append(f"**Earnings Date:** {', '.join(earnings_dates)}")
                else:
                    sections.append(f"**Earnings Date:** {earnings_dates}")
            
            if 'Dividend Date' in events:
                sections.append(f"**Dividend Date:** {events.get('Dividend Date', 'N/A')}")
            
            if 'Ex-Dividend Date' in events:
                sections.append(f"**Ex-Dividend Date:** {events.get('Ex-Dividend Date', 'N/A')}")
            
            # Earnings Estimates
            if 'Earnings Average' in events:
                sections.append(f"\n**Earnings Estimates:**")
                sections.append(f"- Average: ${events.get('Earnings Average', 'N/A')}")
                sections.append(f"- High: ${events.get('Earnings High', 'N/A')}")
                sections.append(f"- Low: ${events.get('Earnings Low', 'N/A')}")
            
            # Revenue Estimates
            if 'Revenue Average' in events:
                sections.append(f"\n**Revenue Estimates:**")
                sections.append(f"- Average: ${events.get('Revenue Average', 'N/A'):,}")
                sections.append(f"- High: ${events.get('Revenue High', 'N/A'):,}")
                sections.append(f"- Low: ${events.get('Revenue Low', 'N/A'):,}")
            
            sections.append("")
        
        # Stock-Specific News
        if 'stock_news' in data:
            sections.append("## Stock-Specific News")
            news_data = data['stock_news']
            
            if 'total_articles' in news_data:
                sections.append(f"**Total Articles:** {news_data['total_articles']}\n")
            
            if 'articles' in news_data and news_data['articles']:
                sections.append("### Recent Articles:\n")
                # Limit to first 20 articles to keep prompt manageable
                for i, article in enumerate(news_data['articles'][:20], 1):
                    sections.append(f"**{i}. {article.get('title', 'No title')}**")
                    sections.append(f"   - Source: {article.get('source', 'Unknown')}")
                    sections.append(f"   - Time: {article.get('time', 'N/A')}")
                    
                    # Add content preview if available
                    if article.get('content'):
                        content = article['content']
                        # Truncate long content
                        if len(content) > 500:
                            content = content[:500] + "..."
                        sections.append(f"   - Preview: {content}")
                    
                    sections.append("")
                
                if len(news_data['articles']) > 20:
                    sections.append(f"... and {len(news_data['articles']) - 20} more articles\n")
        
        # Global News
        if 'global_news' in data:
            sections.append("## Global News Context")
            global_data = data['global_news']
            
            if 'collection_date' in global_data:
                sections.append(f"**Collection Date:** {global_data['collection_date']}")
            if 'collection_time' in global_data:
                sections.append(f"**Collection Time:** {global_data['collection_time']}\n")
            
            if 'data' in global_data:
                news_categories = global_data['data']
                
                # US News
                if 'US_News' in news_categories:
                    sections.append("### US News Headlines (Sample):")
                    us_news = news_categories['US_News'][:15]  # First 15 headlines
                    for i, article in enumerate(us_news, 1):
                        sections.append(f"{i}. {article.get('title', 'No title')} - {article.get('source', 'Unknown')} ({article.get('date', 'N/A')})")
                    sections.append("")
                
                # World News
                if 'World_News' in news_categories:
                    sections.append("### World News Headlines (Sample):")
                    world_news = news_categories['World_News'][:15]  # First 15 headlines
                    for i, article in enumerate(world_news, 1):
                        sections.append(f"{i}. {article.get('title', 'No title')} - {article.get('source', 'Unknown')} ({article.get('date', 'N/A')})")
                    sections.append("")
        
        return "\n".join(sections)
    
    def analyze(self, ticker: str, data_dir: str) -> str:
        """
        Perform news and narrative analysis on a given ticker
        
        Args:
            ticker: Stock ticker symbol
            data_dir: Path to the data directory
            
        Returns:
            Comprehensive news analysis report
        """
        # Load data
        print(f"Loading news data for {ticker}...")
        data = self.load_data(ticker, data_dir)
        
        # Format data for prompt
        formatted_data = self.format_data_for_prompt(data)
        
        # Prepare the prompt
        current_date = datetime.now().strftime("%B %d, %Y")
        
        system_message = (
            "You are a financial analyst specializing in news analysis and market narratives. "
            "Your task is to analyze news articles, upcoming events, and global context to identify "
            "catalysts, sentiment, and potential market-moving narratives for traders and investors. "
            "Provide detailed analysis with actionable insights. Look for themes, sentiment trends, "
            "and connections between company-specific news and broader market conditions. "
            "Do not simply summarize headlines - provide deep analysis of implications and potential impacts. "
            "Make sure to append a Markdown table at the end summarizing key catalysts, sentiment, and timing."
        )
        
        user_message = (
            f"Current Date: {current_date}\n"
            f"Company Ticker: {ticker}\n\n"
            f"Please analyze the following news and events data:\n\n"
            f"{formatted_data}\n\n"
            f"Provide a comprehensive news and narrative analysis report that includes:\n"
            f"1. Upcoming Catalysts & Events (earnings, dividends, key dates)\n"
            f"2. Stock-Specific News Analysis (sentiment, themes, key stories)\n"
            f"3. Global News Context (relevant macro trends, geopolitical factors)\n"
            f"4. Market Sentiment Assessment (bullish, bearish, neutral indicators)\n"
            f"5. Key Narratives & Themes (what stories are driving discussion)\n"
            f"6. Potential Impact on Stock Price (near-term and medium-term)\n"
            f"7. Risk Factors & Watch Points\n"
            f"8. Summary table with key catalysts, sentiment signals, and timing\n"
        )
        
        # Call OpenRouter API
        print(f"Analyzing news for {ticker} using AI...")
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
        Analyze ticker news and save the report to a file
        
        Args:
            ticker: Stock ticker symbol
            data_dir: Path to the data directory
            output_dir: Directory to save the report. If None, saves in data/output/{timestamp}/analyst/news
            
        Returns:
            Path to the saved report file
        """
        # Perform analysis
        report = self.analyze(ticker, data_dir)
        
        # Determine output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_dir is None:
            # Save in data/output/{timestamp}/analyst/news/
            base_path = Path(data_dir).parent  # Go up from ticker folder to data/raw parent
            if base_path.name == 'raw':
                base_path = base_path.parent  # Go up one more level to data/
            output_dir = base_path / "output" / timestamp / "analyst" / "news"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save report
        output_file = output_dir / f"{ticker}_news_analysis_{timestamp}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# News & Narrative Analysis Report: {ticker}\n")
            f.write(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n")
            f.write("---\n\n")
            f.write(report)
        
        print(f"Report saved to: {output_file}")
        return str(output_file)


def main():
    """Example usage of the News Analyst"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze news and events for a stock ticker')
    parser.add_argument('ticker', type=str, help='Stock ticker symbol (e.g., AAPL)')
    parser.add_argument('--data-dir', type=str, required=True, help='Path to data directory')
    parser.add_argument('--api-key', type=str, help='OpenRouter API key (or set OPENROUTER_API_KEY env var)')
    parser.add_argument('--output-dir', type=str, help='Directory to save report (default: data/output/{timestamp}/analyst/news)')
    
    args = parser.parse_args()
    
    # Initialize analyst
    analyst = NewsAnalyst(api_key=args.api_key)
    
    # Analyze and save report
    report_path = analyst.analyze_and_save(
        ticker=args.ticker,
        data_dir=args.data_dir,
        output_dir=args.output_dir
    )
    
    print(f"\n✓ News analysis complete!")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()

