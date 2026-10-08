"""Validate concept coverage/citations offline; flag density for clinical review."""
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


def keys(node, expected, location, optional=""):
    fields = set(node)
    required = set(expected.split())
    require(required <= fields <= required | set(optional.split()), f"Unexpected fields: {location}")


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
dense = []
review = (ROOT / "docs/개념 검토.md").read_text(encoding="utf-8")


def references(node, location):
    global node_count
    ids = node["sourceIds"]
    require(bool(ids) and len(ids) == len(set(ids)), f"Missing or duplicate citations: {location}")
    require(set(ids) <= set(sources), f"Unknown source IDs: {location}")
    used_sources.update(ids)
    node_count += 1


def validate_flow(concept):
    complaint_id = concept["complaintId"]
    flow = concept["flow"]
    keys(flow, "entry conceptRefs sourceIds stages notes", complaint_id + ".flow")
    text(flow["entry"], 80, complaint_id + ".flow.entry")
    references(flow, complaint_id + ".flow")
    clinical = [flow["entry"], concept["caution"]["text"]]
    canonical = {(kind, item.get("label", item.get("disease"))): item
                 for kind in ("differentials", "hx", "pex") for item in concept[kind]}
    covered = set()

    def concept_refs(node, location):
        pairs = []
        for ref in node["conceptRefs"]:
            keys(ref, "kind key", location + ".conceptRefs")
            pair = (ref["kind"], ref["key"])
            require(pair in canonical, f"Unknown clinical concept: {location} {pair}")
            if pair in canonical:
                require(set(canonical[pair]["sourceIds"]) <= set(node["sourceIds"]),
                        f"Original concept citations lost: {location} {pair}")
            pairs.append(pair)
        require(bool(pairs) and len(pairs) == len(set(pairs)), f"Missing/duplicate concept refs: {location}")
        covered.update(pairs)

    concept_refs(flow, complaint_id + ".flow")
    require(bool(flow["stages"]), f"Empty flow stages: {complaint_id}")
    ids = []
    for stage in flow["stages"]:
        location = complaint_id + ".flow." + stage["id"]
        keys(stage, "id question priority sourceIds branches", location)
        ids.append(stage["id"])
        require(stage["priority"] in ("urgent", "standard"), f"Unknown clinical priority: {location}")
        text(stage["question"], 80, location + ".question")
        clinical.append(stage["question"])
        references(stage, location)
        require(bool(stage["branches"]), f"Empty branches: {location}")
        for branch in stage["branches"]:
            branch_location = location + "." + branch["id"]
            keys(branch, "id when check consider conceptRefs sourceIds", branch_location, "note")
            ids.append(branch["id"])
            for field in ("when", "check", "consider"):
                text(branch[field], 80, branch_location + "." + field)
                clinical.append(branch[field])
            if "note" in branch:
                text(branch["note"], 80, branch_location + ".note")
                clinical.append(branch["note"])
            references(branch, branch_location)
            concept_refs(branch, branch_location)
    for index, note in enumerate(flow["notes"]):
        location = f"{complaint_id}.flow.notes[{index}]"
        keys(note, "text sourceIds", location, "conceptRefs")
        text(note["text"], 80, location)
        clinical.append(note["text"])
        references(note, location)
        if "conceptRefs" in note:
            concept_refs(note, location)
    require(all(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", id) for id in ids)
            and len(ids) == len(set(ids)), f"Invalid/duplicate flow IDs: {complaint_id}")
    require(covered == set(canonical), f"Clinical meaning lost from flow: {complaint_id} {set(canonical) - covered}")
    return clinical


for concept in data["complaints"]:
    complaint_id = concept["complaintId"]
    keys(concept, "complaintId scope differentials hx pex caution", complaint_id, "flow")
    if complaint_id not in available:
        continue
    complaint = available[complaint_id]
    require(concept["scope"] == complaint["scope"], f"Adult/pediatric/psychiatric scope mismatch: {complaint_id}")
    layout_ids = {item["id"] for section in complaint.get("layout", {}).get("sections", [])
                  for group in section["groups"] for item in group["items"]}
    require(len(concept["differentials"]) >= 3, f"Missing differential overview: {complaint_id}")
    require(len(concept["hx"]) >= 1 and len(concept["pex"]) >= 2,
            f"Missing Hx/PEx interpretation: {complaint_id}")
    require(f"`{complaint_id}`" in review, f"Missing CC clinical review record: {complaint_id}")
    clinical_text = []
    for index, differential in enumerate(concept["differentials"]):
        location = f"{complaint_id}.differentials[{index}]"
        keys(differential, "disease clues sourceIds", location)
        text(differential["disease"], 30, location + ".disease")
        text(differential["clues"], 80, location + ".clues")
        clinical_text.extend([differential["disease"], differential["clues"]])
        references(differential, location)
    require(len({d["disease"] for d in concept["differentials"]}) == len(concept["differentials"]), f"Duplicate differentials: {complaint_id}")
    for kind in ("hx", "pex"):
        require(len({item["label"] for item in concept[kind]}) == len(concept[kind]), f"Duplicate labels: {complaint_id}.{kind}")
        for index, item in enumerate(concept[kind]):
            location = f"{complaint_id}.{kind}[{index}]"
            keys(item, "label meaning itemIds sourceIds", location)
            text(item["label"], 50, location + ".label")
            text(item["meaning"], 80, location + ".meaning")
            clinical_text.extend([item["label"], item["meaning"]])
            require(len(item["itemIds"]) == len(set(item["itemIds"])) and set(item["itemIds"]) <= layout_ids,
                    f"Unknown or unrelated questionnaire item: {location}")
            references(item, location)
    keys(concept["caution"], "text sourceIds", complaint_id + ".caution")
    text(concept["caution"]["text"], 80, complaint_id + ".caution.text")
    clinical_text.append(concept["caution"]["text"])
    references(concept["caution"], complaint_id + ".caution")
    if "flow" in concept:
        clinical_text = validate_flow(concept)
    length = sum(map(len, clinical_text))
    if length > 500:
        dense.append((complaint_id, length))
        require(f"<!-- density: {complaint_id} -->" in review,
                f"Needs documented density review, not deletion of clinical content: {complaint_id} ({length} characters)")
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
print(f"PASS: {len(concept_ids)} concepts, {len(sources)} references, {node_count} cited clinical rows; max {largest[0]} characters ({largest[1]}).")
if dense:
    print("Density reviewed (>500 characters): " + ", ".join(f"{id} {length}" for id, length in dense))
