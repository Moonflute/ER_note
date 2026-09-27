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
abbreviations = data.get("symptomAbbreviations", [])
visible_category_order = [c["name"] for c in sorted(data["categories"], key=lambda c: (c["secondary"], c["order"])) if c["id"] in {"01", "02", "04", "08", "09", "12", "07", "06", "10"}]
require(len(sections) == len(data["sections"]), "Duplicate section IDs")
require(len(items) == sum(len(s["items"]) for s in data["sections"]), "Duplicate item IDs")
require(set(blocks) == set(provenance["assignments"]), "Source blocks not completely accounted for")
require(len({c["id"] for c in data["complaints"]}) == len(data["complaints"]), "Duplicate complaint IDs")
require(visible_category_order == ["소화기", "순환기", "신장/비뇨기", "산부", "소아", "정신", "신경", "근골격/피부", "눈/이비인후"], "Unexpected home category order")
require(len({a["label"] for a in abbreviations}) == len(abbreviations), "Duplicate symptom abbreviation labels")
require(all(a["label"] and len(a["expansion"]) > 1 and all(a["expansion"]) for a in abbreviations), "Invalid symptom abbreviation definition")
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
    pediatric_refs = [sid for sid in refs if sid.startswith("peds-")]
    if cc["scope"] == "pediatric":
        require(cc["categoryId"] == "09", f"Pediatric entry outside pediatric category: {cc['id']}")
        require(len(pediatric_refs) == len(refs), f"Adult material mixed into pediatric entry: {cc['id']}")
    else:
        require(not pediatric_refs, f"Pediatric material mixed into adult entry: {cc['id']}")
    if cc["categoryId"] == "09" and refs:
        require(cc["scope"] == "pediatric", f"Pediatric category has wrong scope: {cc['id']}")
    layout_item_ids = []
    layout_source_ids = set()
    for layout_section in cc.get("layout", {}).get("sections", []):
        require(layout_section["kind"] in ("history", "exam", "note", "example"), f"Unknown layout section kind: {cc['id']}")
        for group in layout_section["groups"]:
            for layout_item in group["items"]:
                layout_item_ids.append(layout_item["id"])
                require(bool(layout_item["sourceItemIds"]), f"Layout item lacks source items: {layout_item['id']}")
                require(set(layout_item["sourceItemIds"]) <= set(items), f"Layout item has unknown source items: {layout_item['id']}")
                if "abbreviatedText" in layout_item:
                    require(bool(layout_item["abbreviatedText"]) and layout_item["abbreviatedText"] != layout_item["text"], f"Invalid abbreviated text: {layout_item['id']}")
                layout_source_ids.update(layout_item["sourceItemIds"])
    require(len(layout_item_ids) == len(set(layout_item_ids)), f"Duplicate layout item IDs: {cc['id']}")
    if layout_item_ids:
        raw_complaint_item_ids = {item["id"] for sid in refs for item in sections[sid]["items"]}
        require(layout_source_ids == raw_complaint_item_ids, f"Curated layout source coverage mismatch: {cc['id']}")
require(used == set(sections), "Sections are unreachable")
require(not any(sid.startswith("peds-") or sid.startswith("np-") for sid in data["referenceSections"]), "Specialty material mixed into general common reference")
for specialty_id, shared_id in (("psychiatry-interview", "np-history"), ("obgyn-interview", "ob-history"), ("peds-common", "peds-history")):
    specialty = next((cc for cc in data["complaints"] if cc["id"] == specialty_id), None)
    require(specialty is not None and shared_id in specialty["sharedSectionIds"], f"Missing specialty interview entry: {specialty_id}")
require(not any(cc["id"] == "neurology-interview" for cc in data["complaints"]), "Standalone neurology interview should not be shown")
for complaint_id in ("dizziness", "headache", "seizure", "mental-change", "stroke"):
    complaint = next((cc for cc in data["complaints"] if cc["id"] == complaint_id), None)
    require(complaint is not None and "nr-history" in complaint["sharedSectionIds"], f"Shared history missing from neurologic complaint: {complaint_id}")
compact_basic = {"V/S", "CC", "PI", "Medical Hx (U/D Drug Adm Op)", "Social Hx (Alcohol Smoking)"}
for complaint_id in ("syncope", "dizziness", "headache", "seizure", "mental-change", "stroke"):
    complaint = next((cc for cc in data["complaints"] if cc["id"] == complaint_id), None)
    history_texts = {item["text"] for section in complaint.get("layout", {}).get("sections", []) if section["kind"] == "history" for group in section["groups"] for item in group["items"]} if complaint else set()
    require(compact_basic <= history_texts, f"Compact basic history missing from complaint: {complaint_id}")
layout_items = {item["id"]: item for cc in data["complaints"] for section in cc.get("layout", {}).get("sections", []) for group in section["groups"] for item in group["items"]}
expected_display_text = {
    "seizure-hx-family": "Family Hx / Personal Hx",
    "seizure-hx-medication": "Antiepileptic medication / Last dose time",
    "trauma-hx-tetanus": "Tetanus vaccination Hx",
    "pregnancy-hx-edc": "Estimated date of confinement (EDC)",
    "eye-hx-past": "OT HX",
}
for item_id, expected_text in expected_display_text.items():
    require(layout_items.get(item_id, {}).get("text") == expected_text, f"Unexpected compact display text: {item_id}")
for sid in ("np-ex1", "np-template", "np-ex2", "np-ex3", "np-response"):
    require(sections[sid]["kind"] == "example", f"Example placed in main checklist: {sid}")
for source in sources.values():
    path = ROOT / source["file"]
    if path.exists():
        require(hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"], f"Original source changed: {source['id']}")
require(audit["sourceBlocks"] == len(blocks) and audit["unassignedSourceBlocks"] == [], "Stale completeness audit")
require(audit["items"] == len(items), "Stale item audit")
require(audit["complaints"] == len(data["complaints"]), "Stale catalog audit")
require(audit["complaintsWithSourceMaterial"] == sum(cc["status"] != "missing" for cc in data["complaints"]), "Stale available entry audit")
if errors:
    print("FAIL\n" + "\n".join(errors))
    sys.exit(1)
print(f"PASS: {len(sources)} sources, {len(blocks)} source blocks, {len(items)} source-backed items, {len(data['complaints'])} complaints; no omissions or unsupported item text.")
