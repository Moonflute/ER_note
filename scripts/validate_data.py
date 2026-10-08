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
category_records = {c["id"]: c for c in data["categories"]}
categories = set(category_records)
home_groups = sorted(data["homeGroups"], key=lambda group: group["order"])
home_group_order = {group["id"]: group["order"] for group in home_groups}
abbreviations = data.get("symptomAbbreviations", [])
abbreviation_labels = {a["label"] for a in abbreviations}
visible_category_ids = {cc["categoryId"] for cc in data["complaints"] if cc["status"] != "missing"}
visible_category_order = [c["name"] for c in sorted(data["categories"], key=lambda c: (home_group_order[c["homeGroupId"]], c["order"])) if c["id"] in visible_category_ids]
require(len(sections) == len(data["sections"]), "Duplicate section IDs")
require(len(items) == sum(len(s["items"]) for s in data["sections"]), "Duplicate item IDs")
require(set(blocks) == set(provenance["assignments"]), "Source blocks not completely accounted for")
require(len({c["id"] for c in data["complaints"]}) == len(data["complaints"]), "Duplicate complaint IDs")
require([(group["id"], group["name"]) for group in home_groups] == [("adult", "성인"), ("pediatric", "소아"), ("psychiatric", "정신")], "Unexpected home group order")
require(all(category["homeGroupId"] in home_group_order for category in data["categories"]), "Category has an unknown home group")
require(visible_category_order == ["소화기", "순환기", "신장/비뇨기", "산부", "신경", "근골격/피부", "눈/이비인후", "외상", "소아", "정신"], "Unexpected home category order")
require("00" not in categories and not any(cc["categoryId"] == "00" for cc in data["complaints"]), "Admission management category must not be shown")
complaint_categories = {cc["id"]: cc["categoryId"] for cc in data["complaints"]}
require(all(complaint_categories.get(item_id) == "13" for item_id in ("trauma", "head-trauma", "inhalation-burn", "poisoning")), "Trauma category membership is incorrect")
require(complaint_categories.get("cardiac-arrest") == "02", "Cardiac arrest should remain in circulation")
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
item_section = {item["id"]: sid for sid, section in sections.items() for item in section["items"]}
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
                if "abbreviation" in layout_item:
                    require(layout_item["abbreviation"] in abbreviation_labels, f"Unknown item abbreviation: {layout_item['id']}")
                if "compactText" in layout_item or "compactRow" in layout_item:
                    require(bool(layout_item.get("compactText")) and bool(layout_item.get("compactRow")), f"Incomplete compact display metadata: {layout_item['id']}")
                layout_source_ids.update(layout_item["sourceItemIds"])
                used.update(item_section[item_id] for item_id in layout_item["sourceItemIds"])
    require(len(layout_item_ids) == len(set(layout_item_ids)), f"Duplicate layout item IDs: {cc['id']}")
    if layout_item_ids:
        raw_complaint_item_ids = {item["id"] for sid in refs for item in sections[sid]["items"]}
        require(raw_complaint_item_ids <= layout_source_ids, f"Curated layout source coverage mismatch: {cc['id']}")
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
require(layout_items.get("headache-pe-shoulder", {}).get("text") == "Shoulder tenderness", "Confirmed Td meaning is not reflected")
require(layout_items.get("eye-pe-lom", {}).get("text") == "LOM", "Unconfirmed LOM was expanded")
require(layout_items.get("trauma-pe-ent-level", {}).get("text") == "Ear or neck laceration: Neck level", "Unconfirmed neck level was changed")
require(layout_items.get("fever-hx-vaccination", {}).get("text") == "Vaccination Hx / Recent vaccination before fever", "Pediatric fever vaccination questions are incomplete")
require({layout_items[item_id].get("abbreviation") for item_id in ("abd-hx-fccsr", "abd-hx-anvcd", "abd-hx-fundhis")} == {"FCCSR", "ANVCD", "FUND HIS"}, "Abdominal ROS abbreviations are not independently checkable")
require([layout_items[item_id].get("compactRow") for item_id in ("dizz-hx-basic", "dizz-hx-cc", "dizz-hx-pi", "dizz-hx-medical", "dizz-hx-social")] == ["basic", "basic", "basic", "history", "history"], "Neurologic compact history rows are not grouped correctly")
expected_history_group_order = {
    "abdominal-pain": ["여성 환자", "History", "Review of systems"],
    "constipation": ["Bowel habit", "History", "Review of systems"],
    "chest-pain": ["Present illness", "History"],
    "syncope": ["Basic", "Syncope", "Background", "Review of systems"],
    "hematuria": ["Urinary symptoms"],
    "urinary-symptoms": ["Urinary symptoms"],
    "incontinence": ["Urinary symptoms"],
    "back-pain": ["Present illness"],
    "trauma": ["Present illness", "3세 미만 열상", "10세 이하 열상", "Nasal bone fracture", "교통사고", "상해"],
    "head-trauma": ["Present illness"],
    "testicular": ["Present illness"],
    "oral-dental": ["Present illness"],
    "poisoning": ["Exposure · Intent"],
    "inhalation-burn": ["Symptoms"],
    "cardiac-arrest": ["Arrival"],
    "dizziness": ["Basic", "Dizziness", "Background", "Review of systems"],
    "headache": ["Basic", "Headache", "Background", "Review of systems"],
    "seizure": ["Basic", "Ictal", "Postictal · Background", "Background", "Review of systems"],
    "mental-change": ["Basic", "Background", "Review of systems"],
    "stroke": ["Basic", "Time", "Background", "Review of systems"],
    "psychiatry-interview": ["Basic", "Safety · Mood", "Perceptual disturbance", "Current function", "Past psychiatric · Family history", "Social history"],
    "obgyn-interview": ["Symptoms", "Gynecologic history"],
    "pregnancy": ["Current pregnancy", "Obstetric history", "Gynecologic history"],
    "peds-common": ["Basic", "Birth history", "Review of systems"],
    "fever": ["Basic", "Fever", "Birth history", "Review of systems"],
    "vomiting": ["Basic", "Vomiting", "Birth history", "Review of systems"],
    "diarrhea": ["Basic", "Diarrhea", "Birth history", "Review of systems"],
    "cough": ["Basic", "Cough", "Birth history", "Review of systems"],
    "peds-abdominal-pain": ["Basic", "Abdominal pain", "Birth history", "Review of systems"],
    "peds-seizure": ["Basic", "Seizure", "Birth history", "Review of systems"],
    "eye": ["Symptoms", "Past history"],
    "throat": ["Symptoms"],
    "ear": ["Symptoms · Exposure"],
    "epistaxis": ["Present illness", "History"],
}
history_layout_ids = {
    cc["id"]
    for cc in data["complaints"]
    if any(section["kind"] == "history" for section in cc.get("layout", {}).get("sections", []))
}
require(history_layout_ids == set(expected_history_group_order), "History layout order audit is incomplete")
for complaint_id, expected_titles in expected_history_group_order.items():
    complaint = next(cc for cc in data["complaints"] if cc["id"] == complaint_id)
    history = next(section for section in complaint["layout"]["sections"] if section["kind"] == "history")
    require([group["title"] for group in history["groups"]] == expected_titles, f"Symptom history order is incorrect: {complaint_id}")
require(layout_items["hematuria-hx-chief"]["text"] == "Hematuria", "Hematuria chief symptom is not independently checkable")
require(layout_items["incontinence-hx-chief"]["text"] == "Incontinence", "Incontinence chief symptom is not independently checkable")
for item_id in ("hematuria-hx-fundhis", "urinary-hx-fundhis", "incontinence-hx-fundhis"):
    require(layout_items[item_id].get("abbreviatedText") == "FUND HIS", f"Urinary symptom set is not compacted correctly: {item_id}")
for prefix in ("peds-common", "fever", "vomiting", "diarrhea", "cough", "peds-abd", "peds-seizure"):
    require(f"{prefix}-hx-neonate-growth" in layout_items and f"{prefix}-hx-neonate-delivery" in layout_items, f"Pediatric birth history is not split: {prefix}")
for item_id in ("ob-hx-bleeding", "ob-hx-discharge", "pregnancy-hx-bleeding", "pregnancy-hx-discharge", "dizz-pe-upper-coordination", "dizz-pe-lower-coordination", "dizz-pe-positional"):
    require(item_id in layout_items, f"Long checklist item was not split: {item_id}")
app_source = (ROOT / "app.js").read_text(encoding="utf-8")
index_source = (ROOT / "index.html").read_text(encoding="utf-8")
service_worker_source = (ROOT / "sw.js").read_text(encoding="utf-8")
require("common-shortcut" not in app_source and "#common" not in app_source, "Removed common shortcut is still rendered")
require("catalog-tools" not in app_source and '${matching.length}' not in app_source, "Home catalog count is still rendered")
require(all(token in app_source for token in ("orderedHomeGroups", "home-group-title", "home-group-single")), "Home groups are not rendered")
require('serviceWorker.register("./sw.js")' in app_source, "Service worker is not registered")
for asset in ("./styles.css?v=24", "./app.js?v=38", "./data/chief-complaints.json?v=23", "./data/cc-concepts.json?v=4"):
    require(asset in service_worker_source, f"Offline cache asset is stale: {asset}")
require('./styles.css?v=24' in index_source and './app.js?v=38' in index_source, "HTML asset versions do not match offline cache")
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
