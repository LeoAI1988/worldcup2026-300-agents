#!/usr/bin/env python3
"""最后补P04和Q10"""
import json

RESULTS = [
    {
        "id": "P04",
        "faction": "心理抗压派",
        "identity": "抗压训练师",
        "champion": "阿根廷",
        "top3": ["阿根廷", "法国", "英格兰"],
        "confidence": 65,
        "reason": "阿根廷有梅西+大赛底蕴+点球抗压能力,点球大战历史胜率高,淘汰赛心理素质顶级,看好阿根廷卫冕。",
        "weight_logic": "大赛心理素质+点球胜率+逆境翻盘能力",
        "focus": "阿根廷近年淘汰赛点球7连胜,心理抗压属性碾压",
        "counter_trigger": False
    },
    {
        "id": "Q10",
        "faction": "建模派",
        "identity": "PySports派",
        "champion": "法国",
        "top3": ["法国", "西班牙", "阿根廷"],
        "confidence": 62,
        "reason": "PySports模型综合ELO(法国1950)+xG(7场+12.3)+阵容深度(23人均效力五大联赛),模拟夺冠概率19-22%,在所有建模中稳定前三。",
        "weight_logic": "ELO+xG+阵容深度量化",
        "focus": "蒙特卡洛10000次模拟,法国胜率峰值在半决赛",
        "counter_trigger": False
    }
]

with open("/workspace/worldcup2026/agents_output.json") as f:
    existing = json.load(f)

existing_ids = set(r['id'] for r in existing.get('results', []))
to_add = [r for r in RESULTS if r['id'] not in existing_ids]

existing['results'].extend(to_add)
existing['total'] = len(existing['results'])

with open("/workspace/worldcup2026/agents_output.json", "w") as f:
    json.dump(existing, f, ensure_ascii=False, indent=2)

print(f"已添加 {len(to_add)} 个, 总计 {existing['total']} 条")
