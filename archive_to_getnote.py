#!/usr/bin/env python3
"""归档整个项目到Get笔记
- 单笔记上限40KB
- 分门别类:文档/代码/网页/数据
- 分片时每片带索引头"""
import urllib.request, urllib.error
import json, os, time, sys, hashlib

API_KEY = os.environ["GETNOTE_API_KEY"]
CLIENT_ID = os.environ["GETNOTE_CLIENT_ID"]
BASE = "https://openapi.biji.com"
HEADERS = {"Authorization": API_KEY, "X-Client-ID": CLIENT_ID, "Content-Type": "application/json"}
MAX_CONTENT = 38000  # 留6KB缓冲给分片头/markdown包装/JSON尾巴

# ---------- 工具 ----------
def call(path, body):
    req = urllib.request.Request(f"{BASE}{path}", data=json.dumps(body).encode(), headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: err = json.loads(e.read().decode())
        except: err = {"message": e.read().decode()[:200]}
        return {"success": False, "error": err.get("error", err)}
    except Exception as e:
        return {"success": False, "error": {"message": str(e)}}

def save_note(title, content, tags=None):
    body = {"title": title[:200], "content": content, "note_type": "plain_text"}
    if tags: body["tags"] = tags
    return call("/open/api/v1/resource/note/save", body)

def split_for_md(content, max_size, file_header):
    """分片:第一片带文件头,中间/最后片带分片标记"""
    if len(content) <= max_size:
        return [f"{file_header}\n\n{content}"]
    total = (len(content) + max_size - 1) // max_size
    pieces = []
    for i in range(total):
        chunk = content[i*max_size:(i+1)*max_size]
        if i == 0:
            pieces.append(f"{file_header}\n\n{chunk}")
        else:
            pieces.append(f"**[分片 {i+1}/{total}]**\n\n{chunk}")
    return pieces

def md_wrap(content, lang):
    return f"