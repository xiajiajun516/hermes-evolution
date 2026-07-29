// src/web/assets/js/components/memory.js
import { t } from '../i18n.js';
import { store } from '../store.js';

let activeTargetFilter = 'all';
let currentPage = 1;
const pageSize = 10;
let lastTargetFilter = null;
let lastSearchQuery = null;
const expandedMemoryIds = new Set();

const TARGET_CONFIGS = {
  user: { icon: '👤', i18nKey: 'memory_type_user', badgeClass: 'badge-green', label: 'USER' },
  memory: { icon: '🧠', i18nKey: 'memory_type_memory', badgeClass: 'badge-purple', label: 'MEMORY' },
  project: { icon: '📁', i18nKey: 'memory_type_project', badgeClass: 'badge-blue', label: 'PROJECT' },
  ops: { icon: '⚙️', i18nKey: 'memory_type_ops', badgeClass: 'badge-orange', label: 'OPS' },
  general: { icon: '📝', i18nKey: 'memory_type_general', badgeClass: 'badge-cyan', label: 'GENERAL' },
};

function getTargetBadge(target) {
  const tKey = (target || 'memory').toLowerCase();
  const cfg = TARGET_CONFIGS[tKey];
  if (cfg) {
    return {
      badgeClass: cfg.badgeClass,
      badgeText: `${cfg.icon} ${cfg.label}`
    };
  }
  return {
    badgeClass: 'badge',
    badgeText: tKey.toUpperCase()
  };
}

function renderPagination(currentPage, totalPages, lang) {
  if (totalPages <= 1) return '';

  let pageBtns = '';
  for (let i = 1; i <= totalPages; i++) {
    pageBtns += `<button class="page-btn ${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
  }

  return `
    <div class="pagination-bar">
      <button class="page-btn prev-page-btn" ${currentPage === 1 ? 'disabled' : ''} data-page="${currentPage - 1}">
        ${t('pagination_prev', {}, lang)}
      </button>
      <span class="page-info">${t('page_info', { current: currentPage, total: totalPages }, lang)}</span>
      ${pageBtns}
      <button class="page-btn next-page-btn" ${currentPage === totalPages ? 'disabled' : ''} data-page="${currentPage + 1}">
        ${t('pagination_next', {}, lang)}
      </button>
    </div>
  `;
}

export function renderMemory(state) {
  const lang = state.lang;
  const memories = state.latest?.memories || [];
  const searchQuery = (state.searchQuery || '').toLowerCase().trim();

  if (lastTargetFilter !== activeTargetFilter || lastSearchQuery !== searchQuery) {
    currentPage = 1;
    lastTargetFilter = activeTargetFilter;
    lastSearchQuery = searchQuery;
  }

  // 过滤记忆条目
  const filteredMemories = memories.filter(mem => {
    const target = (mem.target || 'memory').toLowerCase();
    // Target 过滤
    if (activeTargetFilter !== 'all' && target !== activeTargetFilter) {
      return false;
    }
    // 搜索词过滤
    if (searchQuery) {
      const matchContent = (mem.content || '').toLowerCase().includes(searchQuery);
      const matchTarget = target.includes(searchQuery);
      const matchScopeId = (mem.scope_id || '').toLowerCase().includes(searchQuery);
      return matchContent || matchTarget || matchScopeId;
    }
    return true;
  });

  // 按 target 分组统计
  const targetCounts = {};
  memories.forEach(mem => {
    const tKey = (mem.target || 'memory').toLowerCase();
    targetCounts[tKey] = (targetCounts[tKey] || 0) + 1;
  });

  const standardTargets = ['user', 'memory', 'project', 'ops', 'general'];
  const presentTargets = memories.map(m => (m.target || 'memory').toLowerCase());
  const filterTargets = Array.from(new Set([...standardTargets, ...presentTargets]));

  const totalPages = Math.ceil(filteredMemories.length / pageSize) || 1;
  if (currentPage > totalPages) currentPage = totalPages;
  if (currentPage < 1) currentPage = 1;

  const startIndex = (currentPage - 1) * pageSize;
  const pagedMemories = filteredMemories.slice(startIndex, startIndex + pageSize);

  return `
    <div class="memory-view">
      <!-- 目标类型 Filter -->
      <div class="tag-filter-bar">
        <button class="filter-chip ${activeTargetFilter === 'all' ? 'active' : ''}" data-target="all">
          ${t('memory_type_all', {}, lang)} (${memories.length})
        </button>
        ${filterTargets.map(tKey => {
          const count = targetCounts[tKey] || 0;
          const cfg = TARGET_CONFIGS[tKey];
          let icon = cfg ? cfg.icon : '🏷️';
          let name = cfg ? t(cfg.i18nKey, {}, lang) : (t(`memory_type_${tKey}`, {}, lang) !== `memory_type_${tKey}` ? t(`memory_type_${tKey}`, {}, lang) : tKey.toUpperCase());
          if (name === cfg?.i18nKey) name = cfg.label;
          return `
            <button class="filter-chip ${activeTargetFilter === tKey ? 'active' : ''}" data-target="${tKey}">
              ${icon} ${name} (${count})
            </button>
          `;
        }).join('')}
      </div>

      <!-- Memory Items List -->
      ${filteredMemories.length === 0 ? `
        <div class="empty-state card">
          <div class="empty-icon">🧠</div>
          <p>${t('memory_empty', {}, lang)}</p>
        </div>
      ` : `
        <div class="memory-list">
          ${pagedMemories.map((mem, index) => {
            const { badgeClass, badgeText } = getTargetBadge(mem.target);
            const isScopeRecall = mem.source === 'scope-recall' || Boolean(mem.scope_id);
            const memId = mem.id || mem.content_hash || `mem_${startIndex + index}`;
            const content = mem.content || '';
            const isLongText = content.length > 150 || content.includes('\n');
            const isExpanded = expandedMemoryIds.has(memId);

            return `
              <div class="memory-item">
                <div style="flex: 1;">
                  <div style="margin-bottom: 0.4rem; display: flex; gap: 0.4rem; align-items: center; flex-wrap: wrap;">
                    <span class="badge ${badgeClass}">
                      ${badgeText}
                    </span>
                    ${isScopeRecall ? `
                      <span class="badge badge-indigo">
                        ${t('memory_source_scope_recall', {}, lang)}
                      </span>
                    ` : ''}
                    ${mem.scope_id ? `
                      <span class="badge badge-blue">
                        ${escapeHtml(mem.scope_id)}
                      </span>
                    ` : ''}
                  </div>
                  <div class="memory-content ${isLongText && !isExpanded ? 'collapsed' : ''}">${escapeHtml(content)}</div>
                  ${isLongText ? `
                    <button class="expand-text-btn" data-id="${memId}">
                      ${isExpanded ? t('text_collapse', {}, lang) : t('text_expand', {}, lang)}
                    </button>
                  ` : ''}
                </div>
                <div class="memory-meta">
                  <span>#${mem.content_hash || '---'}</span>
                  ${mem.updated_at || mem.created_at ? `<span>${mem.updated_at || mem.created_at}</span>` : ''}
                </div>
              </div>
            `;
          }).join('')}
        </div>
        ${renderPagination(currentPage, totalPages, lang)}
      `}
    </div>
  `;
}

export function bindMemoryEvents(container) {
  container.querySelectorAll('.filter-chip').forEach(btn => {
    btn.addEventListener('click', (e) => {
      activeTargetFilter = e.currentTarget.getAttribute('data-target');
      store.notify();
    });
  });

  container.querySelectorAll('.pagination-bar .page-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      if (e.currentTarget.hasAttribute('disabled')) return;
      const page = parseInt(e.currentTarget.getAttribute('data-page'), 10);
      if (page && page !== currentPage) {
        currentPage = page;
        store.notify();
        container.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  container.querySelectorAll('.expand-text-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const id = e.currentTarget.getAttribute('data-id');
      if (expandedMemoryIds.has(id)) {
        expandedMemoryIds.delete(id);
      } else {
        expandedMemoryIds.add(id);
      }
      store.notify();
    });
  });
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&#039;");
}
