import yfinance as yf
import pandas as pd
import requests
import io
import re
import json
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Union, List, Optional

# Constants for News and Scraping
TRUSTED_SOURCES = {
    "bloomberg", "reuters", "wall street journal", "wsj", "barron",
    "associated press", "ap news", "yahoo finance", "investor's business daily",
    "ibd", "fortune", "cnn", "zacks", "motley fool", "marketbeat", "barchart",
    "benzinga", "thestreet", "investing.com", "business wire", "globenewswire",
    "pr newswire", "prnewswire",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://finance.yahoo.com",
    "Referer": "https://finance.yahoo.com/",
}

class YFinanceCollector:
    """
    A collector class to fetch various financial data for a given ticker using yfinance and scraping.
    """
    def __init__(self, ticker: str):
        self.ticker_symbol = ticker.upper()
        self.ticker = yf.Ticker(self.ticker_symbol)

    def _clean_label(self, label: str) -> str:
        """Remove footnotes and extra whitespace from labels."""
        if not isinstance(label, str):
            return label
        label = re.sub(r'\s+\d+$', '', label)
        label = re.sub(r'([a-z])\d$', r'\1', label)
        return label.strip()

    def get_ticker_info(self) -> Dict:
        """Business Summary + Sector + Industry"""
        info = self.ticker.info
        return {
            "longBusinessSummary": info.get("longBusinessSummary"),
            "sector": info.get("sector"),
            "industry": info.get("industry")
        }

    def get_history_2mo_1d(self) -> pd.DataFrame:
        """Historical price 2 month with 1 day interval"""
        return self.ticker.history(period="2mo", interval="1d")

    def get_history_1y_1wk(self) -> pd.DataFrame:
        """Historical price 1 year with 1 week interval"""
        return self.ticker.history(period="1y", interval="1wk")

    def get_history_4y_1mo(self) -> pd.DataFrame:
        """Historical price 4 years with 1 month interval"""
        return self.ticker.history(period="4y", interval="1mo")

    def get_upcoming_events(self) -> Dict:
        """Upcoming event"""
        return self.ticker.calendar

    def get_holding_breakdown(self) -> pd.DataFrame:
        """Composition of holdings"""
        return self.ticker.major_holders

    def get_major_institutional_holders(self) -> pd.DataFrame:
        """Institutional holder breakdown"""
        return self.ticker.institutional_holders

    def get_major_mutual_fund_holders(self) -> pd.DataFrame:
        """Mutualfund holder breakdown"""
        return self.ticker.mutualfund_holders

    def get_insider_purchase(self) -> pd.DataFrame:
        """Insider purchase summary"""
        return self.ticker.insider_purchases

    def get_updowngrade(self) -> pd.DataFrame:
        """Previous 15 updowngrade history"""
        data = self.ticker.upgrades_downgrades
        if data is not None and not data.empty:
            return data.head(15)
        return pd.DataFrame()

    def get_revenue_estimate(self) -> pd.DataFrame:
        """Estimation of revenue by quarter and year"""
        return self.ticker.revenue_estimate

    def get_earning_estimate(self) -> pd.DataFrame:
        """Estimation of earning by quarter and year"""
        return self.ticker.earnings_estimate

    def get_eps_estimate_history(self) -> pd.DataFrame:
        """Estimation of eps by quarter"""
        return self.ticker.earnings_history

    def get_growth_estimate(self) -> pd.DataFrame:
        """Estimation of growth"""
        return self.ticker.growth_estimates

    def get_option_chain_call(self, date_index: int = 0) -> pd.DataFrame:
        """Call option chain"""
        if not self.ticker.options:
            return pd.DataFrame()
        idx = min(date_index, len(self.ticker.options) - 1)
        date = self.ticker.options[idx]
        chain = self.ticker.option_chain(date)
        if chain.calls is not None:
            return chain.calls[['strike', 'lastPrice', 'change', 'volume', 'openInterest', 'impliedVolatility']].dropna()
        return pd.DataFrame()

    def get_option_chain_put(self, date_index: int = 0) -> pd.DataFrame:
        """Put option chain"""
        if not self.ticker.options:
            return pd.DataFrame()
        idx = min(date_index, len(self.ticker.options) - 1)
        date = self.ticker.options[idx]
        chain = self.ticker.option_chain(date)
        if chain.puts is not None:
            return chain.puts[['strike', 'lastPrice', 'change', 'volume', 'openInterest', 'impliedVolatility']].dropna()
        return pd.DataFrame()

    # Integrated from get_historical_stat.py
    def _fetch_key_stats_tables(self) -> List[pd.DataFrame]:
        """Internal helper to fetch tables from key-statistics page."""
        url = f"https://finance.yahoo.com/quote/{self.ticker_symbol}/key-statistics"
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            if response.status_code == 404:
                url_alt = f"https://finance.yahoo.com/quote/{self.ticker_symbol}/key-statistics?p={self.ticker_symbol}"
                response = requests.get(url_alt, headers=HEADERS, timeout=15)
            response.raise_for_status()
            return pd.read_html(io.StringIO(response.text))
        except Exception as e:
            print(f"Error fetching key stats for {self.ticker_symbol}: {e}")
            return []

    def get_key_finance_stats(self) -> pd.DataFrame:
        """
        Key Finance Stat from Yahoo Finance (highlights_df)
        Output: dataframe
        """
        tables = self._fetch_key_stats_tables()
        if not tables or len(tables) < 2:
            return pd.DataFrame()

        highlights_list = []
        for i in range(1, len(tables)):
            df = tables[i]
            if df.shape[1] == 2:
                df.columns = ['Stat', 'Value']
                highlights_list.append(df)
        
        if highlights_list:
            highlights_df = pd.concat(highlights_list, ignore_index=True)
            highlights_df['Stat'] = highlights_df['Stat'].apply(self._clean_label)
            return highlights_df
        return pd.DataFrame()

    def get_historical_valuation_stats(self) -> pd.DataFrame:
        """
        Historical value of financial data such as P/E, P/B (valuation_df)
        Output: dataframe
        """
        tables = self._fetch_key_stats_tables()
        if not tables:
            return pd.DataFrame()

        valuation_df = tables[0]
        valuation_df.columns = [self._clean_label(col) for col in valuation_df.columns]
        if str(valuation_df.columns[0]).startswith('Unnamed'):
            valuation_df.columns = ['Measure'] + list(valuation_df.columns[1:])
        valuation_df.iloc[:, 0] = valuation_df.iloc[:, 0].apply(self._clean_label)
        return valuation_df

    # Integrated from get_finance.py
    def get_financial_report(self) -> Dict[str, pd.DataFrame]:
        """
        Balance sheet, Income statement, and cash flow
        Output: dictionary of dataframes
        """
        return {
            "Income Statement": self.ticker.income_stmt,
            "Balance Sheet": self.ticker.balance_sheet,
            "Cash Flow": self.ticker.cashflow
        }

    # Integrated from news.py
    def _is_trusted_source(self, source: str) -> bool:
        if not source: return False
        source_lower = source.lower()
        return any(t in source_lower or source_lower in t for t in TRUSTED_SOURCES)

    def _fetch_article_content(self, url: str) -> str:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup.find_all(["script", "style", "nav", "footer", "aside", "iframe"]):
                tag.decompose()
            content_selectors = [".caas-body", "article .body", "[data-testid='article-body']", ".article-body", ".story-body", "article"]
            for selector in content_selectors:
                if elem := soup.select_one(selector):
                    paragraphs = elem.find_all("p")
                    if paragraphs:
                        text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
                        if len(text) > 100: return text
            paragraphs = soup.find_all("p")
            text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 50)
            return text[:5000] if text else ""
        except: return ""

    def get_news(self, days: int = 7, trusted_only: bool = True, fetch_content: bool = True) -> Dict:
        """
        Stock news with reliable source
        Output: dictionary
        """
        try:
            raw_news = self.ticker.get_news(count=250)
            if not raw_news:
                return {
                    "ticker": self.ticker_symbol,
                    "total_articles": 0,
                    "articles": []
                }

            articles = []
            cutoff = datetime.now() - timedelta(days=days)
            
            for item in raw_news:
                if not item or not isinstance(item, dict):
                    continue
                    
                content = item.get("content")
                if not content or not isinstance(content, dict):
                    continue
                    
                title = content.get("title", "")
                if not title:
                    continue
                
                # Extract link safely
                click_through = content.get("clickThroughUrl")
                link = ""
                if isinstance(click_through, dict):
                    link = click_through.get("url", "")
                
                if not link:
                    canonical = content.get("canonicalUrl")
                    if isinstance(canonical, dict):
                        link = canonical.get("url", "")
                
                if not link:
                    continue
                
                # Extract provider/source safely
                provider = content.get("provider")
                source = ""
                if isinstance(provider, dict):
                    source = provider.get("displayName", "")
                
                if trusted_only and not self._is_trusted_source(source):
                    continue
                
                pub_date_str = content.get("pubDate", "")
                estimated_date = None
                if pub_date_str:
                    try:
                        estimated_date = datetime.strptime(pub_date_str, "%Y-%m-%dT%H:%M:%SZ")
                    except:
                        pass
                
                if estimated_date and estimated_date < cutoff:
                    continue
                
                articles.append({
                    "title": title,
                    "source": source,
                    "time": pub_date_str,
                    "link": link,
                    "content": ""
                })

            if fetch_content and articles:
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = {executor.submit(self._fetch_article_content, a["link"]): i for i, a in enumerate(articles)}
                    for future in as_completed(futures):
                        idx = futures[future]
                        articles[idx]["content"] = future.result()

            return {
                "ticker": self.ticker_symbol,
                "total_articles": len(articles),
                "articles": articles
            }
        except Exception as e:
            print(f"Error fetching news for {self.ticker_symbol}: {e}")
            return {
                "ticker": self.ticker_symbol,
                "total_articles": 0,
                "articles": []
            }

    def get_all_data(self) -> Dict[str, Union[Dict, pd.DataFrame]]:
        """
        Fetch all info and return as a dictionary.
        """
        return {
            "TickerInfo": self.get_ticker_info(),
            "History1mo/d": self.get_history_2mo_1d(),
            "History6m/1wk": self.get_history_1y_1wk(),
            "History2y/1mo": self.get_history_4y_1mo(),
            "UpcommingEvents": self.get_upcoming_events(),
            "HoldingBreakdown": self.get_holding_breakdown(),
            "MajorInstitutionalHolders": self.get_major_institutional_holders(),
            "MajorMutualFundHolders": self.get_major_mutual_fund_holders(),
            "InsiderPurchase": self.get_insider_purchase(),
            "Updowngrade": self.get_updowngrade(),
            "RevenueEstimate": self.get_revenue_estimate(),
            "EarningEstimate": self.get_earning_estimate(),
            "EPSEestimateHistory": self.get_eps_estimate_history(),
            "GrowthEstimate": self.get_growth_estimate(),
            "OptionChainCall": self.get_option_chain_call(),
            "OptionChainPut": self.get_option_chain_put(),
            "KeyFinanceStat_yfiance": self.get_key_finance_stats(),
            "HistoricalStat": self.get_historical_valuation_stats(),
            "FinancialReport": self.get_financial_report(),
            "News": self.get_news()
        }
