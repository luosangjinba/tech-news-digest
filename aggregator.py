#!/usr/bin/env python3
"""
Tech News Aggregator - 聚合 GitHub, Reddit, Hacker News, RSS
生成美观的静态博客页面
"""

import json
import os
import requests
import feedparser
from datetime import datetime
from collections import defaultdict

# Telegram 配置
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8778530122:AAE9wK2Yu0uIGAPxvMOnvRzh_slkJ7BdLn4")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "6276858705")

# RSS 源配置
RSS_SOURCES = {
    "AI": [
        "https://jack-clark.net/import-ai/feed/",
        "https://www.deeplearning.ai/the-batch/feed/",
    ],
    "Tech": [
        "https://news.ycombinator.com/rss",
        "https://techcrunch.com/feed/",
    ],
    "Space": [
        "https://spacenews.com/feed/",
    ],
    "Bio": [
        "https://www.biospace.com/News/RSS.aspx",
    ]
}

# Reddit 社区
REDDIT_SUBREDDITS = {
    "AI": ["MachineLearning", "LocalLLaMA", "Artificial"],
    "Robotics": ["robotics"],
    "Biotech": ["biotechnology", "labrats"],
    "Space": ["space", "SpaceX"]
}

# 关键词配置
KEYWORDS = {
    "AI": ["ai", "llm", "gpt", "model", "ml", "machine learning", "neural", "gemma", "claude", "openai", "deepseek", "chatgpt", "anthropic", "mistral", "grok", "gemini"],
    "Robotics": ["robot", "drone", "automation", "autonomous", "ros", "humanoid", "boston dynamics", "tesla optimus"],
    "Biotech": ["gene", "drug", "bio", "crispr", "protein", "clinical", "vaccine", "biotech", "genome", "mrna"],
    "Space": ["space", "rocket", "nasa", "spacex", "satellite", "mars", "launch", "asteroid", "starlink", "blue origin", "starship"]
}

OUTPUT_DIR = "digests"

def get_github_trending():
    """获取 GitHub 热门仓库"""
    url = "https://api.github.com/search/repositories"
    params = {
        "q": "created:>2026-02-01",
        "sort": "stars",
        "order": "desc",
        "per_page": 20
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            items = resp.json().get("items", [])
            all_kw = KEYWORDS["AI"] + KEYWORDS["Robotics"] + KEYWORDS["Biotech"] + KEYWORDS["Space"]
            return [{"title": r.get("name", ""), "url": r.get("html_url", ""), "description": r.get("description", ""), "stars": r.get("stargazers_count", 0), "category": detect_category(r.get("name", "") + " " + r.get("description", "")), "source": "GitHub"} for r in items if any(kw in (r.get("name", "") + " " + r.get("description", "")).lower() for kw in all_kw)]
    except:
        pass
    return []

def get_reddit_hot(subreddit, limit=20):
    """获取 Reddit 热帖"""
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    headers = {"User-Agent": "TechNewsBot/1.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            posts = []
            for item in data.get("data", {}).get("children", []):
                post = item.get("data", {})
                posts.append({
                    "title": post.get("title", ""),
                    "url": post.get("url", ""),
                    "score": post.get("score", 0),
                    "comments": post.get("num_comments", 0),
                })
            return posts
    except:
        pass
    return []

def get_hacker_news(limit=30):
    """获取 Hacker News"""
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            ids = resp.json()[:limit]
            posts = []
            for item_id in ids:
                item_url = f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
                item_resp = requests.get(item_url, timeout=10)
                if item_resp.status_code == 200:
                    item = item_resp.json()
                    posts.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "score": item.get("score", 0),
                        "time": item.get("time", 0),
                        "category": "tech"
                    })
            return posts
    except:
        pass
    return []

def get_rss_feed(url):
    """获取 RSS 源"""
    try:
        feed = feedparser.parse(url)
        entries = []
        for entry in feed.entries[:10]:
            entries.append({
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "source": feed.feed.get("title", "RSS"),
                "category": "AI"
            })
        return entries
    except:
        return []

def detect_category(text):
    """检测类别"""
    text = text.lower()
    for kw in KEYWORDS["Space"]:
        if kw in text: return "space"
    for kw in KEYWORDS["Biotech"]:
        if kw in text: return "bio"
    for kw in KEYWORDS["Robotics"]:
        if kw in text: return "robotics"
    return "AI"

def filter_by_keywords(items, category):
    """关键词过滤"""
    keywords = KEYWORDS.get(category, [])
    filtered = []
    for item in items:
        title = item.get("title", "").lower()
        if any(kw.lower() in title for kw in keywords):
            item["category"] = category
            filtered.append(item)
    return filtered

def send_telegram(msg):
    """发送 Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": "true"}
    try:
        requests.post(url, json=data, timeout=10)
    except:
        pass

def generate_html(news_list):
    """生成 HTML"""
    # 读取模板
    with open("templates/index.html", "r", encoding="utf-8") as f:
        html = f.read()
    
    # 准备新闻数据
    news_json = json.dumps(news_list[:30], ensure_ascii=False)
    html = html.replace("{{NEWS_DATA}}", news_json)
    
    return html

def main():
    print("📡 采集新闻数据...")
    all_news = []
    
    # GitHub
    print("  - GitHub Trending...")
    github_news = get_github_trending()
    all_news.extend(github_news[:5])
    
    # Reddit
    print("  - Reddit...")
    for category, subreddits in REDDIT_SUBREDDITS.items():
        for sub in subreddits:
            posts = get_reddit_hot(sub, limit=25)
            filtered = filter_by_keywords(posts, category)
            for p in filtered[:3]:
                p["source"] = f"Reddit/{sub}"
                p["category"] = category
            all_news.extend(filtered[:3])
    
    # Hacker News
    print("  - Hacker News...")
    hn_posts = get_hacker_news(30)
    all_kw = KEYWORDS["AI"] + KEYWORDS["Robotics"] + KEYWORDS["Biotech"] + KEYWORDS["Space"]
    for p in hn_posts:
        if any(kw in p.get("title", "").lower() for kw in all_kw):
            p["source"] = "Hacker News"
            p["category"] = detect_category(p.get("title", ""))
    all_news.extend([p for p in hn_posts if any(kw in p.get("title", "").lower() for kw in all_kw)][:5])
    
    # RSS
    print("  - RSS Feeds...")
    for category, urls in RSS_SOURCES.items():
        for url in urls:
            entries = get_rss_feed(url)
            for e in entries[:3]:
                e["category"] = category
            all_news.extend(entries[:3])
    
    # 按热度排序
    all_news.sort(key=lambda x: x.get("score", x.get("stars", 0)), reverse=True)
    
    print(f"✅ 共采集 {len(all_news)} 条新闻")
    
    # 保存每日 markdown
    date_str = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(f"{OUTPUT_DIR}/{date_str}.json", "w", encoding="utf-8") as f:
        json.dump(all_news[:50], f, ensure_ascii=False, indent=2)
    
    # 生成 HTML
    html = generate_html(all_news)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ 已生成 index.html")
    
    # 发送 Telegram
    msg = f"📡 <b>Tech News Digest</b> - {date_str}\n\n"
    for i, news in enumerate(all_news[:10], 1):
        title = news.get("title", "")[:50]
        score = news.get("score", news.get("stars", 0))
        emoji = {"AI": "🤖", "robotics": "🦾", "bio": "🧬", "space": "🚀", "tech": "💻"}.get(news.get("category", "AI"), "📰")
        msg += f"{emoji} {i}. {title}\n"
    
    msg += f"\n🌐 <a href='https://luosangjinba.github.io/tech-news-digest/'>查看完整页面</a>"
    send_telegram(msg)
    print("✅ 已发送到 Telegram")

if __name__ == "__main__":
    main()
