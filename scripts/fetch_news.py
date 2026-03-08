#!/usr/bin/env python3
"""
新闻获取脚本 - 财经/商业新闻
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

# 财经/商业新闻源
NEWS_SOURCES = {
    'tech': [
        {'name': '36氪', 'url': 'https://www.36kr.com/feed/'},
        {'name': '虎嗅', 'url': 'https://www.huxiu.com/rss'},
        {'name': '钛媒体', 'url': 'https://www.tmtpost.com/feed'},
    ],
    'finance': [
        {'name': '雪球', 'url': 'https://xueqiu.com/v4/statuses/public_timeline.json?count=30&source=web&type=0'},
        {'name': '华尔街见闻', 'url': 'https://api.wallstreetcn.com/apiv1/content/lives?channel=global&client=pc'},
    ],
    'invest': [
        {'name': '创业邦', 'url': 'https://www.cyzone.cn/rss/feed.php?type=1'},
        {'name': '投资界', 'url': 'https://www.pedaily.cn/rss/'},
    ],
}

# 关键词过滤
KEYWORDS = [
    '融资', '投资', 'IPO', '上市', '财报', '营收', '利润', '估值',
    '收购', '并购', '产品', '发布', '上线', '推出', '新功能',
    '市场', '趋势', '行业', '预测', '分析',
    'AI', '人工智能', '大模型', 'GPT', 'Sora',
    '芯片', '半导体', 'GPU', '算力',
    '新能源', '电动车', '自动驾驶',
    '生物医药', '创新药', '疫苗',
    'SpaceX', 'NASA', '火箭', '卫星',
    '降息', '加息', '通胀', '美联储', '央行',
    '人民币', '美元', '汇率', 'A股', '美股', '港股',
]

EXCLUDE_KEYWORDS = [
    '招聘', '求职', '面试', '工资', '薪资',
    '教程', '入门', '学习', '课程', '培训',
]

# 使用当前目录下的 news 文件夹
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
        print(f"获取 {source_name} 失败: {e}")
        return None

def fetch_json(url, source_name):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=15)
        return resp.json()
    except Exception as e:
        print(f"获取 {source_name} 失败: {e}")
        return None

def parse_feed(xml_text, source_name):
    items = []
    try:
        feed = feedparser.parse(xml_text)
        for entry in feed.entries[:20]:
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

def filter_by_keywords(items):
    filtered = []
    for item in items:
        title = item['title']
        exclude = False
        for kw in EXCLUDE_KEYWORDS:
            if kw.lower() in title.lower():
                exclude = True
                break
        if exclude:
            continue
        for kw in KEYWORDS:
            if kw.lower() in title.lower():
                filtered.append(item)
                break
    return filtered[:15] if filtered else items[:10]

def fetch_category_news(category):
    print(f"\n获取 {category} 新闻...")
    all_items = []
    
    if category not in NEWS_SOURCES:
        print(f"未知分类: {category}")
        return []
    
    for source in NEWS_SOURCES[category]:
        if 'xueqiu' in source['url'] or 'wallstreetcn' in source['url']:
            data = fetch_json(source['url'], source['name'])
            if data:
                items = []
                if 'xueqiu' in source['url']:
                    for item in data.get('list', [])[:15]:
                        items.append({
                            'title': item.get('text', '')[:100],
                            'link': f"https://xueqiu.com/S/{item.get('symbol', '')}",
                            'source': source['name']
                        })
                elif 'wallstreetcn' in source['url']:
                    for item in data.get('data', {}).get('articles', [])[:15]:
                        items.append({
                            'title': item.get('title', ''),
                            'link': 'https://wallstreetcn.com' + item.get('uri', ''),
                            'source': source['name']
                        })
                all_items.extend(items)
                print(f"  {source['name']}: {len(items)} 条")
        else:
            xml = fetch_feed(source['url'], source['name'])
            if xml:
                items = parse_feed(xml, source['name'])
                all_items.extend(items)
                print(f"  {source['name']}: {len(items)} 条")
    
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
    
    print(f"已保存 {len(items)} 条到 {file_path}")
    return file_path

def main():
    print("=" * 50)
    print("财经商业新闻获取")
    print("=" * 50)
    
    categories = ['tech', 'finance', 'invest']
    
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
