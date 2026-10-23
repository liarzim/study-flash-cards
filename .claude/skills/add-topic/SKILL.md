---
name: add-topic
description: Add, update or extend a topic on the Study Flash Cards site (liarzim/study-flash-cards) from a study sheet (image, PDF or Word) the admin sends. Use for "נושא חדש", "הוסף לנושא", "עדכן נושא", or any edit to topics, cards, groups or images on that site.
---

# Add or update a Study Flash Cards topic

The admin (Michael) sends study material in chat. You turn it into a verified topic, show a review page, and publish only after he approves. Students only study on the site; there is no upload on the site itself.

- Repo: `liarzim/study-flash-cards` (public). Live site: https://study-flash-cards-eta.vercel.app
- Every push to `main` deploys on Vercel in about a minute.
- Admin's local copy: `C:\Users\micha\Downloads\Claude\Projects\study-flash-cards`

## 0. Get the repo

If the repo is not in the session, attach it with `add_repo` (owner `liarzim`, repo `study-flash-cards`, access `push`) and clone it. Install tools once: `pip install --break-system-packages -r tools/requirements-dev.txt`.

## 1. Understand the request

Work out which case it is, and ask only if it is unclear:
- **New topic**: a new folder under `public/topics/`.
- **Add material**: new cards in an existing topic (`build_topic.py --merge`; duplicates are skipped and reported).
- **Edit**: rename, fix text, move a card to another group, delete or reorder cards, replace an image. Edit `drafts/<id>.json` and rebuild without `--merge`, or edit `topic.json` directly for small text fixes.

Read the material yourself (look at every page). List the items, the text fields per item (for example name, abbreviation, definition) and the groups exactly as written on the sheet. Field labels are in Hebrew; item text stays in the sheet's language.

## 2. Verify every item against the web

Each item needs at least one independent source, two when possible. Record them in the draft's `verify` block (`status`, `sources`, `note`).
- **Chemistry**: if the ChEMBL connector is available, look each compound up there. Otherwise use Wikipedia pages (WebFetch). PubChem blocks automated access from these tools, so don't rely on it. Check the formula or side chain against the source (compute it from the SMILES with RDKit).
- **Other subjects**: Wikipedia or another reliable reference for each term.
- If a source disagrees with the sheet, keep the sheet's wording, set `status: "check"`, and explain in `note`.
- Never mark `ok` without a source you actually read.

## 3. Images

- **Chemical structures**: write a Kekulé SMILES of the form drawn on the sheet (charges included, e.g. zwitterions). Mark the side chain or the highlighted part with atom class 1 (`[CH2:1]`). `tools/render_mol.py` draws all molecules in one textbook style, same scale, side chain up and shaded gray.
- **Everything else (default)**: crop from the admin's sheet. Give `source_image` and a normalized `bbox` that holds the whole drawing and none of the label text that reveals the answer. `tools/clean_image.py` tightens the box to the ink and cleans the photo. Check each crop by looking at it.
- **Web images**: only when the admin asks. Use only public-domain, CC0 or CC BY / BY-SA images (for example Wikimedia Commons), give `image_file` and `credit` ("Author, License, URL"). Don't use images whose license you can't confirm.

## 4. Build

Write `drafts/<id>.json` (format documented at the top of `tools/build_topic.py`), then:

```
python tools/build_topic.py drafts/<id>.json            # new topic or full rebuild
python tools/build_topic.py drafts/<id>.json --merge    # add new cards only
python tools/validate.py                                # must end with 0 errors
python tools/preview.py <id> <scratchpad>/preview-<id>.html
```

Topic ids are lowercase English with dashes (`functional-groups`). Card ids too.

## 5. Review with the admin

Publish the preview HTML as an Artifact and tell him in two or three lines: how many cards, how many verified, which need his attention and why. Wait for his approval. Apply his corrections, rebuild, and show the preview again when the change is visible.

## 6. Publish (only after approval)

1. `python tools/validate.py` with 0 errors.
2. Commit with a clear message and the session's attribution lines, then `git push origin main`.
3. Wait for the Vercel status on the commit: `gh api repos/liarzim/study-flash-cards/commits/<sha>/statuses --jq '.[0].state'` until `success` (or `failure`, then read the deployment page).
4. Open the live site and confirm the topic shows and its images load.
5. Sync the admin's local copy when his computer is linked: in his folder run `git pull` (git needs delete permission there for its lock files; request it once with `device_request_delete_permission`).

Report the result in a few lines: what changed, the live link, anything still marked for review.

## Rules

- Never publish without the admin's approval of the review page.
- Never invent sources or mark unverified items as verified.
- Keep `public/topics/index.json` in sync (the build script does this; validate checks it).
- Don't change the site's code or design while adding content unless the admin asks.
