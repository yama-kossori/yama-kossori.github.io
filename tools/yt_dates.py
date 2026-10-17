#!/usr/bin/env python3
"""data/raw/raw_videos.json の各動画の公開日を watch ページから取って date を足す。"""
import json, re, urllib.request, concurrent.futures as cf
P = "data/raw/raw_videos.json"
V = json.load(open(P, encoding="utf-8"))
def d(v):
    if v.get("date"):
        return v
    s = urllib.request.urlopen(urllib.request.Request("https://www.youtube.com/watch?v=" + v["id"], headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "ja"}), timeout=30).read().decode("utf-8", "ignore")
    m = re.search(r'"(?:publishDate|uploadDate)":"(\d{4}-\d{2}-\d{2})', s) or re.search(r'itemprop="(?:datePublished|uploadDate)" content="(\d{4}-\d{2}-\d{2})', s)
    v["date"] = m.group(1) if m else ""
    return v
with cf.ThreadPoolExecutor(8) as ex:
    V = list(ex.map(d, V))
json.dump(V, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(sum(1 for v in V if v["date"]), "/", len(V))
