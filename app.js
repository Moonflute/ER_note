"use strict";

(() => {
  const main = document.querySelector("#main");
  const sourceDialog = document.querySelector("#source-dialog");
  const sourceContent = document.querySelector("#source-content");
  const frequentIds = ["chest-pain", "abdominal-pain", "dyspnea", "fever", "headache", "dizziness", "syncope", "vomiting"];
  const icons = {
    search: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" stroke="currentColor" stroke-width="1.8"/><path d="m16 16 4.5 4.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
    arrow: '<svg class="arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m9 5 7 7-7 7" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    back: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m14 5-7 7 7 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'
  };
  const state = { data: null, query: "", categoryId: "all", homeScroll: 0, route: null, currentItems: [], checked: new Map(), showSources: false, provenance: null };
  let sections;
  let complaints;
  let provenancePromise;

  const escape = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
  const normalize = (value) => String(value).normalize("NFKC").toLocaleLowerCase().replace(/[^\p{L}\p{N}]/gu, "");
  const orderedCategories = () => [...state.data.categories].sort((a, b) => Number(a.secondary) - Number(b.secondary) || a.order - b.order);
  const categoryOf = (id) => state.data.categories.find((category) => category.id === id);
  const ccUrl = (id) => `#cc/${encodeURIComponent(id)}`;
  const badge = (text, muted = false) => `<span class="badge${muted ? " muted" : ""}">${escape(text)}</span>`;

  function complaintBadges(complaint) {
    const badges = [];
    if (complaint.scope === "pediatric") badges.push(badge("소아 자료"));
    if (complaint.scope === "psychiatric") badges.push(badge("정신과 자료"));
    if (complaint.status === "missing") badges.push(badge("자료 없음", true));
    if (complaint.status === "notesOnly") badges.push(badge("인계 메모만", true));
    return badges.join("");
  }

  function complaintCard(complaint) {
    return `<a class="cc-card" href="${ccUrl(complaint.id)}"><span><span class="cc-name">${escape(complaint.name)}</span><span class="cc-meta">${complaintBadges(complaint)}</span></span>${icons.arrow}</a>`;
  }

  function footer() {
    return `<footer class="footer"><span>인계 자료 기반 · 문진 / 진찰 / 참고 자료</span><span>${escape(state.data.contentVersion)}</span></footer>`;
  }

  function renderHome() {
    document.title = "ER 초진 · Quick Reference";
    main.innerHTML = `<div class="shell home-shell">
      <header><div class="brand-row"><span class="brand">ER QUICK REFERENCE</span><span class="beta">BETA</span></div><h1>초진 문진</h1><p class="intro">증상별 문진 · 신체진찰</p></header>
      <div class="search-panel"><label class="search-box">${icons.search}<input id="cc-search" type="search" inputmode="search" autocomplete="off" autocapitalize="off" spellcheck="false" aria-label="증상 검색" placeholder="증상 검색 · 흉통, chest pain, CP" value="${escape(state.query)}"><button class="icon-button" type="button" id="clear-search" aria-label="검색어 지우기" ${state.query ? "" : "hidden"}>×</button></label><p class="search-hint">한글 · English · 약어</p></div>
      <div id="home-results"></div>${footer()}
    </div>`;
    const input = document.querySelector("#cc-search");
    input.addEventListener("input", () => {
      state.query = input.value;
      state.categoryId = "all";
      document.querySelector("#clear-search").hidden = !state.query;
      renderHomeResults();
    });
    document.querySelector("#clear-search").addEventListener("click", () => {
      state.query = "";
      input.value = "";
      document.querySelector("#clear-search").hidden = true;
      renderHomeResults();
      input.focus();
    });
    renderHomeResults();
  }

  function renderHomeResults() {
    const query = normalize(state.query);
    const indexed = state.data.complaints.map((complaint) => ({ complaint, terms: [complaint.name, ...complaint.aliases].map(normalize) }));
    const shortLatin = /^[a-z0-9]{1,4}$/.test(query);
    const hasExactMatch = shortLatin && indexed.some(({ terms }) => terms.includes(query));
    const matching = indexed.filter(({ complaint, terms }) => {
      const matchesQuery = !query || terms.some((term) => shortLatin ? (hasExactMatch ? term === query : term.startsWith(query)) : term.includes(query));
      return matchesQuery && (state.categoryId === "all" || complaint.categoryId === state.categoryId);
    }).map(({ complaint }) => complaint);
    const categories = orderedCategories();
    const prominent = !query && state.categoryId === "all" ? `<section class="frequent" aria-labelledby="frequent-title"><div class="section-heading"><h2 id="frequent-title">주요 증상</h2></div><div class="frequent-grid">${frequentIds.map((id) => complaints.get(id)).filter(Boolean).map(complaintCard).join("")}</div></section><a class="common-shortcut" href="#common"><span>공통 문진·진찰</span>${icons.arrow}</a>` : "";
    const categoryButtons = [{ id: "all", name: "전체" }, ...categories].map((category) => `<button class="filter" type="button" data-category="${escape(category.id)}" aria-pressed="${category.id === state.categoryId}">${escape(category.name)}</button>`).join("");
    const categoryCards = categories.map((category) => {
      const items = matching.filter((complaint) => complaint.categoryId === category.id).sort((a, b) => a.order - b.order);
      if (!items.length) return "";
      return `<section class="category${category.secondary ? " secondary" : ""}" aria-labelledby="category-${escape(category.id)}"><div class="category-title"><span class="category-number">${escape(category.id)}</span><h3 id="category-${escape(category.id)}">${escape(category.name)}</h3></div><div class="category-cards">${items.map(complaintCard).join("")}</div></section>`;
    }).join("");
    document.querySelector("#home-results").innerHTML = `${prominent}<section aria-labelledby="catalog-title"><div class="section-heading catalog-heading"><h2 id="catalog-title">${query ? "검색 결과" : "증상 목록"}</h2><span class="count" role="status" aria-live="polite">${matching.length}개 증상</span></div><div class="filter-list" role="group" aria-label="증상 분류">${categoryButtons}</div>${matching.length ? `<div class="category-grid">${categoryCards}</div>` : `<div class="empty-state"><h3>일치하는 증상이 없습니다</h3><p>다른 증상명이나 영어·약어로 검색해 주세요.</p></div>`}<p class="catalog-note">‘자료 없음’은 원문 문진·진찰이 아직 없는 항목입니다.</p></section>`;
  }

  function itemMarkup(item, checkable) {
    const sourceButton = `<button class="source-button" type="button" data-source-item="${escape(item.id)}" aria-label="이 항목의 원문 출처" ${state.showSources ? "" : "hidden"}>출처</button>`;
    const text = `${item.condition ? `<span class="condition">${escape(item.condition)}</span>` : ""}<span class="item-text">${escape(item.text)}</span>`;
    if (!checkable) return `<div class="item-row"><div class="reference-item">${text}</div>${sourceButton}</div>`;
    const checked = state.checked.get(state.route)?.has(item.id) ?? false;
    return `<div class="item-row"><label class="check-item"><input type="checkbox" data-check-item="${escape(item.id)}" ${checked ? "checked" : ""}><span>${text}</span></label>${sourceButton}</div>`;
  }

  function sectionMarkup(section) {
    return `<section class="content-section" aria-labelledby="section-${escape(section.id)}"><header class="content-section-header"><h2 id="section-${escape(section.id)}">${escape(section.title)}</h2><span class="kind-label${section.kind === "exam" ? " exam" : ""}">${section.kind === "exam" ? "신체진찰" : "문진"}</span></header>${section.items.map((item) => itemMarkup(item, true)).join("")}</section>`;
  }

  function referenceMarkup(section) {
    return `<details class="reference-section"><summary><span>${escape(section.title)}</span><span class="reference-kind">${section.kind === "note" ? "인계 원문" : "차팅 원문"}</span></summary>${section.items.map((item) => itemMarkup(item, false)).join("")}</details>`;
  }

  function renderDetail(complaint, common = false) {
    const name = common ? "공통 문진·진찰" : complaint.name;
    const category = common ? null : categoryOf(complaint.categoryId);
    const ids = common ? state.data.referenceSections : [...complaint.sectionIds, ...complaint.sharedSectionIds];
    const detailSections = [...new Set(ids)].map((id) => sections.get(id)).filter(Boolean);
    const primary = detailSections.filter((section) => ["history", "exam"].includes(section.kind));
    const references = detailSections.filter((section) => ["note", "example"].includes(section.kind));
    state.currentItems = [...new Set(primary.flatMap((section) => section.items.map((item) => item.id)))];
    let scopeNote = "";
    if (!common && complaint.scope === "pediatric") scopeNote = '<p class="scope-note">이 증상의 원문은 소아 자료입니다.</p>';
    if (!common && complaint.scope === "psychiatric") scopeNote = '<p class="scope-note">정신과 공통 문진 자료입니다.</p>';
    let empty = "";
    if (!primary.length) empty = `<div class="empty-state"><h2>문진·진찰 자료 없음</h2><p>${references.length ? "이 증상은 인계 메모만 있습니다. 아래 참고 자료에서 확인하세요." : "현재 인계 문서에 이 증상의 문진·진찰 항목이 없습니다."}</p></div>`;
    document.title = `${name} · ER 초진`;
    main.innerHTML = `<div class="shell detail-shell"><nav class="detail-toolbar" aria-label="증상 목록으로 이동"><a class="back-link" href="#">${icons.back}증상 목록</a><span class="toolbar-label">${escape(name)}</span></nav>
      <header class="detail-heading"><p class="eyebrow">${category ? `${escape(category.id)} ${escape(category.name)}` : "공통 자료"}</p><h1>${escape(name)}</h1><div class="cc-meta">${common ? "" : complaintBadges(complaint)}</div></header>${scopeNote}
      <div class="detail-actions"><span class="progress" id="check-progress" aria-live="polite"></span><button class="text-button" type="button" id="reset-checks" hidden>체크 초기화</button><button class="text-button" type="button" id="toggle-sources" aria-pressed="${state.showSources}">출처 ${state.showSources ? "숨기기" : "보기"}</button>${references.length ? '<button class="text-button" type="button" id="jump-references">참고 자료 ↓</button>' : ""}</div>
      <div id="primary-content">${empty}${primary.map(sectionMarkup).join("")}</div>
      ${references.length ? `<section id="reference-content" aria-labelledby="reference-title"><header class="reference-heading"><h2 id="reference-title">참고 자료</h2><p>인계 메모 · 차팅 예시 원문</p></header>${references.map(referenceMarkup).join("")}</section>` : ""}${footer()}
      <nav class="mobile-dock" aria-label="빠른 이동"><a class="back-link" href="#">${icons.back}증상 목록</a><button class="text-button" type="button" data-scroll-top>맨 위로</button></nav></div>`;
    updateProgress();
  }

  function updateProgress() {
    const progress = document.querySelector("#check-progress");
    if (!progress) return;
    const checked = state.checked.get(state.route) ?? new Set();
    const count = state.currentItems.filter((id) => checked.has(id)).length;
    progress.textContent = state.currentItems.length ? `확인 ${count} / ${state.currentItems.length}` : "";
    document.querySelector("#reset-checks").hidden = !count;
  }

  function route() {
    const hash = window.location.hash;
    const previousRoute = state.route;
    if (previousRoute === "home") state.homeScroll = window.scrollY;
    if (sourceDialog.open) sourceDialog.close();
    if (hash.startsWith("#cc/")) {
      let id;
      try { id = decodeURIComponent(hash.slice(4)); } catch { id = ""; }
      const complaint = complaints.get(id);
      if (complaint) {
        state.route = complaint.id;
        renderDetail(complaint);
      } else {
        state.route = "unknown";
        main.innerHTML = '<div class="shell"><div class="empty-state"><h1>증상을 찾을 수 없습니다</h1><p>증상 목록에서 다시 선택해 주세요.</p><a class="back-link" href="#">증상 목록으로</a></div></div>';
      }
    } else if (hash === "#common") {
      state.route = "common";
      renderDetail(null, true);
    } else {
      state.route = "home";
      renderHome();
    }
    window.requestAnimationFrame(() => window.scrollTo(0, state.route === "home" ? state.homeScroll : 0));
    if (previousRoute && previousRoute !== state.route) main.focus({ preventScroll: true });
  }

  async function loadProvenance() {
    if (!provenancePromise) provenancePromise = fetch("./data/content-provenance.json").then((response) => {
      if (!response.ok) throw new Error("출처 자료를 불러오지 못했습니다.");
      return response.json();
    }).then((data) => {
      state.provenance = data;
      return data;
    }).catch((error) => {
      provenancePromise = null;
      throw error;
    });
    return provenancePromise;
  }

  async function showSource(itemId) {
    sourceContent.innerHTML = '<p role="status">출처를 불러오는 중…</p>';
    sourceDialog.showModal();
    try {
      const data = await loadProvenance();
      const blockIds = new Set(Object.entries(data.assignments).filter(([, mappings]) => mappings.some((mapping) => mapping.itemId === itemId)).map(([blockId]) => blockId));
      const entries = data.sources.flatMap((source) => source.blocks.filter((block) => blockIds.has(block.id)).map((block) => ({ source, block })));
      const additions = (data.pdfAdditions ?? []).filter(([id]) => id === itemId);
      const markup = entries.map(({ source, block }) => `<section class="source-entry"><p class="source-file">${escape(source.file)}</p><p class="source-location">${block.paragraph ? `문단 ${escape(block.paragraph)}` : escape(block.id)}</p><div class="source-original">${escape(block.text)}</div></section>`).join("");
      const additionMarkup = additions.map(([, text, blockId]) => `<section class="source-entry"><p class="source-file">PDF 추가 원문</p><p class="source-location">${escape(blockId)}</p><div class="source-original">${escape(text)}</div></section>`).join("");
      sourceContent.innerHTML = markup + additionMarkup || "<p>이 항목의 출처를 찾을 수 없습니다.</p>";
    } catch (error) {
      sourceContent.innerHTML = `<p>${escape(error.message)}</p>`;
    }
  }

  main.addEventListener("click", (event) => {
    const filter = event.target.closest("[data-category]");
    if (filter) {
      state.categoryId = filter.dataset.category;
      renderHomeResults();
      const selected = document.querySelector(`[data-category="${state.categoryId}"]`);
      selected?.focus({ preventScroll: true });
      selected?.scrollIntoView({ block: "nearest", inline: "nearest" });
    }
    const source = event.target.closest("[data-source-item]");
    if (source) void showSource(source.dataset.sourceItem);
    if (event.target.closest("#toggle-sources")) {
      state.showSources = !state.showSources;
      document.querySelectorAll(".source-button").forEach((button) => { button.hidden = !state.showSources; });
      const button = document.querySelector("#toggle-sources");
      button.setAttribute("aria-pressed", String(state.showSources));
      button.textContent = `출처 ${state.showSources ? "숨기기" : "보기"}`;
    }
    if (event.target.closest("#reset-checks")) {
      state.checked.delete(state.route);
      document.querySelectorAll("[data-check-item]").forEach((checkbox) => { checkbox.checked = false; });
      updateProgress();
    }
    if (event.target.closest("#jump-references")) document.querySelector("#reference-content")?.scrollIntoView({ block: "start" });
    if (event.target.closest("[data-scroll-top]")) window.scrollTo(0, 0);
  });

  main.addEventListener("change", (event) => {
    if (!event.target.matches("[data-check-item]")) return;
    if (!state.checked.has(state.route)) state.checked.set(state.route, new Set());
    const checked = state.checked.get(state.route);
    if (event.target.checked) checked.add(event.target.dataset.checkItem);
    else checked.delete(event.target.dataset.checkItem);
    updateProgress();
  });

  document.querySelector("#close-source").addEventListener("click", () => sourceDialog.close());
  document.querySelector(".skip-link").addEventListener("click", (event) => {
    event.preventDefault();
    main.focus({ preventScroll: true });
    main.scrollIntoView({ block: "start" });
  });
  window.addEventListener("hashchange", route);
  if ("scrollRestoration" in history) history.scrollRestoration = "manual";

  async function start() {
    try {
      const response = await fetch("./data/chief-complaints.json");
      if (!response.ok) throw new Error("문진 자료를 불러오지 못했습니다.");
      state.data = await response.json();
      sections = new Map(state.data.sections.map((section) => [section.id, section]));
      complaints = new Map(state.data.complaints.map((complaint) => [complaint.id, complaint]));
      route();
    } catch (error) {
      main.innerHTML = `<div class="load-error"><h1>자료를 불러오지 못했습니다</h1><p>${escape(error.message)} 잠시 후 다시 시도해 주세요.</p><button class="text-button" type="button" id="retry-load">다시 불러오기</button></div>`;
      document.querySelector("#retry-load").addEventListener("click", () => { main.innerHTML = '<div class="loading" role="status">문진 자료를 불러오는 중…</div>'; void start(); });
    }
  }

  void start();
})();
