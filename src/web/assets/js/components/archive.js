// src/web/assets/js/components/archive.js
import { t } from '../i18n.js';
import { store } from '../store.js';
import { openDiffModal } from './diff_view.js';

const expandedItems = new Set();
const changeDataMap = new Map();

export function renderArchive(state) {
  const lang = state.lang;
  const timeline = state.timeline || [];
  const searchQuery = (state.searchQuery || '').toLowerCase().trim();
  const selectedProject = state.selectedProject || 'all';

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

  return `
    <div class="archive-view">
      <div class="timeline">
        ${filteredTimeline.map((entry, index) => {
          const itemKey = `${entry.date}_${index}`;
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
                  <span class="badge badge-blue">${entry.summary || ''}</span>
                </div>

                <div class="timeline-summary" style="font-weight: 500; font-size: 1.05rem;">${entry.title}</div>

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

                        const changeId = `change_${index}_${cIdx}`;
                        changeDataMap.set(changeId, c);

                        return `
                          <div class="change-item" style="justify-content: space-between;">
                            <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                              <span class="badge ${badgeClass}">${c.type}</span>
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
}
