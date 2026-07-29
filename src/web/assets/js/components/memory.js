// src/web/assets/js/components/memory.js
import { t } from '../i18n.js';
import { store } from '../store.js';

let activeTargetFilter = 'all';

export function renderMemory(state) {
  const lang = state.lang;
  const memories = state.latest?.memories || [];
  const searchQuery = (state.searchQuery || '').toLowerCase().trim();

  // 过滤记忆条目
  const filteredMemories = memories.filter(mem => {
    // Target 过滤
    if (activeTargetFilter !== 'all' && (mem.target || 'memory').toLowerCase() !== activeTargetFilter) {
      return false;
    }
    // 搜索词过滤
    if (searchQuery) {
      const matchContent = (mem.content || '').toLowerCase().includes(searchQuery);
      const matchTarget = (mem.target || '').toLowerCase().includes(searchQuery);
      return matchContent || matchTarget;
    }
    return true;
  });

  // 按 target 分组统计
  const userCount = memories.filter(m => (m.target || '').toLowerCase() === 'user').length;
  const memoryCount = memories.filter(m => (m.target || '').toLowerCase() !== 'user').length;

  return `
    <div class="memory-view">
      <!-- 目标类型 Filter -->
      <div class="tag-filter-bar">
        <button class="filter-chip ${activeTargetFilter === 'all' ? 'active' : ''}" data-target="all">
          ${t('memory_type_all', {}, lang)} (${memories.length})
        </button>
        <button class="filter-chip ${activeTargetFilter === 'user' ? 'active' : ''}" data-target="user">
          👤 ${t('memory_type_user', {}, lang)} (${userCount})
        </button>
        <button class="filter-chip ${activeTargetFilter === 'memory' ? 'active' : ''}" data-target="memory">
          🧠 ${t('memory_type_memory', {}, lang)} (${memoryCount})
        </button>
      </div>

      <!-- Memory Items List -->
      ${filteredMemories.length === 0 ? `
        <div class="empty-state card">
          <div class="empty-icon">🧠</div>
          <p>${t('memory_empty', {}, lang)}</p>
        </div>
      ` : `
        <div class="memory-list">
          ${filteredMemories.map(mem => {
            const target = (mem.target || 'memory').toLowerCase();
            const isUser = target === 'user';
            return `
              <div class="memory-item">
                <div style="flex: 1;">
                  <div style="margin-bottom: 0.4rem;">
                    <span class="badge ${isUser ? 'badge-green' : 'badge-purple'}">
                      ${isUser ? '👤 USER' : '🧠 MEMORY'}
                    </span>
                  </div>
                  <div class="memory-content">${escapeHtml(mem.content || '')}</div>
                </div>
                <div class="memory-meta">
                  <span>#${mem.content_hash || '---'}</span>
                  ${mem.updated_at || mem.created_at ? `<span>${mem.updated_at || mem.created_at}</span>` : ''}
                </div>
              </div>
            `;
          }).join('')}
        </div>
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
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
