"""Check completeness, source fidelity and references before static deployment."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "data/chief-complaints.json").read_text(encoding="utf-8"))
provenance = json.loads((ROOT / "data/content-provenance.json").read_text(encoding="utf-8"))
audit = json.loads((ROOT / "docs/content-audit.json").read_text(encoding="utf-8"))
errors = []

def require(condition, message):
    if not condition:
        errors.append(message)

def normalize(text):
    text = re.sub(r"^[①②③④⑤⑥⑦⑧⑨⑩]\s*", "", text.strip())
    text = re.sub(r"^-\s*", "", text)
    return re.sub(r"\s+", " ", text).strip()

sources = {s["id"]: s for s in provenance["sources"]}
blocks = {b["id"]: b for s in sources.values() for b in s["blocks"]}
sections = {s["id"]: s for s in data["sections"]}
items = {i["id"]: i for s in sections.values() for i in s["items"]}
categories = {c["id"] for c in data["categories"]}
require(len(sections) == len(data["sections"]), "Duplicate section IDs")
require(len(items) == sum(len(s["items"]) for s in data["sections"]), "Duplicate item IDs")
require(set(blocks) == set(provenance["assignments"]), "Source blocks not completely accounted for")
require(len({c["id"] for c in data["complaints"]}) == len(data["complaints"]), "Duplicate complaint IDs")
linked = Counter()
pdf_additions = {a[0]: a[1] for a in provenance["pdfAdditions"]}
for bid, assignments in provenance["assignments"].items():
    require(bool(assignments), f"Empty source mapping: {bid}")
    for a in assignments:
        if a["type"] not in ("item", "pdfAddition"):
            require(a["type"] in ("structure", "alternateRendition"), f"Unknown mapping type: {bid}")
            continue
        sid, iid = a["sectionId"], a["itemId"]
        require(sid in sections and iid in items, f"Broken target: {bid}")
        if sid not in sections or iid not in items:
            continue
        require(iid in {i["id"] for i in sections[sid]["items"]}, f"Wrong section mapping: {bid}")
        expected = normalize(blocks[bid]["text"]) if a["type"] == "item" else pdf_additions.get(iid)
        require(items[iid]["text"] == expected, f"Unsupported or altered item text: {iid}")
        if a["type"] == "pdfAddition":
            require(re.sub(r"\s", "", expected or "") in re.sub(r"\s", "", blocks[bid]["text"]), f"PDF addition not in page: {iid}")
        linked[iid] += 1
require(set(linked) == set(items), "Items lacking source provenance")
for section in sections.values():
    require(section["kind"] in ("history", "exam", "note", "example"), f"Unknown section kind: {section['id']}")
    if section["kind"] == "example":
        require(all(linked[i["id"]] == 1 for i in section["items"]), f"Merged distinct example occurrences: {section['id']}")
used = set(data["referenceSections"])
for cc in data["complaints"]:
    require(cc["categoryId"] in categories, f"Unknown category: {cc['id']}")
    refs = cc["sectionIds"] + cc["sharedSectionIds"]
    used.update(refs)
    require(set(refs) <= set(sections), f"Broken complaint section: {cc['id']}")
    require(bool(refs) == (cc["status"] != "missing"), f"Wrong material status: {cc['id']}")
    require(cc["scope"] in ("general", "pediatric", "psychiatric"), f"Unknown scope: {cc['id']}")
require(used == set(sections), "Sections are unreachable")
for sid in ("np-ex1", "np-template", "np-ex2", "np-ex3", "np-response"):
    require(sections[sid]["kind"] == "example", f"Example placed in main checklist: {sid}")
for source in sources.values():
    path = ROOT / source["file"]
    if path.exists():
        require(hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"], f"Original source changed: {source['id']}")
require(audit["sourceBlocks"] == len(blocks) and audit["unassignedSourceBlocks"] == [], "Stale completeness audit")
require(audit["items"] == len(items), "Stale item audit")
if errors:
    print("FAIL\n" + "\n".join(errors))
    sys.exit(1)
print(f"PASS: {len(sources)} sources, {len(blocks)} source blocks, {len(items)} source-backed items, {len(data['complaints'])} complaints; no omissions or unsupported item text.")
