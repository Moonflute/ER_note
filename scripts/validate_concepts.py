"""Validate concept coverage, citations and the short-form content budget offline."""
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / "data/cc-concepts.json").read_text(encoding="utf-8"))
chief = json.loads((ROOT / "data/chief-complaints.json").read_text(encoding="utf-8"))
errors = []


def require(condition, message):
    if not condition:
        errors.append(message)


def keys(node, expected, location):
    require(set(node) == set(expected.split()), f"Unexpected fields: {location}")


def text(value, maximum, location):
    require(isinstance(value, str) and bool(value.strip()), f"Missing text: {location}")
    if not isinstance(value, str):
        return
    require(value == value.strip() and "\n" not in value, f"Uncurated whitespace: {location}")
    require(len(value) <= maximum, f"Text budget exceeded: {location} ({len(value)} > {maximum})")
    require(not re.search(r"<[^>]+>|\[.*?\]\(|\(\s*(?:/\s*)*\)", value), f"Markup or blank answer slots: {location}")


keys(data, "schemaVersion contentVersion sources complaints", "root")
require(data["schemaVersion"] == 1, "Unknown concept schema version")
text(data["contentVersion"], 40, "contentVersion")
sources = {source["id"]: source for source in data["sources"]}
require(bool(sources) and len(sources) == len(data["sources"]), "Missing or duplicate source IDs")
for source_id, source in sources.items():
    keys(source, "id title url publisher locator accessedAt access", source_id)
    require(bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", source_id)), f"Invalid source ID: {source_id}")
    for field in ("title", "publisher", "locator"):
        text(source[field], 250, f"{source_id}.{field}")
    parsed = urlparse(source["url"])
    require(parsed.scheme == "https" and bool(parsed.netloc), f"Invalid reference URL: {source_id}")
    try:
        date.fromisoformat(source["accessedAt"])
    except (ValueError, TypeError):
        require(False, f"Invalid access date: {source_id}")
    require(source["access"] in ("full-text", "publisher-excerpt"), f"Unknown reference access: {source_id}")

available = {cc["id"]: cc for cc in chief["complaints"] if cc["status"] != "missing"}
concept_ids = [cc["complaintId"] for cc in data["complaints"]]
require(set(concept_ids) == set(available), f"Concept coverage mismatch: missing={sorted(set(available) - set(concept_ids))}, extra={sorted(set(concept_ids) - set(available))}")
require(len(concept_ids) == len(set(concept_ids)), "Duplicate concept complaint IDs")
used_sources = set()
node_count = 0
largest = (0, "")


def references(node, location):
    global node_count
    ids = node["sourceIds"]
    require(bool(ids) and len(ids) == len(set(ids)), f"Missing or duplicate citations: {location}")
    require(set(ids) <= set(sources), f"Unknown source IDs: {location}")
    used_sources.update(ids)
    node_count += 1


for concept in data["complaints"]:
    complaint_id = concept["complaintId"]
    keys(concept, "complaintId scope differentials hx pex caution", complaint_id)
    if complaint_id not in available:
        continue
    complaint = available[complaint_id]
    require(concept["scope"] == complaint["scope"], f"Adult/pediatric/psychiatric scope mismatch: {complaint_id}")
    layout_ids = {item["id"] for section in complaint.get("layout", {}).get("sections", [])
                  for group in section["groups"] for item in group["items"]}
    require(3 <= len(concept["differentials"]) <= 4, f"Differential count exceeds short-form budget: {complaint_id}")
    require(1 <= len(concept["hx"]) <= 3 and 2 <= len(concept["pex"]) <= 3,
            f"Missing Hx/PEx interpretation or too many rows: {complaint_id}")
    require(len(concept["hx"]) + len(concept["pex"]) <= 5, f"Hx/PEx row budget exceeded: {complaint_id}")
    clinical_text = []
    for index, differential in enumerate(concept["differentials"]):
        location = f"{complaint_id}.differentials[{index}]"
        keys(differential, "disease clues sourceIds", location)
        text(differential["disease"], 30, location + ".disease")
        text(differential["clues"], 60, location + ".clues")
        clinical_text.extend([differential["disease"], differential["clues"]])
        references(differential, location)
    require(len({d["disease"] for d in concept["differentials"]}) == len(concept["differentials"]), f"Duplicate differentials: {complaint_id}")
    for kind in ("hx", "pex"):
        require(len({item["label"] for item in concept[kind]}) == len(concept[kind]), f"Duplicate labels: {complaint_id}.{kind}")
        for index, item in enumerate(concept[kind]):
            location = f"{complaint_id}.{kind}[{index}]"
            keys(item, "label meaning itemIds sourceIds", location)
            text(item["label"], 50, location + ".label")
            text(item["meaning"], 60, location + ".meaning")
            clinical_text.extend([item["label"], item["meaning"]])
            require(len(item["itemIds"]) == len(set(item["itemIds"])) and set(item["itemIds"]) <= layout_ids,
                    f"Unknown or unrelated questionnaire item: {location}")
            references(item, location)
    keys(concept["caution"], "text sourceIds", complaint_id + ".caution")
    text(concept["caution"]["text"], 60, complaint_id + ".caution.text")
    clinical_text.append(concept["caution"]["text"])
    references(concept["caution"], complaint_id + ".caution")
    length = sum(map(len, clinical_text))
    require(length <= 420, f"Total text budget exceeded: {complaint_id} ({length} > 420)")
    require(not [value for value, count in Counter(clinical_text).items() if count > 1], f"Repeated text: {complaint_id}")
    largest = max(largest, (length, complaint_id))

require(used_sources == set(sources), "Unreferenced source records")
workflow = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
require("python3 scripts/validate_concepts.py" in workflow, "Concept validator missing from CI")
require("data/cc-concepts.json _site/data/" in workflow, "Concept data missing from Pages package")
require("app.js sw.js .nojekyll" in workflow, "Service worker missing from Pages package")
if errors:
    print("FAIL\n" + "\n".join(errors))
    sys.exit(1)
print(f"PASS: {len(concept_ids)} concepts, {len(sources)} references, {node_count} cited clinical rows; max {largest[0]}/420 characters ({largest[1]}).")
