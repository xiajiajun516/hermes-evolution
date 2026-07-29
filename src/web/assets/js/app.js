// src/web/assets/js/app.js
import { store } from './store.js';
import { t } from './i18n.js';
import { renderDashboard } from './components/dashboard.js';
import { renderSkills, bindSkillsEvents } from './components/skills.js';
import { renderMemory, bindMemoryEvents } from './components/memory.js';
import { renderArchive, bindArchiveEvents } from './components/archive.js';

let searchDebounceTimer = null;

function updateI18nText() {
  const lang = store.state.lang;

  // 全局标签翻译
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    el.textContent = t(key, {}, lang);
  });

  // Header Title & Subtitle & Placeholder
  const headerTitle = document.getElementById('header-title');
  const headerSubtitle = document.getElementById('header-subtitle');
  const globalSearch = document.getElementById('global-search');
  const langLabel = document.getElementById('lang-label');

  if (headerTitle) headerTitle.textContent = t('page_title', {}, lang);
  if (headerSubtitle) headerSubtitle.textContent = t('page_subtitle', {}, lang);
  if (globalSearch) globalSearch.placeholder = t('search_placeholder', {}, lang);
  if (langLabel) langLabel.textContent = lang === 'zh' ? 'EN' : '中文';
}

function updateFooter() {
  const footerUpdated = document.getElementById('footer-updated');
  if (footerUpdated) {
    const generatedAt = store.state.meta?.generated_at || store.state.latest?.timestamp || '';
    if (generatedAt) {
      footerUpdated.textContent = generatedAt.replace('T', ' ').split('.')[0];
    } else {
      footerUpdated.textContent = '-';
    }
  }
}

function updateProjectSelector() {
  const wrapper = document.getElementById('project-wrapper');
  const select = document.getElementById('project-select');
  const projects = store.state.meta?.projects || [];

  if (projects.length > 0 && wrapper && select) {
    wrapper.style.display = 'block';
    // 动态填充选项
    const currentVal = store.state.selectedProject;
    const allLabel = t('all_projects', {}, lang);
    select.innerHTML = `<option value="all">${allLabel} (All)</option>` +
      projects.map(p => `<option value="${p}" ${p === currentVal ? 'selected' : ''}>${p}</option>`).join('');
  }
}

function renderActiveView() {
  const content = document.getElementById('app-content');
  if (!content) return;

  if (store.state.loading) {
    content.innerHTML = `
      <div class="loading-spinner">
        <div class="spinner"></div>
        <p>${t('loading', {}, store.state.lang)}</p>
      </div>
    `;
    return;
  }

  const currentTab = store.state.currentTab;

  switch (currentTab) {
    case 'dashboard':
      content.innerHTML = renderDashboard(store.state);
      break;

    case 'skills':
      content.innerHTML = renderSkills(store.state);
      bindSkillsEvents(content);
      break;

    case 'memory':
      content.innerHTML = renderMemory(store.state);
      bindMemoryEvents(content);
      break;

    case 'archive':
      content.innerHTML = renderArchive(store.state);
      bindArchiveEvents(content);
      break;

    default:
      content.innerHTML = renderDashboard(store.state);
      break;
  }
}

function updateActiveTabButtons() {
  const currentTab = store.state.currentTab;
  document.querySelectorAll('#app-tabs .tab-btn').forEach(btn => {
    const tab = btn.getAttribute('data-tab');
    if (tab === currentTab) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
}

function renderApp() {
  updateI18nText();
  updateFooter();
  updateProjectSelector();
  updateActiveTabButtons();
  renderActiveView();
}

function setupEventListeners() {
  // 1. Tab 切换绑定 (使用事件委托)
  const tabsNav = document.getElementById('app-tabs');
  if (tabsNav) {
    tabsNav.addEventListener('click', (e) => {
      const btn = e.target.closest('.tab-btn');
      if (btn) {
        const tab = btn.getAttribute('data-tab');
        if (tab) store.setTab(tab);
      }
    });
  }

  // 2. 搜索框防抖
  const searchInput = document.getElementById('global-search');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      clearTimeout(searchDebounceTimer);
      searchDebounceTimer = setTimeout(() => {
        store.setSearchQuery(e.target.value);
      }, 250);
    });
  }

  // 3. 多语言切换
  const langBtn = document.getElementById('lang-toggle');
  if (langBtn) {
    langBtn.addEventListener('click', () => {
      const newLang = store.state.lang === 'zh' ? 'en' : 'zh';
      store.setLang(newLang);
    });
  }

  // 4. 项目筛选 Select
  const projectSelect = document.getElementById('project-select');
  if (projectSelect) {
    projectSelect.addEventListener('change', (e) => {
      store.setSelectedProject(e.target.value);
    });
  }
}

// 启动应用
function initApp() {
  setupEventListeners();
  store.subscribe(renderApp);
  store.loadData();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}
