#!/usr/bin/env python3
"""
Polymarket 统一监控脚本
- 整合 paper trader（模拟）和 polyclaw（实盘）
- 每日生成交易报告
- 胜率/盈亏统计
- 异常通知
"""

import json
import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path

# 路径配置
WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE", "/root/.openclaw/workspace"))
PAPER_TRADER_DB = Path(os.environ.get("PM_TRADER_DATA_DIR", "/root/.pm-trader/main/paper.db"))
POLYCLAW_POSITIONS = WORKSPACE / "polyclaw" / "positions.json"
MONITOR_LOG = WORKSPACE / "polymarket-monitor" / "monitor.log"
REPORT_PATH = WORKSPACE / "polymarket-monitor" / "daily_report.json"

def get_paper_trading_stats():
    """获取模拟交易统计"""
    if not PAPER_TRADER_DB.exists():
        return {
            "total_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "positions": []
        }
    
    conn = sqlite3.connect(PAPER_TRADER_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 总交易数
    cursor.execute("SELECT COUNT(*) FROM trades WHERE 1")
    total_trades = cursor.fetchone()[0]
    
    # 已平仓交易（通过 positions 表的 realized_pnl 计算）
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
            SUM(realized_pnl) as total_pnl
        FROM positions 
        WHERE is_resolved = 1
    """)
    row = cursor.fetchone()
    closed_total = row['total'] or 0
    wins = row['wins'] or 0
    total_pnl = row['total_pnl'] or 0
    win_rate = (wins / closed_total * 100) if closed_total > 0 else 0
    
    # 当前持仓（positions 表未平仓的）
    cursor.execute("""
        SELECT 
            market_condition_id,
            market_question,
            outcome,
            shares,
            avg_entry_price,
            total_cost,
            realized_pnl
        FROM positions 
        WHERE is_resolved = 0 AND shares > 0
    """)
    positions = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "total_trades": total_trades,
        "win_rate": round(win_rate, 1),
        "total_pnl": round(total_pnl, 2),
        "positions": positions,
        "period": "all_time"
    }

def get_polyclaw_positions():
    """获取实盘持仓"""
    # 如果未配置实盘，返回空数据
    if not POLYCLAW_POSITIONS.exists():
        return {
            "total_positions": 0,
            "total_value": 0,
            "total_pnl": 0,
            "positions": [],
            "enabled": False
        }
    
    with open(POLYCLAW_POSITIONS) as f:
        data = json.load(f)
    
    positions = data.get("positions", [])
    total_value = sum(p.get("value", 0) for p in positions)
    total_pnl = sum(p.get("pnl", 0) for p in positions)
    
    return {
        "total_positions": len(positions),
        "total_value": round(total_value, 2),
        "total_pnl": round(total_pnl, 2),
        "positions": positions,
        "enabled": True
    }

def generate_daily_report():
    """生成每日报告"""
    paper_stats = get_paper_trading_stats()
    poly_stats = get_polyclaw_positions()
    
    report = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "generated_at": datetime.now().isoformat(),
        "paper_trading": paper_stats,
        "real_trading": poly_stats,
        "summary": {
            "paper_win_rate": paper_stats["win_rate"],
            "paper_total_pnl": paper_stats["total_pnl"],
            "real_total_value": poly_stats["total_value"],
            "real_total_pnl": poly_stats["total_pnl"],
            "confidence_score": calculate_confidence(paper_stats, poly_stats)
        }
    }
    
    # 保存报告
    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 写入日志
    log_message(f"Daily report generated: {REPORT_PATH}")
    
    return report

def calculate_confidence(paper_stats, poly_stats):
    """
    计算信心分数（0-100）
    仅基于模拟交易胜率（实盘未启用时）
    """
    score = 50  # 基础分
    
    # 模拟交易胜率加分
    win_rate = paper_stats["win_rate"]
    if win_rate > 60:
        score += min((win_rate - 60) * 2, 30)  # 最多加 30 分
    elif win_rate < 40:
        score -= min((40 - win_rate) * 2, 30)  # 最多减 30 分
    
    # 实盘盈亏加分（仅当实盘启用时）
    if poly_stats.get("enabled", True):
        real_pnl = poly_stats["total_pnl"]
        if real_pnl > 100:
            score += 10
        elif real_pnl < -100:
            score -= 10
    
    return max(0, min(100, score))

def log_message(message):
    """写入日志"""
    MONITOR_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(MONITOR_LOG, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")

def check_anomalies():
    """检查异常并返回警告"""
    warnings = []
    
    paper_stats = get_paper_trading_stats()
    poly_stats = get_polyclaw_positions()
    
    # 胜率过低警告
    if paper_stats["win_rate"] < 40 and paper_stats["total_trades"] > 10:
        warnings.append(f"⚠️ 模拟交易胜率过低：{paper_stats['win_rate']}%")
    
    # 实盘大额亏损警告
    if poly_stats.get("enabled") and poly_stats["total_pnl"] < -500:
        warnings.append(f"⚠️ 实盘大额亏损：${poly_stats['total_pnl']}")
    
    return warnings

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "report":
            report = generate_daily_report()
            print(json.dumps(report, indent=2, ensure_ascii=False))
        
        elif command == "stats":
            print("=== 模拟交易统计 ===")
            paper = get_paper_trading_stats()
            print(f"总交易数：{paper['total_trades']}")
            print(f"胜率：{paper['win_rate']}%")
            print(f"总盈亏：${paper['total_pnl']}")
            print(f"当前持仓：{len(paper['positions'])}")
            
            print("\n=== 实盘持仓 ===")
            poly = get_polyclaw_positions()
            if poly.get("enabled"):
                print(f"持仓数：{poly['total_positions']}")
                print(f"总价值：${poly['total_value']}")
                print(f"总盈亏：${poly['total_pnl']}")
            else:
                print("⏸️ 实盘未启用")
        
        elif command == "warnings":
            warnings = check_anomalies()
            if warnings:
                print("⚠️ 警告:")
                for w in warnings:
                    print(f"  {w}")
            else:
                print("✅ 无异常")
        
        else:
            print(f"未知命令：{command}")
            print("可用命令：report, stats, warnings")
    else:
        # 默认生成报告
        report = generate_daily_report()
        print(f"报告已生成：{REPORT_PATH}")
        print(f"信心分数：{report['summary']['confidence_score']}/100")
