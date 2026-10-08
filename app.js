"use strict";

(() => {
  const main = document.querySelector("#main");
  const legacyRoutes = {
    mood: "psychiatry-interview", anxiety: "psychiatry-interview", sleep: "psychiatry-interview", suicide: "psychiatry-interview", poisoning: "psychiatry-interview",
    "vaginal-discharge": "obgyn-interview", "vaginal-bleeding": "obgyn-interview", menstrual: "obgyn-interview", dysmenorrhea: "obgyn-interview", "pelvic-pain": "obgyn-interview"
  };
  const compactViewPreferenceKey = "er-note-compact-view";
  const legacyAbbreviationPreferenceKey = "er-note-symptom-abbreviations";
  const redundantGroupTitles = new Set(["Basic", "History", "Background"]);
  const state = { data: null, concepts: new Map(), homeScroll: 0, route: null, currentItems: [], checked: new Map(), compactView: true, detailTab: "interview", panelScroll: {} };
  let sections;
  let complaints;

  const escape = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
  const orderedHomeGroups = () => [...state.data.homeGroups].sort((a, b) => a.order - b.order);
  const orderedCategories = () => [...state.data.categories].sort((a, b) => a.order - b.order || Number(a.secondary) - Number(b.secondary));
  const categoryOf = (id) => state.data.categories.find((category) => category.id === id);
  const ccUrl = (id) => `#cc/${encodeURIComponent(id)}`;
  const hasContent = (complaint) => complaint.status !== "missing" && [...complaint.sectionIds, ...complaint.sharedSectionIds].some((id) => sections.get(id)?.items.length);

  function complaintCardSpan(name) {
    const compactLength = Array.from(String(name).replace(/\s/g, "")).length;
    if (compactLength <= 4) return 1;
    if (compactLength <= 10) return 2;
    return 3;
  }

  function complaintCard(complaint) {
    const span = complaintCardSpan(complaint.name);
    return `<a class="cc-card span-${span}" href="${ccUrl(complaint.id)}"><span class="cc-name">${escape(complaint.name)}</span></a>`;
  }

  function renderHome() {
    document.title = "ER 초진 · Quick Reference";
    main.innerHTML = `<div class="shell home-shell">
      <h1 class="sr-only">ER Quick Reference</h1>
      <div id="home-results"></div>
      <label class="abbreviation-toggle"><input type="checkbox" data-compact-toggle ${state.compactView ? "checked" : ""}>간략 보기</label>
    </div>`;
    renderHomeResults();
  }

  function renderHomeResults() {
    const matching = state.data.complaints.filter(hasContent);
    const categories = orderedCategories().filter((category) => matching.some((complaint) => complaint.categoryId === category.id));
    const categoryMarkup = (category, headingTag = "h3", headingId = `category-${category.id}`) => {
      const items = matching.filter((complaint) => complaint.categoryId === category.id).sort((a, b) => a.order - b.order);
      if (!items.length) return "";
      return `<section class="category${category.secondary ? " secondary" : ""}${category.id === "09" ? " pediatric" : ""}" aria-labelledby="${escape(headingId)}"><div class="category-title"><${headingTag} id="${escape(headingId)}">${escape(category.name)}</${headingTag}></div><div class="category-cards">${items.map(complaintCard).join("")}</div></section>`;
    };
    const groupMarkup = orderedHomeGroups().map((group) => {
      const groupCategories = categories.filter((category) => category.homeGroupId === group.id);
      if (!groupCategories.length) return "";
      if (groupCategories.length === 1 && groupCategories[0].name === group.name) {
        return `<section class="home-group home-group-single">${categoryMarkup(groupCategories[0], "h2", `home-group-${group.id}`)}</section>`;
      }
      return `<section class="home-group" aria-labelledby="home-group-${escape(group.id)}"><h2 class="home-group-title" id="home-group-${escape(group.id)}">${escape(group.name)}</h2><div class="category-grid">${groupCategories.map((category) => categoryMarkup(category)).join("")}</div></section>`;
    }).join("");
    document.querySelector("#home-results").innerHTML = groupMarkup;
  }

  function displayItemText(item) {
    if (!state.compactView) return item.text;
    if (item.abbreviation) return item.abbreviation;
    if (item.abbreviatedText) return item.abbreviatedText;
    return (state.data.symptomAbbreviations ?? []).reduce((text, abbreviation) => {
      const expansion = abbreviation.expansion.join(" / ");
      return text.replaceAll(expansion, abbreviation.label);
    }, item.text);
  }

  function itemCopy(item) {
    return `<span class="item-copy">${item.condition ? `<span class="condition">${escape(item.condition)}</span>` : ""}<span class="item-text">${escape(displayItemText(item))}</span>${item.note ? `<small class="item-note">* ${escape(item.note)}</small>` : ""}</span>`;
  }

  function itemMarkup(item) {
    const checked = state.checked.get(state.route)?.has(item.id) ?? false;
    return `<div class="item-row"><label class="check-item"><input type="checkbox" data-check-item="${escape(item.id)}" ${checked ? "checked" : ""}>${itemCopy(item)}</label></div>`;
  }

  function compactCheckMarkup(item) {
    const checked = state.checked.get(state.route)?.has(item.id) ?? false;
    const label = item.compactText ?? item.abbreviation;
    return `<label class="compact-check"><input type="checkbox" data-check-item="${escape(item.id)}" ${checked ? "checked" : ""}><span>${escape(label)}</span></label>`;
  }

  function groupItemsMarkup(group) {
    if (!state.compactView) return group.items.map(itemMarkup).join("");
    const rows = new Map();
    const regularItems = [];
    group.items.forEach((item) => {
      const rowKey = item.compactRow ?? (item.abbreviation ? "abbreviations" : null);
      if (!rowKey) {
        regularItems.push(item);
        return;
      }
      if (!rows.has(rowKey)) rows.set(rowKey, []);
      rows.get(rowKey).push(item);
    });
    return `${[...rows.values()].map((items) => `<div class="compact-row">${items.map(compactCheckMarkup).join("")}</div>`).join("")}${regularItems.map(itemMarkup).join("")}`;
  }

  function sectionMarkup(section) {
    return `<section class="content-section" aria-labelledby="section-${escape(section.id)}"><header class="content-section-header"><h2 id="section-${escape(section.id)}">${escape(section.title)}</h2><span class="kind-label${section.kind === "exam" ? " exam" : ""}">${section.kind === "exam" ? "신체진찰" : "문진"}</span></header>${section.items.map(itemMarkup).join("")}</section>`;
  }

  function layoutSectionMarkup(section) {
    return `<section class="content-section" aria-labelledby="section-${escape(section.id)}"><header class="content-section-header"><h2 id="section-${escape(section.id)}">${escape(section.title)}</h2></header>${section.groups.map((group) => `<section class="content-group">${redundantGroupTitles.has(group.title) ? "" : `<h3>${escape(group.title)}</h3>`}${groupItemsMarkup(group)}</section>`).join("")}</section>`;
  }

  function referenceGroupMarkup(group) {
    return `<section class="reference-group"><h3>${escape(group.title)}</h3><ul>${group.items.map((item) => `<li>${itemCopy(item)}</li>`).join("")}</ul></section>`;
  }

  function referenceSectionMarkup(section) {
    return referenceGroupMarkup({ title: section.title, items: section.items });
  }

  function conceptMarkup(complaint) {
    const concept = state.concepts.get(complaint.id);
    if (!concept) return '<p class="concept-error" role="status">개념 자료를 불러오지 못했습니다. <button class="text-button reset-button" type="button" id="retry-concepts">다시 불러오기</button></p>';
    const meanings = (kind, title) => concept[kind].length
      ? `<section class="concept-section"><h2>${title}</h2><dl class="concept-meanings">${concept[kind].map((item) => `<div><dt>${escape(item.label)}</dt><dd>${escape(item.meaning)}</dd></div>`).join("")}</dl></section>`
      : "";
    return `<div class="concept-summary"><section class="concept-section"><h2>감별</h2><dl class="concept-differentials">${concept.differentials.map((item) => `<div><dt>${escape(item.disease)}</dt><dd>${escape(item.clues)}</dd></div>`).join("")}</dl></section>${meanings("hx", "Hx")}${meanings("pex", "PEx")}<p class="concept-caution">${escape(concept.caution.text)}</p></div>`;
  }

  function selectDetailTab(name, focus = false) {
    if (!["interview", "concept"].includes(name)) return;
    if (state.detailTab !== name) {
      state.panelScroll[state.detailTab] = window.scrollY;
      state.detailTab = name;
      document.querySelector("#interview-panel").hidden = name !== "interview";
      document.querySelector("#concept-panel").hidden = name !== "concept";
      document.querySelector(".detail-progress").hidden = name !== "interview";
      const complaintId = state.route;
      window.requestAnimationFrame(() => {
        if (state.route === complaintId && state.detailTab === name) window.scrollTo(0, state.panelScroll[name] ?? 0);
      });
    }
    document.querySelectorAll("[data-detail-tab]").forEach((tab) => {
      const selected = tab.dataset.detailTab === name;
      tab.setAttribute("aria-selected", String(selected));
      tab.tabIndex = selected ? 0 : -1;
      if (selected && focus) tab.focus({ preventScroll: true });
    });
  }

  function renderDetail(complaint) {
    const name = complaint.name;
    const category = categoryOf(complaint.categoryId);
    const ids = [...complaint.sharedSectionIds, ...complaint.sectionIds];
    const detailSections = [...new Set(ids)].map((id) => sections.get(id)).filter(Boolean);
    const primary = ["history", "exam"].flatMap((kind) => detailSections.filter((section) => section.kind === kind));
    const references = detailSections.filter((section) => ["note", "example"].includes(section.kind));
    const layoutSections = complaint.layout?.sections ?? [];
    const layoutPrimary = layoutSections.filter((section) => ["history", "exam"].includes(section.kind));
    const layoutReferences = layoutSections.filter((section) => ["note", "example"].includes(section.kind));
    const primaryMarkup = layoutPrimary.length ? layoutPrimary.map(layoutSectionMarkup).join("") : primary.map(sectionMarkup).join("");
    const referenceMarkup = layoutReferences.length
      ? layoutReferences.flatMap((section) => section.groups).map(referenceGroupMarkup).join("")
      : references.map(referenceSectionMarkup).join("");
    state.currentItems = [...new Set((layoutPrimary.length
      ? layoutPrimary.flatMap((section) => section.groups.flatMap((group) => group.items.map((item) => item.id)))
      : primary.flatMap((section) => section.items.map((item) => item.id))))];
    state.detailTab = "interview";
    state.panelScroll = {};
    document.title = `${name} · ER 초진`;
    main.innerHTML = `<div class="shell detail-shell"><header class="detail-heading"><p class="eyebrow">${escape(category.name)}</p><div class="detail-title-row"><h1>${escape(name)}</h1><div class="detail-progress"><span class="progress" id="check-progress" aria-live="polite"></span><button class="text-button reset-button" type="button" id="reset-checks" hidden>초기화</button></div></div></header>
      <div class="detail-tabs" role="tablist" aria-label="상세 내용"><button type="button" id="interview-tab" role="tab" aria-controls="interview-panel" aria-selected="true" data-detail-tab="interview">문진</button><button type="button" id="concept-tab" role="tab" aria-controls="concept-panel" aria-selected="false" tabindex="-1" data-detail-tab="concept">개념</button></div>
      <div id="interview-panel" role="tabpanel" aria-labelledby="interview-tab"><div id="primary-content">${primaryMarkup}</div>
      ${referenceMarkup ? `<section id="reference-content" aria-labelledby="reference-title"><header class="reference-heading"><h2 id="reference-title">참고사항</h2></header><div class="reference-board">${referenceMarkup}</div></section>` : ""}</div>
      <div id="concept-panel" role="tabpanel" aria-labelledby="concept-tab" hidden>${conceptMarkup(complaint)}</div></div>`;
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
      if (!hasContent(complaints.get(id) ?? { status: "missing" }) && legacyRoutes[id] && complaints.has(legacyRoutes[id])) {
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
    } else {
      state.route = "home";
      renderHome();
    }
    window.requestAnimationFrame(() => window.scrollTo(0, state.route === "home" ? state.homeScroll : 0));
    if (previousRoute && previousRoute !== state.route) main.focus({ preventScroll: true });
  }

  main.addEventListener("click", (event) => {
    const tab = event.target.closest("[data-detail-tab]");
    if (tab) {
      selectDetailTab(tab.dataset.detailTab);
      return;
    }
    if (event.target.closest("#retry-concepts")) {
      const panel = document.querySelector("#concept-panel");
      const complaint = complaints.get(state.route);
      panel.innerHTML = '<p class="concept-error" role="status">개념 자료를 불러오는 중…</p>';
      void loadConcepts().then(() => {
        if (complaint.id === state.route && panel === document.querySelector("#concept-panel")) panel.innerHTML = conceptMarkup(complaint);
      });
      return;
    }
    if (event.target.closest("#reset-checks")) {
      state.checked.delete(state.route);
      document.querySelectorAll("[data-check-item]").forEach((checkbox) => { checkbox.checked = false; });
      updateProgress();
    }
  });

  main.addEventListener("keydown", (event) => {
    const tab = event.target.closest("[data-detail-tab]");
    if (!tab || !["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const name = event.key === "Home" ? "interview" : event.key === "End" ? "concept" : tab.dataset.detailTab === "interview" ? "concept" : "interview";
    selectDetailTab(name, true);
  });

  main.addEventListener("change", (event) => {
    if (event.target.matches("[data-compact-toggle]")) {
      state.compactView = event.target.checked;
      try { localStorage.setItem(compactViewPreferenceKey, state.compactView ? "1" : "0"); } catch {}
      return;
    }
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

  async function loadConcepts() {
    try {
      const response = await fetch("./data/cc-concepts.json?v=2");
      if (!response.ok) throw new Error("개념 자료를 불러오지 못했습니다.");
      const data = await response.json();
      state.concepts = new Map(data.complaints.map((concept) => [concept.complaintId, concept]));
    } catch {
      state.concepts = new Map();
    }
  }

  async function start() {
    try {
      try {
        const savedCompactView = localStorage.getItem(compactViewPreferenceKey);
        const legacyCompactView = localStorage.getItem(legacyAbbreviationPreferenceKey);
        state.compactView = savedCompactView !== null
          ? savedCompactView === "1"
          : legacyCompactView !== null
            ? legacyCompactView === "1"
            : true;
      } catch {}
      const [response] = await Promise.all([fetch("./data/chief-complaints.json?v=22"), loadConcepts()]);
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

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      void navigator.serviceWorker.register("./sw.js").catch(() => {});
    }, { once: true });
  }

  void start();
})();
