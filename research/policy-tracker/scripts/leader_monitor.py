#!/usr/bin/env python3
"""
领导变动定时检测引擎 — 部署到 skill/scripts/
每次运行抓取各委办局领导名单 → 与前次快照对比 → 输出变化报告。
同时抓取北京人事任免公告 → 检测新条目。

用法:
  python3 leader_monitor.py            # 检测一次
  python3 leader_monitor.py --init     # 初始化基线快照
  python3 leader_monitor.py --cron     # cron 模式输出 JSON

数据: leader_data/snapshots/{agency}.json + leader_data/changes.log
"""
# Full source at: /Users/you/Documents/工作/2026创新大赛/agent/政策动态追踪/leader_monitor.py
# Copy to skill scripts: cp leader_monitor.py ~/.hermes/skills/research/policy-tracker/scripts/
