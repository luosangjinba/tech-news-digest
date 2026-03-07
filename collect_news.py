#!/usr/bin/env python3
"""
Tech News Digest - 采集 AI、机器人、生物医药、航天科技 新闻
来源: GitHub Trending, Reddit, Hacker News
"""

import os
import requests
import json
from datetime import datetime
from collections import defaultdict

# 配置
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8644933224:AAGI5L37e6JZP1Vxd_3NmyZNYkbbDN1pxxg")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "6276858705")

REDDIT_SUBREDDITS = {
    "AI": ["MachineLearning", "LocalLLaMA", "Artificial", "singularity"],
    "Robotics": ["robotics", "robotics", "ROS"],
    "Biotech": ["biotechnology", "labrats", "medicine", "biology"],
    "Space": ["space", "SpaceX", "rocketlab", "NASA"]
}

HN_CATEGORIES = ["ai", "programming", "hardware", "biology", "space"]

OUTPUT_FILE = "daily_digest.md"

def send_telegram_message(message):
    """发送 Telegram 消息"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true"
    }
    try:
        resp = requests.post(url, json=data, timeout=10)
        return resp.json()
    except Exception as e:
        print(f" Telegram error: {e}")
        return None

def get_github_trending(language="", since="daily"):
    """获取 GitHub Trending"""
    url = "https://api.github.com/search/repositories"
    params = {
        "q": "created:>2026-03-01",
        "sort": "stars",
        "order": "desc",
        "per_page": 20
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("items", [])
    except Exception as e:
        print(f"  Error: {e}")
    return []

def get_reddit_hot(subreddit, limit=10):
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
                    "score": post.get("score", 0),
                    "url": post.get("url", ""),
                    "comments": post.get("num_comments", 0),
                    "subreddit": subreddit
                })
            return posts
    except:
        pass
    return []

def get_hacker_news(limit=10):
    """获取 Hacker News Top"""
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
                        "score": item.get("score", 0),
                        "url": item.get("url", ""),
                        "by": item.get("by", "")
                    })
            return posts
    except:
        pass
    return []

def filter_by_keywords(items, keywords):
    """根据关键词过滤"""
    filtered = []
    for item in items:
        title = item.get("title", "").lower()
        if any(kw.lower() in title for kw in keywords):
            filtered.append(item)
    return filtered

def format_telegram(data):
    """生成 Telegram 消息"""
    msg = "📡 <b>Tech News Digest</b>\n"
    msg += f"<i>{datetime.now().strftime('%Y-%m-%d')}</i>\n\n"
    
    # GitHub Trending
    msg += "🔥 <b>GitHub Trending</b>\n"
    for repo in data.get("github", [])[:5]:
        name = repo.get("name", "")[:30]
        desc = repo.get("description", "")[:50] if repo.get("description") else ""
        stars = repo.get("stargazers_count", 0)
        msg += f"• {name} ⭐{stars}\n"
    msg += "\n"
    
    # Reddit
    msg += "📱 <b>Reddit</b>\n"
    for category, posts in data.get("reddit", {}).items():
        emoji = {"AI": "🤖", "Robotics": "🦾", "Biotech": "🧬", "Space": "🚀"}.get(category, "📱")
        msg += f"{emoji} <b>{category}</b>\n"
        for post in posts[:3]:
            title = post.get("title", "")[:60]
            score = post.get("score", 0)
            if score > 0:
                msg += f"• {title} (⬆️{score})\n"
        msg += "\n"
    
    # Hacker News
    msg += "📰 <b>Hacker News</b>\n"
    for post in data.get("hn", [])[:3]:
        title = post.get("title", "")[:60]
        score = post.get("score", 0)
        if score > 50:
            msg += f"• {title} (⬆️{score})\n"
    
    msg += f"\n<a href='https://github.com/luosangjinba/tech-news-digest'>GitHub</a>"
    return msg

def format_markdown(data):
    """生成 Markdown 格式"""
    md = []
    md.append(f"# Tech News Digest - {datetime.now().strftime('%Y-%m-%d')}")
    md.append("")
    md.append("> 聚焦: AI | 机器人 | 生物医药 | 航天科技")
    md.append("")
    md.append("---")
    md.append("")
    
    # GitHub Trending
    md.append("## 🔥 GitHub Trending")
    md.append("")
    trending = data.get("github", [])
    for i, repo in enumerate(trending[:10], 1):
        md.append(f"{i}. **{repo.get('name', '')}** - {repo.get('description', '')[:80]}")
        md.append(f"   - ⭐ {repo.get('stargazers_count', 0)} | 👤 {repo.get('owner', {}).get('login', '')}")
    md.append("")
    
    # Reddit
    md.append("## 📱 Reddit Hot")
    md.append("")
    for category, posts in data.get("reddit", {}).items():
        md.append(f"### {category}")
        for post in posts[:5]:
            md.append(f"- [{post.get('title', '')}]({post.get('url', '')}) (⬆️ {post.get('score', 0)})")
        md.append("")
    
    # Hacker News
    md.append("## 📰 Hacker News")
    md.append("")
    for post in data.get("hn", [])[:10]:
        md.append(f"- [{post.get('title', '')}]({post.get('url', '')}) (⬆️ {post.get('score', 0)})")
    md.append("")
    
    md.append("---")
    md.append(f"*Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    return "\n".join(md)

def main():
    print("📡 采集新闻数据...")
    
    data = {
        "github": [],
        "reddit": defaultdict(list),
        "hn": []
    }
    
    # GitHub Trending
    print("  - GitHub Trending...")
    trending = get_github_trending()
    data["github"] = trending[:10]
    
    # Reddit
    print("  - Reddit...")
    for category, subreddits in REDDIT_SUBREDDITS.items():
        for sub in subreddits:
            posts = get_reddit_hot(sub, limit=15)
            # 简单关键词过滤
            keywords = {
                "AI": ["ai", "llm", "gpt", "model", "ml", "machine learning", "neural", "gemma", "claude", "openai", "gemma", "deepseek"],
                "Robotics": ["robot", "drone", "automation", "autonomous", "ros", "humanoid"],
                "Biotech": ["gene", "drug", "bio", "crispr", "protein", "clinical", "vaccine", "mrna"],
                "Space": ["space", "rocket", "nasa", "spacex", "satellite", "mars", "launch", "asteroid"]
            }
            filtered = filter_by_keywords(posts, keywords.get(category, []))
            data["reddit"][category].extend(filtered[:5])
    
    # Hacker News
    print("  - Hacker News...")
    hn_posts = get_hacker_news(20)
    # 简单过滤
    hn_keywords = ["ai", "llm", "robot", "space", "nasa", "bio", "gene", "rocket", "ml"]
    data["hn"] = filter_by_keywords(hn_posts, hn_keywords)[:10]
    
    # 生成 Markdown
    print("📝 生成报告...")
    md_content = format_markdown(data)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    # 发送到 Telegram
    print("📨 发送到 Telegram...")
    tg_msg = format_telegram(data)
    result = send_telegram_message(tg_msg)
    if result and result.get("ok"):
        print("✅ Telegram 消息已发送")
    else:
        print("⚠️ Telegram 发送失败")
    
    print(f"✅ 已保存到 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
