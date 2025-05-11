import tkinter as tk
from tkinter import scrolledtext, Menu, Frame
from datetime import datetime
import sys
sys.path.append('/media/henning/Volume/Programming/macrotrading/src')
from NewsFeed.newsfeed import NewsFeed

class GUI():
    def __init__(self, news_feed):
        self.news_feed = news_feed

        self.search_entry = None
        self.source_var = None
        self.date_entry = None
        self.limit_var = None
        self.results_display = None
        self.search_status = None
        
        # Main Window Setup
        self.root = tk.Tk()
        self.root.title("Macro News Tracker")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)  # Minimum window size
        self.root.configure(bg="black")
        
        # Configure grid for responsive layout
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Menu Bar
        menubar = Menu(self.root)
        menubar.add_command(label="Search", command=self.open_search)
        self.root.config(menu=menubar)
        
        # Main News Display Frame (responsive)
        self.main_frame = Frame(self.root, bg="black")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # News Display with Scrollbar
        self.news_display = scrolledtext.ScrolledText(
            self.main_frame,
            bg="black",
            fg="orange",
            font=("Consolas", 12),
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        self.news_display.grid(row=0, column=0, sticky="nsew")
        
        # Status Bar
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bg="black",
            fg="gray",
            anchor=tk.W
        )
        self.status_bar.grid(row=1, column=0, sticky="ew")
        
        # Auto-Refresh Setup
        self.refresh_news()
        self.auto_refresh_id = self.root.after(300000, self.auto_refresh)  # 5 minutes
    

    def refresh_news(self):
        """Fetch and display latest news with responsive formatting"""
        self.news_display.configure(state='normal')
        self.news_display.delete(1.0, tk.END)

        articles = self.news_feed.get_latest_news(limit=100)
        max_title_width = self.calculate_max_width(articles)
        
        for article in articles:
            # Format with dynamic spacing based on window width
            title = article['title']
            description = article['description'].ljust(max_title_width)[:max_title_width]
            link = article['url']
            self.news_display.insert(
                tk.END,
                f"{self.format_date(article['published_at'])} | {article['source']}\n{title}\n{description}\n{link}\n\n",
                'article'
            )
        
        self.news_display.configure(state='disabled')
        self.status_var.set(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


    def calculate_max_width(self, articles):
        """Calculate optimal title width based on current window size"""
        avg_char_width = 8  # Approximate width of a character in pixels
        window_width = self.root.winfo_width()
        return min(
            max(len(article['title']) for article in articles),
            int((window_width - 100) / avg_char_width)
        )


    def format_date(self, date_str):
        """Convert ISO date to readable format"""
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', ''))
            return dt.strftime('%Y-%m-%d %H:%M')
        except Exception:
            return date_str[:16]


    def auto_refresh(self):
        """Auto-refresh with window size awareness"""
        self.refresh_news()
        self.root.after_cancel(self.auto_refresh_id)  # Cancel previous
        self.auto_refresh_id = self.root.after(300000, self.auto_refresh)
    

    def open_search(self):
        """Enhanced search window with filters"""
        search_win = tk.Toplevel(self.root)
        search_win.title("Advanced News Search")
        search_win.geometry("700x800")
        search_win.configure(bg="black")
        search_win.minsize(600, 700)
        
        # Grid configuration for responsiveness
        search_win.grid_rowconfigure(4, weight=1)  # Results area expands
        search_win.grid_columnconfigure(1, weight=1)
        
        # Search Term
        tk.Label(
            search_win, 
            text="Search Term:", 
            bg="black", fg="orange",
            font=("Helvetica", 10, "bold")
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        self.search_entry = tk.Entry(
            search_win, 
            width=40,
            bg="#222", fg="orange",
            insertbackground="orange"
        )
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        
        # Filters Frame
        filters_frame = tk.Frame(search_win, bg="black")
        filters_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        # Source Filter
        tk.Label(
            filters_frame, 
            text="Source:", 
            bg="black", fg="orange"
        ).grid(row=0, column=0, padx=(0,5), sticky="w")
        
        self.source_var = tk.StringVar(value="All")
        sources = ["All", "NewsAPI", "Financial Times", "ForexLive"]
        tk.OptionMenu(
            filters_frame, self.source_var, *sources
        ).config(bg="#333", fg="orange", highlightthickness=0)
        tk.OptionMenu(
            filters_frame, self.source_var, *sources
        ).grid(row=0, column=1, sticky="w")
        
        # Date Filter
        tk.Label(
            filters_frame, 
            text="After Date:", 
            bg="black", fg="orange"
        ).grid(row=1, column=0, padx=(0,5), pady=(10,0), sticky="w")
        
        self.date_entry = tk.Entry(
            filters_frame, 
            width=15,
            bg="#222", fg="orange",
            insertbackground="orange"
        )
        self.date_entry.grid(row=1, column=1, pady=(10,0), sticky="w")
        self.date_entry.insert(0, "YYYY-MM-DD")
        self.date_entry.bind("<FocusIn>", lambda e: self.date_entry.delete(0, tk.END))
        
        # Limit Results
        tk.Label(
            filters_frame, 
            text="Max Results:", 
            bg="black", fg="orange"
        ).grid(row=2, column=0, padx=(0,5), pady=(10,0), sticky="w")
        
        self.limit_var = tk.IntVar(value=20)
        tk.Spinbox(
            filters_frame,
            from_=1, to=100,
            textvariable=self.limit_var,
            width=5,
            bg="#222", fg="orange"
        ).grid(row=2, column=1, pady=(10,0), sticky="w")
        
        # Search Button
        tk.Button(
            search_win,
            text="SEARCH",
            command=self.execute_advanced_search,
            bg="#333", fg="orange",
            font=("Helvetica", 10, "bold"),
            relief=tk.FLAT
        ).grid(row=2, column=0, columnspan=2, pady=10)
        
        # Results Display
        self.results_display = scrolledtext.ScrolledText(
            search_win,
            bg="black",
            fg="orange",
            font=("Consolas", 11),
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        self.results_display.grid(row=3, column=0, columnspan=2, sticky="nsew")
        
        # Status Bar
        self.search_status = tk.StringVar()
        tk.Label(
            search_win,
            textvariable=self.search_status,
            bg="black", fg="gray",
            anchor=tk.W
        ).grid(row=4, column=0, columnspan=2, sticky="ew")


    def execute_advanced_search(self):
        """Handle search with all filters"""
        query = self.search_entry.get().strip()
        if not query:
            self.search_status.set("Error: Please enter a search term")
            return
        
        try:
            # Get filters
            source = None if self.source_var.get() == "All" else self.source_var.get()
            limit = self.limit_var.get()
            
            # Parse date (if provided)
            date_str = self.date_entry.get().strip()
            after_date = None
            if date_str and date_str != "YYYY-MM-DD":
                try:
                    datetime.strptime(date_str, "%Y-%m-%d")  # Validate format
                    after_date = date_str
                except ValueError:
                    self.search_status.set("Error: Use YYYY-MM-DD date format")
                    return
            
            # Execute search
            results = self.news_feed.search_articles(
                search_term=query,
                limit=limit,
                source=source,
                after_date=after_date
            )
            
            # Display results
            self.results_display.config(state=tk.NORMAL)
            self.results_display.delete(1.0, tk.END)
            
            if not results:
                self.results_display.insert(tk.END, "No matching articles found", "error")
            else:
                for article in results:
                    self.results_display.insert(
                        tk.END,
                        f"[{article['source']}] {article['published_at'][:10]}\n"
                        f"{article['title']}\n"
                        f"{'-'*50}\n"
                        f"{article['description'][:200]}...\n\n",
                        "result"
                    )
            
            self.search_status.set(f"Found {len(results)} results")
            
        except Exception as e:
            self.search_status.set(f"Search error: {str(e)}")
        finally:
            self.results_display.config(state=tk.DISABLED)

        
    def run(self):
        """Run the application"""
        self.root.mainloop()



if __name__ == "__main__":
    gui = GUI(news_feed=NewsFeed())
    gui.run()