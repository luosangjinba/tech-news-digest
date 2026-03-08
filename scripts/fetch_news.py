#!/usr/bin/env python3
"""
新闻获取脚本 - 投资/商业新闻
"""
import os
import json
import requests
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    import feedparser
except ImportError:
    import subprocess
    subprocess.run(['pip', 'install', 'feedparser'])
    import feedparser

# 更稳定的英文财经/投资源
NEWS_SOURCES = {
    'tech': [
        {'name': 'TechCrunch', 'url': 'https://techcrunch.com/feed/'},
        {'name': 'Verge', 'url': 'https://www.theverge.com/rss/index.xml'},
        {'name': 'Wired', 'url': 'https://www.wired.com/feed/rss'},
    ],
    'finance': [
        {'name': 'Yahoo Finance', 'url': 'https://finance.yahoo.com/news/rssindex'},
        {'name': 'MarketWatch', 'url': 'https://feeds.marketwatch.com/marketwatch/topstories/'},
        {'name': 'CNBC', 'url': 'https://www.cnbc.com/id/100003114/device/rss/rss.html'},
    ],
    'invest': [
        {'name': 'Bloomberg', 'url': 'https://feeds.bloomberg.com/markets/news.rss'},
        {'name': 'Reuters Business', 'url': 'https://www.reutersagency.com/feed/?best-topics=business-finance'},
        {'name': 'WSJ', 'url': 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml'},
    ],
}

# 关键词 - 投资/商业相关
KEYWORDS = [
    'stock', 'market', 'invest', 'trading', 'earnings', 'revenue', 'profit',
    'IPO', 'funding', 'acquisition', 'merger', 'startup', 'tech', 'AI',
    'earnings', 'quarterly', 'forecast', 'guidance', 'dividend',
    'Tesla', 'Apple', 'Microsoft', 'Google', 'Amazon', 'Nvidia', 'Meta',
    'Bitcoin', 'crypto', 'Fed', 'interest rate', 'inflation',
    'China', 'economy', 'GDP', 'trade', 'tariff',
]

EXCLUDE_KEYWORDS = [
    'job', 'career', 'hiring', 'salary', 'interview',
    'tutorial', 'how to', 'review', 'opinion', 'advertisement',
]

NEWS_DIR = 'news'

def fetch_feed(url, source_name):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*'
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        return resp.text
    except Exception as e:
        print(f"Error fetching {source_name}: {e}")
        return None

def parse_feed(xml_text, source_name):
    items = []
    try:
        feed = feedparser.parse(xml_text)
        for entry in feed.entries[:25]:
            title = entry.get('title', '').strip()
            link = entry.get('link', '').strip()
            if title and link:
                items.append({
                    'title': title,
                    'link': link,
                    'source': source_name
                })
    except Exception as e:
        print(f"Error parsing {source_name}: {e}")
    return items

def filter_by_keywords(items):
    filtered = []
    for item in items:
        title = item['title'].lower()
        exclude = False
        for kw in EXCLUDE_KEYWORDS:
            if kw.lower() in title:
                exclude = True
                break
        if exclude:
            continue
        for kw in KEYWORDS:
            if kw.lower() in title:
                filtered.append(item)
                break
    return filtered[:15] if filtered else items[:10]

def fetch_category_news(category):
    print(f"\nFetching {category} news...")
    all_items = []
    
    if category not in NEWS_SOURCES:
        print(f"Unknown category: {category}")
        return []
    
    for source in NEWS_SOURCES[category]:
        xml = fetch_feed(source['url'], source['name'])
        if xml:
            items = parse_feed(xml, source['name'])
            all_items.extend(items)
            print(f"  {source['name']}: {len(items)} items")
    
    # Deduplicate
    seen = set()
    unique_items = []
    for item in all_items:
        if item['link'] not in seen:
            seen.add(item['link'])
            unique_items.append(item)
    
    filtered = filter_by_keywords(unique_items)
    return filtered[:10]

def save_news(category, items):
    today = datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(NEWS_DIR, today)
    os.makedirs(date_dir, exist_ok=True)
    
    file_path = os.path.join(date_dir, f'{category}.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(items)} items to {file_path}")
    return file_path

def main():
    print("=" * 50)
    print("Financial & Investment News Fetcher")
    print("=" * 50)
    
    categories = ['tech', 'finance', 'invest']
    
    all_news = {}
    for cat in categories:
        items = fetch_category_news(cat)
        all_news[cat] = items
        save_news(cat, items)
    
    print("\n" + "=" * 50)
    print(f"Done! Total: {sum(len(v) for v in all_news.values())} news items")
    print("=" * 50)

if __name__ == "__main__":
    main()
