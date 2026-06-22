#!/usr/bin/env python3
"""
300个独立agent生成脚本 v2
关键改进:
1. 每个agent的prompt都有"个人倾向锚点" - 强制其从自己的视角独立判断
2. 加入"反共识触发" - 部分agent被要求反向思考
3. JSON解析更鲁棒
4. 失败重试机制
"""
import json
import time
import urllib.request
import urllib.error
import random
import os
import sys
import re

API_URL = "https://api.minimaxi.com/v1/chat/completions"
API_KEY = os.environ.get("MINIMAX_API_KEY", "YOUR_API_KEY_HERE")
MODEL = "MiniMax-M3"

DATA_BLOCK = """[真实数据快照 2026-06-12/13]
赛事状态: 2026 FIFA World Cup 已开赛 (6/11开打,小组赛进行中)
当前赔率(博彩市场隐含概率):
- 法国 +420 (隐含~19%)
- 西班牙 +500 (~17%)
- 英格兰 +600 (~14%)
- 阿根廷 +800 (~11%)
- 巴西 +1100 (~8%)
- 德国 +1400 / 葡萄牙 +1600 / 荷兰 +2000 / 比利时 +2500 / 意大利 +3300
小组赛首日/次日部分结果:
- 法国 3-1 塞内加尔 (Mbappé梅开二度,虽带伤)
- 英格兰 4-2 克罗地亚
- 美国 4-1 巴拉圭
- 墨西哥 2-0 南非
- 葡萄牙 1-1 刚果
- 加拿大 1-1 波黑
关键伤病:
- 法国: Mbappé脚踝/膝盖隐患; Hugo Ekitike(跟腱)缺席
- 巴西: Neymar小腿; Rodrygo缺席
- 阿根廷: Messi轻伤; Balerdi小腿缺席; Romero/Dybala/Martinez小伤
- 西班牙: Lamine Yamal轻伤
- 德国: Gnabry缺席
- 其他: Fermin Lopez缺席
潜在黑马共识: 墨西哥/挪威/瑞士/塞内加尔/哥伦比亚/厄瓜多尔/日本/摩洛哥/美国
48队分12组,加美墨举办,首次48队扩军,赛程密度大"""

# 各派别的核心世界观(强化版)
FACTION_CORE = {
    "数据派": "你的决策完全基于可量化指标:身价/Elo/xG/近期战绩/PPDA/控球率/传球网络密度等。你鄙视只看赔率的赔率派,认为他们没思考。你相信数据不说谎。",
    "赔率派": "你的决策完全基于博彩盘口和隐含概率。Pinnacle sharp线最权威,公众下注量次之,凯利公式决定仓位。你认为市场集体智慧>任何个人判断。",
    "老球迷派": "你的决策基于历史底蕴/大赛基因/决赛抗压记录/血脉传承。你看过90年马拉多纳/02年罗纳尔多/14年克洛泽,你知道大赛气质是纸面看不出的。",
    "玄学派": "你的决策基于东道主魔咒/卫冕魔咒/偶数年规律/数字命理/占星/塔罗等玄学。你是娱乐派但言之凿凿,所有分析都有模有样。",
    "主帅视角派": "你的决策基于战术体系克制/排兵布阵深度/教练临场应变。你是教练视角,认为战术对位比球员名气更重要。",
    "伤病赛程派": "你的决策基于关键球员伤病/赛程密度/旅行气候/高原反应/时差调整。你是医学+地理视角,认为纸面再好也扛不住这些。",
    "黑马派": "你的决策完全基于被市场低估的冷门潜力。你鄙视大热必死但更鄙视赔率派的从众。你专挑赔率+1500以上的队。",
    "阵容年龄派": "你的决策基于球员年龄结构/巅峰集中度/青黄不接风险/老将续航。你是体育科学视角。",
    "心理抗压派": "你的决策基于点球心理/逆境翻盘能力/淘汰赛大心脏/压力管理。你是心理学视角。",
    "建模派": "你的决策基于蒙特卡洛/泊松/Elo/Dixon-Coles/贝叶斯等量化模型。你鄙视定性分析,只相信数字。"
}


def build_prompt(faction_name, agent_meta, data_block, anchor_team=None, counter_consensus=False):
    """每个agent独立prompt,严格保证差异化
    anchor_team: 个人倾向锚点(从agent元数据里拿)
    counter_consensus: 是否加入反共识触发
    """
    system = f"""你是【{faction_name}】派别的预测专家,身份:{agent_meta['identity']}。
加权逻辑:{agent_meta['weight']}
关注重点:{agent_meta.get('focus', '综合判断')}

【你的世界观】{FACTION_CORE[faction_name]}

【你的判断倾向 - 必读】作为{agent_meta['identity']},你深度看好【{anchor_team or agent_meta.get('anchor_team', '未知')}】。
你的任务是从你的专业视角(基于{agent_meta['weight']}和{agent_meta.get('focus', '综合')})为这个看好找到独立论据。
即使主流赔率不看好它,你也要用你的派别世界观证明它能夺冠。
你的冠军选择必须与你的倾向一致,但Top3可以包含赔率榜上的强队作为对比参照。

【你的独特视角】
- 你是{agent_meta['identity']},有独特专业背景
- 论证从{agent_meta['weight']}出发
- 关注点聚焦于{agent_meta.get('focus', '综合')}
- 理由必须体现你这个身份的专业性,不能套用通用模板

直接输出严格JSON,不要think/解释/前缀/后缀/代码块。"""

    counter_text = ""
    if counter_consensus:
        counter_text = "\n\n【反向思考触发】主流赔率共识是法国/西班牙/英格兰,但你作为异见者,要思考:如果共识错了,最可能的真相是什么?黑马是否被严重低估?"

    user = f"""基于真实数据:{data_block}

请从【{faction_name}】派别下【{agent_meta['identity']}】的独特专业视角,做出你独立的世界杯冠军预测。{counter_text}

【严格输出格式 - 不要任何其他内容】
{{"冠军": "球队中文名", "Top3": ["球队A中文名","球队B中文名","球队C中文名"], "信心": 0-100整数, "理由": "一句话40-80字,必须体现你的派别特色+身份关注点"}}

要求:
1. 冠军必须是48参赛队之一
2. Top3的3支球队必须各不相同
3. 信心数字代表你对自己判断的自信程度(0-100),不是该队夺冠概率
4. 理由必须40-80字,言之有物,体现{agent_meta['identity']}的专业关注点
5. 不要引用赔率数字,只用事实推断"""
    return system, user


def call_m3(system, user, max_retries=3):
    """调用M3,带重试"""
    payload = {
        "model": MODEL,
        "max_tokens": 2000,
        "temperature": 0.7,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
    )
    for attempt in range(max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                if "</think>" in content:
                    content = content.split("</think>")[-1].strip()
                return content
        except Exception as e:
            if attempt < max_retries:
                time.sleep(3 + attempt * 3)
                continue
            return None
    return None


def parse_json_safe(content):
    """从内容中提取JSON - 极致鲁棒"""
    if not content:
        return None
    # 1. 提取