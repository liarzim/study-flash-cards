"""Make a single self-contained HTML review page for a topic (all cards, status, sources).

Usage: python tools/preview.py <topic-id> [out.html]
The page embeds the images, so it can be opened anywhere or published for review.
"""
import base64, html, json, mimetypes, os, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
TOPICS = os.path.join(ROOT, "public", "topics")


def data_uri(path):
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


def main():
    tid = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else f"preview-{tid}.html"
    tdir = os.path.join(TOPICS, tid)
    t = json.load(open(os.path.join(tdir, "topic.json"), encoding="utf-8"))
    src_path = os.path.join(tdir, "sources.json")
    sources = json.load(open(src_path, encoding="utf-8")) if os.path.exists(src_path) else {}
    fields = t.get("fields", [])
    e = html.escape

    rows = []
    for g in t.get("groups") or [""]:
        cards = [c for c in t["cards"] if (c.get("group") or "") == g] if t.get("groups") else t["cards"]
        if not cards:
            continue
        tiles = []
        for c in cards:
            s = sources.get(c["id"], {})
            status = s.get("status", "none")
            chip = {"ok": ("ok", "אומת"), "check": ("check", "לבדוק")}.get(status, ("none", "ללא מקור"))
            img = f'<img src="{data_uri(os.path.join(tdir, c["image"]))}" alt="">' if c.get("image") else '<span class="noimg">ללא תמונה</span>'
            vals = "".join(f'<div><span class="k">{e(f["label"])}</span> {e(str(c["values"].get(f["key"], "")))}</div>' for f in fields)
            links = " ".join(f'<a href="{e(u)}" target="_blank" rel="noopener">מקור {i + 1}</a>' for i, u in enumerate(s.get("sources", [])))
            note = f'<div class="note">{e(s["note"])}</div>' if s.get("note") else ""
            credit = f'<div class="note">{e(c["credit"])}</div>' if c.get("credit") else ""
            tiles.append(f'<article class="tile"><div class="plate">{img}</div><div class="body">'
                         f'<span class="chip {chip[0]}">{chip[1]}</span>{vals}<div class="src">{links}</div>{note}{credit}'
                         f'<div class="id">{e(c["id"])}</div></div></article>')
        head = f'<h2>{e(g)} <span class="n">{len(cards)}</span></h2>' if g else ""
        rows.append(head + '<div class="grid">' + "".join(tiles) + "</div>")

    total = len(t["cards"])
    ok = sum(1 for c in t["cards"] if sources.get(c["id"], {}).get("status") == "ok")
    page = f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(t.get('title', tid))} review</title>
<style>
:root{{--bg:#f3f6f8;--card:#fff;--ink:#15232f;--muted:#5a6b78;--line:#d6dfe6;--ok:#1e7a4c;--okbg:#e3f4ea;--ck:#9a6b00;--ckbg:#fdf3d6;--plate:#fff}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0f171d;--card:#16212a;--ink:#e4edf3;--muted:#93a5b2;--line:#2a3a46;--ok:#5fd39a;--okbg:#16352a;--ck:#f0c560;--ckbg:#3a3018;--plate:#f6f8fa;color-scheme:dark}}}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,"Segoe UI",Arial,sans-serif}}
.wrap{{max-width:1100px;margin:0 auto;padding:20px max(16px,env(safe-area-inset-left,0px))}}
h1{{margin:0 0 4px;font-size:1.8rem}} h2{{font-size:1.15rem;margin:26px 0 10px}} .n{{color:var(--muted);font-weight:400}}
.sum{{color:var(--muted)}} .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}}
.tile{{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}}
.plate{{background:var(--plate);height:150px;display:flex;align-items:center;justify-content:center;padding:8px;border-bottom:1px solid var(--line)}}
.plate img{{width:100%;height:100%;object-fit:contain}} .noimg{{color:#888;font-size:.85rem}}
.body{{padding:10px 12px;display:flex;flex-direction:column;gap:3px;font-size:.9rem}} .k{{color:var(--muted)}}
.chip{{align-self:flex-start;font-size:.75rem;border-radius:99px;padding:0 9px;border:1px solid var(--line);margin-bottom:4px}}
.chip.ok{{background:var(--okbg);color:var(--ok);border-color:var(--ok)}} .chip.check,.chip.none{{background:var(--ckbg);color:var(--ck);border-color:var(--ck)}}
.src a{{color:inherit;font-size:.8rem;margin-inline-end:8px}} .note{{color:var(--muted);font-size:.8rem}} .id{{color:var(--muted);font:12px ui-monospace,monospace;direction:ltr;text-align:left}}
</style></head><body><div class="wrap">
<h1>{e(t.get('title', tid))}</h1><div class="sum">{total} כרטיסיות · {ok} אומתו · {total - ok} לבדיקה</div>
{''.join(rows)}
</div></body></html>"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print("wrote", out)


if __name__ == "__main__":
    main()
