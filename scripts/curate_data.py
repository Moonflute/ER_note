"""Reproducible source-only curation. Assignments change organization, not medicine."""
from pathlib import Path
from collections import defaultdict
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs"
DATA.mkdir(exist_ok=True)
DOCS.mkdir(exist_ok=True)
archive = json.loads((ROOT / "working/sources/source-extracts.json").read_text(encoding="utf-8"))
blocks = {b["id"]: b for s in archive["sources"] for b in s["blocks"]}
assignments = defaultdict(list)
groups = {}

KINDS = {"history": "문진", "exam": "진찰", "note": "인계 메모", "example": "차팅 예시"}

def clean(text):
    # Only whitespace and a leading bullet change. Answer slots and words stay.
    text = re.sub(r"^[①②③④⑤⑥⑦⑧⑨⑩]\s*", "", text.strip())
    text = re.sub(r"^-\s*", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def pick(sid, specs):
    numbers = []
    for spec in specs.split(","):
        if "-" in spec:
            first, last = map(int, spec.split("-"))
            numbers.extend(range(first, last + 1))
        else:
            numbers.append(int(spec))
    return [f"{sid}:document:p{n}" for n in numbers if f"{sid}:document:p{n}" in blocks]

def add(gid, title, kind, sid, specs, condition=None):
    group = groups.setdefault(gid, {"id": gid, "title": title, "kind": kind, "items": []})
    for bid in pick(sid, specs):
        b = blocks[bid]
        text = clean(b["text"])
        key = (text, condition)
        # Repeated results belong to their own example and must keep their position.
        found = None if kind == "example" else next((x for x in group["items"] if (x["text"], x.get("condition")) == key), None)
        if found is None:
            seed = gid + "|" + text + "|" + str(condition) + ("|" + bid if kind == "example" else "")
            iid = "i-" + hashlib.sha256(seed.encode()).hexdigest()[:12]
            found = {"id": iid, "text": text}
            if condition:
                found["condition"] = condition
            group["items"].append(found)
        assignments[bid].append({"type": "item", "sectionId": gid, "itemId": found["id"]})

# Shared sections are tied to the specialty scope of the source heading.
add("routine-history", "공통 문진", "history", "templates", "2-4")
add("routine-exam", "공통 진찰", "exam", "templates", "6-7")
add("nr-history", "신경과 공통 문진", "history", "templates", "83,85-86,88-92")
add("nr-history", "신경과 공통 문진", "history", "all", "46,49-50,52-54,56")
add("peds-history", "소아 공통 문진", "history", "templates", "147-151")
add("peds-history", "소아 공통 문진", "history", "all", "203-207")
add("peds-exam", "소아 공통 진찰", "exam", "templates", "153-158")
add("peds-exam", "소아 공통 진찰", "exam", "all", "210-216")
add("np-history", "정신과 공통 문진", "history", "np-docx", "4-5,14-16,33-34,39-43,59-61")
add("np-history", "정신과 공통 문진", "history", "np-docx", "35-36", "정신과적 과거력 있는 분")
add("np-history", "정신과 공통 문진", "history", "np-docx", "37", "정신과적 과거력 없는 분")
add("np-history", "정신과 공통 문진", "history", "np-docx", "47", "Sleep")
add("np-response", "정신과 수면·생활력 응답 예시", "example", "np-docx", "44-46", "Sleep")
add("np-response", "정신과 수면·생활력 응답 예시", "example", "np-docx", "48-49", "Appetite")
add("np-response", "정신과 수면·생활력 응답 예시", "example", "np-docx", "50-52", "Smoking (필수x)")
add("np-response", "정신과 수면·생활력 응답 예시", "example", "np-docx", "53-55", "Alcohol (필수x)")
add("np-response", "정신과 수면·생활력 응답 예시", "example", "np-docx", "56-57", "Caffeine (불안, 두근거림)")
add("np-history", "정신과 공통 문진", "history", "templates", "125,127-130,132-144")
add("np-note", "정신과 인계 메모", "note", "templates", "123-124")
add("np-example", "정신과 응답 예시", "example", "np-docx", "6-11,17-28")
add("np-ex1", "정신과 차팅 예시 1", "example", "np-docx", "63-73")
add("np-template", "정신과 차팅 양식", "example", "np-docx", "75-83")
add("np-ex2", "정신과 차팅 예시 2", "example", "np-docx", "85-95")
add("np-ex3", "정신과 차팅 예시 3", "example", "np-docx", "97-107")
add("np-note", "정신과 인계 메모", "note", "np-docx", "2-3")

# GI.
add("abd-history", "복통 문진", "history", "handover", "50-52")
add("abd-history", "복통 문진", "history", "all", "27,29-31,36-37")
add("abd-exam", "복통 진찰", "exam", "handover", "53")
add("abd-exam", "복통 진찰", "exam", "all", "32-34")
add("abd-note", "복통 인계 메모", "note", "handover", "44-47,56-59,62-67")
add("abd-note", "복통 인계 메모", "note", "all", "39")
add("constipation-history", "변비 문진", "history", "all", "42-44")
add("peds-abd-history", "소아 복통 문진", "history", "templates", "170")
add("peds-abd-history", "소아 복통 문진", "history", "all", "234")
add("peds-abd-mixed", "소아 복통 문진과 진찰", "exam", "templates", "171-172")
add("peds-abd-mixed", "소아 복통 문진과 진찰", "exam", "all", "235-236")
add("peds-vomit", "소아 구토 문진", "history", "templates", "163")
add("peds-vomit", "소아 구토 문진", "history", "all", "224")
add("peds-diarrhea", "소아 설사 문진", "history", "templates", "165-166")
add("peds-diarrhea", "소아 설사 문진", "history", "all", "227-228")

# Cardiovascular and neurologic.
add("chest-history", "흉통 문진", "history", "templates", "64-70")
add("syncope-history", "실신 문진", "history", "all", "96-100")
add("syncope-mixed", "실신 문진과 진찰", "exam", "templates", "111")
add("syncope-note", "실신 인계 메모", "note", "all", "95")
add("headache-history", "두통 문진", "history", "templates", "57,102-104")
add("headache-history", "두통 문진", "history", "all", "70-79")
add("headache-exam", "두통 진찰", "exam", "all", "80-81")
add("dizziness-history", "어지럼 문진", "history", "all", "84-87,90")
add("dizziness-history", "어지럼 문진", "history", "templates", "106")
add("dizziness-history", "어지럼 문진", "history", "handover", "97,105")
add("dizziness-exam", "어지럼 진찰", "exam", "templates", "105,107-108")
add("dizziness-exam", "어지럼 진찰", "exam", "all", "88,92")
add("dizziness-exam", "어지럼 진찰", "exam", "handover", "98-99")
add("dizziness-note", "어지럼 인계 메모", "note", "all", "89,93")
add("dizziness-note", "어지럼 인계 메모", "note", "handover", "92-93,96,102")
add("dizziness-example", "어지럼 차팅 예시", "example", "all", "140-163")
add("stroke-history", "뇌졸중 문진", "history", "templates", "94")
add("stroke-history", "뇌졸중 문진", "history", "all", "59")
add("stroke-exam", "신경학적 진찰 원문", "exam", "templates", "95-101")
add("stroke-exam", "신경학적 진찰 원문", "exam", "all", "60-66")
add("stroke-note", "뇌졸중 인계 메모", "note", "templates", "93")
add("stroke-note", "뇌졸중 인계 메모", "note", "all", "58")
add("seizure-history", "성인 경련 문진", "history", "all", "105-118")
add("seizure-history", "성인 경련 문진", "history", "templates", "112-115")
add("mental-exam", "의식장애 진찰", "exam", "templates", "116-119")
add("mental-exam", "의식장애 진찰", "exam", "all", "122-128")

# Respiratory, fever, urinary.
add("peds-cough", "소아 기침 문진", "history", "templates", "168")
add("peds-cough", "소아 기침 문진", "history", "all", "231")
add("peds-fever", "소아 발열 문진", "history", "templates", "36,38,160-161")
add("peds-fever", "소아 발열 문진", "history", "all", "219-221")
add("peds-fever-exam", "소아 발열 진찰", "exam", "templates", "40-46")
add("peds-fever-example", "소아 발열 차팅 예시", "example", "templates", "35")
add("urinary-history", "배뇨증상 문진", "history", "templates", "61")
add("flank-note", "옆구리 통증 인계 메모", "note", "handover", "71-73,76-77")

# Musculoskeletal / dermatology / trauma.
add("msk-exam", "근골격 진찰", "exam", "templates", "10")
add("trauma-history", "외상 문진", "history", "all", "289-293,308,312-313")
add("trauma-history", "외상 문진", "history", "handover", "14,19")
add("trauma-history", "외상 문진", "history", "handover", "23", "3세 미만 열상")
add("trauma-history", "외상 문진", "history", "handover", "26", "교통사고")
add("trauma-history", "외상 문진", "history", "handover", "32", "상해")
add("trauma-exam", "외상 진찰", "exam", "all", "295-303,309-311")
add("trauma-exam", "외상 진찰", "exam", "templates", "13-15")
add("trauma-exam", "외상 진찰", "exam", "handover", "27", "교통사고")
add("trauma-note", "외상 인계 메모", "note", "handover", "11-13,15,18,20-22")
add("trauma-note", "외상 인계 메모", "note", "handover", "28-29", "교통사고")
add("trauma-note", "외상 인계 메모", "note", "handover", "33-34", "상해")
add("trauma-note", "외상 인계 메모", "note", "all", "287-288")
add("trauma-example", "외상 차팅 예시", "example", "all", "316-326")
add("headtrauma-history", "두부외상 문진", "history", "templates", "18")
add("headtrauma-exam", "두부외상 진찰", "exam", "templates", "19")
add("back-mixed", "비외상성 등·허리 통증 문진과 진찰", "exam", "handover", "37")
add("back-note", "비외상성 등·허리 통증 인계 메모", "note", "handover", "38-39")
add("rash-note", "피부 발진 인계 메모", "note", "handover", "81-83,86-88")

# OBGY.
add("ob-history", "산부인과 공통 문진", "history", "all", "6,8-11")
add("pregnancy-history", "산모 문진", "history", "all", "14-20")
add("ob-note", "산부인과 인계 메모", "note", "all", "1-4,23")

# Pediatrics: values in seizure examples are not converted into patient questions.
add("peds-seizure-history", "소아 경련 문진", "history", "templates", "28-32")
add("peds-seizure-example", "소아 경련 차팅 예시", "example", "templates", "27")
add("peds-seizure-example", "소아 경련 차팅 예시", "example", "all", "239-286")

# Eyes / ENT.
add("ear-history", "귀 증상 문진", "history", "templates", "22-25")
add("ear-history", "귀 증상 문진", "history", "all", "132-133")
add("ear-example", "귀 증상 차팅 예시", "example", "all", "167-186")
add("epistaxis-mixed", "코피 문진과 진찰", "exam", "all", "136-137")
add("epistaxis-note", "코피 인계 메모", "note", "all", "138")
add("eye-history", "눈 증상 문진", "history", "all", "189-194,198,200")
add("eye-exam", "눈 증상 진찰", "exam", "all", "195-196")
add("eye-note", "눈 증상 인계 메모", "note", "all", "201")
add("handover-general", "B구역 인계 메모", "note", "handover", "4-6")

# Visible PDF-only annotations. The rest is an alternate rendition, verified visually.
pdf_additions = [
    ("np-pdf-summary", "가서 물어볼 것들: C.C, o/s, 과거력, 누구와 함께 사는지, 직업, 내원 당시 증상, 최근 stress factor, compliance, sleep/appetite, suicidal idea/plan/attempt", "np-pdf:page1"),
    ("np-pdf-firstline", "맨 앞줄 : 정신과 진료 동의하고, 협조적이며 원활한 대화가능함.", "np-pdf:page2"),
    ("np-pdf-template-label", "복붙와꾸", "np-pdf:page2"),
]
for iid, text, bid in pdf_additions:
    groups["np-note"]["items"].append({"id": iid, "text": text})
    assignments[bid].append({"type": "pdfAddition", "sectionId": "np-note", "itemId": iid})
for b in archive["sources"][2]["blocks"]:
    assignments[b["id"]].append({"type": "alternateRendition", "canonicalSourceId": "np-docx", "verification": "PDF 2페이지 시각 확인. 추가 요약·차팅 문구는 별도 보존."})

# Curated layouts are presentation-ready views over the preserved source items.
# They may merge duplicate wording, expand confirmed abbreviations and separate
# instructions into notes without changing or discarding the source archive.
def view_item(iid, text, source_item_ids, note=None):
    item = {"id": iid, "text": text, "sourceItemIds": source_item_ids}
    if note:
        item["note"] = note
    return item

curated_layouts = {
    "abdominal-pain": {
        "sections": [
            {"id": "abd-view-history", "title": "Hx", "kind": "history", "groups": [
                {"title": "과거력·복용약", "items": [
                    view_item("abd-hx-background", "Underlying disease / Medication Hx / Operation Hx", ["i-a0dbc0b8eaec"]),
                    view_item("abd-hx-operation", "Abdominal operation Hx", ["i-eb4aa9826a2d", "i-ecedeb1e4880"], "반드시 확인"),
                    view_item("abd-hx-npo", "NPO time", ["i-23c56e483dfc"], "수술 가능성이 있는 경우"),
                ]},
                {"title": "Review of systems", "items": [
                    view_item("abd-hx-fccsr", "Fever / Chill / Cough / Sputum / Rhinorrhea", ["i-473758685a66", "i-a5938abb78b4"]),
                    view_item("abd-hx-anvcd", "Anorexia / Nausea / Vomiting / Constipation / Diarrhea", ["i-473758685a66", "i-39ebda833786", "i-c4bf0295923d"]),
                    view_item("abd-hx-fundhis", "Frequency / Urgency / Nocturia / Dysuria / Hesitancy / Incomplete emptying / Straining", ["i-a7cf0271f916"]),
                ]},
                {"title": "여성 환자", "items": [
                    view_item("abd-hx-pregnancy", "임신 가능성 / LMP", ["i-9a089b00c222"]),
                    view_item("abd-hx-female", "Menstruation / Last coitus / 보호자 관계", ["i-f26b6ccefee9", "i-99dd425247e3"], "가임기 여성의 하복부 통증에서는 보호자와의 관계를 고려하여 확인"),
                ]},
            ]},
            {"id": "abd-view-exam", "title": "PEx", "kind": "exam", "groups": [
                {"title": "HEENT", "items": [
                    view_item("abd-pe-heent", "Throat injection / Tonsil enlargement", ["i-e8c7079dbc3e"]),
                ]},
                {"title": "Chest", "items": [
                    view_item("abd-pe-chest", "Lung sound: Clear", ["i-e8c7079dbc3e"]),
                ]},
                {"title": "Abdomen", "items": [
                    view_item("abd-pe-bowel", "Bowel sound: Normoactive", ["i-a40910290557"]),
                    view_item("abd-pe-tenderness", "Abdominal Td / rTd / Muscle guarding", ["i-a40910290557", "i-4e56e4043370", "i-99e95de58023"], "rTd 판단이 어려우면 percussion tenderness를 확인. 환자의 통증 호소만으로 기록하지 말고 진찰자가 판단하여 전공의에게 알림"),
                    view_item("abd-pe-cvat", "CVAT", ["i-48f8724d8595", "i-2983d5754b6e"], "반드시 확인"),
                ]},
            ]},
            {"id": "abd-view-reference", "title": "참고사항", "kind": "note", "groups": [
                {"title": "초기 처방·검사", "items": [
                    view_item("abd-ref-orders", "ER set: Full lab + 05.AGE + 08. Pain control / Main fluid: N/S, Plasma-Lyte 등", ["i-89db9271b34f", "i-c1c68308f8e7"], "검사와 증상 조절을 함께 고려"),
                    view_item("abd-ref-lab", "Full lab: CBC, CRP, E′, bil./OT/PT/ALT/GGT, pancreatic enzyme 포함", ["i-e4595c2448c4"]),
                    view_item("abd-ref-upper", "상복부 통증: Cardiac marker / EKG 포함", ["i-184aeba1bd67"]),
                    view_item("abd-ref-fever", "발열: Procalcitonin 포함", ["i-1edb8093df4b"]),
                    view_item("abd-ref-xray", "서 있기 어려운 경우: X-ray AP 처방", ["i-15284a8890fb"]),
                ]},
                {"title": "보고", "items": [
                    view_item("abd-ref-notify", "Surgical abdomen 의심 시 응급의학과 전공의에게 즉시 보고", ["i-dd44c1460346"]),
                    view_item("abd-ref-confirm", "처방 입력 전 응급의학과 전공의 확인", ["i-f06512502fff"]),
                ]},
                {"title": "증상 조절", "items": [
                    view_item("abd-ref-vomiting", "구토: Macperan", ["i-9d3c23dc7dbf"]),
                    view_item("abd-ref-diarrhea", "설사: Bropium", ["i-cdbbe5c24a89"]),
                    view_item("abd-ref-antipyretic", "발열: Acetphen", ["i-34350a9e270a"]),
                    view_item("abd-ref-heartburn", "속쓰림: Nexium", ["i-e02c1f387b36"]),
                    view_item("abd-ref-pain", "통증: Tridol → Acetphen–Kerasyn 순으로 고려", ["i-a3b5fe662812", "i-80802f501f80"], "CT 촬영이 확실한 경우 Kerasyn을 처음부터 고려"),
                ]},
                {"title": "차팅", "items": [
                    view_item("abd-ref-charting", "상병명: Gastrointestinal disease", ["i-d05fceff2212"]),
                ]},
            ]},
        ]
    },
    "flank-pain": {
        "sections": [
            {"id": "flank-view-reference", "title": "참고사항", "kind": "note", "groups": [
                {"title": "처방·검사", "items": [
                    view_item("flank-ref-order", "ER set: 요로결석", ["i-9c83c71a6e33"]),
                    view_item("flank-ref-old-age", "고령 환자: EKG / D-dimer 추가", ["i-eb78ffa7f6c4"], "Renal infarction 가능성 고려"),
                    view_item("flank-ref-ct", "CT: RUA 결과 확인 후 시행", ["i-e4ebc9e04362"], "원문 인계 원칙"),
                ]},
                {"title": "증상 조절", "items": [
                    view_item("flank-ref-control", "Pain: Kerasyn, 심한 경우 Morphine / Nausea: Macperan", ["i-899326191deb"]),
                    view_item("flank-ref-macperan", "Parkinsonism 환자: Macperan 투여 금지", ["i-956f2c0d1e98"]),
                ]},
            ]},
        ]
    },
    "rash": {
        "sections": [
            {"id": "rash-view-reference", "title": "참고사항", "kind": "note", "groups": [
                {"title": "처방·보고", "items": [
                    view_item("rash-ref-order", "ER set: Allergy & angioedema routine", ["i-0e0ec0f4baeb"]),
                    view_item("rash-ref-peniramine", "IM Peniramine 후 귀가 계획인 경우가 많음", ["i-3dc12c53eebc"]),
                    view_item("rash-ref-angioedema", "Angioedema 동반: IV fluid treatment / ED notify", ["i-6fe69f063abd"]),
                    view_item("rash-ref-consult", "복용 중인 약물에도 호전이 없으면 DM consult", ["i-3b9babba9fdf"]),
                ]},
                {"title": "환자 설명", "items": [
                    view_item("rash-ref-explain", "초진 후 가려움증 완화 주사 계획 설명 → ED 설명 후 귀가 형태로 진행", ["i-92ef6181190b", "i-1fa2d9cbf8e4"]),
                ]},
            ]},
        ]
    },
    "back-pain": {
        "sections": [
            {"id": "back-view-history", "title": "Hx", "kind": "history", "groups": [
                {"title": "Present illness", "items": [
                    view_item("back-hx-invasive", "시술 / 침 등 침습적 치료 Hx", ["i-4adbb353ba50"]),
                ]},
            ]},
            {"id": "back-view-exam", "title": "PEx", "kind": "exam", "groups": [
                {"title": "Neurologic", "items": [
                    view_item("back-pe-neuro", "Neurologic exam", ["i-4adbb353ba50"], "충실히 시행"),
                ]},
            ]},
            {"id": "back-view-reference", "title": "참고사항", "kind": "note", "groups": [
                {"title": "환자 설명", "items": [
                    view_item("back-ref-xray", "XR은 골절 감별 목적이며 디스크·협착증·근육통 감별에는 제한이 있음을 초진 시 설명", ["i-887efc4db26b"]),
                    view_item("back-ref-pain", "Pain control 반응이 더디거나 효과가 거의 없을 수 있음을 미리 설명", ["i-115754ffda99"]),
                ]},
            ]},
        ]
    },
    "trauma": {
        "sections": [
            {"id": "trauma-view-history", "title": "Hx", "kind": "history", "groups": [
                {"title": "Present illness", "items": [
                    view_item("trauma-hx-event", "Injury time / Mechanism / Object / Impact force", ["i-688a6f65c1d7", "i-de73026cd548", "i-e1195a72d9d0", "i-9ebb530af606"]),
                    view_item("trauma-hx-loc", "LOC", ["i-a0f0117152c7"]),
                    view_item("trauma-hx-pain", "Abdominal pain / Flank pain / Chest wall pain", ["i-386ee59bf53f", "i-b2bb84357bb1"]),
                    view_item("trauma-hx-control", "Pain control 필요 여부", ["i-be27568ef195"]),
                    view_item("trauma-hx-tetanus", "Tetanus vaccination Hx", ["i-d721e9eae930", "i-0cc7a621fc77"], "최근 5년 이내 접종 여부 확인"),
                ]},
                {"title": "3세 미만 열상", "items": [
                    view_item("trauma-hx-toddler", "NPO time / Body weight", ["i-b84e19f8e78e"], "Line 확보 및 sedative drug 사용 대비; NPO 3시간 확인"),
                ]},
                {"title": "교통사고", "items": [
                    view_item("trauma-hx-ta", "Mechanism / Speed / Seat / Protective gear / LOC / Airbag deployment", ["i-de147cc79d31"]),
                ]},
                {"title": "상해", "items": [
                    view_item("trauma-hx-assault", "Mechanism·object / Injury site / 횟수·정도", ["i-fcd19e2e6a55"]),
                ]},
            ]},
            {"id": "trauma-view-exam", "title": "PEx", "kind": "exam", "groups": [
                {"title": "Musculoskeletal", "items": [
                    view_item("trauma-pe-msk", "Tenderness / LOM / Deformity / Swelling / External wound", ["i-f87ca1e6cd9b", "i-800b30ed4c7d"]),
                    view_item("trauma-pe-neurovascular", "Motor / Sensory change", ["i-f87ca1e6cd9b", "i-440ea8d2c491", "i-deb36614d74a", "i-03c04767e1cf"]),
                    view_item("trauma-pe-axis", "Pelvis / C-spine tenderness", ["i-108544b6342b"]),
                ]},
                {"title": "Wound", "items": [
                    view_item("trauma-pe-expose", "상처를 완전히 노출하여 직접 확인", ["i-04d6f8b0a8a2"]),
                    view_item("trauma-pe-foreign", "Foreign body", ["i-2d07e2abd35d"]),
                    view_item("trauma-pe-site", "Site / Size", ["i-3066cfdb3509", "i-226da3ed64be"], "Lip laceration은 뒤집어 oral cavity 병변 확인"),
                    view_item("trauma-pe-bleeding", "Active bleeding", ["i-fce3d24d05a6", "i-a169f4388074"]),
                    view_item("trauma-pe-depth", "Depth: superficial / deep / penetrating", ["i-996a841fe07e", "i-226da3ed64be"]),
                    view_item("trauma-pe-margin", "Margin: regular / irregular", ["i-45dcc449d3cd", "i-226da3ed64be"], "예: chin 2 cm superficial linear irregular-margin laceration"),
                    view_item("trauma-pe-structure", "Exposed structure: none / dermis / subcutaneous tissue / tendon / ligament / nerve", ["i-ade2395cb1b7"]),
                    view_item("trauma-pe-face", "Facial tenderness", ["i-33c45fd3619a"]),
                ]},
                {"title": "교통사고", "items": [
                    view_item("trauma-pe-ta", "Head / Thorax / Abdomen / Lower back / Pelvis / Extremities", ["i-92155cfad7fe"], "통증 부위 중심으로 보되 전 부위 확인"),
                ]},
            ]},
            {"id": "trauma-view-reference", "title": "참고사항", "kind": "note", "groups": [
                {"title": "초기 처치·오더", "items": [
                    view_item("trauma-ref-set", "ER set: 정형외과 Routine / 성형외과 Routine / 신경외과 Routine / 07Suture", ["i-cc9fb9ec6dff"]),
                    view_item("trauma-ref-xray", "관절 XR은 여러 view를 모두 포함; 소아는 비교를 위해 양측 촬영", ["i-f374b9394b7f", "i-ce1c89e77931"]),
                    view_item("trauma-ref-confirm", "처방 전 ED R. 확인", ["i-423e0fce3748"]),
                    view_item("trauma-ref-wet", "Open wound 초진: Gauze + 생리식염수 + 픽스몰 준비 및 wet dressing", ["i-189594487b6f", "i-21694bf54bf1", "i-203a4da1266c"]),
                ]},
                {"title": "열상", "items": [
                    view_item("trauma-ref-image", "부위에 맞는 영상 오더; comment에 정확한 부위 입력", ["i-4d81c93f9549"], "예: 4th finger"),
                    view_item("trauma-ref-suture", "07Suture: bite wound는 Tiramox, 그 외 cefazoline / TD / Hyper TET", ["i-883574d75347"]),
                    view_item("trauma-ref-manage", "Simple laceration은 주로 ED R. suture; deep laceration 또는 fracture 동반 wound는 OS/PS 등에서 처치", ["i-a47c1d8faf33"]),
                ]},
                {"title": "교통사고·상해", "items": [
                    view_item("trauma-ref-ta-xray", "Tenderness 부위의 위·아래 뼈까지 촬영", ["i-e8c9278bf2dc"], "예: ankle pain이면 tibia부터 foot까지"),
                    view_item("trauma-ref-statement", "차팅에 정보 제공자를 ‘○○ 진술 상’으로 기록", ["i-a3ca85a94775", "i-5e267dc38824"], "예: 119 현장구급대원, 환자 본인"),
                    view_item("trauma-ref-certificate", "진단서·상해진단서 발급을 원하면 ED R.에게 알림", ["i-74813088c816"]),
                ]},
                {"title": "차팅 예시", "items": [
                    view_item("trauma-ref-chart-neuro", "Alert mentation / Pupil 0.3/0.3 / EOM OK / Visual disturbance (-) / Nuchal midline tenderness (-), LOM (-)", ["i-5735897496c9", "i-612377d2b84a", "i-aec507acc5c5", "i-09934c95f014", "i-ae266c3ddb7d", "i-0aca2be86e56"]),
                    view_item("trauma-ref-chart-motor", "Motor: upper G5/G5, lower G5/G5 / Sensory change (-) / Gait OK", ["i-218af66eb411", "i-438f9d760f95", "i-276cecfacc29"]),
                    view_item("trauma-ref-chart-wound", "No external wound on chest, abdomen, and back", ["i-233de0814bca"]),
                ]},
            ]},
        ]
    },
    "dizziness": {
        "sections": [
            {"id": "dizziness-view-history", "title": "Hx", "kind": "history", "groups": [
                {"title": "Chief complaint · Present illness", "items": [
                    view_item("dizz-hx-basic", "S/A / V/S", ["i-0ed008b89dee"]),
                    view_item("dizz-hx-cc", "Chief complaint / Onset", ["i-ee4e51907a91"]),
                    view_item("dizz-hx-pi", "Present illness", ["i-295d2b8c0877"]),
                ]},
                {"title": "Past · Social · Drug history", "items": [
                    view_item("dizz-hx-past", "Operation / Admission / HTN / DM / Hepatitis / Pulmonary tuberculosis", ["i-f9672a36bab3", "i-090b46250227"]),
                    view_item("dizz-hx-social", "Smoking / Alcohol / Pack-years / Current smoking", ["i-3789fe7ad282"]),
                    view_item("dizz-hx-medication", "Medication", ["i-18572f0f6fd3"]),
                ]},
                {"title": "Review of systems", "items": [
                    view_item("dizz-hx-ros", "Fever / Chill / Cough / Sputum / Rhinorrhea · Anorexia / Nausea / Vomiting / Constipation / Diarrhea · Headache / Dizziness", ["i-f1940c9b999a"]),
                ]},
                {"title": "Dizziness", "items": [
                    view_item("dizz-hx-pattern", "Pattern: Vertigo / Presyncope / Lightheadedness / Disequilibrium", ["i-6ad27ea2b2e4", "i-2e37d0e92ac5"], "빙빙 도는지, 쓰러질 것 같은지, 기운이 없는지, 보행이 이상한지 확인"),
                    view_item("dizz-hx-trs", "True rotating sensation (TRS)", ["i-cdb419f99f24", "i-6caa8883d154", "i-6a49a5ad9c82"]),
                    view_item("dizz-hx-duration", "Duration / 회복까지 걸리는 시간", ["i-98a27e5fe646", "i-6a49a5ad9c82"]),
                    view_item("dizz-hx-ear", "Tinnitus / Otalgia / Ear fullness / Hearing difficulty or loss / URI Hx", ["i-af4103b19fb5", "i-ab8e235e7ce3", "i-6caa8883d154"]),
                    view_item("dizz-hx-neuro", "동반된 neurologic deficit symptom", ["i-4796b70d2f28"], "반드시 확인하고 차팅"),
                ]},
            ]},
            {"id": "dizziness-view-exam", "title": "PEx", "kind": "exam", "groups": [
                {"title": "Nystagmus · Positional test", "items": [
                    view_item("dizz-pe-nystagmus", "Spontaneous / Gaze-evoked / Head-turn induced nystagmus", ["i-6a49a5ad9c82", "i-547582678bb0"]),
                    view_item("dizz-pe-algorithm", "Spontaneous·gaze-evoked nystagmus 확인 → HINTS / ED R. notify / Dix-Hallpike / Head-roll test", ["i-a26c38ea1eef", "i-f1f1b078d1f6"], "원문의 양성·음성 결과별 시행 순서 확인"),
                ]},
                {"title": "Gait · Cerebellar", "items": [
                    view_item("dizz-pe-gait", "Falling tendency / Tandem gait / Romberg test", ["i-69a715c63b8a", "i-83754277e4c2"]),
                    view_item("dizz-pe-cerebellar", "Finger-to-finger / Finger-to-nose / Heel-to-shin / Rapid alternating movement / Positional dependency", ["i-b06a29883b36"]),
                ]},
            ]},
            {"id": "dizziness-view-reference", "title": "참고사항", "kind": "note", "groups": [
                {"title": "처방·검사", "items": [
                    view_item("dizz-ref-order", "ER set: 신경과 Dizziness / Cardiac panel / EKG", ["i-627951e268db", "i-53a627e34512"]),
                    view_item("dizz-ref-mri", "비급여 MR 예정임을 초진 시 고지; 거절 시 acute stroke를 배제할 수 없음을 설명", ["i-b59d9bb13f2d"]),
                ]},
                {"title": "증상 조절", "items": [
                    view_item("dizz-ref-control", "IV Macperan / IV Zofran", ["i-8be062564911"]),
                ]},
                {"title": "원문 참고", "items": [
                    view_item("dizz-ref-nystagmus", "안진 확인법은 전공의에게 문의", ["i-11e18a0af92f"]),
                    view_item("dizz-ref-cerebellar", "Cerebellar function test는 생략 가능하다는 원문 메모", ["i-eba126edda0c"]),
                ]},
                {"title": "차팅 예시 · Ménière/BPPV", "items": [
                    view_item("dizz-ref-example1-hx", "이전 Ménière로 우측 tinnitus가 있었고, 금일 이전과 비슷한 TRS·dizziness가 우측으로 고개를 돌릴 때 발생", ["i-cb9a91e85adf", "i-bebd5c3b1a65", "i-d7a740d21171", "i-d3e1f226fbb1"]),
                    view_item("dizz-ref-example1-pe", "Spontaneous nystagmus (+) / Right torsional / Catch-up saccade (+) / No other lateralizing or localizing sign", ["i-206f7882d71f", "i-ef762d070f24", "i-87070a99c108", "i-566d5c453205"]),
                ]},
                {"title": "차팅 예시 · Dizziness", "items": [
                    view_item("dizz-ref-example2-pi", "HTN·Moyamoya disease로 추적 중. TRS 양상의 지속되는 dizziness가 자세 변화에 따라 악화되고 vomiting 수차례 동반; 뚜렷한 neurologic abnormality 없음", ["i-64463269cabf", "i-83e315881da7", "i-870ebd4a3f0c", "i-6db3db44bec6"]),
                    view_item("dizz-ref-example2-hx", "Onset: 내원 2일 전 / TRS (+), Vertigo (+) / Duration: 지속", ["i-067c395ba43f", "i-454f9219d6e6", "i-e90b2a672f24"]),
                    view_item("dizz-ref-example2-pe", "Spontaneous nystagmus (-) / Positional dependency (+), head turn 시 / Roll test: Right > Left, ageotropic nystagmus (+)", ["i-094174c96cb6", "i-04abbfca2684"]),
                    view_item("dizz-ref-example2-ros", "Headache (-) / Nausea·Vomiting (+/+)", ["i-1334c34cfd7c"]),
                ]},
            ]},
        ]
    }
}

raw_item_ids = {item["id"] for section in groups.values() for item in section["items"]}
for layout in curated_layouts.values():
    for section in layout["sections"]:
        for group in section["groups"]:
            for item in group["items"]:
                missing = set(item["sourceItemIds"]) - raw_item_ids
                if missing:
                    raise ValueError(f"Curated item has unknown source items: {item['id']} {sorted(missing)}")

# All remaining DOCX blocks must be formatting / headings, never substantive omissions.
structures = {
 "handover": "2,8,10,17,25,31,36,41,43,49,55,61,69,70,75,79,80,85,90,91,95,101,104",
 "np-docx": "30-32",
 "templates": "1,5,9,12,17,21,26,34,37,39,56,60,63,82,84,110,121,146,152,159,162,164,167,169",
 "all": "13,25,41,48,69,83,104,120,130-131,135,187,202,209,218,223,226,230,233,238,305,307",
}
for sid, specs in structures.items():
    for bid in pick(sid, specs):
        if assignments[bid]:
            raise ValueError(f"Heading already used: {bid}")
        assignments[bid].append({"type": "structure", "reason": "제목·구획·서식 필드. 원문 보존."})
unassigned = [bid for bid in blocks if not assignments[bid]]
if unassigned:
    raise ValueError("Unassigned source text: " + repr(unassigned))

category_names = ["입원관리", "소화기", "순환기", "호흡기", "신장/비뇨기", "전신증상", "근골격/피부", "신경정신", "산부", "소아", "눈/이비인후", "상담"]
categories = [{"id": f"{i:02}", "name": name, "order": i if 1 <= i <= 10 else (11 if i == 0 else 12), "secondary": i in (0, 11)} for i, name in enumerate(category_names)]
catalog = {
 "00": [("acute-condition","급성상태",[]),("abnormal-lab","수치이상",[]),("prescription","처방체액",[]),("device","기구문제",[]),("ward-event","병동사건",[])],
 "01": [("abdominal-pain","복통",["복부 통증","급성복통","abdominal pain","abd pain","AP"]),("dyspepsia","소화불량 / 만성 복통",["dyspepsia"]),("hematemesis","토혈",["hematemesis"]),("bloody-stool","혈변",["hematochezia","melena"]),("vomiting","오심 / 구토",["구역","nausea","vomiting","N/V","emesis"]),("constipation","변비",["constipation"]),("diarrhea","설사",["diarrhea"]),("jaundice","황달",["jaundice"])],
 "02": [("chest-pain","흉통",["가슴통증","가슴 통증","chest pain","CP"]),("syncope","실신",["syncope","LOC","blackout"]),("palpitation","두근거림",["palpitation","palpitations"]),("hypertension","고혈압",["hypertension","HTN"]),("dyslipidemia","이상지질혈증",["dyslipidemia"])],
 "03": [("cough","기침",["cough"]),("rhinorrhea","콧물 / 코막힘",["rhinorrhea","nasal obstruction"]),("hemoptysis","객혈",["hemoptysis"]),("dyspnea","호흡곤란",["숨참","숨차","dyspnea","dyspnoea","SOB","shortness of breath"])],
 "04": [("polyuria","다뇨",["polyuria"]),("oliguria","핍뇨",["oliguria"]),("hematuria","혈뇨",["hematuria"]),("urinary-symptoms","배뇨이상 / 빈뇨",["배뇨장애","빈뇨","배뇨통","dysuria","frequency","urinary symptoms"]),("incontinence","요실금",["incontinence"]),("flank-pain","옆구리 통증",["flank pain","renal colic"])],
 "05": [("fever","발열",["열","fever","pyrexia"]),("bruising","멍",["bruise"]),("fatigue","피로",["fatigue"]),("weight-loss","체중감소",["weight loss"]),("weight-gain","체중증가",["weight gain"]),("poisoning","중독 / 과량복용",["약물 과다복용","poisoning","overdose","intoxication"])],
 "06": [("joint-pain","관절 통증 / 붓기",["arthralgia","joint pain"]),("neck-pain","목 통증",["neck pain"]),("back-pain","허리 통증",["요통","등 통증","back pain","LBP"]),("rash","피부 발진",["rash","skin rash"]),("trauma","상처 / 외상",["열상","교통사고","상해","trauma","laceration","lac","TA","wound"]),("head-trauma","두부외상",["머리 외상","head trauma","head injury"])],
 "07": [("mood","기분변화",["우울","mood","depression"]),("anxiety","불안",["anxiety","panic"]),("sleep","수면장애",["불면","insomnia","sleep"]),("memory","기억력 저하",["memory loss"]),("dizziness","어지럼",["어지럼증","어지러움","dizziness","dizzy","vertigo","TRS"]),("headache","두통",["headache","HA"]),("peds-seizure","경련 (소아)",["소아 경련","열성경련","pediatric seizure","febrile seizure"]),("seizure","경련 (성인)",["성인 경련","seizure","convulsion","GTC"]),("weakness","근력 / 감각이상",["weakness","sensory change"]),("mental-change","의식장애",["의식저하","mental change","AMS","altered mental status"]),("movement","떨림 / 운동이상",["tremor"]),("stroke","뇌졸중 의심",["stroke","CVA"])],
 "08": [("breast-pain","유방통",["mastalgia"]),("breast-mass","유방덩이",["breast mass"]),("vaginal-discharge","질분비물",["vaginal discharge"]),("vaginal-bleeding","질출혈",["vaginal bleeding"]),("menstrual","월경이상 (무월경)",["amenorrhea"]),("dysmenorrhea","월경통 (월경과다)",["dysmenorrhea","menorrhagia"]),("pregnancy","산전 진찰",["산모","임신","pregnancy","preterm labor","IUP"]),("pelvic-pain","골반통",["pelvic pain"])],
 "09": [("growth","성장 지연",["growth delay"]),("development","발달 지연",["developmental delay"]),("vaccination","예방접종",["vaccination"]),("peds-common","소아 공통",["소아","pediatrics","PD"])],
 "10": [("eye","눈 통증 / 시력저하",["안통","시력저하","eye pain","ocular pain","blurred vision"]),("throat","인후통 / 연하곤란",["sore throat","dysphagia"]),("ear","귀 통증 / 청력저하",["귀먹먹함","otalgia","hearing loss","tinnitus"]),("epistaxis","코피",["비출혈","epistaxis"])],
 "11": [("alcohol-counsel","음주 상담",["alcohol"]),("smoking-counsel","흡연 상담",["smoking"]),("substance","물질 오남용",["substance abuse"]),("bad-news","나쁜 소식 전하기",[]),("domestic-violence","가정폭력",[]),("sexual-violence","성폭력",[]),("suicide","자살 / 자해",["자살사고","자해충동","suicide","suicidal","self harm"])],
}
# The supplied CC catalog is a classification reference. Keep source-backed
# specialty templates as one entry and pediatric material in its own category.
psychiatric_ids = {"mood", "anxiety", "sleep", "suicide", "poisoning"}
obgyn_ids = {"vaginal-discharge", "vaginal-bleeding", "menstrual", "dysmenorrhea", "pelvic-pain"}
pediatric_ids = {"vomiting", "diarrhea", "cough", "fever", "peds-seizure", "peds-common", "peds-abdominal-pain"}
records_by_id = {record[0]: record for records in catalog.values() for record in records}

def specialty_aliases(ids, extras):
    aliases = list(extras)
    for iid in sorted(ids):
        _, name, terms = records_by_id[iid]
        aliases.extend([name, *terms])
    return list(dict.fromkeys(aliases))

for cid, records in catalog.items():
    catalog[cid] = [record for record in records if record[0] not in psychiatric_ids | obgyn_ids | pediatric_ids]
catalog["07"].extend([
    ("neurology-interview", "신경과 문진", ["신경과", "neurology", "NR", "신경과 공통"]),
    ("psychiatry-interview", "정신과 문진", specialty_aliases(psychiatric_ids, ["정신과", "psychiatry", "NP", "정신과 공통"])),
])
catalog["08"].insert(0, ("obgyn-interview", "산부인과 문진", specialty_aliases(obgyn_ids, ["산부인과", "OBGY", "OBGYN", "gynecology", "산부인과 공통"])))
catalog["09"] = [
    ("peds-common", "소아과 문진", ["소아", "소아 공통", "소아과", "pediatrics", "pediatric", "PD"]),
    records_by_id["fever"], records_by_id["vomiting"], records_by_id["diarrhea"], records_by_id["cough"],
    ("peds-abdominal-pain", "복통", ["소아 복통", "소아 복부 통증", "pediatric abdominal pain", "abdominal pain", "abd pain", "AP"]),
    ("peds-seizure", "경련", records_by_id["peds-seizure"][2] + ["경련", "seizure", "convulsion"]),
    *catalog["09"],
]

bindings = {
 "abdominal-pain": (["routine-history","routine-exam"], ["abd-history","abd-exam","abd-note"]),
 "peds-abdominal-pain": (["peds-history","peds-exam"], ["peds-abd-history","peds-abd-mixed"]),
 "constipation": (["routine-history"], ["constipation-history"]),
 "vomiting": (["peds-history","peds-exam"], ["peds-vomit"]),
 "diarrhea": (["peds-history","peds-exam"], ["peds-diarrhea"]),
 "chest-pain": ([], ["chest-history"]),
 "syncope": (["nr-history"], ["syncope-history","syncope-mixed","syncope-note"]),
 "cough": (["peds-history","peds-exam"], ["peds-cough"]),
 "urinary-symptoms": ([], ["urinary-history"]),
 "flank-pain": ([], ["flank-note"]),
 "fever": (["peds-history","peds-exam"], ["peds-fever","peds-fever-exam","peds-fever-example"]),
 "psychiatry-interview": (["np-history"], ["np-note","np-response","np-example","np-ex1","np-template","np-ex2","np-ex3"]),
 "neurology-interview": (["nr-history"], []),
 "obgyn-interview": (["ob-history"], ["ob-note"]),
 "joint-pain": ([], ["msk-exam"]),
 "back-pain": ([], ["back-mixed","back-note"]),
 "rash": ([], ["rash-note"]),
 "trauma": (["msk-exam"], ["trauma-history","trauma-exam","trauma-note","trauma-example"]),
 "head-trauma": ([], ["headtrauma-history","headtrauma-exam"]),
 "dizziness": (["nr-history"], ["dizziness-history","dizziness-exam","dizziness-note","dizziness-example"]),
 "headache": (["nr-history"], ["headache-history","headache-exam"]),
 "peds-seizure": (["peds-history","peds-exam"], ["peds-seizure-history","peds-seizure-example"]),
 "seizure": (["nr-history"], ["seizure-history"]),
 "mental-change": (["nr-history"], ["mental-exam"]),
 "stroke": (["nr-history"], ["stroke-history","stroke-exam","stroke-note"]),
 "pregnancy": (["ob-history"], ["pregnancy-history","ob-note"]),
 "peds-common": (["peds-history","peds-exam"], []),
 "eye": ([], ["eye-history","eye-exam","eye-note"]),
 "ear": ([], ["ear-history","ear-example"]),
 "epistaxis": ([], ["epistaxis-mixed","epistaxis-note"]),
}
for name in ["hematuria","incontinence"]:
    bindings[name] = ([], ["urinary-history"])
complaints = []
specialty_ids = {"neurology-interview", "psychiatry-interview", "obgyn-interview", "peds-common"}
for cid, records in catalog.items():
    records.sort(key=lambda record: record[0] not in specialty_ids)
    for order, (iid, name, aliases) in enumerate(records):
        shared, section_ids = bindings.get(iid, ([], []))
        scope = "general"
        if iid in pediatric_ids:
            scope = "pediatric"
        if iid == "psychiatry-interview":
            scope = "psychiatric"
        item = {"id": iid, "name": name, "categoryId": cid, "aliases": aliases,
                "order": order, "scope": scope, "status": "available" if shared or section_ids else "missing",
                "sharedSectionIds": shared, "sectionIds": section_ids}
        if iid in ("rash","flank-pain"):
            item["status"] = "notesOnly"
        if iid in curated_layouts:
            item["layout"] = curated_layouts[iid]
        complaints.append(item)

data = {"schemaVersion": 1, "contentVersion": "2026-09-26-beta.5", "categories": categories,
        "sections": list(groups.values()), "complaints": complaints,
        "referenceSections": ["routine-history","routine-exam","handover-general"]}
(DATA / "chief-complaints.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
provenance = {"schemaVersion": 1, "sources": archive["sources"],
              "assignments": dict(assignments), "pdfAdditions": pdf_additions,
              "reviewIssues": [
 {"id":"cerebellar-exam", "sectionIds":["dizziness-exam","dizziness-note"], "text":"소뇌기능검사: 한 문서는 검사 항목을 제시하고 다른 문서는 생략 가능 메모를 포함. 양쪽 원문 보존, 우선순위 미결정."},
 {"id":"stroke-timing", "sectionIds":["stroke-note"], "text":"원문의 3시간 기준 인계 메모를 그대로 보존. 현재 임상 기준으로 검증한 내용이 아님."},
 {"id":"abbreviations", "sectionIds":["abd-history","nr-history","peds-history"], "text":"원문 약어는 보존. 복통 화면에서는 사용자 확인을 거친 FCCSR, ANVCD, FUND HIS를 풀어 표시함."},
 {"id":"seizure-examples", "sectionIds":["peds-seizure-example","np-example"], "text":"예시의 양성·음성 소견 및 수치는 실제 환자 정보나 질문의 기본 답으로 취급하지 않음."},
 {"id":"medication-notes", "sectionIds":["abd-note","flank-note","rash-note","trauma-note","dizziness-note"], "text":"약제·검사·병원 내부 오더 및 처치 내용은 인계 메모로 보존. 독립 문진 질문으로 바꾸지 않음."}
]}
(DATA / "content-provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

source_count = sum(len(s["blocks"]) for s in archive["sources"])
item_count = sum(len(s["items"]) for s in groups.values())
linked_blocks = sum(any(a["type"]=="item" for a in assignments[b]) for b in blocks)
report = {"sourceFiles": len(archive["sources"]), "sourceBlocks": source_count,
 "mappedSourceBlocks": len(assignments), "unassignedSourceBlocks": [], "sections": len(groups),
 "items": item_count, "itemSourceBlocks": linked_blocks,
 "exactDuplicateOccurrencesMerged": linked_blocks - (item_count - len(pdf_additions)),
 "complaints": len(complaints), "complaintsWithSourceMaterial": sum(c["status"]!="missing" for c in complaints),
 "pediatricEntries": [c["name"] for c in complaints if c["scope"]=="pediatric"],
 "specialtyEntries": [c["name"] for c in complaints if c["id"] in ("neurology-interview", "psychiatry-interview", "obgyn-interview", "peds-common")],
 "missingComplaints": [c["name"] for c in complaints if c["status"]=="missing"],
 "method": "의미를 추정한 병합 없음. 동일 구획의 공백·앞쪽 bullet 차이만 있는 원문만 통합. 복합 항목과 조건 보존."}
(DOCS / "content-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

lines = ["# ER 초진 자료 정리본", "", "원문 문진·진찰·인계 메모·차팅 예시를 구분한 베타 자료입니다. 의학 내용을 추가하거나 임상 지침으로 검증하지 않았습니다.", "",
 f"- 원본 {len(archive['sources'])}개 / 텍스트 블록 {source_count}개 / 미분류 0개", f"- 정리된 항목 {item_count}개 / 분류 항목 {len(complaints)}개 중 자료 보유 {report['complaintsWithSourceMaterial']}개", "",
 "- 분과 공통 양식은 신경과·정신과·산부인과·소아과 문진으로 연결합니다. 소아 증상 자료는 모두 09 소아에 별도로 배치합니다.",
 "- 항목 수는 원문 묶음 기준입니다. 한 문장에 여러 질문이 들어 있어도 원문 그대로 보존하며, 인계 메모와 차팅 예시를 질문으로 바꾸지 않습니다.", "",
 "## 공통 자료", ""]
rendered = set()
def render_section(sid):
    if sid in rendered:
        return
    rendered.add(sid)
    s = groups[sid]
    lines.extend([f"### {s['title']} · {KINDS[s['kind']]}", ""])
    for item in s["items"]:
        cond = f"**{item['condition']}** — " if item.get("condition") else ""
        refs = [bid for bid, links in assignments.items() if any(a.get("itemId")==item["id"] for a in links)]
        lines.append(f"- {cond}{item['text']}  ")
        lines.append(f"  출처: {', '.join(refs)}")
    lines.append("")
for sid in data["referenceSections"]:
    render_section(sid)
for cat in sorted(categories, key=lambda x:x["order"]):
    lines.extend([f"## {cat['id']} {cat['name']}", ""])
    for complaint in [c for c in complaints if c["categoryId"]==cat["id"]]:
        lines.extend([f"### {complaint['name']}", ""])
        if complaint["status"]=="missing":
            lines.extend(["독립 항목 자료 없음. 문진 내용 미생성.", ""])
        if complaint["scope"]=="pediatric":
            lines.extend(["범위: 소아 원문 자료.", ""])
        if complaint["scope"]=="psychiatric":
            lines.extend(["범위: 정신과 원문 공통 자료.", ""])
        if complaint["sharedSectionIds"]:
            lines.extend(["공통 자료: " + ", ".join(groups[s]["title"] for s in complaint["sharedSectionIds"]), ""])
        primary_ids = [sid for sid in complaint["sectionIds"] + complaint["sharedSectionIds"] if groups[sid]["kind"] in ("history", "exam")]
        reference_ids = [sid for sid in complaint["sectionIds"] + complaint["sharedSectionIds"] if groups[sid]["kind"] in ("note", "example")]
        for sid in dict.fromkeys(primary_ids + reference_ids):
            if sid in rendered:
                lines.extend([f"공통 참조: {groups[sid]['title']}", ""])
            else:
                render_section(sid)
lines.extend(["## 확인이 필요한 원문", ""])
for issue in provenance["reviewIssues"]:
    lines.extend([f"- {issue['text']}"])
lines.extend(["", "## 출처와 보존 방식", "",
 "`data/content-provenance.json`에는 원문 텍스트 전체, 파일 SHA-256, 문단 위치, 정리된 항목과의 대응 관계를 보존합니다. 서식용 제목도 별도 분류합니다.", "",
 "NP PDF는 DOCX와 동등한 본문을 가진 대체 형식입니다. PDF에만 있는 요약과 차팅 문구 3개를 추가 보존했습니다. DOCX의 삽입 이미지는 1×1 빈 이미지로 확인했습니다.", ""])
(DOCS / "자료 정리본.md").write_text("\n".join(lines), encoding="utf-8")
print(json.dumps(report, ensure_ascii=True))
