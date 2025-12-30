import json
import time
import threading
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Union

# Constants
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://news.google.com/"
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

class GoogleNewsCollector:
    """
    Collector for Google News data.
    """
    
    def __init__(self, rps: float = 2.0):
        self.limiter = RateLimiter(rps)
        self.base_url = "https://news.google.com"
        self.us_news_url = (
            "https://news.google.com/topics/CAAqIggKIhxDQkFTRHdvSkwyMHZNRGxqTjNjd0VnSmxiaWdBUAE"
            "?hl=en-US&gl=US&ceid=US%3Aen"
        )
        self.world_news_url = (
            "https://news.google.com/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx1YlY4U0FtVnVHZ0pWVXlnQVAB"
            "?hl=en-US&gl=US&ceid=US%3Aen"
        )

    def _get_news_from_url(self, url: str) -> List[Dict[str, str]]:
        """Internal helper to scrape news from a specific Google News topic URL."""
        self.limiter.wait()
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "html.parser")
            news_items = []
            
            # Find all article containers
            containers = soup.find_all("div", class_="IBr9hb")
            
            for container in containers:
                try:
                    # Title
                    title_elem = container.find("a", class_="gPFEn")
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    # Source
                    source_elem = container.find("div", class_="vr1PYe")
                    source = source_elem.get_text(strip=True) if source_elem else ""
                    
                    # Date/Time
                    time_elem = container.find("time")
                    date = time_elem.get_text(strip=True) if time_elem else ""
                    
                    if title:
                        news_items.append({
                            "title": title,
                            "source": source,
                            "date": date
                        })
                except Exception as e:
                    print(f"Error parsing news item: {e}")
                    continue
            return news_items
            
        except Exception as e:
            print(f"Error fetching news from {url}: {e}")
            return []

    def get_us_news(self) -> List[Dict[str, str]]:
        """Collect US news title, date, and source."""
        return self._get_news_from_url(self.us_news_url)

    def get_world_news(self) -> List[Dict[str, str]]:
        """Collect World news title, date, and source."""
        return self._get_news_from_url(self.world_news_url)

    def get_all_data(self) -> str:
        """
        Fetch all news data (US and World) and return as a JSON string.
        """
        results = {
            "US_News": self.get_us_news(),
            "World_News": self.get_world_news()
        }
        return results

if __name__ == "__main__":
    collector = GoogleNewsCollector()
    with open("data/processed/AAPL_20251226_141139/google_news.json", 'w') as fp:
        json.dump(collector.get_all_data(), fp, indent=4)
