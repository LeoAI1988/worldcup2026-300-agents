#!/usr/bin/env python3
"""补跑14个失败agent - 用更稳健的提示词"""
import json
import os
import re
import time
import urllib.request

# 失败的13个ID (V01, V30, M11, M25, M30, P04, A24, H19, H20, H26, Q10, Q11, Q26)
FAILED_IDS = ['V01', 'V30', 'M11', 'M25', 'M30', 'P04', 'A24', 'H19', 'H20', 'H26', 'Q10', 'Q11', 'Q26']

# 从pool加载这些agent的定义
with open("/workspace/worldcup2026/agents_pool.json", "r", encoding="utf-8") as f:
    pool = json.load(f)

# pool结构: {factions: {派别名: [agent1, agent2, ...]}}
# 平铺所有agent,加上faction字段
all_agents = []
for faction_name, agents in pool['factions'].items():
    for a in agents:
        a_copy = a.copy()
        a_copy['faction'] = faction_name
        all_agents.append(a_copy)

# 过滤出失败的agent
retry_agents = [a for a in all_agents if a['id'] in FAILED_IDS]
print(f"待补跑: {len(retry_agents)} 个")
print(f"派别: {set(a['faction'] for a in retry_agents)}")

# 加载已存在的输出
with open("/workspace/worldcup2026/agents_output.json", "r", encoding="utf-8") as f:
    existing = json.load(f)

# M3 API配置 (翔哥提供的key)
API_URL = "https://api.minimaxi.com/v1/chat/completions"
API_KEY = "sk-cp-451Xpnhb2Q148aJULQajFXZeWJm0L9y2VqOWp9J2NaGDycDfxyBzblFJI4Oe63Kvr-jaOZ1KSThT6B__EOdlcXqlDeqZJQ_NCN8KYh83WLglEA2RYoIbp50"
if not API_KEY:
    print("ERROR: API key缺失")
    exit(1)

def call_m3(prompt, system=""):
    """调用M3生成"""
    body = {
        "model": "MiniMax-M3",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1500  # 降低token数提高稳定性
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode('utf-8'),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())['choices'][0]['message']['content']

def extract_json(text):
    """从文本中提取JSON"""
    text = text.strip()
    # 移除markdown代码块
    if text.startswith("