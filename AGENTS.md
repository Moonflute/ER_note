# Project instructions

Before changing clinical content or detail-page UI, read `docs/편집 기준.md`.

- Review the original files in `문진항목 정리/` one at a time.
- Never add or remove clinical content without a source. Deduplicate and reorder only through a complaint `layout`, with complete `sourceItemIds` coverage.
- Detail pages use `Hx`, `PEx`, then always-visible `참고사항`.
- Do not show blank paper answer slots in curated text.
- Keep the interface dense for one-handed ER use.
- Run the repository validators before pushing.
- Push requested changes to `main`. Do not run browser checks or poll GitHub Pages unless the user explicitly asks.
