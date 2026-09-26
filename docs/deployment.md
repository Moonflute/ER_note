# GitHub Pages 배포

- 저장소: https://github.com/Moonflute/ER_note
- 배포 주소: https://moonflute.github.io/ER_note/
- 배포 대상: `index.html`, `styles.css`, `app.js`, `.nojekyll`, `data/chief-complaints.json`, `data/content-provenance.json`

2026-09-26 최초 베타 배포 완료. [배포 실행](https://github.com/Moonflute/ER_note/actions/runs/36239432218)에서 검증·build·deploy 성공을 확인했고 공개 사이트의 검색과 원문 출처 보기까지 브라우저에서 확인했다.

## 최초 설정

저장소 **Settings → Pages → Build and deployment → Source**를 **GitHub Actions**로 설정한다.

`main` 브랜치에 변경 사항이 반영되면 `.github/workflows/pages.yml`이 정적 파일을 배포한다. 최초 설정 뒤 자동 실행이 없으면 **Actions → Deploy ER Quick Reference to GitHub Pages → Run workflow**로 실행한다.

## 배포 확인

1. 해당 커밋의 Actions 실행에서 `build`와 `deploy`가 성공했는지 확인한다.
2. 배포 주소에서 증상 목록, 한글·영어·약어 검색, 상세 문진과 신체진찰, 뒤쪽 차팅 참고를 확인한다.
3. 저장소 경로 `/ER_note/` 아래에서 CSS·JavaScript·JSON이 정상적으로 로드되는지 확인한다.

## 파일 범위

원본 문서와 작업 중간 파일은 `.gitignore`로 제외한다. 배포 워크플로는 명시된 앱 파일만 `_site`에 복사하므로 원본 문서, 정리 스크립트, 검수 자료는 사이트에 올라가지 않는다.

앱에서는 상대 경로로 정적 데이터에 접근한다. 별도 서버, 환경 변수, npm 설치, 번들러가 필요하지 않다.
