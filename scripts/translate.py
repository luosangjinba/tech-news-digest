#!/usr/bin/env python3
"""
翻译新闻标题
使用免费的翻译API
"""
import os
import json
import requests
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def translate_to_chinese(text):
    """翻译文本到中文"""
    if not text:
        return text
    
    # 使用 MyMemory 免费翻译 API
    try:
        url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(text)}&langpair=en|zh-CN"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data.get('responseStatus') == 200:
            return data['responseData']['translatedText']
    except Exception as e:
        print(f"翻译失败: {e}")
    
    return text  # 翻译失败返回原文

def translate_news_file(news_file):
    """翻译新闻文件"""
    with open(news_file, 'r', encoding='utf-8') as f:
        news = json.load(f)
    
    for item in news:
        if 'title_zh' not in item:
            item['title_zh'] = translate_to_chinese(item['title'])
    
    with open(news_file, 'w', encoding='utf-8') as f:
        json.dump(news, f, ensure_ascii=False, indent=2)
    
    print(f"已翻译 {len(news)} 条新闻: {news_file}")

def translate_all_today():
    """翻译今天的所有新闻"""
    today = datetime.now().strftime('%Y-%m-%d')
    news_dir = os.path.join(SCRIPT_DIR, '..', 'news', today)
    
    if not os.path.exists(news_dir):
        print(f"目录不存在: {news_dir}")
        return
    
    categories = ['ai', 'robotics', 'biotech', 'aerospace']
    for cat in categories:
        file_path = os.path.join(news_dir, f'{cat}.json')
        if os.path.exists(file_path):
            translate_news_file(file_path)

if __name__ == "__main__":
    translate_all_today()
