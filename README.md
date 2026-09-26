# ER 초진 Quick Reference

응급실 초진 중 증상별 문진과 신체진찰 항목을 빠르게 확인하는 정적 웹앱입니다.

**[베타 앱 열기](https://moonflute.github.io/ER_note/)**

## 베타 구성

- 증상 검색: 한글, 영어, 약어
- 주요 CC 8개와 00–11 분류 목록
- 문진과 신체진찰을 상세 본문에 표시
- 인계 메모와 차팅 예시는 본문 뒤 참고 영역
- 소아·정신과 자료 범위 표시, 원문이 없는 CC는 자료 없음 표시
- 체크 상태는 현재 탭에서만 유지되며 새로고침 시 초기화됨. 환자 정보나 체크 상태를 저장하지 않음

## 데이터와 출처

`data/chief-complaints.json`이 앱과 다른 프로젝트에서 공유할 수 있는 데이터입니다. HTML, 화면 상태, 체크 상태를 포함하지 않습니다.

```text
categories  분류 코드와 표시 순서
complaints  CC 식별자, 검색 별칭, 범위, 연결된 section ID
sections    문진·신체진찰·메모·예시 항목
```

각 항목은 안정적인 `id`와 원문 `text`를 가집니다. 원문 조건이 필요한 경우 `condition`을 따로 둡니다. 여러 CC가 동일한 공통 문진을 `sectionId`로 참조할 수 있습니다.

- [자료 정리본](docs/자료%20정리본.md): 분류별 검토용 문서
- `data/content-provenance.json`: 원본 파일 해시, 원문 텍스트, 문단 위치, 정리 항목 대응표
- `docs/content-audit.json`: 보존 검사 및 자료가 없는 CC 목록
- `docs/chief-complaints.schema.json`: 다른 프로젝트에서 재사용할 때 참고할 JSON Schema

원본 5개 파일의 문진·진찰·메모·예시를 보존했습니다. 같은 구획에서 공백 또는 앞쪽 bullet만 다른 중복만 통합합니다. 차팅 예시의 반복 소견은 사례 순서를 위해 통합하지 않습니다. 비슷하지만 조건·범위가 다른 항목은 각각 유지합니다. 원문 약어, 수치와 인계 내용을 임의로 교정하거나 새 의학 내용을 보충하지 않았습니다.

베타 데이터는 인계 자료를 정리한 것으로, 최신 진료 지침이나 병원 내부 오더의 적합성을 검증한 결과는 아닙니다. 원문 간 상충 내용은 `content-provenance.json`의 `reviewIssues`에 기록합니다.

## 로컬 실행

빌드·npm 의존성이 없습니다. 프로젝트 폴더에서 정적 HTTP 서버를 실행합니다.

```shell
python -m http.server 4173 --bind 127.0.0.1
```

브라우저에서 `http://127.0.0.1:4173/`를 엽니다. JSON을 fetch하므로 `file://` 직접 열기 대신 HTTP 서버를 사용합니다.

## 자료 재정리

원본은 로컬 `문진항목 정리/` 폴더에 보존하며 Git과 Pages 배포에서 제외합니다. 추출에는 `lxml`, `pdfplumber`, PDF 렌더링 런타임이 필요합니다. 재정리 과정의 핵심은 `scripts/curate_data.py`의 명시적인 원문 위치 대응표입니다.

```shell
python scripts/extract_sources.py
python scripts/curate_data.py
python scripts/validate_data.py
```

배포 전 검증은 Python 표준 라이브러리만 사용합니다. 원본이 로컬에 있으면 해시까지 확인하고, CI에서는 보존된 원문·대응표와 결과 데이터의 일치 여부를 확인합니다.

## GitHub Pages

저장소: [Moonflute/ER_note](https://github.com/Moonflute/ER_note)

배포 방법과 상태 확인은 [배포 안내](docs/deployment.md)를 참고합니다. 앱의 URL·파일 경로는 상대 경로와 hash routing을 사용해 GitHub Pages의 `/ER_note/` 하위 경로에서도 동작합니다.
