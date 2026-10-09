# ER 초진 Quick Reference

응급실 초진 중 문진·신체진찰과 핵심 감별을 확인하는 정적 PWA입니다.

**[앱 열기](https://moonflute.github.io/ER_note/)**

## 구성

- 홈: `성인 → 소아 → 정신`. 자료가 있는 CC만 표시합니다.
- 상세: `문진 | 개념 | Flow`. 문진은 `Hx → PEx → 참고사항`, 개념은 기존 핵심 감별·Hx/PEx 설명, Flow는 주제별 초기 평가의 분기 흐름입니다. 성인 발열은 `개념 | Flow`입니다.
- 현재 38개 항목을 제공합니다. 원문 자료가 있는 37개 항목과 개념만 추가한 성인 발열이며, 소아는 성인과 분리합니다.
- 38개 주제 모두 Flow에서 `해당 양상 → 추가 Hx/PEx → 의심 질환`을 표시합니다. 각 CC의 기존 개념 설명은 그대로 유지합니다.
- 작은 글자와 간결한 버튼, 흰 배경과 빨강 강조를 사용합니다.
- 간략 보기 선택은 브라우저에 저장합니다. 체크 상태는 새로고침 전까지 유지하며, 탭을 바꿔도 체크와 각 탭의 스크롤 위치를 유지합니다.
- 앱과 자료는 서비스 워커로 캐시합니다. 정적 자료는 네트워크 우선, 연결 실패 시 캐시를 사용합니다.

## 데이터

UI·체크 상태와 분리된 JSON이므로 다른 앱에서도 재사용할 수 있습니다.

| 파일 | 내용 |
| --- | --- |
| `data/chief-complaints.json` | CC·분류·원문 보존 계층·화면용 `layout` |
| `data/cc-concepts.json` | CC별 감별·Hx/PEx 의미·Flow·주의점·외부 근거 |
| `data/content-provenance.json` | 원본 해시·문단·원문 항목 대응표 |
| `docs/chief-complaints.schema.json` | 문진 데이터 스키마 |
| `docs/cc-concepts.schema.json` | 개념 데이터 스키마 |

문진은 원본 6개 자료의 600개 항목을 보존합니다. 중복 정리·순서 변경은 `layout`에서만 하며, 모든 원문 항목을 `sourceItemIds`로 연결합니다. 참고사항도 문진 탭 뒤에 항상 표시합니다.

개념은 별도 요청에 따라 작성한 외부 근거 기반 설명입니다. Tintinalli의 출판사 제공 본문과 SAEM·NICE·AHA·EAU·RCH 등 공식 자료를 대조했습니다. 각 문장에 `sourceIds`, 근거 자료에 판/절·URL·확인일·본문 접근 범위를 기록합니다. 개념 작성으로 기존 체크리스트를 늘리거나 줄이지 않습니다.

성인 발열은 `전신증상`에 별도로 추가했습니다. 제공 원문에는 소아 발열 문진만 있어 성인 문진을 만들지 않고 `conceptOnly`로 관리합니다. [성인 발열 열기](https://moonflute.github.io/ER_note/#cc/adult-fever).

- [편집 기준](docs/편집%20기준.md)
- [개념 자료와 근거](docs/개념%20자료.md)
- [전체 CC 개념 검토 기록](docs/개념%20검토.md)
- [전체 CC Flow 검토 기록](docs/전체%20Flow%20검토.md)
- [문진 자료 정리본](docs/자료%20정리본.md)
- `docs/content-audit.json`: 원문 보존 검사 결과

## 로컬 실행

빌드·npm 의존성 없이 정적 HTTP 서버를 사용합니다.

```shell
python -m http.server 4173 --bind 127.0.0.1
```

JSON을 fetch하므로 `file://`로 직접 열 수 없습니다.

## 편집·검증

원본은 로컬 `문진항목 정리/`에 보존하고 Git·Pages에서 제외합니다. 문진 재정리는 `scripts/curate_data.py`의 명시적 대응표를 사용합니다. 개념은 별도 JSON에서 수정합니다.

```shell
python scripts/curate_data.py
python scripts/validate_data.py
python scripts/validate_concepts.py
node --check app.js
node --check sw.js
git diff --check
```

검증기는 원문 보존·전체 CC의 개념 및 Flow 연결·소아/성인 범위·근거 연결·문구 길이·주제별 검토 기록을 확인합니다. 임상 내용의 정확성은 근거 본문과 직접 대조해야 합니다.

## 배포

[Moonflute/ER_note](https://github.com/Moonflute/ER_note)의 `main`에 푸시하면 GitHub Actions가 Pages에 배포합니다. 상대 경로·hash routing으로 `/ER_note/` 하위 경로에서 동작합니다.

[배포 안내](docs/deployment.md). 사용자의 요청에 따라 브라우저 검증과 배포 상태 조회는 하지 않습니다.
