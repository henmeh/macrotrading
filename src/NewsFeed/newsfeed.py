#how to activate the .venv in a terminal
#source .venv/bin/activate

import requests
import os
from dotenv import load_dotenv
import feedparser
import sqlite3
from datetime import datetime
from dateutil import parser
import pytz



class NewsFeed():
    def __init__(self, db_name: str = "news_feed.db"):
        load_dotenv()
        self.db_name = db_name
        self._initialize_database()
        self.get_macro_news_api()
        self.get_macro_news()
        self.get_marketaux_news()
        self.get_alphavantage_news()
        self.get_fred_news()
    

    def _initialize_database(self):
        """Create database and tables if they don't exist"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    content TEXT,
                    url TEXT UNIQUE NOT NULL,
                    published_at TIMESTAMP,
                    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    category TEXT
                )
            """)
            # Index for faster searching
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_title ON articles(title)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_published ON articles(published_at)")
            conn.commit()
    

    def _store_articles(self, articles: list[dict], source: str):
        """Store articles in database, ignoring duplicates"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            for article in articles:
                try:
                    cursor.execute("""
                        INSERT INTO articles (
                            source, title, description, content, url, published_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        source,
                        article["title"],
                        article.get("description"),
                        article.get("content"),
                        article["url"],
                        article.get("published_at", datetime.now().isoformat())
                    ))
                except sqlite3.IntegrityError:
                    # Skip duplicate URLs
                    continue
            conn.commit()


    def get_macro_news_api(self):
        news = []
        url = f"https://newsapi.org/v2/everything?q=Federal+Reserve+OR+inflation+OR+CPI+OR+unemployment&apiKey={os.getenv('NEWSAPI_KEY')}"
        
        try:
            response = requests.get(url).json()

            for article in response['articles']:
                news_article = {
                        "title": article["title"],
                        "description": article["description"],
                        "content": article["content"],
                        "url": article["url"],
                        "published_at": self._parse_date(article["publishedAt"])
                    }
                news.append(news_article)

            self._store_articles(news, "newsapi") 
        except KeyError:
            pass

    def get_macro_news(self):
        sources = {
            "Financial Times": "https://www.ft.com/?format=rss",
            "ForexLive": "https://www.forexlive.com/feed/"
        }
        try:
            for name, url in sources.items():
                news = []
                feed = feedparser.parse(url)
                for article in feed.entries:
                    news_article = {
                        "title": article["title"],
                        "description": article["summary"],
                        "content": "",
                        "url": article["link"],
                        "published_at": self._parse_date(article["published"])
                    }
                    news.append(news_article)
                self._store_articles(news, name)
        except Exception:
            pass

    
    def get_marketaux_news(self):
        news = []
        url = f"https://api.marketaux.com/v1/news/all?countries=global&filter_entities=true&language=en&api_token={os.getenv('MARKETAUX_KEY')}"

        try:
            response = requests.get(url).json()

            for article in response['data']:
                news_article = {
                        "title": article["title"],
                        "description": article["description"],
                        "content": "",
                        "url": article["url"],
                        "published_at": self._parse_date(article["published_at"])
                    }
                news.append(news_article)

            self._store_articles(news, "marketaux")
        except KeyError:
            pass

    def get_alphavantage_news(self):
        news = []
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&apikey={os.getenv('ALPHA_VANTAGE_KEY')}"
        
        try:
            response = requests.get(url).json()

            for article in response['feed']:
                news_article = {
                        "title": article["title"],
                        "description": article["summary"],
                        "content": "",
                        "url": article["url"],
                        "published_at": self._parse_date(article["time_published"])
                    }
                news.append(news_article)

            self._store_articles(news, "alphavantage")
        except KeyError:
            pass
    

    def get_fred_news(self):
        news = []
        url = f"https://api.stlouisfed.org/fred/releases?api_key={os.getenv('FRED_KEY')}&file_type=json"
        

        try:
            response = requests.get(url).json()
            
            for article in response['releases']:
                news_article = {
                                "title": article.get("name", ""),         
                                "description": article.get("notes", ""),  
                                "content": "",
                                "url": article.get("link", ""),            
                                "published_at": self._parse_date(article.get("realtime_start", ""))
                                #"published_at": self._parse_date(datetime.now())
                                }   
                news.append(news_article)
            self._store_articles(news, "FRED")
        except Exception as e:
            pass


    def get_latest_news(self, limit: int = 100) -> list[dict]:
        self.get_macro_news_api()
        self.get_macro_news()
        self.get_marketaux_news()
        self.get_alphavantage_news()
        self.get_fred_news()

        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM articles 
                ORDER BY published_at DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    

    def search_articles(self, search_term: str, limit: int = 20, source: str = None, after_date: str = None) -> list[dict]:
        """
        Search articles across title, description, and content
        Returns articles containing the search term (case-insensitive)
        """
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM articles 
                WHERE 
                    (title LIKE ? OR 
                    description LIKE ? OR 
                    content LIKE ?)
            """
            params = [f"%{search_term}%"] * 3
            
            # Add optional filters
            if source:
                query += " AND source = ?"
                params.append(source)
                
            if after_date:
                query += " AND published_at >= ?"
                params.append(after_date)
                
            query += " ORDER BY published_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    

    def _parse_date(self, date_str: str) -> str:
        """
        Parse various date formats into standardized ISO 8601 format.
        Returns current UTC time if parsing fails.
        """
        if not date_str:
            return datetime.now().isoformat() + "Z"
        
        try:
            # Parse with dateutil.parser (handles most common formats)
            dt = parser.parse(date_str)
            
            # Convert to UTC if timezone-aware
            if dt.tzinfo is not None:
                dt = dt.astimezone(pytz.UTC)
            else:
                # Assume UTC if no timezone specified
                dt = dt.replace(tzinfo=pytz.UTC)
            
            return dt.isoformat().replace("+00:00", "Z")
        except (ValueError, TypeError):
            return datetime.now().isoformat() + "Z"


test = NewsFeed()
#test.get_fred_news()
#print(x[0])
#x = test.get_macro_news_api()
#print(x[0])


"""
from rich.console import Console
from rich.panel import Panel
import time 




console = Console()

def display_news():
    test = NewsFeed()
    test.get_macro_news_api() 
    test.get_macro_news()

    news_array = test.get_latest_news(limit=100)
    for news in news_array:
        #console.print("[bold orange3]" + news["title"])
        console.print(Panel.fit(news["description"], title=news["title"], subtitle=news["url"]), style="bold orange3")


while True:
    display_news()
    time.sleep(90)
"""