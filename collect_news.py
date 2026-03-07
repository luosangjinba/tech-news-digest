#!/usr/bin/env python3
"""
Tech News Digest - 采集 AI、机器人、生物医药、航天科技 新闻
来源: GitHub Trending, Reddit, Hacker News
"""

import os
import requests
import json
from datetime import datetime, timedelta
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

# 关键词配置
KEYWORDS = {
    "AI": ["ai", "llm", "gpt", "model", "ml", "machine learning", "neural", "gemma", "claude", "openai", "deepseek", "chatgpt", "anthropic", "mistral"],
    "Robotics": ["robot", "drone", "automation", "autonomous", "ros", "humanoid", "boston dynamics"],
    "Biotech": ["gene", "drug", "bio", "crispr", "protein", "clinical", "vaccine", "mrna", "biotech", "genome"],
    "Space": ["space", "rocket", "nasa", "spacex", "satellite", "mars", "launch", "asteroid", "starlink", "blue origin"]
}

OUTPUT_DIR = "digests"

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

def get_github_trending():
    """获取 GitHub 新热门仓库"""
    url = "https://api.github.com/search/repositories"
    params = {
        "q": "created:>2026-02-01",
        "sort": "stars",
        "order": "desc",
        "per_page": 30
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("items", [])
    except Exception as e:
        print(f"  Error: {e}")
    return []

def get_reddit_hot(subreddit, limit=15):
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

def get_hacker_news(limit=20):
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

def format_telegram(data, date_str):
    """生成 Telegram 消息"""
    msg = f"📡 <b>Tech News Digest</b> - {date_str}\n\n"
    
    # GitHub
    msg += "🔥 <b>GitHub</b>\n"
    for repo in data.get("github", [])[:5]:
        name = repo.get("name", "")[:25]
        stars = repo.get("stargazers_count", 0)
        msg += f"• {name} ⭐{stars}\n"
    msg += "\n"
    
    # Reddit
    for category, posts in data.get("reddit", {}).items():
        emoji = {"AI": "🤖", "Robotics": "🦾", "Biotech": "🧬", "Space": "🚀"}.get(category, "📱")
        msg += f"{emoji} <b>{category}</b>\n"
        for post in posts[:3]:
            title = post.get("title", "")[:50]
            score = post.get("score", 0)
            if score > 0:
                msg += f"• {title} ({score}⬆)\n"
        msg += "\n"
    
    # HN
    msg += "📰 <b>HN</b>\n"
    for post in data.get("hn", [])[:3]:
        title = post.get("title", "")[:50]
        score = post.get("score", 0)
        if score > 30:
            msg += f"• {title} ({score}⬆)\n"
    
    msg += f"\n<a href='https://luosangjinba.github.io/tech-news-digest/'>🌐 Web</a>"
    return msg

def format_day_md(data, date_str):
    """生成单日 Markdown"""
    md = []
    md.append(f"# {date_str}")
    md.append("")
    md.append("## 🔥 GitHub Trending")
    md.append("")
    for repo in data.get("github", [])[:10]:
        name = repo.get("name", "")
        desc = repo.get("description", "")[:80] if repo.get("description") else "无描述"
        stars = repo.get("stargazers_count", 0)
        url = repo.get("html_url", "")
        md.append(f"- [{name}]({url}) ⭐{stars}")
        md.append(f"  - {desc}")
    md.append("")
    
    md.append("## 📱 Reddit")
    for category, posts in data.get("reddit", {}).items():
        md.append(f"### {category}")
        for post in posts[:5]:
            title = post.get("title", "")
            url = post.get("url", "")
            score = post.get("score", 0)
            md.append(f"- [{title}]({url}) ({score}⬆)")
        md.append("")
    
    md.append("## 📰 Hacker News")
    for post in data.get("hn", [])[:10]:
        title = post.get("title", "")
        url = post.get("url", "")
        score = post.get("score", 0)
        md.append(f"- [{title}]({url}) ({score}⬆)")
    md.append("")
    
    return "\n".join(md)

def update_index(dates):
    """更新索引文件"""
    md = ["# Tech News Digest", ""]
    md.append("> 聚焦: AI | 机器人 | 生物医药 | 航天科技")
    md.append("")
    md.append("## 按日期")
    md.append("")
    for d in sorted(dates, reverse=True):
        md.append(f"- [{d}](digests/{d}.md)")
    md.append("")
    md.append("---")
    md.append("*由 GitHub Actions 自动生成*")
    
    with open("index.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md))

def main():
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    
    print(f"📡 采集 {date_str} 新闻...")
    
    data = {
        "github": [],
        "reddit": defaultdict(list),
        "hn": []
    }
    
    # GitHub
    print("  - GitHub...")
    trending = get_github_trending()
    # 按关键词过滤
    all_ai_keywords = KEYWORDS["AI"] + KEYWORDS["Robotics"] + KEYWORDS["Biotech"] + KEYWORDS["Space"]
    data["github"] = filter_by_keywords(trending, all_ai_keywords)[:10]
    
    # Reddit
    print("  - Reddit...")
    for category, subreddits in REDDIT_SUBREDDITS.items():
        for sub in subreddits:
            posts = get_reddit_hot(sub, limit=20)
            filtered = filter_by_keywords(posts, KEYWORDS.get(category, []))
            data["reddit"][category].extend(filtered[:5])
    
    # Hacker News
    print("  - Hacker News...")
    hn_posts = get_hacker_news(30)
    hn_keywords = KEYWORDS["AI"] + KEYWORDS["Robotics"] + KEYWORDS["Biotech"] + KEYWORDS["Space"]
    data["hn"] = filter_by_keywords(hn_posts, hn_keywords)[:10]
    
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 保存单日文件
    day_file = f"{OUTPUT_DIR}/{date_str}.md"
    with open(day_file, "w", encoding="utf-8") as f:
        f.write(format_day_md(data, date_str))
    print(f"✅ 已保存 {day_file}")
    
    # 更新索引
    existing_dates = [f.replace(".md", "") for f in os.listdir(OUTPUT_DIR) if f.endswith(".md")]
    update_index(existing_dates)
    print("✅ 已更新 index.md")
    
    # 发送到 Telegram
    print("📨 发送到 Telegram...")
    tg_msg = format_telegram(data, date_str)
    result = send_telegram_message(tg_msg)
    if result and result.get("ok"):
        print("✅ Telegram 消息已发送")
    else:
        print("⚠️ Telegram 发送失败")

if __name__ == "__main__":
    main()
