"""Build or update a topic from a draft file.

Usage:
  python tools/build_topic.py drafts/<id>.json            # create or replace a topic
  python tools/build_topic.py drafts/<id>.json --merge    # add new cards to an existing topic

Draft format (UTF-8 JSON):
{
  "id": "amino-acids", "title": "...", "subtitle": "...",
  "imageLabel": "מבנה", "groupLabel": "קבוצה",
  "fields": [{"key": "name", "label": "שם"}],
  "groups": ["Polar", ...],                        # optional; derived from cards when missing
  "covers": ["serine", "proline", "lysine"],       # optional card ids for the landing page
  "cards": [
    {"id": "serine", "values": {"name": "Serine"}, "group": "Polar",
     "smiles": "[NH3+]C([CH2:1][OH:1])C(=O)[O-]",                  # chemistry: drawn with RDKit
     "source_image": "path/to/page.jpg", "bbox": [x0, y0, x1, y1], # or: cropped from the sheet
     "image_file": "path/to/picture.jpg",                           # or: a ready image (credited)
     "credit": "Author, License, URL",                              # required with image_file from the web
     "verify": {"status": "ok" | "check", "sources": ["https://..."], "note": "..."}}
  ]
}
Writes public/topics/<id>/topic.json, images, sources.json and updates public/topics/index.json.
"""
import argparse, json, os, re, shutil, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
TOPICS = os.path.join(ROOT, "public", "topics")
sys.path.insert(0, os.path.dirname(__file__))

SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "item"


def load(p, default=None):
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def dump(obj, p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def make_image(card, img_dir):
    """Create the card image. Returns the image path relative to the topic folder, or None."""
    cid = card["id"]
    if card.get("smiles"):
        from render_mol import svg_file
        out = os.path.join(img_dir, f"{cid}.svg")
        svg_file(card["smiles"], out)
        return f"images/{cid}.svg"
    if card.get("source_image") and card.get("bbox"):
        from clean_image import crop_clean
        out = os.path.join(img_dir, f"{cid}.jpg")
        card["bbox"] = crop_clean(card["source_image"], card["bbox"], out, card.get("tighten", True))
        return f"images/{cid}.jpg"
    if card.get("image_file"):
        ext = os.path.splitext(card["image_file"])[1].lower() or ".jpg"
        out = os.path.join(img_dir, f"{cid}{ext}")
        shutil.copyfile(card["image_file"], out)
        return f"images/{cid}{ext}"
    return card.get("image")  # keep an existing image path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("draft")
    ap.add_argument("--merge", action="store_true", help="add new cards to an existing topic")
    a = ap.parse_args()

    draft = load(a.draft)
    tid = draft["id"]
    if not SLUG.match(tid):
        sys.exit(f"Topic id '{tid}' must be lowercase letters, digits and dashes")
    tdir = os.path.join(TOPICS, tid)
    img_dir = os.path.join(tdir, "images")
    os.makedirs(img_dir, exist_ok=True)

    old = load(os.path.join(tdir, "topic.json"), {}) if a.merge else {}
    old_sources = load(os.path.join(tdir, "sources.json"), {}) if a.merge else {}
    existing = {c["id"]: c for c in old.get("cards", [])}
    known_names = {json.dumps(c.get("values", {}), sort_keys=True, ensure_ascii=False) for c in old.get("cards", [])}

    cards, sources, skipped = list(old.get("cards", [])), dict(old_sources), []
    for c in draft["cards"]:
        c.setdefault("id", slugify(next(iter(c.get("values", {}).values()), "item")))
        key = json.dumps(c.get("values", {}), sort_keys=True, ensure_ascii=False)
        if c["id"] in existing or key in known_names:
            skipped.append(c["id"])
            continue
        image = make_image(c, img_dir)
        card = {"id": c["id"], "values": c.get("values", {}), "group": c.get("group", "")}
        if image:
            card["image"] = image
            card["origin"] = "drawn" if c.get("smiles") else "sheet" if c.get("bbox") else "web" if c.get("image_file") else c.get("origin", "sheet")
        if c.get("smiles"):
            card["smiles"] = c["smiles"]
        if c.get("credit"):
            card["credit"] = c["credit"]
        cards.append(card)
        if c.get("verify"):
            sources[c["id"]] = c["verify"]

    meta_keys = ["title", "subtitle", "imageLabel", "groupLabel", "fields", "notes"]
    topic = {"id": tid, **{k: draft.get(k, old.get(k)) for k in meta_keys if draft.get(k, old.get(k)) is not None}}
    groups = draft.get("groups") or old.get("groups") or []
    for c in cards:
        if c.get("group") and c["group"] not in groups:
            groups.append(c["group"])
    topic["groups"] = groups
    topic["cards"] = cards
    dump(topic, os.path.join(tdir, "topic.json"))
    dump(sources, os.path.join(tdir, "sources.json"))

    idx = load(os.path.join(TOPICS, "index.json"), {"topics": []})
    by_id = {c["id"]: c for c in cards}
    cover_ids = draft.get("covers") or [c["id"] for c in cards if c.get("image")][:3]
    entry = {"id": tid, "title": topic.get("title", tid), "subtitle": topic.get("subtitle", ""),
             "count": len(cards), "groups": groups,
             "covers": [by_id[i]["image"] for i in cover_ids if i in by_id and by_id[i].get("image")][:3]}
    old_entry = next((t for t in idx["topics"] if t["id"] == tid), None)
    if old_entry and not draft.get("covers") and old_entry.get("covers"):
        entry["covers"] = old_entry["covers"]
    idx["topics"] = [entry if t["id"] == tid else t for t in idx["topics"]]
    if not old_entry:
        idx["topics"].append(entry)
    dump(idx, os.path.join(TOPICS, "index.json"))

    check = [k for k, v in sources.items() if v.get("status") != "ok"]
    print(f"Topic '{tid}': {len(cards)} cards ({len(cards) - len(old.get('cards', []))} new)")
    if skipped:
        print("Skipped as duplicates:", ", ".join(skipped))
    if check:
        print("Needs review:", ", ".join(check))


if __name__ == "__main__":
    main()
