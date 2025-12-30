import re
import json
import time
import threading
import requests
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Constants
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://finviz.com/"
}

class RateLimiter:
    """Thread-safe rate limiter for API calls."""
    def __init__(self, rps: float):
        self.interval = 1.0 / rps
        self.lock = threading.Lock()
        self.last = 0.0

    def wait(self):
        with self.lock:
            current = time.time()
            elapsed = current - self.last
            if elapsed < self.interval:
                time.sleep(self.interval - elapsed)
            self.last = time.time()

class FinvizCollector:
    """
    Integrated Finviz data collector combining chart downloads, 
    technical stats, and screening capabilities.
    """
    
    def __init__(self, ticker: Optional[str] = None, rps: float = 3.0):
        self.ticker = ticker.upper() if ticker else None
        self.limiter = RateLimiter(rps)
        self.base_url = "https://finviz.com"

    def _clean_label(self, label: str) -> str:
        """Standardize labels for data consistency."""
        if not label:
            return ""
        return label.replace(".", "").replace("/", "_").replace(" ", "_")

    def get_daily_chart(self, output_dir: str = "charts") -> str:
        """
        Download a daily candlestick chart for the ticker.
        Corresponds to 'DailyChart' in requested output.
        """
        if not self.ticker:
            raise ValueError("Ticker is required for chart download")
            
        # Build URL for Daily (p=d), Candlestick (ty=c), Large (s=l)
        url = f"{self.base_url}/chart.ashx?t={self.ticker}&ty=c&ta=1&p=d&s=l"
        
        output_path = Path(output_dir) / f"{self.ticker}_daily.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.limiter.wait()
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return str(output_path)
        except Exception as e:
            print(f"Error downloading chart for {self.ticker}: {e}")
            return ""

    def get_weekly_chart(self, output_dir: str = "charts") -> str:
        """
        Download a weekly candlestick chart for the ticker.
        Corresponds to 'WeeklyChart' in requested output.
        """
        if not self.ticker:
            raise ValueError("Ticker is required for chart download")
            
        # Build URL for Weekly (p=w), Candlestick (ty=c), Large (s=l)
        url = f"{self.base_url}/chart.ashx?t={self.ticker}&ty=c&ta=1&p=w&s=l"
        
        output_path = Path(output_dir) / f"{self.ticker}_weekly.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.limiter.wait()
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return str(output_path)
        except Exception as e:
            print(f"Error downloading chart for {self.ticker}: {e}")
            return ""

    def get_key_finance_stats(self) -> pd.DataFrame:
        """
        Extract technical and fundamental data from the Finviz quote page.
        Corresponds to 'KeyFinanceStat_finviz' in requested output.
        """
        if not self.ticker:
            return pd.DataFrame()
            
        url = f"{self.base_url}/quote.ashx?t={self.ticker}"
        
        self.limiter.wait()
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            data_dict = {}
            
            # 1. Extract Snapshot Table
            if table := soup.find("table", class_="snapshot-table2"):
                for row in table.find_all("tr"):
                    cells = row.find_all("td")
                    for i in range(0, len(cells) - 1, 2):
                        label = cells[i].get_text(strip=True)
                        if label:
                            # Extract value from <b> or <a> within the cell
                            value_elem = cells[i + 1].find(["b", "a"]) or cells[i + 1]
                            value = " ".join(value_elem.get_text().split())
                            if value and value != "-":
                                data_dict[self._clean_label(label)] = value
            
            # 2. Extract Company Name and Header Info
            if name_elem := soup.find("h2"):
                data_dict["Company"] = name_elem.get_text(strip=True)
            
            # Sector, Industry, Country from links
            links = [a.get_text(strip=True) for a in soup.find_all("a", class_="tab-link")]
            links = [t for t in links if t and t != data_dict.get("Company")]
            for i, key in enumerate(["Sector", "Industry", "Country"]):
                if i < len(links):
                    data_dict[key] = links[i]
            
            # Convert to DataFrame (Stat, Value format like yfinance reference)
            if data_dict:
                df = pd.DataFrame(list(data_dict.items()), columns=['Stat', 'Value'])
                return df
            return pd.DataFrame()
            
        except Exception as e:
            print(f"Error fetching technical stats for {self.ticker}: {e}")
            return pd.DataFrame()

    def get_peers(self) -> List[str]:
        """
        Collect the top 5 peers for the ticker from Finviz.
        Corresponds to the logic in get_peers.py.
        """
        if not self.ticker:
            return []
            
        url = f"{self.base_url}/quote.ashx?t={self.ticker}"
        
        self.limiter.wait()
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Look for the 'Peers' link which contains the ticker list in its href
            # Example href: "screener.ashx?t=TGT,COST,DG,DLTR,BJ,KR,AMZN,HD,LOW,FIVE"
            peers_link = soup.find("a", string=lambda t: t and "Peers" in t)
            
            if peers_link and 'href' in peers_link.attrs:
                href = peers_link['href']
                # Extract tickers from the 't' parameter
                match = re.search(r"t=([A-Z0-9,.-]+)", href)
                if match:
                    peers_str = match.group(1)
                    peers_list = peers_str.split(',')
                    # Filter out the original ticker if present and return top 5
                    filtered_peers = [p for p in peers_list if p and p != self.ticker]
                    return filtered_peers[:5]
            
            return []
            
        except Exception as e:
            print(f"Error fetching peers for {self.ticker}: {e}")
            return []

    def get_screener_tickers(self) -> List[str]:
        """
        Extract tickers from Finviz screener with Volume > 5M and Price > $50.
        Corresponds to 'Screener' in requested output.
        """
        # Filters: Volume over 5M (sh_curvol_o5000), Price over $50 (sh_price_o50)
        # v=111 is the basic screener view
        screener_url = f"{self.base_url}/screener.ashx?v=111&f=geo_usa,ind_stocksonly,sh_curvol_o5000,sh_price_o50&ft=4"
        
        tickers = []
        try:
            self.limiter.wait()
            resp = requests.get(screener_url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Parse total count for pagination
            total = 0
            if (el := soup.find("td", class_="count-text")):
                if (m := re.search(r"Total:\s*(\d+)", el.get_text())):
                    total = int(m.group(1))
            
            if not total:
                # Fallback pattern #1 / 123
                for td in soup.find_all("td"):
                    if (m := re.search(r"#\d+\s*/\s*(\d+)", td.get_text())):
                        total = int(m.group(1))
                        break
            
            def parse_tickers_from_html(html_content):
                page_soup = BeautifulSoup(html_content, "html.parser")
                # Try primary screener link class first
                links = page_soup.find_all("a", class_="screener-link-primary")
                if not links:
                    # Fallback to any quote link
                    links = page_soup.find_all("a", href=re.compile(r"quote\.ashx\?t="))
                
                found = []
                for link in links:
                    href = link.get("href", "")
                    if match := re.search(r"quote\.ashx\?t=([A-Z0-9.-]+)", href):
                        found.append(match.group(1))
                return list(dict.fromkeys(found))

            tickers = parse_tickers_from_html(resp.text)
            print(f"First page: {len(tickers)} tickers found. Total results: {total}")
            
            # Handle Pagination (20 rows per page)
            if total > 20:
                rows_per_page = 20
                total_pages = (total + rows_per_page - 1) // rows_per_page
                page_rows = [1 + i * rows_per_page for i in range(1, total_pages)]
                
                print(f"Fetching remaining {total_pages - 1} pages...")
                
                def fetch_page(row):
                    url = f"{screener_url}&r={row}"
                    self.limiter.wait()
                    try:
                        r = requests.get(url, headers=HEADERS, timeout=30)
                        r.raise_for_status()
                        p_tickers = parse_tickers_from_html(r.text)
                        return p_tickers
                    except Exception as e:
                        print(f"  Error fetching row {row}: {e}")
                        return []

                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [executor.submit(fetch_page, r) for r in page_rows]
                    for i, future in enumerate(as_completed(futures), 1):
                        page_results = future.result()
                        tickers.extend(page_results)
                        if i % 5 == 0 or i == len(futures):
                            print(f"  Progress: {i}/{len(futures)} pages fetched")
            
            unique_tickers = sorted(list(set(tickers)))
            print(f"Done: {len(unique_tickers)} unique tickers extracted")
            return unique_tickers
            
        except Exception as e:
            print(f"Error in screening: {e}")
            return []

    def _fetch_options_page(self, expiry: Optional[str] = None) -> Optional[str]:
        """
        Fetch the options page HTML
        
        Args:
            expiry: Optional expiry date in YYYY-MM-DD format
            
        Returns:
            HTML content or None if request fails
        """
        if not self.ticker:
            return None
            
        url = f"{self.base_url}/quote.ashx?t={self.ticker}&p=d&ty=oc"
        if expiry:
            url += f"&e={expiry}"
        
        self.limiter.wait()
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            print(f"Error fetching options page for {self.ticker}: {e}")
            return None
    
    def _extract_options_json_data(self, html: str) -> Optional[Dict]:
        """
        Extract the embedded JSON data from the options page
        
        Args:
            html: Page HTML content
            
        Returns:
            Parsed JSON data or None
        """
        soup = BeautifulSoup(html, "html.parser")
        
        # Find the script tag with route-init-data
        script = soup.find("script", id="route-init-data")
        
        if script and script.string:
            try:
                return json.loads(script.string)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON data: {e}")
                return None
        
        return None
    
    def get_available_option_expiries(self) -> List[str]:
        """
        Get list of available expiry dates for the ticker
        
        Returns:
            List of expiry dates in YYYY-MM-DD format
        """
        if not self.ticker:
            return []
            
        html = self._fetch_options_page()
        if not html:
            return []
        
        data = self._extract_options_json_data(html)
        if data and "expiries" in data:
            return data["expiries"]
        
        return []
    
    def get_nearest_expiry(self, target_days: int = 30, from_date: Optional[str] = None) -> Optional[str]:
        """
        Find the expiry date closest to a target number of days from now
        
        Args:
            target_days: Number of days from now to target (default: 30 for 1 month)
            from_date: Reference date in YYYY-MM-DD format (default: today)
            
        Returns:
            Expiry date in YYYY-MM-DD format or None if no expiries available
        """
        expiries = self.get_available_option_expiries()
        if not expiries:
            return None
        
        # Use provided date or today
        if from_date:
            reference = pd.Timestamp(from_date)
        else:
            reference = pd.Timestamp.now()
        
        target_date = reference + pd.Timedelta(days=target_days)
        
        # Find closest expiry to target date
        closest_expiry = None
        min_diff = float('inf')
        
        for expiry in expiries:
            expiry_date = pd.Timestamp(expiry)
            diff = abs((expiry_date - target_date).days)
            
            if diff < min_diff:
                min_diff = diff
                closest_expiry = expiry
        
        return closest_expiry
    
    def get_option_chain(self, expiry: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Extract option chain data for a given expiry
        
        Args:
            expiry: Expiry date in YYYY-MM-DD format (e.g., '2026-01-23')
            
        Returns:
            Tuple of (calls_df, puts_df) DataFrames
        """
        if not self.ticker:
            return pd.DataFrame(), pd.DataFrame()
            
        html = self._fetch_options_page(expiry)
        if not html:
            return pd.DataFrame(), pd.DataFrame()
        
        data = self._extract_options_json_data(html)
        if not data or "options" not in data:
            print(f"No options data found for {self.ticker}")
            return pd.DataFrame(), pd.DataFrame()
        
        options = data["options"]
        
        if not options:
            print(f"Empty options list for {self.ticker}")
            return pd.DataFrame(), pd.DataFrame()
        
        # Separate calls and puts
        calls_data = []
        puts_data = []
        
        for opt in options:
            record = {
                "Strike": opt.get("strike"),
                "Bid": opt.get("bidPrice"),
                "Ask": opt.get("askPrice"),
                "Last": opt.get("lastClose") if opt.get("lastClose", 0) != 0 else None,
                "Change": opt.get("lastChange") if opt.get("lastChange", 0) != 0 else None,
                "OpenInt": opt.get("openInterest", 0),
                "IV": opt.get("iv"),
                "Delta": opt.get("delta"),
                "Gamma": opt.get("gamma"),
                "Theta": opt.get("theta"),
                "Vega": opt.get("vega"),
                "Rho": opt.get("rho"),
            }
            
            if opt.get("type") == "call":
                calls_data.append(record)
            elif opt.get("type") == "put":
                puts_data.append(record)
        
        # Create DataFrames
        calls_df = pd.DataFrame(calls_data) if calls_data else pd.DataFrame()
        puts_df = pd.DataFrame(puts_data) if puts_data else pd.DataFrame()
        
        # Sort by strike
        if not calls_df.empty:
            calls_df = calls_df.sort_values("Strike").reset_index(drop=True)
        if not puts_df.empty:
            puts_df = puts_df.sort_values("Strike").reset_index(drop=True)
        
        return calls_df, puts_df
    
    def save_option_chain(self, expiry: str, output_dir: str = ".") -> Tuple[str, str]:
        """
        Extract option chain and save to CSV files
        
        Args:
            expiry: Expiry date in YYYY-MM-DD format
            output_dir: Directory to save files
            
        Returns:
            Tuple of (calls_path, puts_path)
        """
        if not self.ticker:
            return "", ""
            
        calls_df, puts_df = self.get_option_chain(expiry)
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        calls_file = output_path / f"finviz_OptionChainCall_{expiry}.csv"
        puts_file = output_path / f"finviz_OptionChainPut_{expiry}.csv"
        
        # Save calls
        if not calls_df.empty:
            calls_df.to_csv(calls_file, index=False)
            print(f"Saved calls to: {calls_file}")
        else:
            print("No calls data to save")
            calls_file = ""
            
        # Save puts
        if not puts_df.empty:
            puts_df.to_csv(puts_file, index=False)
            print(f"Saved puts to: {puts_file}")
        else:
            print("No puts data to save")
            puts_file = ""
        
        return str(calls_file), str(puts_file)
    
    def save_option_chains_multi_expiry(self, output_dir: str = ".", target_days: List[int] = None) -> Dict[str, Tuple[str, str]]:
        """
        Save option chains for multiple target expiry periods
        
        Args:
            output_dir: Directory to save files
            target_days: List of target days from now (default: [7, 30] for 1 week and 1 month)
            
        Returns:
            Dictionary mapping expiry dates to (calls_path, puts_path) tuples
        """
        if not self.ticker:
            return {}
        
        if target_days is None:
            target_days = [7, 30]  # Default: 1 week and 1 month
        
        results = {}
        
        for days in target_days:
            expiry = self.get_nearest_expiry(target_days=days)
            if expiry:
                print(f"\nCollecting option chain for ~{days} days out (expiry: {expiry})...")
                paths = self.save_option_chain(expiry, output_dir)
                results[expiry] = paths
            else:
                print(f"No expiry found for target {days} days")
        
        return results

    def get_all_data(self, chart_output_dir: str = "charts") -> Dict[str, Union[str, pd.DataFrame, List[str]]]:
        """
        Fetch all Finviz data points as requested.
        
        Args:
            chart_output_dir: Directory to save chart images (default: "charts")
        """
        results = {}
        
        # Screener results (independent of ticker)
        results["Screener"] = self.get_screener_tickers()
        
        # Ticker-specific results
        if self.ticker:
            results["DailyChart"] = self.get_daily_chart(output_dir=chart_output_dir)
            results["WeeklyChart"] = self.get_weekly_chart(output_dir=chart_output_dir)
            results["KeyFinanceStat_finviz"] = self.get_key_finance_stats()
            results["Peers"] = self.get_peers()
            
        return results

