"use strict";

(() => {
  const main = document.querySelector("#main");
  const legacyRoutes = {
    mood: "psychiatry-interview", anxiety: "psychiatry-interview", sleep: "psychiatry-interview", suicide: "psychiatry-interview", poisoning: "psychiatry-interview",
    "vaginal-discharge": "obgyn-interview", "vaginal-bleeding": "obgyn-interview", menstrual: "obgyn-interview", dysmenorrhea: "obgyn-interview", "pelvic-pain": "obgyn-interview"
  };
  const icons = {
    back: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m14 5-7 7 7 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>'
  };
  const state = { data: null, homeScroll: 0, route: null, currentItems: [], checked: new Map() };
  let sections;
  let complaints;

  const escape = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
  const orderedCategories = () => [...state.data.categories].sort((a, b) => Number(a.secondary) - Number(b.secondary) || a.order - b.order);
  const categoryOf = (id) => state.data.categories.find((category) => category.id === id);
  const ccUrl = (id) => `#cc/${encodeURIComponent(id)}`;
  const badge = (text, muted = false) => `<span class="badge${muted ? " muted" : ""}">${escape(text)}</span>`;
  const hasContent = (complaint) => complaint.status !== "missing" && [...complaint.sectionIds, ...complaint.sharedSectionIds].some((id) => sections.get(id)?.items.length);

  function complaintBadges(complaint, includeScope = true) {
    const badges = [];
    if (includeScope && complaint.scope === "pediatric" && !complaint.name.includes("소아")) badges.push(badge("소아"));
    if (includeScope && complaint.scope === "psychiatric") badges.push(badge("정신과"));
    return badges.join("");
  }

  function complaintCard(complaint) {
    return `<a class="cc-card" href="${ccUrl(complaint.id)}"><span><span class="cc-name">${escape(complaint.name)}</span><span class="cc-meta">${complaintBadges(complaint, false)}</span></span></a>`;
  }

  function renderHome() {
    document.title = "ER 초진 · Quick Reference";
    main.innerHTML = `<div class="shell home-shell">
      <h1 class="sr-only">ER Quick Reference</h1>
      <div id="home-results"></div>
    </div>`;
    renderHomeResults();
  }

  function renderHomeResults() {
    const matching = state.data.complaints.filter(hasContent);
    const categories = orderedCategories().filter((category) => matching.some((complaint) => complaint.categoryId === category.id));
    const categoryCards = categories.map((category) => {
      const items = matching.filter((complaint) => complaint.categoryId === category.id).sort((a, b) => a.order - b.order);
      if (!items.length) return "";
      return `<section class="category${category.secondary ? " secondary" : ""}${category.id === "09" ? " pediatric" : ""}" aria-labelledby="category-${escape(category.id)}"><div class="category-title"><h3 id="category-${escape(category.id)}">${escape(category.name)}</h3></div><div class="category-cards">${items.map(complaintCard).join("")}</div></section>`;
    }).join("");
    document.querySelector("#home-results").innerHTML = `<section aria-labelledby="catalog-title"><div class="section-heading catalog-heading"><h2 id="catalog-title">분류</h2><div class="catalog-tools"><a class="common-shortcut" href="#common">공통 문진·진찰</a><span class="count">${matching.length}</span></div></div><div class="category-grid">${categoryCards}</div></section>`;
  }

  function itemMarkup(item, checkable) {
    const text = `${item.condition ? `<span class="condition">${escape(item.condition)}</span>` : ""}<span class="item-text">${escape(item.text)}</span>`;
    if (!checkable) return `<div class="item-row"><div class="reference-item">${text}</div></div>`;
    const checked = state.checked.get(state.route)?.has(item.id) ?? false;
    return `<div class="item-row"><label class="check-item"><input type="checkbox" data-check-item="${escape(item.id)}" ${checked ? "checked" : ""}><span>${text}</span></label></div>`;
  }

  function sectionMarkup(section) {
    return `<section class="content-section" aria-labelledby="section-${escape(section.id)}"><header class="content-section-header"><h2 id="section-${escape(section.id)}">${escape(section.title)}</h2><span class="kind-label${section.kind === "exam" ? " exam" : ""}">${section.kind === "exam" ? "신체진찰" : "문진"}</span></header>${section.items.map((item) => itemMarkup(item, true)).join("")}</section>`;
  }

  function referenceMarkup(section) {
    return `<details class="reference-section"><summary><span>${escape(section.title)}</span><span class="reference-kind">${section.kind === "note" ? "인계" : "차팅"}</span></summary>${section.items.map((item) => itemMarkup(item, false)).join("")}</details>`;
  }

  function renderDetail(complaint, common = false) {
    const name = common ? "공통 문진·진찰" : complaint.name;
    const category = common ? null : categoryOf(complaint.categoryId);
    const ids = common ? state.data.referenceSections : [...complaint.sectionIds, ...complaint.sharedSectionIds];
    const detailSections = [...new Set(ids)].map((id) => sections.get(id)).filter(Boolean);
    const primary = detailSections.filter((section) => ["history", "exam"].includes(section.kind));
    const references = detailSections.filter((section) => ["note", "example"].includes(section.kind));
    state.currentItems = [...new Set(primary.flatMap((section) => section.items.map((item) => item.id)))];
    document.title = `${name} · ER 초진`;
    main.innerHTML = `<div class="shell detail-shell"><nav class="detail-toolbar" aria-label="증상 목록으로 이동"><a class="back-link" href="#">${icons.back}목록</a><span class="toolbar-label">${escape(name)}</span></nav>
      <header class="detail-heading"><p class="eyebrow">${category ? escape(category.name) : "공통"}</p><h1>${escape(name)}</h1><div class="cc-meta">${common ? "" : complaintBadges(complaint)}</div></header>
      <div class="detail-actions"><span class="progress" id="check-progress" aria-live="polite"></span><button class="text-button" type="button" id="reset-checks" hidden>초기화</button></div>
      <div id="primary-content">${primary.map(sectionMarkup).join("")}</div>
      ${references.length ? `<section id="reference-content" aria-labelledby="reference-title"><header class="reference-heading"><h2 id="reference-title">참고</h2></header>${references.map(referenceMarkup).join("")}</section>` : ""}
      <nav class="mobile-dock" aria-label="빠른 이동"><a class="back-link" href="#">${icons.back}목록</a><button class="text-button" type="button" data-scroll-top>위로</button></nav></div>`;
    if (!primary.length) document.querySelector(".reference-section")?.setAttribute("open", "");
    updateProgress();
  }

  function updateProgress() {
    const progress = document.querySelector("#check-progress");
    if (!progress) return;
    const checked = state.checked.get(state.route) ?? new Set();
    const count = state.currentItems.filter((id) => checked.has(id)).length;
    progress.textContent = state.currentItems.length ? `${count} / ${state.currentItems.length}` : "";
    progress.setAttribute("aria-label", `확인 ${count} / ${state.currentItems.length}`);
    document.querySelector("#reset-checks").hidden = !count;
  }

  function route() {
    const hash = window.location.hash;
    const previousRoute = state.route;
    if (previousRoute === "home") state.homeScroll = window.scrollY;
    if (hash.startsWith("#cc/")) {
      let id;
      try { id = decodeURIComponent(hash.slice(4)); } catch { id = ""; }
      if (legacyRoutes[id] && complaints.has(legacyRoutes[id])) {
        id = legacyRoutes[id];
        history.replaceState(null, "", window.location.pathname + window.location.search + ccUrl(id));
      }
      const complaint = complaints.get(id);
      if (complaint && hasContent(complaint)) {
        state.route = complaint.id;
        renderDetail(complaint);
      } else if (complaint) {
        history.replaceState(null, "", window.location.pathname + window.location.search);
        state.route = "home";
        renderHome();
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

  main.addEventListener("click", (event) => {
    if (event.target.closest("#reset-checks")) {
      state.checked.delete(state.route);
      document.querySelectorAll("[data-check-item]").forEach((checkbox) => { checkbox.checked = false; });
      updateProgress();
    }
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

  document.querySelector(".skip-link").addEventListener("click", (event) => {
    event.preventDefault();
    main.focus({ preventScroll: true });
    main.scrollIntoView({ block: "start" });
  });
  window.addEventListener("hashchange", route);
  if ("scrollRestoration" in history) history.scrollRestoration = "manual";

  async function start() {
    try {
      const response = await fetch("./data/chief-complaints.json?v=3");
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
