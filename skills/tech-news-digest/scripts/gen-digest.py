#!/usr/bin/env python3
"""
每日简报生成器 - 生产版本
支持调用 Qwen API 生成中文核心要闻摘要
"""
import json
import sys
import os
import requests
from datetime import datetime
from pathlib import Path

TOPIC_CONFIG = {
    "crypto": ("💰 加密货币", "比特币、以太坊、DeFi、NFT、区块链"),
    "llm": ("🤖 大模型", "大语言模型、基础模型、AI 研究"),
    "ai-agent": ("🧠 AI Agent", "自主 Agent、AI 助手、Agent 框架"),
    "frontier-tech": ("🚀 前沿科技", "量子计算、太空、生物技术、机器人"),
}

def get_qwen_api_key():
    """获取 Qwen API Key（阿里云百炼）"""
    # 优先从环境变量获取
    api_key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("BAILOU_API_KEY")
    if api_key:
        return api_key
    # 尝试从 auth.json 获取
    try:
        auth_paths = [
            "/root/.openclaw/agents/main/agent/auth.json",
            os.path.expanduser("~/.openclaw/agents/main/agent/auth.json"),
        ]
        for auth_path in auth_paths:
            if os.path.exists(auth_path):
                with open(auth_path) as f:
                    auth = json.load(f)
                    # 支持多种配置名
                    for key in ["bailian", "qwen", "dashscope", "alibaba"]:
                        if key in auth and auth[key].get("key"):
                            return auth[key]["key"]
    except Exception as e:
        print(f"⚠️  读取 auth.json 失败：{e}")
    return None

def ai_summarize(highlights):
    """使用 Qwen 生成中文摘要"""
    api_key = get_qwen_api_key()
    if not api_key:
        return None
    
    titles = "\n".join([f"- {h['title']} ({h.get('source_name', '')})" for h in highlights[:6]])
    
    prompt = f"""请将以下科技新闻标题概括成一段 80 字以内的中文摘要，要求：
1. 用连贯的句子，不要列表
2. 突出最重要的 2-3 件事
3. 使用简洁的中文科技新闻风格

新闻标题：
{titles}

摘要："""

    try:
        resp = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "qwen-plus",
                "input": {"messages": [{"role": "user", "content": prompt}]},
                "parameters": {"temperature": 0.5}
            },
            timeout=10
        )
        if resp.ok:
            data = resp.json()
            content = data.get("output", {}).get("text", "")
            return content.strip() if content else None
    except Exception as e:
        print(f"⚠️  AI 摘要失败：{e}")
    return None

def clean_title(title):
    """清理 HTML 实体"""
    return (title
        .replace('&#39;', "'")
        .replace('&amp;', '&')
        .replace('&lt;', '<')
        .replace('&gt;', '>')
        .replace('&quot;', '"'))

def get_domain(url):
    """提取域名"""
    return url.replace('https://www.', '').replace('https://', '').split('/')[0]

def generate_digest(data, output_path=None):
    lines = []
    date_str = datetime.now().strftime('%Y年%m月%d日')
    
    # 标题
    lines.append(f"# 📰 每日科技新闻摘要 - {date_str}")
    lines.append("")
    
    # 核心要闻 - 选取各分类 Top1，去重
    lines.append("## 核心要闻")
    lines.append("")
    
    highlights = []
    seen_titles = set()
    for topic in ["crypto", "llm", "ai-agent", "frontier-tech"]:
        if topic in data['topics']:
            articles = data['topics'][topic]['articles']
            if articles:
                top = max(articles, key=lambda x: x.get('quality_score', 0))
                title = clean_title(top['title'])
                if title in seen_titles:
                    continue
                seen_titles.add(title)
                highlights.append(top)
    
    # 尝试 AI 生成摘要
    ai_summary = ai_summarize(highlights)
    if ai_summary:
        lines.append(ai_summary)
    else:
        # 降级方案：简洁列举
        summaries = []
        for h in highlights[:4]:
            title = clean_title(h['title'])
            short = title[:40] + "..." if len(title) > 40 else title
            summaries.append(short)
        lines.append("；".join(summaries) + "。")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 分类详情
    for topic_id, (topic_name, topic_desc) in TOPIC_CONFIG.items():
        if topic_id not in data['topics']:
            continue
        
        topic_data = data['topics'][topic_id]
        articles = topic_data['articles']
        if not articles:
            continue
        
        lines.append(f"## {topic_name}")
        lines.append("")
        lines.append(f"_{topic_desc}_")
        lines.append("")
        
        # 按质量评分排序，取 Top 5
        sorted_articles = sorted(articles, key=lambda x: x.get('quality_score', 0), reverse=True)[:5]
        
        for i, article in enumerate(sorted_articles, 1):
            title = clean_title(article['title'])
            source = article.get('source_name', 'Unknown')
            link = article['link']
            domain = get_domain(link)
            
            lines.append(f"**{i}. {title}**")
            lines.append(f"   _{source} · {domain}_")
            lines.append(f"   {link}")
            lines.append("")
        
        lines.append("")
    
    # 数据统计
    lines.append("---")
    lines.append("")
    input_src = data.get('input_sources', {})
    lines.append(f"**数据来源**: RSS {input_src.get('rss_articles', 0)} | GitHub {input_src.get('github_articles', 0)} | Web {input_src.get('web_articles', 0)} | 去重后共 {data['output_stats']['total_articles']} 篇文章")
    lines.append("")
    lines.append(f"**🤖 tech-news-digest v3.5.0** | Powered by OpenClaw")
    
    content = "\n".join(lines)
    
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(content)
        print(f"✅ 简报已保存至：{output_path}")
    
    return content

if __name__ == "__main__":
    merged_json = "/tmp/td-merged.json"
    archive_dir = "/root/.openclaw/workspace/archive/tech-news-digest"
    
    if len(sys.argv) > 1:
        merged_json = sys.argv[1]
    if len(sys.argv) > 2:
        archive_dir = sys.argv[2]
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    output_path = f"{archive_dir}/daily-{date_str}.md"
    
    with open(merged_json, 'r') as f:
        data = json.load(f)
    
    generate_digest(data, output_path)
