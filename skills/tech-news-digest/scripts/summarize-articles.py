#!/usr/bin/env python3
"""Summarize articles using Bailian API and add Chinese summaries."""

import json
import sys
import argparse
import os
import requests
from typing import Dict, List

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

def summarize_article(title: str, snippet: str) -> str:
    """Generate Chinese summary for an article."""
    
    if not API_KEY:
        return snippet[:80] + "..." if snippet else ""
    
    prompt = f"""请用一句话总结这篇科技新闻的核心内容（中文，不超过 40 字）：

标题：{title}
摘要：{snippet if snippet else '无'}

直接输出总结，不要其他内容。"""

    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "qwen-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100
            },
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    except Exception as e:
        pass
    
    return snippet[:80] + "..." if snippet else ""

def get_relevance_score(article: Dict) -> int:
    """Calculate relevance score for 舟哥."""
    title = (article.get("title", "") + " " + article.get("snippet", "")).lower()
    score = 0
    
    if any(kw in title for kw in ["polymarket", "prediction market", "kalshi", "binary bet"]):
        score += 30
    if any(kw in title for kw in ["quant", "trading bot", "algorithmic", "backtest"]):
        score += 25
    if any(kw in title for kw in ["payment", "stripe", "paypal", "cross-border", "stablecoin"]):
        score += 20
    if any(kw in title for kw in ["llm", "gpt", "claude", "ai agent"]):
        score += 15
    
    score += int(article.get("quality_score", 0) * 2)
    return score

def summarize_top_articles(data: Dict, top_n: int = 4) -> Dict:
    """Summarize top relevant articles."""
    
    all_articles = []
    for topic_data in data.get("topics", {}).values():
        all_articles.extend(topic_data.get("articles", []))
    
    # Score and sort
    for article in all_articles:
        article["_relevance"] = get_relevance_score(article)
    
    all_articles.sort(key=lambda x: x.get("_relevance", 0), reverse=True)
    
    # Summarize top articles
    summarized = []
    seen_topics = set()
    
    for article in all_articles:
        if len(summarized) >= top_n:
            break
        
        if article.get("quality_score", 0) < 5.0:
            continue
        
        topic = article.get("primary_topic", "general")
        if topic in seen_topics and len(summarized) >= 3:
            continue
        
        summary = summarize_article(
            article.get("title", ""),
            article.get("snippet", "")
        )
        
        article["_summary_zh"] = summary
        summarized.append({
            "title": article.get("title", ""),
            "summary": summary
        })
        seen_topics.add(topic)
    
    print(f"✅ Summarized {len(summarized)} articles:")
    for item in summarized:
        print(f"   - {item['summary']}")
    
    return data

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--api-key", help="DashScope/Bailian API key")
    args = parser.parse_args()
    
    if args.api_key:
        API_KEY = args.api_key
    
    # Try to get API key from config
    if not API_KEY:
        try:
            with open("/root/.openclaw/openclaw.json") as f:
                config = json.load(f)
                API_KEY = config.get("models", {}).get("providers", {}).get("bailian", {}).get("apiKey", "")
        except:
            pass
    
    if not API_KEY:
        print("⚠️  No API key found, summaries will use snippets")
    
    with open(args.input, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    summarize_top_articles(data)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Output: {args.output}")
