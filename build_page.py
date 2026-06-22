#!/usr/bin/env python3
"""生成可交互HTML网页"""
import json

with open("/workspace/worldcup2026/aggregated.json", "r", encoding="utf-8") as f:
    data = json.load(f)

with open("/workspace/worldcup2026/agents_output.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

# 简化agents数据(只保留网页需要的字段)
agents = raw["results"]

# 准备JS数据
page_data = {
    "stats": {
        "total": data["total_agents"],
        "failed": data["total_failed"],
        "factions": len(data["faction_summary"])
    },
    "ranking": data["champion_ranking"],
    "maxFavorite": data["dark_horse"]["max_favorite"],
    "darkHorseTop5": data["dark_horse"]["most_undervalued"],
    "factionSummary": data["faction_summary"],
    "factionQuotes": data["faction_quotes"],
    "agents": agents
}

with open("/workspace/worldcup2026/page_data.json", "w", encoding="utf-8") as f:
    json.dump(page_data, f, ensure_ascii=False)

print(f"数据就绪: {len(agents)}个agent")
print(f"文件大小: {__import__('os').path.getsize('/workspace/worldcup2026/page_data.json')/1024:.1f}KB")
