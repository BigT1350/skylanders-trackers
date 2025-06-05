import requests
import sqlite3
import smtplib
from datetime import datetime

# CONFIGURATION (Edit these!)
CONFIG = {
    "EBAY_API_KEY": "TristenJ-skylande-PRD-d377d0d67-a193bdd0",  # From developer.ebay.com
    "SKYLANDERS": [
        {"name": "chrome spyro", "max_price": 250, "keywords": "chrome spyro skylander", "must_include": ["chrome", "spyro"]},
        {"name": "crystal clear cynder", "max_price": 250, "keywords": "crystal clear cynder skylander", "must_include": ["crystal", "cynder"]},
        {"name": "crystal clear stealth elf", "max_price": 250, "keywords": "crystal clear stealth elf skylander", "must_include": ["crystal", "elf"]},
        {"name": "crystal clear wham-shell", "max_price": 250, "keywords": "crystal clear wham-shell skylander", "must_include": ["crystal", "wham"]},
        {"name": "crystal clear whirlwind", "max_price": 250, "keywords": "crystal clear whirlwind skylander", "must_include": ["crystal", "whirlwind"]},
        {"name": "flocked stump smash", "max_price": 100, "keywords": "flocked stump smash skylander", "must_include": ["flocked", "stump"]},
        {"name": "glow in the dark warnado", "max_price": 250, "keywords": "glow in the dark warnado skylander", "must_include": ["glow", "warnado"]},
        {"name": "glow in the dark wrecking ball", "max_price": 250, "keywords": "glow in the dark wrecking ball skylander", "must_include": ["glow", "wrecking"]},
        {"name": "glow in the dark zap", "max_price": 250, "keywords": "glow in the dark zap skylander", "must_include": ["glow", "zap"]},
        {"name": "gold chop chop", "max_price": 250, "keywords": "gold chop chop skylander", "must_include": ["gold", "chop"]},
        {"name": "gold drill sergeant", "max_price": 250, "keywords": "gold drill sergeant skylander", "must_include": ["gold", "drill"]},
        {"name": "gold flameslinger", "max_price": 250, "keywords": "gold flameslinger skylander", "must_include": ["gold", "flame"]},
        {"name": "metallic purple cynder", "max_price": 250, "keywords": "metallic purple cynder skylander", "must_include": ["purple", "cynder"]},
        {"name": "pearl hex", "max_price": 250, "keywords": "pearl hex skylander", "must_include": ["pearl", "hex"]},
        {"name": "red camo", "max_price": 250, "keywords": "red camo skylander", "must_include": ["red", "camo"]},
        {"name": "silver boomer", "max_price": 250, "keywords": "silver boomer skylander", "must_include": ["silver", "boomer"]},
        {"name": "silver dino-rang", "max_price": 250, "keywords": "silver dino-rang skylander", "must_include": ["silver", "dino"]},
        {"name": "silver eruptor", "max_price": 250, "keywords": "silver eruptor skylander", "must_include": ["silver", "eruptor"]}
    ],
    "BLACKLIST": ["poster", "handmade", "digital", "card"],  # Auto-reject these
    "EMAIL": {
        "enabled": True,
        "sender": "gertbimbanos1350@gmail.com",
        "password": "ptovezdiebowsond",  # 2FA required
        "recipient": "gertbimbanos1350@gmail.com"
    },
    "CHECK_INTERVAL": 3600  # Seconds (1 hour)
}

class SkylandersTracker:
    def __init__(self):
        self.db = sqlite3.connect("skylanders.db")
        self._init_db()
        
    def _init_db(self):
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id TEXT PRIMARY KEY,
            skylander TEXT,
            price REAL,
            title TEXT,
            url TEXT,
            status TEXT DEFAULT 'new',
            last_checked TIMESTAMP
        )
        """)
        self.db.commit()

    def fetch_ebay_listings(self):
        for skylander in CONFIG["SKYLANDERS"]:
            params = {
                "q": skylander["keywords"],
                "filter": f"price:[0..{skylander['max_price']}]",
                "sort": "newlyListed",
                "limit": 5
            }
            headers = {"Authorization": f"Bearer {CONFIG['EBAY_API_KEY']}"}
            
            try:
                res = requests.get(
                    "https://api.ebay.com/buy/browse/v1/item_summary/search",
                    headers=headers,
                    params=params
                )
                if res.status_code == 200:
                    self.process_listings(res.json(), skylander)
            except Exception as e:
                print(f"Error fetching {skylander['name']}: {str(e)}")

    def process_listings(self, data, skylander):
        for item in data.get("itemSummaries", []):
            if any(bad in item["title"].lower() for bad in CONFIG["BLACKLIST"]):
                continue
                
            if not all(kw.lower() in item["title"].lower() for kw in skylander["must_include"]):
                continue
                
            self.db.execute("""
            INSERT OR IGNORE INTO listings (id, skylander, price, title, url)
            VALUES (?, ?, ?, ?, ?)
            """, (
                item["itemId"],
                skylander["name"],
                float(item["price"]["value"]),
                item["title"],
                item["itemWebUrl"]
            ))
            self.db.commit()
            
            cursor = self.db.execute(
                "SELECT status FROM listings WHERE id = ?", 
                (item["itemId"],)
            if cursor.fetchone()[0] == "new":
                self.send_alert(item, skylander["name"])

    def send_alert(self, item, skylander_name):
        message = f"""New {skylander_name} found!
Price: ${item['price']['value']}
Title: {item['title']}
Link: {item['itemWebUrl']}
"""
        if CONFIG["EMAIL"]["enabled"]:
            try:
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(
                        CONFIG["EMAIL"]["sender"],
                        CONFIG["EMAIL"]["password"]
                    )
                    server.sendmail(
                        CONFIG["EMAIL"]["sender"],
                        CONFIG["EMAIL"]["recipient"],
                        f"Subject: 🚨 Skylander Alert!\n\n{message}"
                    )
            except Exception as e:
                print(f"Email failed: {str(e)}")

if __name__ == "__main__":
    import time
    tracker = SkylandersTracker()
    while True:
        tracker.fetch_ebay_listings()
        time.sleep(CONFIG["CHECK_INTERVAL"])
