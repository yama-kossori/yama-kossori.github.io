#!/usr/bin/env python3
"""yama 公式 YouTube（UClbieOB_NYcY9TlIthmyw-A）の動画タブを全件たどって [{id, title}] を JSON で出す（API キー不要）。"""
import json, re, sys, urllib.request

UA = {"User-Agent": "Mozilla/5.0", "Accept-Language": "ja"}

def get(url, data=None):
    h = dict(UA)
    if data is not None:
        h["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    return urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=30).read().decode("utf-8", "ignore")

def collect(o, vids, conts):
    if isinstance(o, dict):
        if "videoId" in o and "title" in o and ("lengthText" in o or "thumbnailOverlays" in o):
            t = o["title"]
            title = t.get("simpleText") or "".join(r.get("text", "") for r in t.get("runs", []))
            vids.append({"id": o["videoId"], "title": title})
        if "lockupViewModel" in o and o["lockupViewModel"].get("contentType") == "LOCKUP_CONTENT_TYPE_VIDEO":
            l = o["lockupViewModel"]
            title = l.get("metadata", {}).get("lockupMetadataViewModel", {}).get("title", {}).get("content", "")
            vids.append({"id": l["contentId"], "title": title})
        if "continuationItemRenderer" in o:
            for t in re.findall(r'"token": "([^"]+)"', json.dumps(o["continuationItemRenderer"])):
                conts.append(t)
        for v in o.values():
            collect(v, vids, conts)
    elif isinstance(o, list):
        for v in o:
            collect(v, vids, conts)

def main(tab="videos"):
    s = get(f"https://www.youtube.com/channel/UClbieOB_NYcY9TlIthmyw-A/{tab}?hl=ja")
    key = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', s).group(1)
    ver = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', s).group(1)
    data = json.loads(re.search(r"var ytInitialData = (\{.*?\});</script>", s).group(1))
    vids, conts = [], []
    collect(data, vids, conts)
    seen = set()
    while conts:
        tok = conts.pop()
        if tok in seen:
            continue
        seen.add(tok)
        r = json.loads(get(f"https://www.youtube.com/youtubei/v1/browse?key={key}",
                           {"context": {"client": {"clientName": "WEB", "clientVersion": ver, "hl": "ja"}}, "continuation": tok}))
        collect(r, vids, conts)
    out, ids = [], set()
    for v in vids:
        if v["id"] not in ids:
            ids.add(v["id"]); out.append(v)
    return out

if __name__ == "__main__":
    res = main(sys.argv[1] if len(sys.argv) > 1 else "videos")
    print(json.dumps(res, ensure_ascii=False))
