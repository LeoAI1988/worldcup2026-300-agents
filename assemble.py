#!/usr/bin/env python3
"""把数据塞进HTML模板,生成最终index.html"""
import json

with open("/workspace/worldcup2026/index_template.html", "r", encoding="utf-8") as f:
    template = f.read()

with open("/workspace/worldcup2026/page_data.json", "r", encoding="utf-8") as f:
    page_data = json.load(f)

# 替换placeholder
final_html = template.replace("__PAGE_DATA_PLACEHOLDER__", json.dumps(page_data, ensure_ascii=False))

with open("/workspace/worldcup2026/index.html", "w", encoding="utf-8") as f:
    f.write(final_html)

import os
print(f"最终HTML生成: index.html ({os.path.getsize('/workspace/worldcup2026/index.html')/1024:.1f}KB)")
