# yamaファンのこっそり部屋

シンガー yama さんの歩みを、2018年の歌ってみたから今まで年表にまとめた有志の非公式ファンサイト。
公開先: https://yama-kossori.github.io/
保管庫（リポジトリ）: yama-kossori/yama-kossori.github.io（GitHub 組織 yama-kossori）。旧 masabee1029/yama-kossori は新しい住所への転送ページだけ（~/yama-kossori-redirect）。新しいページを足したら転送ページも足す
つくりは「Ado 非公式ワクワク秘密基地」（~/ado-himitsukichi）と同じ。

- `data/core.json` … 手で書く節目のできごと（毎月、前の月のできごとを追記）
- `python3 tools/mk_data.py` … 公式 YouTube（data/raw/raw_videos.json）・LiveFans（data/raw/livefans.json）・setlist.fm（data/raw/rows.txt）・core.json から
  `data/mv.json` / `data/timeline.json` / `data/setlists.json` を作る
- `python3 build.py` … docs/ を生成（これからの予定は ~/knowledge-os/oshi-events.js の yama 分）
- 元データの取り直し: `tools/yt_uploads.py videos > data/raw/raw_videos.json` → `tools/yt_dates.py`。LiveFans は artists/141490、setlist.fm は yama-4bf5ab66（Cloudflare のためブラウザの中で fetch）
- 画像ファイルは置かない。MV は YouTube サムネイルを直接表示して公式動画にリンク
- 広告・アフィリエイトなし。歌詞の引用なし。Google アナリティクスはほかのサイトと共通の測定 ID（ホスト名 yama-kossori.github.io で絞る）
