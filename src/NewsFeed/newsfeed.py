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


    def get_macro_news_api(self, number_of_headlines=20):
        news = []
        url = f"https://newsapi.org/v2/everything?q=Federal+Reserve+OR+inflation+OR+CPI+OR+unemployment&apiKey={os.getenv('NEWSAPI_KEY')}"
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

        #return news[:number_of_headlines]
    

    def get_macro_news(self, number_of_headlines=10):
        news = []
        sources = {
            "Financial Times": "https://www.ft.com/?format=rss",
            "ForexLive": "https://www.forexlive.com/feed/"
        }
        for _, url in sources.items():
            feed = feedparser.parse(url)
            for article in feed.entries[:number_of_headlines]:
                news_article = {
                    "title": article["title"],
                    "description": article["summary"],
                    "content": "",
                    "url": article["link"],
                    "published_at": self._parse_date(article["published"])
                }
                news.append(news_article)

        #return news

    
    def get_latest_news(self, limit: int = 10) -> list[dict]:
        """Fetch the most recent news articles from the database"""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM articles 
                ORDER BY published_at DESC 
                LIMIT ?
            """, (limit,))
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


#test = NewsFeed()
#x = test.get_macro_news_api()
#print(x[0])
#x = test.get_macro_news_api()
#print(x[0])


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
