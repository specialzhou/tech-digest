#!/usr/bin/env python3
"""
Polymarket 每日简报集成
生成可插入到 tech-news-digest 的 HTML 片段
"""

import json
import sys
from pathlib import Path
from datetime import datetime

WORKSPACE = Path("/root/.openclaw/workspace")
REPORT_PATH = WORKSPACE / "polymarket-monitor" / "daily_report.json"

def generate_digest_section():
    """生成简报 HTML 片段"""
    
    if not REPORT_PATH.exists():
        return "<p>暂无交易数据</p>"
    
    with open(REPORT_PATH) as f:
        report = json.load(f)
    
    paper = report.get("paper_trading", {})
    poly = report.get("real_trading", {})
    summary = report.get("summary", {})
    
    # 信心分数颜色
    confidence = summary.get("confidence_score", 50)
    if confidence >= 70:
        confidence_color = "#10b981"  # 绿色
        confidence_text = "高"
    elif confidence >= 50:
        confidence_color = "#f59e0b"  # 黄色
        confidence_text = "中"
    else:
        confidence_color = "#ef4444"  # 红色
        confidence_text = "低"
    
    html = f"""
    <section class="polymarket-section" style="background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); padding: 32px; border-radius: 12px; margin-bottom: 40px; color: white;">
        <h2 style="font-size: 18px; font-weight: 600; margin-bottom: 20px; display: flex; align-items: center; gap: 8px;">
            <span>🎯</span> Polymarket 交易日报
        </h2>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px;">
            <!-- 信心分数 -->
            <div style="background: rgba(255,255,255,0.1); padding: 16px; border-radius: 8px; text-align: center;">
                <div style="font-size: 13px; opacity: 0.8; margin-bottom: 8px;">信心分数</div>
                <div style="font-size: 32px; font-weight: 700; color: {confidence_color}">{confidence}</div>
                <div style="font-size: 12px; opacity: 0.7;">/ 100 ({confidence_text})</div>
            </div>
            
            <!-- 模拟交易 -->
            <div style="background: rgba(255,255,255,0.1); padding: 16px; border-radius: 8px;">
                <div style="font-size: 13px; opacity: 0.8; margin-bottom: 8px;">📊 模拟交易</div>
                <div style="font-size: 14px; margin-bottom: 4px;">胜率：<strong style="color: {'#10b981' if paper.get('win_rate', 0) >= 50 else '#ef4444'}">{paper.get('win_rate', 0)}%</strong></div>
                <div style="font-size: 14px;">盈亏：<strong style="color: {'#10b981' if paper.get('total_pnl', 0) >= 0 else '#ef4444'}">${paper.get('total_pnl', 0)}</strong></div>
                <div style="font-size: 12px; opacity: 0.7; margin-top: 8px;">交易数：{paper.get('total_trades', 0)}</div>
            </div>
            
            <!-- 实盘持仓 -->
            <div style="background: rgba(255,255,255,0.1); padding: 16px; border-radius: 8px;">
                <div style="font-size: 13px; opacity: 0.8; margin-bottom: 8px;">💰 实盘持仓</div>
                <div style="font-size: 14px; margin-bottom: 4px;">价值：<strong>${poly.get('total_value', 0)}</strong></div>
                <div style="font-size: 14px;">盈亏：<strong style="color: {'#10b981' if poly.get('total_pnl', 0) >= 0 else '#ef4444'}">${poly.get('total_pnl', 0)}</strong></div>
                <div style="font-size: 12px; opacity: 0.7; margin-top: 8px;">持仓数：{poly.get('total_positions', 0)}</div>
            </div>
        </div>
        
        <!-- 持仓详情 -->
        {generate_positions_html(paper.get('positions', []), poly.get('positions', []))}
        
        <div style="margin-top: 20px; padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.2); font-size: 12px; opacity: 0.7; text-align: center;">
            数据更新时间：{report.get('generated_at', 'N/A')}
        </div>
    </section>
    """
    
    return html

def generate_positions_html(paper_positions, poly_positions):
    """生成持仓详情 HTML"""
    
    if not paper_positions and not poly_positions:
        return ""
    
    html = '<div style="margin-top: 20px;">'
    
    # 模拟交易持仓
    if paper_positions:
        html += '<h3 style="font-size: 14px; margin-bottom: 12px; opacity: 0.8;">📊 模拟持仓</h3>'
        html += '<div style="display: grid; gap: 8px;">'
        for pos in paper_positions[:3]:  # 最多显示 3 个
            pnl = pos.get('pnl', 0)
            pnl_color = '#10b981' if pnl >= 0 else '#ef4444'
            html += f"""
            <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 6px; font-size: 13px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>市场：{pos.get('market_id', 'N/A')[:30]}...</span>
                    <span style="color: {pnl_color}">P&L: ${pnl}</span>
                </div>
                <div style="opacity: 0.7; font-size: 12px;">
                    {pos.get('side', 'N/A')} @ ${pos.get('entry_price', 0)} → ${pos.get('current_price', 0)}
                </div>
            </div>
            """
        html += '</div>'
    
    # 实盘持仓
    if poly_positions:
        html += '<h3 style="font-size: 14px; margin-bottom: 12px; opacity: 0.8; margin-top: 16px;">💰 实盘持仓</h3>'
        html += '<div style="display: grid; gap: 8px;">'
        for pos in poly_positions[:3]:  # 最多显示 3 个
            pnl = pos.get('pnl', 0)
            pnl_color = '#10b981' if pnl >= 0 else '#ef4444'
            html += f"""
            <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 6px; font-size: 13px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span>市场：{pos.get('market', 'N/A')[:30]}...</span>
                    <span style="color: {pnl_color}">P&L: ${pnl}</span>
                </div>
                <div style="opacity: 0.7; font-size: 12px;">
                    {pos.get('side', 'N/A')} - 价值：${pos.get('value', 0)}
                </div>
            </div>
            """
        html += '</div>'
    
    html += '</div>'
    return html

if __name__ == "__main__":
    html = generate_digest_section()
    print(html)
