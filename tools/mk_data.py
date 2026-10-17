#!/usr/bin/env python3
"""集めた元データ（data/raw/）から data/mv.json・data/timeline.json・data/setlists.json を作る。

- data/raw/raw_videos.json … yama 公式 YouTube の全動画（tools/yt_uploads.py + tools/yt_dates.py）
- data/raw/feat_raw.json   … ほかのアーティストの公式チャンネルにある feat. / BIN の動画
- data/raw/livefans.json   … LiveFans の出演記録（日本語の公演名・会場名）
- data/raw/rows.txt        … setlist.fm の 112 公演（日付|ID|会場|曲番号）。曲番号は SONGS の順
- data/core.json           … 手で書いた節目のできごと（デビュー・リリース・タイアップなど）
毎月の更新では core.json に足すか、raw を取り直してこのスクリプト → build.py の順に走らせる。
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
J = lambda p: json.load(open(os.path.join(ROOT, p), encoding="utf-8"))

# setlist.fm のローマ字曲名 → 日本語（rows.txt の曲番号の順）
SONGS = ["蛹", "色彩", "U and I", "TWILIGHT", "Remember", "midnight", "マジカルシンドローム", "Oz.", "クリーム", "Dawn",
         "飛ぼうよ", "血流", "Kyogan", "Downtown", "ハロ", "麻痺", "あるいは映画のような", "mountain", "a.m.3:21", "春を告げる",
         "偽顔", "くびったけ", "rain check", "憧れのままに", "slash", "UPSIDE DOWN", "End roll", "TORIHADA", "Hikari no Yoru", "それでも僕は",
         "masquerade", "飛ぶ時", "Hanamushiro", "雫", "新星", "イノセント", "BURN", "doku", "Downtown", "希望論",
         "us", "Amairo", "タルト", "Blue Monday", "桃源郷", "愛を解く", "Ever", "真っ白", "アダルトチックチルドレン", "砂の城",
         "semicolon", "世界は美しいはずなんだ", "陽だまり", "Nagisa", "沫雪", "こだま", "オリジン", "MoonWalker", "独白", "パレットは透明",
         "一寸の赤", "ライカ", "ストロボ", "ランニングアウト"]
assert len(SONGS) == 64
NOTE = {"behind the curtain partly performed": "幕の後ろで一部だけ", "TV ver.": "TV サイズ", "Vaundy cover": "Vaundy のカバー",
        "☆Taku Takahashi remix": "☆Taku Takahashi リミックス", "safmusic remix": "safmusic リミックス", "KO3 remix": "KO3 リミックス",
        "imase cover": "imase のカバー", "with Tatsuya Kitani": "キタニタツヤと", "THE FIRST TAKE version": "THE FIRST TAKE バージョン"}
SEC = {"Encore": "アンコール", "Set 1": ""}
MON = {m: i + 1 for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}

# setlist.fm にだけある海外公演など（日付 → 公演名, 都市, 会場）
SF_ONLY = {
    "2022-05-29": ("SAPPORO COLLECTION 2022 SPRING/SUMMER", "北海道", "札幌コンベンションセンター"),
    "2022-11-19": ("TGC KITAKYUSHU 2022", "福岡県", "西日本総合展示場 新館"),
    "2023-07-29": ("Impactnation Japan Festival 2023", "インドネシア・ジャカルタ", "Istora Gelora Bung Karno"),
    "2024-05-02": ("Bubbling & Boiling Music and Arts Tianjin 2024", "中国・天津", "Dongjiang Seaside Music Plaza"),
    "2024-12-01": ("Clockenflap 2024", "香港", "Central Harbourfront Event Space"),
    "2025-07-12": ("BILIBILI MACRO LINK 2025", "中国・上海", "National Exhibition and Convention Center"),
    "2025-07-25": ("Crunchyroll Anime FanFest 2025", "アメリカ・サンディエゴ", "The Rady Shell at Jacobs Park"),
    "2026-07-10": ("Japan Expo 2026", "フランス・パリ", "Parc des Expositions de Paris-Nord Villepinte"),
    "2026-08-21": ("Anime NYC 2026", "アメリカ・ニューヨーク", "Javits Center（メインステージ）"),
}
# yama 本人のツアー（setlist.fm の海外公演をまとめる分）
SF_TOURS = {
    "yama 1st ASIA TOUR \"thanks for waiting\"": {"2023-11-28": ("マレーシア・クアラルンプール", "Zepp Kuala Lumpur"), "2023-11-29": ("シンガポール", "Capitol Theatre"),
                                                  "2023-12-01": ("フィリピン・マニラ", "The Podium"), "2023-12-03": ("タイ・バンコク", "The Portal Ballroom")},
    "yama Asia Tour 2025「虎視眈々」": {"2025-10-11": ("韓国・ソウル", "YES24 WANDERLOCH HALL"), "2025-10-12": ("韓国・ソウル", "YES24 WANDERLOCH HALL"),
                                   "2025-10-16": ("台湾・台北", "Legacy TERA"), "2025-10-17": ("台湾・高雄", "Live warehouse"),
                                   "2025-10-20": ("シンガポール", "Capitol Theatre"), "2025-10-22": ("香港", "MacPherson Stadium")},
    "Australian Tour 袋鼠爆走": {"2026-10-16": ("オーストラリア・メルボルン", "Northcote Theatre"), "2026-10-17": ("オーストラリア・シドニー", "Liberty Hall")},
}
# LiveFans の公演名 → yama のツアー名（1 つにまとめて "shows" に入れる）
OWN_TOURS = [
    (r"1st LIVE TOUR「meaning of life」", "1st LIVE TOUR「meaning of life」", "はじめての有観客ツアー（大阪・東京）。"),
    (r'"the meaning of life" TOUR 2021', "\"the meaning of life\" TOUR 2021", "初の全国ツアー（9 都市 10 公演）。ファイナルの Zepp DiverCity 公演は映像作品になりました。"),
    (r"軌道共鳴 2022", "yama×ACIDMAN 東名阪対バンツアー「軌道共鳴 2022」", "ACIDMAN との対バンツアー。"),
    (r'"the meaning of life" TOUR 2022', "\"the meaning of life\" TOUR 2022", "全国 10 か所 12 公演。Zepp DiverCity 公演は映像作品になりました。"),
    (r"acoustic live tour 2023|^yama$", "yama acoustic live tour 2023「夜と閃き」", "アコースティック編成のツアー。"),
    (r"Christmas Special Live 2023", "yama Christmas Special Live 2023", "ホールで歌うクリスマスの特別公演。"),
    (r'"the meaning of life" TOUR 2024', "\"the meaning of life\" TOUR 2024", "青森から沖縄まで、全国 20 都市 21 公演。LINE CUBE SHIBUYA 公演は 2025 年に劇場上映されました。"),
    (r"軌道共鳴2024", "対バンツアー「軌道共鳴2024」", ""),
    (r"Life is Beautiful 2024", "Life is Beautiful 2024", "大阪・東京のホール公演。東京公演の全編は「アダルトチックチルドレン」の Blu-ray 付きの盤に収録。"),
    (r"the meaning of life TOUR 2025", "the meaning of life TOUR 2025", "4th アルバム『; semicolon』を携えた全国ツアー。"),
    (r"versus the night 2\.0", "CLUB yama 会員限定ライブ「versus the night 2.0」", "ファンクラブ会員限定のライブ。"),
    (r"C\.U\.Tリリースツアー", "yama C.U.T リリースツアー「羽化」", "EP『C.U.T』のリリースツアー（全 6 公演）。"),
]
TV = re.compile(r"CDTV|音楽の日|FNS|MUSIC STATION|ミュージックステーション")
SKIP = {"Haruno 2025 Tour \"Familiar\"", "yama 1st 配信LIVE『Versus the night』"}  # 出演者に yama の名前がない記録・core.json と重複
RENAME = {"Versus The Night 0.0": "2nd 配信ライブ「Versus The Night 0.0」", "yama special online live 『Early Summer Nights』": "yama special online live「Early Summer Nights」"}
# 公演の公式ライブ映像（mv.json のキー）を年表の項目にのせる
LIVE_VIDEOS = {"Versus The Night 0.0": ["live:あるいは映画のような（ライブ映像）", "live:タルト〜クローバー（ライブ映像）"],
               "Early Summer Nights": ["live:ストロボ（“Special Online Live「Early Summer Nights」“ 2023.05.23）", "live:slash（“Special Online Live「Early Summer Nights」“ 2023.05.23）"],
               "\"the meaning of life\" TOUR 2022": ["live:色彩（“the meaning of life“ TOUR 2022 at Zepp DiverCity 2022.10.8）", "live:くびったけ（“the meaning of life“ TOUR 2022 at Zepp DiverCity 2022.10.8）", "live:ライカ（“the meaning of life“ TOUR 2022 at Zepp DiverCity 2022.10.8）"],
               "夜と閃き": ["live:新星（acoustic live tour 2023 “夜と閃き“ at GORILLA HALL OSAKA）"],
               "\"the meaning of life\" TOUR 2024": ["live:色彩（the meaning of life）"],
               "\"the meaning of life\" TOUR 2021": ["live:春を告げる（ライブ映像）", "live:麻痺（ライブ映像）"]}


def mk_mv():
    V = J("data/raw/raw_videos.json")
    mv = {}
    rank = lambda t: 0 if re.search(r"Music Video|MV|Official Video", t) and "Teaser" not in t and "メイキング" not in t else (1 if "Lyric" in t or "lyric" in t else 2)
    for v in sorted(V, key=lambda v: v["date"]):
        t = v["title"]
        m = re.match(r"\[cover\]\s*(.+?)\s*/\s*yama", t)
        if m:
            mv["cover:" + m.group(1)] = {"id": v["id"], "title": f"{m.group(1)}（歌ってみた）", "kind": "歌ってみた", "yt_date": v["date"]}
            continue
        if re.search(r"teaser|Teaser|ティザー|トレーラー|Trailer|PV$| PV|TV SPOT", t):
            continue
        if re.search(r"Official Live Video|Studio Live|ACOUSTIC LIVE|配信ライブ|配信LIVE」|from “the meaning|億回再生記念", t):
            m = re.search(r"『(.+?)』|「(.+?)」", t)
            if m:
                song = m.group(1) or m.group(2)
                where = "Life is beautiful 2024" if "億回" in t else re.sub(r".*?(“|\"|\()(.+?)(”|\"|\)).*", r"\2", t) if re.search(r"“|\(", t) else "ライブ映像"
                if "Versus the night」Ver" in t or "1st 配信ライブ" in t:
                    where = "Versus the night"
                key = f"live:{song}" if "億回" in t else f"live:{song}（{where}）"
                mv.setdefault(key, {"id": v["id"], "title": t, "kind": "ライブ映像", "yt_date": v["date"]})
            continue
        m = re.search(r"『(.+?)』|「(.+?)」|yama - (.+?) +\(Official Video\)", t)
        if not m or re.search(r"Trailer|trailer|teaser|Teaser|試聴|視聴|SPOT|メイキング|behind|開封|楽屋|dialogue|対談|ラジオ|ダイジェスト|お知らせ", t):
            continue
        song = (m.group(1) or m.group(2) or m.group(3)).strip()
        song = re.sub(r"\s*[(（](prod\.|Movie|with\.|feat\.).*$", "", song)
        if "×" in t and "yama × " in t or "✕" in t:
            song = re.sub(r"『|』", "", song)
        old = mv.get(song)
        if old and rank(old["title"]) <= rank(t):
            continue
        mv[song] = {"id": v["id"], "title": t, "kind": "オリジナル", "yt_date": v["date"]}
    for f in J("data/raw/feat_raw.json"):
        mv["feat:" + f["song"]] = {"id": f["id"], "title": f["title"], "kind": "feat", "by": f["by"], "yt_date": f["date"]}
    mv["Hello/Hello"] = {"id": "zj_X7PS8cpk", "title": "Hello/Hello feat. yama, 泣き虫☔(Bedroom ver.) – MAISONdes", "kind": "feat", "by": "MAISONdes", "yt_date": "2021-01-24"}
    return mv


def sf_rows():
    out = []
    for r in open(os.path.join(RAW, "rows.txt"), encoding="utf-8").read().strip().split(";"):
        d, sid, venue, s = r.split("|")
        y, mo, da = d.split("-")
        date = f"{y}-{MON[mo]:02d}-{int(da):02d}"
        songs = []
        for x in [x for x in s.split(",") if x]:
            if x.startswith("#"):
                lab = SEC.get(x[1:], x[1:])
                if lab:
                    songs.append({"sec": lab})
                continue
            n, _, note = x.partition("^")
            it = {"t": SONGS[int(n)]}
            if note:
                it["n"] = NOTE.get(note, note)
            songs.append(it)
        out.append({"date": date, "sfid": sid, "venue": venue, "url": f"https://www.setlist.fm/setlist/yama/{y}/x-{sid}.html", "songs": songs})
    return out


def place_of(v):
    m = re.search(r"\(([^()]+)\)\s*$", v)
    return m.group(1) if m else ""


def clean_venue(v):
    return re.sub(r"\s*\([^()]+\)\s*$", "", v).strip()


def mk_lives(sf):
    LF = J("data/raw/livefans.json")
    ev, tours = [], {}
    for x in LF:
        t = x["title"]
        if t in SKIP:
            continue
        if TV.search(t):
            ev.append({"date": x["date"], "cat": "media", "title": f"テレビ「{t}」に出演", "note": f"{clean_venue(x['venue'])}。", "big": False})
            continue
        for pat, name, note in OWN_TOURS:
            if re.search(pat, t):
                tours.setdefault(name, {"note": note, "shows": []})["shows"].append(
                    {"date": x["date"], "place": place_of(x["venue"]) or "オンライン", "venue": clean_venue(x["venue"])})
                break
        else:
            v = clean_venue(x["venue"])
            online = "オンライン" in v
            pl = place_of(x["venue"])
            note = ("オンラインで開催。" if online else f"{pl}・{v}。")
            title = RENAME.get(t) or (t if re.search(r"yama", t) else f"「{t}」に出演")
            ev.append({"date": x["date"], "cat": "live", "title": title, "note": note, "big": False})
    for name, d in SF_TOURS.items():
        tours[name] = {"note": "", "shows": [{"date": k, "place": p, "venue": v} for k, (p, v) in sorted(d.items())]}
    tours["yama 1st ASIA TOUR \"thanks for waiting\""]["note"] = "初のアジアツアー。クアラルンプール・シンガポール・マニラ・バンコク・台北の 5 都市。"
    tours["yama 1st ASIA TOUR \"thanks for waiting\""]["shows"].append({"date": "2023-12-05", "place": "台湾・新北", "venue": "Zepp New Taipei"})
    tours["yama Asia Tour 2025「虎視眈々」"]["note"] = "ソウル・台北・高雄・シンガポール・香港をめぐるアジアツアー（計約 7,000 人）。"
    tours["Australian Tour 袋鼠爆走"]["note"] = "初のオーストラリア公演。"
    # LiveFans 側の台北公演（ASIA TOUR 2023）は上でまとめたので消す
    ev = [e for e in ev if not (e["date"] == "2023-12-05")]
    for name, d in tours.items():
        shows = sorted(d["shows"], key=lambda s: s["date"])
        big = len(shows) >= 5 or "ASIA" in name.upper() or "Asia" in name
        ev.append({"date": shows[0]["date"], "cat": "live", "title": f"『{name}』", "note": d["note"], "big": big, "shows": shows})
    for e in ev:
        for k, vids in LIVE_VIDEOS.items():
            if k in e["title"]:
                e["videos"] = [v for v in vids if v in MV]
    for date, (name, pl, v) in SF_ONLY.items():
        ev.append({"date": date, "cat": "live", "title": f"「{name}」に出演", "note": f"{pl}・{v}。", "big": "NYC" in name or "Expo" in name})
    return ev


def mk_releases():
    """公式サイトの Music に載っている配信・CD のうち、core.json に無いもの。"""
    R = [("2021-02-22", "名前のない日々へ", "配信", "セブン-イレブンのオリジナル WEB アニメ「レインボーファインダー」#2 テーマソング。"),
         ("2021-03-25", "一寸の赤", "配信", "セブン-イレブンのオリジナル WEB アニメ「レインボーファインダー」#3 テーマソング。"),
         ("2021-05-28", "カーテンコール", "配信", "ABEMA『恋愛ドラマな恋がしたい〜KISS or kiss〜』主題歌。"),
         ("2021-06-21", "Sleepless Night", "配信", "フジテレビ系月 9 ドラマ「ナイト・ドクター」オリジナルナンバー。"),
         ("2021-10-22", "Oz.", "配信", "TV アニメ「王様ランキング」エンディング・テーマ。"),
         ("2022-02-23", "the meaning of life TOUR 2021 at Zepp DiverCity", "映像作品", "初の全国ツアーのファイナル公演を収めた Blu-ray / DVD。"),
         ("2022-03-07", "MoonWalker", "配信", ""),
         ("2022-06-22", "桃源郷", "配信", ""),
         ("2022-11-09", "色彩", "CD シングル", "「色彩」の CD シングル。"),
         ("2023-02-22", "the meaning of life TOUR 2022 at Zepp DiverCity", "映像作品", "2022 年ツアーの Zepp DiverCity 公演を収めた Blu-ray / DVD。"),
         ("2023-07-12", "返光", "配信", "映画『スイート・マイホーム』主題歌（Movie Edition）。"),
         ("2023-09-20", "憧れのままに", "配信", "yama × キタニタツヤ。"),
         ("2023-10-18", "パレットは透明", "配信", ""),
         ("2024-02-28", "こだま", "配信", ""),
         ("2024-04-27", "声明", "配信", "SusHi Tech Tokyo 2024 コラボレーション。"),
         ("2024-10-31", "オリジン", "配信", ""),
         ("2025-02-05", "BURN", "CD シングル", "yama × WurtS。"),
         ("2025-04-23", "春を告げる（☆Taku Takahashi Remix）", "配信", ""),
         ("2025-06-11", "GRIDOUT", "CD シングル", ""),
         ("2025-07-09", "us", "配信", ""),
         ("2025-08-20", "doku", "配信 EP", ""),
         ("2025-10-03", "アダルトチックチルドレン", "配信", "TV アニメ「SANDA」オープニング主題歌（CD は 12 月 10 日）。"),
         ("2025-10-29", "季節の灯", "配信", "トリビュート盤「ACIDMAN Tribute Works」収録のカバー。"),
         ("2026-07-14", "U and I", "配信", "")]
    out = []
    for d, n, k, note in R:
        tie = "tieup" if re.search(r"主題歌|テーマ|オリジナルナンバー|コラボ", note) else "release"
        out.append({"date": d, "cat": tie, "title": f"{k}「{n}」" + ("発売" if "CD" in k or "映像" in k else "リリース"), "note": note, "big": False,
                    "videos": [n] if n in MV else []})
    return out


def mk_covers():
    out = []
    for k, m in MV.items():
        if m["kind"] == "歌ってみた" and k not in ("cover:暖かい生き物", "cover:bin"):
            out.append({"date": m["yt_date"], "cat": "cover", "title": f"「{k[6:]}」を歌ってみた", "note": "YouTube に投稿。", "big": False, "videos": [k]})
    for k, m in MV.items():
        if m["kind"] == "feat" and k not in ("feat:チルドレン", "feat:ねむるまち"):
            name = k.split(":", 1)[-1]
            who = "BIN（ボーカル・山上）" if m["by"] == "BIN" else m["by"]
            out.append({"date": m["yt_date"], "cat": "feat", "title": f"{who}「{name}」" + ("の MV 公開" if m["by"] == "BIN" else "に参加"),
                        "note": "", "big": False, "videos": [k]})
    return out


MV = mk_mv()
if __name__ == "__main__":
    sf = sf_rows()
    T = J("data/core.json") + mk_releases() + mk_covers() + mk_lives(sf)
    T.sort(key=lambda e: e["date"])
    json.dump(MV, open(os.path.join(ROOT, "data", "mv.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(T, open(os.path.join(ROOT, "data", "timeline.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    sl = [{"date": x["date"], "sfid": x["sfid"], "url": x["url"], "songs": x["songs"]} for x in sf if x["songs"]]
    json.dump(sl, open(os.path.join(ROOT, "data", "setlists.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"mv {len(MV)}, timeline {len(T)}（ツアー公演の展開前）, setlists {len(sl)}")
