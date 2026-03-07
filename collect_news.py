#!/usr/bin/env python3
"""
Tech News Digest - 采集 AI、机器人、生物医药、航天科技 新闻
来源: GitHub Trending, Reddit, Hacker News
"""

import requests
import json
from datetime import datetime
from collections import defaultdict

# 配置
REDDIT_SUBREDDITS = {
    "AI": ["MachineLearning", "LocalLLaMA", "Artificial", "singularity"],
    "Robotics": ["robotics", " robotics", "ROS"],
    "Biotech": ["biotechnology", "labrats", "medicine", "biology"],
    "Space": ["space", "SpaceX", "rocketlab", "NASA"]
}

HN_CATEGORIES = ["ai", "programming", "hardware", "biology", "space"]

OUTPUT_FILE = "daily_digest.md"

def get_github_trending(language="", since="daily"):
    """获取 GitHub Trending"""
    # 使用 GitHub API 搜索近期仓库
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
    url = f"https://hacker-news.firebaseio.com/v0/topstories.json"
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
        md.append(f"   - ⭐ {repo.get('stars', '')} | 👤 {repo.get('author', '')}")
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
                "AI": ["ai", "llm", "gpt", "model", "ml", "machine learning", "neural", "gemma", "claude", "openai"],
                "Robotics": ["robot", "drone", "automation", "autonomous", "ros"],
                "Biotech": ["gene", "drug", "bio", "crispr", "protein", "clinical", "vaccine"],
                "Space": ["space", "rocket", "nasa", "spacex", "satellite", "mars", "launch"]
            }
            filtered = filter_by_keywords(posts, keywords.get(category, []))
            data["reddit"][category].extend(filtered[:5])
    
    # Hacker News
    print("  - Hacker News...")
    hn_posts = get_hacker_news(20)
    # 简单过滤
    hn_keywords = ["ai", "llm", "robot", "space", "nasa", "bio", "gene", "rocket"]
    data["hn"] = filter_by_keywords(hn_posts, hn_keywords)[:10]
    
    # 生成 Markdown
    print("📝 生成报告...")
    md_content = format_markdown(data)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print(f"✅ 已保存到 {OUTPUT_FILE}")
    print("\n" + md_content[:500] + "...")

if __name__ == "__main__":
    main()
