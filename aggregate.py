#!/usr/bin/env python3
"""
聚合300份agent判断
- 加权概率(信心加权)
- 派别分布
- 黑马识别(派别分歧度)
- 最大热门/最被低估
"""
import json
from collections import defaultdict, Counter
import math

def aggregate(agents_data):
    results = agents_data["results"]
    meta = agents_data.get("meta", {})

    # 1. 冠军票(信心加权)
    champion_votes = defaultdict(lambda: {"count": 0, "weighted_score": 0.0, "confidence_sum": 0, "factions": defaultdict(int)})
    top3_votes = defaultdict(lambda: {"count": 0, "weighted_score": 0.0, "factions": defaultdict(int)})

    total_weight = 0
    for r in results:
        w = r["confidence"]
        total_weight += w
        champ = r["champion"]
        champion_votes[champ]["count"] += 1
        champion_votes[champ]["weighted_score"] += w
        champion_votes[champ]["confidence_sum"] += w
        champion_votes[champ]["factions"][r["faction"]] += 1

        for t in r["top3"]:
            top3_votes[t]["count"] += 1
            top3_votes[t]["weighted_score"] += w * 0.5  # Top3权重低于冠军

    # 归一化为百分比
    for team, v in champion_votes.items():
        v["probability"] = round(v["weighted_score"] / total_weight * 100, 2)
    for team, v in top3_votes.items():
        v["top3_probability"] = round(v["weighted_score"] / total_weight * 100, 2)

    # Top8热力榜
    champion_ranked = sorted(champion_votes.items(), key=lambda x: -x[1]["probability"])[:12]

    # 2. 派别冠军倾向分布
    faction_champion_dist = defaultdict(Counter)
    faction_avg_confidence = defaultdict(list)
    for r in results:
        faction_champion_dist[r["faction"]][r["champion"]] += 1
        faction_avg_confidence[r["faction"]].append(r["confidence"])

    faction_summary = {}
    for f, dist in faction_champion_dist.items():
        total_faction = sum(dist.values())
        ranked = dist.most_common(5)
        avg_conf = round(sum(faction_avg_confidence[f]) / len(faction_avg_confidence[f]), 1)
        faction_summary[f] = {
            "top_champions": [{"team": t, "votes": c, "pct": round(c/total_faction*100, 1)} for t, c in ranked],
            "agent_count": total_faction,
            "avg_confidence": avg_conf
        }

    # 3. 黑马识别 - 找"赔率榜靠后但被某些派别看好"的队
    odds_top = ["France", "Spain", "England", "Argentina", "Brazil"]  # 赔率前5
    # 计算每队在"非赔率派(黑马派/玄学派/老球迷派)"中的得票率
    darkhorse_factions = {"黑马派", "玄学派", "老球迷派"}
    odds_factions = {"赔率派"}

    dark_horse_score = {}
    for team, v in champion_votes.items():
        dark_votes = sum(v["factions"].get(f, 0) for f in darkhorse_factions)
        odds_votes = sum(v["factions"].get(f, 0) for f in odds_factions)
        total_votes = v["count"]
        if total_votes < 3:
            continue
        # 黑马得分 = (黑马派得票率 - 赔率派得票率)
        dark_pct = dark_votes / total_votes if total_votes else 0
        odds_pct = odds_votes / total_votes if total_votes else 0
        # 派别分歧度(标准差)
        faction_dist = list(v["factions"].values())
        if len(faction_dist) > 1:
            mean = sum(faction_dist) / len(faction_dist)
            variance = sum((x-mean)**2 for x in faction_dist) / len(faction_dist)
            divergence = math.sqrt(variance)
        else:
            divergence = 0
        dark_horse_score[team] = {
            "dark_pct": round(dark_pct*100, 1),
            "odds_pct": round(odds_pct*100, 1),
            "gap": round((dark_pct - odds_pct)*100, 1),
            "total_votes": total_votes,
            "divergence": round(divergence, 2),
            "factions": dict(v["factions"]),
            "in_odds_top5": team in odds_top
        }

    # 排序找最被低估的黑马
    # 综合:黑马得分 + 派别分歧度
    dark_horse_ranked = sorted(
        [(t, v) for t, v in dark_horse_score.items() if v["total_votes"] >= 3],
        key=lambda x: (-x[1]["gap"] - x[1]["divergence"]*0.5, -x[1]["total_votes"])
    )

    # 4. 最大热门
    max_favorite = champion_ranked[0] if champion_ranked else None

    # 5. 派别内部代表quote
    faction_quotes = {}
    for f, agents in defaultdict(list, {r["faction"]: [] for r in results}).items():
        pass
    for f in set(r["faction"] for r in results):
        faction_agents = [r for r in results if r["faction"] == f]
        # 取信心最高的3个作为代表quote
        top_agents = sorted(faction_agents, key=lambda x: -x["confidence"])[:3]
        faction_quotes[f] = [
            {"identity": a["identity"], "champion": a["champion"], "confidence": a["confidence"], "reason": a["reason"]}
            for a in top_agents
        ]

    return {
        "meta": meta,
        "total_agents": len(results),
        "total_failed": len(agents_data.get("failures", [])),
        "champion_ranking": [
            {
                "team": t,
                "champion_votes": v["count"],
                "weighted_score": round(v["weighted_score"], 1),
                "probability": v["probability"],
                "top3_probability": top3_votes.get(t, {}).get("top3_probability", 0),
                "factions": dict(v["factions"]),
                "avg_confidence": round(v["confidence_sum"] / v["count"], 1) if v["count"] else 0
            }
            for t, v in champion_ranked
        ],
        "faction_summary": faction_summary,
        "faction_quotes": faction_quotes,
        "dark_horse": {
            "max_favorite": {
                "team": max_favorite[0],
                "probability": max_favorite[1]["probability"],
                "votes": max_favorite[1]["count"]
            } if max_favorite else None,
            "most_undervalued": [
                {
                    "team": t,
                    "dark_pct": v["dark_pct"],
                    "odds_pct": v["odds_pct"],
                    "gap": v["gap"],
                    "total_votes": v["total_votes"],
                    "divergence": v["divergence"],
                    "factions": v["factions"]
                }
                for t, v in dark_horse_ranked[:5]
            ]
        },
        "all_agents": results
    }


def main():
    with open("/workspace/worldcup2026/agents_output.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    aggregated = aggregate(data)
    with open("/workspace/worldcup2026/aggregated.json", "w", encoding="utf-8") as f:
        json.dump(aggregated, f, ensure_ascii=False, indent=2)

    # 打印关键结论
    print(f"=== 聚合完成 ===")
    print(f"总agent数: {aggregated['total_agents']} (失败: {aggregated['total_failed']})")
    print(f"\nTop10夺冠概率:")
    for i, t in enumerate(aggregated['champion_ranking'][:10], 1):
        print(f"  {i}. {t['team']}: {t['probability']}% (票{t['champion_votes']}, 信{t['avg_confidence']})")

    print(f"\n最大热门: {aggregated['dark_horse']['max_favorite']}")
    print(f"\n最被低估黑马 Top5:")
    for d in aggregated['dark_horse']['most_undervalued'][:5]:
        print(f"  {d['team']}: 黑马派{d['dark_pct']}% vs 赔率派{d['odds_pct']}% (落差{d['gap']}%, 分歧度{d['divergence']})")

    print(f"\n派别分布:")
    for f, s in aggregated['faction_summary'].items():
        top = s['top_champions'][0] if s['top_champions'] else None
        print(f"  {f}({s['agent_count']}人,平均信{s['avg_confidence']}): 首选{top}")


if __name__ == "__main__":
    main()
