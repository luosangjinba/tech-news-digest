#!/usr/bin/env python3
"""
Telegram 推送脚本
"""
import os
import sys
import json
import requests
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 从环境变量获取配置
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

CATEGORY_NAMES = {
    'ai': '🤖 AI 人工智能',
    'robotics': '🦾 机器人',
    'biotech': '🧬 生物医药',
    'aerospace': '🚀 航空航天',
}

def send_telegram_message(message):
    """发送Telegram消息"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram配置未设置")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": "false"
    }
    
    try:
        resp = requests.post(url, json=data, timeout=30)
        if resp.status_code == 200:
            print("推送成功")
            return True
        else:
            print(f"推送失败: {resp.text}")
            return False
    except Exception as e:
        print(f"推送异常: {e}")
        return False

def load_news(category, date=None):
    """加载新闻"""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    news_file = os.path.join(SCRIPT_DIR, '..', 'news', date, f'{category}.json')
    
    if not os.path.exists(news_file):
        return []
    
    with open(news_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_news_for_push(news, category, max_items=10):
    """格式化新闻为推送消息"""
    if not news:
        return ""
    
    title = f"\n{CATEGORY_NAMES.get(category, category)}\n"
    lines = [title]
    
    # 取前几条
    for i, item in enumerate(news[:max_items], 1):
        title_zh = item.get('title_zh', item.get('title', ''))
        link = item.get('link', '')
        lines.append(f"{i}. <a href=\"{link}\">{title_zh}</a>")
    
    return '\n'.join(lines)

def push_daily_summary(hours=24):
    """推送每日汇总"""
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    
    message = f"📰 科技新闻汇总 ({hours}小时内)\n"
    message += f"⏰ 更新时间: {now.strftime('%H:%M')}\n"
    message += "=" * 30 + "\n"
    
    categories = ['ai', 'robotics', 'biotech', 'aerospace']
    total = 0
    
    for cat in categories:
        news = load_news(cat, today)
        if news:
            total += len(news)
            message += format_news_for_push(news, cat, 10)
            message += "\n"
    
    message += "=" * 30 + "\n"
    message += f"📊 共 {total} 条新闻\n"
    message += f"🌐 查看完整: https://luosangjinba.github.io/tech-news-digest/"
    
    send_telegram_message(message)

def push_hourly_update():
    """推送每小时更新（最近1小时）"""
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # 获取最近1小时的新闻
    message = f"🕐 每小时新闻速递\n"
    message += f"⏰ {now.strftime('%H:%M')}\n"
    message += "=" * 30 + "\n"
    
    categories = ['ai', 'robotics', 'biotech', 'aerospace']
    total = 0
    
    for cat in categories:
        # 尝试加载今天的和昨天的新闻
        news_today = load_news(cat, today)
        news_yesterday = load_news(cat, yesterday)
        news = news_today + news_yesterday
        
        if news:
            total += len(news)
            message += format_news_for_push(news, cat, 5)
            message += "\n"
    
    if total > 0:
        message += "=" * 30 + "\n"
        message += f"📊 共 {total} 条新闻\n"
        send_telegram_message(message)

def push_github_trending():
    """推送 GitHub 热门项目"""
    try:
        import urllib.request
        url = "https://api.github.com/search/repositories?q=created:>2024-01-01&sort=stars&order=desc"
        req = urllib.request.Request(url, headers={'Accept': 'application/vnd.github.v3+json'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read())
        
        repos = data.get('items', [])[:10]
        
        message = "⭐ GitHub 热门项目\n"
        message += "=" * 30 + "\n"
        
        for i, repo in enumerate(repos, 1):
            name = repo.get('full_name', '')
            stars = repo.get('stargazers_count', 0)
            desc = repo.get('description', '')[:50]
            url = repo.get('html_url', '')
            message += f"{i}. <a href=\"{url}\">{name}</a> ⭐{stars:,}\n"
            if desc:
                message += f"   {desc}\n"
        
        send_telegram_message(message)
        
    except Exception as e:
        print(f"获取GitHub热门失败: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python send_telegram.py [daily|hourly|github]")
        sys.exit(1)
    
    mode = sys.argv[1]
    
    if mode == 'daily':
        push_daily_summary(24)
    elif mode == 'hourly':
        push_hourly_update()
    elif mode == 'github':
        push_github_trending()
    else:
        print(f"未知模式: {mode}")
