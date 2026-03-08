#!/usr/bin/env python3
"""
新闻获取脚本 - 从多个数据源获取科技新闻
"""
import os
import json
import requests
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    import feedparser
except ImportError:
    import subprocess
    subprocess.run(['pip', 'install', 'feedparser'])
    import feedparser

# 新闻源配置
NEWS_SOURCES = {
    'ai': [
        {'name': 'Hacker News', 'url': 'https://hnrss.org/frontpage'},
        {'name': 'TechCrunch', 'url': 'https://techcrunch.com/feed/'},
    ],
    'robotics': [
        {'name': 'IEEE Spectrum', 'url': 'https://spectrum.ieee.org/feeds/atom.xml'},
        {'name': 'The Robot Report', 'url': 'https://www.therobotreport.com/feed/'},
    ],
    'biotech': [
        {'name': 'ScienceDaily', 'url': 'https://www.sciencedaily.com/rss/all.xml'},
        {'name': 'BioSpace', 'url': 'https://www.biospace.com/feed/'},
    ],
    'aerospace': [
        {'name': 'NASA', 'url': 'https://www.nasa.gov/rss/dyn/breaking_news.rss'},
        {'name': 'Space.com', 'url': 'https://www.space.com/feeds/all'},
    ],
}

# 关键词过滤
KEYWORDS = {
    'ai': ['AI', 'artificial intelligence', 'machine learning', 'deep learning', 'GPT', 'LLM', 'neural', 'OpenAI', 'Google AI', 'Microsoft AI', 'anthropic', 'Claude', 'ChatGPT', 'robot', 'automation'],
    'robotics': ['robot', 'robotics', 'drone', 'automation', 'humanoid', 'Boston Dynamics', 'quadruped', 'autonomous'],
    'biotech': ['biotech', 'biotechnology', 'drug', 'clinical trial', 'vaccine', 'gene', 'CRISPR', 'FDA', 'pharmaceutical', 'medicine', 'health'],
    'aerospace': ['space', 'NASA', 'SpaceX', 'rocket', 'satellite', 'Mars', 'astronaut', 'ISS', 'launch', 'aerospace'],
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NEWS_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'news')

def fetch_feed(url, source_name):
    """获取RSS源"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        return resp.text
    except Exception as e:
        print(f"获取 {source_name} 失败: {e}")
        return None

def parse_feed(xml_text, source_name):
    """解析RSS"""
    items = []
    try:
        feed = feedparser.parse(xml_text)
        for entry in feed.entries[:15]:
            title = entry.get('title', '').strip()
            link = entry.get('link', '').strip()
            if title and link:
                items.append({
                    'title': title,
                    'link': link,
                    'source': source_name
                })
    except Exception as e:
        print(f"解析 {source_name} 失败: {e}")
    
    return items

def filter_by_keywords(items, category):
    """根据关键词过滤"""
    if category not in KEYWORDS:
        return items[:10]
    
    filtered = []
    for item in items:
        title_lower = item['title'].lower()
        for keyword in KEYWORDS[category]:
            if keyword.lower() in title_lower:
                filtered.append(item)
                break
    
    return filtered[:10] if filtered else items[:10]

def fetch_category_news(category):
    """获取某个分类的新闻"""
    print(f"\n获取 {category} 新闻...")
    all_items = []
    
    if category not in NEWS_SOURCES:
        print(f"未知分类: {category}")
        return []
    
    for source in NEWS_SOURCES[category]:
        xml = fetch_feed(source['url'], source['name'])
        if xml:
            items = parse_feed(xml, source['name'])
            all_items.extend(items)
            print(f"  {source['name']}: {len(items)} 条")
    
    # 去重
    seen = set()
    unique_items = []
    for item in all_items:
        if item['link'] not in seen:
            seen.add(item['link'])
            unique_items.append(item)
    
    # 关键词过滤
    filtered = filter_by_keywords(unique_items, category)
    
    # 取前10条
    return filtered[:10]

def save_news(category, items):
    """保存新闻到文件"""
    today = datetime.now().strftime('%Y-%m-%d')
    date_dir = os.path.join(NEWS_DIR, today)
    os.makedirs(date_dir, exist_ok=True)
    
    file_path = os.path.join(date_dir, f'{category}.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    
    print(f"已保存 {len(items)} 条到 {file_path}")
    return file_path

def main():
    """主函数"""
    print("=" * 50)
    print("科技新闻获取")
    print("=" * 50)
    
    categories = ['ai', 'robotics', 'biotech', 'aerospace']
    
    all_news = {}
    for cat in categories:
        items = fetch_category_news(cat)
        all_news[cat] = items
        save_news(cat, items)
    
    print("\n" + "=" * 50)
    print(f"完成！共获取 {sum(len(v) for v in all_news.values())} 条新闻")
    print("=" * 50)

if __name__ == "__main__":
    main()
