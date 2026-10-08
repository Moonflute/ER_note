# GitHub Pages 배포

- 저장소: [Moonflute/ER_note](https://github.com/Moonflute/ER_note)
- 배포 주소: [ER note](https://moonflute.github.io/ER_note/)
- `main` 푸시 시 `.github/workflows/pages.yml` 실행

## 배포 범위

워크플로가 다음 파일만 `_site`에 복사합니다.

- `index.html`, `styles.css`, `app.js`, `sw.js`, `.nojekyll`, `manifest.webmanifest`
- `data/chief-complaints.json`, `data/cc-concepts.json`
- `assets/icons/`의 앱 아이콘

원본 문서·작업 파일·검수 자료는 배포하지 않습니다. URL은 상대 경로와 hash routing을 사용합니다.

## 작업 기준

원문 보존·개념 자료 검증과 JavaScript 구문 검사를 통과한 변경을 `main`에 커밋·푸시합니다. 사용자가 직접 확인하므로 별도 요청이 없으면 브라우저 검증·GitHub Pages 상태 조회는 하지 않습니다.

앱/스타일/개념 자료를 바꾸면 `index.html`, `app.js`, `sw.js`의 해당 버전을 함께 갱신합니다. 서비스 워커는 앱과 두 데이터 파일을 캐시합니다.

## 최초 설정

저장소 **Settings → Pages → Build and deployment → Source**를 **GitHub Actions**로 설정합니다. 이후 `main` 변경으로 배포됩니다.
