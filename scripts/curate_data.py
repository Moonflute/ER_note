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
add("nr-history", "증상 공통 문진", "history", "templates", "83,85-86,88-92")
add("nr-history", "증상 공통 문진", "history", "all", "46,49-50,52-54,56")
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
def view_item(iid, text, source_item_ids, note=None, abbreviated_text=None):
    item = {"id": iid, "text": text, "sourceItemIds": source_item_ids}
    if note:
        item["note"] = note
    if abbreviated_text:
        item["abbreviatedText"] = abbreviated_text
    return item

def neuro_history_groups(prefix):
    return [
        {"title": "Basic", "items": [
            view_item(f"{prefix}-hx-basic", "V/S", ["i-0ed008b89dee"]),
            view_item(f"{prefix}-hx-cc", "CC", ["i-ee4e51907a91"]),
            view_item(f"{prefix}-hx-pi", "PI", ["i-295d2b8c0877"]),
            view_item(f"{prefix}-hx-medical", "Medical Hx (U/D Drug Adm Op)", ["i-f9672a36bab3", "i-090b46250227", "i-18572f0f6fd3"]),
            view_item(f"{prefix}-hx-social", "Social Hx (Alcohol Smoking)", ["i-3789fe7ad282"]),
        ]},
        {"title": "Review of systems", "items": [
            view_item(f"{prefix}-hx-ros", "Fever / Chill / Cough / Sputum / Rhinorrhea · Anorexia / Nausea / Vomiting / Constipation / Diarrhea · Headache / Dizziness", ["i-f1940c9b999a"]),
        ]},
    ]

def peds_history_groups(prefix, fccsr_sources=(), daily_sources=()):
    return [
        {"title": "General · Birth history", "items": [
            view_item(f"{prefix}-hx-vital", "V/S", ["i-88fe282cb4fe"]),
            view_item(f"{prefix}-hx-neonate", "Neonate: Current weight / Gestational week / Vaginal delivery or C-section / Birth asphyxia", ["i-88fe282cb4fe", "i-52e3c96499b8"]),
            view_item(f"{prefix}-hx-mother", "Maternal problem", ["i-0ed4387ab7a9"]),
        ]},
        {"title": "Review of systems", "items": [
            view_item(f"{prefix}-hx-fccsr", "Fever / Chill / Cough / Sputum / Rhinorrhea / Nasal obstruction", ["i-52e3c96499b8", *fccsr_sources]),
            view_item(f"{prefix}-hx-anvcd", "Anorexia / Nausea / Vomiting / Constipation / Diarrhea / Headache / Irritability", ["i-0ed4387ab7a9"]),
            view_item(f"{prefix}-hx-daily", "Feeding / Activity / Urination / Sleeping: Fair or Poor", ["i-915a1e9fb598", *daily_sources]),
            view_item(f"{prefix}-hx-appearance", "Appearance: Well or Ill / Irritable / Lethargic", ["i-2565eaefaa14"]),
        ]},
    ]

def peds_exam_groups(prefix, throat_sources=(), neck_sources=(), lung_sources=(), bowel_sources=()):
    return [
        {"title": "HEENT · Neck", "items": [
            view_item(f"{prefix}-pe-throat", "Throat injection / Tonsillar enlargement", ["i-f563840a36c8", "i-711f3514742f", *throat_sources]),
            view_item(f"{prefix}-pe-tongue", "Dehydrated tongue", ["i-b65cf64b5492"]),
            view_item(f"{prefix}-pe-neck", "Neck stiffness / Nuchal rigidity", ["i-795bc09a858d", *neck_sources]),
        ]},
        {"title": "Chest", "items": [
            view_item(f"{prefix}-pe-lung", "Lung sound: Clear / Coarse / Wheezing / Stridor / Crackle", ["i-afddfcfacdfb", *lung_sources]),
            view_item(f"{prefix}-pe-heart", "Heart murmur", ["i-adc3e02089cf"]),
        ]},
        {"title": "Abdomen", "items": [
            view_item(f"{prefix}-pe-abd", "Bowel sound: Normoactive / Increased / Decreased · Palpation: Soft / Hard · Flat / Distended", ["i-aed40d3bdf5b", *bowel_sources]),
        ]},
    ]

curated_layouts = {
    "abdominal-pain": {
        "sections": [
            {"id": "abd-view-history", "title": "Hx", "kind": "history", "groups": [
                {"title": "History", "items": [
                    view_item("abd-hx-background", "Medical Hx (U/D Drug Adm Op)", ["i-a0dbc0b8eaec"]),
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
                *neuro_history_groups("dizz"),
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
    },
    "chest-pain": {
        "sections": [
            {"id": "chest-view-history", "title": "Hx", "kind": "history", "groups": [
                {"title": "Present illness", "items": [
                    view_item("chest-hx-onset", "Onset", ["i-cc1f243d2ac8"]),
                    view_item("chest-hx-character", "Character", ["i-8c8fcfe105b3"]),
                    view_item("chest-hx-duration", "Duration", ["i-490fd8e4dda3"]),
                    view_item("chest-hx-radiation", "Radiation", ["i-c13032d51230"]),
                    view_item("chest-hx-factor", "Aggravating / Alleviating factors", ["i-bf595e446444"]),
                    view_item("chest-hx-associated", "Associated symptoms", ["i-ae5de500815f"]),
                ]},
                {"title": "History", "items": [
                    view_item("chest-hx-past", "Medical Hx (U/D Drug Adm Op)", ["i-bdecab5aa049"]),
                ]},
            ]},
        ]
    },
    "hematuria": {
        "sections": [
            {"id": "hematuria-view-history", "title": "Hx", "kind": "history", "groups": [
                {"title": "Urinary symptoms", "items": [
                    view_item("hematuria-hx-urinary", "Residual sensation / Frequency / Urgency / Hesitancy / Dysuria / Hematuria / Terminal dribbling / Nocturia / Incontinence / Narrow urine stream", ["i-bda12e23e084"], abbreviated_text="FUND HIS / Hematuria / Terminal dribbling / Incontinence / Narrow urine stream"),
                ]},
            ]},
        ]
    },
    "urinary-symptoms": {
        "sections": [
            {"id": "urinary-view-history", "title": "Hx", "kind": "history", "groups": [
                {"title": "Urinary symptoms", "items": [
                    view_item("urinary-hx-symptoms", "Residual sensation / Frequency / Urgency / Hesitancy / Dysuria / Hematuria / Terminal dribbling / Nocturia / Incontinence / Narrow urine stream", ["i-bda12e23e084"], abbreviated_text="FUND HIS / Hematuria / Terminal dribbling / Incontinence / Narrow urine stream"),
                ]},
            ]},
        ]
    },
    "incontinence": {
        "sections": [
            {"id": "incontinence-view-history", "title": "Hx", "kind": "history", "groups": [
                {"title": "Urinary symptoms", "items": [
                    view_item("incontinence-hx-urinary", "Residual sensation / Frequency / Urgency / Hesitancy / Dysuria / Hematuria / Terminal dribbling / Nocturia / Incontinence / Narrow urine stream", ["i-bda12e23e084"], abbreviated_text="FUND HIS / Hematuria / Terminal dribbling / Incontinence / Narrow urine stream"),
                ]},
            ]},
        ]
    },
    "joint-pain": {
        "sections": [
            {"id": "joint-view-exam", "title": "PEx", "kind": "exam", "groups": [
                {"title": "Musculoskeletal", "items": [
                    view_item("joint-pe-msk", "LOM / M·S change / Tenderness point / External wound / Swelling", ["i-f87ca1e6cd9b"]),
                ]},
            ]},
        ]
    },
    "head-trauma": {
        "sections": [
            {"id": "head-trauma-view-history", "title": "Hx", "kind": "history", "groups": [
                {"title": "Present illness", "items": [
                    view_item("head-trauma-hx", "LOC / Headache / Nausea / Vomiting", ["i-3ef205c69344"]),
                ]},
            ]},
            {"id": "head-trauma-view-exam", "title": "PEx", "kind": "exam", "groups": [
                {"title": "Neurologic", "items": [
                    view_item("head-trauma-pe-pupil", "Pupil reflex", ["i-5d548532fd14"]),
                ]},
            ]},
        ]
    },
    "peds-common": {
        "sections": [
            {"id": "peds-common-view-history", "title": "Hx", "kind": "history", "groups": [
                {"title": "General · Birth history", "items": [
                    view_item("peds-common-hx-vital", "V/S", ["i-88fe282cb4fe"]),
                    view_item("peds-common-hx-neonate", "Neonate: Current weight / Gestational week / Vaginal delivery or C-section / Birth asphyxia", ["i-88fe282cb4fe", "i-52e3c96499b8"]),
                    view_item("peds-common-hx-mother", "Maternal problem", ["i-0ed4387ab7a9"]),
                ]},
                {"title": "Review of systems", "items": [
                    view_item("peds-common-hx-fccsr", "Fever / Chill / Cough / Sputum / Rhinorrhea / Nasal obstruction", ["i-52e3c96499b8"]),
                    view_item("peds-common-hx-anvcd", "Anorexia / Nausea / Vomiting / Constipation / Diarrhea / Headache / Irritability", ["i-0ed4387ab7a9"]),
                    view_item("peds-common-hx-daily", "Feeding / Activity / Urination / Sleeping: Fair or Poor", ["i-915a1e9fb598"]),
                    view_item("peds-common-hx-appearance", "Appearance: Well or Ill / Irritable / Lethargic", ["i-2565eaefaa14"]),
                ]},
            ]},
            {"id": "peds-common-view-exam", "title": "PEx", "kind": "exam", "groups": [
                {"title": "HEENT · Neck", "items": [
                    view_item("peds-common-pe-throat", "Throat injection / Tonsillar enlargement", ["i-f563840a36c8", "i-711f3514742f"]),
                    view_item("peds-common-pe-tongue", "Dehydrated tongue", ["i-b65cf64b5492"]),
                    view_item("peds-common-pe-neck", "Neck stiffness / Nuchal rigidity", ["i-795bc09a858d"]),
                ]},
                {"title": "Chest", "items": [
                    view_item("peds-common-pe-lung", "Lung sound: Clear / Coarse / Wheezing / Stridor / Crackle", ["i-afddfcfacdfb"]),
                    view_item("peds-common-pe-heart", "Heart murmur", ["i-adc3e02089cf"]),
                ]},
                {"title": "Abdomen", "items": [
                    view_item("peds-common-pe-abd", "Bowel sound: Normoactive / Increased / Decreased · Palpation: Soft / Hard · Flat / Distended", ["i-aed40d3bdf5b"]),
                ]},
            ]},
        ]
    },
    "constipation": {
        "sections": [
            {"id": "constipation-view-history", "title": "Hx", "kind": "history", "groups": [
                {"title": "History", "items": [
                    view_item("constipation-hx-past", "Medical Hx (U/D Drug Adm Op)", ["i-a0dbc0b8eaec"]),
                ]},
                {"title": "Review of systems", "items": [
                    view_item("constipation-hx-ros", "Fever / Chill / Cough / Sputum / Rhinorrhea · Anorexia / Nausea / Vomiting / Constipation / Diarrhea", ["i-473758685a66"]),
                    view_item("constipation-hx-npo", "NPO time", ["i-23c56e483dfc"], "수술 가능성이 있는 경우"),
                ]},
                {"title": "Bowel habit", "items": [
                    view_item("constipation-hx-defecation", "Last defecation", ["i-2b7af5302516"]),
                    view_item("constipation-hx-gas", "Last flatus", ["i-017c756636f4"]),
                    view_item("constipation-hx-scope", "Last colonoscopy / Gastroscopy", ["i-96a78e8d87e7"], "고령 환자의 배변 습관 변화 시 malignancy 감별과 work-up 필요성 설명"),
                ]},
            ]},
        ]
    },
    "syncope": {
        "sections": [
            {"id": "syncope-view-history", "title": "Hx", "kind": "history", "groups": [
                *neuro_history_groups("syncope"),
                {"title": "Syncope", "items": [
                    view_item("syncope-hx-loc", "LOC / Blackout / HTN medication", ["i-74e665c4ee32", "i-0395d2464d8f"]),
                    view_item("syncope-hx-prodrome", "Prodrome: 시야가 캄캄함 / Dizziness / Sweating / Nausea / Chest pain / Dyspnea", ["i-cd65d5c1c19d"]),
                    view_item("syncope-hx-change", "실신 당시 증상과 현재 증상 비교 / 호전 여부", ["i-dc2c688b1dbb"]),
                    view_item("syncope-hx-prior", "Previous similar episode", ["i-5662f55888f8"]),
                    view_item("syncope-hx-context", "Meal / Sleep / Stress", ["i-be7d7e3c523b"]),
                ]},
            ]},
            {"id": "syncope-view-exam", "title": "PEx", "kind": "exam", "groups": [
                {"title": "Orthostatic blood pressure", "items": [
                    view_item("syncope-pe-bp", "Supine / Sitting / Standing BP", ["i-0395d2464d8f"]),
                ]},
            ]},
            {"id": "syncope-view-reference", "title": "참고사항", "kind": "note", "groups": [
                {"title": "원문 메모", "items": [
                    view_item("syncope-ref-definition", "Syncope는 LOC가 있었던 경우로 기록", ["i-f858019a30f5"]),
                ]},
            ]},
        ]
    },
    "headache": {
        "sections": [
            {"id": "headache-view-history", "title": "Hx", "kind": "history", "groups": [
                *neuro_history_groups("headache"),
                {"title": "Headache", "items": [
                    view_item("headache-hx-character", "Character / Pulsatile", ["i-9fc7e16784c7", "i-9cfdc43f0e0f", "i-29e1606c5666", "i-4d8fc6f58f75"]),
                    view_item("headache-hx-location", "Location", ["i-9fc7e16784c7", "i-9cfdc43f0e0f", "i-ffc390c13501"]),
                    view_item("headache-hx-onset", "Mode of onset: Sudden / Gradual · AM / PM", ["i-9fc7e16784c7", "i-29b81de03b58", "i-3bd2beb9a620", "i-a4eafc7a2e27"]),
                    view_item("headache-hx-duration", "Duration", ["i-9fc7e16784c7", "i-9cfdc43f0e0f", "i-e70103d43042"]),
                    view_item("headache-hx-aura", "Aura / Prodrome", ["i-9fc7e16784c7", "i-29b81de03b58", "i-74fa33af7ce3"]),
                    view_item("headache-hx-analgesic", "Analgesic effect", ["i-9fc7e16784c7", "i-29b81de03b58", "i-9d87bd973952"]),
                    view_item("headache-hx-associated", "Nausea / Vomiting / Dizziness / Other associated symptoms", ["i-29b81de03b58", "i-9de2e117b6a9"]),
                    view_item("headache-hx-factor", "Trauma / Family Hx / Sleep disturbance / Tenderness point", ["i-79bdeb7f9c37"]),
                ]},
            ]},
            {"id": "headache-view-exam", "title": "PEx", "kind": "exam", "groups": [
                {"title": "Neurologic", "items": [
                    view_item("headache-pe-nuchal", "Nuchal tenderness", ["i-05a884b2bfd5"]),
                    view_item("headache-pe-deficit", "Neurologic deficit", ["i-ba842357a8d8"]),
                ]},
            ]},
        ]
    },
    "seizure": {
        "sections": [
            {"id": "seizure-view-history", "title": "Hx", "kind": "history", "groups": [
                *neuro_history_groups("seizure-common"),
                {"title": "Ictal", "items": [
                    view_item("seizure-hx-type", "Type: GTC / Partial", ["i-5b74d90d649a", "i-ae89dd865504"]),
                    view_item("seizure-hx-site", "Involved body part", ["i-0c9edd42be8b", "i-ae89dd865504"]),
                    view_item("seizure-hx-duration", "Duration / First attack", ["i-64f5b3d5fed6", "i-ae89dd865504"]),
                    view_item("seizure-hx-aura", "Aura", ["i-26f686a03c4b", "i-f42db10ce4f7"]),
                    view_item("seizure-hx-eye", "Eyeball deviation", ["i-f0b47426e7f9", "i-f42db10ce4f7"]),
                    view_item("seizure-hx-foamy", "Foamy salivation", ["i-75c5995c9d79", "i-f42db10ce4f7"]),
                    view_item("seizure-hx-cyanosis", "Cyanosis", ["i-b2313f955111", "i-f42db10ce4f7"]),
                    view_item("seizure-hx-bite", "Tongue bite", ["i-83e4105cd93b", "i-f42db10ce4f7"]),
                ]},
                {"title": "Postictal · Background", "items": [
                    view_item("seizure-hx-postictal", "Postictal: Sleep / Confusion / Urination / Defecation", ["i-dfa4b6f07ef6", "i-a892e9cfe5c3"]),
                    view_item("seizure-hx-family", "Family Hx / Personal Hx", ["i-aa2f3fa3f103", "i-a892e9cfe5c3"]),
                    view_item("seizure-hx-nutrition", "Nutritional status", ["i-c181139b0f70", "i-a892e9cfe5c3"]),
                    view_item("seizure-hx-medication", "Antiepileptic medication / Last dose time", ["i-9fe7bc643a6a", "i-60884bae711f"]),
                    view_item("seizure-hx-alcohol", "Last alcohol", ["i-5ae8a078122d", "i-60884bae711f"]),
                    view_item("seizure-hx-sleep", "Sleep hours per day", ["i-821430aff642", "i-60884bae711f"]),
                ]},
            ]},
        ]
    },
    "mental-change": {
        "sections": [
            {"id": "mental-view-history", "title": "Hx", "kind": "history", "groups": [
                *neuro_history_groups("mental"),
            ]},
            {"id": "mental-view-exam", "title": "PEx", "kind": "exam", "groups": [
                {"title": "Mental · Respiration", "items": [
                    view_item("mental-pe-mental", "Mental status", ["i-5880a2a9aa60", "i-7605224c4f7e"], "Stroke 진찰 참고"),
                    view_item("mental-pe-resp", "Respiration: Regular / Irregular · Deep / Shallow", ["i-5880a2a9aa60", "i-bf300566329e"]),
                ]},
                {"title": "Pupil · Response", "items": [
                    view_item("mental-pe-pupil", "Pupil size / Symmetry", ["i-fe4bc183cc47", "i-593abf312fe2"]),
                    view_item("mental-pe-light", "Light reflex", ["i-fe4bc183cc47", "i-2c0ef8400763"]),
                    view_item("mental-pe-touch", "휴지로 눈을 살짝 건드렸을 때 반응", ["i-fe4bc183cc47", "i-9e1ef0fb5a14"]),
                    view_item("mental-pe-pain", "Pain response: Right upper / Left upper / Right lower / Left lower extremity", ["i-485924cb448e"]),
                    view_item("mental-pe-babinski", "Babinski reflex: Right / Left", ["i-f9d2ad838f38"]),
                ]},
            ]},
        ]
    },
    "stroke": {
        "sections": [
            {"id": "stroke-view-history", "title": "Hx", "kind": "history", "groups": [
                *neuro_history_groups("stroke"),
                {"title": "Time", "items": [
                    view_item("stroke-hx-time", "Last normal time / First abnormal time", ["i-eddf689b48ac"]),
                ]},
            ]},
            {"id": "stroke-view-exam", "title": "PEx", "kind": "exam", "groups": [
                {"title": "Mental · Commands", "items": [
                    view_item("stroke-pe-mental", "Mentation: Alert / Drowsy / Stupor / Semicoma / Coma", ["i-c9dceb3fed3a"], "Drowsy: 말에 반응 · Stupor: 자극에 반응 · Semicoma: Light reflex (+)"),
                    view_item("stroke-pe-command", "Month / Age / Eye open-close / Hand grip-release", ["i-e998b4dd9427"]),
                ]},
                {"title": "Cranial nerve · Language", "items": [
                    view_item("stroke-pe-eye-face", "Horizontal eye movement / Vision / Facial palsy", ["i-68765d3a2beb"], "이마 주름만 가능하면 central pattern"),
                    view_item("stroke-pe-language", "Dysarthria / Incoherent speech / Impaired comprehension", ["i-fe7269b0f02e"]),
                ]},
                {"title": "Motor · Sensory · Cerebellar", "items": [
                    view_item("stroke-pe-power", "Motor grade: 5 유지 / 4 떨어짐 / 3 들었다 떨어짐 / 2 수평 이동 / 1 움직임 없음", ["i-2146beb834c1"]),
                    view_item("stroke-pe-limb", "Right upper / Left upper / Right lower / Left lower extremity", ["i-9d85b6c7f674"]),
                    view_item("stroke-pe-cerebellar", "Finger-to-finger / Heel-to-shin / Sensory change", ["i-f4d9158beb62"]),
                ]},
            ]},
            {"id": "stroke-view-reference", "title": "참고사항", "kind": "note", "groups": [
                {"title": "보고", "items": [
                    view_item("stroke-ref-hyperacute", "증상 발생 3시간 이내인 경우 주증상 확인 후 즉시 연락", ["i-2bace8d99e96"], "원문 인계 기준"),
                ]},
            ]},
        ]
    },
    "obgyn-interview": {
        "sections": [
            {"id": "ob-view-history", "title": "Hx", "kind": "history", "groups": [
                {"title": "Gynecologic history", "items": [
                    view_item("ob-hx-background", "Previous gynecologic care / TPAL / Marital status / NPO time", ["i-1109f9f55fe5"], "필요하면 보호자를 내보내고 환자와 단독으로 확인"),
                    view_item("ob-hx-menstrual", "LMP / Menstrual cycle / Duration / Amount / Dysmenorrhea", ["i-6ea8e54d6744"]),
                    view_item("ob-hx-sexual", "Last coitus / Dyspareunia", ["i-68d84b1f6aac"]),
                ]},
                {"title": "Symptoms", "items": [
                    view_item("ob-hx-vaginal", "Vaginal bleeding / Vaginal discharge / Abnormal bleeding / Discharge change / Bleeding amount", ["i-49c213f030fe", "i-ccbca1cd1f76"]),
                ]},
            ]},
            {"id": "ob-view-reference", "title": "참고사항", "kind": "note", "groups": [
                {"title": "원문 인계 범위", "items": [
                    view_item("ob-ref-scope", "OBGY: Preterm labor / Hemoperitoneum / Vaginal bleeding 등", ["i-a81efe90df85", "i-057ab3fb8640", "i-754621b3148d", "i-1517462b6cc6"]),
                    view_item("ob-ref-emr", "본원 OBGY 추적 환자는 EMR 내용을 참고하여 차팅", ["i-301803998d87"]),
                ]},
            ]},
        ]
    },
    "pregnancy": {
        "sections": [
            {"id": "pregnancy-view-history", "title": "Hx", "kind": "history", "groups": [
                {"title": "Gynecologic history", "items": [
                    view_item("pregnancy-hx-background", "Previous gynecologic care / Marital status", ["i-1109f9f55fe5"], "필요하면 보호자를 내보내고 환자와 단독으로 확인"),
                    view_item("pregnancy-hx-menstrual", "LMP / Menstrual cycle / Duration / Amount / Dysmenorrhea", ["i-6ea8e54d6744"]),
                    view_item("pregnancy-hx-sexual", "Last coitus / Dyspareunia", ["i-68d84b1f6aac"]),
                    view_item("pregnancy-hx-vaginal", "Vaginal bleeding / Vaginal discharge / Abnormal bleeding / Discharge change / Bleeding amount", ["i-49c213f030fe", "i-ccbca1cd1f76"]),
                ]},
                {"title": "Obstetric history", "items": [
                    view_item("pregnancy-hx-tpal", "TPAL", ["i-1109f9f55fe5", "i-5e79003059b9"]),
                    view_item("pregnancy-hx-iup", "IUP: 정확한 gestational week and day / OT", ["i-10e0162d3aee"]),
                    view_item("pregnancy-hx-labor", "진통·배뭉침 / 주기 / 지속시간", ["i-c75d69226429"]),
                    view_item("pregnancy-hx-lmp", "LMP", ["i-0138e8dfa9af"]),
                    view_item("pregnancy-hx-edc", "Estimated date of confinement (EDC)", ["i-57925bf76ebf"]),
                    view_item("pregnancy-hx-npo", "NPO time", ["i-1109f9f55fe5", "i-0c081eadaa0e"]),
                    view_item("pregnancy-hx-operation", "Op Hx", ["i-ff7aec9585a2"]),
                ]},
            ]},
            {"id": "pregnancy-view-reference", "title": "참고사항", "kind": "note", "groups": [
                {"title": "원문 인계 범위", "items": [
                    view_item("pregnancy-ref-scope", "OBGY: Preterm labor / Hemoperitoneum / Vaginal bleeding 등", ["i-a81efe90df85", "i-057ab3fb8640", "i-754621b3148d", "i-1517462b6cc6"]),
                    view_item("pregnancy-ref-emr", "본원 OBGY 추적 환자는 EMR 내용을 참고하여 차팅", ["i-301803998d87"]),
                ]},
            ]},
        ]
    },
    "fever": {
        "sections": [
            {"id": "fever-view-history", "title": "Hx", "kind": "history", "groups": [
                *peds_history_groups("fever", fccsr_sources=("i-f67d6676b11b",), daily_sources=("i-ca2d5f59c88c", "i-f67d6676b11b")),
                {"title": "Fever", "items": [
                    view_item("fever-hx-temperature", "Maximum temperature at home / Temperature on arrival", ["i-09f9f960f4d3", "i-d6027d327579"]),
                    view_item("fever-hx-antipyretic", "Antipyretic: Last dose / Number of doses / Type / Interval / Response", ["i-09f9f960f4d3", "i-d410e445b7d6", "i-d054632e1182"]),
                ]},
            ]},
            {"id": "fever-view-exam", "title": "PEx", "kind": "exam", "groups": [
                *peds_exam_groups("fever", throat_sources=("i-88be3820287a",), neck_sources=("i-78f591a013bf",), lung_sources=("i-89b8406e0d1a",), bowel_sources=("i-85e00579f43c",)),
                {"title": "Additional", "items": [
                    view_item("fever-pe-uvula", "Uvular deviation / White patch", ["i-c1abfc2296d2"]),
                    view_item("fever-pe-retraction", "Chest retraction", ["i-92df79d13f9d"]),
                    view_item("fever-pe-ear", "Tympanic redness / TM injection", ["i-1ba15ce64ef8", "i-78f591a013bf"]),
                ]},
            ]},
            {"id": "fever-view-reference", "title": "참고사항", "kind": "example", "groups": [
                {"title": "차팅 예시", "items": [
                    view_item("fever-ref-example", "내원 당일 14시부터 fever. 가정 최고 38.0℃, 내원 시 39.5℃. 14시 해열제 복용 후 호전되었다가 17시 다시 상승. 전일 저녁부터 cough가 있어 당일 아침 local clinic 방문 후 medication.", ["i-f70eebcacd56"]),
                ]},
            ]},
        ]
    },
    "vomiting": {
        "sections": [
            {"id": "vomiting-view-history", "title": "Hx", "kind": "history", "groups": [
                *peds_history_groups("vomiting"),
                {"title": "Vomiting", "items": [
                    view_item("vomiting-hx-count", "Frequency / Pattern: Regurgitation / Vomiting / Projectile", ["i-0cb004905b21"]),
                    view_item("vomiting-hx-content", "Emesis color / Character: Food content / Watery", ["i-0cb004905b21"]),
                ]},
            ]},
            {"id": "vomiting-view-exam", "title": "PEx", "kind": "exam", "groups": [
                *peds_exam_groups("vomiting"),
            ]},
        ]
    },
    "diarrhea": {
        "sections": [
            {"id": "diarrhea-view-history", "title": "Hx", "kind": "history", "groups": [
                *peds_history_groups("diarrhea"),
                {"title": "Diarrhea", "items": [
                    view_item("diarrhea-hx-stool", "Frequency / Character / Color / Last defecation time", ["i-9b0fd04b87dd"]),
                    view_item("diarrhea-hx-npo", "NPO time", ["i-9b0fd04b87dd"]),
                    view_item("diarrhea-hx-diet", "Current diet: 밥 / 미음 / 모유 / 분유", ["i-d8c672ae10ca"]),
                ]},
            ]},
            {"id": "diarrhea-view-exam", "title": "PEx", "kind": "exam", "groups": [
                *peds_exam_groups("diarrhea"),
            ]},
        ]
    },
    "cough": {
        "sections": [
            {"id": "cough-view-history", "title": "Hx", "kind": "history", "groups": [
                *peds_history_groups("cough"),
                {"title": "Cough", "items": [
                    view_item("cough-hx-sound", "Cough sound: Barking or usual cough", ["i-3368440da93b"]),
                    view_item("cough-hx-position", "Worse when supine / Hoarseness", ["i-3368440da93b"]),
                    view_item("cough-hx-atopy", "Atopy/Asthma PHx / FHx", ["i-3368440da93b"]),
                ]},
            ]},
            {"id": "cough-view-exam", "title": "PEx", "kind": "exam", "groups": [
                *peds_exam_groups("cough"),
            ]},
        ]
    },
    "peds-abdominal-pain": {
        "sections": [
            {"id": "peds-abd-view-history", "title": "Hx", "kind": "history", "groups": [
                *peds_history_groups("peds-abd"),
                {"title": "Abdominal pain", "items": [
                    view_item("peds-abd-hx-pain", "Character / Location / Intermittent or Steady / Duration / Relieving time", ["i-26e3ede4229f"]),
                    view_item("peds-abd-hx-bowel", "Last defecation / NPO time", ["i-2e8d142d81a5"]),
                ]},
            ]},
            {"id": "peds-abd-view-exam", "title": "PEx", "kind": "exam", "groups": [
                *peds_exam_groups("peds-abd"),
                {"title": "Abdomen", "items": [
                    view_item("peds-abd-pe-tenderness", "Surgical abdomen / RLQ tenderness / Rebound tenderness", ["i-2e8d142d81a5"]),
                    view_item("peds-abd-pe-sign", "Rovsing sign / Obturator sign / Psoas sign", ["i-e1aa94a6069a"]),
                ]},
            ]},
        ]
    },
    "peds-seizure": {
        "sections": [
            {"id": "peds-seizure-view-history", "title": "Hx", "kind": "history", "groups": [
                *peds_history_groups("peds-seizure"),
                {"title": "Seizure", "items": [
                    view_item("peds-seizure-hx-loc", "LOC", ["i-be829747b960"]),
                    view_item("peds-seizure-hx-eye", "Eyeball deviation", ["i-d953400df2c6"]),
                    view_item("peds-seizure-hx-urine", "Urination", ["i-597bebc96605"]),
                    view_item("peds-seizure-hx-foam", "Foamy salivation", ["i-8ce09ee87474"]),
                    view_item("peds-seizure-hx-past", "Previous seizure Hx", ["i-837190c5a23c"]),
                ]},
            ]},
            {"id": "peds-seizure-view-exam", "title": "PEx", "kind": "exam", "groups": [
                *peds_exam_groups("peds-seizure"),
            ]},
            {"id": "peds-seizure-view-reference", "title": "참고사항", "kind": "example", "groups": [
                {"title": "차팅 예시 · 간단 기록", "items": [
                    view_item("peds-seizure-ref-brief", "00시 seizure 30분 지속 / 04시 seizure 5분 이내 / 경련 상황 기억함", ["i-23456d42c6fc"]),
                ]},
                {"title": "차팅 예시 1 · Ictal", "items": [
                    view_item("peds-seizure-ref-ex1-ictal", "Duration 약 5분 / 사지가 떨리는 양상 / Upper EBD (+) / Perioral cyanosis (+/-)", ["i-bad96a5b387f", "i-fb689eb0618a", "i-dc69f0bb12ba", "i-fc2673bb7748", "i-4d3b5103a30a"]),
                    view_item("peds-seizure-ref-ex1-post", "Postictal weakness. 다른 특이소견은 관찰되지 않음 / Family Hx of epilepsy (-) / Previous seizure Hx (-) / Development: 달리기 가능, 문장 유창", ["i-2c96ef85afac", "i-8b9a8c640bce", "i-2f3dc6ac0206", "i-29448cbaaa9e", "i-73dd027c822c"]),
                    view_item("peds-seizure-ref-ex1-ros", "FCCSR +/+/-/-/- / ANVCD -/-/-/-/-; 1주 전 constipation으로 abdominal pain 있었으나 현재 없음 / TE·TI -/- / Normal lung sound", ["i-a1dac288ec72", "i-44d3ed573ae1", "i-3fbf66a97202", "i-f0282fe3cfb0"]),
                    view_item("peds-seizure-ref-ex1-general", "General condition: Moderate. 보호자 진술상 seizure 외에는 평소처럼 운동·식사하고 상태가 좋아 보였음", ["i-5a2cbc0475fb", "i-f147200e243f"]),
                    view_item("peds-seizure-ref-ex1-neuro", "Mental alert / Gait normal, no imbalance / Ankle clonus -/- / Knee reflex / Normotonia / Upper·Lower G4 G4 / G4 G4 / 의사소통 가능", ["i-bc032a1ed254", "i-2b956438347f", "i-6fddc51fc43b", "i-075fdb65c37b", "i-7691f22e2a0e", "i-cba13eb9d26f", "i-2cfe9b4c15cf"]),
                ]},
                {"title": "차팅 예시 2 · Febrile seizure", "items": [
                    view_item("peds-seizure-ref-ex2-pi", "12개월경 febrile seizure Hx 1회. 내원 2일 전 local clinic에서 목이 부었다는 말을 들었고, 전일 18시부터 fever up to 39.8℃. 내원 약 30분 전 04:15경 1–2분 seizure 후 내원.", ["i-ac579761ba69", "i-edca7648132c"]),
                    view_item("peds-seizure-ref-ex2-pre", "Preictal: 깨어 있었고 미온수 마사지 중 보호자가 안고 있었음", ["i-406b815fb2d3", "i-6c17ef340c59"]),
                    view_item("peds-seizure-ref-ex2-ictal", "EBD 뚜렷하지 않고 눈에 초점 없어 보임 / LOC (+), 불러도 대답 없고 의사소통 불가 / 양측 팔다리가 뻣뻣해짐 / Duration 1–2분 / Cyanosis (+), Drooling (-), Foamy salivation (-), Postictal urination·defecation -/-", ["i-742cc0b30316", "i-f80f91d75429", "i-89049e8df4f3", "i-c911a5fb9aba", "i-3bb8a497989d", "i-34a4ab26187c"]),
                    view_item("peds-seizure-ref-ex2-post", "Postictal: 뻣뻣함이 멈추며 의식이 명료하게 돌아오고 의사소통 가능", ["i-0679481a0b8e", "i-4cad4a81bc53"]),
                    view_item("peds-seizure-ref-ex2-history", "Past convulsion Hx (-) / 부모·형제 convulsion Hx (-)", ["i-a00556823521", "i-e54f06313209"]),
                ]},
            ]},
        ]
    },
    "eye": {
        "sections": [
            {"id": "eye-view-history", "title": "Hx", "kind": "history", "groups": [
                {"title": "Symptoms", "items": [
                    view_item("eye-hx-symptoms", "Ocular pain / Foreign body sensation / Conjunctival injection / Discharge", ["i-28ecfc7fcdda", "i-e20bddff3b1d", "i-d16c7ea78bb3", "i-4f259c29f187"]),
                    view_item("eye-hx-vision", "Blurred vision / Diplopia / Baseline vision and change", ["i-d0723942eb28", "i-cec96462eb1a", "i-18279ab2c20f"]),
                ]},
                {"title": "Past history", "items": [
                    view_item("eye-hx-past", "OT HX", ["i-f7aed3e8baa4"]),
                ]},
            ]},
            {"id": "eye-view-exam", "title": "PEx", "kind": "exam", "groups": [
                {"title": "Eye", "items": [
                    view_item("eye-pe-light", "Light reflex", ["i-b5dbf567b8b4"]),
                    view_item("eye-pe-eom", "Extraocular movement", ["i-3354730896e4"]),
                ]},
            ]},
            {"id": "eye-view-reference", "title": "참고사항", "kind": "note", "groups": [
                {"title": "보고·처치", "items": [
                    view_item("eye-ref-irrigation", "Foreign body, 특히 화학물질 노출은 즉시 보고; 지시 시 suture room에서 eye irrigation", ["i-12d19359ec2c"]),
                ]},
            ]},
        ]
    },
    "ear": {
        "sections": [
            {"id": "ear-view-history", "title": "Hx", "kind": "history", "groups": [
                {"title": "Symptoms · Exposure", "items": [
                    view_item("ear-hx-symptoms", "Otalgia / Tinnitus / Ear fullness / Hearing difficulty or loss / Dizziness", ["i-9ed2447b8d64", "i-00f4e17f31db", "i-7eda19f1989e", "i-fdd513cc18af"]),
                    view_item("ear-hx-local", "Redness / Swelling", ["i-9ed2447b8d64"]),
                    view_item("ear-hx-exposure", "URI symptoms / Trauma / Recent water exposure", ["i-5a33dba2ab00", "i-87611c37fa0b"]),
                ]},
            ]},
            {"id": "ear-view-reference", "title": "참고사항", "kind": "example", "groups": [
                {"title": "차팅 예시 · Ear fullness / r/o AOM", "items": [
                    view_item("ear-ref-pi", "16시부터 물속이나 비행기에 있는 듯 귀가 먹먹하고 잘 들리지 않아 내원. 우측이 좌측보다 심하며 우측 hearing은 좌측의 5–60% 정도라고 함. Mild tinnitus 동반. Underlying disease 없음.", ["i-c58066a39b79", "i-4f8534ce0b1a", "i-0d4397058996", "i-87ad0ab613de", "i-46fe29a75c9a", "i-7443589aa977", "i-7cb201e1e2fd"]),
                    view_item("ear-ref-ros", "FCCSR +-+-+; fever는 ER 도착 후 인지 / ANVCD ----- / FUND HIS ---- ---", ["i-8ee23d3a8187", "i-1a66fc8ad5f8", "i-c9b17d933458"]),
                    view_item("ear-ref-pe-general", "Lung sound clear / No focal abdominal tenderness / CVAT -/-", ["i-88c5ef8c7891", "i-ce05ec24f986", "i-63a0c00c9b37"]),
                    view_item("ear-ref-pe-ear", "Right TM r/o intact; cerumen으로 정확한 관찰 어려움 / Left TM intact / 최근 수영장 노출 없음", ["i-ab1f37c078d6", "i-79549d9c1f3c", "i-5a54890e1070"]),
                ]},
            ]},
        ]
    },
    "epistaxis": {
        "sections": [
            {"id": "epistaxis-view-history", "title": "Hx", "kind": "history", "groups": [
                {"title": "Present illness", "items": [
                    view_item("epistaxis-hx-bleeding", "Bleeding amount / Onset time / Current active bleeding", ["i-4a6311b2bab7"]),
                ]},
                {"title": "History", "items": [
                    view_item("epistaxis-hx-background", "Drug / HTN Hx", ["i-ca15bdb71320"]),
                ]},
            ]},
            {"id": "epistaxis-view-exam", "title": "PEx", "kind": "exam", "groups": [
                {"title": "Bleeding", "items": [
                    view_item("epistaxis-pe-throat", "Active bleeding / Oropharynx", ["i-4a6311b2bab7"], "목 안을 반드시 확인"),
                    view_item("epistaxis-pe-bp", "Blood pressure", ["i-ca15bdb71320"]),
                ]},
            ]},
            {"id": "epistaxis-view-reference", "title": "참고사항", "kind": "note", "groups": [
                {"title": "처치", "items": [
                    view_item("epistaxis-ref-merocel", "Active bleeding: Merocel", ["i-ed62a7868ff4"]),
                ]},
            ]},
        ]
    },
    "psychiatry-interview": {
        "sections": [
            {"id": "psychiatry-view-history", "title": "Hx", "kind": "history", "groups": [
                {"title": "Basic", "items": [
                    view_item("psychiatry-hx-cc", "CC", ["i-93bec4f5a11f", "i-783f0ccc8ad0", "i-a3f32e80a086", "i-1cfcd0419c4d", "i-48e0d543b3fc"]),
                    view_item("psychiatry-hx-current", "초진 당시 증상 유무", ["i-b6b3279a5fe5"]),
                    view_item("psychiatry-hx-stress", "PI / 최근 stress factor", ["i-504770b9ef6c", "i-326344007df5"]),
                ]},
                {"title": "Past psychiatric · Family history", "items": [
                    view_item("psychiatry-hx-past", "Past NP Hx / FHx", ["i-fd017583932e", "i-f97606906869"]),
                    view_item("psychiatry-hx-compliance", "Drug compliance", ["i-37fe40251ce9"], "정신과적 과거력이 있는 경우"),
                    view_item("psychiatry-hx-discharge", "마지막 퇴원 이후 경과", ["i-0813ce0b8951"], "입퇴원력이 있는 경우"),
                    view_item("psychiatry-hx-first", "이전에도 같은 증상이 있었는지 / First episode인지", ["i-946e076984ba"], "정신과적 과거력이 없는 경우"),
                ]},
                {"title": "Social history", "items": [
                    view_item("psychiatry-hx-household", "동거인 / Genogram", ["i-7da5c539aa44", "i-5c3a50bc1ae3", "i-b5075a04bd96"]),
                    view_item("psychiatry-hx-job", "Occupation", ["i-1cf9af4b7bfa"]),
                    view_item("psychiatry-hx-sleep", "Sleep / Fragmentation", ["i-f089d42d65bc", "i-5010d4f57ede", "i-24ee16959511"]),
                    view_item("psychiatry-hx-appetite", "Appetite", ["i-29695720395d", "i-b2c9fb17e5b3"]),
                    view_item("psychiatry-hx-smoking", "Smoking", ["i-fb406c1d6afc"], "필수 항목 아님"),
                    view_item("psychiatry-hx-alcohol", "Alcohol", ["i-351476d46859"], "필수 항목 아님"),
                    view_item("psychiatry-hx-caffeine", "Caffeine", ["i-13ed46f5c82e"], "불안·두근거림이 있는 경우"),
                ]},
                {"title": "Perceptual disturbance", "items": [
                    view_item("psychiatry-hx-hallucination", "A-H / V-H", ["i-90dad06721fb", "i-a5f32442cb55", "i-836f2bdf14e8"], "헛것이 보이거나 주변에 아무도 없는데 소리가 들리는지"),
                    view_item("psychiatry-hx-illusion", "Illusion", ["i-2211a268632f"]),
                    view_item("psychiatry-hx-derealization", "Derealization / Depersonalization", ["i-afcdf3f62fec"]),
                ]},
                {"title": "Thought · Mood", "items": [
                    view_item("psychiatry-hx-drive", "Loss of will / Energy / Pleasure", ["i-5425c2d47801", "i-aad1c5cd2aa6", "i-368fa3cdb991"], "의욕·기운·즐거움 확인"),
                    view_item("psychiatry-hx-suicide", "Suicidal idea / Plan / Attempt", ["i-04e13c90aa27", "i-3931bf6f6de2"], "죽고 싶은지, 계획을 세운 적이 있는지, 자해·자살 시도 여부"),
                ]},
            ]},
            {"id": "psychiatry-view-reference", "title": "참고사항", "kind": "note", "groups": [
                {"title": "초진·보고", "items": [
                    view_item("psychiatry-ref-consent", "정신과 진료 동의 여부", ["i-2f6c9dc4a7c1"], "젊은 환자는 진료 기록이 남을 수 있음을 설명"),
                    view_item("psychiatry-ref-conversation", "현재 대화 가능 여부", ["i-00bfc259bdbd"], "Drowsy 상태이면 alert해졌을 때 notify"),
                    view_item("psychiatry-ref-firstline", "첫 줄: 정신과 진료 동의 / 협조적 / 원활한 대화 가능 여부", ["np-pdf-firstline"]),
                    view_item("psychiatry-ref-summary", "확인 항목 요약: C.C / Onset / Past Hx / 동거인 / 직업 / 내원 당시 증상 / 최근 stress factor / Compliance / Sleep / Appetite / Suicidal idea·plan·attempt", ["np-pdf-summary"]),
                    view_item("psychiatry-ref-safety", "위험해 보이는 상황에서는 무리하지 말고 정신과 전공의 등 주변 의료진과 상의", ["i-45ca9b877fa0", "i-35a8bcbc9c0f"]),
                ]},
                {"title": "응답 예시 · Sleep / Appetite", "items": [
                    view_item("psychiatry-ref-sleep-response", "Sleep: Good / Fair / Poor · Total sleep time 7 hr (00:00–07:00) · Fragmented or not", ["i-0f2e94f4bc55", "i-f93d7de309a1", "i-45c8918b7306"]),
                    view_item("psychiatry-ref-appetite-response", "Appetite: Good / Fair / Poor · Increased / Decreased", ["i-28df4eae0b81", "i-d6beec8a9b9f"]),
                ]},
                {"title": "응답 예시 · Smoking / Alcohol / Caffeine", "items": [
                    view_item("psychiatry-ref-smoking-response", "Smoking: None / 이틀에 한 갑 / 음주 시 3개비", ["i-c4d2366055e8", "i-6cfb97fc22f3", "i-d9282e1eb585"]),
                    view_item("psychiatry-ref-alcohol-response", "Alcohol: None / 주 3회 소주 2병 / 잦은 폭음", ["i-ae2fd3f70acf", "i-28ebb7b0feac", "i-d85ca4d343e2"]),
                    view_item("psychiatry-ref-caffeine-response", "Caffeine: 하루 커피 한 잔 / 아침에", ["i-fe13f3dd3046", "i-1fef2a3ac3c7"]),
                ]},
                {"title": "문구 예시 · Chief complaint / Onset", "items": [
                    view_item("psychiatry-ref-cc-example", "죽고 싶음·자해 충동·난폭 행동 / 약물 복용·손목 자해·목맴·고층 이동 / 우울·불안·두근거림·죽을 것 같은 느낌·걱정 / 불면·잦은 각성", ["i-74e1eb994f0a", "i-16dbbc960cbe", "i-51288bb4ad2d", "i-22a95beabd75"]),
                    view_item("psychiatry-ref-onset-example", "Onset: 내원 당일 / 내원 ○일·주·개월 전", ["i-8342aa0da8a7", "i-6bc117ddb0ea"]),
                ]},
                {"title": "문구 예시 · Past / Social history", "items": [
                    view_item("psychiatry-ref-past-example", "정신과적 과거력 없음 / MDD 본원 OPD 추적 / Bipolar I disorder 본원 4회 입퇴원 / Panic disorder local NP 추적", ["i-3b9cfbbfdbfa", "i-65fcc167ba99", "i-513d80e67c17", "i-6c92388e8ac5"]),
                    view_item("psychiatry-ref-household-example", "혼자 거주 / 부모·남동생과 거주 / 연인과 거주", ["i-12b76fb6de85", "i-45f7cd0316a3", "i-77250d5facdd"]),
                    view_item("psychiatry-ref-job-example", "초등학교 교사 / 교통공사 직원 / 대학원생 / 택시 운전기사", ["i-860601a21c51", "i-dbd9b553ee8b", "i-70df43f0dd32", "i-ccd84f3b4e90"]),
                ]},
                {"title": "차팅 양식", "items": [
                    view_item("psychiatry-ref-template-intro", "정신과 진료 동의. 협조적이며 원활한 대화 가능.", ["np-pdf-template-label", "i-98d304c7e190"]),
                    view_item("psychiatry-ref-template-pi", "#. Chief complaint / Onset: 내원 ○일 전 / 초진 시 증상 호전 또는 심한 증상 호소", ["i-a19ddea45be3", "i-488d1459bc8e"]),
                    view_item("psychiatry-ref-template-social", "Sleep: Good·Fair·Poor / TST / Fragmentation · Appetite: Good·Fair·Poor", ["i-f98792661760", "i-33b92a80ee67"]),
                    view_item("psychiatry-ref-template-mse", "A-H/V-H / Loss of will·energy·pleasure / Suicidal idea·plan·attempt", ["i-8c67144fc367", "i-269938b69699", "i-5a5857592f63"]),
                ]},
                {"title": "차팅 예시 1 · Anxiety / Palpitation", "items": [
                    view_item("psychiatry-ref-ex1-intro", "F/34. 정신과 진료 동의, 협조적이며 대화 가능. C.C: 가슴이 두근거리고 죽을 것 같음. Onset: 내원 당일.", ["i-f5e712dd832d", "i-fdfecce4683c", "i-7044aaea42f4"]),
                    view_item("psychiatry-ref-ex1-pi", "정신과적 과거력 없음. 남편과 사는 초등학교 교사. 당일 학생이 던진 물건에 맞은 뒤 증상 발생. 초진 시 다소 호전됐으나 불안감 남음.", ["i-8aafc55fe932", "i-a94a020f822d", "i-2a7a9a6fff35"]),
                    view_item("psychiatry-ref-ex1-social", "Sleep poor, TST 5 hr, fragmented / Appetite fair / Caffeine 하루 한 잔", ["i-17274170fed3", "i-84e4255b71bd"]),
                    view_item("psychiatry-ref-ex1-mse", "A-H/V-H -/- / Loss of will·energy·pleasure -/-/- / Suicidal idea·plan·attempt -/-/-", ["i-eb71bb2d876c", "i-f77662ef8001", "i-6cd83d1495c0"]),
                ]},
                {"title": "차팅 예시 2 · Bipolar disorder", "items": [
                    view_item("psychiatry-ref-ex2-intro", "M/26. 정신과 진료 동의. 말이 빠르고 자주 맥락을 벗어나지만 비교적 협조적이며 대화 가능. C.C: 밤새 춤춤. Onset: 내원 전날.", ["i-d9c09183994b", "i-ccb0df1a0249", "i-947914bb7b25"]),
                    view_item("psychiatry-ref-ex2-pi", "Bipolar I disorder로 본원 NP 10회 입퇴원한 사진작가. 3개월 전 마지막 퇴원, 1개월 전 장염으로 약 복용 불량, 1주 전부터 기분 상승·과소비, 3일 전부터 불면 후 밤새 클럽에 있었고 부모 권유로 내원. 초진 시 들뜬 기분과 병실을 나가려는 모습.", ["i-ab8771b6db1e", "i-5507a856743d", "i-0b6a1bec4127"]),
                    view_item("psychiatry-ref-ex2-social", "Sleep poor, 최근 3일간 수면 없음 / Appetite fair, 2주 전부터 decreased", ["i-6aa778153f43", "i-32a0ee60491b"]),
                    view_item("psychiatry-ref-ex2-mse", "A-H/V-H +/-: 귀에서 노랫소리가 들림 / Loss of will·energy·pleasure -/-/- / Suicidal idea·plan·attempt -/-/-", ["i-da3e1e44effd", "i-d3778330e6ce", "i-a8bd8780859e"]),
                ]},
                {"title": "차팅 예시 3 · Depression / Suicidal idea", "items": [
                    view_item("psychiatry-ref-ex3-intro", "M/76. 정신과 진료 동의. 말이 느리고 종종 멈추지만 협조적이며 대화 가능. C.C: 죽고 싶음. Onset: 내원 1년 전.", ["i-fd1983798474", "i-5f0c119d7e35", "i-54a542d8bade"]),
                    view_item("psychiatry-ref-ex3-pi", "MDD로 local NP 추적 중이며 혼자 사는 무직. 20년 전 사별 후 우울감으로 medication 시작. 1년 전 다친 뒤 외출이 어려워지며 우울감과 자살사고 악화. 금일 다리에서 뛰어내리려다 행인 신고로 내원. 초진 시 눈을 감고 누워 무뚝뚝하게 답함.", ["i-350bc3689e2c", "i-d78d139a5482", "i-80ecea7215b5"]),
                    view_item("psychiatry-ref-ex3-social", "Sleep poor, TST 4 hr, fragmented / Appetite poor", ["i-27dbed1e2f21", "i-5fb72d5416f8"]),
                    view_item("psychiatry-ref-ex3-mse", "A-H/V-H -/+: 천장에 저승사자가 보임 / Loss of will·energy·pleasure -/+/+ / Suicidal idea·plan·attempt +/-/-", ["i-5807cca5f5e0", "i-9c05f6d645a1", "i-f9fe431ca32a"]),
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

category_specs = [
    ("00", "입원관리", 12, True),
    ("01", "소화기", 1, False),
    ("02", "순환기", 2, False),
    ("03", "호흡기", 3, False),
    ("04", "신장/비뇨기", 4, False),
    ("05", "전신증상", 5, False),
    ("06", "근골격/피부", 6, False),
    ("07", "신경", 7, False),
    ("12", "정신", 8, False),
    ("08", "산부", 9, False),
    ("09", "소아", 10, False),
    ("10", "눈/이비인후", 11, False),
    ("11", "상담", 13, True),
]
categories = [{"id": cid, "name": name, "order": order, "secondary": secondary} for cid, name, order, secondary in category_specs]
catalog = {
 "00": [("acute-condition","급성상태",[]),("abnormal-lab","수치이상",[]),("prescription","처방체액",[]),("device","기구문제",[]),("ward-event","병동사건",[])],
 "01": [("abdominal-pain","복통",["복부 통증","급성복통","abdominal pain","abd pain","AP"]),("dyspepsia","소화불량 / 만성 복통",["dyspepsia"]),("hematemesis","토혈",["hematemesis"]),("bloody-stool","혈변",["hematochezia","melena"]),("vomiting","오심 구토",["오심 / 구토","구역","nausea","vomiting","N/V","emesis"]),("constipation","변비",["constipation"]),("diarrhea","설사",["diarrhea"]),("jaundice","황달",["jaundice"])],
 "02": [("chest-pain","흉통",["가슴통증","가슴 통증","chest pain","CP"]),("syncope","실신",["syncope","LOC","blackout"]),("palpitation","두근거림",["palpitation","palpitations"]),("hypertension","고혈압",["hypertension","HTN"]),("dyslipidemia","이상지질혈증",["dyslipidemia"])],
 "03": [("cough","기침",["cough"]),("rhinorrhea","콧물 / 코막힘",["rhinorrhea","nasal obstruction"]),("hemoptysis","객혈",["hemoptysis"]),("dyspnea","호흡곤란",["숨참","숨차","dyspnea","dyspnoea","SOB","shortness of breath"])],
 "04": [("polyuria","다뇨",["polyuria"]),("oliguria","핍뇨",["oliguria"]),("hematuria","혈뇨",["hematuria"]),("urinary-symptoms","배뇨이상",["배뇨이상 / 빈뇨","배뇨장애","빈뇨","배뇨통","dysuria","frequency","urinary symptoms"]),("incontinence","요실금",["incontinence"]),("flank-pain","옆구리 통",["옆구리 통증","flank pain","renal colic"])],
 "05": [("fever","발열",["열","fever","pyrexia"]),("bruising","멍",["bruise"]),("fatigue","피로",["fatigue"]),("weight-loss","체중감소",["weight loss"]),("weight-gain","체중증가",["weight gain"]),("poisoning","중독 / 과량복용",["약물 과다복용","poisoning","overdose","intoxication"])],
 "06": [("joint-pain","관절 문제",["관절 통증 / 붓기","관절 통증","붓기","arthralgia","joint pain"]),("neck-pain","목 통증",["neck pain"]),("back-pain","허리 통증",["요통","등 통증","back pain","LBP"]),("rash","피부 발진",["rash","skin rash"]),("trauma","상처 외상",["상처 / 외상","열상","교통사고","상해","trauma","laceration","lac","TA","wound"]),("head-trauma","두부외상",["머리 외상","head trauma","head injury"])],
 "07": [("mood","기분변화",["우울","mood","depression"]),("anxiety","불안",["anxiety","panic"]),("sleep","수면장애",["불면","insomnia","sleep"]),("memory","기억력 저하",["memory loss"]),("dizziness","어지럼",["어지럼증","어지러움","dizziness","dizzy","vertigo","TRS"]),("headache","두통",["headache","HA"]),("peds-seizure","경련 (소아)",["소아 경련","열성경련","pediatric seizure","febrile seizure"]),("seizure","경련",["경련 (성인)","성인 경련","seizure","convulsion","GTC"]),("weakness","근력 / 감각이상",["weakness","sensory change"]),("mental-change","의식장애",["의식저하","mental change","AMS","altered mental status"]),("movement","떨림 / 운동이상",["tremor"]),("stroke","뇌졸중",["뇌졸중 의심","stroke","CVA"])],
 "12": [],
 "08": [("breast-pain","유방통",["mastalgia"]),("breast-mass","유방덩이",["breast mass"]),("vaginal-discharge","질분비물",["vaginal discharge"]),("vaginal-bleeding","질출혈",["vaginal bleeding"]),("menstrual","월경이상 (무월경)",["amenorrhea"]),("dysmenorrhea","월경통 (월경과다)",["dysmenorrhea","menorrhagia"]),("pregnancy","산전 진찰",["산모","임신","pregnancy","preterm labor","IUP"]),("pelvic-pain","골반통",["pelvic pain"])],
 "09": [("growth","성장 지연",["growth delay"]),("development","발달 지연",["developmental delay"]),("vaccination","예방접종",["vaccination"]),("peds-common","소아 공통",["소아","pediatrics","PD"])],
 "10": [("eye","눈 이상",["눈 통증 / 시력저하","안통","시력저하","eye pain","ocular pain","blurred vision"]),("throat","인후통 / 연하곤란",["sore throat","dysphagia"]),("ear","귀 이상",["귀 통증 / 청력저하","귀먹먹함","otalgia","hearing loss","tinnitus"]),("epistaxis","코 이상",["코피","비출혈","epistaxis"])],
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
catalog["12"].append(("psychiatry-interview", "정신과 문진", specialty_aliases(psychiatric_ids, ["정신과", "psychiatry", "NP", "정신과 공통"])))
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
specialty_ids = {"psychiatry-interview", "obgyn-interview", "peds-common"}
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

symptom_abbreviations = [
    {"label": "FCCSR", "expansion": ["Fever", "Chill", "Cough", "Sputum", "Rhinorrhea"]},
    {"label": "ANVCD", "expansion": ["Anorexia", "Nausea", "Vomiting", "Constipation", "Diarrhea"]},
    {"label": "FUND HIS", "expansion": ["Frequency", "Urgency", "Nocturia", "Dysuria", "Hesitancy", "Incomplete emptying", "Straining"]},
]

data = {"schemaVersion": 1, "contentVersion": "2026-09-27-beta.13", "categories": categories,
        "sections": list(groups.values()), "complaints": complaints,
        "symptomAbbreviations": symptom_abbreviations,
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
 "specialtyEntries": [c["name"] for c in complaints if c["id"] in ("psychiatry-interview", "obgyn-interview", "peds-common")],
 "missingComplaints": [c["name"] for c in complaints if c["status"]=="missing"],
 "method": "의미를 추정한 병합 없음. 동일 구획의 공백·앞쪽 bullet 차이만 있는 원문만 통합. 복합 항목과 조건 보존."}
(DOCS / "content-audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

lines = ["# ER 초진 자료 정리본", "", "원문 문진·진찰·인계 메모·차팅 예시를 구분한 베타 자료입니다. 의학 내용을 추가하거나 임상 지침으로 검증하지 않았습니다.", "",
 f"- 원본 {len(archive['sources'])}개 / 텍스트 블록 {source_count}개 / 미분류 0개", f"- 정리된 항목 {item_count}개 / 분류 항목 {len(complaints)}개 중 자료 보유 {report['complaintsWithSourceMaterial']}개", "",
 "- 일반 공통 문진은 각 신경 증상에 공유하고, 정신과·산부인과·소아과 공통 양식은 독립 문진으로 연결합니다. 소아 증상 자료는 모두 소아 분류에 별도로 배치합니다.",
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
        lines.append(f"- {cond}{item['text']}")
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
