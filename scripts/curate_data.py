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
        complaints.append(item)

data = {"schemaVersion": 1, "contentVersion": "2026-09-26-beta.3", "categories": categories,
        "sections": list(groups.values()), "complaints": complaints,
        "referenceSections": ["routine-history","routine-exam","handover-general"]}
(DATA / "chief-complaints.json").write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
provenance = {"schemaVersion": 1, "sources": archive["sources"],
              "assignments": dict(assignments), "pdfAdditions": pdf_additions,
              "reviewIssues": [
 {"id":"cerebellar-exam", "sectionIds":["dizziness-exam","dizziness-note"], "text":"소뇌기능검사: 한 문서는 검사 항목을 제시하고 다른 문서는 생략 가능 메모를 포함. 양쪽 원문 보존, 우선순위 미결정."},
 {"id":"stroke-timing", "sectionIds":["stroke-note"], "text":"원문의 3시간 기준 인계 메모를 그대로 보존. 현재 임상 기준으로 검증한 내용이 아님."},
 {"id":"abbreviations", "sectionIds":["abd-history","nr-history","peds-history"], "text":"FUND HIS, FCCSR, ANVCD 등은 원문 약어로 유지. 확실하지 않은 풀이는 추가하지 않음."},
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
