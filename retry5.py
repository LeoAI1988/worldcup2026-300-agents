#!/usr/bin/env python3
"""最后补5个JSON易碎的agent - 用更严格prompt+更宽容parser"""
import json
import re
import time
import urllib.request

API_URL = "https://api.minimaxi.com/v1/chat/completions"
API_KEY = os.environ.get("MINIMAX_API_KEY", "YOUR_API_KEY_HERE")

REMAIN = ['H19', 'H20', 'H26', 'P04', 'Q10']

with open("/workspace/worldcup2026/agents_pool.json") as f:
    pool = json.load(f)
all_agents = []
for fn, ags in pool['factions'].items():
    for a in ags:
        a_copy = a.copy()
        a_copy['faction'] = fn
        all_agents.append(a_copy)

targets = [a for a in all_agents if a['id'] in REMAIN]

with open("/workspace/worldcup2026/agents_output.json") as f:
    existing = json.load(f)

def call_m3(prompt):
    body = {"model": "MiniMax-M3", "messages": [{"role":"user","content":prompt}], "temperature":0.5, "max_tokens":600}
    req = urllib.request.Request(API_URL, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())['choices'][0]['message']['content']

def extract_strict(text):
    """超宽容提取: 找第一个 { 和匹配的 }"""
    text = text.strip()
    # 移除markdown
    text = re.sub(r'^