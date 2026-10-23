"""Check every topic before publishing. Exits with code 1 when something is wrong.

Usage: python tools/validate.py
"""
import json, os, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
TOPICS = os.path.join(ROOT, "public", "topics")


def main():
    errors, warnings = [], []
    try:
        idx = json.load(open(os.path.join(TOPICS, "index.json"), encoding="utf-8"))
    except Exception as e:
        print("index.json is missing or invalid:", e)
        sys.exit(1)

    ids = [t.get("id") for t in idx.get("topics", [])]
    if len(ids) != len(set(ids)):
        errors.append("index.json lists the same topic twice")
    for d in sorted(os.listdir(TOPICS)):
        if os.path.isdir(os.path.join(TOPICS, d)) and d not in ids:
            warnings.append(f"folder topics/{d} is not listed in index.json")

    for entry in idx.get("topics", []):
        tid = entry.get("id")
        tdir = os.path.join(TOPICS, tid or "")
        where = f"[{tid}]"
        try:
            t = json.load(open(os.path.join(tdir, "topic.json"), encoding="utf-8"))
        except Exception as e:
            errors.append(f"{where} topic.json is missing or invalid: {e}")
            continue
        for k in ("id", "title", "fields", "cards"):
            if k not in t:
                errors.append(f"{where} topic.json has no '{k}'")
        if t.get("id") != tid:
            errors.append(f"{where} id in topic.json is '{t.get('id')}'")
        keys = [f.get("key") for f in t.get("fields", [])]
        if not keys or None in keys:
            errors.append(f"{where} every field needs a key")
        groups = set(t.get("groups", []))
        seen, names = set(), set()
        for c in t.get("cards", []):
            cid = c.get("id")
            if not cid:
                errors.append(f"{where} a card has no id")
                continue
            if cid in seen:
                errors.append(f"{where} duplicate card id '{cid}'")
            seen.add(cid)
            vals = c.get("values", {})
            missing = [k for k in keys if not str(vals.get(k, "")).strip()]
            if missing:
                warnings.append(f"{where} {cid}: empty field(s) {', '.join(missing)}")
            name = json.dumps(vals, sort_keys=True, ensure_ascii=False)
            if name in names:
                errors.append(f"{where} {cid}: same values as another card")
            names.add(name)
            if groups and c.get("group") not in groups:
                errors.append(f"{where} {cid}: group '{c.get('group')}' is not in groups")
            img = c.get("image")
            if img and not os.path.isfile(os.path.join(tdir, img)):
                errors.append(f"{where} {cid}: image '{img}' not found")
            if c.get("origin") == "web" and not c.get("credit"):
                errors.append(f"{where} {cid}: image from the web needs a credit (author, license, URL)")
        if entry.get("count") != len(t.get("cards", [])):
            errors.append(f"{where} index.json count {entry.get('count')} != {len(t.get('cards', []))} cards")
        for cov in entry.get("covers", []):
            if not os.path.isfile(os.path.join(tdir, cov)):
                errors.append(f"{where} cover '{cov}' not found")
        src = os.path.join(tdir, "sources.json")
        if os.path.exists(src):
            s = json.load(open(src, encoding="utf-8"))
            todo = [c["id"] for c in t.get("cards", []) if s.get(c["id"], {}).get("status") != "ok"]
            if todo:
                warnings.append(f"{where} not verified yet: {', '.join(todo)}")
        else:
            warnings.append(f"{where} no sources.json")

    for w in warnings:
        print("warning:", w)
    for e in errors:
        print("error:", e)
    print(f"{len(ids)} topics checked: {len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
