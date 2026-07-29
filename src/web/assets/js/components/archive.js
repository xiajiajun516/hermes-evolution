// src/web/assets/js/components/archive.js
import { t } from '../i18n.js';
import { store } from '../store.js';
import { openDiffModal } from './diff_view.js';

let currentPage = 1;
const pageSize = 5;
let lastProject = null;
let lastSearchQuery = null;

const expandedItems = new Set();
const changeDataMap = new Map();

function formatChangeType(type, lang) {
  const key = `type_${type}`;
  const translated = t(key, {}, lang);
  return translated !== key ? translated : type;
}

function formatEntryTitle(entry, lang) {
  if (!entry.changes || entry.changes.length === 0) {
    return entry.title || t('change_title_fallback', {}, lang);
  }
  const counts = {};
  entry.changes.forEach(c => {
    counts[c.type] = (counts[c.type] || 0) + 1;
  });
  const parts = [];
  if (counts.skill_added) parts.push(t('change_skill_added', { n: counts.skill_added }, lang));
  if (counts.skill_updated) parts.push(t('change_skill_updated', { n: counts.skill_updated }, lang));
  if (counts.skill_removed) parts.push(t('change_skill_removed', { n: counts.skill_removed }, lang));
  if (counts.memory_added) parts.push(t('change_memory_added', { n: counts.memory_added }, lang));
  if (counts.memory_removed) parts.push(t('change_memory_removed', { n: counts.memory_removed }, lang));
  if (counts.cron_added) parts.push(t('change_cron_added', { n: counts.cron_added }, lang));
  if (counts.cron_removed) parts.push(t('change_cron_removed', { n: counts.cron_removed }, lang));
  return parts.length > 0 ? parts.join(' · ') : entry.title;
}

function formatEntrySummary(entry, lang) {
  const count = entry.changes ? entry.changes.length : 0;
  return count > 0 ? t('change_summary', { n: count }, lang) : (entry.summary || '');
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

export function renderArchive(state) {
  const lang = state.lang;
  const timeline = state.timeline || [];
  const searchQuery = (state.searchQuery || '').toLowerCase().trim();
  const selectedProject = state.selectedProject || 'all';

  if (lastProject !== selectedProject || lastSearchQuery !== searchQuery) {
    currentPage = 1;
    lastProject = selectedProject;
    lastSearchQuery = searchQuery;
  }

  changeDataMap.clear();

  // 过滤时间线条目
  const filteredTimeline = timeline.filter(entry => {
    // 1. 项目过滤
    if (selectedProject !== 'all' && entry.project && entry.project !== selectedProject) {
      return false;
    }
    // 2. 搜索框过滤
    if (searchQuery) {
      const matchTitle = (entry.title || '').toLowerCase().includes(searchQuery);
      const matchDate = (entry.date || '').toLowerCase().includes(searchQuery);
      const matchSummary = (entry.summary || '').toLowerCase().includes(searchQuery);
      const matchChanges = (entry.changes || []).some(c =>
        (c.name || '').toLowerCase().includes(searchQuery) ||
        (c.desc || '').toLowerCase().includes(searchQuery)
      );
      return matchTitle || matchDate || matchSummary || matchChanges;
    }
    return true;
  });

  if (filteredTimeline.length === 0) {
    return `
      <div class="archive-view">
        <div class="empty-state card">
          <div class="empty-icon">📚</div>
          <h2>${t('archive_empty_title', {}, lang)}</h2>
          <p style="margin-top: 0.5rem;">${t('archive_empty_desc', {}, lang)}</p>
        </div>
      </div>
    `;
  }

  const totalPages = Math.ceil(filteredTimeline.length / pageSize) || 1;
  if (currentPage > totalPages) currentPage = totalPages;
  if (currentPage < 1) currentPage = 1;

  const startIndex = (currentPage - 1) * pageSize;
  const pagedTimeline = filteredTimeline.slice(startIndex, startIndex + pageSize);

  return `
    <div class="archive-view">
      <div class="timeline">
        ${pagedTimeline.map((entry, index) => {
          const globalIndex = startIndex + index;
          const itemKey = `${entry.date}_${globalIndex}`;
          const isExpanded = expandedItems.has(itemKey);
          const hasChanges = entry.changes && entry.changes.length > 0;

          return `
            <div class="timeline-item">
              <div class="timeline-dot"></div>
              <div class="timeline-card">
                <div class="timeline-header">
                  <div>
                    <span class="timeline-date">📅 ${entry.date}</span>
                    ${entry.project ? `<span class="badge badge-purple" style="margin-left: 0.5rem;">${entry.project}</span>` : ''}
                    ${entry.has_gap ? `<span class="badge badge-orange" style="margin-left: 0.5rem;">${t('timeline_gap_warning', {}, lang)}</span>` : ''}
                  </div>
                  <span class="badge badge-blue">${formatEntrySummary(entry, lang)}</span>
                </div>

                <div class="timeline-summary" style="font-weight: 500; font-size: 1.05rem;">${formatEntryTitle(entry, lang)}</div>

                ${hasChanges ? `
                  <div style="margin-top: 0.75rem;">
                    <button class="btn btn-secondary toggle-expand-btn" data-key="${itemKey}" style="font-size: 0.8rem; padding: 0.25rem 0.6rem;">
                      ${isExpanded ? t('archive_collapse', {}, lang) : t('archive_expand', {}, lang)}
                    </button>
                  </div>

                  ${isExpanded ? `
                    <div class="timeline-changes-details" style="margin-top: 0.75rem; border-top: 1px dashed var(--border-color); padding-top: 0.75rem;">
                      ${entry.changes.map((c, cIdx) => {
                        let badgeClass = 'badge-blue';
                        if (c.type.includes('added')) badgeClass = 'badge-green';
                        if (c.type.includes('removed')) badgeClass = 'badge-red';

                        const changeId = `change_${globalIndex}_${cIdx}`;
                        changeDataMap.set(changeId, c);

                        return `
                          <div class="change-item" style="justify-content: space-between;">
                            <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                              <span class="badge ${badgeClass}">${formatChangeType(c.type, lang)}</span>
                              <strong>${c.name}</strong>
                              ${c.desc ? `<span class="change-item-desc">(${c.desc})</span>` : ''}
                            </div>
                            <button class="btn view-diff-btn" data-id="${changeId}" style="font-size: 0.75rem; padding: 0.15rem 0.45rem;">
                              Visual Diff 🔍
                            </button>
                          </div>
                        `;
                      }).join('')}
                    </div>
                  ` : ''}
                ` : ''}
              </div>
            </div>
          `;
        }).join('')}
      </div>
      ${renderPagination(currentPage, totalPages, lang)}
    </div>
  `;
}

export function bindArchiveEvents(container) {
  // 1. 展开/收起按钮绑定
  container.querySelectorAll('.toggle-expand-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const key = e.currentTarget.getAttribute('data-key');
      if (expandedItems.has(key)) {
        expandedItems.delete(key);
      } else {
        expandedItems.add(key);
      }
      store.notify();
    });
  });

  // 2. Visual Diff 按钮绑定
  container.querySelectorAll('.view-diff-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const id = e.currentTarget.getAttribute('data-id');
      const change = changeDataMap.get(id);
      if (change) {
        const oldText = change.old_content || '';
        const newText = change.new_content || '';
        const title = `${change.type}: ${change.name}`;
        openDiffModal(title, oldText, newText);
      }
    });
  });

  // 3. 分页按钮绑定
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
}
