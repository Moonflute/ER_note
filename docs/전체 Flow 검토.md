# 전체 CC Flow 검토

검토일: 2026-10-10 · 데이터 버전: `2026-10-10.1`

홈에서 제공하는 38개 주제 모두에 Flow를 연결했다. 신규 35개를 주제별로 작성하고 기존 두통·어지럼·성인 발열의 3개 흐름을 보존했다.

기존 개념의 감별·Hx·PEx·주의 문구와 문진 원문/layout은 변경하지 않았다. Flow는 질문에서 시작해 답에 해당하는 진찰·결과와 우선 의심 질환을 연결한다. 분과 문진도 해당 분과의 초기 평가 흐름으로 구성했다.

## 검토 기준

- 주제별 기존 개념과 연결된 문진의 증상 특이 Hx/PEx를 대조한다.
- 위험 갈래를 앞에 두고, 정상 소견의 배제 한계·검사 적용 조건을 필요한 갈래에 남긴다.
- 기존 개념의 모든 감별·Hx/PEx를 `conceptRefs`로 연결하고 기존 인용을 보존한다.
- 신규 문장의 근거 본문은 공식 지침·매뉴얼·교재 출판사 공개 범위에서 확인한다. 유료 전체 본문을 읽은 것으로 표시하지 않는다.
- 성인/소아/정신 범위를 유지한다. 임상 핵심을 글자 수 때문에 삭제하지 않고 500자 초과 사유를 따로 기록한다.

개념의 이전 임상 검토는 [개념 검토](개념%20검토.md), 자료의 URL·판/절·접근 범위는 [개념 자료](개념%20자료.md)에 기록한다. 아래 근거 ID는 JSON의 source 기록과 대응한다.

## 주제별 결과

| CC ID | 이름·범위 | 시작 질문 | 검토 내용 | Flow 표시 글자 수 | 이번 대조 근거 ID |
| --- | --- | --- | --- | ---: | --- |
| `abdominal-pain` <!-- flow-review: abdominal-pain --> | 복통 · 성인/일반 | 통증 위치·이동/방사? → 구토·배변/가스·요로증상 → LMP·수술력 | 통증 위치·이동/방사에서 시작해 관류·복막 위험, 임신, 위치별 압통/Murphy, 폐색과 CVAT를 분기. 원문 복부수술력·ANVCD·FUND HIS·임신 문진을 대조했고 단독 음성 진찰과 초기/고령/면역저하 한계를 보존. | 517 | `aci-abd`, `msd-acute-abd`, `msd-cholecystitis`, `msd-cholangitis`, `msd-gi-exam`, `eau-stones`, `eau-infections`, `tint-appendix-signs`, `tint-abd`, `wses-cholecystitis` |
| `constipation` <!-- flow-review: constipation --> | 변비 · 성인/일반 | Last defecation·flatus? → 평소와 다른지·구토/팽만 → 약물·수술·내시경력 | 원문 Last defecation/flatus·최근 내시경·배변 습관 변화 질문에서 시작. 폐색 위험을 앞에 두고 매복의 overflow 설사, DRE의 굳은 변/혈액/종괴와 약물성·기질성 분기를 분리. | 267 | `msd-constipation` |
| `chest-pain` <!-- flow-review: chest-pain --> | 흉통 · 성인/일반 | 언제·얼마나, 어디로 방사? → 운동/호흡/자세·구토 연관 → 동반 증상·U/D | 원문 onset/character/duration/radiation/factors/associated 질문 순서와 대조. 관류 이상 뒤 ACS·박리·PE·기흉·구토 후 식도파열을 구분하고 심낭염/흉벽 압통을 추가. 정상 청진·양측 BP·압통 재현의 배제 한계를 보존. | 479 | `tint-chest`, `aci-chest`, `tint-pneumothorax`, `aha-chest-exam`, `tint-acs` |
| `syncope` <!-- flow-review: syncope --> | 실신 · 성인/일반 | 전조·자세/운동 중? → 목격 당시 움직임·회복 뒤 혼돈 → 심질환·약물·가족력 | 전조·발생 자세와 운동·사건 당시/현재 증상 비교를 먼저 확인. 목격자 정보와 회복 양상으로 경련을, ECG/불규칙맥/AS 잡음으로 심장 위험을 연결. 기립성 변화와 짧은 jerk가 다른 원인의 배제를 뜻하지 않음을 유지. | 308 | `nice-syncope`, `tint-syncope`, `aha-chest-exam` |
| `cardiac-arrest` <!-- flow-review: cardiac-arrest --> | 심정지 / DOA · 성인/일반 | 목격·발생 시각·CPR/초기 리듬? → 반응·호흡·맥박을 소생과 동시에 확인 | Incoming CPR/DOA와 무맥 원문을 AHA 2025 BLS·ALS 본문 및 Figure 2 accessible algorithm에 대조. 질문은 목격/이송자에게 소생과 병행하도록 표시하고 10초 맥박 확인, VF/pVT와 비충격 리듬, Hs/Ts 원인군과 POCUS 지연 금지를 유지. 정식 ACLS 전체 약물·순서를 대체하는 프로토콜로 만들지 않음. | 391 | `aha-arrest`, `aha-bls`, `tint-pneumothorax` |
| `hematuria` <!-- flow-review: hematuria --> | 혈뇨 · 성인/일반 | 진짜 소변 피·혈괴·기간? → 통증/발열·FUND HIS·줄기 → 흡연·항응고제 | Hematuria의 실제 요로 출혈·기간/혈괴와 FUND HIS/좁은 줄기를 대조. 혈괴 요폐를 먼저 두고 감염·산통 결석·부종/BP/단백뇨/RBC cast의 사구체성·무통 종양 단서를 나눔. 항응고제만으로 혈뇨를 설명하지 않는 한계를 유지. | 293 | `msd-hematuria`, `eau-infections`, `aci-retention` |
| `urinary-symptoms` <!-- flow-review: urinary-symptoms --> | 배뇨이상 · 성인/일반 | FUND HIS: 급한 요의/통증인가, 배출이 힘든가? → 혈뇨·실금·줄기 | FUND HIS 저장/배출 증상부터 혈뇨·실금·줄기를 연결. 요폐/PVR·CES 신경 소견·전신 UTI 위험을 앞에 두고 분비물/성접촉력의 요도염과 전립선 DRE 양성 소견을 구분. 빈뇨/배뇨 가능에도 overflow 요폐가 가능하며 전립선 마사지 금지를 보존. | 345 | `eau-infections`, `aci-retention` |
| `incontinence` <!-- flow-review: incontinence --> | 요실금 · 성인/일반 | 언제 새나: 요의 직후, 기침/운동 때, 계속 조금씩? → 새 변화·FUND HIS | 원문 누출·FUND HIS·줄기의 시점을 먼저 묻고 새 허리/하지·회음부 이상은 CES로 연결. 절박·복압·범람을 구분하며 충만 방광 기침검사에서 즉시 누출 의미/빈 방광 음성 한계와 PVR에 의한 동반 요폐 확인을 보존. | 329 | `msd-incontinence`, `aci-retention` |
| `flank-pain` <!-- flow-review: flank-pain --> | 옆구리 통 · 성인/일반 | 언제·산통/지속통·서혜부 방사? → 발열·배뇨증상·소변량·단일신 | 원문은 요로결석 오더/증상 조절 참고 자료이므로 원문 질문을 보충하지 않고 개념 설명으로 작성. EAU의 발열/무뇨·단일신·불확실 진단 영상 우선과 감염성 폐색 배액 평가를 보존. 원문 RUA 확인 후 CT·고령 D-dimer 등 병원 오더를 일반 지침으로 승격하지 않음. AF/지속통 신경색과 AAA 대체 원인을 별도 분기. | 331 | `eau-stones`, `msd-hematuria`, `eau-infections`, `aci-abd`, `msd-renal-occlusion` |
| `testicular` <!-- flow-review: testicular --> | 고환 이상 · 성인/일반 | 갑자기인가·한쪽인가? → 구토·배뇨통/발열·서혜 종괴 → 양측 고환 진찰 | 고환 이상/염전 의심 및 cremasteric 원문을 대조해 급작 편측 통증/구토→고위·가로/반사 소견을 우선 연결. 감돈 탈장·Fournier 피부/전신 위험과 서서히 진행하는 부고환 감염을 구분. 반사 보존/Prehn sign 한계 및 검사 대기로 수술 평가 지연 금지를 유지. | 294 | `aci-scrotum` |
| `joint-pain` <!-- flow-review: joint-pain --> | 관절 문제 · 성인/일반 | 언제부터·외상/시술 후인가? → 통증 위치·부종 → Active/Passive ROM | 급성 관절 염증은 감염을 먼저 평가하고 결정성·외상·관절주위 병변을 ROM/압통 위치로 분기. 관절액 결정과 정상 CRP의 배제 한계를 보존. | 305 | `sanjo`, `aci-msk`, `msd-joint-exam`, `tint-joints` |
| `back-pain` <!-- flow-review: back-pain --> | 허리 통증 · 성인/일반 | 언제부터·다리로 방사? → 배뇨/배변·회음부 변화 → 시술·발열·외상/암 Hx | 시술/침, 배뇨·회음부 변화, 외상/암 병력을 앞에서 묻고 CES/감염·혈종/골절·종양과 근육·신경근성을 분리. SLR 양성과 crossed SLR 의미 보존. | 401 | `aci-back`, `msd-radiculopathy` |
| `rash` <!-- flow-review: rash --> | 피부 발진 · 성인/일반 | 언제·얼마나 빨리 퍼졌나? → 새 약물/노출 → 가려움 vs 통증·호흡/실신 | 피부 모양 이전에 급성 노출·진행 속도·통증·호흡/실신을 묻고 아나필락시스, SJS/TEN, NSTI, 자반성 감염을 분리. 기존 병원 약제/연락 지시는 일반 알고리즘으로 사용하지 않음. | 359 | `msd-sjs`, `msd-anaphylaxis`, `idsa-skin`, `nice-meningitis` |
| `dizziness` <!-- flow-review: dizziness --> | 어지럼 · 성인/일반 | TRS? → Duration·유발 상황 → Ear/Neuro Sx → 안진·보행 | TRS 출발 유지. 지속/자세 유발/기타 발작을 나누고 안진·보행 결과 연결. HINTS는 지속 AVS+자발안진의 숙련자 조건, TRS·Romberg의 배제 한계 보존. | 580 | `grace3`, `aci-vertigo`, `aao-bppv`, `msd-sensation` |
| `headache` <!-- flow-review: headache --> | 두통 · 성인/일반 | 최대 강도까지 얼마나 빨리? · 처음/평소와 다른 두통? | 발병 속도·양상 변화에서 위험 분기를 먼저 확인하고 반복 일차성 양상으로 진행. 경부강직/근육 압통·눈/측두동맥 소견과 음성 한계를 유지. | 393 | `aci-headache`, `msd-headache-exam`, `nice-meningitis` |
| `seizure` <!-- flow-review: seizure --> | 경련 · 성인/일반 | 목격자: 전신/한쪽? 몇 분·반복? 회복? → 복약·Last alcohol | 목격 양상·시간·회복부터 시작해 5분 지속/회복 없는 반복, 비경련성 status, 국소 병변, 실신, 복약 누락·금단을 분리. 새 편측 약화를 Todd로 단정하지 않는다. | 420 | `msd-seizures`, `nice-epilepsy`, `nice-status`, `nice-syncope`, `tint-seizures` |
| `mental-change` <!-- flow-review: mental-change --> | 의식장애 · 성인/일반 | 보호자: 마지막 정상은? 경련·외상·약물/음주·발열? → 의식·호흡 | 보호자의 마지막 정상·노출 병력에서 ABC/혈당과 국소 소견으로 연결. 축동의 opioid/교뇌 감별, 운동반응 비대칭과 Babinski의 의미, 감염·발작 후 상태를 보존. | 401 | `aci-unconscious`, `msd-coma`, `msd-reflexes`, `msd-seizures`, `tint-seizures` |
| `stroke` <!-- flow-review: stroke --> | 뇌졸중 · 성인/일반 | Last normal / First abnormal? → 갑작스러운 결손·기존 기능·항응고제 | Last normal/First abnormal·기상 시 발견에서 시작. 새 Face/Motor 결손으로 허혈을 단정하지 않고 영상으로 허혈/출혈 감별. 언어/구음·후순환·의식 소견, 회복된 TIA, 저혈당/발작 후 mimic을 각각 연결. | 450 | `aci-stroke`, `grace3`, `msd-coma`, `msd-stroke-signs`, `nice-epilepsy` |
| `psychiatry-interview` <!-- flow-review: psychiatry-interview --> | 정신과 문진 · 정신 | 오늘 달라진 점? → 자살 생각·계획·시도 → 급성 변화·복약·물질 | 오늘의 변화와 자살 생각/계획/시도에서 시작. 안전·섬망/신체원인을 앞에 두고 우울·조증·공황·정신병적 상태로 연결하며 점수로 안전/퇴원을 판단하지 않는다. | 431 | `aci-behaviour`, `nice-bipolar`, `nice-delirium`, `nice-depression`, `nice-panic`, `nice-panic-flow`, `nice-self-harm` |
| `obgyn-interview` <!-- flow-review: obgyn-interview --> | 산부인과 문진 · 성인/일반 | 출혈량·분비물 변화? → LMP·Last coitus·통증 양상 → Previous gynecologic care | 출혈량·분비물, LMP/주기/Last coitus, 기존 산부 진료 문진부터 시작. 임신 검사/쇼크·복막자극과 편측 갑작 통증의 염전을 먼저 분기. 질경 출혈/분비물 관찰과 양손 CMT/부속기 압통 목적을 구분하고 CMT 단독 확정·정상 진찰 배제 한계를 유지. | 346 | `msd-pelvic`, `cdc-pid` |
| `pregnancy` <!-- flow-review: pregnancy --> | 산전 진찰 · 성인/일반 | 정확한 주수·진통 주기/지속? → 출혈/물 같은 유출 → Op Hx·동반 증상 | IUP 주수/일·수축 주기/지속·출혈/분비물·Op Hx 원문을 대조. 초기 임신 응급, 후반기 통증/무통 출혈과 은폐 출혈, ≥20주 고혈압/두통·시각/RUQ·clonus를 우선 연결. 규칙 수축/경부 변화 및 질경 양수 pooling·음성 추가 평가를 분리. 전치태반 배제 전 digital 경부진찰 금지를 보존. | 385 | `nice-preterm`, `msd-pregnancy-bleeding`, `msd-pelvic`, `nice-pregnancy-htn` |
| `peds-common` <!-- flow-review: peds-common --> | 소아과 문진 · 소아 | 몇 개월·미숙/출생 문제? → 평소 대비 수유·활동·소변·반응 | 연령·미숙/출생력 및 수유/활동/소변의 평소 대비 변화로 시작. 무열 중증 감염, CNS 경고, 심장·외과·대사 응급, 탈수·호흡기 소견을 구체적으로 연결. | 358 | `nice-meningitis`, `rch-abd`, `rch-cough`, `rch-dehydration`, `rch-infant` |
| `fever` <!-- flow-review: fever --> | 발열 · 소아 | Tmax·언제부터? → 교정연령·접종 → 반응·수유·소변 | Tmax/기간→교정연령/접종→반응/수유/소변 순서. 신생아 발열과 관류/CNS 위험을 우선하고 폐·TM/uvula·초점 없는 UTI·가와사키 분기를 보존. RCH 최신 가와사키 기준은 특징 동반 4일부터 판단 가능. | 468 | `msd-throat`, `nice-meningitis`, `rch-cough`, `rch-fever`, `rch-infant`, `rch-kawasaki`, `rch-otitis` |
| `vomiting` <!-- flow-review: vomiting --> | 오심 구토 · 소아 | 구토 색·분출성·횟수? → 수유·소변·설사·두통·연령 | 색/양상/횟수에서 담즙성 폐색·CNS 위험·탈수로 연결. 간헐적 장중첩, 영아 분출성 유문협착, 설사 동반 위장염을 구분하고 혈변/종괴/장음의 배제 한계를 보존. | 388 | `nice-meningitis`, `rch-abd`, `rch-dehydration`, `rch-ge`, `rch-infant`, `rch-intussusception`, `rch-pyloric`, `rch-vomiting` |
| `diarrhea` <!-- flow-review: diarrhea --> | 설사 · 소아 | 횟수·혈액/점액·색? → 통증 양상·섭취·손실·마지막 소변 | 변 양상·통증·섭취/손실·소변에서 시작. 탈수/쇼크와 간헐적 장중첩을 앞에 두고 혈변/점액 염증과 급성 위장염을 연결. 설사만으로 외과 원인을 배제하지 않음. | 295 | `rch-abd`, `rch-dehydration`, `rch-ge`, `rch-intussusception` |
| `cough` <!-- flow-review: cough --> | 기침 · 소아 | Barking·쉰 목소리? 갑자기/choking? → 연령·atopy·호흡 노력 | 기침 소리/쉰 목소리와 갑작스러운 choking에서 시작. 호흡 노력·silent chest를 먼저 보고 stridor/croup, 반복 wheeze·영아 세기관지염, 국소 폐렴, 편측 이물 소견을 연결. | 439 | `rch-asthma`, `rch-cough`, `rch-fb`, `rch-infant` |
| `peds-abdominal-pain` <!-- flow-review: peds-abdominal-pain --> | 복통 · 소아 | 어디가 아프고 지속/간헐적? → 배변·구토·소변·연령 | 위치·지속/간헐·배변·구토/소변에서 충수·장중첩·생식기 응급으로 연결. RLQ/rTd, Rovsing과 Psoas/Obturator의 실제 유발 방향을 보존하고 장염/변비·폐렴/UTI 및 반복 진찰에 연결. | 422 | `msd-appendicitis`, `rch-abd`, `rch-ge`, `rch-intussusception`, `tint-appendix-signs` |
| `peds-seizure` <!-- flow-review: peds-seizure --> | 경련 · 소아 | LOC·한쪽/EBD·몇 분? → 발열·연령·과거 발작·회복/재발 | 발작 목격/시간·발열/연령·과거력·회복/재발 순서. 5분 지속과 회복 없는 반복에 대응하고 CNS 감염·대사 원인을 먼저 본 뒤 단순 열성경련 4조건·복잡 양상·무열 뇌전증으로 연결. 열성경련 연령 범위는 RCH 기준. | 497 | `msd-seizures`, `nice-meningitis`, `nice-status`, `rch-febrile-seizure`, `rch-infant` |
| `eye` <!-- flow-review: eye --> | 눈 이상 · 성인/일반 | 언제·Pain/Photophobia/Vision? → 외상·렌즈·OT HX → 양안 시력/시야·동공 | 화학·관통 손상의 즉시 조치, 무통 시력저하의 혈관/망막 경로, 녹내장·안와 감염/포착·안내염, 각막/포도막/결막 경로를 구분. RAPD·동공·각막·EOM 소견과 화학/관통 예외를 보존. | 636 | `aci-eye`, `tint-eye`, `msd-retina`, `msd-retinal-artery`, `msd-glaucoma`, `msd-eye-exam`, `msd-eye-pain` |
| `throat` <!-- flow-review: throat --> | 인후통 / 연하곤란 · 성인/일반 | 섭취 직후 시작? → 침 삼킴·호흡 → 편측 통증·목소리·목 부종 | 섭취 상황, 침 삼킴·호흡, 편측 통증/목소리로 출발. 무리한 인두 진찰 예외, 보이지 않는 식도 이물/완전 폐쇄, PTA와 심부 감염을 구분. | 354 | `msd-throat`, `msd-fb` |
| `ear` <!-- flow-review: ear --> | 귀 이상 · 성인/일반 | 언제부터·Hearing loss? → URI·물/외상 → 외이도·TM·음차 | 급성 난청을 먼저 묻고 감각신경성/전음성의 Weber·Rinne 방향을 명시. Tragus/외이도, TM 팽륜/삼출, mastoid 부종·귀 돌출 소견과 음차 한계 보존. | 347 | `aao-hearing`, `msd-ear`, `msd-hearing-exam` |
| `epistaxis` <!-- flow-review: epistaxis --> | 코 이상 · 성인/일반 | 언제·어느 쪽 먼저·지금도 출혈? → 양/재발·외상 → Warfarin/Aspirin | 출혈 시작 측·시간·양·지속 여부를 먼저 확인하고 순환 상태, 출혈점/인두 유출, 비중격 혈종, 항혈전·국소 병변으로 분기. 오래된 BP 160·약제 지시는 사용하지 않음. | 383 | `tint-nose`, `msd-epistaxis`, `msd-nasal-fracture` |
| `oral-dental` <!-- flow-review: oral-dental --> | 구강·치아 · 성인/일반 | 어느 치아·온도/저작통인가, 외상인가? → 삼킴·입벌림 → 구강/교합 | 온도/저작통과 외상 기전을 먼저 구분하고 구강저 경결·혀 상승/분비물, 치아 타진·파동성 농양, 소실 파편·교합의 의미를 연결. | 350 | `aci-dental`, `tint-dental`, `msd-dental-exam` |
| `trauma` <!-- flow-review: trauma --> | 상처 외상 · 성인/일반 | 언제·무엇에/어떻게 다쳤나? → LOC·음주 → 흉복부 통증·상처·원위 변화 | 수상 시각/기전·물체·LOC/음주를 묻고 전신 손상→구획/개방/건·신경·혈관→깊이/이물 순으로 연결. 뼈 미노출 개방성, 보존 맥박·부분 건 손상, 마취 전 감각과 미확인 LOM/neck level 보존. | 443 | `aci-trauma`, `tint-tendon`, `boa-compartment`, `msd-compartment`, `aci-msk`, `tint-wound`, `msd-fractures` |
| `head-trauma` <!-- flow-review: head-trauma --> | 두부외상 · 성인/일반 | 기전·LOC/기억장애·구토·두통 악화? → 나이/항응고 → GCS·동공·사지 | 기전·LOC/기억·구토/두통 경과에서 출발. GCS·동공·사지 양성 소견, 정상 GCS의 골절 영상 기준, 동반 경추와 뇌진탕을 구분. 단독 음주 또는 정상 진찰로 출혈을 배제하지 않음. | 417 | `nice-head-injury`, `msd-coma`, `aci-trauma`, `tint-head-injury` |
| `inhalation-burn` <!-- flow-review: inhalation-burn --> | 흡입화상 · 성인/일반 | 밀폐 공간·연기 노출 시간? → 기침/호흡곤란·목소리·두통/실신 | 밀폐 공간/시간과 호흡·목소리·신경 증상에서 출발. 상기도 부종, wheeze/호흡 노력, COHb/SpO₂ 한계, 심한 의식/순환 악화와 lactate/acidosis의 cyanide 단서를 분리. | 343 | `aci-burn`, `cdc-co`, `msd-smoke` |
| `poisoning` <!-- flow-review: poisoning --> | 약물중독 · 성인/일반 | 무엇·얼마나·언제·동시 복용? → 사고/자해·현재 계획 → 의식·호흡·V/S | 물질·양·시각·동시 복용·자해로 출발. 호흡/축동, 건조 vs 발한, 과다 분비/근섬유다발수축, clonus/과반사, CO SpO₂, APAP 급성 복용(<24h)·시작 시각/제형 조건 및 안전/심리사회 평가를 보존. | 592 | `tint-toxicology`, `nice-self-harm`, `msd-cholinergic`, `msd-serotonin`, `cdc-co`, `atlas-apap`, `apap-consensus-2023` |
| `adult-fever` <!-- flow-review: adult-fever --> | 발열 · 성인/일반 | Tmax·측정법·기간 → 동반 증상 → U/D·Drug·노출 → 진찰 | Tmax·기간·동반 증상에서 중증/고위험 병력, 국소 진찰, 초점 없는 발열로 연결. 체온 단독 중증도 판정·CNS 음성 소견 배제 불가 유지. | 489 | `msd-adult-fever`, `nice-adult-sepsis`, `nice-neutropenic-sepsis`, `eau-infections`, `nice-meningitis` |

## 500자 초과 Flow

글자 수에는 시작 질문·단계 제목·분기의 양상/확인/의심·주석·주의 문구가 포함된다. 실제 짧은 화면이나 글자 확대에서는 자연스러운 스크롤을 허용한다.

<!-- density: abdominal-pain -->
### 복통 · 517자

위치별 압통·Murphy·장음·CVAT의 의미와 혈관/복막·임신 위험 분기, 초기/고령 진찰 및 단독 음성 한계를 함께 보존해 500자를 초과.

<!-- density: dizziness -->
### 어지럼 · 580자

기존 Flow 보존 요청에 따라 580자를 유지한다. HINTS 적용 조건, 두 BPPV 유발검사, 보행/청력 경고와 TRS·Romberg 해석의 한계를 구분해 보존한다.

<!-- density: eye -->
### 눈 이상 · 636자

눈 이상은 화학·관통상, 망막동맥폐색/박리, 녹내장, 안와 감염/외상 후 포착, 안내염, 각막/포도막/결막의 서로 다른 응급 의미를 함께 담아야 한다. 결과와 검사 예외를 삭제하지 않고 중복을 압축함.

<!-- density: poisoning -->
### 약물중독 · 592자

중독은 6 toxidrome의 실제 동공·피부·호흡·반사 소견, CO 산소포화도 한계, APAP 무증상 지연독성·급성 복용(<24h)의 시작 시각/nomogram 조건과 시각 불명·>24h 반복/서방형 예외, 자해 안전을 함께 보여야 하므로 500자 초과를 허용한다.

## 보존·검증

- 기준 커밋 `e1ae022`와 대조해 38개 기존 개념·기존 3개 Flow·119개 기존 source 기록이 그대로임을 확인한다.
- `chief-complaints.json`, 원문 대응 자료 및 문진 layout은 그대로 유지한다. 원문에 없는 Flow 설명을 문진 체크리스트로 추가하지 않는다.
- 저장소 검증기는 제공 중인 모든 주제의 Flow·개념 대응·인용·scope·글자 수·검토 기록을 검사한다.
- Node에서 38개 경로의 별도 탭과 전체 표시 문구, 체크/스크롤 보존, 개념 로딩 실패 후 복구를 검사한다. 브라우저·Pages 배포 상태는 조회하지 않는다.
- 자동 검증은 임상적 완전성을 보증하지 않는다. 분기는 우선 감별을 위한 요약이며 확정 진단이나 배제 규칙으로 만들지 않는다.
