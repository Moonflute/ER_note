"""Extract immutable source text and locations; never edit source documents."""
from pathlib import Path
import hashlib
import json
import zipfile
from lxml import etree
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "working" / "sources"
OUT.mkdir(parents=True, exist_ok=True)
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = "{" + NS["w"] + "}"
FILES = [
    ("handover", "2023.10 B구역 인계의 사본의 사본.docx"),
    ("np-docx", "NP 인턴초진.docx"),
    ("np-pdf", "NP 인턴초진.pdf"),
    ("templates", "와꾸모음 2020ver. ~이거 뽑으시면 됩니다~.docx"),
    ("all", "초진 all.docx"),
]

def paragraph_text(p):
    parts = []
    for node in p.iter():
        if node.tag in (W + "t", W + "delText"):
            parts.append(node.text or "")
        elif node.tag == W + "tab":
            parts.append("\t")
        elif node.tag in (W + "br", W + "cr"):
            parts.append("\n")
    return "".join(parts)

sources = []
for sid, filename in FILES:
    path = ROOT / "문진항목 정리" / filename
    source = {"id": sid, "file": "문진항목 정리/" + filename,
              "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "blocks": []}
    if path.suffix == ".docx":
        with zipfile.ZipFile(path) as z:
            source["media"] = [n for n in z.namelist() if n.startswith("word/media/")]
            source["parts"] = []
            for name in z.namelist():
                if not name.startswith("word/") or not name.endswith(".xml"):
                    continue
                root = etree.fromstring(z.read(name))
                paragraphs = root.findall(".//w:p", NS)
                if not paragraphs:
                    continue
                source["parts"].append(name)
                for number, p in enumerate(paragraphs, 1):
                    # Textbox paragraphs have their own stable source location.
                    if p.findall(".//w:p", NS):
                        continue
                    text = paragraph_text(p)
                    if not text.strip():
                        continue
                    style = p.find("w:pPr/w:pStyle", NS)
                    num = p.find("w:pPr/w:numPr", NS)
                    bid = f"{sid}:{Path(name).stem}:p{number}"
                    source["blocks"].append({"id": bid, "part": name,
                        "paragraph": number, "style": style.get(W+"val") if style is not None else None,
                        "numbered": num is not None, "inTable": bool(p.xpath("ancestor::w:tc", namespaces=NS)),
                        "text": text})
            source["trackedChanges"] = len(etree.fromstring(z.read("word/document.xml")).xpath(".//w:ins | .//w:del", namespaces=NS))
    else:
        with pdfplumber.open(path) as pdf:
            source["pages"] = len(pdf.pages)
            for number, page in enumerate(pdf.pages, 1):
                text = page.extract_text(layout=False) or ""
                source["blocks"].append({"id": f"{sid}:page{number}", "page": number, "text": text})
                page.to_image(resolution=110).save(OUT / f"{sid}-page-{number}.png")
    (OUT / f"{sid}.txt").write_text("\n\n".join(f'[{b["id"]}] {b["text"]}' for b in source["blocks"]), encoding="utf-8")
    sources.append(source)
(OUT / "source-extracts.json").write_text(json.dumps({"sources": sources}, ensure_ascii=False, indent=2), encoding="utf-8")
for s in sources:
    print(s["id"], len(s["blocks"]), "blocks", sum(len(b["text"]) for b in s["blocks"]), "chars", len(s.get("media", [])), "images", s.get("trackedChanges", 0), "tracked changes")
